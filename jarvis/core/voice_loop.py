"""The voice turn loop: activation → STT → policy → Orchestrator → TTS.

Deterministic rules that never depend on the language model:

* While a confirmation is pending, only an exact confirmation phrase can approve it,
  and only if it is the very call VEXEL prompted for (same action id and digest) *and*
  the prompt was actually presented (``Presentation.SPOKEN``). A prompt whose speech
  failed, was interrupted or was not presented cancels the pending call.
* Rejection, cancellation, silence, timeout and anything ambiguous cancel it. The
  utterance that cancelled it is never forwarded as a new request.
* ``sim`` with nothing pending executes nothing (replay protection).
* ``cancela``/``para`` interrupts whatever is running, also from another task while a
  turn is in flight. Each turn carries a generation number; a response that arrives
  after a cancel is discarded, never spoken, and any confirmation it created is cleared.
* The spoken result of an effectful action is built from the recorded tool result
  (``ActionStatus``: SIMULATED, SUCCEEDED, FAILED, DENIED), never from the model text.
  A model reply that claims an action without a matching SUCCEEDED result is replaced.
* A failed TTS call is never reported as spoken: the state goes to ERROR, then IDLE.

Threading: tool callbacks arrive on worker threads and are marshalled onto the event
loop with ``call_soon_threadsafe``; every state transition therefore happens on the
loop thread, in order. Stale callbacks (older generation) are dropped.

Limitation (InProcessExecutor): Wyzer's in-process executor cannot interrupt a tool
that is already running. Cancelling after a side effect has happened stops the turn
and suppresses the reply, but it does not undo the effect. For
``open_allowed_application`` the effect only happens after a valid ``sim``.

The Orchestrator still validates TTL and the argument digest on ``yes``; VEXEL's binding
check is an additional, earlier gate.

Repeated call after a confirmed execution (JAR-CONF-01): after ``yes`` the Orchestrator
runs the approved call and asks the model again. A model that re-requests a call that
already ran in the same logical action (same Orchestrator ``action_id`` and same
argument digest, also later in the action, e.g. calculator → notepad → calculator)
would raise another confirmation and, on another ``sim``, a second execution. VEXEL
keeps a small ledger of the digests executed per action and drops such a pending call
with the Orchestrator's own ``no`` (never approves it), then speaks the recorded status
of the confirmed call. A *different* call is not a repeat: it keeps its own policy and
needs its own confirmation, and the question then starts with the confirmed call's
real result. A new user request is a new action and never inherits anything.

Metrics (JAR-ENGINE-01): with a ``ProviderMeter`` each turn also records the local
model's share of ``think_ms`` (``llm_calls``, ``llm_ms``, ``llm_eval_count``,
``llm_model_ms``, ``llm_failures``, ``llm_cancelled``, ``llm_truncated``). A provider
failure is spoken as the fixed "model unavailable" sentence and its fixed code (e.g.
``PROVIDER_TIMEOUT``) is put in ``TurnResult.detail``; no provider text is kept.
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections import OrderedDict
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any
from uuid import UUID

from wyzer.app.orchestrator import Orchestrator
from wyzer.models import AssistantResponse, PendingConfirmation
from wyzer.policy import ConfirmationPolicy

from jarvis.brain.pt_provider import EffectGate, MeterSnapshot, ProviderMeter
from jarvis.config import VexelSettings
from jarvis.language.prompts import (
    SAY_CANCELLED,
    SAY_CANCELLED_NO_CONFIRMATION,
    SAY_CANCELLED_UNCLEAR,
    SAY_ERROR,
    SAY_NOT_HEARD,
    SAY_NOTHING_OPENED,
    SAY_NOTHING_TO_CANCEL,
    action_outcome_text,
    claims_action,
    confirmation_prompt,
    strip_action_claims,
    translate_wyzer_reply,
)
from jarvis.language.intent import NO_REQUEST, IntentVerdict, classify_request
from jarvis.language.pt import ControlIntent, classify_control, normalize, strip_vocative
from jarvis.tools.allowlist import ActionOutcome, action_outcome_from_result
from jarvis.ui.events import InvalidTransitionError, StateMachine, UiEventSink, VoiceState
from jarvis.voice.contracts import Activation, CaptureError, SpeechToText, TextToSpeech
from jarvis.voice.presentation import GuardedSpeech, Presentation, PresentationResult

LOGGER = logging.getLogger(__name__)

_EXECUTED_LEDGER_ACTIONS = 16  # recent Orchestrator actions remembered for repeat checks

SAY_NOTHING_TO_CONFIRM = "Não há nada para confirmar."
SAY_STT_FAILED = "Não consegui ouvir: houve um problema com o microfone ou o reconhecimento."
SAY_CONFIRMATION_MISMATCH = "Cancelei, porque essa confirmação não corresponde ao pedido."

# Orchestrator control words. Sent only by VEXEL, never derived from free text.
_WYZER_YES = "yes"
_WYZER_NO = "no"
_WYZER_STOP = "stop"


class TurnOutcome(StrEnum):
    ANSWERED = "answered"
    CONFIRMATION_REQUESTED = "confirmation_requested"
    CONFIRMATION_NOT_PRESENTED = "confirmation_not_presented"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"
    CANCELLED_UNCLEAR = "cancelled_unclear"
    CANCELLED_NO_RESPONSE = "cancelled_no_response"
    CANCELLED_MISMATCH = "cancelled_mismatch"
    NOTHING_TO_CONFIRM = "nothing_to_confirm"
    NOTHING_TO_CANCEL = "nothing_to_cancel"
    STOPPED = "stopped"
    NOT_HEARD = "not_heard"
    TTS_FAILED = "tts_failed"
    STT_FAILED = "stt_failed"
    SPEECH_INTERRUPTED = "speech_interrupted"
    DISCARDED = "discarded"
    ERROR = "error"


@dataclass(frozen=True)
class PromptedConfirmation:
    """A confirmation VEXEL actually presented to the user."""

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
    """``outcome`` is what happened; ``intended`` is the policy decision behind it.

    They differ only when presentation failed: e.g. ``outcome=TTS_FAILED`` with
    ``intended=NOTHING_TO_CONFIRM``. A failed presentation is never reported as spoken.
    """

    outcome: TurnOutcome
    intended: TurnOutcome | None = None
    heard: str | None = None
    intent: ControlIntent = ControlIntent.NONE
    reply: str | None = None
    spoken: bool = False
    presentation: Presentation | None = None
    wyzer_reply: str | None = None
    reply_translated: bool = False
    awaiting_confirmation: bool = False
    action_status: str | None = None
    claim_blocked: bool = False
    detail: str | None = None
    metrics: dict[str, float] = field(default_factory=dict)
    session_id: str | None = None
    turn_index: int | None = None
    request_intent: dict[str, Any] | None = None
    tools_executed: list[str] = field(default_factory=list)

    def as_record(self, include_text: bool = False) -> dict[str, Any]:
        record: dict[str, Any] = {
            "session_id": self.session_id,
            "turn_index": self.turn_index,
            "request_intent": self.request_intent,
            "tools_executed": list(self.tools_executed),
            "outcome": self.outcome.value,
            "intended": (self.intended or self.outcome).value,
            "intent": self.intent.value,
            "spoken": self.spoken,
            "presentation": self.presentation.value if self.presentation else None,
            "awaiting_confirmation": self.awaiting_confirmation,
            "action_status": self.action_status,
            "claim_blocked": self.claim_blocked,
            "detail": self.detail,
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


@dataclass
class _Turn:
    generation: int
    seen_steps: set[Any]
    metrics: dict[str, float] = field(default_factory=dict)
    confirmed_arguments: dict[str, Any] = field(default_factory=dict)
    confirmed: PendingConfirmation | None = None
    meter_before: MeterSnapshot | None = None
    llm_failure: str | None = None
    index: int = 0
    gate_before: tuple[int, int] = (0, 0)
    verdict: IntentVerdict | None = None
    tools_executed: list[str] = field(default_factory=list)


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
        provider_meter: ProviderMeter | None = None,
        effect_gate: EffectGate | None = None,
        context_stats: Callable[[], dict[str, float]] | None = None,
    ) -> None:
        self.orchestrator = orchestrator
        self.provider_meter = provider_meter
        self.effect_gate = effect_gate
        self.context_stats = context_stats
        self.session_id = session_id
        self._turn_index = 0
        # Verdict of the user request a pending confirmation belongs to (JAR-COG-01).
        self._request_verdict: IntentVerdict = NO_REQUEST
        self.stt = stt
        self.speech = tts if isinstance(tts, GuardedSpeech) else GuardedSpeech(tts)
        self.activation = activation
        self.settings = settings
        self.machine = StateMachine(sink, session_id=session_id)
        self._timer = timer
        self._turn_lock = asyncio.Lock()
        self._generation = 0
        self._turn_generation = -1
        self._loop: asyncio.AbstractEventLoop | None = None
        self._prompted: PromptedConfirmation | None = None
        self._stopping = False
        self.stale_callbacks = 0
        # action_id -> digests of confirmed calls that really ran (JAR-CONF-01).
        self._executed: OrderedDict[UUID, set[str]] = OrderedDict()

    # ------------------------------------------------------------------ lifecycle

    @property
    def tts(self) -> TextToSpeech:
        return self.speech.inner

    @property
    def state(self) -> VoiceState:
        return self.machine.state

    @property
    def generation(self) -> int:
        return self._generation

    def start(self) -> None:
        if self.state is VoiceState.OFFLINE:
            self._move(VoiceState.IDLE, detail="started")

    def shutdown(self) -> None:
        self._stopping = True
        self.cancel(reason="shutdown")
        self.activation.close()
        self._call_adapter(self.stt, "close")
        self._call_adapter(self.speech.inner, "close")
        self._move(VoiceState.OFFLINE, detail="shutdown")

    @staticmethod
    def _call_adapter(adapter: object, method: str) -> None:
        """Best-effort optional hook (``cancel``/``close``); never raises."""
        hook = getattr(adapter, method, None)
        if not callable(hook):
            return
        try:
            hook()
        except Exception as error:
            LOGGER.warning("%s.%s failed: %s", type(adapter).__name__, method, type(error).__name__)

    def on_tool_start(self, tool_name: str) -> None:
        """Called by the allowlisted tools, usually from a worker thread.

        Never touches state directly from the worker: it is marshalled onto the event
        loop, tagged with the generation of the turn that started the tool.
        """
        generation = self._turn_generation
        loop = self._loop
        if loop is not None and loop.is_running():
            try:
                loop.call_soon_threadsafe(self._tool_started, tool_name, generation)
                return
            except RuntimeError:  # loop closed
                return
        self._tool_started(tool_name, generation)

    def _tool_started(self, tool_name: str, generation: int) -> None:
        if generation != self._generation:
            self.stale_callbacks += 1
            return
        if self.state in {VoiceState.THINKING, VoiceState.TOOL_RUNNING}:
            self._move(VoiceState.TOOL_RUNNING, detail=tool_name)

    def cancel(self, *, reason: str = "user") -> bool:
        """Interrupt the current turn from any task.

        Bumps the generation so any late response is dropped, interrupts the
        Orchestrator (which also clears a pending confirmation) and stops speech.
        """
        self._generation += 1
        self._prompted = None
        interrupted = self.orchestrator.interrupt()
        self._call_adapter(self.stt, "cancel")
        try:
            self.speech.stop()
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
        self._loop = asyncio.get_running_loop()
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
            turn = self._begin_turn()
            if self.state is not VoiceState.LISTENING:
                self._move(VoiceState.LISTENING, detail="text")
            return await self._handle(text, intent, turn)

    # ------------------------------------------------------------------ internals

    def _begin_turn(self) -> _Turn:
        if self.state is VoiceState.OFFLINE:
            self.start()
        self._turn_generation = self._generation
        seen = {result.step_id for result in self.orchestrator.world.snapshot().recent_tool_calls}
        before = self.provider_meter.snapshot() if self.provider_meter is not None else None
        self._turn_index += 1
        gate = self.effect_gate.counts() if self.effect_gate is not None else (0, 0)
        return _Turn(
            self._generation, seen, meter_before=before, index=self._turn_index, gate_before=gate
        )

    def _authorize(self, verdict: IntentVerdict | None) -> None:
        """Bind the effect gate to the user's own request for this turn (fail closed)."""
        if self.effect_gate is not None:
            self.effect_gate.authorize(verdict)

    def _finalize(self, result: TurnResult, turn: _Turn) -> TurnResult:
        """Stamp sanitised telemetry; close the effect gate until the next request."""
        result.session_id = self.session_id
        result.turn_index = turn.index
        if turn.verdict is not None:
            result.request_intent = turn.verdict.as_record()
        result.tools_executed = list(turn.tools_executed)
        if self.effect_gate is not None:
            blocked, _allowed = self.effect_gate.counts()
            if blocked - turn.gate_before[0]:
                result.metrics["tools_blocked"] = float(blocked - turn.gate_before[0])
        if self.context_stats is not None:
            try:
                for key, value in self.context_stats().items():
                    result.metrics[key] = float(value)
            except Exception as error:
                LOGGER.warning("context stats failed: %s", type(error).__name__)
        if self._pending() is None:
            self._request_verdict = NO_REQUEST
        self._authorize(NO_REQUEST)
        return result

    def _record_llm(self, turn: _Turn) -> None:
        """Add the local model's share of this turn to its metrics (no text). Never raises."""
        if self.provider_meter is None or turn.meter_before is None:
            return
        try:
            now = self.provider_meter.snapshot()
            llm = now.since(turn.meter_before)
            for key in [k for k in turn.metrics if k.startswith("llm_")]:
                del turn.metrics[key]
            turn.metrics.update(llm)
            if llm.get("llm_failures"):
                turn.llm_failure = now.last_failure
        except Exception as error:
            LOGGER.warning("llm metrics failed: %s", type(error).__name__)

    async def _listen_and_handle(self, timeout_seconds: float) -> TurnResult:
        self._loop = asyncio.get_running_loop()
        generation = self._generation
        async with self._turn_lock:
            if generation != self._generation:
                return TurnResult(TurnOutcome.DISCARDED)
            turn = self._begin_turn()
            self._move(VoiceState.LISTENING)
            started = self._timer()
            try:
                transcript = await asyncio.to_thread(self.stt.listen, timeout_seconds)
            except Exception as error:
                turn.metrics["stt_ms"] = round((self._timer() - started) * 1000, 1)
                return self._finalize(await self._stt_failed(error, turn), turn)
            turn.metrics["stt_ms"] = round((self._timer() - started) * 1000, 1)
            if turn.generation != self._generation:
                return self._finalize(TurnResult(TurnOutcome.DISCARDED, metrics=turn.metrics), turn)
            text = transcript.text if transcript is not None else None
            return await self._handle(text, self._intent(text), turn)

    async def _stt_failed(self, error: Exception, turn: _Turn) -> TurnResult:
        """Capture/STT failure is not silence: report it, and never keep a confirmation."""
        stage = "capture" if isinstance(error, CaptureError) else "stt"
        LOGGER.warning("%s failed: %s", stage, type(error).__name__)
        self._clear_pending(f"{stage} failure")
        if turn.generation != self._generation:
            return TurnResult(TurnOutcome.DISCARDED, metrics=turn.metrics)
        turn.metrics[f"{stage}_error"] = 1.0
        self._move(VoiceState.ERROR, detail=f"{stage}_{type(error).__name__}")
        result = await self._say(TurnOutcome.STT_FAILED, SAY_STT_FAILED, turn)
        result.detail = stage
        return result

    @staticmethod
    def _intent(text: str | None) -> ControlIntent:
        if not text or not text.strip():
            return ControlIntent.NONE
        return classify_control(strip_vocative(normalize(text)))

    def _pending(self) -> PendingConfirmation | None:
        return self.orchestrator.world.snapshot().pending_confirmation

    def _clear_pending(self, reason: str) -> None:
        """Fail-closed: drop any pending confirmation and VEXEL's binding to it."""
        self._prompted = None
        if self._pending() is not None:
            LOGGER.info("clearing pending confirmation: %s", reason)
            self.orchestrator.interrupt()

    def _new_outcomes(self, turn: _Turn) -> list[ActionOutcome]:
        outcomes: list[ActionOutcome] = []
        for result in self.orchestrator.world.snapshot().recent_tool_calls:
            if result.step_id in turn.seen_steps:
                continue
            turn.seen_steps.add(result.step_id)
            if getattr(result, "ok", False):
                turn.tools_executed.append(str(result.tool))  # tool names only, no data
            outcome = action_outcome_from_result(result)
            if outcome is not None:
                outcomes.append(outcome)
        return outcomes

    async def _handle(self, text: str | None, intent: ControlIntent, turn: _Turn) -> TurnResult:
        try:
            result = await self._handle_inner(text, intent, turn)
        except BaseException:
            self._authorize(NO_REQUEST)
            raise
        return self._finalize(result, turn)

    async def _handle_inner(
        self, text: str | None, intent: ControlIntent, turn: _Turn
    ) -> TurnResult:
        heard = text.strip() if text and text.strip() else None
        pending = self._pending()
        try:
            if pending is not None:
                return await self._handle_while_pending(heard, intent, pending, turn)
            self._prompted = None
            if heard is None:
                return await self._say(TurnOutcome.NOT_HEARD, SAY_NOT_HEARD, turn)
            if intent is ControlIntent.CONFIRM:
                return await self._say(
                    TurnOutcome.NOTHING_TO_CONFIRM,
                    SAY_NOTHING_TO_CONFIRM,
                    turn,
                    heard=heard,
                    intent=intent,
                )
            if intent is ControlIntent.REJECT:
                return await self._say(
                    TurnOutcome.NOTHING_TO_CANCEL,
                    SAY_NOTHING_TO_CANCEL,
                    turn,
                    heard=heard,
                    intent=intent,
                )
            if intent is ControlIntent.CANCEL:
                self._move(VoiceState.THINKING, detail="stop")
                response = await self.orchestrator.handle(_WYZER_STOP)
                outcome = (
                    TurnOutcome.STOPPED if response.interrupted else TurnOutcome.NOTHING_TO_CANCEL
                )
                return await self._respond(response, outcome, turn, heard=heard, intent=intent)
            self._move(VoiceState.THINKING)
            # A new request: only the user's own words can authorise an effectful call.
            # Known applications, not only the configured ones: a request for a
            # non-configured app is still a request, and the tool denies it honestly.
            turn.verdict = classify_request(heard)
            self._request_verdict = turn.verdict
            self._authorize(turn.verdict)
            started = self._timer()
            response = await self.orchestrator.handle(heard)
            turn.metrics["think_ms"] = round((self._timer() - started) * 1000, 1)
            self._record_llm(turn)
            return await self._respond(
                response, TurnOutcome.ANSWERED, turn, heard=heard, intent=intent
            )
        except asyncio.CancelledError:
            self._clear_pending("task cancelled")
            raise
        except Exception as error:
            LOGGER.exception("turn failed: %s", type(error).__name__)
            self._clear_pending("turn error")
            self._record_llm(turn)
            if turn.generation != self._generation:
                return TurnResult(
                    TurnOutcome.DISCARDED, heard=heard, intent=intent, metrics=turn.metrics
                )
            self._move(VoiceState.ERROR, detail=type(error).__name__)
            return await self._say(TurnOutcome.ERROR, SAY_ERROR, turn, heard=heard, intent=intent)

    async def _handle_while_pending(
        self,
        heard: str | None,
        intent: ControlIntent,
        pending: PendingConfirmation,
        turn: _Turn,
    ) -> TurnResult:
        prompted = self._prompted
        # Consume the binding before anything else: no second caller can reuse it.
        self._prompted = None
        if intent is ControlIntent.CONFIRM:
            if prompted is not None and prompted.matches(pending):
                turn.confirmed_arguments = dict(pending.arguments)
                turn.confirmed = pending
                # The continuation keeps the original request's scope, nothing more.
                turn.verdict = self._request_verdict
                self._authorize(self._request_verdict)
                self._move(VoiceState.THINKING, detail="confirmed")
                started = self._timer()
                response = await self.orchestrator.handle(_WYZER_YES)
                turn.metrics["think_ms"] = round((self._timer() - started) * 1000, 1)
                self._record_llm(turn)
                return await self._respond(
                    response, TurnOutcome.CONFIRMED, turn, heard=heard, intent=intent
                )
            outcome, say = TurnOutcome.CANCELLED_MISMATCH, SAY_CONFIRMATION_MISMATCH
        elif intent in {ControlIntent.REJECT, ControlIntent.CANCEL}:
            outcome, say = TurnOutcome.REJECTED, SAY_CANCELLED
        elif heard is None:
            outcome, say = TurnOutcome.CANCELLED_NO_RESPONSE, SAY_CANCELLED_NO_CONFIRMATION
        else:
            # Ambiguous: cancel, and do not treat the phrase as a new request.
            outcome, say = TurnOutcome.CANCELLED_UNCLEAR, SAY_CANCELLED_UNCLEAR
        self._move(VoiceState.THINKING, detail=outcome.value)
        await self.orchestrator.handle(_WYZER_NO)
        self._clear_pending("rejected")
        return await self._say(outcome, say, turn, heard=heard, intent=intent)

    async def _respond(
        self,
        response: AssistantResponse,
        outcome: TurnOutcome,
        turn: _Turn,
        *,
        heard: str | None,
        intent: ControlIntent,
    ) -> TurnResult:
        if turn.generation != self._generation:
            # Late response after a cancel: never speak it and never let it leave a
            # confirmation armed behind the user's back.
            self._clear_pending("late response")
            return TurnResult(
                TurnOutcome.DISCARDED,
                heard=heard,
                intent=intent,
                wyzer_reply=response.text,
                metrics=turn.metrics,
            )
        outcomes = self._new_outcomes(turn)
        confirmed_outcome = self._record_executed(turn, outcomes)
        pending = self._pending()
        if pending is not None and self._already_executed(pending):
            # The same call already ran in this action: never ask (or run) it again.
            # Wyzer's own "no" clears it and closes the action; it never reaches the model.
            self._prompted = None
            await self.orchestrator.handle(_WYZER_NO)
            if self._pending() is not None:  # fail closed if Wyzer kept anything pending
                self._clear_pending("repeat drop left a pending call")
            turn.metrics["repeat_call_dropped"] = 1.0
            pending = None
            if turn.generation != self._generation:
                return TurnResult(
                    TurnOutcome.DISCARDED, heard=heard, intent=intent, metrics=turn.metrics
                )
        if pending is not None:
            prior = confirmed_outcome or (outcomes[-1] if outcomes else None)
            return await self._present_confirmation(
                pending, response, turn, heard, intent, prior=prior
            )

        reply, translated = translate_wyzer_reply(response.text)
        wyzer_text = response.text.strip()
        if wyzer_text.startswith("That confirmation expired"):
            outcome = TurnOutcome.CANCELLED_NO_RESPONSE
        elif wyzer_text.startswith("I couldn't confirm it because"):
            outcome = TurnOutcome.CANCELLED_MISMATCH

        action_status: str | None = None
        claim_blocked = False
        if outcomes:
            # A confirmed turn reports the confirmed call's recorded result, not a later
            # model call that was refused (e.g. DENIED extra arguments).
            last = confirmed_outcome or outcomes[-1]
            action_status = last.status.value
            app = last.app
            if app is None and last is confirmed_outcome:
                # A failed launch carries no data; name the app the user confirmed.
                app = turn.confirmed_arguments.get("app")
            reply = action_outcome_text(last.status.value, app)
        elif claims_action(reply):
            # Remove only the false claim; keep the rest of an unrelated answer.
            claim_blocked = True
            cleaned, _removed = strip_action_claims(reply)
            reply = cleaned or SAY_NOTHING_OPENED

        result = await self._say(outcome, reply, turn, heard=heard, intent=intent)
        result.wyzer_reply = response.text
        result.reply_translated = translated
        result.action_status = action_status
        result.claim_blocked = claim_blocked
        if turn.llm_failure is not None and result.detail is None:
            result.detail = turn.llm_failure
        return result

    def _record_executed(
        self, turn: _Turn, outcomes: list[ActionOutcome]
    ) -> ActionOutcome | None:
        """Ledger the confirmed call if it really ran in this turn; return its outcome."""
        confirmed = turn.confirmed
        if confirmed is None:
            return None
        outcome = next((o for o in outcomes if o.step_id == confirmed.step_id), None)
        if outcome is None:
            return None  # nothing ran (e.g. expired): not executed, nothing to ledger
        digest = ConfirmationPolicy.digest(confirmed.tool_name, dict(confirmed.arguments))
        self._executed.setdefault(confirmed.action_id, set()).add(digest)
        self._executed.move_to_end(confirmed.action_id)
        while len(self._executed) > _EXECUTED_LEDGER_ACTIONS:
            self._executed.popitem(last=False)
        return outcome

    def _already_executed(self, pending: PendingConfirmation) -> bool:
        """True when this exact call (digest) already ran in the same Orchestrator action."""
        return pending.call_digest in self._executed.get(pending.action_id, set())

    async def _present_confirmation(
        self,
        pending: PendingConfirmation,
        response: AssistantResponse,
        turn: _Turn,
        heard: str | None,
        intent: ControlIntent,
        *,
        prior: ActionOutcome | None = None,
    ) -> TurnResult:
        prompt = confirmation_prompt(pending)
        if prior is not None:
            # A different call after an executed one: say what really happened first.
            app = prior.app
            confirmed = turn.confirmed
            if app is None and confirmed is not None and prior.step_id == confirmed.step_id:
                app = turn.confirmed_arguments.get("app")
            prompt = f"{action_outcome_text(prior.status.value, app)} {prompt}"
        self._move(VoiceState.AWAITING_CONFIRMATION, detail=pending.tool_name)
        presentation = await self._present(prompt, turn)
        current = self._pending()
        armed = (
            presentation.presented
            and turn.generation == self._generation
            and current is not None
            and current.action_id == pending.action_id
            and current.call_digest == pending.call_digest
        )
        base = dict(
            heard=heard,
            intent=intent,
            reply=prompt,
            presentation=presentation.outcome,
            wyzer_reply=response.text,
            metrics=turn.metrics,
            action_status=prior.status.value if prior is not None else None,
        )
        if armed:
            self._prompted = PromptedConfirmation.of(pending)
            return TurnResult(
                TurnOutcome.CONFIRMATION_REQUESTED,
                spoken=True,
                awaiting_confirmation=True,
                **base,
            )
        # Fail closed: a confirmation that was not presented cannot be approved later.
        self._clear_pending(f"confirmation not presented: {presentation.outcome.value}")
        if turn.generation != self._generation:
            return TurnResult(TurnOutcome.DISCARDED, **base)
        if presentation.outcome is Presentation.INTERRUPTED:
            self._move(VoiceState.IDLE, detail="confirmation_interrupted")
        else:
            self._move(VoiceState.ERROR, detail=f"tts_{presentation.stage.value}")
            self._move(VoiceState.IDLE, detail="recovered")
        return TurnResult(TurnOutcome.CONFIRMATION_NOT_PRESENTED, **base)

    async def _say(
        self,
        outcome: TurnOutcome,
        text: str,
        turn: _Turn,
        *,
        heard: str | None = None,
        intent: ControlIntent = ControlIntent.NONE,
    ) -> TurnResult:
        base = dict(heard=heard, intent=intent, reply=text, metrics=turn.metrics)
        if turn.generation != self._generation:
            return TurnResult(TurnOutcome.DISCARDED, **base)
        self._move(VoiceState.SPEAKING)
        presentation = await self._present(text, turn)
        if turn.generation != self._generation:
            return TurnResult(TurnOutcome.DISCARDED, presentation=presentation.outcome, **base)
        if presentation.presented:
            self._move(VoiceState.IDLE)
            return TurnResult(
                outcome, intended=outcome, spoken=True, presentation=presentation.outcome, **base
            )
        if presentation.outcome is Presentation.INTERRUPTED:
            self._move(VoiceState.IDLE, detail="speech_interrupted")
            return TurnResult(
                TurnOutcome.SPEECH_INTERRUPTED,
                intended=outcome,
                presentation=presentation.outcome,
                **base,
            )
        self._move(VoiceState.ERROR, detail=f"tts_{presentation.stage.value}")
        self._move(VoiceState.IDLE, detail="recovered")
        return TurnResult(
            TurnOutcome.TTS_FAILED, intended=outcome, presentation=presentation.outcome, **base
        )

    async def _present(self, text: str, turn: _Turn) -> PresentationResult:
        if turn.generation != self._generation:
            return PresentationResult(Presentation.INTERRUPTED)
        started = self._timer()
        result = await asyncio.to_thread(self.speech.present, text)
        turn.metrics["tts_ms"] = round((self._timer() - started) * 1000, 1)
        if result.outcome is Presentation.FAILED:
            LOGGER.warning("tts failed at %s: %s", result.stage.value, result.error)
            turn.metrics["tts_error"] = 1.0
        return result

    def _move(self, target: VoiceState, *, detail: str | None = None) -> None:
        try:
            self.machine.transition(target, detail=detail, generation=self._generation)
        except InvalidTransitionError:
            # Fall back through IDLE so a racing cancel never wedges the machine.
            LOGGER.debug("invalid transition %s -> %s", self.machine.state, target)
            if self.machine.can_transition(VoiceState.IDLE):
                self.machine.transition(
                    VoiceState.IDLE, detail="recovered", generation=self._generation
                )
            if self.machine.can_transition(target):
                self.machine.transition(target, detail=detail, generation=self._generation)
