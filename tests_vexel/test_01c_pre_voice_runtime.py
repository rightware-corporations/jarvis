"""JAR-SLICE-01C-PRE — voice runtime preparation, all with fakes.

Covers the order's twelve items: voice-mode start, missing microphone, missing PT
voice, Ollama unavailable / model missing, capture failure, STT failure, TTS failure,
cancel during recognition, late response after cancel, unpresented confirmation,
Windows tools disabled, and (via the full suite) regression.
"""

from __future__ import annotations

import asyncio
import json
import threading
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from jarvis.core.voice_loop import TurnOutcome
from jarvis.runtime.preflight import CheckStatus, PreflightDeps, run_preflight
from jarvis.runtime.voice_mode import (
    EXIT_OK,
    EXIT_PREFLIGHT_BLOCKED,
    VoiceRuntimeDeps,
    run_voice_mode,
)
from jarvis.tools.allowlist import SimulatedLauncher
from jarvis.ui.events import VoiceState
from jarvis.voice.capture import CancellableCapture, MicrophoneStatus, probe_microphone
from jarvis.voice.contracts import CaptureError, SpeechPlaybackError, Transcript
from jarvis.voice.sapi import VoiceInfo, parse_inventory, select_portuguese_voice
from jarvis.voice.stt_pt import create_voice_input
from wyzer.brain.http import HttpTransportError, JsonResponse
from wyzer.brain.providers import OllamaChatProvider
from wyzer.speech.windows import SpeechAdapterError
from tests_vexel.conftest import make_rig
from jarvis.ui.events import RecordingSink
from tests_vexel.fakes import (
    FailingTts,
    RecordingTts,
    ScriptedProvider,
    ScriptedStt,
    StubbornProvider,
    call,
    say,
    slice_config,
)

MIC_OK = MicrophoneStatus(True, 1, True, "MIC_OK")
VOICES = [
    VoiceInfo("Microsoft Zira Desktop", "en-US", "Female", True),
    VoiceInfo("Microsoft Maria Desktop", "pt-BR", "Female", True),
    VoiceInfo("Microsoft Helia Desktop", "pt-PT", "Female", True),
]


def _diag(available: bool, found: bool | None = True, endpoint: str = "http://127.0.0.1:11434"):
    details = {} if found is None else {"configured_model_found": found, "model_count": 2}
    return SimpleNamespace(available=available, endpoint=endpoint, details=details)


def ready_deps(**overrides: Any) -> PreflightDeps:
    async def llm(_config):
        return _diag(True)

    base = dict(
        platform="win32",
        python_version=(3, 11),
        find_spec=lambda name: object(),
        whisper_present=lambda settings: True,
        microphone=lambda: MIC_OK,
        voices=lambda: VOICES,
        llm_diagnose=llm,
    )
    base.update(overrides)
    return PreflightDeps(**base)


def preflight(deps: PreflightDeps, config=None):
    return asyncio.run(run_preflight(config or slice_config(), deps))


class ScriptedConsole:
    """Feeds console commands; waits for the previous turn to settle before the next."""

    def __init__(self, lines: list[str | None], settle: threading.Event | None = None) -> None:
        self.lines = list(lines)
        self.output: list[str] = []
        self.settle = settle
        self._turn_requested = False

    def read_line(self) -> str | None:
        if self.settle is not None and self._turn_requested:
            # Wait until the turn started by the previous Enter is back to IDLE.
            assert self.settle.wait(5), "turn did not settle"
            self.settle.clear()
        line = self.lines.pop(0) if self.lines else None
        self._turn_requested = line == ""
        return line

    def write(self, text: str) -> None:
        self.output.append(text)


class SettleSink(RecordingSink):
    """Signals the console whenever the session goes back to IDLE."""

    def __init__(self, event: threading.Event) -> None:
        super().__init__()
        self.event = event

    def publish(self, event) -> None:
        super().publish(event)
        if event.state is VoiceState.IDLE and event.previous is not VoiceState.OFFLINE:
            self.event.set()


