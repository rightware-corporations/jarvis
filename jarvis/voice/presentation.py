"""Fail-closed speech presentation.

The Wyzer adapters return normally in cases where nothing was heard: after ``stop()``
and, for Kokoro, when the volume is 0 or the text is empty. ``speak()`` returning is
therefore not proof that the user heard anything. ``GuardedSpeech`` turns every call
into an explicit ``PresentationResult``; only ``SPOKEN`` counts as presented, and the
voice loop only arms a confirmation after a ``SPOKEN`` prompt.

There is no visual confirmation channel in 01B. ``TextOnlySpeech`` (text mode) is an
explicit text channel and reports ``SPOKEN`` only after the line was written.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass
from enum import StrEnum

from jarvis.voice.contracts import SpeechPlaybackError, SpeechSynthesisError, TextToSpeech


class Presentation(StrEnum):
    SPOKEN = "spoken"
    INTERRUPTED = "interrupted"
    FAILED = "failed"
    NOT_PRESENTED = "not_presented"


class FailureStage(StrEnum):
    NONE = "none"
    SYNTHESIS = "synthesis"
    PLAYBACK = "playback"
    ADAPTER = "adapter"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class PresentationResult:
    outcome: Presentation
    stage: FailureStage = FailureStage.NONE
    error: str | None = None

    @property
    def presented(self) -> bool:
        return self.outcome is Presentation.SPOKEN


def _stage_of(error: BaseException) -> FailureStage:
    if isinstance(error, SpeechSynthesisError):
        return FailureStage.SYNTHESIS
    if isinstance(error, SpeechPlaybackError):
        return FailureStage.PLAYBACK
    if type(error).__name__ == "SpeechAdapterError":
        return FailureStage.ADAPTER
    return FailureStage.UNKNOWN


class GuardedSpeech:
    """Wraps any ``TextToSpeech`` and reports what really happened."""

    def __init__(self, inner: TextToSpeech) -> None:
        self.inner = inner
        self._stops = 0
        self._lock = threading.Lock()

    def warm_up(self) -> None:
        self.inner.warm_up()

    def stop(self) -> None:
        with self._lock:
            self._stops += 1
        self.inner.stop()

    def present(self, text: str) -> PresentationResult:
        if not text or not text.strip():
            return PresentationResult(Presentation.NOT_PRESENTED)
        if int(getattr(self.inner, "volume", 100)) <= 0:
            return PresentationResult(Presentation.NOT_PRESENTED, error="volume is 0")
        with self._lock:
            stops_before = self._stops
        try:
            self.inner.speak(text)
        except Exception as error:
            return PresentationResult(Presentation.FAILED, _stage_of(error), type(error).__name__)
        with self._lock:
            interrupted = self._stops != stops_before
        if interrupted:
            return PresentationResult(Presentation.INTERRUPTED)
        return PresentationResult(Presentation.SPOKEN)
