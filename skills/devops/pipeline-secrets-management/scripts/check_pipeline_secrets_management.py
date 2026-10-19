#!/usr/bin/env python3
"""Checker for the pipeline-secrets-management skill.

Scans a repository (or any directory) for Salesforce credential material and for
CI steps that would print it. Matched values are never printed — only the file,
line number, and rule.

ERROR (exit 1):
  - an SFDX authorization URL (force://<...>@<host>)
  - a PEM private key block (BEGIN ... PRIVATE KEY)
  - an external client app global OAuth settings file (*.ecaGlblOauth*), which the
    Metadata API guide says must not be added to source control
  - a <consumerSecret> element in connected app metadata
WARN (exit 0 unless --strict):
  - a CI/script file that runs `sf org auth show-...` or sets SF_TEMP_SHOW_SECRETS
  - `set -x` in a CI/script file that also handles a JWT key file
  - connected app metadata with isAdminApproved false or missing

Skips .git, node_modules, and binary files. Stdlib only.

Usage:
    python3 check_pipeline_secrets_management.py --manifest-dir .
    python3 check_pipeline_secrets_management.py --manifest-dir . --strict
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

AUTH_URL_RE = re.compile(r"force://[^\s\"'<>]+@[^\s\"'<>]+")
PEM_RE = re.compile(r"-----BEGIN (?:RSA |EC |ENCRYPTED |OPENSSH )?PRIVATE KEY-----")
SHOW_RE = re.compile(r"\b(?:sf|sfdx)\s+org\s+auth\s+show-[a-z-]+|SF_TEMP_SHOW_SECRETS\s*[:=]\s*['\"]?true", re.I)
SETX_RE = re.compile(r"^\s*set\s+-[a-wyz]*x", re.M)
JWT_RE = re.compile(r"--jwt-key-file|org\s+login\s+jwt", re.I)
SECRET_EL_RE = re.compile(r"<consumerSecret>\s*[^<\s]")
ADMIN_RE = re.compile(r"<isAdminApproved>\s*true\s*</isAdminApproved>", re.I)
CI_SUFFIXES = {".yml", ".yaml", ".sh", ".bash", ".ps1", ".groovy", ".cfg"}
CI_NAMES = {"Jenkinsfile", "Makefile", "bitbucket-pipelines.yml", ".gitlab-ci.yml"}
SKIP_DIRS = {".git", "node_modules"}


def _files(root: Path):
    for p in root.rglob("*"):
        if p.is_file() and not (SKIP_DIRS & set(p.relative_to(root).parts)):
            yield p


def _text(p: Path) -> str | None:
    try:
        data = p.read_bytes()
    except OSError:
        return None
    if b"\x00" in data[:4096]:
        return None
    return data.decode("utf-8", errors="ignore")


def _line(text: str, pos: int) -> int:
    return text.count("\n", 0, pos) + 1


def scan(root: Path, out: list[tuple[str, str]]) -> int:
    n = 0
    for p in _files(root):
        rel = p.relative_to(root)
        if ".ecaGlblOauth" in p.name:
            out.append(("ERROR", f"{rel}: external client app global OAuth settings file; must not be in source control"))
        text = _text(p)
        if text is None:
            continue
        n += 1
        m = AUTH_URL_RE.search(text)
        if m:
            out.append(("ERROR", f"{rel}:{_line(text, m.start())}: SFDX authorization URL (value not shown)"))
        m = PEM_RE.search(text)
        if m:
            out.append(("ERROR", f"{rel}:{_line(text, m.start())}: PEM private key block (value not shown)"))
        if p.name.endswith(".connectedApp-meta.xml") or p.name.endswith(".connectedApp"):
            m = SECRET_EL_RE.search(text)
            if m:
                out.append(("ERROR", f"{rel}:{_line(text, m.start())}: <consumerSecret> in connected app metadata (value not shown)"))
            if "<oauthConfig>" in text and not ADMIN_RE.search(text):
                out.append(("WARN", f"{rel}: isAdminApproved is not true; anyone in the org can authorize this app"))
        is_ci = p.suffix in CI_SUFFIXES or p.name in CI_NAMES or ".github" in rel.parts
        if is_ci:
            m = SHOW_RE.search(text)
            if m:
                out.append(("WARN", f"{rel}:{_line(text, m.start())}: CI step prints credentials (org auth show-* / SF_TEMP_SHOW_SECRETS)"))
            if JWT_RE.search(text):
                m = SETX_RE.search(text)
                if m:
                    out.append(("WARN", f"{rel}:{_line(text, m.start())}: set -x in a file that handles a JWT key"))
    return n


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Scan a repository for Salesforce CI credential leaks.")
    parser.add_argument("--manifest-dir", required=True, type=Path, help="Repository or directory to scan.")
    parser.add_argument("--strict", action="store_true", help="Exit 1 on WARN as well as ERROR.")
    args = parser.parse_args(argv)

    root = args.manifest_dir
    if not root.is_dir():
        print(f"ERROR: manifest directory not found: {root}")
        sys.exit(1)
    out: list[tuple[str, str]] = []
    scanned = scan(root, out)
    if not scanned and not out:
        print(f"WARN: no text files under {root}; nothing to scan")
        return 0
    for level, msg in out:
        print(f"{level}: {msg}")
    errors = sum(1 for lvl, _ in out if lvl == "ERROR")
    warns = len(out) - errors
    print(f"Scanned {scanned} file(s): {errors} error(s), {warns} warning(s).")
    return 1 if errors or (args.strict and warns) else 0


if __name__ == "__main__":
    sys.exit(main())