def runtime(
    tmp_path: Path,
    *,
    stt: Any,
    provider: Any,
    tts: Any = None,
    lines: list[str | None] | None = None,
    preflight_deps: PreflightDeps | None = None,
    config=None,
):
    settle = threading.Event()
    sink = SettleSink(settle)
    speech = tts or RecordingTts()
    seen: dict[str, Any] = {}

    def stt_factory(cfg, capture):
        seen["capture"] = capture
        return stt

    def tts_factory(cfg, voice_name):
        seen["voice"] = voice_name
        return speech

    deps = VoiceRuntimeDeps(
        preflight=preflight_deps or ready_deps(),
        capture_factory=lambda: SimpleNamespace(capture=lambda t: None),
        stt_factory=stt_factory,
        tts_factory=tts_factory,
        provider_factory=lambda cfg: provider,
        console=ScriptedConsole(lines if lines is not None else ["", None], settle),
        log_directory=tmp_path / "logs",
        extra_sink=sink,
    )
    result = asyncio.run(run_voice_mode(config or slice_config(), deps))
    return result, deps, sink, speech, seen


# ===================================================================== 1. start


def test_voice_mode_starts_runs_a_turn_and_shuts_down(tmp_path: Path) -> None:
    provider = ScriptedProvider([call("get_local_time"), say("São catorze e trinta.")])
    result, deps, sink, tts, seen = runtime(
        tmp_path, stt=ScriptedStt(["Jarvis, que horas são?"]), provider=provider
    )
    assert result.exit_code == EXIT_OK and result.report.ready
    assert seen["voice"] == "Microsoft Helia Desktop"  # pt-PT preferred over pt-BR
    assert isinstance(seen["capture"], CancellableCapture)
    assert tts.spoken == ["São catorze e trinta."]
    assert [t["outcome"] for t in result.turns] == ["answered"]
    assert sink.states[-1] is VoiceState.OFFLINE
    # Per-stage timings recorded, transcript text not recorded by default.
    record = result.turns[0]
    assert {"stt_ms", "think_ms", "tts_ms"} <= set(record["metrics"])
    log = (tmp_path / "logs" / "voice-turns.jsonl").read_text(encoding="utf-8")
    assert "que horas" not in log.casefold() and "catorze" not in log
    assert "heard_chars" in json.loads(log.splitlines()[0])


def test_voice_mode_preserves_text_mode_entry_point() -> None:
    from jarvis.__main__ import main

    with pytest.raises(SystemExit):
        main(["--help"])
    assert main(["--check-config"]) == 0


# ===================================================================== preflight


def test_preflight_ready_with_all_probes_passing() -> None:
    report = preflight(ready_deps())
    assert report.ready and report.blocking_codes == []
    assert report.get("tts_voice").code == "PT_VOICE_SELECTED"


@pytest.mark.parametrize(
    ("override", "check", "code"),
    [
        ({"platform": "linux"}, "platform", "NOT_WINDOWS"),
        ({"python_version": (3, 12)}, "python", "PYTHON_NOT_311"),
        ({"find_spec": lambda n: None if n == "faster_whisper" else object()}, "dependencies", "DEPENDENCY_MISSING"),
        ({"whisper_present": lambda s: False}, "stt_model", "STT_MODEL_MISSING"),
    ],
    ids=["not_windows", "python", "dependency", "stt_model"],
)
def test_preflight_blocks_on_environment(override: dict, check: str, code: str) -> None:
    report = preflight(ready_deps(**override))
    assert not report.ready
    assert report.get(check).status is CheckStatus.FAIL and report.get(check).code == code


# ===================================================================== 2. microphone


@pytest.mark.parametrize(
    ("devices", "default", "code"),
    [
        ([{"name": "Speakers", "max_input_channels": 0}], (-1, 0), "MIC_MISSING"),
        ([{"name": "Mic", "max_input_channels": 1}], (-1, 0), "MIC_NO_DEFAULT"),
        ([{"name": "Mic", "max_input_channels": 2}], (0, 1), "MIC_OK"),
    ],
)
def test_microphone_probe(devices, default, code) -> None:
    status = probe_microphone(lambda: devices, lambda: default)
    assert status.code == code and status.available is (code == "MIC_OK")


