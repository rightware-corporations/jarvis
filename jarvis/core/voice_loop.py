"""The voice turn loop: activation → STT → policy → Orchestrator → TTS.

Deterministic rules that never depend on the language model:

* While a confirmation is pending, only an exact confirmation phrase can approve it,
  and only if it is the very call VEXEL prompted for (same action id and digest).
  Rejection, cancellation, silence, timeout and anything ambiguous cancel it. The
  utterance that cancelled it is never forwarded as a new request.
* ``sim`` with nothing pending executes nothing (replay protection).
* ``cancela``/``para`` interrupts whatever is running, also from another task while a
  turn is in flight. Each turn carries a generation number; a response that arrives
  after a cancel is discarded and never spoken.

The Orchestrator still validates TTL and the argument digest on ``yes``; VEXEL's binding
check is an additional, earlier gate.
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any
from uuid import UUID

from wyzer.app.orchestrator import Orchestrator
from wyzer.models import AssistantResponse, PendingConfirmation

from jarvis.config import VexelSettings
from jarvis.language.prompts import (
    SAY_CANCELLED,
    SAY_CANCELLED_NO_CONFIRMATION,
    SAY_CANCELLED_UNCLEAR,
    SAY_ERROR,
    SAY_NOT_HEARD,
    SAY_NOTHING_TO_CANCEL,
    confirmation_prompt,
    translate_wyzer_reply,
)
from jarvis.language.pt import ControlIntent, classify_control, normalize, strip_vocative
from jarvis.ui.events import InvalidTransitionError, StateMachine, UiEventSink, VoiceState
from jarvis.voice.contracts import Activation, SpeechToText, TextToSpeech

LOGGER = logging.getLogger(__name__)

SAY_NOTHING_TO_CONFIRM = "Não há nada para confirmar."
SAY_CONFIRMATION_MISMATCH = "Cancelei, porque essa confirmação não corresponde ao pedido."

# Orchestrator control words. Sent only by VEXEL, never derived from free text.
_WYZER_YES = "yes"
_WYZER_NO = "no"
_WYZER_STOP = "stop"


class TurnOutcome(StrEnum):
    ANSWERED = "answered"
    CONFIRMATION_REQUESTED = "confirmation_requested"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"
    CANCELLED_UNCLEAR = "cancelled_unclear"
    CANCELLED_NO_RESPONSE = "cancelled_no_response"
    CANCELLED_MISMATCH = "cancelled_mismatch"
    NOTHING_TO_CONFIRM = "nothing_to_confirm"
    NOTHING_TO_CANCEL = "nothing_to_cancel"
    STOPPED = "stopped"
    NOT_HEARD = "not_heard"
    DISCARDED = "discarded"
    ERROR = "error"


@dataclass(frozen=True)
class PromptedConfirmation:
    action_id: UUID
    call_digest: str
    tool_name: str

    @classmethod
    def of(cls, pending: PendingConfirmation) -> PromptedConfirmation:
        return cls(pending.action_id, pending.call_digest, pending.tool_name)

    def matches(self, pending: PendingConfirmation) -> bool:
        return (
            self.action_id == pending.action_id
            and self.call_digest == pending.call_digest
            and self.tool_name == pending.tool_name
        )


@dataclass
class TurnResult:
    outcome: TurnOutcome
    heard: str | None = None
    intent: ControlIntent = ControlIntent.NONE
    reply: str | None = None
    spoken: bool = False
    wyzer_reply: str | None = None
    reply_translated: bool = False
    awaiting_confirmation: bool = False
    metrics: dict[str, float] = field(default_factory=dict)

    def as_record(self, include_text: bool = False) -> dict[str, Any]:
        record: dict[str, Any] = {
            "outcome": self.outcome.value,
            "intent": self.intent.value,
            "spoken": self.spoken,
            "awaiting_confirmation": self.awaiting_confirmation,
            "reply_translated": self.reply_translated,
            "metrics": dict(self.metrics),
        }
        if include_text:
            record.update(heard=self.heard, reply=self.reply)
        else:
            record.update(
                heard_chars=len(self.heard or ""), reply_chars=len(self.reply or "")
            )
        return record


class VoiceSession:
    def __init__(
        self,
        orchestrator: Orchestrator,
        *,
        stt: SpeechToText,
        tts: TextToSpeech,
        activation: Activation,
        sink: UiEventSink,
        settings: VexelSettings,
        session_id: str = "local",
        timer: Callable[[], float] = time.perf_counter,
    ) -> None:
        self.orchestrator = orchestrator
        self.stt = stt
        self.tts = tts
        self.activation = activation
        self.settings = settings
        self.machine = StateMachine(sink, session_id=session_id)
        self._timer = timer
        self._turn_lock = asyncio.Lock()
        self._generation = 0
        self._prompted: PromptedConfirmation | None = None
        self._stopping = False

    # ------------------------------------------------------------------ lifecycle

    @property
    def state(self) -> VoiceState:
        return self.machine.state

    @property
    def generation(self) -> int:
        return self._generation

    def start(self) -> None:
        if self.state is VoiceState.OFFLINE:
            self.machine.transition(VoiceState.IDLE, detail="started")

    def shutdown(self) -> None:
        self._stopping = True
        self.cancel(reason="shutdown")
        self.activation.close()
        self._move(VoiceState.OFFLINE, detail="shutdown")

    def on_tool_start(self, tool_name: str) -> None:
        """Called from the worker thread by the allowlisted tools."""
        if self.state in {VoiceState.THINKING, VoiceState.TOOL_RUNNING}:
            self._move(VoiceState.TOOL_RUNNING, detail=tool_name)

    def cancel(self, *, reason: str = "user") -> bool:
        """Interrupt the current turn from any task or thread-safe caller.

        Bumps the generation so any late response is dropped, interrupts the
        Orchestrator (which also clears a pending confirmation) and stops speech.
        """
        self._generation += 1
        self._prompted = None
        interrupted = self.orchestrator.interrupt()
        try:
            self.tts.stop()
        except Exception as error:  # stopping must never raise into the caller
            LOGGER.warning("tts.stop failed: %s", type(error).__name__)
        if self.state not in {VoiceState.OFFLINE, VoiceState.MUTED, VoiceState.IDLE}:
            self._move(VoiceState.IDLE, detail=f"cancelled:{reason}")
        return interrupted

    # --------------------------------------------------------------- entry points

    async def run(self, *, activation_timeout_seconds: float = 30.0) -> None:
        """Main loop for voice mode (QA PC, 01C). Returns after ``shutdown``."""
        self.start()
        while not self._stopping:
            fired = await asyncio.to_thread(self.activation.wait, activation_timeout_seconds)
            if self._stopping:
                break
            if fired:
                await self.voice_turn()

    async def voice_turn(self) -> list[TurnResult]:
        """One activation: listen, act, and if needed listen once more for confirmation."""
        results = [await self._listen_and_handle(self.settings.listen_timeout_seconds)]
        while results[-1].awaiting_confirmation and not self._stopping:
            results.append(
                await self._listen_and_handle(self.settings.confirmation_listen_timeout_seconds)
            )
        return results

    async def handle_text(self, text: str | None) -> TurnResult:
        """Text entry point (text mode and tests). ``None`` or blank means silence."""
        intent = self._intent(text)
        if intent is ControlIntent.CANCEL and self._turn_lock.locked():
            # Barge-in from a concurrent caller: do not queue behind the running turn.
            stopped = self.cancel(reason="barge_in")
            return TurnResult(
                TurnOutcome.STOPPED if stopped else TurnOutcome.NOTHING_TO_CANCEL,
                heard=text,
                intent=intent,
            )
        generation = self._generation
        async with self._turn_lock:
            if generation != self._generation:
                return TurnResult(TurnOutcome.DISCARDED, heard=text, intent=intent)
            if self.state is VoiceState.OFFLINE:
                self.start()
            if self.state is not VoiceState.LISTENING:
                self._move(VoiceState.LISTENING, detail="text")
            return await self._handle(text, intent, generation, metrics={})

    # ------------------------------------------------------------------ internals

    async def _listen_and_handle(self, timeout_seconds: float) -> TurnResult:
        generation = self._generation
        async with self._turn_lock:
            if generation != self._generation:
                return TurnResult(TurnOutcome.DISCARDED)
            if self.state is VoiceState.OFFLINE:
                self.start()
            self._move(VoiceState.LISTENING)
            started = self._timer()
            try:
                transcript = await asyncio.to_thread(self.stt.listen, timeout_seconds)
            except Exception as error:
                LOGGER.warning("stt failed: %s", type(error).__name__)
                transcript = None
            metrics = {"stt_ms": round((self._timer() - started) * 1000, 1)}
            if generation != self._generation:
                return TurnResult(TurnOutcome.DISCARDED, metrics=metrics)
            text = transcript.text if transcript is not None else None
            return await self._handle(text, self._intent(text), generation, metrics)

    @staticmethod
    def _intent(text: str | None) -> ControlIntent:
        if not text or not text.strip():
            return ControlIntent.NONE
        return classify_control(strip_vocative(normalize(text)))

    def _pending(self) -> PendingConfirmation | None:
        return self.orchestrator.world.snapshot().pending_confirmation

    async def _handle(
        self,
        text: str | None,
        intent: ControlIntent,
        generation: int,
        metrics: dict[str, float],
    ) -> TurnResult:
        heard = text.strip() if text and text.strip() else None
        pending = self._pending()
        try:
            if pending is not None:
                return await self._handle_while_pending(heard, intent, pending, generation, metrics)
            self._prompted = None
            if heard is None:
                return await self._say(TurnOutcome.NOT_HEARD, SAY_NOT_HEARD, generation, metrics)
            if intent is ControlIntent.CONFIRM:
                return await self._say(
                    TurnOutcome.NOTHING_TO_CONFIRM,
                    SAY_NOTHING_TO_CONFIRM,
                    generation,
                    metrics,
                    heard=heard,
                    intent=intent,
                )
            if intent is ControlIntent.REJECT:
                return await self._say(
                    TurnOutcome.NOTHING_TO_CANCEL,
                    SAY_NOTHING_TO_CANCEL,
                    generation,
                    metrics,
                    heard=heard,
                    intent=intent,
                )
            if intent is ControlIntent.CANCEL:
                self._move(VoiceState.THINKING, detail="stop")
                response = await self.orchestrator.handle(_WYZER_STOP)
                outcome = TurnOutcome.STOPPED if response.interrupted else TurnOutcome.NOTHING_TO_CANCEL
                return await self._respond(
                    response, outcome, generation, metrics, heard=heard, intent=intent
                )
            self._move(VoiceState.THINKING)
            started = self._timer()
            response = await self.orchestrator.handle(heard)
            metrics["think_ms"] = round((self._timer() - started) * 1000, 1)
            return await self._respond(
                response, TurnOutcome.ANSWERED, generation, metrics, heard=heard, intent=intent
            )
        except asyncio.CancelledError:
            raise
        except Exception as error:
            LOGGER.exception("turn failed: %s", type(error).__name__)
            if generation != self._generation:
                return TurnResult(TurnOutcome.DISCARDED, heard=heard, intent=intent, metrics=metrics)
            self._move(VoiceState.ERROR, detail=type(error).__name__)
            return await self._say(
                TurnOutcome.ERROR, SAY_ERROR, generation, metrics, heard=heard, intent=intent
            )

    async def _handle_while_pending(
        self,
        heard: str | None,
        intent: ControlIntent,
        pending: PendingConfirmation,
        generation: int,
        metrics: dict[str, float],
    ) -> TurnResult:
        prompted = self._prompted
        if intent is ControlIntent.CONFIRM:
            if prompted is not None and prompted.matches(pending):
                self._prompted = None
                self._move(VoiceState.THINKING, detail="confirmed")
                started = self._timer()
                response = await self.orchestrator.handle(_WYZER_YES)
                metrics["think_ms"] = round((self._timer() - started) * 1000, 1)
                return await self._respond(
                    response, TurnOutcome.CONFIRMED, generation, metrics, heard=heard, intent=intent
                )
            outcome, say = TurnOutcome.CANCELLED_MISMATCH, SAY_CONFIRMATION_MISMATCH
        elif intent in {ControlIntent.REJECT, ControlIntent.CANCEL}:
            outcome, say = TurnOutcome.REJECTED, SAY_CANCELLED
        elif heard is None:
            outcome, say = TurnOutcome.CANCELLED_NO_RESPONSE, SAY_CANCELLED_NO_CONFIRMATION
        else:
            # Ambiguous: cancel, and do not treat the phrase as a new request.
            outcome, say = TurnOutcome.CANCELLED_UNCLEAR, SAY_CANCELLED_UNCLEAR
        self._prompted = None
        self._move(VoiceState.THINKING, detail=outcome.value)
        await self.orchestrator.handle(_WYZER_NO)
        return await self._say(outcome, say, generation, metrics, heard=heard, intent=intent)

    async def _respond(
        self,
        response: AssistantResponse,
        outcome: TurnOutcome,
        generation: int,
        metrics: dict[str, float],
        *,
        heard: str | None,
        intent: ControlIntent,
    ) -> TurnResult:
        if generation != self._generation:
            return TurnResult(
                TurnOutcome.DISCARDED,
                heard=heard,
                intent=intent,
                wyzer_reply=response.text,
                metrics=metrics,
            )
        pending = self._pending()
        if pending is not None:
            self._prompted = PromptedConfirmation.of(pending)
            prompt = confirmation_prompt(pending)
            self._move(VoiceState.AWAITING_CONFIRMATION, detail=pending.tool_name)
            spoken = await self._speak(prompt, generation, metrics)
            return TurnResult(
                TurnOutcome.CONFIRMATION_REQUESTED,
                heard=heard,
                intent=intent,
                reply=prompt,
                spoken=spoken,
                wyzer_reply=response.text,
                awaiting_confirmation=spoken and self._pending() is not None,
                metrics=metrics,
            )
        reply, translated = translate_wyzer_reply(response.text)
        wyzer_text = response.text.strip()
        if wyzer_text.startswith("That confirmation expired"):
            outcome = TurnOutcome.CANCELLED_NO_RESPONSE
        elif wyzer_text.startswith("I couldn't confirm it because"):
            outcome = TurnOutcome.CANCELLED_MISMATCH
        result = await self._say(outcome, reply, generation, metrics, heard=heard, intent=intent)
        result.wyzer_reply = response.text
        result.reply_translated = translated
        return result

    async def _say(
        self,
        outcome: TurnOutcome,
        text: str,
        generation: int,
        metrics: dict[str, float],
        *,
        heard: str | None = None,
        intent: ControlIntent = ControlIntent.NONE,
    ) -> TurnResult:
        if generation != self._generation:
            return TurnResult(TurnOutcome.DISCARDED, heard=heard, intent=intent, metrics=metrics)
        self._move(VoiceState.SPEAKING)
        spoken = await self._speak(text, generation, metrics)
        if generation == self._generation:
            self._move(VoiceState.IDLE)
        return TurnResult(
            outcome if spoken else TurnOutcome.DISCARDED,
            heard=heard,
            intent=intent,
            reply=text,
            spoken=spoken,
            metrics=metrics,
        )

    async def _speak(self, text: str, generation: int, metrics: dict[str, float]) -> bool:
        if generation != self._generation:
            return False
        started = self._timer()
        try:
            await asyncio.to_thread(self.tts.speak, text)
        except Exception as error:
            LOGGER.warning("tts failed: %s", type(error).__name__)
            metrics["tts_error"] = 1.0
        metrics["tts_ms"] = round((self._timer() - started) * 1000, 1)
        return generation == self._generation

    def _move(self, target: VoiceState, *, detail: str | None = None) -> None:
        try:
            self.machine.transition(target, detail=detail)
        except InvalidTransitionError:
            # Fall back through IDLE/ERROR so a racing cancel never wedges the machine.
            LOGGER.debug("invalid transition %s -> %s", self.machine.state, target)
            if self.machine.can_transition(VoiceState.IDLE):
                self.machine.transition(VoiceState.IDLE, detail="recovered")
            if self.machine.can_transition(target):
                self.machine.transition(target, detail=detail)
