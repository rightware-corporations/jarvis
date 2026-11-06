"""Vector rendering of the orb with QPainter (no bitmaps, no OpenGL, no web engine).

``paint_orb`` draws one ``OrbFrame`` into any QPainter target: the live widget or an
offscreen QImage (snapshots). Coordinates are logical pixels; Qt applies the device
pixel ratio, so the same code is sharp at 100 %, 150 % and 200 % scaling.
"""

from __future__ import annotations

import math

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QImage,
    QPainter,
    QPainterPath,
    QPen,
    QRadialGradient,
)

from apps.desktop.orb.visuals import OrbFrame, StateVisual, frame, visual_for
from jarvis.ui.events import VoiceState

TEXT_COLOUR = QColor("#e8f4ff")


def _colour(hex_value: str, alpha: float = 1.0) -> QColor:
    colour = QColor(hex_value)
    colour.setAlphaF(max(0.0, min(1.0, alpha)))
    return colour


def _mix(hex_a: str, hex_b: str, amount: float) -> QColor:
    """Opaque blend from ``hex_a`` (amount=0) to ``hex_b`` (amount=1)."""
    a, b = QColor(hex_a), QColor(hex_b)
    k = max(0.0, min(1.0, amount))
    return QColor(
        round(a.red() + (b.red() - a.red()) * k),
        round(a.green() + (b.green() - a.green()) * k),
        round(a.blue() + (b.blue() - a.blue()) * k),
    )


def paint_orb(
    painter: QPainter,
    area: QRectF,
    orb: OrbFrame,
    visual: StateVisual,
    *,
    show_label: bool = True,
) -> None:
    painter.save()
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    label_space = 26.0 if show_label else 0.0
    side = min(area.width(), area.height() - label_space)
    radius = side / 2.0 * 0.92
    centre = QPointF(area.center().x(), area.top() + side / 2.0)

    _halo(painter, centre, radius, visual, orb)
    _rings(painter, centre, radius, visual, orb)
    _core(painter, centre, radius, visual, orb)
    if orb.crossed:
        _slash(painter, centre, radius, visual)
    if show_label:
        _label(painter, area, side, visual)
    painter.restore()


def _halo(painter: QPainter, c: QPointF, r: float, v: StateVisual, f: OrbFrame) -> None:
    gradient = QRadialGradient(c, r)
    gradient.setColorAt(0.0, _colour(v.glow, 0.35 * f.glow_alpha))
    gradient.setColorAt(0.55, _colour(v.glow, 0.18 * f.glow_alpha))
    gradient.setColorAt(1.0, _colour(v.glow, 0.0))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QBrush(gradient))
    painter.drawEllipse(c, r, r)


