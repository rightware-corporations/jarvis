"""Load the VEXEL slice configuration without touching the upstream ``wyzer.toml``.

The file is ordinary Wyzer TOML plus one ``[vexel]`` table. ``WyzerSettings`` forbids
unknown keys, so the ``[vexel]`` table is split off and validated here first. The
slice also refuses settings that would break the RIGHTWARE rules: a non-loopback or
keyed LLM endpoint, English-only Whisper models, pre-trained non-commercial wake
models, memory/tasks/coding agent, and worker isolation (tools must notify state).
"""

from __future__ import annotations

import ipaddress
import tomllib
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field, field_validator

from wyzer.config import WyzerSettings

AllowedApplication = Literal["calculator", "notepad"]

WAKE_WORD_BLOCKED = "WAKE_WORD_BLOCKED"


class SliceConfigError(ValueError):
    """The slice configuration violates a RIGHTWARE rule or is malformed."""


class WakeWordBlockedError(SliceConfigError):
    def __init__(self, detail: str) -> None:
        super().__init__(f"{WAKE_WORD_BLOCKED}: {detail}")


class VexelSettings(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    language: Literal["pt"] = "pt"
    timezone: str = Field(default="Africa/Maputo", min_length=1, max_length=64)
    activation: Literal["manual"] = "manual"
    allowed_applications: tuple[AllowedApplication, ...] = ("calculator", "notepad")
    stt_hotwords: str = Field(
        default="Jarvis calculadora bloco de notas estado do computador cancela sim não",
        max_length=400,
    )
    listen_timeout_seconds: float = Field(default=8, gt=0, le=60)
    confirmation_listen_timeout_seconds: float = Field(default=8, gt=0, le=60)
    allow_real_windows_actions: bool = False
    log_transcript_text: bool = False

    @field_validator("allowed_applications")
    @classmethod
    def _unique_apps(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if len(set(value)) != len(value):
            raise ValueError("allowed_applications contains duplicates")
        return value


@dataclass(frozen=True, slots=True)
class SliceConfig:
    wyzer: WyzerSettings
    vexel: VexelSettings
    source: Path | None


_LOOPBACK_NAMES = {"localhost"}


def _is_loopback(host: str) -> bool:
    if host.casefold() in _LOOPBACK_NAMES:
        return True
    try:
        return ipaddress.ip_address(host.strip("[]")).is_loopback
    except ValueError:
        return False


def _validate_slice_rules(settings: WyzerSettings) -> None:
    llm = settings.llm
    if llm.provider == "none":
        raise SliceConfigError("the slice requires a local LLM provider (llm.provider)")
    if llm.endpoint is not None:
        host = urlparse(str(llm.endpoint)).hostname or ""
        if not _is_loopback(host):
            raise SliceConfigError(
                f"llm.endpoint must be loopback for the slice, got host {host!r}"
            )
    if llm.api_key is not None and llm.api_key.get_secret_value():
        raise SliceConfigError("llm.api_key must be empty: no keyed or paid AI endpoint")
    if llm.auto_start:
        raise SliceConfigError(
            "llm.auto_start must be false: the slice never launches processes by itself"
        )

    speech = settings.speech
    if speech.whisper_model.casefold().endswith(".en"):
        raise SliceConfigError(
            f"whisper_model {speech.whisper_model!r} is English-only; use a multilingual model"
        )
    if speech.volume <= 0:
        raise SliceConfigError(
            "speech.volume must be above 0: a silent voice cannot present a confirmation"
        )
    if speech.wake_word_adapter != "manual":
        raise WakeWordBlockedError(
            "no commercially licensed wake model is approved; set wake_word_adapter = 'manual'"
        )
    if settings.memory.enabled:
        raise SliceConfigError("memory must stay disabled in JAR-SLICE-01")
    if settings.task_engine.enabled:
        raise SliceConfigError("task_engine must stay disabled in JAR-SLICE-01")
    if settings.coding_agent.enabled:
        raise SliceConfigError("coding_agent must stay disabled in JAR-SLICE-01")
    if settings.worker_isolation_enabled:
        raise SliceConfigError("worker_isolation_enabled must be false in JAR-SLICE-01")
    if settings.tool_packs.enabled:
        raise SliceConfigError("external tool packs are not allowed in JAR-SLICE-01")


def parse_slice_config(data: Mapping[str, Any], source: Path | None = None) -> SliceConfig:
    raw = dict(data)
    vexel_raw = raw.pop("vexel", {})
    if not isinstance(vexel_raw, Mapping):
        raise SliceConfigError("[vexel] must be a table")
    try:
        vexel = VexelSettings.model_validate(dict(vexel_raw))
        wyzer = WyzerSettings.model_validate(raw)
    except ValueError as error:
        raise SliceConfigError(str(error)) from error
    _validate_slice_rules(wyzer)
    return SliceConfig(wyzer=wyzer, vexel=vexel, source=source)


def load_slice_config(path: Path) -> SliceConfig:
    """Read a slice TOML file. Environment overrides are deliberately not applied."""
    with path.open("rb") as handle:
        data = tomllib.load(handle)
    return parse_slice_config(data, source=path)
