"""Moves ``UiEvent``s from any thread to the Qt GUI thread.

Producers (the voice loop, the demo driver) publish into ``jarvis.ui.QueueSink`` from
whatever thread they run on. ``OrbEventPump`` drains that queue with a ``QTimer`` on
the GUI thread, so no Qt object is ever touched from a worker thread and no signal is
emitted from one (PySide6 rule: emit only from the owning thread).
"""

from __future__ import annotations

import threading
from collections.abc import Callable

from PySide6.QtCore import QObject, QTimer

from apps.desktop.orb.model import OrbStateModel
from jarvis.ui.events import QueueSink


class OrbEventPump(QObject):
    def __init__(
        self,
        queue: QueueSink,
        model: OrbStateModel,
        on_change: Callable[[], None],
        *,
        interval_ms: int = 33,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._queue = queue
        self._model = model
        self._on_change = on_change
        self.drain_threads: set[int] = set()
        self._timer = QTimer(self)
        self._timer.setInterval(interval_ms)
        self._timer.timeout.connect(self.drain)

    def start(self) -> None:
        self._timer.start()

    def stop(self) -> None:
        self._timer.stop()

    def drain(self) -> None:
        events = self._queue.drain()
        if not events:
            return
        self.drain_threads.add(threading.get_ident())
        if self._model.apply(events):
            self._on_change()
