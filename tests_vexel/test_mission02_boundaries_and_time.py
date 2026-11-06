"""JAR-MISSION-02 — ADR-0001 layer boundaries and Windows-sensitive behaviour.

* Boundaries: the backend never imports a UI toolkit, a web framework or ``apps``;
  the web lab never touches Windows adapters or real tools; the desktop frontend only
  consumes ``jarvis.ui`` (it must not build its own orchestrator).
* Repository hygiene: no audio, model, database or private evidence file is tracked.
* Time: Africa/Maputo with the IANA database, and the documented fallback to the
  system clock when the database is missing (stock Python on Windows has no tzdata).
"""

from __future__ import annotations

import ast
import sys
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

import pytest

from jarvis.tools.allowlist import GetLocalTimeTool, NoArguments
from wyzer.tools.base import ToolContext
from tests_vexel.fakes import REPO_ROOT

UI_OR_WEB = {"PySide6", "PyQt5", "PyQt6", "shiboken6", "fastapi", "starlette", "uvicorn", "apps"}
WINDOWS_ONLY = {
    "wyzer.desktop",
    "wyzer.tools.windows",
    "wyzer.speech.windows",
    "wyzer.speech.kokoro",
}


def _imports(root: Path) -> dict[Path, set[str]]:
    found: dict[Path, set[str]] = {}
    for path in sorted(root.rglob("*.py")):
        names: set[str] = set()
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Import):
                names.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
                names.add(node.module)
                names.update(f"{node.module}.{alias.name}" for alias in node.names)
        found[path] = names
    return found


def _top(name: str) -> str:
    return name.split(".")[0]


@pytest.mark.parametrize("path", sorted((REPO_ROOT / "jarvis").rglob("*.py")), ids=lambda p: p.name)
def test_backend_never_imports_ui_web_or_apps(path: Path) -> None:
    names = _imports(REPO_ROOT / "jarvis")[path]
    assert not {_top(n) for n in names} & UI_OR_WEB, sorted(names)


def test_weblab_never_reaches_windows_adapters_or_real_launcher() -> None:
    for path, names in _imports(REPO_ROOT / "apps" / "weblab").items():
        bad = {n for n in names if any(n == w or n.startswith(w + ".") for w in WINDOWS_ONLY)}
        bad |= {n for n in names if n.endswith("WindowsApplicationLauncher")}
        assert not bad, f"{path}: {sorted(bad)}"


def test_desktop_frontend_only_consumes_ui_contracts() -> None:
    desktop = REPO_ROOT / "apps" / "desktop"
    for path, names in _imports(desktop).items():
        backend = {n for n in names if _top(n) in {"jarvis", "wyzer"}}
        allowed = {n for n in backend if n == "jarvis.ui" or n.startswith("jarvis.ui.")}
        assert backend == allowed, f"{path}: frontend imports backend internals {sorted(backend - allowed)}"


def test_weblab_entrypoint_and_frontend_assets_exist() -> None:
    source = (REPO_ROOT / "apps" / "weblab" / "api.py").read_text(encoding="utf-8")
    assert "\napp = create_app()" in source  # ASGI entrypoint apps.weblab.api:app
    for asset in ("index.html", "lab.css", "lab.js"):
        assert (REPO_ROOT / "apps" / "weblab" / "web" / asset).is_file()
    assert not (REPO_ROOT / "jarvis_lab").exists()


FORBIDDEN_TRACKED = (
    ".wav", ".mp3", ".flac", ".ogg", ".m4a",
    ".onnx", ".tflite", ".pt", ".pth", ".bin", ".gguf", ".safetensors",
    ".sqlite", ".sqlite3", ".db",
)


IGNORED_DIRS = {".git", ".venv", ".wyzer", "evidence", "logs", "__pycache__", ".pytest_cache"}


def test_no_audio_models_or_databases_in_the_source_tree() -> None:
    # Walks the checkout (no subprocess); git-ignored runtime folders are skipped.
    offenders = []
    for path in REPO_ROOT.rglob("*"):
        if any(part in IGNORED_DIRS for part in path.relative_to(REPO_ROOT).parts):
            continue
        if path.is_file() and path.name.lower().endswith(FORBIDDEN_TRACKED):
            offenders.append(str(path.relative_to(REPO_ROOT)))
    assert not offenders, offenders


# ----------------------------------------------------------------------------- time

FIXED = datetime(2026, 11, 4, 12, 30, tzinfo=UTC)  # 14:30 in Maputo (UTC+2, no DST)


def test_maputo_time_with_iana_database() -> None:
    result = GetLocalTimeTool("Africa/Maputo", clock=lambda: FIXED).execute(
        NoArguments(), ToolContext(uuid4(), uuid4())
    )
    assert (result.hour, result.minute, result.timezone_source) == (14, 30, "configured")
    assert result.iso.endswith("+02:00")


def test_missing_timezone_database_falls_back_to_system_clock(monkeypatch: pytest.MonkeyPatch) -> None:
    """Stock Windows Python without ``tzdata``: no crash, the system clock is used and
    the reply is marked ``timezone_source="system"`` so the evidence shows it."""
    import jarvis.tools.allowlist as allowlist
    from zoneinfo import ZoneInfoNotFoundError

    def missing(_name: str):
        raise ZoneInfoNotFoundError("No time zone found with key Africa/Maputo")

    monkeypatch.setattr(allowlist, "ZoneInfo", missing)
    system_cat = datetime(2026, 11, 4, 14, 30, tzinfo=timezone(timedelta(hours=2), "CAT"))
    result = GetLocalTimeTool("Africa/Maputo", clock=lambda: system_cat).execute(
        NoArguments(), ToolContext(uuid4(), uuid4())
    )
    assert result.timezone_source == "system"
    assert result.date == "2026-11-04"


def test_tzdata_is_available_where_the_suite_runs() -> None:
    # Linux has /usr/share/zoneinfo; Windows CI installs the ``tzdata`` package.
    from zoneinfo import ZoneInfo

    assert datetime(2026, 1, 1, tzinfo=ZoneInfo("Africa/Maputo")).utcoffset() == timedelta(hours=2)
    if sys.platform == "win32":
        import tzdata  # noqa: F401


def test_os_description_spawns_no_process() -> None:
    # The process guard (conftest) fails this test if a helper such as `ver`/`uname` runs.
    from jarvis.runtime.preflight import os_description

    text = os_description()
    assert text and (text.startswith("Windows ") if sys.platform == "win32" else True)
