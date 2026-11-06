"""Test 3 — Portuguese STT configuration (simulated model; nothing is downloaded)."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from jarvis.config import SliceConfigError, parse_slice_config
from jarvis.voice.contracts import SpeechToText, Transcript
from jarvis.voice.stt_pt import (
    EnglishOnlyModelError,
    PortugueseWhisperRecognizer,
    create_portuguese_stt,
)
from tests_vexel.fakes import SLICE_CONFIG, slice_config


class FakeWhisperModel:
    def __init__(self, segments: list[Any]) -> None:
        self.segments = segments
        self.calls: list[dict[str, Any]] = []

    def transcribe(self, audio: str, **kwargs: Any) -> tuple[Any, Any]:
        self.calls.append({"audio": audio, **kwargs})
        return iter(self.segments), None


def _segment(text: str, logprob: float = -0.1, no_speech: float = 0.01) -> Any:
    return SimpleNamespace(text=text, avg_logprob=logprob, no_speech_prob=no_speech)


def _factory(model: FakeWhisperModel, seen: dict[str, Any]):
    def factory(name: str, **kwargs: Any) -> FakeWhisperModel:
        seen.update(name=name, **kwargs)
        return model

    return factory


def test_slice_config_selects_multilingual_whisper() -> None:
    speech = slice_config().wyzer.speech
    assert speech.whisper_model == "small"
    assert speech.wake_word_adapter == "manual"


def test_recognizer_passes_pt_language_and_hotwords(tmp_path: Path) -> None:
    model = FakeWhisperModel([_segment(" Que horas são?")])
    seen: dict[str, Any] = {}
    stt = create_portuguese_stt(
        slice_config().wyzer.speech.model_copy(update={"whisper_download_root": tmp_path}),
        capture_utterance=lambda _t: b"\x00\x00" * 1600,
        model_factory=_factory(model, seen),
    )
    assert isinstance(stt, SpeechToText)
    transcript = stt.listen(3)
    assert transcript == Transcript(text="Que horas são?", confidence=pytest.approx(0.905, abs=1e-3))
    options = model.calls[0]
    assert options["language"] == "pt"
    assert options["task"] == "transcribe"
    assert "Calculadora" in options["hotwords"] and "Bloco de Notas" in options["hotwords"]
    assert seen["name"] == "small" and seen["local_files_only"] is True


@pytest.mark.parametrize(
    ("segments", "expected"),
    [
        ([], None),
        ([_segment("ruído", no_speech=0.9)], None),
        ([_segment("murmúrio", logprob=-3.0)], None),
    ],
    ids=["empty", "no_speech", "low_confidence"],
)
def test_silence_and_low_confidence_return_none(
    tmp_path: Path, segments: list[Any], expected: None
) -> None:
    recognizer = PortugueseWhisperRecognizer(
        "small",
        download_root=tmp_path,
        capture_utterance=lambda _t: b"\x00\x00" * 1600,
        model_factory=_factory(FakeWhisperModel(segments), {}),
    )
    assert recognizer.listen(1) is expected


def test_no_audio_captured_returns_none(tmp_path: Path) -> None:
    recognizer = PortugueseWhisperRecognizer(
        "small", download_root=tmp_path, capture_utterance=lambda _t: None
    )
    assert recognizer.listen(1) is None


@pytest.mark.parametrize("name", ["small.en", "base.en", "Medium.EN"])
def test_english_only_models_are_refused(name: str, tmp_path: Path) -> None:
    with pytest.raises(EnglishOnlyModelError):
        PortugueseWhisperRecognizer(name, download_root=tmp_path, capture_utterance=lambda _t: None)


def test_config_refuses_english_only_model() -> None:
    import tomllib

    data = tomllib.loads(SLICE_CONFIG.read_text(encoding="utf-8"))
    data["speech"]["whisper_model"] = "small.en"
    with pytest.raises(SliceConfigError, match="English-only"):
        parse_slice_config(data)
