"""Portable, non-destructive tests for the VEXEL Jarvis headless boundary."""
import asyncio
from uuid import uuid4

import pytest

from apps.weblab.headless import create_headless_assistant, memory_for_subject
from wyzer.brain.provider import FakeChatProvider
from wyzer.models import ChatMessage, ProviderChatResponse
from wyzer.tools.registry import UnknownToolError


def scripted_reply(text: str) -> ProviderChatResponse:
    return ProviderChatResponse(message=ChatMessage(role="assistant", content=text))


def test_headless_text_conversation_with_fake_provider():
    provider = FakeChatProvider([scripted_reply("Resposta simulada, sem IA real.")])
    assistant = create_headless_assistant(provider, subject_id="qa-user-A")
    response = asyncio.run(assistant.handle("Olá, Jarvis"))
    assert response.text == "Resposta simulada, sem IA real."
    assert len(provider.requests) == 1
    assert provider.requests[0][1] == []


def test_no_real_desktop_tools_are_registered():
    assistant = create_headless_assistant(FakeChatProvider(), subject_id="qa-user-A")
    for name in ("open_application", "run_powershell", "write_text_file", "delete_file", "power"):
        with pytest.raises(UnknownToolError):
            assistant.registry.get(name)


def test_unknown_tool_is_denied_by_executor():
    assistant = create_headless_assistant(FakeChatProvider(), subject_id="qa-user-A")
    result = asyncio.run(
        assistant._executor.execute("shutdown", {}, uuid4(), uuid4())
    )
    assert result.ok is False
    assert result.error is not None
    assert result.error.code == "UNKNOWN_TOOL"


def test_subject_specific_memory_isolation(tmp_path):
    alice = memory_for_subject(tmp_path, "account-A")
    bob = memory_for_subject(tmp_path, "account-B")
    alice.remember("Preferência de teste A")
    assert len(alice.list()) == 1
    assert bob.list() == []
    assert alice.database_path != bob.database_path
    bob.remember("Preferência de teste B")
    assert len(bob.list()) == 1
    assert alice.list()[0].content["fact"] == "Preferência de teste A"


def test_blank_subject_is_rejected():
    with pytest.raises(ValueError):
        create_headless_assistant(FakeChatProvider(), subject_id="")
