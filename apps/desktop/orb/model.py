"""Orb state model: applies ``UiEvent``s in order and ignores stale ones. No Qt.

Events arrive through ``jarvis.ui.QueueSink`` and are applied on the Qt thread by
``OrbEventPump``. The model keeps only the newest state: an event with an older
``generation`` (a cancelled turn) or an older ``sequence`` (out of order) is dropped,
so a late event can never overwrite a newer state on screen.

``sequence`` and ``generation`` are numbered per ``StateMachine`` session, so the
ordering is reset when an event from a different ``session_id`` arrives (a restarted
voice session starts again at sequence 1).
"""

from __future__ import annotations

from collections import deque
from collections.abc import Iterable
from dataclasses import dataclass, field

from jarvis.ui.events import UiEvent, VoiceState


@dataclass
class OrbStateModel:
    state: VoiceState = VoiceState.OFFLINE
    generation: int = -1
    sequence: int = -1
    detail: str | None = None
    session_id: str | None = None
    applied: int = 0
    dropped: int = 0
    history: deque[VoiceState] = field(default_factory=lambda: deque(maxlen=512))

    def apply(self, events: Iterable[UiEvent]) -> bool:
        """Apply events; return True if the visible state changed."""
        before = self.state
        for event in events:
            if event.session_id != self.session_id:
                # New session: its counters restart, so forget the previous ordering.
                self.session_id = event.session_id
                self.generation = -1
                self.sequence = -1
            if event.generation < self.generation or (
                event.generation == self.generation and event.sequence <= self.sequence
            ):
                self.dropped += 1
                continue
            self.generation = event.generation
            self.sequence = event.sequence
            self.state = event.state
            self.detail = event.detail
            self.applied += 1
            self.history.append(event.state)
        return self.state is not before
