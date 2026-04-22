#!/usr/bin/env python3
"""Checker script for Composable Commerce Architecture skill.

Scans a composable-commerce repo for common mistakes:
- Frontend code calling SCAPI directly (should go through BFF)
- CDN / cache config applying blanket max-age to authenticated routes
- Checkout components that render raw card inputs (PCI scope risk)

Usage:
    python3 check_composable_commerce_architecture.py [--repo-dir path/to/storefront]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


SCAPI_CLIENT_PAT = re.compile(
    r"(?i)(from\s+['\"]@salesforce/commerce-sdk[^'\"]*['\"]|commerce-sdk-isomorphic)"
)
RAW_CARD_PAT = re.compile(
    r"(?i)(autocomplete\s*=\s*['\"]cc-number['\"]|name\s*=\s*['\"](cardNumber|card_number|cvv|cvc)['\"])"
)
CACHE_ALL_PAT = re.compile(
    r"(?i)(s-maxage|max-age)\s*=\s*\d{4,}"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check composable commerce repo for anti-patterns.")
    parser.add_argument("--repo-dir", default=".", help="Root directory of the storefront repo.")
    return parser.parse_args()


def iter_frontend_files(root: Path):
    for ext in ("*.ts", "*.tsx", "*.js", "*.jsx"):
        for path in root.rglob(ext):
            parts = set(path.parts)
            if "node_modules" in parts or ".next" in parts or "dist" in parts:
                continue
            yield path


def check_direct_scapi(root: Path) -> list[str]:
    issues: list[str] = []
    for path in iter_frontend_files(root):
        parts = set(path.parts)
        is_frontend = any(seg in parts for seg in ("pages", "app", "components", "src", "client"))
        is_bff = any(seg in parts for seg in ("bff", "server", "api", "functions"))
        if is_bff:
            continue
        if not is_frontend:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if SCAPI_CLIENT_PAT.search(text):
            issues.append(
                f"{path.relative_to(root)}: frontend imports SCAPI SDK directly; route through BFF"
            )
    return issues


def check_raw_card_inputs(root: Path) -> list[str]:
    issues: list[str] = []
    for path in iter_frontend_files(root):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if RAW_CARD_PAT.search(text):
            issues.append(
                f"{path.relative_to(root)}: raw card input detected; use hosted payment page or tokenization"
            )
    return issues


def check_blanket_cache(root: Path) -> list[str]:
    issues: list[str] = []
    candidates = []
    for name in ("vercel.json", "netlify.toml", "cloudflare.toml"):
        candidate = root / name
        if candidate.exists():
            candidates.append(candidate)
    for header_file in root.rglob("_headers"):
        candidates.append(header_file)
    for path in candidates:
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if CACHE_ALL_PAT.search(text) and re.search(r"(?i)(/cart|/account|/checkout|/\*)", text):
            issues.append(
                f"{path.relative_to(root)}: long cache max-age on auth-sensitive or catch-all route"
            )
    return issues


def main() -> int:
    args = parse_args()
    repo_dir = Path(args.repo_dir)
    if not repo_dir.exists():
        print(f"ERROR: repo directory not found: {repo_dir}", file=sys.stderr)
        return 1

    issues: list[str] = []
    issues.extend(check_direct_scapi(repo_dir))
    issues.extend(check_raw_card_inputs(repo_dir))
    issues.extend(check_blanket_cache(repo_dir))

    if not issues:
        print("No composable commerce anti-patterns detected.")
        return 0
    for issue in issues:
        print(f"ISSUE: {issue}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
