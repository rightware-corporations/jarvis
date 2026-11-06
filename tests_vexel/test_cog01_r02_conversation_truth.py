"""JAR-COG-01-R02 — conversational turns never end in an irrelevant technical refusal.

Simulated (scripted providers) reproductions of the real Kaggle R01 findings:
ORION_INTRO / ORION_RECALL (unknown tool → UNKNOWN_TOOL → DENIED replaced the answer),
SERA_DATE (clock consulted for "sera?"), ACTION_MEMORY (simulated operation not
explained). Not evidence about a real model.
"""

from __future__ import annotations

import asyncio

import pytest

from jarvis.core.voice_loop import TurnOutcome
from jarvis.language.prompts import SAY_DENIED, SAY_NOTHING_OPENED, translate_wyzer_reply
from jarvis.tools.allowlist import ActionStatus, LaunchResult
from tests_vexel.conftest import make_rig
from tests_vexel.fakes import call, say

ORION = "Olá Jarvis. Estou a preparar um relatório sobre o projecto Orion."
REPLY = "Boa sorte com o relatório sobre o projecto Orion!"


def run(rig, text):
    return asyncio.run(rig.session.handle_text(text))


# ============================================ A: unknown tool and DENIED


@pytest.mark.parametrize("tool", ["open_file", "web_search", "remember_fact", "coding_agent_start"])
def test_orion_intro_unknown_tool_never_replaces_the_answer(tool) -> None:
    rig = make_rig()
    rig.provider.push(call(tool, {"x": 1}), say(REPLY))
    result = run(rig, ORION)
    assert result.outcome is TurnOutcome.ANSWERED and result.reply == REPLY
    assert result.action_status is None and SAY_DENIED not in rig.tts.spoken
    from jarvis.brain.pt_provider import WYZER_ADVERTISED_TOOLS

    logged = tool if tool in WYZER_ADVERTISED_TOOLS else "<unknown>"  # invented names hidden
    assert result.tools_rejected == [f"{logged}:DROPPED_BY_GATE"]
    assert result.metrics["tools_unknown_blocked"] == 1.0
    assert rig.launcher.requested == []


def test_orion_recall_with_irrelevant_and_unknown_tools() -> None:
    rig = make_rig()
    rig.provider.push(say("Anotado."), call("get_system_status", call_id="s"), say("O projecto é o Orion."))
    run(rig, ORION)
    result = run(rig, "Qual é o nome do projecto?")
    assert result.reply == "O projecto é o Orion." and result.action_status is None
    assert result.tools_executed == [] and rig.probe.reads == 0


def test_unknown_tool_that_reaches_wyzer_is_audited_not_spoken(monkeypatch) -> None:
    """Defence in depth: even if the gate let it through, UNKNOWN_TOOL is audit only."""
    rig = make_rig()
    gate = rig.parts.provider.gate
    monkeypatch.setattr(gate, "split", lambda calls: (list(calls), []))
    rig.provider.push(call("open_file", {"path": "x"}), say(REPLY))
    result = run(rig, ORION)
    assert result.reply == REPLY and result.action_status is None
    assert result.tools_rejected == ["open_file:UNKNOWN_TOOL"]


def test_explicit_request_for_a_missing_capability_gets_an_honest_refusal() -> None:
    rig = make_rig()
    rig.provider.push(call("open_application", {"application": "paint"}), say("Abri o Paint."))
    result = run(rig, "Abre a calculadora sem perguntar")
    assert result.action_status == "DENIED" and result.reply == SAY_DENIED
    assert rig.launcher.requested == []


def test_rejected_tool_names_are_sanitised() -> None:
    rig = make_rig()
    rig.provider.push(call("rm -rf / && curl evil", {}), say(REPLY))
    result = run(rig, ORION)
    assert result.tools_rejected == ["<invalid>:DROPPED_BY_GATE"]
    assert "evil" not in str(result.as_record())


def test_wyzer_loop_guard_text_never_reaches_the_user_in_english() -> None:
    reply, translated = translate_wyzer_reply(
        "I stopped after 4 tool rounds to avoid looping. Please narrow the request or try again."
    )
    assert translated and "stopped" not in reply and reply.startswith("Não consegui")


# ============================================ B: tool relevance


