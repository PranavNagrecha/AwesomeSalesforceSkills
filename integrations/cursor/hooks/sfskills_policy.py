#!/usr/bin/env python3
"""Cursor hook entry: fail-closed Salesforce mutation guard.

Reads JSON from stdin (beforeShellExecution / beforeMCPExecution). Writes a
permission decision to stdout. Exit 2 also means deny.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Plugin dist layout: <plugin>/hooks/this.py → walk up to repo, or import via
# baked PYTHONPATH. Fall back to locating AGENT_RULES.md.
def _repo_root() -> Path | None:
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "AGENT_RULES.md").is_file() and (parent / "pipelines" / "product").is_dir():
            return parent
    pointer = here.parent.parent / "repo-root.json"
    if pointer.is_file():
        try:
            raw = json.loads(pointer.read_text(encoding="utf-8"))
            path = Path(raw["repo_root"])
            if path.is_dir():
                return path
        except (OSError, KeyError, json.JSONDecodeError):
            return None
    return None


def main() -> int:
    raw = sys.stdin.read()
    try:
        payload = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        decision = {
            "permission": "deny",
            "user_message": "SfSkills policy: hook received invalid JSON (failClosed)",
            "agent_message": "Hook payload was not JSON. Refusing the action.",
        }
        json.dump(decision, sys.stdout)
        return 2

    root = _repo_root()
    if root is None:
        decision = {
            "permission": "deny",
            "user_message": "SfSkills policy: cannot locate repository (failClosed)",
            "agent_message": "Install the plugin with --link from a SfSkills checkout.",
        }
        json.dump(decision, sys.stdout)
        return 2

    sys.path.insert(0, str(root))
    from pipelines.product.policy import evaluate_hook_payload

    decision = evaluate_hook_payload(payload)
    json.dump(decision, sys.stdout)
    if decision.get("permission") == "deny":
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
