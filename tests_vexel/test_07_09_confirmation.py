"""Tests 7, 8 and 9 — deterministic Portuguese confirmation policy.

7: a valid ``sim`` executes exactly the pending operation.
8: ``não``, ``cancela``, silence, timeout and ambiguous phrases reject it.
9: repeated, expired or other-operation confirmations are refused.
"""

from __future__ import annotations

import asyncio
import time

import pytest

from jarvis.core.voice_loop import (
    SAY_CONFIRMATION_MISMATCH,
    SAY_NOTHING_TO_CONFIRM,
    TurnOutcome,
)
from jarvis.language.pt import CONFIRM_PHRASES, ControlIntent, classify_control, normalize, strip_vocative
from jarvis.language.prompts import (
    SAY_CANCELLED,
    SAY_CANCELLED_NO_CONFIRMATION,
    SAY_CANCELLED_UNCLEAR,
)
from jarvis.ui.events import VoiceState
from tests_vexel.conftest import Rig, make_rig
from tests_vexel.fakes import call, say


def _request_open(rig: Rig, app: str = "calculator") -> None:
    rig.provider.push(call("open_allowed_application", {"app": app}), say("Abri."))
    result = asyncio.run(rig.session.handle_text(f"abre {app}"))
    assert result.outcome is TurnOutcome.CONFIRMATION_REQUESTED
    assert rig.pending is not None
    assert rig.launcher.launched == []


# ----------------------------------------------------------------- policy unit


@pytest.mark.parametrize(
    ("phrase", "intent"),
    [
        ("Sim", ControlIntent.CONFIRM),
        ("sim.", ControlIntent.CONFIRM),
        ("Jarvis, sim!", ControlIntent.CONFIRM),
        ("sim, confirmo", ControlIntent.CONFIRM),
        ("confirmo", ControlIntent.CONFIRM),
        ("pode avançar", ControlIntent.CONFIRM),
        ("Não", ControlIntent.REJECT),
        ("nao", ControlIntent.REJECT),
        ("não quero", ControlIntent.REJECT),
        ("esquece", ControlIntent.REJECT),
        ("Cancela", ControlIntent.CANCEL),
        ("cancela essa operação", ControlIntent.CANCEL),
        ("pára", ControlIntent.CANCEL),
        ("para", ControlIntent.CANCEL),
        ("sim não", ControlIntent.NONE),
        ("talvez", ControlIntent.NONE),
        ("sim mas abre o bloco de notas", ControlIntent.NONE),
        ("simples", ControlIntent.NONE),
        ("não sei", ControlIntent.NONE),
        ("yes", ControlIntent.NONE),
        ("", ControlIntent.NONE),
    ],
)
def test_classification_is_exact(phrase: str, intent: ControlIntent) -> None:
    assert classify_control(strip_vocative(normalize(phrase))) is intent


# --------------------------------------------------------------------- test 7


@pytest.mark.parametrize("phrase", ["sim", "Sim!", "sim, confirmo", "confirmo", "pode", "Jarvis sim"])
def test_valid_confirmation_executes_the_pending_call_once(phrase: str) -> None:
    rig = make_rig()
    _request_open(rig, "calculator")
    assert rig.tts.spoken[-1] == "Queres que eu abra a Calculadora? Responde sim ou não."
    result = asyncio.run(rig.session.handle_text(phrase))
    assert result.outcome is TurnOutcome.CONFIRMED
    assert rig.launcher.launched == ["calculator"]
    assert rig.pending is None
    assert rig.session.state is VoiceState.IDLE


def test_notepad_prompt_and_execution() -> None:
    rig = make_rig()
    _request_open(rig, "notepad")
    assert rig.tts.spoken[-1] == "Queres que eu abra o Bloco de Notas? Responde sim ou não."
    asyncio.run(rig.session.handle_text("sim"))
    assert rig.launcher.launched == ["notepad"]


def test_all_confirm_phrases_are_recognised() -> None:
    for phrase in CONFIRM_PHRASES:
        assert classify_control(phrase) is ControlIntent.CONFIRM


# --------------------------------------------------------------------- test 8


@pytest.mark.parametrize(
    ("reply", "outcome", "spoken"),
    [
        ("não", TurnOutcome.REJECTED, SAY_CANCELLED),
        ("Não, obrigado", TurnOutcome.REJECTED, SAY_CANCELLED),
        ("cancela", TurnOutcome.REJECTED, SAY_CANCELLED),
        ("cancela essa operação", TurnOutcome.REJECTED, SAY_CANCELLED),
        (None, TurnOutcome.CANCELLED_NO_RESPONSE, SAY_CANCELLED_NO_CONFIRMATION),
        ("   ", TurnOutcome.CANCELLED_NO_RESPONSE, SAY_CANCELLED_NO_CONFIRMATION),
        ("talvez", TurnOutcome.CANCELLED_UNCLEAR, SAY_CANCELLED_UNCLEAR),
        ("sim não", TurnOutcome.CANCELLED_UNCLEAR, SAY_CANCELLED_UNCLEAR),
        ("sim, mas abre o bloco de notas", TurnOutcome.CANCELLED_UNCLEAR, SAY_CANCELLED_UNCLEAR),
        ("yes", TurnOutcome.CANCELLED_UNCLEAR, SAY_CANCELLED_UNCLEAR),
    ],
)
def test_rejections_cancel_and_never_execute(reply: str | None, outcome: TurnOutcome, spoken: str) -> None:
    rig = make_rig()
    _request_open(rig)
    requests_before = len(rig.provider.requests)
    result = asyncio.run(rig.session.handle_text(reply))
    assert result.outcome is outcome
    assert rig.tts.spoken[-1] == spoken
    assert rig.launcher.launched == []
    assert rig.pending is None
    # The rejecting phrase is never forwarded to the model as a new request.
    assert len(rig.provider.requests) == requests_before
    # A later "sim" cannot revive it.
    assert asyncio.run(rig.session.handle_text("sim")).outcome is TurnOutcome.NOTHING_TO_CONFIRM
    assert rig.launcher.launched == []


