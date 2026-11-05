"""Test-only, fail-closed headless composition of the upstream Wyzer core.

Do not deploy directly as a public HTTP server. This module deliberately omits
Windows packs, Chrome automation, coding agent, shell and real desktop actions.
An authenticated API boundary and separate tenant/session management are still
required before exposing the assistant to any network client.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

from wyzer.app import Orchestrator
from wyzer.brain.provider import ChatProvider
from wyzer.models import ChatMessage, ProviderChatResponse

# Explicit adapter-level sentinel; must never contain provider exception details.
MODEL_FAILURE_SENTINEL = "[JARVIS_LAB_PROVIDER_FAILED]"


class SafeLabProvider:
    """Translate upstream provider failures into a fixed, non-sensitive lab result."""

    def __init__(self, inner: ChatProvider) -> None:
        self.inner = inner

    @property
    def available(self) -> bool:
        return self.inner.available

    async def chat(self, messages, tools, settings=None) -> ProviderChatResponse:
        try:
            return await self.inner.chat(messages, tools, settings)
        except Exception:
            return ProviderChatResponse(
                message=ChatMessage(
                    role="assistant",
                    content=MODEL_FAILURE_SENTINEL,
                )
            )

from wyzer.memory import MemoryStore
from wyzer.tools import ToolRegistry
from wyzer.workers.in_process import InProcessExecutor


def _subject_scope(subject_id: str) -> str:
    if not isinstance(subject_id, str) or not subject_id.strip() or len(subject_id) > 256:
        raise ValueError("A nonempty, bounded subject_id is required")
    return hashlib.sha256(subject_id.encode("utf-8")).hexdigest()


def memory_for_subject(storage_dir: Path, subject_id: str) -> MemoryStore:
    """Store facts in a subject-scoped SQLite file; never reuse a shared DB."""
    scope = _subject_scope(subject_id)
    return MemoryStore(Path(storage_dir) / scope / "memory.db")


def create_headless_assistant(
    provider: ChatProvider,
    *,
    subject_id: str,
    storage_dir: Path | None = None,
) -> Orchestrator:
    """Instantiate the original Orchestrator without executable desktop tools.

    A simulated provider may be injected for contract tests. An actual hosted
    Ollama provider is a separate integration step with network authentication.
    Memory persistence is off unless a subject-specific storage root is supplied.
    """
    _subject_scope(subject_id)
    registry = ToolRegistry()  # no OS, browser, coding, network or shell tools
    executor = InProcessExecutor(registry)
    memory = (
        memory_for_subject(storage_dir, subject_id)
        if storage_dir is not None
        else None
    )
    return Orchestrator(
        registry,
        executor,
        SafeLabProvider(provider),
        memory=memory,
        tasks=None,
        coding_manager=None,
        maximum_tool_rounds=4,
        personality={
            "assistant_name": "Jarvis",
            "tone": "concise and professional",
            "response_length": "concise",
        },
    )
