from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import dataclass, replace
from typing import Any

import pytest

from jarvis.core.assistant import AssistantParts, build_voice_session
from jarvis.core.voice_loop import VoiceSession
from jarvis.tools.allowlist import SimulatedLauncher
from jarvis.ui.events import RecordingSink, UiEventSink
from tests_vexel.fakes import (
    FIXED_NOW,
    REPO_ROOT,
    FixedProbe,
    ImmediateActivation,
    RecordingTts,
    ScriptedProvider,
    ScriptedStt,
    slice_config,
)

# ------------------------------------------------------------ process guard
# Test 10 / R01-P1: no process may be started during the suite except the repository's
# own read-only integrity verifier. Any other spawn fails the test that caused it.

SPAWN_ATTEMPTS: list[Any] = []
_ALLOWED_SCRIPT = str(REPO_ROOT / "scripts" / "verify_import.py")
_REAL_POPEN = subprocess.Popen


class _GuardedPopen(_REAL_POPEN):  # type: ignore[misc, valid-type]
    def __init__(self, args: Any, *rest: Any, **kwargs: Any) -> None:
        argv = list(args) if isinstance(args, (list, tuple)) else [args]
        if argv[:2] != [sys.executable, _ALLOWED_SCRIPT]:
            SPAWN_ATTEMPTS.append(argv)
            raise AssertionError(f"process spawn blocked in tests: {argv!r}")
        super().__init__(args, *rest, **kwargs)


def _blocked(name: str):
    def guard(*args: Any, **kwargs: Any) -> Any:
        SPAWN_ATTEMPTS.append([name, *args])
        raise AssertionError(f"{name} blocked in tests")

    return guard


@pytest.fixture(autouse=True)
def _no_process_spawn(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(subprocess, "Popen", _GuardedPopen)
    for name in ("system", "startfile", "posix_spawn", "posix_spawnp", "execv", "execve"):
        if hasattr(os, name):
            monkeypatch.setattr(os, name, _blocked(f"os.{name}"))


# -------------------------------------------------------------------- rig


@dataclass
class Rig:
    session: VoiceSession
    parts: AssistantParts
    provider: ScriptedProvider
    stt: ScriptedStt
    tts: Any
    sink: RecordingSink
    launcher: Any
    probe: FixedProbe

    @property
    def pending(self):
        return self.parts.orchestrator.world.snapshot().pending_confirmation


def make_rig(
    *,
    ttl: float | None = None,
    delay: float = 0.0,
    tts: Any = None,
    provider: ScriptedProvider | None = None,
    launcher: Any = None,
    sink: UiEventSink | None = None,
    allowed: tuple[str, ...] | None = None,
) -> Rig:
    chosen_provider = provider or ScriptedProvider(delay=delay)
    stt = ScriptedStt()
    speech = tts or RecordingTts()
    recorder = RecordingSink()
    chosen_launcher = launcher or SimulatedLauncher()
    probe = FixedProbe()
    config = slice_config()
    if allowed is not None:
        config = replace(
            config, vexel=config.vexel.model_copy(update={"allowed_applications": allowed})
        )
    session, parts = build_voice_session(
        config,
        chosen_provider,
        stt=stt,
        tts=speech,
        activation=ImmediateActivation(),
        sink=sink or recorder,
        launcher=chosen_launcher,
        probe=probe,
        clock=lambda: FIXED_NOW,
        confirmation_ttl_seconds=ttl,
    )
    session.start()
    return Rig(session, parts, chosen_provider, stt, speech, recorder, chosen_launcher, probe)


@pytest.fixture
def rig() -> Rig:
    return make_rig()
