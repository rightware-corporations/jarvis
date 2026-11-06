"""Model context hygiene for the VEXEL session (JAR-COG-01, Package B).

``VexelConversation`` is injected into Wyzer's ``Orchestrator`` (``conversation=``),
so Wyzer's ``ConversationManager`` keeps recording exactly as upstream; only the
*copy* that ``snapshot()`` hands to the prompt builder and the provider is cleaned:

* **Settled calls.** An assistant tool call without a tool result — a confirmation that
  was refused, unclear, expired, cancelled or dropped as a repeat (JAR-CONF-01) — is
  followed by a fixed synthetic tool result ``NOT_EXECUTED``. Before this, the model
  saw an unanswered ``open_allowed_application`` in every later request and tended to
  "complete" it (observed: "Qual é a capital de Moçambique?" → "abro o Bloco de
  Notas?" after a refused Notepad request).
* **No orphans.** Tool messages without their assistant call (cut by Wyzer's
  40-entry window) are removed, and the context always starts at a user message.
* **Budget.** At most ``max_context_characters`` of conversation (system prompt not
  counted) are sent; older whole exchanges are dropped first. The counts are exposed
  through ``stats()`` for the sanitised turn log; no content is ever logged.

Nothing here is persistent: the history lives in the process and dies with it.
"""

from __future__ import annotations

import json
import threading
from collections import Counter
from typing import Any

from wyzer.conversation.manager import ConversationManager
from wyzer.models import ChatMessage

# Neutral on purpose: it settles refused, unclear, expired and cancelled confirmations and
# also a dropped duplicate of a call that already ran (whose real result stays above it).
NOT_EXECUTED_RESULT = json.dumps(
    {"ok": False, "status": "NOT_EXECUTED", "reason": "no_execution_for_this_call"},
    separators=(",", ":"),
)
DEFAULT_MAX_CONTEXT_CHARACTERS = 12_000  # ~3–4k tokens; the Wyzer system prompt is extra


def _size(message: ChatMessage) -> int:
    size = len(message.content or "")
    for call in message.tool_calls or []:
        size += len(call.function.name) + len(json.dumps(call.function.arguments, default=str))
    return size + 16


def settle_and_trim(
    messages: list[ChatMessage], *, max_characters: int
) -> tuple[list[ChatMessage], dict[str, int]]:
    """Return a clean copy of ``messages`` and counts of what was changed."""
    settled = 0
    orphans = 0
    clean: list[ChatMessage] = []
    index = 0
    while index < len(messages):
        message = messages[index]
        if message.role == "tool":
            orphans += 1  # a tool result whose call is not right before it
            index += 1
            continue
        clean.append(message)
        index += 1
        if message.role != "assistant" or not message.tool_calls:
            continue
        results: list[ChatMessage] = []
        while index < len(messages) and messages[index].role == "tool":
            results.append(messages[index])
            index += 1
        clean.extend(results)
        answered = Counter(result.name for result in results)
        by_id = {result.tool_call_id for result in results if result.tool_call_id}
        for call in message.tool_calls:
            if call.id and call.id in by_id:
                continue
            if answered[call.function.name] > 0:
                answered[call.function.name] -= 1
                continue
            clean.append(
                ChatMessage(
                    role="tool",
                    name=call.function.name,
                    tool_call_id=call.id,
                    content=NOT_EXECUTED_RESULT,
                )
            )
            settled += 1

    # Budget: keep the most recent messages, cut only at a user message.
    total = 0
    start = len(clean)
    for position in range(len(clean) - 1, -1, -1):
        total += _size(clean[position])
        if total > max_characters and start < len(clean):
            break
        start = position
    while start < len(clean) and clean[start].role != "user":
        start += 1
    if start >= len(clean):  # never send nothing: keep from the last user message
        last_user = max((i for i, m in enumerate(clean) if m.role == "user"), default=0)
        start = last_user
    dropped = start
    return clean[start:], {
        "context_messages": len(clean) - start,
        "context_dropped": dropped,
        "context_settled": settled,
        "context_orphans": orphans,
    }


class VexelConversation(ConversationManager):
    def __init__(
        self, limit: int = 40, *, max_context_characters: int = DEFAULT_MAX_CONTEXT_CHARACTERS
    ) -> None:
        super().__init__(limit)
        self.max_context_characters = max_context_characters
        self._stats_lock = threading.Lock()
        self._last: dict[str, int] = {}

    def snapshot(self) -> Any:
        state = super().snapshot()  # deep copy: the recorded history is untouched
        cleaned, counts = settle_and_trim(
            list(state.model_messages), max_characters=self.max_context_characters
        )
        state.model_messages = cleaned
        with self._stats_lock:
            self._last = counts
        return state

    def stats(self) -> dict[str, int]:
        """Counts for the last snapshot sent to the model (no content)."""
        with self._stats_lock:
            return dict(self._last)
