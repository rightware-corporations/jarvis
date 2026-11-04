#!/usr/bin/env python3
"""Verify vendored Wyzer source bytes against the pinned upstream Git blob IDs.

This verifies source integrity only; it neither imports modules nor executes tools.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "upstream-v0.3.1-manifest.json"


def git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\x00" + data).hexdigest()


def main() -> int:
    document = json.loads(MANIFEST.read_text(encoding="utf-8"))
    items = document["imported"]
    failures: list[str] = []
    if len(items) != document["imported_count"]:
        failures.append("Manifest imported_count differs from imported entry count")
    if len(document["excluded"]) != document["excluded_count"]:
        failures.append("Manifest excluded_count differs from excluded entry count")
    seen: set[str] = set()
    for entry in items:
        destination = entry["destination"]
        path = PurePosixPath(destination)
        if path.is_absolute() or ".." in path.parts or destination in seen:
            failures.append(f"Unsafe or duplicate path: {destination}")
            continue
        seen.add(destination)
        actual = ROOT.joinpath(*path.parts)
        if not actual.is_file():
            failures.append(f"Missing: {destination}")
            continue
        data = actual.read_bytes()
        actual_sha = git_blob_sha(data)
        if actual_sha != entry["blob_sha"]:
            failures.append(f"Modified: {destination}: {actual_sha} != {entry['blob_sha']}")
    for path in ("LICENSE", "NOTICE.md", "UPSTREAM_PROVENANCE.md", "pyproject.toml"):
        if not (ROOT / path).is_file():
            failures.append(f"Missing required project file: {path}")
    print(f"Wyzer upstream: {document['upstream_repo']}@{document['upstream_commit']}")
    print(f"Source integrity: {len(items) - len([f for f in failures if f.startswith('Missing:') or f.startswith('Modified:')])}/{len(items)}")
    print(f"Binary assets intentionally excluded: {document['excluded_count']}")
    if failures:
        print("FAILURES:")
        for failure in failures:
            print(" - " + failure)
        return 1
    print("SOURCE_INTEGRITY_PASS (not functional/runtime verification)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
