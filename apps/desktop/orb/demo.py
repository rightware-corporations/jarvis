"""Simulated event source for the demo: no model, microphone, voice or tools needed.

Drives a real ``jarvis.ui.StateMachine`` (so only valid transitions are produced) from
a background thread into a ``QueueSink``. The scripted path visits all nine states.
"""

from __future__ import annotations

import threading

from jarvis.ui.events import QueueSink, StateMachine, VoiceState

S = VoiceState
# One full scripted conversation; every step is a valid transition from the previous.
DEMO_SCRIPT: tuple[tuple[VoiceState, float], ...] = (
    (S.IDLE, 1.5),
    (S.LISTENING, 2.0),
    (S.THINKING, 1.8),
    (S.TOOL_RUNNING, 1.6),
    (S.SPEAKING, 2.4),
    (S.IDLE, 1.2),
    (S.LISTENING, 1.6),
    (S.THINKING, 1.2),
    (S.AWAITING_CONFIRMATION, 2.4),
    (S.LISTENING, 1.2),
    (S.THINKING, 1.0),
    (S.SPEAKING, 1.8),
    (S.IDLE, 1.0),
    (S.MUTED, 1.8),
    (S.IDLE, 0.8),
    (S.ERROR, 1.6),
    (S.IDLE, 1.0),
)


class DemoDriver:
    def __init__(
        self,
        sink: QueueSink,
        *,
        loop: bool = True,
        speed: float = 1.0,
        script: tuple[tuple[VoiceState, float], ...] = DEMO_SCRIPT,
    ) -> None:
        self.machine = StateMachine(sink, session_id="demo")
        self.loop = loop
        self.speed = speed
        self.script = script
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, name="orb-demo", daemon=True)
        self.thread_id: int | None = None
        self.steps = 0

    def start(self) -> None:
        self._thread.start()

    def stop(self, timeout: float = 2.0) -> bool:
        """Signal and join. Returns True if the thread has ended."""
        self._stop.set()
        if self._thread.is_alive():
            self._thread.join(timeout)
        return not self._thread.is_alive()

    @property
    def alive(self) -> bool:
        return self._thread.is_alive()

    def _run(self) -> None:
        self.thread_id = threading.get_ident()
        generation = 0
        while not self._stop.is_set():
            for state, seconds in self.script:
                if self._stop.is_set():
                    return
                if self.machine.can_transition(state):
                    self.machine.transition(state, detail="demo", generation=generation)
                    self.steps += 1
                if self._stop.wait(seconds / self.speed):
                    return
            if not self.loop:
                return
            generation += 1
