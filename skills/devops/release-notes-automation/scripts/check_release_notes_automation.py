#!/usr/bin/env python3
"""Static checker for release-notes-automation pipelines.

Scans CI workflow files (`.github/workflows/*.yml`, `bitbucket-pipelines.yml`,
`.gitlab-ci.yml`) for known smells:

- `git describe`/`git log <range>` without an explicit `fetch-depth: 0`
- Token-shaped literals (long alphanumerics) assigned to env vars containing
  TOKEN/KEY/SECRET (instead of `${{ secrets.* }}`)

Stdlib only.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

GIT_DESCRIBE = re.compile(r"git\s+(describe|log\s+\S+\.\.\S+|tag\b)")
TOKEN_LITERAL = re.compile(
    r"^(?P<indent>\s*)(?P<key>[A-Z][A-Z0-9_]*(?:TOKEN|KEY|SECRET))\s*[:=]\s*"
    r"['\"]?(?P<val>[A-Za-z0-9+/=_-]{20,})['\"]?\s*$",
    re.MULTILINE,
)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Lint release-notes pipeline workflows.")
    p.add_argument("--manifest-dir", default=".", help="Repository root.")
    return p.parse_args()


def workflow_files(root: Path) -> list[Path]:
    candidates: list[Path] = []
    candidates.extend(root.glob(".github/workflows/*.yml"))
    candidates.extend(root.glob(".github/workflows/*.yaml"))
    for name in ("bitbucket-pipelines.yml", ".gitlab-ci.yml"):
        p = root / name
        if p.exists():
            candidates.append(p)
    return candidates


def check_workflow(path: Path) -> list[str]:
    issues: list[str] = []
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        return [f"{path}: cannot read ({exc})"]

    if GIT_DESCRIBE.search(text) and "fetch-depth: 0" not in text:
        issues.append(
            f"{path}: uses git describe/log/tag but no `fetch-depth: 0` in checkout"
        )

    for m in TOKEN_LITERAL.finditer(text):
        val = m.group("val")
        if val.startswith("${{") or val in ("true", "false"):
            continue
        issues.append(
            f"{path}: token-shaped literal in env var {m.group('key')} — use ${{{{ secrets.* }}}}"
        )

    return issues


def main() -> int:
    args = parse_args()
    root = Path(args.manifest_dir)
    if not root.exists():
        print(f"ERROR: manifest dir not found: {root}", file=sys.stderr)
        return 1

    issues: list[str] = []
    for wf in workflow_files(root):
        issues.extend(check_workflow(wf))

    if not issues:
        print("[release-notes-automation] no issues found")
        return 0
    for i in issues:
        print(f"WARN: {i}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
