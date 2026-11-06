"""Assemble and run the orb: model + pump + widget (+ optional demo driver)."""

from __future__ import annotations

import signal
import sys
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QApplication

from apps.desktop.orb.demo import DemoDriver
from apps.desktop.orb.model import OrbStateModel
from apps.desktop.orb.pump import OrbEventPump
from apps.desktop.orb.widget import OrbWidget
from jarvis.ui.events import QueueSink, VoiceState


def ensure_application(argv: list[str] | None = None) -> QApplication:
    app = QApplication.instance()
    if app is None:
        # High-DPI: keep fractional scale factors (125 %, 150 %) instead of rounding.
        QGuiApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )
        app = QApplication(argv or sys.argv[:1])
    return app  # type: ignore[return-value]


@dataclass
class OrbApp:
    queue: QueueSink
    model: OrbStateModel
    pump: OrbEventPump
    widget: OrbWidget
    demo: DemoDriver | None

    def shutdown(self) -> bool:
        """Stop producers first, then the pump (idempotent).

        Returns True only if everything really stopped: the demo thread joined and no
        timer is still active. Safe to call after the widget (and the pump, its Qt
        child) has been deleted.
        """
        stopped = True
        if self.demo is not None:
            stopped = self.demo.stop() and stopped
        try:
            self.pump.stop()
            self.pump.drain()
            stopped = not self.pump.active and stopped
        except RuntimeError:  # C++ object already deleted with its parent widget
            pass
        return stopped


def build_orb(*, demo: bool, loop: bool = True, speed: float = 1.0, size: int = 220,
              frameless: bool = True) -> OrbApp:
    queue = QueueSink(maxlen=256)
    model = OrbStateModel()
    widget = OrbWidget(model, size=size, frameless=frameless)
    pump = OrbEventPump(queue, model, widget.state_changed, parent=widget)
    driver = DemoDriver(queue, loop=loop, speed=speed) if demo else None
    orb = OrbApp(queue, model, pump, widget, driver)
    widget.on_close = orb.shutdown
    return orb


def save_snapshots(directory: Path, *, scale: float = 2.0, t: float = 0.37) -> list[Path]:
    from apps.desktop.orb.render import render_image

    directory.mkdir(parents=True, exist_ok=True)
    written = []
    for state in VoiceState:
        path = directory / f"orb-{state.value}.png"
        if not render_image(state, t, scale=scale).save(str(path)):
            raise OSError(f"could not write {path}")
        written.append(path)
    return written


def run(*, demo: bool = True, loop: bool = True, speed: float = 1.0,
        duration: float | None = None) -> int:
    app = ensure_application()
    orb = build_orb(demo=demo, loop=loop, speed=speed)

    clean = {"ok": True}

    def close_and_quit() -> None:
        # Qt::Tool windows do not count for quitOnLastWindowClosed: quit explicitly,
        # after the producers and the pump have stopped.
        clean["ok"] = orb.shutdown()
        app.quit()

    orb.widget.on_close = close_and_quit
    # Ctrl+C in the console closes the window cleanly.
    signal.signal(signal.SIGINT, lambda *_: orb.widget.close())
    keepalive = QTimer()
    keepalive.start(200)  # lets Python handle signals while Qt's loop runs
    keepalive.timeout.connect(lambda: None)
    if duration is not None:
        QTimer.singleShot(int(duration * 1000), orb.widget.close)
    orb.widget.show()
    orb.pump.start()
    if orb.demo is not None:
        orb.demo.start()
    code = app.exec()
    clean["ok"] = orb.shutdown() and clean["ok"]
    if code == 0 and not clean["ok"]:
        print("orb: shutdown incomplete (demo thread or timer still running)", file=sys.stderr)
        return 2
    return code
