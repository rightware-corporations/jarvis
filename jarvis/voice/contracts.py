"""Small synchronous contracts the voice loop depends on.

All three are blocking by design (they wrap audio devices); the voice loop calls them
through ``asyncio.to_thread`` so cancellation of the turn never blocks the event loop.
Real adapters live in ``stt_pt``, ``tts`` and ``activation``; tests use fakes.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass(frozen=True, slots=True)
class Transcript:
    text: str
    confidence: float
    language: str = "pt"


@runtime_checkable
class SpeechToText(Protocol):
    def listen(self, timeout_seconds: float) -> Transcript | None:
        """Capture one utterance. ``None`` means silence, timeout or low confidence."""
        ...


@runtime_checkable
class TextToSpeech(Protocol):
    def warm_up(self) -> None: ...

    def speak(self, text: str) -> None:
        """Speak and block until finished or until ``stop`` is called."""
        ...

    def stop(self) -> None: ...


@runtime_checkable
class Activation(Protocol):
    def wait(self, timeout_seconds: float) -> bool:
        """Block until the user activates the assistant. ``False`` on timeout/close."""
        ...

    def close(self) -> None: ...


class SpeechSynthesisError(RuntimeError):
    """Audio could not be generated (model, G2P, voice missing)."""


class SpeechPlaybackError(RuntimeError):
    """Audio was generated but could not be played (device, driver, stream)."""


class CaptureError(RuntimeError):
    """The microphone could not be opened or read (missing device, driver, permission)."""


@runtime_checkable
class Interruptible(Protocol):
    """Optional: adapters that can abandon a blocking call and release devices."""

    def cancel(self) -> None: ...

    def close(self) -> None: ...