def test_microphone_probe_handles_query_failure() -> None:
    def broken():
        raise OSError("PortAudio not initialized")

    assert probe_microphone(broken, lambda: (0, 0)).code == "AUDIO_QUERY_FAILED"


def test_missing_microphone_blocks_voice_mode(tmp_path: Path) -> None:
    deps = ready_deps(microphone=lambda: MicrophoneStatus(False, 0, False, "MIC_MISSING"))
    result, *_ = runtime(tmp_path, stt=ScriptedStt(), provider=ScriptedProvider(), preflight_deps=deps)
    assert result.exit_code == EXIT_PREFLIGHT_BLOCKED
    assert "MIC_MISSING" in result.report.blocking_codes
    assert result.turns == []


# ===================================================================== 3. PT voice


def test_missing_portuguese_voice_blocks_voice_mode(tmp_path: Path) -> None:
    english_only = [VoiceInfo("Microsoft Zira Desktop", "en-US"), VoiceInfo("Microsoft David Desktop", "en-US")]
    result, *_ = runtime(
        tmp_path, stt=ScriptedStt(), provider=ScriptedProvider(),
        preflight_deps=ready_deps(voices=lambda: english_only),
    )
    assert result.exit_code == EXIT_PREFLIGHT_BLOCKED
    check = result.report.get("tts_voice")
    assert check.code == "PT_VOICE_MISSING" and "en-US" in check.detail


@pytest.mark.parametrize(
    ("voices", "configured", "expected", "code"),
    [
        (VOICES, None, "Microsoft Helia Desktop", "PT_VOICE_SELECTED"),
        (VOICES, "Microsoft Maria Desktop", "Microsoft Maria Desktop", "PT_VOICE_CONFIGURED"),
        (VOICES, "Microsoft Zira Desktop", "Microsoft Helia Desktop", "PT_VOICE_FALLBACK"),
        (VOICES, "Voz Inexistente", "Microsoft Helia Desktop", "PT_VOICE_FALLBACK"),
        ([VoiceInfo("Microsoft Helia Desktop", "pt-PT", enabled=False),
          VoiceInfo("Microsoft Maria Desktop", "pt-BR")], None, "Microsoft Maria Desktop", "PT_VOICE_SELECTED"),
        ([VoiceInfo("Microsoft Helia Desktop", "pt-PT", enabled=False)], None, None, "PT_VOICE_MISSING"),
        ([], None, None, "PT_VOICE_MISSING"),
    ],
    ids=["prefer_pt_pt", "configured_pt", "configured_english", "configured_missing",
         "skip_disabled", "only_disabled", "none"],
)
def test_portuguese_voice_selection(voices, configured, expected, code) -> None:
    selection = select_portuguese_voice(voices, configured=configured)
    assert selection.code == code
    assert (selection.voice.name if selection.voice else None) == expected


def test_configured_non_portuguese_voice_is_a_warning_not_a_silent_choice() -> None:
    config = slice_config()
    config = replace(config, wyzer=config.wyzer.model_copy(
        update={"speech": config.wyzer.speech.model_copy(update={"voice": "Microsoft Zira Desktop"})}))
    report = preflight(ready_deps(), config)
    check = report.get("tts_voice")
    assert check.status is CheckStatus.WARN and "not Portuguese" in check.detail
    assert report.voice.culture == "pt-PT"


@pytest.mark.parametrize(
    ("raw", "count"),
    [
        ('[{"name":"Microsoft Helia Desktop","culture":"pt-PT","gender":"Female","enabled":true}]', 1),
        ('{"name":"Microsoft Maria Desktop","culture":"pt-BR","gender":"Female","enabled":true}', 1),
        ("[]", 0),
        ("", 0),
    ],
    ids=["list", "single_object", "empty_list", "empty_output"],
)
def test_inventory_parsing(raw: str, count: int) -> None:
    assert len(parse_inventory(raw)) == count


def test_voice_inventory_is_not_probed_outside_windows() -> None:
    def must_not_run():
        raise AssertionError("SAPI probed on non-Windows")

    report = preflight(ready_deps(platform="linux", voices=must_not_run))
    assert report.get("tts_voice").status is CheckStatus.SKIP


