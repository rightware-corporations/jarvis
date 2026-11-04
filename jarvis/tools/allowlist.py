"""Exactly three model-visible tools for the first vertical slice.

* ``get_local_time``          read-only, low risk
* ``get_system_status``       read-only, low risk, fixed and enumerated fields only
* ``open_allowed_application`` effectful, ``ConfirmationMode.ALWAYS``, closed enum

Every other Wyzer capability (browser, files, clipboard, desktop interaction,
perception, audio, coding agent, external packs) is simply not registered, so the
model cannot see or call it. Side effects go through an ``ApplicationLauncher``; the
default is a simulated launcher. The Windows launcher refuses to act unless the
platform is Windows *and* the configuration explicitly allows real actions.
"""

from __future__ import annotations

import sys
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal, Protocol
from uuid import uuid4
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, Field

from wyzer.models import ConfirmationMode, RiskLevel, ToolArguments
from wyzer.tools import ToolRegistry
from wyzer.tools.base import Tool, ToolContext, ToolExecutionError

from jarvis.config import AllowedApplication

ToolStartedCallback = Callable[[str], None]

ALLOWLIST_TOOL_NAMES: tuple[str, ...] = (
    "get_local_time",
    "get_system_status",
    "open_allowed_application",
)


def _noop(_: str) -> None:
    return None


# --------------------------------------------------------------------------- time


class NoArguments(ToolArguments):
    pass


class LocalTimeResult(BaseModel):
    iso: str
    hour: int
    minute: int
    weekday: int = Field(description="0 = Monday")
    date: str
    timezone: str
    timezone_source: Literal["configured", "system"]


Clock = Callable[[], datetime]


class GetLocalTimeTool(Tool[NoArguments, LocalTimeResult]):
    name = "get_local_time"
    description = "Read the current local date and time. Read-only."
    arguments_type = NoArguments
    result_type = LocalTimeResult
    risk_level = RiskLevel.LOW
    read_only = True
    confirmation = ConfirmationMode.NEVER
    default_timeout_seconds = 5

    def __init__(
        self,
        timezone: str,
        *,
        clock: Clock | None = None,
        on_start: ToolStartedCallback = _noop,
    ) -> None:
        self._timezone_name = timezone
        self._clock = clock
        self._on_start = on_start

    def _now(self) -> tuple[datetime, str, Literal["configured", "system"]]:
        try:
            zone = ZoneInfo(self._timezone_name)
        except (ZoneInfoNotFoundError, ValueError):
            # Windows ships without the IANA database unless tzdata is installed.
            now = self._clock() if self._clock else datetime.now().astimezone()
            return now.astimezone(), str(now.astimezone().tzname()), "system"
        now = self._clock() if self._clock else datetime.now(zone)
        return now.astimezone(zone), self._timezone_name, "configured"

    def execute(self, arguments: NoArguments, context: ToolContext) -> LocalTimeResult:
        del arguments, context
        self._on_start(self.name)
        now, zone_name, source = self._now()
        return LocalTimeResult(
            iso=now.isoformat(timespec="minutes"),
            hour=now.hour,
            minute=now.minute,
            weekday=now.weekday(),
            date=now.date().isoformat(),
            timezone=zone_name,
            timezone_source=source,
        )


# ------------------------------------------------------------------ system status


class SystemStatusResult(BaseModel):
    """The complete, pre-authorised field list. Nothing else may be returned."""

    cpu_percent: float = Field(ge=0, le=100)
    memory_percent: float = Field(ge=0, le=100)
    memory_used_gb: float = Field(ge=0)
    memory_total_gb: float = Field(ge=0)
    uptime_minutes: int = Field(ge=0)
    battery_percent: float | None = Field(default=None, ge=0, le=100)
    on_ac_power: bool | None = None


class SystemProbe(Protocol):
    def read(self) -> SystemStatusResult: ...


