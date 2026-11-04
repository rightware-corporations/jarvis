"""Assistant state machine and UI event contract.

The voice loop is the only writer. Sinks (the future orb, an evidence log, test
recorders) only observe. Transitions outside ``ALLOWED_TRANSITIONS`` are refused so
that the visible state can never claim something the engine did not do (gate
``STATE_SYNC``).
"""

from __future__ import annotations

import json
import threading
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Protocol, runtime_checkable


class VoiceState(StrEnum):
    OFFLINE = "offline"
    IDLE = "idle"
    LISTENING = "listening"
    THINKING = "thinking"
    TOOL_RUNNING = "tool_running"
    AWAITING_CONFIRMATION = "awaiting_confirmation"
    SPEAKING = "speaking"
    MUTED = "muted"
    ERROR = "error"


_S = VoiceState

ALLOWED_TRANSITIONS: dict[VoiceState, frozenset[VoiceState]] = {
    _S.OFFLINE: frozenset({_S.IDLE, _S.ERROR}),
    _S.IDLE: frozenset({_S.LISTENING, _S.THINKING, _S.MUTED, _S.OFFLINE, _S.ERROR}),
    _S.LISTENING: frozenset({_S.THINKING, _S.IDLE, _S.SPEAKING, _S.MUTED, _S.ERROR}),
    _S.THINKING: frozenset(
        {_S.TOOL_RUNNING, _S.AWAITING_CONFIRMATION, _S.SPEAKING, _S.IDLE, _S.ERROR}
    ),
    _S.TOOL_RUNNING: frozenset(
        {_S.THINKING, _S.AWAITING_CONFIRMATION, _S.SPEAKING, _S.IDLE, _S.ERROR}
    ),
    _S.AWAITING_CONFIRMATION: frozenset({_S.LISTENING, _S.THINKING, _S.IDLE, _S.ERROR}),
    _S.SPEAKING: frozenset({_S.IDLE, _S.LISTENING, _S.ERROR}),
    _S.MUTED: frozenset({_S.IDLE, _S.OFFLINE}),
    _S.ERROR: frozenset({_S.IDLE, _S.SPEAKING, _S.OFFLINE}),
}


class InvalidTransitionError(RuntimeError):
    def __init__(self, current: VoiceState, requested: VoiceState) -> None:
        self.current = current
        self.requested = requested
        super().__init__(f"invalid state transition {current.value} -> {requested.value}")


@dataclass(frozen=True, slots=True)
class UiEvent:
    state: VoiceState
    previous: VoiceState
    session_id: str
    sequence: int
    ts: datetime
    request_id: str | None = None
    text: str | None = None
    detail: str | None = None
    metrics: dict[str, float] = field(default_factory=dict)


@runtime_checkable
class UiEventSink(Protocol):
    def publish(self, event: UiEvent) -> None: ...


class RecordingSink:
    """Keeps every event in memory; used by tests and diagnostics."""

    def __init__(self) -> None:
        self.events: list[UiEvent] = []
        self._lock = threading.Lock()

    def publish(self, event: UiEvent) -> None:
        with self._lock:
            self.events.append(event)

    @property
    def states(self) -> list[VoiceState]:
        with self._lock:
            return [event.state for event in self.events]


class FanOutSink:
    def __init__(self, sinks: Iterable[UiEventSink]) -> None:
        self._sinks = tuple(sinks)

    def publish(self, event: UiEvent) -> None:
        for sink in self._sinks:
            sink.publish(event)


class JsonlEventLog:
    """Sanitised evidence log: states, timings and lengths; text only if explicitly enabled."""

    def __init__(self, path: Path, *, include_text: bool = False) -> None:
        self.path = path
        self.include_text = include_text
        self._lock = threading.Lock()

    def publish(self, event: UiEvent) -> None:
        record: dict[str, object] = {
            "ts": event.ts.isoformat(),
            "seq": event.sequence,
            "session_id": event.session_id,
            "request_id": event.request_id,
            "from": event.previous.value,
            "to": event.state.value,
            "detail": event.detail,
            "metrics": event.metrics,
            "text_chars": len(event.text) if event.text else 0,
        }
        if self.include_text:
            record["text"] = event.text
        with self._lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(record, ensure_ascii=False) + "\n")


class StateMachine:
    """Thread-safe single source of truth for the assistant state."""

    def __init__(
        self,
        sink: UiEventSink,
        *,
        session_id: str,
        initial: VoiceState = VoiceState.OFFLINE,
    ) -> None:
        self._sink = sink
        self._session_id = session_id
        self._state = initial
        self._sequence = 0
        self._lock = threading.Lock()

    @property
    def state(self) -> VoiceState:
        with self._lock:
            return self._state

    def can_transition(self, target: VoiceState) -> bool:
        with self._lock:
            return target == self._state or target in ALLOWED_TRANSITIONS[self._state]

    def transition(
        self,
        target: VoiceState,
        *,
        request_id: str | None = None,
        text: str | None = None,
        detail: str | None = None,
        metrics: dict[str, float] | None = None,
    ) -> UiEvent | None:
        """Move to ``target`` and publish; repeating the current state is a no-op."""
        with self._lock:
            current = self._state
            if target == current:
                return None
            if target not in ALLOWED_TRANSITIONS[current]:
                raise InvalidTransitionError(current, target)
            self._state = target
            self._sequence += 1
            event = UiEvent(
                state=target,
                previous=current,
                session_id=self._session_id,
                sequence=self._sequence,
                ts=datetime.now(UTC),
                request_id=request_id,
                text=text,
                detail=detail,
                metrics=dict(metrics or {}),
            )
        self._sink.publish(event)
        return event
