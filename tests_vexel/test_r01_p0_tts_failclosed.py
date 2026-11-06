"""R01 · P0 — TTS failures are never reported as spoken; confirmations fail closed."""

from __future__ import annotations

import asyncio
import threading

import pytest

from jarvis.config import SliceConfigError, parse_slice_config
from jarvis.core.voice_loop import TurnOutcome
from jarvis.ui.events import VoiceState
from jarvis.voice.contracts import SpeechPlaybackError, SpeechSynthesisError
from jarvis.voice.presentation import FailureStage, GuardedSpeech, Presentation
from wyzer.speech.windows import SpeechAdapterError
from tests_vexel.conftest import make_rig
from tests_vexel.fakes import SLICE_CONFIG, FailingTts, RecordingTts, SilentTts, call, say

FAILURES = [
    pytest.param(SpeechSynthesisError("no voice model"), FailureStage.SYNTHESIS, id="synthesis"),
    pytest.param(SpeechPlaybackError("device lost"), FailureStage.PLAYBACK, id="playback"),
    pytest.param(SpeechAdapterError("Kokoro returned no audio."), FailureStage.ADAPTER, id="adapter"),
    pytest.param(RuntimeError("unexpected"), FailureStage.UNKNOWN, id="unknown"),
]


def _ask_open(rig, app: str = "calculator"):
    rig.provider.push(call("open_allowed_application", {"app": app}), say("Abri."))
    return asyncio.run(rig.session.handle_text(f"abre {app}"))


# ------------------------------------------------------------ presentation unit


@pytest.mark.parametrize(("error", "stage"), FAILURES)
def test_guard_reports_failure_stage(error: BaseException, stage: FailureStage) -> None:
    result = GuardedSpeech(FailingTts(error)).present("Olá")
    assert result.outcome is Presentation.FAILED and not result.presented
    assert result.stage is stage


def test_guard_treats_silent_adapter_as_not_presented() -> None:
    silent = SilentTts()
    result = GuardedSpeech(silent).present("Olá")
    assert result.outcome is Presentation.NOT_PRESENTED
    assert silent.calls == 0


def test_guard_treats_empty_text_as_not_presented() -> None:
    assert GuardedSpeech(RecordingTts()).present("   ").outcome is Presentation.NOT_PRESENTED


def test_guard_detects_stop_during_speech() -> None:
    gate = threading.Event()
    guard = GuardedSpeech(RecordingTts(block=gate))
    outcome: list = []
    worker = threading.Thread(target=lambda: outcome.append(guard.present("longa")))
    worker.start()
    while not guard.inner.spoken:
        pass
    guard.stop()
    worker.join(2)
    assert outcome[0].outcome is Presentation.INTERRUPTED


# ------------------------------------------------------------ normal response


@pytest.mark.parametrize(("error", "stage"), FAILURES)
def test_tts_failure_on_normal_reply_is_not_success(error: BaseException, stage: FailureStage) -> None:
    rig = make_rig(tts=FailingTts(error))
    rig.provider.push(say("Olá."))
    result = asyncio.run(rig.session.handle_text("olá"))
    assert result.outcome is TurnOutcome.TTS_FAILED
    assert result.spoken is False
    assert result.presentation is Presentation.FAILED
    errors = [e for e in rig.sink.events if e.state is VoiceState.ERROR]
    assert len(errors) == 1 and errors[0].detail == f"tts_{stage.value}"
    assert rig.sink.states[-2:] == [VoiceState.ERROR, VoiceState.IDLE]
    assert rig.session.state is VoiceState.IDLE


# ------------------------------------------------------------ confirmation prompt


@pytest.mark.parametrize(("error", "stage"), FAILURES)
def test_tts_failure_on_confirmation_prompt_cancels_it(
    error: BaseException, stage: FailureStage
) -> None:
    rig = make_rig(tts=FailingTts(error))
    result = _ask_open(rig)
    assert result.outcome is TurnOutcome.CONFIRMATION_NOT_PRESENTED
    assert result.awaiting_confirmation is False and result.spoken is False
    assert rig.pending is None
    assert rig.session.state is VoiceState.IDLE
    # A later "sim" cannot approve a confirmation the user never heard.
    later = asyncio.run(rig.session.handle_text("sim"))
    assert later.intended is TurnOutcome.NOTHING_TO_CONFIRM
    assert later.outcome is TurnOutcome.TTS_FAILED  # the TTS is still broken
    assert rig.launcher.requested == []


