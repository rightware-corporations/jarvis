"""Microphone capture behind a replaceable adapter.

Reuses Wyzer's energy-gated 16 kHz capture (``WindowsSpeechRecognizer.capture_utterance``,
SoundDevice + NumPy) instead of re-implementing it. Nothing is imported or opened at
construction; the first ``capture`` call does that. No audio is ever written to disk
here; Wyzer's recognizer writes a temporary WAV only for the duration of transcription
and deletes it.

Cancellation: the Wyzer capture loop cannot be interrupted mid-utterance (it ends on
silence, timeout or the 15 s phrase limit). ``CancellableCapture`` therefore guarantees
that audio captured across a cancel is discarded, and refuses new captures after
``close``.
"""

from __future__ import annotations

import importlib
import threading
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable

from jarvis.voice.contracts import CaptureError


@runtime_checkable
class AudioCapture(Protocol):
    def capture(self, timeout_seconds: float) -> bytes | None:
        """16 kHz mono int16 PCM for one utterance; ``None`` for silence/timeout."""
        ...


class _NoRunner:
    """Placeholder runner: capture never needs PowerShell."""

    def run(self, *args: Any, **kwargs: Any) -> str:  # pragma: no cover - never called
        raise CaptureError("not used for capture")


class WyzerMicrophoneCapture:
    sample_rate = 16_000

    def __init__(self) -> None:
        self._recognizer: Any | None = None

    def capture(self, timeout_seconds: float) -> bytes | None:
        from wyzer.speech.windows import SpeechAdapterError, WindowsSpeechRecognizer

        if self._recognizer is None:
            self._recognizer = WindowsSpeechRecognizer(runner=_NoRunner())
        try:
            return self._recognizer.capture_utterance(timeout_seconds)
        except SpeechAdapterError as error:
            raise CaptureError(str(error)) from error


class CancellableCapture:
    def __init__(self, inner: AudioCapture) -> None:
        self.inner = inner
        self._lock = threading.Lock()
        self._epoch = 0
        self._closed = False

    def capture(self, timeout_seconds: float) -> bytes | None:
        with self._lock:
            if self._closed:
                raise CaptureError("capture adapter is closed")
            epoch = self._epoch
        audio = self.inner.capture(timeout_seconds)
        with self._lock:
            if self._closed or epoch != self._epoch:
                return None  # captured across a cancel or close: discard
        return audio

    def cancel(self) -> None:
        with self._lock:
            self._epoch += 1

    def close(self) -> None:
        with self._lock:
            self._closed = True
            self._epoch += 1


# ------------------------------------------------------------------ device probe


@dataclass(frozen=True, slots=True)
class MicrophoneStatus:
    available: bool
    input_devices: int
    default_input: bool
    code: str
    detail: str = ""


def probe_microphone(
    query_devices: Callable[..., Any] | None = None,
    default_device: Callable[[], Any] | None = None,
) -> MicrophoneStatus:
    """Read-only device listing via SoundDevice. Opens no stream, records nothing."""
    if query_devices is None:
        try:
            sounddevice = importlib.import_module("sounddevice")
        except Exception as error:  # ImportError, or PortAudio missing (OSError)
            return MicrophoneStatus(False, 0, False, "AUDIO_DEPENDENCY_MISSING", type(error).__name__)
        query_devices = sounddevice.query_devices
        default_device = lambda: sounddevice.default.device  # noqa: E731
    try:
        devices = list(query_devices())
    except Exception as error:
        return MicrophoneStatus(False, 0, False, "AUDIO_QUERY_FAILED", type(error).__name__)
    inputs = [d for d in devices if int(_field(d, "max_input_channels", 0)) > 0]
    default_ok = False
    try:
        default = default_device() if default_device is not None else None
        index = default[0] if isinstance(default, (list, tuple)) else default
        if index is not None and 0 <= int(index) < len(devices):
            default_ok = int(_field(devices[int(index)], "max_input_channels", 0)) > 0
    except Exception:
        default_ok = False
    if not inputs:
        return MicrophoneStatus(False, 0, False, "MIC_MISSING", "no input device")
    if not default_ok:
        return MicrophoneStatus(False, len(inputs), False, "MIC_NO_DEFAULT", "no default input")
    return MicrophoneStatus(True, len(inputs), True, "MIC_OK")


def _field(device: Any, key: str, default: Any) -> Any:
    if isinstance(device, dict):
        return device.get(key, default)
    return getattr(device, key, default)
