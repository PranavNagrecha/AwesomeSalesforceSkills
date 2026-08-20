#!/usr/bin/env python3
"""Capture M1 milestone gate evidence under .sfskills/v2-evidence/m1/."""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / ".sfskills" / "v2-evidence" / "m1"
M0_TAG = "sfskills-v2-m0-spec-adopted"
KERNEL_ROOT = ROOT / "framework" / "specification" / "reference-kernel"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def run(command: list[str], cwd: Path | None = None) -> dict:
    started = utc_now()
    proc = subprocess.run(command, cwd=cwd or ROOT, capture_output=True, text=True, check=False)
    return {
        "command": command,
        "cwd": str(cwd or ROOT),
        "started_utc": started,
        "finished_utc": utc_now(),
        "exit_code": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
    }


def write_gate(name: str, result: dict, classification: str) -> None:
    payload = {**result, "classification": classification}
    gate_dir = EVIDENCE / "gates"
    gate_dir.mkdir(parents=True, exist_ok=True)
    (gate_dir / f"{name}.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (gate_dir / f"{name}.log").write_text(
        "\n".join(
            [
                f"command: {' '.join(result['command'])}",
                f"exit_code: {result['exit_code']}",
                f"classification: {classification}",
                "",
                result.get("stdout") or "",
                result.get("stderr") or "",
            ]
        ),
        encoding="utf-8",
    )


def _clean_kernel_pycache() -> None:
    import shutil

    if not KERNEL_ROOT.is_dir():
        return
    for cache in KERNEL_ROOT.rglob("__pycache__"):
        if cache.is_dir():
            shutil.rmtree(cache)


def main() -> int:
    _clean_kernel_pycache()
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=False
    ).stdout.strip()
    meta = {
        "milestone": "m1-deterministic-core",
        "branch": "product/sfskills-v2-local",
        "m0_tag": M0_TAG,
        "head_sha": head,
        "captured_utc": utc_now(),
    }
    (EVIDENCE / "metadata.json").write_text(
        json.dumps(meta, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    gates: list[tuple[str, list[str], str, Path | None]] = [
        (
            "framework-tests",
            [
                sys.executable,
                "-B",
                "-m",
                "unittest",
                "discover",
                "-s",
                "tests/framework",
                "-p",
                "test_*.py",
            ],
            "required",
            ROOT,
        ),
        (
            "product-tests",
            [
                sys.executable,
                "-B",
                "-m",
                "unittest",
                "discover",
                "-s",
                "tests/product",
                "-p",
                "test_*.py",
            ],
            "required",
            ROOT,
        ),
        (
            "reference-kernel-tests",
            [
                sys.executable,
                "-B",
                "-m",
                "unittest",
                "discover",
                "-s",
                "tests",
                "-p",
                "test_*.py",
            ],
            "required",
            KERNEL_ROOT,
        ),
        ("validate-framework", [sys.executable, "-B", "scripts/validate_framework.py"], "required", ROOT),
    ]
    failed = False
    for name, cmd, classification, cwd in gates:
        result = run(cmd, cwd=cwd)
        write_gate(name, result, classification)
        if result["exit_code"] != 0:
            failed = True
    _clean_kernel_pycache()
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
