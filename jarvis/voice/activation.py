"""Activation for JAR-SLICE-01: manual only.

The openWakeWord pretrained ``hey_jarvis`` models are CC BY-NC-SA 4.0 (non-commercial)
and are not used or downloaded. Wake word stays ``WAKE_WORD_BLOCKED`` until a model
with acceptable terms is approved; the ``Activation`` contract lets it drop in later.
"""

from __future__ import annotations

import threading

from jarvis.config import WAKE_WORD_BLOCKED, WakeWordBlockedError


class ManualActivation:
    """Push-to-talk style trigger (a key, a HUD button or a text command)."""

    def __init__(self) -> None:
        self._event = threading.Event()
        self._closed = threading.Event()

    def trigger(self) -> None:
        if not self._closed.is_set():
            self._event.set()

    def wait(self, timeout_seconds: float) -> bool:
        if self._closed.is_set():
            return False
        fired = self._event.wait(timeout_seconds)
        self._event.clear()
        return fired and not self._closed.is_set()

    def close(self) -> None:
        self._closed.set()
        self._event.set()

    @property
    def closed(self) -> bool:
        return self._closed.is_set()


def create_activation(adapter: str) -> ManualActivation:
    name = adapter.strip().casefold()
    if name == "manual":
        return ManualActivation()
    raise WakeWordBlockedError(f"{WAKE_WORD_BLOCKED}: activation adapter {adapter!r}")
