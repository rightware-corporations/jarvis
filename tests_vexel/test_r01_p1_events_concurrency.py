"""R01 · P1 — event order, threading, stale events, cancellation and concurrency."""

from __future__ import annotations

import asyncio
import threading
import time

from jarvis.core.voice_loop import TurnOutcome
from jarvis.ui.events import (
    FanOutSink,
    InvalidTransitionError,
    QueueSink,
    RecordingSink,
    StateMachine,
    UiEvent,
    VoiceState,
)
from tests_vexel.conftest import make_rig
from tests_vexel.fakes import ExplodingSink, StubbornProvider, call, say


class ThreadRecordingSink(RecordingSink):
    def __init__(self) -> None:
        super().__init__()
        self.threads: list[int] = []

    def publish(self, event: UiEvent) -> None:
        self.threads.append(threading.get_ident())
        super().publish(event)


# ------------------------------------------------------------ 1. order


def test_events_are_published_in_sequence_order_under_thread_contention() -> None:
    sink = RecordingSink()
    machine = StateMachine(sink, session_id="t", initial=VoiceState.IDLE)
    cycle = {VoiceState.IDLE: VoiceState.LISTENING, VoiceState.LISTENING: VoiceState.IDLE}

    def worker() -> None:
        for _ in range(500):
            try:
                machine.transition(cycle[machine.state])
            except InvalidTransitionError:
                pass

    threads = [threading.Thread(target=worker) for _ in range(8)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    events = sink.events
    assert len(events) > 100
    for before, after in zip(events, events[1:]):
        assert after.sequence == before.sequence + 1
        assert after.previous is before.state


# ------------------------------------------------------------ 2. threads


def test_tool_callbacks_are_marshalled_to_the_event_loop_thread() -> None:
    sink = ThreadRecordingSink()
    rig = make_rig(sink=sink)
    rig.provider.push(call("get_system_status"), say("Está tudo bem."))
    loop_thread = threading.get_ident()  # asyncio.run executes on this thread
    asyncio.run(rig.session.handle_text("estado do computador"))
    assert VoiceState.TOOL_RUNNING in sink.states
    assert set(sink.threads) == {loop_thread}


def test_queue_sink_hands_events_to_another_thread_and_is_bounded() -> None:
    queue = QueueSink(maxlen=3)
    machine = StateMachine(queue, session_id="t", initial=VoiceState.IDLE)
    for _ in range(3):
        machine.transition(VoiceState.LISTENING)
        machine.transition(VoiceState.IDLE)
    drained = queue.drain()
    assert [event.sequence for event in drained] == [4, 5, 6]
    assert queue.dropped == 3 and queue.drain() == []


# ------------------------------------------------------------ 3. stale events


def test_stale_tool_callback_does_not_overwrite_newer_state() -> None:
    rig = make_rig()
    session = rig.session
    session._turn_generation = session.generation  # a turn started a tool...
    session.cancel()  # ...and was cancelled before the tool reported in
    published = len(rig.sink.events)
    session.on_tool_start("get_system_status")
    assert session.stale_callbacks == 1
    assert len(rig.sink.events) == published
    assert session.state is VoiceState.IDLE


def test_events_carry_increasing_generation_across_cancel() -> None:
    rig = make_rig()
    rig.provider.push(say("um"), say("dois"))
    asyncio.run(rig.session.handle_text("primeira"))
    first_gen = rig.sink.events[-1].generation
    rig.session.cancel()
    asyncio.run(rig.session.handle_text("segunda"))
    assert rig.sink.events[-1].generation > first_gen


# ------------------------------------------------------------ 4. late responses


def test_late_response_cannot_arm_a_confirmation_after_cancel() -> None:
    provider = StubbornProvider(
        [call("open_allowed_application", {"app": "calculator"})], delay=0.2
    )
    rig = make_rig(provider=provider)

    async def run():
        turn = asyncio.create_task(rig.session.handle_text("abre a calculadora"))
        await provider.started.wait()
        rig.session.cancel()
        return await turn

    result = asyncio.run(run())
    assert result.outcome is TurnOutcome.DISCARDED
    assert rig.pending is None
    assert not any("Calculadora" in text for text in rig.tts.spoken)
    assert asyncio.run(rig.session.handle_text("sim")).outcome is TurnOutcome.NOTHING_TO_CONFIRM
    assert rig.launcher.requested == []


# ------------------------------------------------------------ 5. expiry


def test_expired_confirmation_cannot_be_reused() -> None:
    rig = make_rig(ttl=0.05)
    rig.provider.push(call("open_allowed_application", {"app": "calculator"}), say("Abri."))
    asyncio.run(rig.session.handle_text("abre a calculadora"))
    time.sleep(0.1)
    outcomes = [asyncio.run(rig.session.handle_text("sim")).outcome for _ in range(3)]
    assert outcomes == [
        TurnOutcome.CANCELLED_NO_RESPONSE,
        TurnOutcome.NOTHING_TO_CONFIRM,
        TurnOutcome.NOTHING_TO_CONFIRM,
    ]
    assert rig.launcher.requested == []


# ------------------------------------------------------------ 6. concurrency


def test_concurrent_confirmations_consume_it_exactly_once() -> None:
    rig = make_rig()
    rig.provider.push(call("open_allowed_application", {"app": "calculator"}), say("Abri."))
    asyncio.run(rig.session.handle_text("abre a calculadora"))

    async def run():
        return await asyncio.gather(*(rig.session.handle_text("sim") for _ in range(5)))

    outcomes = sorted(r.outcome.value for r in asyncio.run(run()))
    assert outcomes.count(TurnOutcome.CONFIRMED.value) == 1
    assert outcomes.count(TurnOutcome.NOTHING_TO_CONFIRM.value) == 4
    assert rig.launcher.requested == ["calculator"]


def test_concurrent_new_request_cancels_rather_than_steals_confirmation() -> None:
    rig = make_rig()
    rig.provider.push(call("open_allowed_application", {"app": "calculator"}), say("Abri."))
    asyncio.run(rig.session.handle_text("abre a calculadora"))

    async def run():
        return await asyncio.gather(
            rig.session.handle_text("abre o bloco de notas"), rig.session.handle_text("sim")
        )

    first, second = asyncio.run(run())
    assert first.outcome is TurnOutcome.CANCELLED_UNCLEAR
    assert second.outcome is TurnOutcome.NOTHING_TO_CONFIRM
    assert rig.launcher.requested == []


# ------------------------------------------------------------ 7. sink failures


def test_failing_sink_does_not_bypass_confirmation_policy() -> None:
    sink = ExplodingSink()
    rig = make_rig(sink=sink)
    rig.provider.push(call("open_allowed_application", {"app": "calculator"}), say("Abri."))
    first = asyncio.run(rig.session.handle_text("abre a calculadora"))
    assert first.outcome is TurnOutcome.CONFIRMATION_REQUESTED
    assert rig.launcher.requested == []  # nothing ran without "sim"
    rejected = asyncio.run(rig.session.handle_text("talvez"))
    assert rejected.outcome is TurnOutcome.CANCELLED_UNCLEAR
    assert asyncio.run(rig.session.handle_text("sim")).outcome is TurnOutcome.NOTHING_TO_CONFIRM
    assert rig.launcher.requested == []
    assert sink.calls > 0 and rig.session.machine.sink_failures == sink.calls
    assert rig.session.state is VoiceState.IDLE


def test_reentrant_sink_cannot_change_state() -> None:
    holder: list[StateMachine] = []

    class Meddling:
        def publish(self, event: UiEvent) -> None:
            holder[0].transition(VoiceState.ERROR)

    machine = StateMachine(Meddling(), session_id="t", initial=VoiceState.IDLE)
    holder.append(machine)
    machine.transition(VoiceState.LISTENING)
    assert machine.state is VoiceState.LISTENING
    assert machine.sink_failures == 1


def test_fan_out_isolates_failing_sink() -> None:
    good = RecordingSink()
    fan = FanOutSink([ExplodingSink(), good])
    StateMachine(fan, session_id="t", initial=VoiceState.IDLE).transition(VoiceState.LISTENING)
    assert good.states == [VoiceState.LISTENING]
    assert fan.failures == 1