# ===================================================================== 4. Ollama


class FakeTransport:
    def __init__(self, *, error: Exception | None = None, models: list[str] | None = None) -> None:
        self.error = error
        self.models = models or []
        self.calls: list[tuple[str, str]] = []

    async def request(self, method, url, *, payload=None, headers=None, timeout_seconds=60):
        self.calls.append((method, url))
        if self.error is not None:
            raise self.error
        return JsonResponse(200, {"models": [{"name": name} for name in self.models]})


def _ollama_diagnose(transport: FakeTransport):
    async def diagnose(config):
        llm = config.wyzer.llm
        provider = OllamaChatProvider(
            str(llm.endpoint).rstrip("/"), llm.model, auto_start=llm.auto_start, transport=transport
        )
        return await provider.diagnose()

    return diagnose


@pytest.mark.parametrize(
    ("transport", "code"),
    [
        (FakeTransport(error=HttpTransportError("Connection refused")), "OLLAMA_UNREACHABLE"),
        (FakeTransport(models=["llama3.2:1b"]), "MODEL_NOT_INSTALLED"),
        (FakeTransport(models=[]), "MODEL_NOT_INSTALLED"),
        (FakeTransport(models=["qwen3.5:4b", "qwen3.5:2b"]), "LLM_MODEL_OK"),
    ],
    ids=["unreachable", "other_model", "no_models", "installed"],
)
def test_ollama_preflight_with_real_wyzer_provider(transport: FakeTransport, code: str) -> None:
    report = preflight(ready_deps(llm_diagnose=_ollama_diagnose(transport)))
    assert report.get("llm").code == code
    assert report.ready is (code == "LLM_MODEL_OK")
    # One read-only GET to the loopback /api/tags; Ollama is never started.
    assert transport.calls == [("GET", "http://127.0.0.1:11434/api/tags")]


def test_ollama_unavailable_blocks_voice_mode(tmp_path: Path) -> None:
    deps = ready_deps(llm_diagnose=_ollama_diagnose(FakeTransport(error=HttpTransportError("refused"))))
    result, *_ = runtime(tmp_path, stt=ScriptedStt(), provider=ScriptedProvider(), preflight_deps=deps)
    assert result.exit_code == EXIT_PREFLIGHT_BLOCKED
    assert result.report.blocking_codes == ["OLLAMA_UNREACHABLE"]


def test_model_disappearing_after_preflight_gives_fixed_portuguese_reply() -> None:
    # Ollama reachable at start, then the model call fails: PT sentence, no crash.
    async def run():
        from jarvis.brain.pt_provider import PortugueseProvider
        from jarvis.language.prompts import SAY_MODEL_UNAVAILABLE

        provider = PortugueseProvider(
            OllamaChatProvider("http://127.0.0.1:11434", "qwen3.5:4b",
                               transport=FakeTransport(error=HttpTransportError("model not found", status=404)))
        )
        response = await provider.chat([], [], None)
        return response.message.content, SAY_MODEL_UNAVAILABLE

    text, expected = asyncio.run(run())
    assert text == expected


# ===================================================================== 5/6. capture & STT failures


class RaisingStt:
    def __init__(self, error: Exception) -> None:
        self.error = error

    def listen(self, timeout_seconds: float):
        raise self.error


@pytest.mark.parametrize(
    ("error", "stage"),
    [
        (CaptureError("Microphone capture failed: device unavailable"), "capture"),
        (SpeechAdapterError("Whisper transcription failed: bad model"), "stt"),
        (RuntimeError("ctranslate2 crashed"), "stt"),
    ],
    ids=["capture", "whisper", "unexpected"],
)
def test_capture_and_stt_failures_are_not_silence(error: Exception, stage: str) -> None:
    rig = make_rig()
    rig.session.stt = RaisingStt(error)
    result = asyncio.run(rig.session.voice_turn())[0]
    assert result.outcome is TurnOutcome.STT_FAILED and result.detail == stage
    errors = [e for e in rig.sink.events if e.state is VoiceState.ERROR]
    assert errors and errors[-1].detail.startswith(f"{stage}_")
    assert rig.session.state is VoiceState.IDLE
    assert rig.provider.requests == []


