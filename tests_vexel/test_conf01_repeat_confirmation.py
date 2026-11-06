"""JAR-CONF-01 — a confirmed call runs once; a model repeat never loops or re-runs it.

Observed with a real qwen3.5:2b (JAR-INFER-01/B5, CALCULATOR_APPROVE): after ``sim`` the
Orchestrator ran the approved call (SIMULATED) and asked the model again; the model
re-requested the same ``open_allowed_application`` and a second confirmation was
spoken instead of the result. Reproduced here with scripted providers (simulated) and
once over loopback HTTP with Wyzer's real Ollama client.
"""

from __future__ import annotations

import asyncio
import time

import pytest

from wyzer.models import ChatMessage, NativeFunctionCall, NativeToolCall, ProviderChatResponse

from jarvis.core.voice_loop import TurnOutcome
from jarvis.language.prompts import SAY_CANCELLED, SAY_CANCELLED_UNCLEAR
from jarvis.tools.allowlist import ActionStatus, LaunchResult
from jarvis.ui.events import VoiceState
from tests_vexel.conftest import make_rig
from tests_vexel.fakes import call, say
from tests_vexel.ollama_loopback import FakeOllama, chat_tool
from tests_vexel.test_engine01_ollama_http_contract import ask, http_rig

CALC = {"app": "calculator"}
NOTEPAD = {"app": "notepad"}
SIMULATED_CALC = "Modo de simulação: não abri a Calculadora. Nenhuma aplicação foi iniciada."
ASK_CALC = "Queres que eu abra a Calculadora? Responde sim ou não."
ASK_NOTEPAD = "Queres que eu abra o Bloco de Notas? Responde sim ou não."


def run(rig, text):
    return asyncio.run(rig.session.handle_text(text))


def awaiting_count(rig) -> int:
    return rig.sink.states.count(VoiceState.AWAITING_CONFIRMATION)


def open_app(arguments: dict, call_id: str = "c1") -> ProviderChatResponse:
    return call("open_allowed_application", arguments, call_id=call_id)


def calls(*arguments: dict) -> ProviderChatResponse:
    """One model reply with several open_allowed_application calls."""
    return ProviderChatResponse(
        message=ChatMessage(
            role="assistant",
            content=None,
            tool_calls=[
                NativeToolCall(
                    id=f"b{index}",
                    function=NativeFunctionCall(name="open_allowed_application", arguments=args),
                )
                for index, args in enumerate(arguments)
            ],
        )
    )


class FailingLauncher:
    def __init__(self) -> None:
        self.requested: list[str] = []

    def launch(self, app):
        self.requested.append(app)
        return LaunchResult(
            app=app,
            status=ActionStatus.FAILED,
            opened=False,
            simulated=False,
            launch_id="x",
            detail="failed",
        )


# ------------------------------------------------------------- single approval


def test_approved_once_then_model_answers_without_new_tool() -> None:
    rig = make_rig()
    rig.provider.push(open_app(CALC), say("Pronto."))
    assert run(rig, "Abre a calculadora").outcome is TurnOutcome.CONFIRMATION_REQUESTED
    done = run(rig, "sim")
    assert done.outcome is TurnOutcome.CONFIRMED and done.action_status == "SIMULATED"
    assert done.reply == SIMULATED_CALC and rig.launcher.requested == ["calculator"]
    assert "repeat_call_dropped" not in done.metrics


def test_b5_exact_repeat_after_execution_is_dropped_not_reconfirmed() -> None:
    rig = make_rig()
    rig.provider.push(open_app(CALC), open_app(CALC, "c2"))  # c2: the qwen3.5:2b repeat
    run(rig, "Abre a calculadora")
    done = run(rig, "sim")

    assert done.outcome is TurnOutcome.CONFIRMED and not done.awaiting_confirmation
    assert done.action_status == "SIMULATED" and done.reply == SIMULATED_CALC
    assert done.metrics["repeat_call_dropped"] == 1.0
    assert rig.launcher.requested == ["calculator"]  # executed exactly once
    assert rig.pending is None
    assert awaiting_count(rig) == 1  # no second confirmation question
    assert rig.tts.spoken == [ASK_CALC, SIMULATED_CALC]
    # The dropped repeat can never be approved later: "sim" now confirms nothing.
    assert run(rig, "sim").outcome is TurnOutcome.NOTHING_TO_CONFIRM
    assert rig.launcher.requested == ["calculator"]


def test_repeated_twice_in_one_reply_still_runs_once() -> None:
    rig = make_rig()
    rig.provider.push(open_app(CALC), calls(CALC, CALC))
    run(rig, "Abre a calculadora")
    done = run(rig, "sim")
    assert done.action_status == "SIMULATED" and rig.launcher.requested == ["calculator"]
    assert rig.pending is None and run(rig, "sim").outcome is TurnOutcome.NOTHING_TO_CONFIRM
    assert rig.launcher.requested == ["calculator"]


