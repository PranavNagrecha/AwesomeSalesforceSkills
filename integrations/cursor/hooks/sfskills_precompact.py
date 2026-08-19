#!/usr/bin/env python3
"""Observe Cursor preCompact events. Does not rewrite or prevent compaction."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path


def main() -> int:
    raw = sys.stdin.read()
    try:
        payload = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        payload = {"error": "invalid_json"}
    event = {
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "hook": "preCompact",
        "payload_keys": sorted(payload.keys()) if isinstance(payload, dict) else [],
        "note": "Observation only. SfSkills cannot prevent Cursor compaction.",
    }
    cwd = Path.cwd()
    dest_dir = cwd / ".sfskills" / "runs" / "_compaction"
    try:
        dest_dir.mkdir(parents=True, exist_ok=True)
        with (dest_dir / "events.jsonl").open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, sort_keys=True) + "\n")
    except OSError:
        pass
    json.dump({"continue": True}, sys.stdout)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