def test_stt_failure_while_awaiting_confirmation_cancels_it() -> None:
    rig = make_rig()
    rig.provider.push(call("open_allowed_application", {"app": "calculator"}), say("Abri."))
    asyncio.run(rig.session.handle_text("abre a calculadora"))
    assert rig.pending is not None
    rig.session.stt = RaisingStt(CaptureError("device unplugged"))
    result = asyncio.run(rig.session.voice_turn())[0]
    assert result.outcome is TurnOutcome.STT_FAILED
    assert rig.pending is None
    rig.session.stt = ScriptedStt(["sim"])
    assert asyncio.run(rig.session.voice_turn())[0].intended is TurnOutcome.NOTHING_TO_CONFIRM
    assert rig.launcher.requested == []


def test_real_whisper_adapter_maps_capture_failure_to_capture_error(tmp_path: Path) -> None:
    def broken_capture(_timeout):
        raise CaptureError("Microphone capture failed")

    stt = create_voice_input(
        slice_config().wyzer.speech.model_copy(update={"whisper_download_root": tmp_path}),
        SimpleNamespace(capture=broken_capture),
        model_factory=lambda *a, **k: pytest.fail("model must not load before audio exists"),
    )
    with pytest.raises(CaptureError):
        stt.listen(1)


# ===================================================================== 7. TTS failure


def test_tts_failure_in_voice_runtime_is_reported_and_recovers(tmp_path: Path) -> None:
    provider = ScriptedProvider([say("Olá."), say("Olá outra vez.")])
    tts = FailingTts(SpeechPlaybackError("device lost"), fail_calls={1})
    result, *_ = runtime(
        tmp_path, stt=ScriptedStt(["olá", "olá"]), provider=provider, tts=tts, lines=["", "", None]
    )
    assert [t["outcome"] for t in result.turns] == ["tts_failed", "answered"]
    assert tts.spoken == ["Olá outra vez."]


# ===================================================================== 8. cancel during recognition


class BlockingStt:
    """Simulates a capture in progress; returns speech only after being released."""

    def __init__(self, text: str) -> None:
        self.text = text
        self.started = threading.Event()
        self.release = threading.Event()
        self.cancelled = 0

    def listen(self, timeout_seconds: float):
        self.started.set()
        self.release.wait(5)
        return Transcript(self.text, 0.9)

    def cancel(self) -> None:
        self.cancelled += 1
        self.release.set()


def test_cancel_during_recognition_discards_the_utterance() -> None:
    rig = make_rig()
    stt = BlockingStt("abre a calculadora")
    rig.session.stt = stt
    rig.provider.push(call("open_allowed_application", {"app": "calculator"}), say("Abri."))

    async def run():
        turn = asyncio.create_task(rig.session.voice_turn())
        await asyncio.to_thread(stt.started.wait, 5)
        rig.session.cancel(reason="test")
        return await turn

    results = asyncio.run(run())
    assert [r.outcome for r in results] == [TurnOutcome.DISCARDED]
    assert stt.cancelled == 1  # the adapter was told to abandon the capture
    assert rig.provider.requests == [] and rig.pending is None
    assert rig.tts.spoken == [] and rig.session.state is VoiceState.IDLE


def test_cancellable_capture_discards_audio_across_cancel_and_refuses_after_close() -> None:
    gate = threading.Event()
    inner = SimpleNamespace(capture=lambda t: (gate.wait(5), b"\x01\x02")[1])
    capture = CancellableCapture(inner)
    out: list = []
    worker = threading.Thread(target=lambda: out.append(capture.capture(1)))
    worker.start()
    capture.cancel()
    gate.set()
    worker.join(2)
    assert out == [None]
    gate.set()
    assert capture.capture(1) == b"\x01\x02"  # a fresh capture after cancel works
    capture.close()
    with pytest.raises(CaptureError):
        capture.capture(1)


def test_shutdown_closes_the_capture_adapter(tmp_path: Path) -> None:
    closed: list[str] = []

    class ClosingStt(ScriptedStt):
        def close(self) -> None:
            closed.append("stt")

    runtime(tmp_path, stt=ClosingStt([]), provider=ScriptedProvider(), lines=[None])
    assert closed == ["stt"]


