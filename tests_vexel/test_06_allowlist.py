"""Test 6 — only the three allowlisted tools are visible to the model."""

from __future__ import annotations

import asyncio

import pytest

from jarvis.tools.allowlist import (
    ALLOWLIST_TOOL_NAMES,
    OpenAllowedApplicationArguments,
    OpenAllowedApplicationTool,
    SimulatedLauncher,
)
from wyzer.models import ConfirmationMode
from wyzer.tools.base import ToolExecutionError
from tests_vexel.conftest import make_rig
from tests_vexel.fakes import call, say

FORBIDDEN = [
    "open_application",
    "close_application",
    "run_command",
    "shell",
    "write_text_file",
    "browser_navigate",
    "type_text",
    "click",
    "screenshot",
    "set_master_volume",
    "list_tool_capabilities",
    "activate_tool_capability",
]


def test_registry_holds_exactly_the_allowlist() -> None:
    rig = make_rig()
    assert tuple(rig.parts.registry) == ALLOWLIST_TOOL_NAMES
    visible = [tool.function.name for tool in rig.parts.registry.native_tools()]
    assert sorted(visible) == sorted(ALLOWLIST_TOOL_NAMES)
    assert sorted(t.function.name for t in rig.parts.registry.all_native_tools()) == sorted(
        ALLOWLIST_TOOL_NAMES
    )


def test_model_only_ever_sees_the_allowlist() -> None:
    rig = make_rig()
    rig.provider.push(say("Olá."), call("get_local_time"), say("São duas e meia."))
    asyncio.run(rig.session.handle_text("olá"))
    asyncio.run(rig.session.handle_text("que horas são"))
    assert rig.provider.tool_names_seen() == set(ALLOWLIST_TOOL_NAMES)


@pytest.mark.parametrize("name", FORBIDDEN)
def test_model_cannot_call_unregistered_tools(name: str) -> None:
    rig = make_rig()
    rig.provider.push(call(name, {"application": "cmd"}), say("Não posso fazer isso."))
    asyncio.run(rig.session.handle_text("faz uma coisa perigosa"))
    assert rig.launcher.requested == []
    assert rig.pending is None


def test_open_application_schema_is_a_closed_enum() -> None:
    schema = OpenAllowedApplicationArguments.model_json_schema()
    assert schema["properties"]["app"]["enum"] == ["calculator", "notepad"]
    assert schema.get("additionalProperties") is False
    assert OpenAllowedApplicationTool.confirmation is ConfirmationMode.ALWAYS


@pytest.mark.parametrize("app", ["cmd", "powershell", "regedit", "explorer", "C:\\Windows\\x.exe"])
def test_application_outside_enum_is_rejected_by_validation(app: str) -> None:
    rig = make_rig()
    rig.provider.push(call("open_allowed_application", {"app": app}), say("Não posso abrir isso."))
    asyncio.run(rig.session.handle_text(f"abre {app}"))
    assert rig.pending is None
    assert rig.launcher.requested == []


def test_tool_refuses_app_removed_from_configured_allowlist() -> None:
    from uuid import uuid4

    from wyzer.tools.base import ToolContext

    tool = OpenAllowedApplicationTool(SimulatedLauncher(), ["calculator"])
    with pytest.raises(ToolExecutionError):
        tool.execute(OpenAllowedApplicationArguments(app="notepad"), ToolContext(uuid4(), uuid4()))