def test_voice_timeout_while_awaiting_confirmation_cancels() -> None:
    rig = make_rig()
    rig.provider.push(call("open_allowed_application", {"app": "calculator"}), say("Abri."))
    rig.stt.push("abre a calculadora", None)  # second listen times out
    results = asyncio.run(rig.session.voice_turn())
    assert [r.outcome for r in results] == [
        TurnOutcome.CONFIRMATION_REQUESTED,
        TurnOutcome.CANCELLED_NO_RESPONSE,
    ]
    assert rig.stt.timeouts == [8.0, 8.0]
    assert rig.launcher.launched == []
    assert rig.pending is None


def test_voice_turn_confirmed_by_voice() -> None:
    rig = make_rig()
    rig.provider.push(call("open_allowed_application", {"app": "notepad"}), say("Abri o Bloco de Notas."))
    rig.stt.push("Jarvis, abre o Bloco de Notas", "sim")
    results = asyncio.run(rig.session.voice_turn())
    assert results[-1].outcome is TurnOutcome.CONFIRMED
    assert rig.launcher.launched == ["notepad"]
    assert rig.tts.spoken[-1] == "Abri o Bloco de Notas."


# --------------------------------------------------------------------- test 9


def test_repeated_confirmation_is_not_replayed() -> None:
    rig = make_rig()
    _request_open(rig)
    asyncio.run(rig.session.handle_text("sim"))
    for _ in range(3):
        result = asyncio.run(rig.session.handle_text("sim"))
        assert result.outcome is TurnOutcome.NOTHING_TO_CONFIRM
        assert result.reply == SAY_NOTHING_TO_CONFIRM
    assert rig.launcher.launched == ["calculator"]


def test_sim_without_any_pending_does_nothing() -> None:
    rig = make_rig()
    result = asyncio.run(rig.session.handle_text("sim"))
    assert result.outcome is TurnOutcome.NOTHING_TO_CONFIRM
    assert rig.provider.requests == []
    assert rig.launcher.launched == []


def test_expired_confirmation_is_refused() -> None:
    rig = make_rig(ttl=0.05)
    _request_open(rig)
    time.sleep(0.1)
    result = asyncio.run(rig.session.handle_text("sim"))
    assert result.outcome is TurnOutcome.CANCELLED_NO_RESPONSE
    assert result.reply == "Essa confirmação expirou. Pede-me de novo, por favor."
    assert rig.launcher.launched == []
    assert rig.pending is None


def test_confirmation_for_another_operation_is_refused() -> None:
    """A pending call that VEXEL did not prompt for (swapped underneath) is not approved."""
    rig = make_rig()
    _request_open(rig, "calculator")
    original = rig.pending
    assert original is not None
    swapped = original.model_copy(
        update={
            "arguments": {"app": "notepad"},
            "call_digest": __import__("hashlib").sha256(b"other").hexdigest(),
        }
    )
    rig.parts.orchestrator.world.set_confirmation(swapped)
    result = asyncio.run(rig.session.handle_text("sim"))
    assert result.outcome is TurnOutcome.CANCELLED_MISMATCH
    assert result.reply == SAY_CONFIRMATION_MISMATCH
    assert rig.launcher.launched == []
    assert rig.pending is None


def test_tampered_arguments_fail_orchestrator_digest_check() -> None:
    """Second gate: even if VEXEL's binding matched, Wyzer re-validates the digest."""
    rig = make_rig()
    _request_open(rig, "calculator")
    original = rig.pending
    assert original is not None
    tampered = original.model_copy(update={"arguments": {"app": "notepad"}})
    rig.parts.orchestrator.world.set_confirmation(tampered)
    result = asyncio.run(rig.session.handle_text("sim"))
    # VEXEL binding (id + digest) matched, so Wyzer's own digest check is what refuses it.
    assert result.outcome is TurnOutcome.CANCELLED_MISMATCH
    assert result.reply == "Não consegui confirmar, porque o pedido mudou."
    assert rig.launcher.launched == []


def test_new_request_while_pending_cancels_it_and_is_not_executed() -> None:
    rig = make_rig()
    _request_open(rig, "calculator")
    result = asyncio.run(rig.session.handle_text("abre o bloco de notas"))
    assert result.outcome is TurnOutcome.CANCELLED_UNCLEAR
    assert rig.pending is None
    assert asyncio.run(rig.session.handle_text("sim")).outcome is TurnOutcome.NOTHING_TO_CONFIRM
    assert rig.launcher.launched == []