# ===================================================================== 9. late response


def test_late_model_response_after_cancel_in_voice_turn() -> None:
    provider = StubbornProvider([call("open_allowed_application", {"app": "notepad"})], delay=0.2)
    rig = make_rig(provider=provider)
    rig.session.stt = ScriptedStt(["abre o bloco de notas", "sim"])

    async def run():
        turn = asyncio.create_task(rig.session.voice_turn())
        await provider.started.wait()
        rig.session.cancel()
        return await turn

    results = asyncio.run(run())
    assert [r.outcome for r in results] == [TurnOutcome.DISCARDED]
    assert rig.pending is None and rig.launcher.requested == []


# ===================================================================== 10. unpresented confirmation


def test_unpresented_confirmation_in_voice_runtime(tmp_path: Path) -> None:
    provider = ScriptedProvider([call("open_allowed_application", {"app": "calculator"}), say("Abri.")])
    result, *_ = runtime(
        tmp_path,
        stt=ScriptedStt(["abre a calculadora", "sim"]),
        provider=provider,
        tts=FailingTts(SpeechPlaybackError("device lost")),
    )
    assert [t["outcome"] for t in result.turns] == ["confirmation_not_presented"]
    assert result.launcher.requested == []


# ===================================================================== 11. Windows tools disabled


def test_voice_runtime_always_uses_the_simulated_launcher(tmp_path: Path) -> None:
    provider = ScriptedProvider([call("open_allowed_application", {"app": "calculator"}), say("Abri.")])
    result, _deps, _sink, tts, _ = runtime(
        tmp_path, stt=ScriptedStt(["abre a calculadora", "sim"]), provider=provider
    )
    assert isinstance(result.launcher, SimulatedLauncher)
    assert result.launcher.requested == ["calculator"]
    assert [t["action_status"] for t in result.turns] == [None, "SIMULATED"]
    assert tts.spoken[-1].startswith("Modo de simulação")


def test_real_windows_actions_flag_blocks_voice_mode(tmp_path: Path) -> None:
    config = slice_config()
    config = replace(config, vexel=config.vexel.model_copy(update={"allow_real_windows_actions": True}))
    result, *_ = runtime(tmp_path, stt=ScriptedStt(), provider=ScriptedProvider(), config=config)
    assert result.exit_code == EXIT_PREFLIGHT_BLOCKED
    assert "REAL_ACTIONS_NOT_ALLOWED" in result.report.blocking_codes


def test_console_cancel_and_quit_commands(tmp_path: Path) -> None:
    result, _d, sink, tts, _ = runtime(
        tmp_path, stt=ScriptedStt(), provider=ScriptedProvider(), lines=["c", "q"]
    )
    assert result.exit_code == EXIT_OK and result.turns == []
    assert sink.states[-1] is VoiceState.OFFLINE


# ===================================================================== default wiring


def test_default_factories_construct_without_loading_or_spawning(tmp_path: Path) -> None:
    import sys

    from jarvis.runtime.voice_mode import _default_provider, _default_stt, _default_tts, default_log_directory

    config = slice_config()
    before = set(sys.modules)
    stt = _default_stt(config, CancellableCapture(SimpleNamespace(capture=lambda t: None)))
    tts = _default_tts(config, "Microsoft Helia Desktop")
    provider = _default_provider(config)
    loaded = set(sys.modules) - before
    assert not {"faster_whisper", "ctranslate2", "sounddevice", "numpy", "kokoro", "torch"} & loaded
    assert type(tts).__name__ == "WindowsSpeechSynthesizer" and tts.voice == "Microsoft Helia Desktop"
    assert stt.listen(1) is None  # silent capture → no model load, no transcript
    assert provider.inner.auto_start is False  # Jarvis never starts Ollama
    assert default_log_directory(config).parts[-3:] == (".wyzer", "vexel", "logs")
    configured = replace(config, vexel=config.vexel.model_copy(update={"log_directory": str(tmp_path)}))
    assert default_log_directory(configured) == tmp_path