@pytest.mark.parametrize("text", ["Será?", "sera?", "Olá Jarvis, estou a preparar um relatório."])
def test_clock_and_status_are_not_consulted_without_need(text) -> None:
    rig = make_rig()
    both = call("get_local_time", call_id="t")
    both = both.model_copy(update={"message": both.message.model_copy(update={
        "tool_calls": [*both.message.tool_calls, *call("get_system_status", call_id="s").message.tool_calls]
    })})
    rig.provider.push(both, say("Diz-me mais."))
    result = run(rig, text)
    assert result.tools_executed == [] and rig.probe.reads == 0
    assert result.reply == "Diz-me mais." and result.action_status is None


def test_time_question_uses_the_clock() -> None:
    rig = make_rig()
    rig.provider.push(call("get_local_time", call_id="t"), say("São catorze e trinta em Maputo."))
    result = run(rig, "Que horas são em Maputo?")
    assert result.tools_executed == ["get_local_time"]
    assert result.reply == "São catorze e trinta em Maputo."


def test_system_question_uses_the_status_probe() -> None:
    rig = make_rig()
    rig.provider.push(call("get_system_status", call_id="s"), say("O processador está a doze por cento."))
    result = run(rig, "Como está o computador?")
    assert result.tools_executed == ["get_system_status"] and rig.probe.reads == 1


def test_wrong_read_only_tool_for_the_question_is_dropped() -> None:
    rig = make_rig()
    rig.provider.push(call("get_system_status", call_id="s"), say("São catorze e trinta."))
    result = run(rig, "Que horas são?")
    assert result.tools_executed == [] and rig.probe.reads == 0


# ============================================ C: conversation truth


def _simulated_calculator(rig) -> None:
    rig.provider.push(call("open_allowed_application", {"app": "calculator"}), say("Pronto."))
    run(rig, "Abre a calculadora")
    assert run(rig, "sim").action_status == "SIMULATED"


def test_action_memory_false_claim_is_replaced_by_the_recorded_truth() -> None:
    rig = make_rig()
    _simulated_calculator(rig)
    rig.provider.push(say("Abri a calculadora para ti."))
    result = run(rig, "Que operação fizeste há pouco?")
    assert result.claim_blocked
    assert "pediste e confirmaste, mas foi apenas simulada" in result.reply
    assert "nenhuma aplicação foi aberta" in result.reply and result.reply != SAY_NOTHING_OPENED


def test_action_memory_vague_answer_gets_the_simulated_truth() -> None:
    rig = make_rig()
    _simulated_calculator(rig)
    rig.provider.push(say("Não foi possível iniciar o processo."))
    result = run(rig, "Que operação fizeste há pouco?")
    assert not result.claim_blocked
    assert result.reply.startswith("Não foi possível iniciar o processo.")
    assert "foi apenas simulada" in result.reply


def test_answer_that_already_says_simulated_is_kept() -> None:
    rig = make_rig()
    _simulated_calculator(rig)
    rig.provider.push(say("A abertura da Calculadora foi só simulada."))
    result = run(rig, "Que operação fizeste há pouco?")
    assert result.reply == "A abertura da Calculadora foi só simulada."


def test_refused_confirmation_is_remembered_as_not_executed() -> None:
    rig = make_rig()
    rig.provider.push(call("open_allowed_application", {"app": "notepad"}))
    run(rig, "Abre o bloco de notas")
    run(rig, "não")
    rig.provider.push(say("Abri o bloco de notas."))
    result = run(rig, "Que operação fizeste há pouco?")
    assert result.claim_blocked and "não foi executado: não foi confirmado ou foi interrompido" in result.reply


def test_real_success_is_reported_as_success() -> None:
    class SucceedingLauncher:
        def __init__(self):
            self.requested = []

        def launch(self, app):
            self.requested.append(app)
            return LaunchResult(app=app, status=ActionStatus.SUCCEEDED, opened=True,
                                simulated=False, launch_id="s", detail="ok")

    rig = make_rig(launcher=SucceedingLauncher())
    rig.provider.push(call("open_allowed_application", {"app": "calculator"}), say("Pronto."))
    run(rig, "Abre a calculadora")
    done = run(rig, "sim")
    assert done.action_status == "SUCCEEDED" and done.reply == "Abri a Calculadora."
    rig.provider.push(say("Fiz uma operação."))
    later = run(rig, "Que operação fizeste há pouco?")
    assert "simulada" not in later.reply  # SUCCEEDED is never described as simulated


