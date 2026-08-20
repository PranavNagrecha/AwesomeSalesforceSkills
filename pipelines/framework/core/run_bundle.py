"""Redacted replayable run bundle persistence."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_RUN_ROOT = ROOT / ".sfskills" / "runs"

_SECRET_RE = re.compile(
    r"(sfdxAuthUrl|BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY|Bearer\s+ey[A-Za-z0-9_-]+\.)",
    re.IGNORECASE,
)
_REDACTED = "[REDACTED]"


def _redact_value(value: Any) -> Any:
    if isinstance(value, str):
        return _SECRET_RE.sub(_REDACTED, value)
    if isinstance(value, dict):
        return {k: _redact_value(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_redact_value(item) for item in value]
    return value


def run_directory(run_id: str, base: Path | None = None) -> Path:
    base = base or DEFAULT_RUN_ROOT
    safe = run_id.replace("/", "_")
    return base / safe


def write_run_bundle(
    run_id: str,
    *,
    run_record: dict[str, Any],
    evidence: list[dict[str, Any]] | None = None,
    claims: list[dict[str, Any]] | None = None,
    context_manifest: dict[str, Any] | None = None,
    handoffs: list[dict[str, Any]] | None = None,
    output_envelope: dict[str, Any] | None = None,
    deterministic_lint: dict[str, Any] | None = None,
    independent_review: dict[str, Any] | None = None,
    base: Path | None = None,
) -> Path:
    directory = run_directory(run_id, base)
    directory.mkdir(parents=True, exist_ok=True)
    artifacts = {
        "run.json": run_record,
        "evidence.json": evidence or [],
        "claims.json": claims or [],
        "context-manifest.json": context_manifest or {},
        "handoffs.json": handoffs or [],
        "output.json": output_envelope or {},
        "deterministic-lint.json": deterministic_lint or {},
        "independent-review.json": independent_review or {},
    }
    for name, payload in artifacts.items():
        redacted = _redact_value(payload)
        (directory / name).write_text(
            json.dumps(redacted, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    return directory


def load_run_bundle(run_id: str, base: Path | None = None) -> dict[str, Any]:
    directory = run_directory(run_id, base)
    if not directory.is_dir():
        raise FileNotFoundError(directory)
    result: dict[str, Any] = {"run_id": run_id, "directory": str(directory)}
    for name in (
        "run.json",
        "evidence.json",
        "claims.json",
        "context-manifest.json",
        "handoffs.json",
        "output.json",
        "deterministic-lint.json",
        "independent-review.json",
    ):
        path = directory / name
        if path.is_file():
            result[name.replace(".json", "").replace("-", "_")] = json.loads(path.read_text(encoding="utf-8"))
    return result


def validate_bundle_redaction(run_id: str, base: Path | None = None) -> list[str]:
    directory = run_directory(run_id, base)
    issues: list[str] = []
    if not directory.is_dir():
        return [f"bundle missing: {directory}"]
    for path in directory.glob("*.json"):
        text = path.read_text(encoding="utf-8")
        if _SECRET_RE.search(text):
            issues.append(f"unredacted secret pattern in {path.name}")
    return issues