def test_silent_voice_cannot_present_confirmation() -> None:
    rig = make_rig(tts=SilentTts())
    result = _ask_open(rig)
    assert result.outcome is TurnOutcome.CONFIRMATION_NOT_PRESENTED
    assert result.presentation is Presentation.NOT_PRESENTED
    assert rig.pending is None
    asyncio.run(rig.session.handle_text("sim"))
    assert rig.launcher.requested == []


def test_prompt_interrupted_by_external_stop_is_not_armed() -> None:
    gate = threading.Event()
    rig = make_rig(tts=RecordingTts(block=gate))
    rig.provider.push(call("open_allowed_application", {"app": "calculator"}), say("Abri."))

    async def run():
        turn = asyncio.create_task(rig.session.handle_text("abre a calculadora"))
        while not rig.tts.spoken:
            await asyncio.sleep(0.005)
        rig.session.speech.stop()  # speech stopped without a session cancel
        return await turn

    result = asyncio.run(run())
    assert result.outcome is TurnOutcome.CONFIRMATION_NOT_PRESENTED
    assert result.presentation is Presentation.INTERRUPTED
    assert rig.pending is None
    rig.tts.block = None
    assert asyncio.run(rig.session.handle_text("sim")).outcome is TurnOutcome.NOTHING_TO_CONFIRM
    assert rig.launcher.requested == []


def test_voice_turn_does_not_listen_for_unpresented_confirmation() -> None:
    rig = make_rig(tts=FailingTts(SpeechPlaybackError("device lost")))
    rig.provider.push(call("open_allowed_application", {"app": "notepad"}), say("Abri."))
    rig.stt.push("abre o bloco de notas", "sim")
    results = asyncio.run(rig.session.voice_turn())
    assert [r.outcome for r in results] == [TurnOutcome.CONFIRMATION_NOT_PRESENTED]
    assert len(rig.stt.timeouts) == 1  # the queued "sim" was never consumed
    assert rig.launcher.requested == []


# ------------------------------------------------------------ after execution


def test_tts_failure_after_confirmed_action_reports_status_and_no_replay() -> None:
    # Call 1 (prompt) speaks; call 2 (result) fails.
    rig = make_rig(tts=FailingTts(SpeechPlaybackError("device lost"), fail_calls={2}))
    _ask_open(rig)
    result = asyncio.run(rig.session.handle_text("sim"))
    assert result.outcome is TurnOutcome.TTS_FAILED
    assert result.intended is TurnOutcome.CONFIRMED
    assert result.action_status == "SIMULATED"
    assert rig.launcher.requested == ["calculator"]
    for _ in range(2):
        again = asyncio.run(rig.session.handle_text("sim"))
        assert again.outcome is TurnOutcome.NOTHING_TO_CONFIRM
    assert rig.launcher.requested == ["calculator"]


def test_session_recovers_after_tts_failure() -> None:
    tts = FailingTts(SpeechSynthesisError("no voice"), fail_calls={1})
    rig = make_rig(tts=tts)
    rig.provider.push(say("primeira"), say("segunda"))
    first = asyncio.run(rig.session.handle_text("um"))
    second = asyncio.run(rig.session.handle_text("dois"))
    assert first.outcome is TurnOutcome.TTS_FAILED and first.intended is TurnOutcome.ANSWERED
    assert second.outcome is TurnOutcome.ANSWERED and second.spoken
    assert tts.spoken == ["segunda"]
    assert rig.session.state is VoiceState.IDLE
    # Every published transition was valid and ordered.
    for before, after in zip(rig.sink.events, rig.sink.events[1:]):
        assert after.previous is before.state
        assert after.sequence == before.sequence + 1


def test_config_refuses_silent_volume() -> None:
    import tomllib

    data = tomllib.loads(SLICE_CONFIG.read_text(encoding="utf-8"))
    data["speech"]["volume"] = 0
    with pytest.raises(SliceConfigError, match="volume"):
        parse_slice_config(data)
