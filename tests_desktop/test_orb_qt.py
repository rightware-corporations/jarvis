"""Qt behaviour, offscreen: rendering, thread-safe delivery, DPI and shutdown."""

from __future__ import annotations

import hashlib
import threading
from pathlib import Path

import pytest

from tests_desktop.conftest import process_events_until

from apps.desktop.orb.app import build_orb, save_snapshots  # noqa: E402
from apps.desktop.orb.render import render_image  # noqa: E402
from apps.desktop.orb.visuals import VISUALS  # noqa: E402
from jarvis.ui.events import StateMachine, VoiceState  # noqa: E402


def _digest(image) -> str:
    bits = image.constBits()
    return hashlib.sha256(bytes(bits)).hexdigest()


@pytest.mark.parametrize("state", list(VoiceState), ids=lambda s: s.value)
def test_each_state_renders_its_colour_at_the_core(qapp, state: VoiceState) -> None:
    image = render_image(state, 0.37, size=200, scale=1.0, show_label=False)
    centre = image.pixelColor(100, 112)  # a bit below the specular highlight
    core = VISUALS[state].core
    from PySide6.QtGui import QColor

    target = QColor(core)
    distance = abs(centre.red() - target.red()) + abs(centre.green() - target.green()) + abs(centre.blue() - target.blue())
    assert distance < 260, (state, centre.name(), core)


def test_states_produce_different_images(qapp) -> None:
    # Labels off: the orb graphics alone must differ per state.
    digests = {_digest(render_image(state, 0.37, size=120, scale=1.0, show_label=False)) for state in VoiceState}
    assert len(digests) == len(VoiceState)


def test_rendering_is_deterministic(qapp) -> None:
    a = render_image(VoiceState.SPEAKING, 1.234, size=120, scale=1.0)
    b = render_image(VoiceState.SPEAKING, 1.234, size=120, scale=1.0)
    assert _digest(a) == _digest(b)


@pytest.mark.parametrize("scale", [1.0, 1.25, 1.5, 2.0])
def test_high_dpi_snapshots_scale_device_pixels(qapp, scale: float) -> None:
    image = render_image(VoiceState.IDLE, 0.0, size=200, scale=scale)
    assert image.width() == int(200 * scale)
    assert image.devicePixelRatio() == pytest.approx(scale)


def test_snapshot_cli_writes_one_png_per_state(qapp, tmp_path: Path) -> None:
    paths = save_snapshots(tmp_path, scale=1.0)
    assert sorted(p.name for p in paths) == sorted(f"orb-{s.value}.png" for s in VoiceState)
    assert all(p.stat().st_size > 1000 for p in paths)


def test_events_from_a_worker_thread_are_applied_on_the_gui_thread(qapp) -> None:
    orb = build_orb(demo=False, frameless=False)
    machine = StateMachine(orb.queue, session_id="t")
    gui_thread = threading.get_ident()

    def produce() -> None:
        for target in (VoiceState.IDLE, VoiceState.LISTENING, VoiceState.THINKING,
                       VoiceState.AWAITING_CONFIRMATION):
            machine.transition(target)

    worker = threading.Thread(target=produce)
    worker.start()
    worker.join()
    orb.pump.start()
    assert process_events_until(qapp, lambda: orb.model.state is VoiceState.AWAITING_CONFIRMATION)
    assert orb.pump.drain_threads == {gui_thread}
    assert list(orb.model.history) == [VoiceState.IDLE, VoiceState.LISTENING, VoiceState.THINKING,
                                 VoiceState.AWAITING_CONFIRMATION]
    orb.shutdown()
    orb.widget.deleteLater()


def test_widget_paints_every_state(qapp) -> None:
    orb = build_orb(demo=False, frameless=False)
    for state in VoiceState:
        orb.model.state = state
        pixmap = orb.widget.grab()
        assert not pixmap.isNull() and pixmap.width() >= 220
    orb.widget.deleteLater()


def test_demo_runs_and_shuts_down_cleanly(qapp) -> None:
    orb = build_orb(demo=True, speed=40.0)
    orb.widget.show()
    orb.pump.start()
    orb.demo.start()
    wanted = {VoiceState.AWAITING_CONFIRMATION, VoiceState.ERROR, VoiceState.MUTED}
    assert process_events_until(qapp, lambda: wanted <= set(orb.model.history), timeout=8.0)
    assert orb.demo.thread_id != threading.get_ident()
    orb.widget.close()  # closeEvent -> shutdown: stop demo, stop pump
    assert not orb.demo.alive
    assert not orb.pump.active
    assert not orb.widget._animation.isActive()
    assert orb.shutdown() is True  # idempotent, reports a complete stop
    orb.widget.deleteLater()


def test_desktop_package_never_imports_the_assistant_or_tools() -> None:
    """Allow-list: a fresh interpreter importing the orb may load only jarvis.ui."""
    import subprocess
    import sys

    code = (
        "import sys, apps.desktop.orb.app, apps.desktop.__main__;"
        "print(','.join(sorted(m for m in sys.modules if m.split('.')[0] in ('jarvis','wyzer'))))"
    )
    root = Path(__file__).resolve().parents[1]
    out = subprocess.run([sys.executable, "-c", code], cwd=root, capture_output=True, text=True,
                         timeout=60, check=True, env={**__import__("os").environ, "QT_QPA_PLATFORM": "offscreen"})
    assert set(out.stdout.strip().split(",")) <= {"jarvis", "jarvis.ui", "jarvis.ui.events"}, out.stdout


def test_shutdown_is_safe_after_the_widget_is_deleted(qapp) -> None:
    orb = build_orb(demo=True, speed=40.0)
    orb.widget.deleteLater()
    from tests_desktop.conftest import process_events_until as pump_events
    import shiboken6

    pump_events(qapp, lambda: not shiboken6.isValid(orb.widget), timeout=2.0)
    orb.shutdown()  # must not raise
    assert not orb.demo.alive


def test_still_states_repaint_rarely(qapp) -> None:
    from apps.desktop.orb.widget import FRAME_MS, STILL_FRAME_MS

    orb = build_orb(demo=False, frameless=False)
    for state, expected in ((VoiceState.MUTED, STILL_FRAME_MS), (VoiceState.SPEAKING, FRAME_MS),
                            (VoiceState.OFFLINE, STILL_FRAME_MS)):
        orb.model.state = state
        orb.widget.state_changed()
        assert orb.widget.animation_interval == expected
    orb.widget.deleteLater()
