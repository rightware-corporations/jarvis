"""Test 10 — no real Windows execution and no paid-service access in 01B."""

from __future__ import annotations

import ast
import asyncio
import sys
from pathlib import Path

import pytest

from jarvis.config import SliceConfigError, WakeWordBlockedError, parse_slice_config
from jarvis.tools.allowlist import RealWindowsActionsDisabledError, WindowsApplicationLauncher
from jarvis.voice.activation import ManualActivation, create_activation
from tests_vexel.conftest import make_rig
from tests_vexel.fakes import REPO_ROOT, SLICE_CONFIG, call, say

JARVIS_SOURCES = sorted((REPO_ROOT / "jarvis").rglob("*.py"))
FORBIDDEN_IMPORTS = {
    "anthropic",
    "openai",
    "elevenlabs",
    "pvporcupine",
    "porcupine",
    "google",
    "azure",
    "boto3",
    "subprocess",
    "openwakeword",
}
FORBIDDEN_CALLS = {"system", "popen", "startfile", "spawnl", "spawnv", "execv", "execl"}


def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module.split(".")[0])
    return names


@pytest.mark.parametrize("path", JARVIS_SOURCES, ids=lambda p: str(p.relative_to(REPO_ROOT)))
def test_no_paid_sdk_or_process_imports(path: Path) -> None:
    assert not (_imports(path) & FORBIDDEN_IMPORTS)


@pytest.mark.parametrize("path", JARVIS_SOURCES, ids=lambda p: str(p.relative_to(REPO_ROOT)))
def test_no_os_process_calls(path: Path) -> None:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id == "os":
            assert node.attr.casefold() not in FORBIDDEN_CALLS, f"os.{node.attr} in {path}"


def test_full_cycle_never_imports_windows_backend() -> None:
    rig = make_rig()
    rig.provider.push(call("open_allowed_application", {"app": "calculator"}), say("Abri."))
    asyncio.run(rig.session.handle_text("abre a calculadora"))
    asyncio.run(rig.session.handle_text("sim"))
    assert rig.launcher.launched == ["calculator"]
    result = rig.launcher.launch("notepad")
    assert result.simulated is True
    assert "wyzer.desktop.windows_backend" not in sys.modules


@pytest.mark.parametrize(
    ("platform", "allow"), [("linux", True), ("linux", False), ("win32", False), ("darwin", True)]
)
def test_windows_launcher_fails_closed(platform: str, allow: bool) -> None:
    with pytest.raises(RealWindowsActionsDisabledError):
        WindowsApplicationLauncher(allow_real_windows_actions=allow, platform=platform)


def _config_with(**changes: object) -> dict:
    import tomllib

    data = tomllib.loads(SLICE_CONFIG.read_text(encoding="utf-8"))
    for dotted, value in changes.items():
        section, _, key = dotted.rpartition("__")
        target = data[section] if section else data
        target[key] = value
    return data


@pytest.mark.parametrize(
    "changes",
    [
        {"llm__endpoint": "https://api.openai.com/v1"},
        {"llm__endpoint": "http://192.168.1.20:11434"},
        {"llm__api_key": "sk-test"},
        {"llm__auto_start": True},
        {"llm__provider": "none"},
        {"memory__enabled": True},
        {"task_engine__enabled": True},
        {"coding_agent__enabled": True},
        {"worker_isolation_enabled": True},
    ],
    ids=lambda c: next(iter(c)),
)
def test_config_refuses_unsafe_settings(changes: dict) -> None:
    with pytest.raises(SliceConfigError):
        parse_slice_config(_config_with(**changes))


def test_wake_word_is_blocked() -> None:
    with pytest.raises(WakeWordBlockedError, match="WAKE_WORD_BLOCKED"):
        parse_slice_config(_config_with(speech__wake_word_adapter="openwakeword"))
    with pytest.raises(WakeWordBlockedError):
        create_activation("openwakeword")
    assert isinstance(create_activation("manual"), ManualActivation)


def test_no_wake_models_in_repository_additions() -> None:
    for folder in ("jarvis", "configs", "tests_vexel"):
        assert not list((REPO_ROOT / folder).rglob("*.onnx"))
        assert not list((REPO_ROOT / folder).rglob("*.tflite"))


def test_default_config_disallows_real_windows_actions() -> None:
    assert parse_slice_config(_config_with()).vexel.allow_real_windows_actions is False
