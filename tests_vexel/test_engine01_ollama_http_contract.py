"""JAR-ENGINE-01 — backend path over real HTTP, with Wyzer's own Ollama client.

USER INPUT → PT normalisation → VoiceSession → Wyzer Orchestrator → OllamaChatProvider
(UrllibJsonTransport, unmodified upstream) → HTTP on 127.0.0.1 → response validation →
allowlist / confirmation → result presentation.

The server is ``tests_vexel.ollama_loopback.FakeOllama``: scripted replies on an
ephemeral loopback port. Evidence class: **HTTP_CONTRACT_PASS** (wire format, parsing,
failure handling, policy). It is not inference: no model runs, so nothing here is
``REAL_INFERENCE_PASS``. Applications stay simulated (``SimulatedLauncher``).
"""

from __future__ import annotations

import asyncio
import json
import socket
import time
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

import pytest

from jarvis.brain.pt_provider import PORTUGUESE_INSTRUCTION, create_local_provider
from jarvis.config import SliceConfig
from jarvis.core.assistant import AssistantParts, build_voice_session
from jarvis.core.voice_loop import TurnOutcome, VoiceSession
from jarvis.language.prompts import (
    SAY_CANCELLED,
    SAY_CANCELLED_UNCLEAR,
    SAY_DENIED,
    SAY_MODEL_UNAVAILABLE,
    SAY_NOTHING_OPENED,
)
from jarvis.runtime import text_mode
from jarvis.tools.allowlist import ALLOWLIST_TOOL_NAMES, SimulatedLauncher
from jarvis.ui.events import RecordingSink, VoiceState
from tests_vexel.fakes import (
    FIXED_NOW,
    FixedProbe,
    ImmediateActivation,
    RecordingTts,
    ScriptedStt,
    slice_config,
)
from tests_vexel.ollama_loopback import DEFAULT_MODEL, FakeOllama, Reply, chat_text, chat_tool

_PROXY_VARIABLES = ("http_proxy", "HTTP_PROXY", "https_proxy", "HTTPS_PROXY", "all_proxy", "ALL_PROXY")


@pytest.fixture(autouse=True)
def _direct_loopback(monkeypatch: pytest.MonkeyPatch) -> None:
    """urllib honours proxy variables; loopback traffic must never leave the host."""
    for name in _PROXY_VARIABLES:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("NO_PROXY", "127.0.0.1,localhost")
    monkeypatch.setenv("no_proxy", "127.0.0.1,localhost")


@pytest.fixture
def ollama():
    server = FakeOllama().start()
    try:
        yield server
    finally:
        server.stop()


def config_for(endpoint: str, *, timeout: float = 5.0, real_actions: bool = False) -> SliceConfig:
    base = slice_config()
    llm = base.wyzer.llm.model_copy(update={"endpoint": endpoint, "request_timeout_seconds": timeout})
    vexel = base.vexel.model_copy(update={"allow_real_windows_actions": real_actions})
    return replace(base, wyzer=base.wyzer.model_copy(update={"llm": llm}), vexel=vexel)


@dataclass
class HttpRig:
    session: VoiceSession
    parts: AssistantParts
    tts: RecordingTts
    sink: RecordingSink
    launcher: SimulatedLauncher
    probe: FixedProbe

    @property
    def pending(self):
        return self.parts.orchestrator.world.snapshot().pending_confirmation


def http_rig(endpoint: str, *, timeout: float = 5.0) -> HttpRig:
    config = config_for(endpoint, timeout=timeout)
    tts, sink, launcher, probe = RecordingTts(), RecordingSink(), SimulatedLauncher(), FixedProbe()
    session, parts = build_voice_session(
        config,
        create_local_provider(config.wyzer),  # the real Wyzer OllamaChatProvider
        stt=ScriptedStt(),
        tts=tts,
        activation=ImmediateActivation(),
        sink=sink,
        launcher=launcher,
        probe=probe,
        clock=lambda: FIXED_NOW,
    )
    session.start()
    return HttpRig(session, parts, tts, sink, launcher, probe)


def closed_port_url() -> str:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    return f"http://127.0.0.1:{port}"


