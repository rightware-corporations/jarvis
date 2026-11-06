"""Test 4 — simulated TTS contract and adapter selection (no audio is produced)."""

from __future__ import annotations

import asyncio
import io
import sys
import threading
from types import SimpleNamespace

import pytest

from jarvis.voice.contracts import TextToSpeech
from jarvis.voice.tts import TextOnlySpeech, UnsupportedTtsError, create_text_to_speech
from tests_vexel.conftest import make_rig
from tests_vexel.fakes import RecordingTts, say


def _speech(**overrides):
    base = dict(tts_adapter="windows_system", voice=None, rate=0, volume=100, tts_speed=1.0, tts_device="cpu")
    base.update(overrides)
    return SimpleNamespace(**base)


@pytest.mark.parametrize("impl", [RecordingTts(), TextOnlySpeech(io.StringIO())])
def test_implementations_satisfy_contract(impl: object) -> None:
    assert isinstance(impl, TextToSpeech)


def test_text_only_speech_writes_instead_of_playing() -> None:
    stream = io.StringIO()
    TextOnlySpeech(stream).speak("Olá")
    assert stream.getvalue() == "Jarvis: Olá\n"


def test_windows_adapter_constructs_without_running_anything() -> None:
    tts = create_text_to_speech(_speech(voice="Microsoft Maria Desktop"))
    assert isinstance(tts, TextToSpeech)
    assert type(tts).__name__ == "WindowsSpeechSynthesizer"


@pytest.mark.parametrize("voice", ["pf_dora", "pm_alex", "pm_santa"])
def test_kokoro_accepts_only_portuguese_voices(voice: str) -> None:
    before = set(sys.modules)
    tts = create_text_to_speech(_speech(tts_adapter="kokoro", voice=voice))
    assert getattr(tts, "language_code") == "p"
    assert "kokoro" not in set(sys.modules) - before  # no model library imported


@pytest.mark.parametrize("voice", ["af_heart", "bm_george", "ef_dora"])
def test_kokoro_refuses_non_portuguese_voices(voice: str) -> None:
    with pytest.raises(UnsupportedTtsError):
        create_text_to_speech(_speech(tts_adapter="kokoro", voice=voice))


def test_unknown_adapter_is_refused() -> None:
    with pytest.raises(UnsupportedTtsError):
        create_text_to_speech(_speech(tts_adapter="elevenlabs"))


def test_cancel_during_speech_stops_tts_and_returns_to_idle() -> None:
    gate = threading.Event()
    rig = make_rig(tts=RecordingTts(block=gate))
    rig.provider.push(say("Uma resposta longa que vai ser interrompida."))

    async def run():
        turn = asyncio.create_task(rig.session.handle_text("conta uma história"))
        while not rig.tts.spoken:
            await asyncio.sleep(0.01)
        rig.session.cancel()
        return await turn

    result = asyncio.run(run())
    assert rig.tts.stops >= 1
    assert result.spoken is False
    assert rig.session.state.value == "idle"
