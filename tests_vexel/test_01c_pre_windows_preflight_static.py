"""Static safety review of the Windows QA preflight script (it is never executed here)."""

from __future__ import annotations

import re

import pytest

from tests_vexel.fakes import REPO_ROOT

SCRIPT = REPO_ROOT / "qa" / "windows" / "Invoke-JarvisPreflight.ps1"
TEXT = SCRIPT.read_text(encoding="utf-8")
# Comment-based help and line comments may legitimately *mention* forbidden things.
CODE = re.sub(r"<#.*?#>", "", TEXT, flags=re.S)
CODE = "\n".join(line.split("#", 1)[0] if not line.lstrip().startswith("#Requires") else ""
                 for line in CODE.splitlines())

FORBIDDEN = {
    "install": r"\b(Install-(Module|Package|Script)|winget|choco|msiexec|pip\s+install|Add-AppxPackage)\b",
    "download": r"\b(Invoke-WebRequest|Start-BitsTransfer|DownloadString|DownloadFile|WebClient|curl\.exe|wget)\b",
    "ollama_mutation": r"\bollama(\.exe)?\b[^\n]*\b(pull|run|serve|rm|create|cp|push)\b",
    "registry_write": r"\b(Set-ItemProperty|New-ItemProperty|Remove-ItemProperty|Rename-ItemProperty|reg(\.exe)?\s+(add|delete|import))\b",
    "file_delete_move": r"\b(Remove-Item|Move-Item|Rename-Item|Clear-Content|Copy-Item)\b",
    "service_process": r"\b(Start-Service|Stop-Service|Set-Service|Restart-Service|New-Service|Start-Process|Stop-Process|Restart-Computer|Stop-Computer)\b",
    "policy": r"\b(Set-ExecutionPolicy|Set-MpPreference|Set-NetFirewall\w*|New-NetFirewall\w*)\b",
    "elevation": r"(-Verb\s+RunAs|runas\.exe)",
    "dynamic_code": r"\b(Invoke-Expression|iex)\b|\[scriptblock\]::Create",
    "audio_record_speak": r"\b(SetInputToDefaultAudioDevice|SetInputToWaveFile|Recognize(Async)?\(|\.Speak(Async)?\(|SoundPlayer)\b",
    "transcript_header": r"\bStart-Transcript\b",
    "secrets": r"\b(Get-StoredCredential|ConvertFrom-SecureString|cmdkey|vaultcmd|Get-Credential)\b",
    "identity": r"\b(SerialNumber|MACAddress|IPAddress|Get-NetIPAddress|ipconfig|whoami)\b",
}


@pytest.mark.parametrize("name", sorted(FORBIDDEN))
def test_script_contains_no_forbidden_operation(name: str) -> None:
    match = re.search(FORBIDDEN[name], CODE, flags=re.I)
    assert match is None, f"{name}: {match.group(0) if match else ''}"


def test_only_loopback_network_access() -> None:
    urls = re.findall(r"https?://[^\s'\"]+", CODE)
    assert urls and all(url.startswith("http://127.0.0.1") for url in urls), urls
    assert set(re.findall(r"-Method\s+(\w+)", CODE)) == {"Get"}
    assert "'127.0.0.1'" in CODE  # TCP port probe target


def test_writes_only_its_own_report_files() -> None:
    writes = [m.group(0) for m in re.finditer(r"\b(?:Set-Content|Add-Content|Out-File|New-Item)\b[^\n]*", CODE)]
    assert writes, "expected the report writes"
    for line in writes:
        assert "$target" in line or "$OutputDirectory" in line, line
    assert re.search(r"New-Item -ItemType Directory -Path \$target", CODE)


def test_clipboard_is_opt_in() -> None:
    assert re.search(r"if \(\$CopySummary\) \{\s*\n\s*Set-Clipboard", CODE)
    assert CODE.count("Set-Clipboard") == 1


def test_redaction_covers_user_and_machine_identity() -> None:
    for token in ("$env:USERNAME", "$env:COMPUTERNAME", "$env:USERPROFILE", "$env:USERDOMAIN"):
        assert token in CODE
    # Every written artefact goes through Protect-Text or the sanitised transcript.
    assert "Protect-Text $json" in CODE and "Protect-Text $_" in CODE


def test_powershell_51_compatible_syntax() -> None:
    assert TEXT.startswith("#Requires -Version 5.1")
    # PowerShell 7-only operators would fail on stock Windows PowerShell 5.1.
    assert not re.search(r"\?\?|\?\.|\s\?\s[^:]+\s:\s|&&|\|\||-Parallel", CODE)
    for opening, closing in ("{}", "()", "[]"):
        assert CODE.count(opening) == CODE.count(closing), opening + closing


def test_script_is_documented_as_not_executed_by_author() -> None:
    assert "Not executed by the author" in TEXT
    assert "-ExecutionPolicy Bypass applies to this one process only" in TEXT


def test_script_is_ascii_for_windows_powershell_51() -> None:
    # Windows PowerShell 5.1 reads BOM-less files as the ANSI code page.
    assert TEXT.isascii()


def test_native_calls_do_not_abort_on_stderr() -> None:
    # Under ErrorActionPreference='Stop', 5.1 turns native stderr into a terminating error.
    for probe in ("'python'", "'ollama'"):
        body = CODE.split(f"Invoke-Probe {probe} {{", 1)[1].split("\n}", 1)[0]
        assert "$ErrorActionPreference = 'Continue'" in body, probe
