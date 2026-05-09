#!/usr/bin/env python3
"""Checker for Agentforce Production Readiness Checklist.

Scans an SFDX-style metadata directory for the smoke-level signals that an
Agentforce agent's metadata package is plausibly ready to gate. The checker
does not replace the human readiness review — it surfaces the structural
omissions that almost always indicate the team has not yet completed the
review. Stdlib only.

What it inspects (best-effort, version-tolerant):
- Agent definition files (look under common Agentforce metadata folders for
  files referencing the agent / Bot / GenAi* surface) and verify that at
  least one references a Named Credential.
- Apex action classes (.cls + .cls-meta.xml) for `@InvocableMethod`
  declarations: confirm each has a non-trivial `description`.
- Prompt template metadata files: confirm each has non-empty test-data
  references (a clear indicator the team has at least staged a test rather
  than shipping an empty template).

Usage:
    python3 check_agentforce_production_readiness_checklist.py
    python3 check_agentforce_production_readiness_checklist.py --manifest-dir path/to/metadata
    python3 check_agentforce_production_readiness_checklist.py --json

Exit codes:
    0 — no issues
    1 — issues found
    2 — invocation error (e.g. manifest dir missing)
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

# ---------------------------------------------------------------------------
# Tunables
# ---------------------------------------------------------------------------

# Minimum length for an action @InvocableMethod description. Anything shorter
# is a default-templated stub that won't help the LLM disambiguate actions.
MIN_ACTION_DESCRIPTION_LEN = 30

# Folder roots typically used by Agentforce metadata. The checker scans
# candidates in order and stops at the first that exists; alternatively
# scans the entire tree if none of the canonical roots exist.
AGENT_METADATA_HINTS = (
    "bots",
    "genAiPlanners",
    "genAiPlanner",
    "genAiPlugins",
    "genAiPlugin",
    "genAiFunctions",
    "genAiFunction",
    "agents",
)

PROMPT_TEMPLATE_HINTS = (
    "promptTemplates",
    "prompt_templates",
    "genAiPromptTemplates",
)


# ---------------------------------------------------------------------------
# Result aggregation
# ---------------------------------------------------------------------------


@dataclass
class CheckResult:
    issues: list[str] = field(default_factory=list)
    info: list[str] = field(default_factory=list)

    def add_issue(self, msg: str) -> None:
        self.issues.append(msg)

    def add_info(self, msg: str) -> None:
        self.info.append(msg)


# ---------------------------------------------------------------------------
# Filesystem walking
# ---------------------------------------------------------------------------


def find_force_app_root(manifest_dir: Path) -> Path:
    """Return the most useful root to scan from.

    Prefers `force-app/main/default` if present, falls back to the supplied
    manifest_dir.
    """
    candidates = [
        manifest_dir / "force-app" / "main" / "default",
        manifest_dir / "main" / "default",
        manifest_dir,
    ]
    for c in candidates:
        if c.exists():
            return c
    return manifest_dir


def find_apex_classes(root: Path) -> list[Path]:
    classes_dir = root / "classes"
    if classes_dir.exists():
        return sorted(classes_dir.glob("*.cls"))
    # Fallback: scan recursively
    return sorted(root.rglob("*.cls"))


def find_agent_metadata_files(root: Path) -> list[Path]:
    found: list[Path] = []
    for hint in AGENT_METADATA_HINTS:
        d = root / hint
        if d.exists():
            found.extend(p for p in d.rglob("*") if p.is_file())
    return sorted(found)


def find_prompt_template_files(root: Path) -> list[Path]:
    found: list[Path] = []
    for hint in PROMPT_TEMPLATE_HINTS:
        d = root / hint
        if d.exists():
            found.extend(p for p in d.rglob("*") if p.is_file())
    return sorted(found)


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------


_NAMED_CRED_PATTERNS = (
    re.compile(r"<namedCredential>", re.IGNORECASE),
    re.compile(r"namedCredential\s*=", re.IGNORECASE),
    re.compile(r"callout:[A-Za-z0-9_]+"),
)


def check_agent_uses_named_credential(
    agent_files: Iterable[Path], result: CheckResult
) -> None:
    if not agent_files:
        result.add_issue(
            "No Agentforce agent metadata found under common metadata hints "
            f"({', '.join(AGENT_METADATA_HINTS)}). Either the manifest does "
            "not contain an agent or the metadata layout is non-standard."
        )
        return

    found_any = False
    for path in agent_files:
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if any(p.search(text) for p in _NAMED_CRED_PATTERNS):
            found_any = True
            result.add_info(
                f"Named credential reference found in agent metadata: {path.name}"
            )
    if not found_any:
        result.add_issue(
            "No named credential reference found in any agent metadata file. "
            "If the agent's actions call external systems via Apex, confirm "
            "the named credential is referenced and scoped least-privilege "
            "for the production environment."
        )


_INVOCABLE_BLOCK = re.compile(
    r"@InvocableMethod\s*\(([^)]*)\)",
    re.IGNORECASE | re.DOTALL,
)


def _extract_attribute(block: str, key: str) -> str | None:
    m = re.search(rf"{key}\s*=\s*'([^']*)'", block, re.IGNORECASE)
    if not m:
        m = re.search(rf'{key}\s*=\s*"([^"]*)"', block, re.IGNORECASE)
    if not m:
        return None
    return m.group(1)


def check_action_descriptions(
    apex_files: Iterable[Path], result: CheckResult
) -> None:
    seen_any = False
    for path in apex_files:
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for match in _INVOCABLE_BLOCK.finditer(text):
            seen_any = True
            block = match.group(1)
            label = _extract_attribute(block, "label") or "(no label)"
            desc = _extract_attribute(block, "description")
            if not desc:
                result.add_issue(
                    f"InvocableMethod in {path.name} (label={label!r}) has "
                    "no description. The agent uses the description to "
                    "select the action; missing descriptions cause routing "
                    "ambiguity in production."
                )
                continue
            if len(desc.strip()) < MIN_ACTION_DESCRIPTION_LEN:
                result.add_issue(
                    f"InvocableMethod in {path.name} (label={label!r}) has "
                    f"a description shorter than {MIN_ACTION_DESCRIPTION_LEN} "
                    f"characters: {desc!r}. Tighten to a clear scope phrase "
                    "the LLM can disambiguate against other actions."
                )
    if not seen_any:
        result.add_info(
            "No @InvocableMethod declarations found in scanned Apex classes. "
            "If the agent uses Apex actions, confirm the manifest includes "
            "the action classes."
        )


def check_prompt_template_test_data(
    template_files: Iterable[Path], result: CheckResult
) -> None:
    files = list(template_files)
    if not files:
        result.add_info(
            "No prompt template metadata found under common hints "
            f"({', '.join(PROMPT_TEMPLATE_HINTS)}). Skipping test-data check."
        )
        return

    # Group by template basename (e.g. MyTemplate.promptTemplate-meta.xml +
    # MyTemplate.promptTemplate). Inspect each grouping for any reference to
    # test data: a non-empty <testData>, <testInputs>, or a sibling
    # *.testData.json / *.test.json file.
    by_stem: dict[str, list[Path]] = {}
    for path in files:
        stem = path.name.split(".")[0]
        by_stem.setdefault(stem, []).append(path)

    for stem, paths in sorted(by_stem.items()):
        has_test_data = False
        for p in paths:
            try:
                text = p.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            if re.search(r"<testData>([^<]+)</testData>", text):
                has_test_data = True
                break
            if re.search(r"<testInput[s]?>", text, re.IGNORECASE) and re.search(
                r"</testInput[s]?>", text, re.IGNORECASE
            ):
                # crude non-empty check: any character between the tags
                if re.search(
                    r"<testInput[s]?>[\s\S]*?\S[\s\S]*?</testInput[s]?>",
                    text,
                    re.IGNORECASE,
                ):
                    has_test_data = True
                    break
            # Sibling test data file
            sibling_candidates = [
                p.with_suffix(".testData.json"),
                p.with_suffix(".test.json"),
            ]
            if any(s.exists() and s.stat().st_size > 0 for s in sibling_candidates):
                has_test_data = True
                break
        if not has_test_data:
            result.add_issue(
                f"Prompt template {stem!r} has no non-empty test data. Add a "
                "test-data entry or a sibling test fixture; an untested prompt "
                "template is a production liability."
            )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "Check an SFDX metadata directory for Agentforce production-"
            "readiness signals: agent uses a named credential, Apex action "
            "@InvocableMethod descriptions are not stubs, prompt templates "
            "have non-empty test data."
        ),
    )
    p.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current dir).",
    )
    p.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of human-readable lines.",
    )
    return p.parse_args(argv)


def run_checks(manifest_dir: Path) -> CheckResult:
    result = CheckResult()
    if not manifest_dir.exists():
        result.add_issue(f"Manifest directory not found: {manifest_dir}")
        return result

    root = find_force_app_root(manifest_dir)
    agent_files = find_agent_metadata_files(root)
    apex_files = find_apex_classes(root)
    template_files = find_prompt_template_files(root)

    check_agent_uses_named_credential(agent_files, result)
    check_action_descriptions(apex_files, result)
    check_prompt_template_test_data(template_files, result)
    return result


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    manifest_dir = Path(args.manifest_dir).resolve()
    result = run_checks(manifest_dir)

    if args.json:
        payload = {
            "manifest_dir": str(manifest_dir),
            "issues": result.issues,
            "info": result.info,
        }
        print(json.dumps(payload, indent=2))
    else:
        for note in result.info:
            print(f"INFO: {note}")
        for issue in result.issues:
            print(f"WARN: {issue}", file=sys.stderr)
        if not result.issues:
            print("No production-readiness issues detected.")

    if not manifest_dir.exists():
        return 2
    return 1 if result.issues else 0


if __name__ == "__main__":
    sys.exit(main())
