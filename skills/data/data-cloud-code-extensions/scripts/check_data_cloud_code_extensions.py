#!/usr/bin/env python3
"""Checker for Data Cloud (Data 360) Code Extension project scaffolds.

Validates a code extension project directory for the common mistakes documented in
references/gotchas.md and references/llm-anti-patterns.md. Stdlib only — no pip deps.

Usage:
    python3 check_data_cloud_code_extensions.py [--project-dir path]

It looks for the documented scaffold shape (Dockerfile, requirements.txt,
payload/config.json, payload/entrypoint.py) anywhere beneath --project-dir and reports
concrete, actionable issues:
  - missing scaffold files, invalid config.json
  - deployment vs local-venv hygiene (do not ship pytest etc. in requirements.txt)
  - sensitive-looking values written to stdout (everything lands in the broadly
    readable DataCustomCodeLogs__dll Logs DLO)
  - hand-typed CLI subcommands that don't exist in the documented toolchain

Exit code 0 = no issues, 1 = issues found.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REQUIRED_FILES = (
    "Dockerfile",
    "requirements.txt",
    "payload/config.json",
    "payload/entrypoint.py",
)

# Everything printed at runtime lands in the Logs DLO (DataCustomCodeLogs__dll),
# which any user with access to it can read. Flag prints that look sensitive.
SENSITIVE_TOKENS = (
    "password",
    "passwd",
    "secret",
    "token",
    "api_key",
    "apikey",
    "credential",
    "ssn",
    "credit_card",
)
PRINT_RE = re.compile(r"\bprint\s*\(", re.IGNORECASE)

# Fabricated CLI surface frequently produced from memory. The documented toolchain is
# Salesforce CLI 2.130.9+, the Code Extension plugin 0.1.5+, and the
# salesforce-data-customcode SDK.
FABRICATED_CLI_RE = re.compile(
    r"\bsf\s+(datacloud\s+code|data\s+transform\s+deploy|code-extension\s+push)\b",
    re.IGNORECASE,
)

# Dev/test-only packages that must not ship in the deployed container.
DEV_ONLY_PACKAGES = ("pytest", "flake8", "black", "mypy", "ruff", "ipython", "ipdb")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check a Data 360 Code Extension project scaffold for common issues "
            "(missing files, sensitive logging, dependency hygiene)."
        ),
    )
    parser.add_argument(
        "--project-dir",
        default=".",
        help=(
            "Root of the code extension project, or a parent folder — the checker "
            "finds scaffolds by locating payload/entrypoint.py beneath it."
        ),
    )
    return parser.parse_args()


def _find_scaffolds(root: Path) -> list[Path]:
    """A scaffold root is any directory containing payload/entrypoint.py."""
    return sorted({p.parent.parent for p in root.rglob("payload/entrypoint.py")})


def _check_required_files(scaffold: Path, issues: list[str]) -> None:
    for rel in REQUIRED_FILES:
        if not (scaffold / rel).exists():
            issues.append(
                f"{scaffold}: missing required scaffold file '{rel}' — scaffold with "
                f"the Code Extension plugin (0.1.5+) rather than assembling by hand"
            )


def _check_config_json(scaffold: Path, issues: list[str]) -> None:
    config = scaffold / "payload" / "config.json"
    if not config.exists():
        return
    try:
        data = json.loads(config.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        issues.append(f"{config}: not valid JSON ({exc})")
        return
    if not isinstance(data, dict):
        issues.append(f"{config}: expected a JSON object (Data 360 deployment configuration)")


def _check_entrypoint(scaffold: Path, issues: list[str]) -> None:
    entrypoint = scaffold / "payload" / "entrypoint.py"
    if not entrypoint.exists():
        return
    try:
        text = entrypoint.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        issues.append(f"{entrypoint}: unreadable ({exc})")
        return

    stripped = "\n".join(
        line for line in text.splitlines() if line.strip() and not line.strip().startswith("#")
    )
    if not stripped:
        issues.append(f"{entrypoint}: is empty — the batch transform logic belongs here")
        return

    for lineno, line in enumerate(text.splitlines(), start=1):
        if PRINT_RE.search(line):
            lowered = line.lower()
            hits = [t for t in SENSITIVE_TOKENS if t in lowered]
            if hits:
                issues.append(
                    f"{entrypoint}:{lineno}: print() mentions {', '.join(hits)} — stdout "
                    f"lands in the Logs DLO (DataCustomCodeLogs__dll), readable by any "
                    f"user with access to it; never log PII or credentials"
                )
        if FABRICATED_CLI_RE.search(line):
            issues.append(
                f"{entrypoint}:{lineno}: references a CLI subcommand that isn't in the "
                f"documented Code Extension toolchain — verify against the developer guide"
            )


def _read_requirement_names(path: Path) -> list[str]:
    names: list[str] = []
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if not line or line.startswith(("#", "-")):
            continue
        names.append(re.split(r"[=<>!~\[; ]", line, maxsplit=1)[0].lower())
    return names


def _check_requirements(scaffold: Path, issues: list[str]) -> None:
    req = scaffold / "requirements.txt"
    if not req.exists():
        return
    try:
        deploy_names = _read_requirement_names(req)
    except OSError as exc:
        issues.append(f"{req}: unreadable ({exc})")
        return

    for name in deploy_names:
        if name in DEV_ONLY_PACKAGES:
            issues.append(
                f"{req}: '{name}' looks like a dev/test-only package — do not ship it in "
                f"requirements.txt. Leave the scaffold requirements-dev.txt unmodified; "
                f"install extra test tools in the local venv"
            )

    dev_req = scaffold / "requirements-dev.txt"
    if dev_req.exists():
        try:
            dev_names = set(_read_requirement_names(dev_req))
        except OSError:
            dev_names = set()
        dupes = sorted(dev_names.intersection(deploy_names))
        if dupes:
            issues.append(
                f"{scaffold}: {', '.join(dupes)} listed in both requirements.txt and "
                f"requirements-dev.txt — keep each dependency in exactly one file"
            )


def check(project_dir: Path) -> list[str]:
    issues: list[str] = []
    if not project_dir.exists():
        return [f"Project directory not found: {project_dir}"]

    scaffolds = _find_scaffolds(project_dir)
    if not scaffolds:
        return [
            f"No code extension scaffold (payload/entrypoint.py) found under {project_dir} "
            f"— nothing to check."
        ]

    for scaffold in scaffolds:
        _check_required_files(scaffold, issues)
        _check_config_json(scaffold, issues)
        _check_entrypoint(scaffold, issues)
        _check_requirements(scaffold, issues)
    return issues


def main() -> int:
    args = parse_args()
    issues = check(Path(args.project_dir))
    if not issues:
        print("No issues found.")
        return 0
    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