def test_repeat_after_failed_launch_does_not_loop() -> None:
    launcher = FailingLauncher()
    rig = make_rig(launcher=launcher)
    rig.provider.push(open_app(CALC), open_app(CALC, "c2"))
    run(rig, "Abre a calculadora")
    done = run(rig, "sim")
    assert done.action_status == "FAILED" and done.reply == "Não consegui abrir a Calculadora."
    assert launcher.requested == ["calculator"] and rig.pending is None


# -------------------------------------------- different calls keep their policy


def test_model_asks_for_another_application_needs_its_own_confirmation() -> None:
    rig = make_rig()
    rig.provider.push(open_app(CALC), open_app(NOTEPAD, "c2"))
    run(rig, "Abre a calculadora")
    second = run(rig, "sim")

    assert second.outcome is TurnOutcome.CONFIRMATION_REQUESTED and second.awaiting_confirmation
    assert second.action_status == "SIMULATED"  # the first call's real result is kept
    assert second.reply == f"{SIMULATED_CALC} {ASK_NOTEPAD}"
    assert rig.launcher.requested == ["calculator"]  # notepad not auto-approved
    assert rig.pending is not None and rig.pending.arguments == NOTEPAD

    rig.provider.push(say("Feito."))
    third = run(rig, "sim")
    assert third.outcome is TurnOutcome.CONFIRMED and third.action_status == "SIMULATED"
    assert rig.launcher.requested == ["calculator", "notepad"]


def test_another_application_can_be_refused_without_affecting_the_first() -> None:
    rig = make_rig()
    rig.provider.push(open_app(CALC), open_app(NOTEPAD, "c2"))
    run(rig, "Abre a calculadora")
    run(rig, "sim")
    refused = run(rig, "não")
    assert refused.outcome is TurnOutcome.REJECTED and rig.launcher.requested == ["calculator"]


def test_model_alters_arguments_after_execution() -> None:
    rig = make_rig()
    rig.provider.push(
        open_app(CALC),
        open_app({"app": "calculator", "path": "C:\\evil.exe"}, "c2"),
        say("Abri."),
    )
    run(rig, "Abre a calculadora")
    done = run(rig, "sim")
    # The altered call is refused by validation; the confirmed call's result is reported.
    assert done.outcome is TurnOutcome.CONFIRMED and done.action_status == "SIMULATED"
    assert done.reply == SIMULATED_CALC
    assert rig.launcher.requested == ["calculator"] and rig.pending is None


def test_ping_pong_between_applications_never_runs_one_twice() -> None:
    rig = make_rig()
    rig.provider.push(open_app(CALC), open_app(NOTEPAD, "c2"), open_app(CALC, "c3"))
    run(rig, "Abre a calculadora")
    assert run(rig, "sim").outcome is TurnOutcome.CONFIRMATION_REQUESTED  # notepad asked
    done = run(rig, "sim")
    assert done.outcome is TurnOutcome.CONFIRMED and done.metrics["repeat_call_dropped"] == 1.0
    assert done.action_status == "SIMULATED"
    assert rig.launcher.requested == ["calculator", "notepad"]
    assert rig.pending is None and awaiting_count(rig) == 2
    assert run(rig, "sim").outcome is TurnOutcome.NOTHING_TO_CONFIRM


def test_batched_continuation_repeat_is_dropped() -> None:
    rig = make_rig()
    rig.provider.push(open_app(CALC), calls(NOTEPAD, CALC))
    run(rig, "Abre a calculadora")
    assert run(rig, "sim").outcome is TurnOutcome.CONFIRMATION_REQUESTED  # notepad
    done = run(rig, "sim")  # notepad runs; the calc continuation is a repeat
    assert done.action_status == "SIMULATED" and done.metrics["repeat_call_dropped"] == 1.0
    assert rig.launcher.requested == ["calculator", "notepad"] and rig.pending is None


def test_prefix_reports_the_confirmed_result_not_a_later_refusal() -> None:
    rig = make_rig()
    rig.provider.push(
        open_app(CALC),
        calls({"app": "calculator", "path": "x"}),  # DENIED by validation
        open_app(NOTEPAD, "c3"),
    )
    run(rig, "Abre a calculadora")
    second = run(rig, "sim")
    assert second.outcome is TurnOutcome.CONFIRMATION_REQUESTED
    assert second.action_status == "SIMULATED"
    assert second.reply == f"{SIMULATED_CALC} {ASK_NOTEPAD}"


def test_repeat_with_continuation_fails_closed() -> None:
    rig = make_rig()
    rig.provider.push(open_app(CALC), calls(CALC, NOTEPAD))
    run(rig, "Abre a calculadora")
    done = run(rig, "sim")
    # The repeat is dropped with its continuation: notepad is neither run nor approved.
    assert done.outcome is TurnOutcome.CONFIRMED and done.action_status == "SIMULATED"
    assert rig.launcher.requested == ["calculator"] and rig.pending is None


# ------------------------------------------------- refusals keep working