def ask(rig: HttpRig, text: str | None):
    return asyncio.run(rig.session.handle_text(text))


def subsequence(needle: list[VoiceState], haystack: list[VoiceState]) -> bool:
    iterator = iter(haystack)
    return all(state in iterator for state in needle)


def tool_messages(body: dict[str, Any]) -> list[dict[str, Any]]:
    return [m for m in body["messages"] if m.get("role") == "tool"]


# =========================================================== 1-3 availability


def test_01_provider_available_diagnosis_over_http(ollama: FakeOllama) -> None:
    rig = http_rig(ollama.url)
    provider = rig.parts.provider
    result = asyncio.run(provider.inner.diagnose())
    assert result.available and result.details == {"configured_model_found": True, "model_count": 1}
    assert asyncio.run(text_mode.diagnose_provider(provider)) == text_mode.LLM_READY
    assert [(r.method, r.path) for r in ollama.received] == [("GET", "/api/tags")] * 2
    assert ollama.host == "127.0.0.1"


def test_02_provider_unavailable_is_spoken_as_fixed_sentence() -> None:
    # Windows answers a refused loopback connect only after ~2 s: generous timeout.
    rig = http_rig(closed_port_url(), timeout=10.0)
    assert asyncio.run(text_mode.diagnose_provider(rig.parts.provider)) == text_mode.LLM_UNREACHABLE
    result = ask(rig, "Jarvis, qual é a capital de Moçambique?")
    assert result.outcome is TurnOutcome.ANSWERED and result.spoken
    assert rig.tts.spoken == [SAY_MODEL_UNAVAILABLE]
    assert result.detail == "PROVIDER_UNREACHABLE"
    assert result.metrics["llm_failures"] == 1.0
    assert "127.0.0.1" not in result.reply and "refused" not in result.reply.casefold()
    assert rig.launcher.requested == [] and rig.session.state is VoiceState.IDLE


def test_03_model_not_found(ollama: FakeOllama) -> None:
    ollama.models = ["llama3.2:1b"]
    rig = http_rig(ollama.url)
    assert asyncio.run(text_mode.diagnose_provider(rig.parts.provider)) == text_mode.LLM_MODEL_MISSING
    ollama.script(
        Reply({"error": f'model "{DEFAULT_MODEL}" not found, try pulling it first'}, status=404)
    )
    result = ask(rig, "Olá Jarvis")
    assert rig.tts.spoken == [SAY_MODEL_UNAVAILABLE]
    assert result.detail == "PROVIDER_HTTP_404"
    assert "pull" not in (result.reply or "")  # provider text never reaches the user


# ================================================== 4, 9 valid reply + payload


def test_04_09_valid_portuguese_reply_and_request_contract(ollama: FakeOllama) -> None:
    ollama.script(chat_text("Maputo é a capital de Moçambique."))
    rig = http_rig(ollama.url)
    result = ask(rig, "Jarvis, qual é a capital de Moçambique?")

    assert result.outcome is TurnOutcome.ANSWERED and result.spoken
    assert rig.tts.spoken == ["Maputo é a capital de Moçambique."]
    [request] = ollama.chats()
    body, headers = request.body, {k.casefold(): v for k, v in request.headers.items()}
    # Wire contract of Wyzer's OllamaChatProvider with the slice configuration.
    assert request.method == "POST" and request.path == "/api/chat"
    assert body["model"] == DEFAULT_MODEL and body["stream"] is False and body["think"] is False
    assert body["options"] == {"temperature": 0.1, "num_predict": 256, "num_ctx": 8192}
    assert body["keep_alive"] == "30m"
    assert "authorization" not in headers and headers["content-type"] == "application/json"
    assert {tool["function"]["name"] for tool in body["tools"]} == set(ALLOWLIST_TOOL_NAMES)
    assert len(body["tools"]) == 3
    system = body["messages"][0]
    assert system["role"] == "system" and PORTUGUESE_INSTRUCTION in system["content"]
    assert body["messages"][-1] == {
        "role": "user",
        "content": "Jarvis, qual é a capital de Moçambique?",  # UTF-8 intact on the wire
    }
    # Per-component latency: the model's share is measured inside think_ms.
    metrics = result.metrics
    assert metrics["llm_calls"] == 1.0 and metrics["llm_eval_count"] == 12.0
    assert metrics["llm_model_ms"] == 1500.0
    assert 0 < metrics["llm_ms"] <= metrics["think_ms"]
    assert {"think_ms", "tts_ms"} <= set(metrics)


