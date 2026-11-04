"""Safe cancellation: barge-in, concurrent requests and late responses."""

from __future__ import annotations

import asyncio

from jarvis.core.voice_loop import TurnOutcome
from jarvis.language.prompts import SAY_NOTHING_TO_CANCEL
from jarvis.ui.events import VoiceState
from tests_vexel.conftest import make_rig
from tests_vexel.fakes import call, say


def test_cancela_with_nothing_running() -> None:
    rig = make_rig()
    result = asyncio.run(rig.session.handle_text("cancela essa operação"))
    assert result.outcome is TurnOutcome.NOTHING_TO_CANCEL
    assert rig.tts.spoken == [SAY_NOTHING_TO_CANCEL]
    assert rig.provider.requests == []


def test_barge_in_cancel_discards_late_model_response() -> None:
    rig = make_rig(delay=0.3)
    rig.provider.push(say("Resposta que chega tarde."))

    async def run():
        turn = asyncio.create_task(rig.session.handle_text("explica a teoria da relatividade"))
        await rig.provider.started.wait()
        cancel = await rig.session.handle_text("cancela")
        return cancel, await turn

    cancel, late = asyncio.run(run())
    assert cancel.outcome is TurnOutcome.STOPPED
    assert late.outcome is TurnOutcome.DISCARDED
    assert "Resposta que chega tarde." not in rig.tts.spoken
    assert rig.session.state is VoiceState.IDLE


def test_queued_request_is_dropped_by_cancel() -> None:
    rig = make_rig(delay=0.2)
    rig.provider.push(say("primeira"), say("segunda"))

    async def run():
        first = asyncio.create_task(rig.session.handle_text("pergunta um"))
        await rig.provider.started.wait()
        second = asyncio.create_task(rig.session.handle_text("pergunta dois"))
        await asyncio.sleep(0)
        rig.session.cancel()
        return await first, await second

    first, second = asyncio.run(run())
    assert first.outcome is TurnOutcome.DISCARDED
    assert second.outcome is TurnOutcome.DISCARDED
    assert rig.tts.spoken == []
    assert len(rig.provider.requests) == 1


def test_concurrent_requests_are_serialised() -> None:
    rig = make_rig(delay=0.05)
    rig.provider.push(say("um"), say("dois"))

    async def run():
        return await asyncio.gather(
            rig.session.handle_text("primeira"), rig.session.handle_text("segunda")
        )

    results = asyncio.run(run())
    assert [r.outcome for r in results] == [TurnOutcome.ANSWERED, TurnOutcome.ANSWERED]
    assert rig.tts.spoken == ["um", "dois"]


def test_cancel_while_awaiting_confirmation_clears_pending() -> None:
    rig = make_rig()
    rig.provider.push(call("open_allowed_application", {"app": "calculator"}), say("Abri."))
    asyncio.run(rig.session.handle_text("abre a calculadora"))
    assert rig.pending is not None
    rig.session.cancel()
    assert rig.pending is None
    assert asyncio.run(rig.session.handle_text("sim")).outcome is TurnOutcome.NOTHING_TO_CONFIRM
    assert rig.launcher.launched == []


def test_shutdown_goes_offline() -> None:
    rig = make_rig()
    rig.session.shutdown()
    assert rig.session.state is VoiceState.OFFLINE
