"""Compose the Wyzer Orchestrator with the closed allowlist and an injected provider.

This deliberately does not call ``wyzer.app.bootstrap.build_assistant``: that path
registers every Wyzer pack. Here the registry contains exactly the three slice tools,
memory, tasks and the coding agent are off, and the provider is whatever is injected
(the local Ollama provider in 01C, a fake in tests).
"""

from __future__ import annotations

from dataclasses import dataclass

from wyzer.app.orchestrator import Orchestrator
from wyzer.brain.provider import ChatProvider
from wyzer.policy import ConfirmationPolicy
from wyzer.tools import ToolRegistry
from wyzer.workers.in_process import InProcessExecutor

from jarvis.brain.pt_provider import PortugueseProvider
from jarvis.config import SliceConfig
from jarvis.core.voice_loop import VoiceSession
from jarvis.tools.allowlist import (
    ApplicationLauncher,
    Clock,
    PsutilSystemProbe,
    SimulatedLauncher,
    SystemProbe,
    ToolStartedCallback,
    build_allowlist_registry,
)
from jarvis.ui.events import UiEventSink
from jarvis.voice.contracts import Activation, SpeechToText, TextToSpeech

PERSONALITY: dict[str, object] = {
    "assistant_name": "Jarvis",
    "tone": "concise and professional",
    "response_length": "concise",
}


@dataclass(frozen=True)
class AssistantParts:
    orchestrator: Orchestrator
    registry: ToolRegistry
    provider: PortugueseProvider
    launcher: ApplicationLauncher


def build_slice_assistant(
    config: SliceConfig,
    provider: ChatProvider,
    *,
    launcher: ApplicationLauncher | None = None,
    probe: SystemProbe | None = None,
    clock: Clock | None = None,
    on_tool_start: ToolStartedCallback | None = None,
    confirmation_ttl_seconds: float | None = None,
) -> AssistantParts:
    chosen_launcher = launcher if launcher is not None else SimulatedLauncher()
    registry = build_allowlist_registry(
        timezone=config.vexel.timezone,
        allowed_applications=config.vexel.allowed_applications,
        launcher=chosen_launcher,
        probe=probe if probe is not None else PsutilSystemProbe(),
        clock=clock,
        on_tool_start=on_tool_start or (lambda _name: None),
    )
    wrapped = provider if isinstance(provider, PortugueseProvider) else PortugueseProvider(provider)
    ttl = (
        confirmation_ttl_seconds
        if confirmation_ttl_seconds is not None
        else config.wyzer.confirmation_ttl_seconds
    )
    orchestrator = Orchestrator(
        registry,
        InProcessExecutor(registry),
        wrapped,
        maximum_tool_rounds=config.wyzer.maximum_tool_rounds,
        confirmation_policy=ConfirmationPolicy(ttl),
        memory=None,
        tasks=None,
        coding_manager=None,
        personality=PERSONALITY,
    )
    return AssistantParts(orchestrator, registry, wrapped, chosen_launcher)


def build_voice_session(
    config: SliceConfig,
    provider: ChatProvider,
    *,
    stt: SpeechToText,
    tts: TextToSpeech,
    activation: Activation,
    sink: UiEventSink,
    launcher: ApplicationLauncher | None = None,
    probe: SystemProbe | None = None,
    clock: Clock | None = None,
    confirmation_ttl_seconds: float | None = None,
    session_id: str = "local",
) -> tuple[VoiceSession, AssistantParts]:
    """Wire tools → session so TOOL_RUNNING is published from the allowlisted tools."""
    holder: list[VoiceSession] = []

    def tool_started(name: str) -> None:
        if holder:
            holder[0].on_tool_start(name)

    parts = build_slice_assistant(
        config,
        provider,
        launcher=launcher,
        probe=probe,
        clock=clock,
        on_tool_start=tool_started,
        confirmation_ttl_seconds=confirmation_ttl_seconds,
    )
    session = VoiceSession(
        parts.orchestrator,
        stt=stt,
        tts=tts,
        activation=activation,
        sink=sink,
        settings=config.vexel,
        session_id=session_id,
    )
    holder.append(session)
    return session, parts