# ============================================================ 5 malformed


@pytest.mark.parametrize(
    "reply",
    [
        Reply(b"<html>not json</html>"),
        Reply([1, 2, 3]),
        Reply({"model": DEFAULT_MODEL, "done": True}),  # no message
        Reply({"message": {"role": "assistant", "content": "x", "tool_calls": {"a": 1}}}),
        Reply(b'{"message": {"role": "assistant", "content": "trunc'),
    ],
    ids=["not_json", "json_array", "no_message", "tool_calls_not_list", "truncated_json"],
)
def test_05_malformed_response_fails_closed(ollama: FakeOllama, reply: Reply) -> None:
    ollama.script(reply)
    rig = http_rig(ollama.url)
    result = ask(rig, "Que horas são?")
    assert rig.tts.spoken == [SAY_MODEL_UNAVAILABLE]
    assert result.detail == "PROVIDER_INVALID_RESPONSE"
    assert result.action_status is None and rig.launcher.requested == []
    assert rig.pending is None


# ============================================================ 6-8 transport


def test_06_timeout(ollama: FakeOllama) -> None:
    ollama.script(Reply(delay=3.0, body={"message": {"role": "assistant", "content": "tarde"}}))
    rig = http_rig(ollama.url, timeout=0.3)
    started = time.monotonic()
    result = ask(rig, "Que horas são?")
    assert time.monotonic() - started < 2.5
    assert result.detail == "PROVIDER_TIMEOUT"
    assert rig.tts.spoken == [SAY_MODEL_UNAVAILABLE] and "tarde" not in rig.tts.spoken


def test_07_network_error_connection_dropped(ollama: FakeOllama) -> None:
    ollama.script(Reply(drop=True))
    rig = http_rig(ollama.url)
    result = ask(rig, "Que horas são?")
    assert result.detail == "PROVIDER_UNREACHABLE"
    assert rig.tts.spoken == [SAY_MODEL_UNAVAILABLE]


def test_08_cancellation_while_request_in_flight_discards_late_tool_call(
    ollama: FakeOllama,
) -> None:
    # The late reply would ask to open the Calculator: it must never arm a confirmation.
    ollama.script(Reply(hold=True, body=chat_tool("open_allowed_application", {"app": "calculator"}).body))
    rig = http_rig(ollama.url)

    async def scenario():
        turn = asyncio.create_task(rig.session.handle_text("Abre a calculadora"))
        deadline = time.monotonic() + 5
        while not ollama.chat_arrived.is_set():
            assert time.monotonic() < deadline, "request never reached the loopback server"
            await asyncio.sleep(0.01)
        assert rig.session.state is VoiceState.THINKING
        assert rig.session.cancel(reason="test") is True
        result = await turn
        ollama.release.set()  # let the server answer the abandoned request
        await asyncio.sleep(0.2)
        return result

    result = asyncio.run(scenario())
    assert result.outcome is TurnOutcome.DISCARDED and not result.spoken
    assert rig.tts.spoken == [] and rig.pending is None and rig.launcher.requested == []
    assert result.metrics.get("llm_cancelled") == 1.0
    assert rig.session.state is VoiceState.IDLE
    # The session recovers: the next turn goes over HTTP normally.
    ollama.script(chat_text("Estou aqui."))
    assert ask(rig, "Estás aí?").outcome is TurnOutcome.ANSWERED
    assert rig.tts.spoken == ["Estou aqui."]


# ===================================================== 10 tool calls (B, C)


