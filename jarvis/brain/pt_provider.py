"""Portuguese instruction and failure sanitising around any Wyzer ``ChatProvider``.

The wrapper never changes tool definitions or tool calls; it only appends a fixed
Portuguese instruction to the system message the Orchestrator already built, and
replaces provider exceptions with a fixed Portuguese sentence (no internal details).
"""

from __future__ import annotations

import logging

from wyzer.brain.provider import ChatProvider
from wyzer.config import WyzerSettings
from wyzer.models import (
    ChatMessage,
    ChatRequestSettings,
    NativeToolDefinition,
    ProviderChatResponse,
)

from jarvis.language.prompts import SAY_MODEL_UNAVAILABLE

LOGGER = logging.getLogger(__name__)

PORTUGUESE_INSTRUCTION = (
    "VEXEL_LANGUAGE_POLICY: Responde sempre em português, de forma natural e curta, "
    "porque a resposta vai ser lida em voz alta. Não uses markdown, listas, títulos, "
    "emojis nem código. Usa frases completas e números por extenso quando forem curtos. "
    "Nunca digas que uma acção foi feita sem um resultado de ferramenta que o confirme. "
    "Para saber a hora usa get_local_time; para o estado do computador usa "
    "get_system_status; para abrir aplicações usa apenas open_allowed_application."
)


class PortugueseProvider:
    def __init__(self, inner: ChatProvider, *, instruction: str = PORTUGUESE_INSTRUCTION) -> None:
        self.inner = inner
        self.instruction = instruction

    @property
    def available(self) -> bool:
        return self.inner.available

    def _with_instruction(self, messages: list[ChatMessage]) -> list[ChatMessage]:
        if messages and messages[0].role == "system":
            first = messages[0]
            merged = f"{first.content or ''}\n\n{self.instruction}".strip()
            return [first.model_copy(update={"content": merged}), *messages[1:]]
        return [ChatMessage(role="system", content=self.instruction), *messages]

    async def chat(
        self,
        messages: list[ChatMessage],
        tools: list[NativeToolDefinition],
        settings: ChatRequestSettings | None = None,
    ) -> ProviderChatResponse:
        try:
            return await self.inner.chat(self._with_instruction(messages), tools, settings)
        except Exception as error:  # sanitise: never expose provider internals
            LOGGER.warning("local provider failed: %s", type(error).__name__)
            return ProviderChatResponse(
                message=ChatMessage(role="assistant", content=SAY_MODEL_UNAVAILABLE),
                metadata={"vexel_provider_failure": type(error).__name__},
            )


def create_local_provider(settings: WyzerSettings) -> PortugueseProvider:
    """Build the configured local provider (Ollama by default). Makes no network call."""
    from wyzer.brain import create_chat_provider

    return PortugueseProvider(create_chat_provider(settings.llm, settings.personality))
