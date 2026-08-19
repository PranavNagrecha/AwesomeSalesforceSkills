"""Pilot context pack for deployment failure triage.

Not a repository-wide dependency engine. Selection is deterministic from
observed failure classes.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]

TARGET_FILES = 8
HARD_LIMIT = 12
CHARS_PER_TOKEN = 4  # conservative estimate; telemetry only


CORE_READS: list[dict[str, str]] = [
    {
        "path": "agents/_shared/AGENT_CONTRACT.md",
        "reason": "Output envelope, confidence rubric, process observations",
        "class": "contract",
    },
    {
        "path": "agents/_shared/DELIVERABLE_CONTRACT.md",
        "reason": "Persisted report + envelope requirement",
        "class": "contract",
    },
    {
        "path": "skills/devops/deployment-error-troubleshooting/SKILL.md",
        "reason": "DeployMessage / componentFailures taxonomy",
        "class": "skill",
    },
    {
        "path": "skills/devops/deployment-error-diagnosis/SKILL.md",
        "reason": "Failure-class diagnosis patterns",
        "class": "skill",
    },
    {
        "path": "skills/devops/metadata-api-retrieve-deploy/SKILL.md",
        "reason": "Metadata API deploy semantics and limits",
        "class": "skill",
    },
]

CONDITIONAL_PACKS: dict[str, list[dict[str, str]]] = {
    "component_failure": [
        {
            "path": "skills/devops/deployment-error-troubleshooting/references/gotchas.md",
            "reason": "Common componentFailure gotchas",
            "class": "reference",
        },
    ],
    "test_failure": [
        {
            "path": "skills/apex/test-class-standards/SKILL.md",
            "reason": "Apex test failure patterns during deploy",
            "class": "skill",
        },
        {
            "path": "skills/devops/automated-regression-testing/SKILL.md",
            "reason": "Deploy-time test execution expectations",
            "class": "skill",
        },
    ],
    "coverage": [
        {
            "path": "skills/devops/code-coverage-orphan-class-cleanup/SKILL.md",
            "reason": "Coverage failures and orphan classes",
            "class": "skill",
        },
    ],
    "missing_metadata": [
        {
            "path": "skills/data/deployment-data-dependencies/SKILL.md",
            "reason": "Missing field/object dependency at deploy",
            "class": "skill",
        },
    ],
    "api_version": [
        {
            "path": "skills/devops/api-version-management/SKILL.md",
            "reason": "API version mismatch at deploy",
            "class": "skill",
        },
    ],
    "permissions": [
        {
            "path": "skills/devops/permission-set-deployment-ordering/SKILL.md",
            "reason": "Permission set ordering / FLS drop on deploy",
            "class": "skill",
        },
    ],
    "destructive": [
        {
            "path": "skills/devops/destructive-changes-deployment/SKILL.md",
            "reason": "Destructive changes and dependency errors",
            "class": "skill",
        },
    ],
}

# Distractors the librarian must not load unless a class matches.
DISTRACTORS = [
    "skills/omnistudio/omnistudio-deployment-datapacks/SKILL.md",
    "skills/agentforce/agent-deployment-checklist/SKILL.md",
]


def classify_failures(normalized: dict[str, Any]) -> list[str]:
    classes: list[str] = []
    if normalized.get("component_failures") or (normalized.get("source_counts") or {}).get("component_failures"):
        classes.append("component_failure")
    if normalized.get("test_failures") or (normalized.get("source_counts") or {}).get("test_failures"):
        classes.append("test_failure")
    if normalized.get("coverage") or (normalized.get("source_counts") or {}).get("coverage"):
        classes.append("coverage")
    blob = json.dumps(normalized, ensure_ascii=False).lower()
    if any(s in blob for s in ("no such column", "invalid field", "not found", "missing", "dependent class is invalid")):
        classes.append("missing_metadata")
    if "api version" in blob or "apiversion" in blob or "version specified" in blob:
        classes.append("api_version")
    if any(s in blob for s in ("insufficient_access", "permission", "fls", "crud")):
        classes.append("permissions")
    if "destructive" in blob or "delete" in blob and "cannot" in blob:
        classes.append("destructive")
    # Preserve order, unique.
    seen: set[str] = set()
    out: list[str] = []
    for item in classes:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out


def _estimate_tokens(path: Path) -> int:
    if not path.is_file():
        return 0
    size = path.stat().st_size
    return max(1, size // CHARS_PER_TOKEN)


def select_context_pack(
    normalized: dict[str, Any],
    *,
    repo_root: Path | None = None,
    extra_paths: list[str] | None = None,
) -> dict[str, Any]:
    root = repo_root or REPO_ROOT
    selected: list[dict[str, Any]] = []
    seen: set[str] = set()

    def add(item: dict[str, str]) -> None:
        rel = item["path"]
        if rel in seen:
            return
        seen.add(rel)
        full = root / rel
        selected.append(
            {
                "path": rel,
                "reason": item["reason"],
                "class": item.get("class", "other"),
                "exists": full.is_file(),
                "estimated_tokens": _estimate_tokens(full),
                "bytes": full.stat().st_size if full.is_file() else 0,
            }
        )

    for item in CORE_READS:
        add(item)
    for failure_class in classify_failures(normalized):
        for item in CONDITIONAL_PACKS.get(failure_class, []):
            add(item)
    for rel in extra_paths or []:
        add({"path": rel, "reason": "caller extra", "class": "extra"})

    domain_files = [s for s in selected if s["class"] in {"skill", "reference"}]
    overflow = False
    if len(domain_files) > HARD_LIMIT:
        overflow = True
        # Keep core + first conditional files up to HARD_LIMIT domain files.
        kept: list[dict[str, Any]] = []
        domain_kept = 0
        for row in selected:
            if row["class"] in {"skill", "reference"}:
                if domain_kept >= HARD_LIMIT:
                    overflow = True
                    continue
                domain_kept += 1
            kept.append(row)
        selected = kept
    elif len(domain_files) > TARGET_FILES:
        overflow = False  # still under hard limit; telemetry records over-target
        # Do not silently drop — return over_target instead.
    missing = [s["path"] for s in selected if not s["exists"]]
    tokens = sum(int(s["estimated_tokens"]) for s in selected)
    return {
        "files": selected,
        "files_loaded": len(selected),
        "domain_skill_or_reference_files": len([s for s in selected if s["class"] in {"skill", "reference"}]),
        "estimated_tokens": tokens,
        "target": TARGET_FILES,
        "hard_limit": HARD_LIMIT,
        "overflow": overflow or (len([s for s in selected if s["class"] in {"skill", "reference"}]) > HARD_LIMIT),
        "over_target": len([s for s in selected if s["class"] in {"skill", "reference"}]) > TARGET_FILES,
        "missing_paths": missing,
        "failure_classes": classify_failures(normalized),
        "distractors_excluded": DISTRACTORS,
    }