def test_10_case_b_local_time_maputo_through_tool_round_trip(ollama: FakeOllama) -> None:
    ollama.script(chat_tool("get_local_time"), chat_text("São catorze e trinta em Maputo."))
    rig = http_rig(ollama.url)
    result = ask(rig, "Jarvis, que horas são em Maputo?")

    assert rig.tts.spoken == ["São catorze e trinta em Maputo."]
    first, second = ollama.chats()
    [tool_message] = tool_messages(second.body)
    assert tool_message["tool_name"] == "get_local_time"
    content = tool_message["content"]  # the tool result is fed back to the model over HTTP
    assert "14:30" in content and "Africa/Maputo" in content, content
    states = rig.sink.states
    assert subsequence(
        [VoiceState.LISTENING, VoiceState.THINKING, VoiceState.TOOL_RUNNING, VoiceState.SPEAKING, VoiceState.IDLE],
        states,
    ), states
    assert result.metrics["llm_calls"] == 2.0 and result.action_status is None


def test_10_case_c_system_status_test_probe(ollama: FakeOllama) -> None:
    ollama.script(chat_tool("get_system_status"), chat_text("O processador está a doze por cento."))
    rig = http_rig(ollama.url)
    ask(rig, "Como está o computador?")
    assert rig.probe.reads == 1
    [tool_message] = tool_messages(ollama.chats()[1].body)
    assert tool_message["tool_name"] == "get_system_status" and "12.5" in tool_message["content"]
    assert rig.tts.spoken == ["O processador está a doze por cento."]


# ====================================== D, E simulated apps with confirmation


@pytest.mark.parametrize(
    ("app", "label", "request_text"),
    [("calculator", "a Calculadora", "Abre a calculadora"), ("notepad", "o Bloco de Notas", "Abre o bloco de notas")],
)
def test_cases_d_e_simulated_application_after_spoken_confirmation(
    ollama: FakeOllama, app: str, label: str, request_text: str
) -> None:
    ollama.script(
        chat_tool("open_allowed_application", {"app": app}),
        chat_text(f"Abri {label}."),  # a false claim the policy must not repeat
    )
    rig = http_rig(ollama.url)
    asked = ask(rig, request_text)
    assert asked.outcome is TurnOutcome.CONFIRMATION_REQUESTED and asked.awaiting_confirmation
    assert rig.tts.spoken == [f"Queres que eu abra {label}? Responde sim ou não."]
    assert rig.launcher.requested == []  # nothing before the confirmation
    assert rig.pending is not None and rig.pending.tool_name == "open_allowed_application"

    done = ask(rig, "sim")
    assert done.outcome is TurnOutcome.CONFIRMED and done.action_status == "SIMULATED"
    assert rig.launcher.requested == [app]
    assert done.reply == f"Modo de simulação: não abri {label}. Nenhuma aplicação foi iniciada."
    assert f"Abri {label}." not in rig.tts.spoken
    assert subsequence(
        # The question is spoken while AWAITING_CONFIRMATION; the answer starts a new LISTENING.
        [VoiceState.THINKING, VoiceState.AWAITING_CONFIRMATION, VoiceState.LISTENING,
         VoiceState.THINKING, VoiceState.TOOL_RUNNING, VoiceState.SPEAKING, VoiceState.IDLE],
        rig.sink.states,
    ), rig.sink.states
    # Replay protection: a second "sim" executes nothing and makes no HTTP call.
    calls = len(ollama.chats())
    again = ask(rig, "sim")
    assert again.outcome is TurnOutcome.NOTHING_TO_CONFIRM
    assert rig.launcher.requested == [app] and len(ollama.chats()) == calls


# ===================================================== F negation / invalid


@pytest.mark.parametrize(
    ("answer", "outcome", "spoken"),
    [
        ("não", TurnOutcome.REJECTED, SAY_CANCELLED),
        ("cancela", TurnOutcome.REJECTED, SAY_CANCELLED),
        ("talvez amanhã", TurnOutcome.CANCELLED_UNCLEAR, SAY_CANCELLED_UNCLEAR),
    ],
)
def test_case_f_negation_or_invalid_confirmation_never_launches(
    ollama: FakeOllama, answer: str, outcome: TurnOutcome, spoken: str
) -> None:
    ollama.script(chat_tool("open_allowed_application", {"app": "calculator"}))
    rig = http_rig(ollama.url)
    assert ask(rig, "Abre a calculadora").awaiting_confirmation
    calls = len(ollama.chats())
    result = ask(rig, answer)
    assert result.outcome is outcome and rig.tts.spoken[-1] == spoken
    assert rig.launcher.requested == [] and rig.pending is None
    assert len(ollama.chats()) == calls  # the refusal is never sent to the model
    assert ask(rig, "sim").outcome is TurnOutcome.NOTHING_TO_CONFIRM
    assert rig.launcher.requested == []


