"""Read the local Salesforce CLI deploy cache (no org writes).

``sf project deploy report --job-id`` will return a cached job even when
``--target-org`` names a different org. The product must not diagnose Org A
using Org B's cached result.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


def deploy_cache_path() -> Path:
    override = os.environ.get("SFSKILLS_DEPLOY_CACHE")
    if override:
        return Path(override).expanduser()
    return Path.home() / ".sf" / "deploy-cache.json"


def cache_entry_for_job(job_id: str) -> dict[str, Any] | None:
    path = deploy_cache_path()
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    entry = payload.get(job_id)
    return entry if isinstance(entry, dict) else None


def cache_target_org(job_id: str) -> str | None:
    entry = cache_entry_for_job(job_id)
    if not entry:
        return None
    value = entry.get("target-org") or entry.get("targetOrg")
    return str(value) if value else None


def usernames_match(left: str | None, right: str | None) -> bool:
    if not left or not right:
        return False
    return left.strip().lower() == right.strip().lower()