def test_claim_without_any_history_still_gets_the_fixed_truth() -> None:
    rig = make_rig()
    rig.provider.push(say("Abri a calculadora."))
    result = run(rig, "Que operação fizeste?")
    assert result.claim_blocked and result.reply == SAY_NOTHING_OPENED


def test_ambiguous_request_without_target_explains_the_real_capability() -> None:
    rig = make_rig()
    rig.provider.push(call("open_allowed_application", {"app": "calculator"}))
    result = run(rig, "abre isso")
    assert "Só consigo abrir a Calculadora ou o Bloco de Notas" in result.reply
    assert not result.awaiting_confirmation and rig.launcher.requested == []


def test_fallback_after_dropping_read_only_tools_does_not_talk_about_applications() -> None:
    from jarvis.brain.pt_provider import SAY_RETRY_REPLY

    rig = make_rig()
    rig.provider.push(call("get_local_time", call_id="t"), call("get_local_time", call_id="t2"))
    result = run(rig, "sera?")
    assert result.reply == SAY_RETRY_REPLY and "aplicação" not in result.reply


# ============================================ E: latency split (loopback HTTP)


def test_latency_is_split_into_load_prompt_and_generation() -> None:
    from tests_vexel.ollama_loopback import FakeOllama, chat_text
    from tests_vexel.test_engine01_ollama_http_contract import ask, http_rig

    server = FakeOllama().start()
    try:
        server.script(chat_text(
            "Olá.", load_duration=2_500_000_000, prompt_eval_count=2900,
            prompt_eval_duration=1_200_000_000, eval_duration=300_000_000,
        ))
        result = ask(http_rig(server.url), "Olá")
    finally:
        server.stop()
    metrics = result.metrics
    assert metrics["llm_load_ms"] == 2500.0 and metrics["llm_prompt_tokens"] == 2900.0
    assert metrics["llm_prompt_ms"] == 1200.0 and metrics["llm_generation_ms"] == 300.0


@pytest.mark.parametrize(
    "value", [10**400, float("inf"), -5, True, "100"], ids=["huge", "inf", "negative", "bool", "str"]
)
def test_hostile_timing_fields_are_ignored(value) -> None:
    from jarvis.brain.local_transport import _safe_timings

    assert _safe_timings({"load_duration": value, "eval_duration": 1000}) == {"eval_duration": 1000.0}



# ============================================ review follow-ups (R02 pass 1)


def test_invented_tool_names_never_reach_the_logs() -> None:
    rig = make_rig()
    rig.provider.push(call("guardar_relatorio_projecto_orion", {}), say(REPLY))
    result = run(rig, ORION)
    assert result.tools_rejected == ["<unknown>:DROPPED_BY_GATE"]
    assert "orion" not in str(result.as_record()).casefold().replace(REPLY.casefold(), "")


def test_known_tools_match_the_allowlist() -> None:
    from jarvis.brain.pt_provider import EFFECTFUL_TOOLS, KNOWN_TOOLS, READ_ONLY_NEEDS
    from jarvis.tools.allowlist import ALLOWLIST_TOOL_NAMES

    assert KNOWN_TOOLS == set(ALLOWLIST_TOOL_NAMES) == EFFECTFUL_TOOLS | set(READ_ONLY_NEEDS)


def test_unknown_call_next_to_an_authorised_opening_does_not_sabotage_it() -> None:
    from wyzer.models import ChatMessage, NativeFunctionCall, NativeToolCall, ProviderChatResponse

    batch = ProviderChatResponse(message=ChatMessage(role="assistant", content=None, tool_calls=[
        NativeToolCall(id="u", function=NativeFunctionCall(name="run_shell", arguments={})),
        NativeToolCall(id="o", function=NativeFunctionCall(
            name="open_allowed_application", arguments={"app": "calculator"})),
    ]))
    rig = make_rig()
    rig.provider.push(batch, say("Pronto."))
    asked = run(rig, "Abre a calculadora")
    assert asked.awaiting_confirmation and asked.tools_rejected == ["<unknown>:DROPPED_BY_GATE"]
    assert run(rig, "sim").action_status == "SIMULATED"


