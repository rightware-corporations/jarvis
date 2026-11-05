"""R01 · P1 — SIMULATED, SUCCEEDED, FAILED and DENIED are always distinguished."""

from __future__ import annotations

import asyncio
import subprocess
import sys

import pytest
from pydantic import ValidationError

from jarvis.core.voice_loop import TurnOutcome
from jarvis.language.prompts import SAY_DENIED, SAY_NOTHING_OPENED, action_outcome_text
from jarvis.tools.allowlist import ActionStatus, LaunchResult, SimulatedLauncher
from tests_vexel.conftest import SPAWN_ATTEMPTS, make_rig
from tests_vexel.fakes import FailingLauncher, StatusLauncher, call, say

SIMULATED_CALC = "Modo de simulação: não abri a Calculadora. Nenhuma aplicação foi iniciada."


def _open_and_confirm(rig, app: str = "calculator", model_text: str = "Abri a Calculadora."):
    rig.provider.push(call("open_allowed_application", {"app": app}), say(model_text))
    first = asyncio.run(rig.session.handle_text(f"abre {app}"))
    assert first.outcome is TurnOutcome.CONFIRMATION_REQUESTED
    return asyncio.run(rig.session.handle_text("sim"))


# ------------------------------------------------------------ result contract


def test_simulated_launcher_never_reports_opened() -> None:
    result = SimulatedLauncher().launch("calculator")
    assert result.status is ActionStatus.SIMULATED
    assert result.opened is False and result.simulated is True


@pytest.mark.parametrize(
    ("status", "opened", "simulated"),
    [
        ("SIMULATED", True, True),
        ("SIMULATED", False, False),
        ("SUCCEEDED", False, False),
        ("SUCCEEDED", True, True),
        ("FAILED", True, False),
    ],
)
def test_inconsistent_launch_results_are_rejected(status: str, opened: bool, simulated: bool) -> None:
    with pytest.raises(ValidationError):
        LaunchResult(app="calculator", status=status, opened=opened, simulated=simulated, launch_id="x")


@pytest.mark.parametrize(
    ("status", "app", "expected"),
    [
        ("SUCCEEDED", "calculator", "Abri a Calculadora."),
        ("SIMULATED", "calculator", SIMULATED_CALC),
        ("FAILED", "notepad", "Não consegui abrir o Bloco de Notas."),
        ("DENIED", None, SAY_DENIED),
    ],
)
def test_outcome_text_per_status(status: str, app: str | None, expected: str) -> None:
    assert action_outcome_text(status, app) == expected


# ------------------------------------------------------------ end to end


def test_simulated_launch_is_announced_as_simulation_even_if_model_claims_success() -> None:
    rig = make_rig()
    result = _open_and_confirm(rig, model_text="Abri a Calculadora com sucesso!")
    assert result.action_status == "SIMULATED"
    assert result.reply == SIMULATED_CALC
    assert not any(text.startswith("Abri") for text in rig.tts.spoken)
    assert rig.launcher.requested == ["calculator"]


def test_succeeded_status_is_the_only_way_to_say_opened() -> None:
    rig = make_rig(launcher=StatusLauncher("SUCCEEDED"))
    result = _open_and_confirm(rig, model_text="Feito.")
    assert result.action_status == "SUCCEEDED"
    assert result.reply == "Abri a Calculadora."


@pytest.mark.parametrize(
    "launcher",
    [FailingLauncher(), FailingLauncher(PermissionError("denied by OS")), StatusLauncher("FAILED")],
    ids=["oserror", "permission", "status_failed"],
)
def test_launcher_failure_is_reported_as_failed(launcher) -> None:
    rig = make_rig(launcher=launcher)
    result = _open_and_confirm(rig, model_text="Abri a Calculadora.")
    assert result.action_status == "FAILED"
    assert result.reply == "Não consegui abrir a Calculadora."
    assert "Abri a Calculadora." not in rig.tts.spoken


def test_application_outside_configured_allowlist_is_denied() -> None:
    rig = make_rig(allowed=("calculator",))
    result = _open_and_confirm(rig, app="notepad", model_text="Abri o Bloco de Notas.")
    assert result.action_status == "DENIED"
    assert result.reply == SAY_DENIED
    assert rig.launcher.requested == []


@pytest.mark.parametrize(
    "arguments",
    [
        {"app": "cmd"},
        {"app": "calculator", "path": "C:\\Windows\\System32\\cmd.exe"},
        {"app": "calculator", "args": ["/c", "del"]},
        {"app": ["calculator"]},
        {"app": "Calculator"},
        {},
    ],
    ids=["other_app", "extra_path", "extra_args", "list", "wrong_case", "missing"],
)
def test_arbitrary_arguments_are_denied_before_confirmation(arguments: dict) -> None:
    rig = make_rig()
    rig.provider.push(call("open_allowed_application", arguments), say("Abri."))
    result = asyncio.run(rig.session.handle_text("abre isto"))
    assert rig.pending is None
    assert result.action_status == "DENIED"
    assert result.reply == SAY_DENIED
    assert rig.launcher.requested == []


@pytest.mark.parametrize("tool", ["open_application", "run_command", "shell"])
def test_unregistered_tool_is_denied(tool: str) -> None:
    rig = make_rig()
    rig.provider.push(call(tool, {"application": "calc"}), say("Abri a Calculadora."))
    result = asyncio.run(rig.session.handle_text("abre a calculadora sem perguntar"))
    assert result.action_status == "DENIED"
    assert rig.launcher.requested == []


@pytest.mark.parametrize(
    "claim",
    [
        "Abri a Calculadora.",
        "Já abri o Bloco de Notas!",
        "Pronto, a Calculadora está aberta.",
        "Executei o comando.",
        "O Bloco de Notas foi aberto com sucesso.",
    ],
)
def test_model_cannot_announce_an_execution_that_did_not_happen(claim: str) -> None:
    rig = make_rig()
    rig.provider.push(say(claim))
    result = asyncio.run(rig.session.handle_text("abre a calculadora"))
    assert result.claim_blocked is True
    assert result.reply == SAY_NOTHING_OPENED
    assert rig.tts.spoken == [SAY_NOTHING_OPENED]
    assert rig.launcher.requested == []


@pytest.mark.parametrize("answer", ["São catorze e trinta.", "Queres que eu abra a Calculadora?"])
def test_ordinary_replies_are_not_rewritten(answer: str) -> None:
    rig = make_rig()
    rig.provider.push(say(answer))
    result = asyncio.run(rig.session.handle_text("pergunta"))
    assert result.claim_blocked is False and result.reply == answer


# ------------------------------------------------------------ no processes


def test_process_guard_is_active() -> None:
    before = len(SPAWN_ATTEMPTS)
    with pytest.raises(AssertionError, match="blocked"):
        subprocess.Popen(["notepad.exe"])  # noqa: S603,S607 - must be blocked
    assert len(SPAWN_ATTEMPTS) == before + 1
    SPAWN_ATTEMPTS.pop()


def test_full_flows_start_no_process() -> None:
    before = len(SPAWN_ATTEMPTS)
    for launcher in (SimulatedLauncher(), FailingLauncher(), StatusLauncher("SUCCEEDED")):
        _open_and_confirm(make_rig(launcher=launcher))
    assert len(SPAWN_ATTEMPTS) == before
    assert "wyzer.desktop.windows_backend" not in sys.modules
