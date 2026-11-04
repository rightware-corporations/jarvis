from __future__ import annotations

from dataclasses import dataclass

import pytest

from jarvis.core.assistant import AssistantParts, build_voice_session
from jarvis.core.voice_loop import VoiceSession
from jarvis.tools.allowlist import SimulatedLauncher
from jarvis.ui.events import RecordingSink
from tests_vexel.fakes import (
    FIXED_NOW,
    FixedProbe,
    ImmediateActivation,
    RecordingTts,
    ScriptedProvider,
    ScriptedStt,
    slice_config,
)


@dataclass
class Rig:
    session: VoiceSession
    parts: AssistantParts
    provider: ScriptedProvider
    stt: ScriptedStt
    tts: RecordingTts
    sink: RecordingSink
    launcher: SimulatedLauncher
    probe: FixedProbe

    @property
    def pending(self):
        return self.parts.orchestrator.world.snapshot().pending_confirmation


def make_rig(*, ttl: float | None = None, delay: float = 0.0, tts: RecordingTts | None = None) -> Rig:
    provider = ScriptedProvider(delay=delay)
    stt = ScriptedStt()
    speech = tts or RecordingTts()
    sink = RecordingSink()
    launcher = SimulatedLauncher()
    probe = FixedProbe()
    session, parts = build_voice_session(
        slice_config(),
        provider,
        stt=stt,
        tts=speech,
        activation=ImmediateActivation(),
        sink=sink,
        launcher=launcher,
        probe=probe,
        clock=lambda: FIXED_NOW,
        confirmation_ttl_seconds=ttl,
    )
    session.start()
    return Rig(session, parts, provider, stt, speech, sink, launcher, probe)


@pytest.fixture
def rig() -> Rig:
    return make_rig()