@pytest.mark.parametrize(
    ("answer", "outcome", "spoken"),
    [
        ("não", TurnOutcome.REJECTED, SAY_CANCELLED),
        ("talvez", TurnOutcome.CANCELLED_UNCLEAR, SAY_CANCELLED_UNCLEAR),
    ],
)
def test_negation_or_ambiguous_answer_runs_nothing(answer, outcome, spoken) -> None:
    rig = make_rig()
    rig.provider.push(open_app(CALC), open_app(CALC, "c2"))
    run(rig, "Abre a calculadora")
    result = run(rig, answer)
    assert result.outcome is outcome and rig.tts.spoken[-1] == spoken
    assert rig.launcher.requested == [] and rig.pending is None
    assert len(rig.provider.requests) == 1  # the refusal never reaches the model


def test_expired_confirmation_runs_nothing() -> None:
    rig = make_rig(ttl=0.05)
    rig.provider.push(open_app(CALC), open_app(CALC, "c2"))
    run(rig, "Abre a calculadora")
    time.sleep(0.1)
    result = run(rig, "sim")
    assert result.outcome is TurnOutcome.CANCELLED_NO_RESPONSE and result.action_status is None
    assert rig.launcher.requested == [] and rig.pending is None


def test_cancel_while_awaiting_runs_nothing() -> None:
    rig = make_rig()
    rig.provider.push(open_app(CALC))
    run(rig, "Abre a calculadora")
    assert run(rig, "cancela").outcome is TurnOutcome.REJECTED
    assert rig.launcher.requested == []
    assert run(rig, "sim").outcome is TurnOutcome.NOTHING_TO_CONFIRM


def test_no_result_recorded_means_no_repeat_rule_and_no_execution() -> None:
    """A pending call with nothing executed in the turn is never dropped as a 'repeat'."""
    rig = make_rig()
    rig.provider.push(open_app(CALC))
    first = run(rig, "Abre a calculadora")
    assert first.outcome is TurnOutcome.CONFIRMATION_REQUESTED and first.action_status is None
    assert "repeat_call_dropped" not in first.metrics and rig.launcher.requested == []


# ------------------------------------------- independent turns never inherit


def test_two_legitimate_requests_in_independent_turns_each_need_confirmation() -> None:
    rig = make_rig()
    rig.provider.push(open_app(CALC), say("Pronto."))
    run(rig, "Abre a calculadora")
    assert run(rig, "sim").action_status == "SIMULATED"

    rig.provider.push(open_app(CALC, "c3"), say("Pronto."))
    again = run(rig, "Abre a calculadora outra vez")
    assert again.outcome is TurnOutcome.CONFIRMATION_REQUESTED  # not inherited
    assert rig.launcher.requested == ["calculator"]
    assert run(rig, "sim").action_status == "SIMULATED"
    assert rig.launcher.requested == ["calculator", "calculator"]
    assert awaiting_count(rig) == 2


def test_read_only_tool_after_confirmed_action_keeps_its_policy() -> None:
    rig = make_rig()
    rig.provider.push(
        open_app(CALC), call("get_local_time", call_id="c2"), say("São catorze e trinta.")
    )
    run(rig, "Abre a calculadora e diz as horas")
    done = run(rig, "sim")
    assert done.outcome is TurnOutcome.CONFIRMED and done.action_status == "SIMULATED"
    assert rig.launcher.requested == ["calculator"] and rig.pending is None


def test_drop_closes_the_orchestrator_action() -> None:
    rig = make_rig()
    rig.provider.push(open_app(CALC), open_app(CALC, "c2"), say("São catorze e trinta."))
    run(rig, "Abre a calculadora")
    run(rig, "sim")
    orchestrator = rig.parts.orchestrator
    assert orchestrator._active_action is None and not orchestrator._interrupted
    assert orchestrator.world.snapshot().pending_confirmation is None
    following = run(rig, "Que horas são?")
    assert following.outcome is TurnOutcome.ANSWERED and rig.launcher.requested == ["calculator"]
    sent = [m.content for m in rig.provider.requests[-1][0] if m.role == "user"]
    assert "no" not in sent and "yes" not in sent  # Wyzer's control words stay local


# ------------------------------------------------ B5 over loopback HTTP


def test_b5_calculator_approve_over_http_with_wyzer_ollama_client() -> None:
    server = FakeOllama().start()
    try:
        server.script(
            chat_tool("open_allowed_application", CALC),
            chat_tool("open_allowed_application", CALC),  # repeat after the SIMULATED result
        )
        rig = http_rig(server.url)
        assert ask(rig, "Jarvis, abre a calculadora").outcome is TurnOutcome.CONFIRMATION_REQUESTED
        done = ask(rig, "sim")
        assert done.outcome is TurnOutcome.CONFIRMED and done.action_status == "SIMULATED"
        assert rig.launcher.requested == ["calculator"] and rig.pending is None
        assert done.metrics["llm_calls"] == 1.0  # one model call after "sim"
        assert len(server.chats()) == 2
    finally:
        server.stop()
