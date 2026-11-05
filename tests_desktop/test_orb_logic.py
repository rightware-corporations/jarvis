"""Pure logic: visuals and the event model (no Qt needed)."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from apps.desktop.orb.demo import DEMO_SCRIPT
from apps.desktop.orb.model import OrbStateModel
from apps.desktop.orb.visuals import BAR_COUNT, VISUALS, Motion, frame
from jarvis.ui.events import ALLOWED_TRANSITIONS, UiEvent, VoiceState

TIMES = [0.0, 0.13, 0.37, 1.0, 2.71, 10.5]


def test_every_state_has_one_visual_with_a_portuguese_label() -> None:
    assert set(VISUALS) == set(VoiceState)
    labels = [v.label for v in VISUALS.values()]
    assert len(set(labels)) == len(labels)
    assert VISUALS[VoiceState.AWAITING_CONFIRMATION].label == "Confirma: sim ou não?"


def test_states_are_visually_distinct() -> None:
    signatures = {(v.core, v.glow, v.motion) for v in VISUALS.values()}
    assert len(signatures) == len(VoiceState)


@pytest.mark.parametrize("state", list(VoiceState), ids=lambda s: s.value)
@pytest.mark.parametrize("t", TIMES)
def test_frames_are_deterministic_and_bounded(state: VoiceState, t: float) -> None:
    a, b = frame(state, t), frame(state, t)
    assert a == b
    assert 0.40 <= a.core_scale <= 0.62
    assert 0.0 <= a.glow_alpha <= 1.0 and 0.0 <= a.pulse <= 1.0
    assert 0.0 <= a.rotation < 360.0
    assert all(0.0 <= p < 1.0 for p in a.ring_phases)
    assert all(0.0 <= x <= 1.0 for x in a.bars)


def test_motion_semantics() -> None:
    assert len(frame(VoiceState.LISTENING, 0.2).ring_phases) == 3
    assert len(frame(VoiceState.SPEAKING, 0.2).bars) == BAR_COUNT
    assert frame(VoiceState.THINKING, 0.1).rotation != frame(VoiceState.THINKING, 0.6).rotation
    assert frame(VoiceState.MUTED, 0.3).crossed and not frame(VoiceState.IDLE, 0.3).crossed
    assert frame(VoiceState.OFFLINE, 0.0) == frame(VoiceState.OFFLINE, 5.0)  # still
    error = {frame(VoiceState.ERROR, t).pulse for t in (0.05, 0.25)}
    assert error == {1.0, 0.35}  # flicker, not a smooth pulse
    assert VISUALS[VoiceState.AWAITING_CONFIRMATION].motion is Motion.PULSE


def _event(state: VoiceState, seq: int, gen: int = 0) -> UiEvent:
    return UiEvent(state=state, previous=VoiceState.IDLE, session_id="t", sequence=seq,
                   ts=datetime.now(UTC), generation=gen)


def test_model_applies_in_order_and_drops_stale_events() -> None:
    model = OrbStateModel()
    assert model.apply([_event(VoiceState.IDLE, 1), _event(VoiceState.LISTENING, 2)])
    assert model.state is VoiceState.LISTENING
    # Out of order (older sequence) is ignored.
    assert not model.apply([_event(VoiceState.SPEAKING, 1)])
    # A cancelled turn (older generation) cannot overwrite a newer one.
    model.apply([_event(VoiceState.IDLE, 5, gen=2)])
    assert not model.apply([_event(VoiceState.THINKING, 9, gen=1)])
    assert model.state is VoiceState.IDLE and model.dropped == 2


def test_demo_script_is_valid_and_visits_every_state() -> None:
    state = VoiceState.OFFLINE
    for target, seconds in DEMO_SCRIPT:
        assert target is state or target in ALLOWED_TRANSITIONS[state], (state, target)
        assert seconds > 0
        state = target
    assert {target for target, _ in DEMO_SCRIPT} | {VoiceState.OFFLINE} == set(VoiceState)
    assert DEMO_SCRIPT[-1][0] is VoiceState.IDLE  # loops back cleanly


def test_new_session_restarts_ordering() -> None:
    # Review finding P2: a restarted session (sequence back to 1) used to be dropped.
    from dataclasses import replace

    model = OrbStateModel()
    model.apply([_event(VoiceState.IDLE, 1), _event(VoiceState.LISTENING, 5)])
    fresh = [replace(_event(s, n), session_id="t2") for n, s in
             enumerate((VoiceState.IDLE, VoiceState.LISTENING, VoiceState.THINKING), start=1)]
    assert model.apply(fresh)
    assert model.state is VoiceState.THINKING and model.dropped == 0


def test_history_is_bounded() -> None:
    model = OrbStateModel()
    model.apply(_event(VoiceState.IDLE if n % 2 else VoiceState.LISTENING, n) for n in range(1, 2000))
    assert len(model.history) == 512


@pytest.mark.parametrize("speed", [0.0, -1.0])
def test_demo_rejects_non_positive_speed(speed: float) -> None:
    from apps.desktop.orb.demo import DemoDriver
    from jarvis.ui.events import QueueSink

    with pytest.raises(ValueError):
        DemoDriver(QueueSink(), speed=speed)


@pytest.mark.parametrize("value", ["0", "-2"])
def test_cli_rejects_non_positive_speed(value: str) -> None:
    from apps.desktop.__main__ import main

    with pytest.raises(SystemExit) as exit_info:
        main(["--demo", "--speed", value])
    assert exit_info.value.code == 2
