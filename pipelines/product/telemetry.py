"""Redacted local run telemetry under .sfskills/runs/<run_id>/."""

from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_RUN_ROOT_NAME = ".sfskills"
_TOKEN_RE = re.compile(r"\b00[A-Z][A-Za-z0-9]{12,15}![A-Za-z0-9._\-]{20,200}")


def default_runs_root(cwd: Path | None = None) -> Path:
    base = cwd or Path.cwd()
    return base / _RUN_ROOT_NAME / "runs"


def new_run_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")


def redact(value: Any) -> Any:
    if isinstance(value, str):
        return _TOKEN_RE.sub("[REDACTED]", value)
    if isinstance(value, dict):
        out = {}
        for key, val in value.items():
            if str(key).lower() in {"accesstoken", "refreshtoken", "password", "sessionid"}:
                out[key] = "[REDACTED]"
            else:
                out[key] = redact(val)
        return out
    if isinstance(value, list):
        return [redact(item) for item in value]
    return value


def write_run(run_id: str, payload: dict[str, Any], *, cwd: Path | None = None) -> Path:
    root = default_runs_root(cwd)
    dest = root / run_id
    dest.mkdir(parents=True, exist_ok=True)
    body = redact(payload)
    path = dest / "telemetry.json"
    path.write_text(json.dumps(body, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def append_compaction_event(run_id: str, event: dict[str, Any], *, cwd: Path | None = None) -> Path:
    root = default_runs_root(cwd) / run_id
    root.mkdir(parents=True, exist_ok=True)
    path = root / "compaction.jsonl"
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(redact(event), sort_keys=True) + "\n")
    return path


def gitignore_hint() -> str:
    return os.path.join(_RUN_ROOT_NAME, "runs/")