class PsutilSystemProbe:
    """Read-only probe using psutil (already pinned by the Wyzer constraints)."""

    def read(self) -> SystemStatusResult:
        import psutil

        memory = psutil.virtual_memory()
        battery = psutil.sensors_battery() if hasattr(psutil, "sensors_battery") else None
        return SystemStatusResult(
            cpu_percent=float(psutil.cpu_percent(interval=0.2)),
            memory_percent=float(memory.percent),
            memory_used_gb=round((memory.total - memory.available) / 1024**3, 1),
            memory_total_gb=round(memory.total / 1024**3, 1),
            uptime_minutes=max(0, int((time.time() - psutil.boot_time()) // 60)),
            battery_percent=float(battery.percent) if battery is not None else None,
            on_ac_power=bool(battery.power_plugged) if battery is not None else None,
        )


class GetSystemStatusTool(Tool[NoArguments, SystemStatusResult]):
    name = "get_system_status"
    description = (
        "Read CPU use, memory use, uptime and battery level of this computer. Read-only."
    )
    arguments_type = NoArguments
    result_type = SystemStatusResult
    risk_level = RiskLevel.LOW
    read_only = True
    confirmation = ConfirmationMode.NEVER
    default_timeout_seconds = 5

    def __init__(self, probe: SystemProbe, *, on_start: ToolStartedCallback = _noop) -> None:
        self._probe = probe
        self._on_start = on_start

    def execute(self, arguments: NoArguments, context: ToolContext) -> SystemStatusResult:
        del arguments, context
        self._on_start(self.name)
        return SystemStatusResult.model_validate(self._probe.read().model_dump())


# ------------------------------------------------------------- open application


class OpenAllowedApplicationArguments(ToolArguments):
    app: AllowedApplication = Field(
        description="Which approved application to open: calculator or notepad."
    )


class LaunchResult(BaseModel):
    app: str
    opened: bool
    simulated: bool
    launch_id: str
    detail: str = ""


class ApplicationLauncher(Protocol):
    simulated: bool

    def launch(self, app: AllowedApplication) -> LaunchResult: ...


@dataclass
class SimulatedLauncher:
    """Records launches without starting any process (cloud, CI, tests)."""

    simulated: bool = True
    launched: list[str] = field(default_factory=list)

    def launch(self, app: AllowedApplication) -> LaunchResult:
        self.launched.append(app)
        return LaunchResult(
            app=app,
            opened=True,
            simulated=True,
            launch_id=uuid4().hex,
            detail="SIMULATED: no process was started",
        )


# Display names tried in order on Windows (English, then Portuguese UI).
WINDOWS_APPLICATION_NAMES: dict[str, tuple[str, ...]] = {
    "calculator": ("Calculator", "Calculadora"),
    "notepad": ("Notepad", "Bloco de Notas"),
}


class RealWindowsActionsDisabledError(RuntimeError):
    pass


class WindowsApplicationLauncher:
    """Delegates to Wyzer's ``OpenApplicationTool`` on Windows only (JAR-SLICE-01D).

    Not used in 01B. Construction fails closed unless the platform is Windows and the
    caller passes ``allow_real_windows_actions=True`` from an approved configuration.
    """

    simulated = False

    def __init__(self, *, allow_real_windows_actions: bool, platform: str | None = None) -> None:
        current = platform or sys.platform
        if current != "win32":
            raise RealWindowsActionsDisabledError(
                f"real Windows actions are unavailable on platform {current!r}"
            )
        if not allow_real_windows_actions:
            raise RealWindowsActionsDisabledError(
                "real Windows actions are disabled (vexel.allow_real_windows_actions = false)"
            )
        from wyzer.desktop.windows_backend import CtypesWindowsBackend
        from wyzer.tools.windows import OpenApplicationArguments, OpenApplicationTool

        self._tool = OpenApplicationTool(CtypesWindowsBackend())
        self._arguments_type = OpenApplicationArguments

    def launch(self, app: AllowedApplication) -> LaunchResult:
        last_error: Exception | None = None
        for name in WINDOWS_APPLICATION_NAMES[app]:
            try:
                self._tool.execute(
                    self._arguments_type(application=name),
                    ToolContext(uuid4(), uuid4()),
                )
            except Exception as error:  # try the next localised name
                last_error = error
                continue
            return LaunchResult(
                app=app, opened=True, simulated=False, launch_id=uuid4().hex, detail=name
            )
        raise ToolExecutionError(
            "APPLICATION_NOT_OPENED",
            f"Could not open {app}.",
            details={"error": type(last_error).__name__ if last_error else "unknown"},
        )


class OpenAllowedApplicationTool(Tool[OpenAllowedApplicationArguments, LaunchResult]):
    name = "open_allowed_application"
    description = (
        "Open one approved desktop application (calculator or notepad). "
        "Always asks the user to confirm first."
    )
    arguments_type = OpenAllowedApplicationArguments
    result_type = LaunchResult
    risk_level = RiskLevel.MEDIUM
    read_only = False
    confirmation = ConfirmationMode.ALWAYS
    default_timeout_seconds = 15

    def __init__(
        self,
        launcher: ApplicationLauncher,
        allowed: Sequence[AllowedApplication],
        *,
        on_start: ToolStartedCallback = _noop,
    ) -> None:
        self._launcher = launcher
        self._allowed = frozenset(allowed)
        self._on_start = on_start

    def execute(
        self, arguments: OpenAllowedApplicationArguments, context: ToolContext
    ) -> LaunchResult:
        del context
        if arguments.app not in self._allowed:
            raise ToolExecutionError(
                "APPLICATION_NOT_ALLOWED", f"{arguments.app} is not in the configured allowlist."
            )
        self._on_start(self.name)
        return self._launcher.launch(arguments.app)


# --------------------------------------------------------------------- registry


def build_allowlist_registry(
    *,
    timezone: str,
    allowed_applications: Sequence[AllowedApplication],
    launcher: ApplicationLauncher,
    probe: SystemProbe,
    clock: Clock | None = None,
    on_tool_start: ToolStartedCallback = _noop,
) -> ToolRegistry:
    registry = ToolRegistry()
    registry.register_many(
        (
            GetLocalTimeTool(timezone, clock=clock, on_start=on_tool_start),
            GetSystemStatusTool(probe, on_start=on_tool_start),
            OpenAllowedApplicationTool(launcher, allowed_applications, on_start=on_tool_start),
        )
    )
    if tuple(registry) != tuple(sorted(ALLOWLIST_TOOL_NAMES)):
        raise RuntimeError("allowlist registry drifted from ALLOWLIST_TOOL_NAMES")
    return registry