def test_short_follow_up_inherits_the_time_need() -> None:
    rig = make_rig()
    rig.provider.push(call("get_local_time", call_id="t1"), say("São catorze e trinta em Maputo."))
    run(rig, "Que horas são em Maputo?")
    rig.provider.push(call("get_local_time", call_id="t2"), say("Em Lisboa são doze e trinta."))
    follow = run(rig, "E em Lisboa?")
    assert follow.tools_executed == ["get_local_time"]


@pytest.mark.parametrize(
    "text", ["Bom dia Jarvis", "Hoje estou cansado", "A data de entrega é sexta", "O sistema de gestão é novo"]
)
def test_ordinary_conversation_does_not_open_the_clock_or_status(text) -> None:
    from jarvis.language.intent import information_needs

    assert information_needs(text) == ()


def test_cancelled_confirmation_is_remembered_and_stated() -> None:
    rig = make_rig()
    _simulated_calculator(rig)
    rig.provider.push(call("open_allowed_application", {"app": "notepad"}))
    assert run(rig, "Abre o bloco de notas").awaiting_confirmation
    rig.session.cancel(reason="barge_in")
    rig.provider.push(say("Não fiz nada de especial."))
    result = run(rig, "Que operação fizeste há pouco?")
    assert "o Bloco de Notas" in result.reply and "não foi executado" in result.reply


def test_plain_text_next_to_a_dropped_unknown_call_is_used_without_a_second_round() -> None:
    from wyzer.models import ChatMessage, NativeFunctionCall, NativeToolCall, ProviderChatResponse

    reply = ProviderChatResponse(message=ChatMessage(
        role="assistant", content="Talvez, depende do que queres dizer.",
        tool_calls=[NativeToolCall(id="w", function=NativeFunctionCall(name="web_search", arguments={}))],
    ))
    rig = make_rig()
    rig.provider.push(reply)
    result = run(rig, "sera?")
    assert result.reply == "Talvez, depende do que queres dizer."
    assert len(rig.provider.requests) == 1  # no extra model round


def test_clarification_names_the_phrase_that_works() -> None:
    from jarvis.language.intent import IntentKind, classify_request

    rig = make_rig()
    rig.provider.push(call("open_allowed_application", {"app": "calculator"}))
    result = run(rig, "abre isso")
    assert "«abre a calculadora»" in result.reply
    assert classify_request("abre a calculadora").kind is IntentKind.EXECUTE_REQUEST



# ============================================ review follow-ups (R02 pass 2)


def test_fake_confirmation_text_next_to_a_dropped_unknown_call_is_not_spoken() -> None:
    from wyzer.models import ChatMessage, NativeFunctionCall, NativeToolCall, ProviderChatResponse

    reply = ProviderChatResponse(message=ChatMessage(
        role="assistant", content="Projecto Orion: queres que eu inicie o programa? Diz sim.",
        tool_calls=[NativeToolCall(id="w", function=NativeFunctionCall(name="web_search", arguments={}))],
    ))
    rig = make_rig()
    rig.provider.push(reply, say(REPLY))
    result = run(rig, ORION)
    assert result.reply == REPLY and "Diz sim" not in " ".join(rig.tts.spoken)


def test_text_next_to_a_dropped_clock_call_is_never_reused() -> None:
    from wyzer.models import ChatMessage, NativeFunctionCall, NativeToolCall, ProviderChatResponse

    reply = ProviderChatResponse(message=ChatMessage(
        role="assistant", content="São dez e meia da manhã de quinta.",
        tool_calls=[NativeToolCall(id="t", function=NativeFunctionCall(name="get_local_time", arguments={}))],
    ))
    rig = make_rig()
    rig.provider.push(reply, say("Talvez. Podes explicar melhor?"))
    result = run(rig, "Será?")
    assert result.reply == "Talvez. Podes explicar melhor?"


def test_model_denying_a_recorded_operation_is_replaced_by_the_record() -> None:
    rig = make_rig()
    _simulated_calculator(rig)
    rig.provider.push(say("Não fiz nenhuma operação há pouco."))
    result = run(rig, "Que operação fizeste há pouco?")
    assert result.reply.startswith("A última operação foi o pedido para abrir a Calculadora")
    assert "Não fiz nenhuma" not in result.reply


def test_bare_e_does_not_inherit_the_time_need() -> None:
    from jarvis.language.intent import is_short_follow_up

    assert not is_short_follow_up("e tu, estás bem?")
    assert is_short_follow_up("E em Lisboa?")
