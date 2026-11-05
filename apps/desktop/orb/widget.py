"""Floating orb window: frameless, translucent, always on top, draggable.

Controls: drag with the left mouse button to move; Esc or double-click to close.
The widget only reads ``OrbStateModel``; it never calls the assistant.
"""

from __future__ import annotations

import time

from PySide6.QtCore import QPoint, QRectF, Qt, QTimer
from PySide6.QtGui import QCloseEvent, QKeyEvent, QMouseEvent, QPainter, QPaintEvent
from PySide6.QtWidgets import QWidget

from apps.desktop.orb.model import OrbStateModel
from apps.desktop.orb.render import paint_orb
from apps.desktop.orb.visuals import frame, visual_for


class OrbWidget(QWidget):
    def __init__(
        self,
        model: OrbStateModel,
        *,
        size: int = 220,
        show_label: bool = True,
        frameless: bool = True,
        clock=time.monotonic,
    ) -> None:
        super().__init__()
        self.model = model
        self.show_label = show_label
        self._clock = clock
        self._t0 = clock()
        self._drag: QPoint | None = None
        self.on_close = None
        self.setWindowTitle("VEXEL Jarvis")
        if frameless:
            self.setWindowFlags(
                Qt.WindowType.FramelessWindowHint
                | Qt.WindowType.WindowStaysOnTopHint
                | Qt.WindowType.Tool
            )
            self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        # Minimum (not fixed) size: Qt scales it for 125–200 % DPI without clipping.
        self.setMinimumSize(size, size + (26 if show_label else 0))
        self.resize(size, size + (26 if show_label else 0))
        self._animation = QTimer(self)
        self._animation.setInterval(16)  # ~60 fps
        self._animation.timeout.connect(self.update)
        self._animation.start()

    # ------------------------------------------------------------------ painting

    def elapsed(self) -> float:
        return self._clock() - self._t0

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: N802 (Qt API)
        painter = QPainter(self)
        try:
            state = self.model.state
            paint_orb(painter, QRectF(self.rect()), frame(state, self.elapsed()),
                      visual_for(state), show_label=self.show_label)
        finally:
            painter.end()

    def state_changed(self) -> None:
        self.setToolTip(f"Jarvis: {visual_for(self.model.state).label}")
        self.update()

    # ------------------------------------------------------------------ input

    def mousePressEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if self._drag is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        self._drag = None

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        self.close()

    def keyPressEvent(self, event: QKeyEvent) -> None:  # noqa: N802
        if event.key() == Qt.Key.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)

    # ------------------------------------------------------------------ shutdown

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802
        self._animation.stop()
        if callable(self.on_close):
            self.on_close()
        super().closeEvent(event)