def _rings(painter: QPainter, c: QPointF, r: float, v: StateVisual, f: OrbFrame) -> None:
    base = r * 0.78
    # Static outer ring (always present, gives the orb its shape).
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.setPen(QPen(_colour(v.glow, 0.45 * f.glow_alpha + 0.1), max(1.0, r * 0.018)))
    painter.drawEllipse(c, base, base)

    # Listening: rings travel outward and fade.
    for phase in f.ring_phases:
        radius = base * (0.62 + 0.38 * phase) + r * 0.2 * phase
        painter.setPen(QPen(_colour(v.glow, (1.0 - phase) * 0.8), max(1.0, r * 0.02)))
        painter.drawEllipse(c, radius, radius)

    rect = QRectF(c.x() - base, c.y() - base, base * 2, base * 2)
    if v.motion.value == "orbit":
        # Thinking: three arcs at different speeds and lengths.
        for k, (length, width) in enumerate(((110, 0.035), (70, 0.025), (40, 0.02))):
            pen = QPen(_colour(v.glow, 0.85 - k * 0.2), max(1.0, r * width))
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(pen)
            start = -(f.rotation * (1 + k * 0.6)) + k * 120
            inner = rect.adjusted(k * r * 0.07, k * r * 0.07, -k * r * 0.07, -k * r * 0.07)
            painter.drawArc(inner, int(start * 16), int(length * 16))
    elif v.motion.value == "segments":
        # Tool running: segmented ring with a bright sweeping head.
        segments = 24
        for k in range(segments):
            angle = (k * 360 / segments - f.rotation) % 360
            bright = 1.0 - (angle / 360.0)
            pen = QPen(_colour(v.glow, 0.15 + 0.85 * bright ** 3), max(1.0, r * 0.04))
            pen.setCapStyle(Qt.PenCapStyle.FlatCap)
            painter.setPen(pen)
            painter.drawArc(rect, int((k * 360 / segments) * 16), int((360 / segments - 4) * 16))
    elif f.bars:
        # Speaking: radial bars around the core.
        pen = QPen(_colour(v.glow, 0.9), max(1.0, r * 0.03))
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        inner = r * 0.56
        for k, length in enumerate(f.bars):
            angle = 2 * math.pi * k / len(f.bars) - math.pi / 2
            outer = inner + r * 0.30 * length
            painter.drawLine(
                QPointF(c.x() + inner * math.cos(angle), c.y() + inner * math.sin(angle)),
                QPointF(c.x() + outer * math.cos(angle), c.y() + outer * math.sin(angle)),
            )
    if f.pulse > 0:
        # Confirmation/error: an attention ring that swells with the pulse.
        radius = base + r * 0.12 * f.pulse
        painter.setPen(QPen(_colour(v.glow, 0.25 + 0.65 * f.pulse), max(1.0, r * 0.03)))
        painter.drawEllipse(c, radius, radius)


def _core(painter: QPainter, c: QPointF, r: float, v: StateVisual, f: OrbFrame) -> None:
    core = r * f.core_scale
    gradient = QRadialGradient(QPointF(c.x() - core * 0.3, c.y() - core * 0.35), core * 1.3)
    # Opaque specular highlight: blend towards white by the glow level (no dark hole).
    gradient.setColorAt(0.0, _mix(v.glow, "#ffffff", 0.25 + 0.55 * f.glow_alpha))
    gradient.setColorAt(0.30, _mix(v.core, v.glow, 0.85))
    gradient.setColorAt(1.0, _colour(v.core, 1.0))
    painter.setPen(QPen(_colour(v.glow, 0.6), max(1.0, r * 0.012)))
    painter.setBrush(QBrush(gradient))
    painter.drawEllipse(c, core, core)


def _slash(painter: QPainter, c: QPointF, r: float, v: StateVisual) -> None:
    pen = QPen(_colour("#d0d4da", 0.9), max(1.5, r * 0.05))
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    painter.setPen(pen)
    d = r * 0.42
    path = QPainterPath(QPointF(c.x() - d, c.y() + d))
    path.lineTo(QPointF(c.x() + d, c.y() - d))
    painter.drawPath(path)


def _label(painter: QPainter, area: QRectF, side: float, v: StateVisual) -> None:
    font = QFont()
    font.setPointSizeF(10.0)
    font.setBold(True)
    painter.setFont(font)
    painter.setPen(TEXT_COLOUR)
    box = QRectF(area.left(), area.top() + side, area.width(), area.height() - side)
    painter.drawText(box, int(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter), v.label)


def render_image(state: VoiceState, t: float, size: int = 240, scale: float = 2.0,
                 *, show_label: bool = True) -> QImage:
    """Offscreen snapshot: ``size`` logical pixels, rendered at ``scale`` device ratio."""
    pixels = int(size * scale)
    height = int((size + (26 if show_label else 0)) * scale)
    image = QImage(pixels, height, QImage.Format.Format_ARGB32_Premultiplied)
    image.setDevicePixelRatio(scale)
    image.fill(QColor(8, 12, 20, 255))
    painter = QPainter(image)
    try:
        paint_orb(painter, QRectF(0, 0, size, size + (26 if show_label else 0)),
                  frame(state, t), visual_for(state), show_label=show_label)
    finally:
        painter.end()
    return image
