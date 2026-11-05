"""State → visual parameters. Pure Python, no Qt, fully deterministic.

Every ``VoiceState`` has exactly one ``StateVisual``. ``frame(state, t)`` turns it into
the numbers the renderer draws at time ``t`` (seconds). Same inputs → same frame, so
snapshots and tests are reproducible. The palette is provisional (design review
pending); semantics are fixed: colour = state family, motion = what the engine does.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import StrEnum

from jarvis.ui.events import VoiceState


class Motion(StrEnum):
    STILL = "still"          # offline: nothing happens
    BREATHE = "breathe"      # idle: slow, calm
    RIPPLE = "ripple"        # listening: rings move outward (sound coming in)
    ORBIT = "orbit"          # thinking: arcs rotate
    SEGMENTS = "segments"    # tool running: segmented ring sweeps
    PULSE = "pulse"          # awaiting confirmation: steady attention pulse
    WAVE = "wave"            # speaking: radial bars like a voice waveform
    DIMMED = "dimmed"        # muted: low, still, crossed
    ALERT = "alert"          # error: sharp flicker


@dataclass(frozen=True, slots=True)
class StateVisual:
    state: VoiceState
    label: str                     # short Portuguese caption
    core: str                      # core colour (hex)
    glow: str                      # halo/rings colour (hex)
    motion: Motion
    speed: float                   # cycles per second of the main motion
    intensity: float               # 0..1 brightness of glow and rings


VISUALS: dict[VoiceState, StateVisual] = {
    VoiceState.OFFLINE: StateVisual(VoiceState.OFFLINE, "Desligado", "#3a4450", "#5b6672", Motion.STILL, 0.0, 0.15),
    VoiceState.IDLE: StateVisual(VoiceState.IDLE, "Pronto", "#1f6fd1", "#4fb3ff", Motion.BREATHE, 0.20, 0.55),
    VoiceState.LISTENING: StateVisual(VoiceState.LISTENING, "A ouvir", "#00a8e8", "#5ff0ff", Motion.RIPPLE, 0.90, 0.85),
    VoiceState.THINKING: StateVisual(VoiceState.THINKING, "A pensar", "#5a3fd8", "#a48bff", Motion.ORBIT, 0.60, 0.80),
    VoiceState.TOOL_RUNNING: StateVisual(VoiceState.TOOL_RUNNING, "A executar", "#0f9f8f", "#5fffd8", Motion.SEGMENTS, 0.75, 0.85),
    VoiceState.AWAITING_CONFIRMATION: StateVisual(VoiceState.AWAITING_CONFIRMATION, "Confirma: sim ou não?", "#d98a00", "#ffd166", Motion.PULSE, 0.70, 0.95),
    VoiceState.SPEAKING: StateVisual(VoiceState.SPEAKING, "A falar", "#00b4d8", "#90f1ff", Motion.WAVE, 1.20, 0.90),
    VoiceState.MUTED: StateVisual(VoiceState.MUTED, "Silenciado", "#4a4f57", "#8a929c", Motion.DIMMED, 0.0, 0.25),
    VoiceState.ERROR: StateVisual(VoiceState.ERROR, "Erro", "#c62828", "#ff6b6b", Motion.ALERT, 2.50, 1.00),
}


@dataclass(frozen=True, slots=True)
class OrbFrame:
    state: VoiceState
    core_scale: float        # core radius as a fraction of the orb radius (0.40..0.62)
    glow_alpha: float        # 0..1
    ring_phases: tuple[float, ...]  # each 0..1: position of an expanding ring (ripple)
    rotation: float          # degrees, for orbit/segments
    bars: tuple[float, ...]  # 0..1 lengths of radial bars (wave); empty otherwise
    pulse: float             # 0..1 attention pulse (confirmation/error)
    crossed: bool            # draw the muted slash


BAR_COUNT = 36


def visual_for(state: VoiceState) -> StateVisual:
    return VISUALS[state]


def frame(state: VoiceState, t: float) -> OrbFrame:
    """Deterministic frame for ``state`` at ``t`` seconds."""
    v = VISUALS[state]
    phase = (t * v.speed) % 1.0
    wave = 0.5 - 0.5 * math.cos(2 * math.pi * phase)  # smooth 0..1..0
    core = 0.50
    glow = v.intensity
    rings: tuple[float, ...] = ()
    rotation = 0.0
    bars: tuple[float, ...] = ()
    pulse = 0.0

    if v.motion is Motion.STILL:
        core, glow = 0.46, v.intensity
    elif v.motion is Motion.BREATHE:
        core = 0.48 + 0.04 * wave
        glow = v.intensity * (0.75 + 0.25 * wave)
    elif v.motion is Motion.RIPPLE:
        core = 0.50 + 0.02 * wave
        rings = tuple(((phase + k / 3.0) % 1.0) for k in range(3))
    elif v.motion is Motion.ORBIT:
        rotation = 360.0 * phase
        core = 0.49 + 0.02 * wave
    elif v.motion is Motion.SEGMENTS:
        rotation = 360.0 * phase
        core = 0.50
    elif v.motion is Motion.PULSE:
        pulse = wave
        core = 0.50 + 0.05 * wave
        glow = v.intensity * (0.70 + 0.30 * wave)
    elif v.motion is Motion.WAVE:
        bars = tuple(
            0.25 + 0.75 * (0.5 + 0.5 * math.sin(2 * math.pi * (phase * 2 + k * 0.137) + k * 0.9))
            * (0.6 + 0.4 * math.sin(math.pi * k / BAR_COUNT))
            for k in range(BAR_COUNT)
        )
        core = 0.48 + 0.04 * wave
    elif v.motion is Motion.DIMMED:
        core, glow = 0.44, v.intensity
    elif v.motion is Motion.ALERT:
        # Square-ish flicker: readable as an alarm, not a calm pulse.
        pulse = 1.0 if phase < 0.5 else 0.35
        glow = v.intensity * pulse
        core = 0.52

    return OrbFrame(
        state=state,
        core_scale=round(core, 6),
        glow_alpha=round(max(0.0, min(1.0, glow)), 6),
        ring_phases=tuple(round(r, 6) for r in rings),
        rotation=round(rotation % 360.0, 6),
        bars=tuple(round(max(0.0, min(1.0, b)), 6) for b in bars),
        pulse=round(pulse, 6),
        crossed=v.motion is Motion.DIMMED,
    )