def test_case_f_confirmation_without_pending_makes_no_http_call(ollama: FakeOllama) -> None:
    rig = http_rig(ollama.url)
    assert ask(rig, "sim").outcome is TurnOutcome.NOTHING_TO_CONFIRM
    assert ollama.chats() == []


# ============================================== 11 unauthorised tool calls


@pytest.mark.parametrize(
    "reply",
    [
        chat_tool("run_shell", {"command": "del C:\\Windows"}),
        chat_tool("open_allowed_application", {"app": "cmd"}),
        chat_tool("open_allowed_application", {"app": "calculator", "path": "C:\\x.exe"}),
        chat_tool("open_allowed_application", '{"app": "calc'),  # invalid JSON string
    ],
    ids=["unregistered_tool", "app_outside_allowlist", "extra_argument", "invalid_json_arguments"],
)
def test_11_unauthorised_tool_call_is_denied(ollama: FakeOllama, reply: Reply) -> None:
    ollama.script(reply, chat_text("Abri a linha de comandos."))
    rig = http_rig(ollama.url)
    # JAR-COG-01: explicit request, so the malformed call reaches Wyzer's validation.
    result = ask(rig, "Abre a calculadora")
    assert result.action_status == "DENIED"
    assert result.reply == SAY_DENIED and rig.tts.spoken == [SAY_DENIED]
    assert rig.launcher.requested == [] and rig.pending is None


# ============================================== 12 unexpected information


def test_12_model_claims_an_action_without_tool_result(ollama: FakeOllama) -> None:
    ollama.script(chat_text("Pronto, abri a Calculadora."))
    rig = http_rig(ollama.url)
    result = ask(rig, "Abre a calculadora")
    assert result.claim_blocked and rig.tts.spoken == [SAY_NOTHING_OPENED]
    assert rig.launcher.requested == []


def test_12_non_string_content_and_unknown_fields(ollama: FakeOllama) -> None:
    ollama.script(chat_text(42, unexpected={"nested": [1, 2]}, model="other-model"))
    rig = http_rig(ollama.url)
    result = ask(rig, "Diz um número")
    assert result.outcome is TurnOutcome.ANSWERED and rig.tts.spoken == ["42"]


def test_12_malformed_tool_call_entries_are_ignored(ollama: FakeOllama) -> None:
    body = chat_text("Não percebi o pedido.").body
    body["message"]["tool_calls"] = ["junk", {"function": {"arguments": {}}}, {"function": "x"}]
    ollama.script(Reply(body))
    rig = http_rig(ollama.url)
    result = ask(rig, "Faz qualquer coisa")
    assert rig.tts.spoken == ["Não percebi o pedido."] and result.action_status is None


@pytest.mark.parametrize(
    "metadata",
    [b'"total_duration": 1' + b"0" * 400, b'"eval_count": 1' + b"0" * 400,
     b'"total_duration": Infinity', b'"eval_count": true', b'"total_duration": -5'],
    ids=["huge_duration", "huge_eval_count", "infinite_duration", "bool_eval_count", "negative"],
)
def test_12_hostile_metadata_never_breaks_the_turn(
    ollama: FakeOllama, tmp_path: Path, metadata: bytes
) -> None:
    body = b'{"message": {"role": "assistant", "content": "Tudo bem."}, "done": true, ' + metadata + b"}"
    ollama.script(Reply(body))
    rig = http_rig(ollama.url)
    result = ask(rig, "Tudo bem?")
    assert result.outcome is TurnOutcome.ANSWERED and rig.tts.spoken == ["Tudo bem."]
    assert result.metrics["llm_calls"] == 1.0
    assert "llm_model_ms" not in result.metrics and "llm_eval_count" not in result.metrics
    from jarvis.runtime.voice_mode import TurnLog

    log = TurnLog(tmp_path / "t.jsonl")
    log.write(result.as_record())
    json.loads(log.path.read_text(encoding="utf-8"), parse_constant=lambda c: pytest.fail(c))


