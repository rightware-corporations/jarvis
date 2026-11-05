"""Portuguese Faster-Whisper adapter, by composition over Wyzer's recognizer.

``wyzer/speech/whisper.py`` hardcodes ``language="en"`` and English hotwords inside
``_transcribe``. It is a protected file, so this module subclasses the recognizer and
overrides only that method. Model loading (``local_files_only=True``), CUDA→CPU
fallback and WAV handling stay upstream. Nothing here downloads a model.
"""

from __future__ import annotations

import math
from collections.abc import Callable
from pathlib import Path
from typing import Any

from wyzer.speech.whisper import FasterWhisperRecognizer, WhisperModelProtocol
from wyzer.speech.windows import SpeechRecognition

from jarvis.voice.contracts import Transcript

DEFAULT_PT_HOTWORDS = (
    "Jarvis Calculadora Bloco de Notas horas estado do computador "
    "abre cancela sim não confirmo"
)
NO_SPEECH_THRESHOLD = 0.6


class EnglishOnlyModelError(ValueError):
    pass


class PortugueseWhisperRecognizer(FasterWhisperRecognizer):
    def __init__(
        self,
        model_name: str = "small",
        *,
        language: str = "pt",
        hotwords: str = DEFAULT_PT_HOTWORDS,
        device: str = "auto",
        compute_type: str = "int8_float16",
        download_root: Path = Path(".wyzer/models"),
        minimum_confidence: float = 0.35,
        capture_utterance: Callable[[float], bytes | None],
        model_factory: Callable[..., WhisperModelProtocol] | None = None,
    ) -> None:
        if model_name.strip().casefold().endswith(".en"):
            raise EnglishOnlyModelError(
                f"{model_name!r} is an English-only Whisper model; use a multilingual one"
            )
        super().__init__(
            model_name,
            device=device,
            compute_type=compute_type,
            download_root=download_root,
            minimum_confidence=minimum_confidence,
            capture_utterance=capture_utterance,
            model_factory=model_factory,
        )
        self.language = language
        self.hotwords = hotwords

    def transcribe_options(self) -> dict[str, Any]:
        return {
            "language": self.language,
            "task": "transcribe",
            "beam_size": 5,
            "vad_filter": True,
            "condition_on_previous_text": False,
            "hotwords": self.hotwords,
        }

    def _transcribe(self, path: Path) -> SpeechRecognition | None:
        model = self._ensure_model()
        segments_raw, _ = model.transcribe(str(path), **self.transcribe_options())
        segments = [
            segment
            for segment in segments_raw
            if float(getattr(segment, "no_speech_prob", 0.0)) < NO_SPEECH_THRESHOLD
        ]
        text = " ".join(str(segment.text).strip() for segment in segments).strip()
        if not text:
            return None
        log_probs = [float(segment.avg_logprob) for segment in segments]
        confidence = math.exp(sum(log_probs) / len(log_probs)) if log_probs else 0.0
        confidence = max(0.0, min(1.0, confidence))
        if confidence < self.minimum_confidence:
            return None
        return SpeechRecognition(text=text, confidence=confidence)


class WhisperSpeechToText:
    """Adapts any Wyzer-style recognizer (``listen -> SpeechRecognition``) to the contract.

    ``cancel``/``close`` are forwarded to the capture adapter when it supports them, so a
    cancelled turn never returns audio captured across the cancel.
    """

    def __init__(self, recognizer: Any, *, language: str = "pt", capture: Any = None) -> None:
        self._recognizer = recognizer
        self._language = language
        self._capture = capture

    def cancel(self) -> None:
        cancel = getattr(self._capture, "cancel", None)
        if callable(cancel):
            cancel()

    def close(self) -> None:
        close = getattr(self._capture, "close", None)
        if callable(close):
            close()

    def listen(self, timeout_seconds: float) -> Transcript | None:
        result = self._recognizer.listen(timeout_seconds)
        if result is None:
            return None
        return Transcript(text=result.text, confidence=result.confidence, language=self._language)


def create_portuguese_stt(
    speech: Any,
    *,
    capture_utterance: Callable[[float], bytes | None],
    hotwords: str = DEFAULT_PT_HOTWORDS,
    model_factory: Callable[..., WhisperModelProtocol] | None = None,
) -> WhisperSpeechToText:
    """Build from ``WyzerSettings.speech``. Loads nothing until the first ``listen``."""
    recognizer = PortugueseWhisperRecognizer(
        speech.whisper_model,
        language="pt",
        hotwords=hotwords,
        device=speech.whisper_device,
        compute_type=speech.whisper_compute_type,
        download_root=speech.whisper_download_root,
        minimum_confidence=speech.minimum_stt_confidence,
        capture_utterance=capture_utterance,
        model_factory=model_factory,
    )
    return WhisperSpeechToText(recognizer)


def create_voice_input(
    speech: Any,
    capture: Any,
    *,
    hotwords: str = DEFAULT_PT_HOTWORDS,
    model_factory: Callable[..., WhisperModelProtocol] | None = None,
) -> WhisperSpeechToText:
    """Microphone capture → Portuguese Faster-Whisper, for ``--voice`` mode.

    ``capture`` is any ``AudioCapture`` (normally ``CancellableCapture``). The Whisper
    model is loaded lazily from the local cache (``local_files_only=True``) on first use.
    """
    recognizer = PortugueseWhisperRecognizer(
        speech.whisper_model,
        language="pt",
        hotwords=hotwords,
        device=speech.whisper_device,
        compute_type=speech.whisper_compute_type,
        download_root=speech.whisper_download_root,
        minimum_confidence=speech.minimum_stt_confidence,
        capture_utterance=capture.capture,
        model_factory=model_factory,
    )
    return WhisperSpeechToText(recognizer, capture=capture)
