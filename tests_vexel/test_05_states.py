"""Test 5 — valid states and transitions; signals for the future 01E orb."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest

from jarvis.ui.events import (
    ALLOWED_TRANSITIONS,
    InvalidTransitionError,
    JsonlEventLog,
    RecordingSink,
    StateMachine,
    VoiceState,
)
from tests_vexel.conftest import make_rig
from tests_vexel.fakes import call, say

ALL_PAIRS = [(a, b) for a in VoiceState for b in VoiceState if a is not b]


def test_every_state_has_a_transition_entry() -> None:
    assert set(ALLOWED_TRANSITIONS) == set(VoiceState)


@pytest.mark.parametrize(("source", "target"), ALL_PAIRS, ids=lambda s: s.value)
def test_transition_table_is_enforced(source: VoiceState, target: VoiceState) -> None:
    machine = StateMachine(RecordingSink(), session_id="t", initial=source)
    if target in ALLOWED_TRANSITIONS[source]:
        event = machine.transition(target)
        assert event is not None and event.previous is source and event.state is target
    else:
        with pytest.raises(InvalidTransitionError):
            machine.transition(target)
        assert machine.state is source


def test_same_state_is_a_noop() -> None:
    sink = RecordingSink()
    machine = StateMachine(sink, session_id="t", initial=VoiceState.IDLE)
    assert machine.transition(VoiceState.IDLE) is None
    assert sink.events == []


def test_answer_cycle_publishes_expected_sequence() -> None:
    rig = make_rig()
    rig.provider.push(call("get_local_time"), say("São catorze e trinta."))
    asyncio.run(rig.session.handle_text("que horas são"))
    assert rig.sink.states == [
        VoiceState.IDLE,
        VoiceState.LISTENING,
        VoiceState.THINKING,
        VoiceState.TOOL_RUNNING,
        VoiceState.SPEAKING,
        VoiceState.IDLE,
    ]
    sequences = [event.sequence for event in rig.sink.events]
    assert sequences == sorted(sequences) and len(set(sequences)) == len(sequences)


def test_confirmation_cycle_publishes_awaiting_state() -> None:
    rig = make_rig()
    rig.provider.push(call("open_allowed_application", {"app": "calculator"}), say("Abri a Calculadora."))
    asyncio.run(rig.session.handle_text("abre a calculadora"))
    assert rig.session.state is VoiceState.AWAITING_CONFIRMATION
    asyncio.run(rig.session.handle_text("sim"))
    assert rig.sink.states == [
        VoiceState.IDLE,
        VoiceState.LISTENING,
        VoiceState.THINKING,
        VoiceState.AWAITING_CONFIRMATION,
        VoiceState.LISTENING,
        VoiceState.THINKING,
        VoiceState.TOOL_RUNNING,
        VoiceState.SPEAKING,
        VoiceState.IDLE,
    ]


def test_jsonl_log_omits_transcript_text_by_default(tmp_path: Path) -> None:
    log_path = tmp_path / "events.jsonl"
    machine = StateMachine(JsonlEventLog(log_path), session_id="t", initial=VoiceState.IDLE)
    machine.transition(VoiceState.LISTENING, text="o meu segredo")
    record = json.loads(log_path.read_text(encoding="utf-8").splitlines()[0])
    assert "o meu segredo" not in json.dumps(record, ensure_ascii=False)
    assert record["to"] == "listening" and record["text_chars"] == len("o meu segredo")