def test_orchestrator_raw_failure_text_is_translated() -> None:
    from jarvis.language.prompts import translate_wyzer_reply

    reply, translated = translate_wyzer_reply("The local model could not respond: boom at 127.0.0.1")
    assert translated and reply == SAY_MODEL_UNAVAILABLE


def test_non_object_json_wording_is_pinned_to_upstream() -> None:
    source = (Path(__file__).resolve().parents[1] / "wyzer" / "brain" / "http.py").read_text(encoding="utf-8")
    assert "non-object JSON" in source  # classify_provider_failure relies on this wording


def test_12_truncated_generation_is_reported(ollama: FakeOllama) -> None:
    ollama.script(chat_text("Resposta cortada", done_reason="length"))
    rig = http_rig(ollama.url)
    result = ask(rig, "Explica a história de Moçambique")
    assert result.metrics["llm_truncated"] == 1.0


def test_12_qwen_tool_parse_500_is_retried_once_conservatively(ollama: FakeOllama) -> None:
    ollama.script(
        Reply({"error": "XML syntax error on line 1: tool call parsing failed"}, status=500),
        chat_tool("get_local_time"),
        chat_text("São catorze e trinta."),
    )
    rig = http_rig(ollama.url)
    ask(rig, "Que horas são?")
    first, retry, final = ollama.chats()
    assert retry.body["think"] is False and retry.body["options"]["temperature"] == 0.0
    assert "Tool-call recovery" in retry.body["messages"][0]["content"]
    assert rig.tts.spoken == ["São catorze e trinta."]


def test_12_repeated_server_error_is_not_retried_forever(ollama: FakeOllama) -> None:
    error = Reply({"error": "tool call parsing failed"}, status=500)
    ollama.script(error, error, error)
    rig = http_rig(ollama.url)
    result = ask(rig, "Que horas são?")
    assert len(ollama.chats()) == 2  # original + one retry, nothing more
    assert result.detail == "PROVIDER_HTTP_500" and rig.tts.spoken == [SAY_MODEL_UNAVAILABLE]


# ======================================================== text mode runtime


class ScriptedConsole:
    def __init__(self, lines: list[str]) -> None:
        self.lines = list(lines)
        self.written: list[str] = []

    def read_line(self) -> str | None:
        return self.lines.pop(0) if self.lines else None

    def write(self, text: str) -> None:
        self.written.append(text)


def test_text_mode_end_to_end_over_http_logs_timings_without_text(
    ollama: FakeOllama, tmp_path: Path
) -> None:
    ollama.script(
        chat_text("Maputo é a capital de Moçambique."),
        chat_tool("open_allowed_application", {"app": "notepad"}),
        chat_text("Abri o Bloco de Notas."),
    )
    console = ScriptedConsole(
        ["Qual é a capital de Moçambique?", "Abre o bloco de notas", "sim", "sair"]
    )
    # Even with real actions enabled in the config, text mode stays simulated.
    config = config_for(ollama.url, real_actions=True)
    deps = text_mode.TextRuntimeDeps(console=console, log_directory=tmp_path)
    result = asyncio.run(text_mode.run_text_mode(config, deps))

    assert result.exit_code == 0 and result.llm_status == text_mode.LLM_READY
    assert isinstance(result.launcher, SimulatedLauncher)
    assert result.launcher.requested == ["notepad"]
    assert [t["outcome"] for t in result.turns] == ["answered", "confirmation_requested", "confirmed"]
    assert result.turns[2]["action_status"] == "SIMULATED"
    assert "Jarvis: Maputo é a capital de Moçambique." in console.written
    assert any(line.startswith("[resultado=answered") and "llm_ms=" in line for line in console.written)
    log = (tmp_path / "text-turns.jsonl").read_text(encoding="utf-8")
    assert "Moçambique" not in log and "Maputo" not in log  # no text by default
    first = json.loads(log.splitlines()[0])
    assert first["metrics"]["llm_calls"] == 1.0 and "heard_chars" in first
    assert first["mode"] == "text"
    assert (tmp_path / "text-ui-events.jsonl").exists()


