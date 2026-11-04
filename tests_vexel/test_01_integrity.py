"""Test 1 — the 182 protected Wyzer files are byte-identical to the manifest."""

from __future__ import annotations

import subprocess
import sys

from tests_vexel.fakes import REPO_ROOT


def test_source_integrity_182_of_182() -> None:
    # Runs the repository's own read-only verifier (hash check only, no install).
    completed = subprocess.run(  # noqa: S603 - fixed argv, test-only
        [sys.executable, str(REPO_ROOT / "scripts" / "verify_import.py")],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    output = completed.stdout + completed.stderr
    assert completed.returncode == 0, output
    assert "182/182" in output
    assert "SOURCE_INTEGRITY_PASS" in output
