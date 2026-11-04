"""Test 2 — full conversation cycle with a simulated provider (no network)."""

from __future__ import annotations

import asyncio

from jarvis.brain.pt_provider import PORTUGUESE_INSTRUCTION, PortugueseProvider
from jarvis.core.voice_loop import TurnOutcome
from jarvis.language.prompts import SAY_MODEL_UNAVAILABLE
from jarvis.ui.events import VoiceState
from tests_vexel.conftest import make_rig
from tests_vexel.fakes import ExplodingProvider, call, say


def test_plain_chat_reply_is_spoken_in_portuguese() -> None:
    rig = make_rig()
    rig.provider.push(say("Olá! Em que posso ajudar?"))
    result = asyncio.run(rig.session.handle_text("Olá Jarvis"))
    assert result.outcome is TurnOutcome.ANSWERED
    assert rig.tts.spoken == ["Olá! Em que posso ajudar?"]
    assert rig.session.state is VoiceState.IDLE
    system = rig.provider.requests[0][0][0]
    assert system.role == "system" and PORTUGUESE_INSTRUCTION in (system.content or "")


def test_que_horas_sao_uses_time_tool_with_injected_clock() -> None:
    rig = make_rig()
    rig.provider.push(call("get_local_time"), say("São catorze e trinta."))
    result = asyncio.run(rig.session.handle_text("Que horas são?"))
    assert result.outcome is TurnOutcome.ANSWERED
    assert rig.tts.spoken == ["São catorze e trinta."]
    tool_messages = [m for m in rig.provider.requests[1][0] if m.role == "tool"]
    assert tool_messages and '"hour":14' in (tool_messages[0].content or "").replace(" ", "")
    assert VoiceState.TOOL_RUNNING in rig.sink.states


def test_estado_do_computador_uses_fixed_probe() -> None:
    rig = make_rig()
    rig.provider.push(call("get_system_status"), say("O processador está a doze por cento."))
    asyncio.run(rig.session.handle_text("Qual é o estado do computador?"))
    assert rig.probe.reads == 1
    content = next(m for m in rig.provider.requests[1][0] if m.role == "tool").content or ""
    for key in ("cpu_percent", "memory_percent", "uptime_minutes"):
        assert key in content
    assert "process" not in content.replace("processador", "")  # no process list leaked


def test_explica_novamente_reaches_model_with_history() -> None:
    rig = make_rig()
    rig.provider.push(say("Primeira resposta."), say("Explico de outra forma."))
    asyncio.run(rig.session.handle_text("Fala-me do tempo"))
    asyncio.run(rig.session.handle_text("Explica novamente a última resposta"))
    second_messages = rig.provider.requests[1][0]
    assert any(m.role == "assistant" and m.content == "Primeira resposta." for m in second_messages)
    assert rig.tts.spoken[-1] == "Explico de outra forma."


def test_provider_failure_becomes_fixed_portuguese_sentence() -> None:
    async def run() -> str | None:
        provider = PortugueseProvider(ExplodingProvider())
        response = await provider.chat([], [], None)
        assert response.metadata == {"vexel_provider_failure": "ConnectionError"}
        return response.message.content

    text = asyncio.run(run())
    assert text == SAY_MODEL_UNAVAILABLE
    assert "11434" not in (text or "")