def test_text_mode_module_has_no_real_launcher() -> None:
    source = Path(text_mode.__file__).read_text(encoding="utf-8")
    assert "WindowsApplicationLauncher" not in source
    main_source = (Path(text_mode.__file__).parents[1] / "__main__.py").read_text(encoding="utf-8")
    assert "WindowsApplicationLauncher" not in main_source


# ================================================= failure codes and meter


def _chained(outer: BaseException, cause: BaseException) -> BaseException:
    outer.__cause__ = cause
    return outer


@pytest.mark.parametrize(
    ("error", "code"),
    [
        (ConnectionError("refused 127.0.0.1:11434"), "PROVIDER_UNREACHABLE"),
        (TimeoutError("timed out"), "PROVIDER_TIMEOUT"),
        (json.JSONDecodeError("bad", "x", 0), "PROVIDER_INVALID_RESPONSE"),
        (RuntimeError("internal provider detail"), "PROVIDER_ERROR"),
    ],
)
def test_failure_codes_are_fixed_and_carry_no_provider_text(error: BaseException, code: str) -> None:
    from wyzer.brain.http import HttpTransportError
    from wyzer.brain.providers import LLMProviderError

    from jarvis.brain.pt_provider import classify_provider_failure

    wrapped = _chained(LLMProviderError("PROVIDER_REQUEST_FAILED", "x"), _chained(HttpTransportError("y"), error))
    assert classify_provider_failure(wrapped) == code
    assert classify_provider_failure(error) == code
    http = _chained(LLMProviderError("PROVIDER_REQUEST_FAILED", "x"), HttpTransportError("z", status=503))
    assert classify_provider_failure(http) == "PROVIDER_HTTP_503"
    assert classify_provider_failure(LLMProviderError("PROVIDER_NOT_CONFIGURED", "x")) == "PROVIDER_NOT_CONFIGURED"


def test_meter_turn_delta_only_reports_activity() -> None:
    from jarvis.brain.pt_provider import ProviderMeter

    meter = ProviderMeter()
    before = meter.snapshot()
    assert meter.snapshot().since(before) == {}
    meter.record_success(100.0, {"eval_count": 20, "total_duration": 80_000_000, "done_reason": "stop"})
    meter.record_failure(5.0, "PROVIDER_TIMEOUT")
    delta = meter.snapshot().since(before)
    assert delta == {
        "llm_calls": 2.0,
        "llm_ms": 105.0,
        "llm_failures": 1.0,
        "llm_eval_count": 20.0,
        "llm_model_ms": 80.0,
    }
    assert meter.snapshot().last_failure == "PROVIDER_TIMEOUT"


def test_latency_summary_reports_llm_stage() -> None:
    import importlib.util

    path = Path(__file__).resolve().parents[1] / "qa" / "benchmarks" / "latency_summary.py"
    spec = importlib.util.spec_from_file_location("latency_summary_engine01", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    turns = [{"outcome": "answered", "metrics": {"think_ms": 900.0, "llm_ms": 700.0, "tts_ms": 100.0}}]
    summary = module.summarise(turns)
    assert summary["stages"]["llm_ms"]["p50"] == 700.0
    assert summary["response_ms"]["p50"] == 1000.0  # llm_ms is not added on top of think_ms
    # Text-mode logs are never G9 voice-latency evidence, however fast and numerous.
    fast_text = [{"outcome": "answered", "mode": "text", "metrics": {"think_ms": 10.0, "tts_ms": 0.0}}] * 25
    text_summary = module.summarise(fast_text)
    assert text_summary["acceptance"]["applicable"] is False
    assert text_summary["acceptance"]["pass"] is False
    assert "NOT_APPLICABLE" in module.render(text_summary)
