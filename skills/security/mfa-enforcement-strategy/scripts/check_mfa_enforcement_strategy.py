#!/usr/bin/env python3
"""Checker for MFA enforcement strategy skill package and optional org metadata.

Validates the skill author's package (frontmatter, body length, required files)
and optionally scans retrieved ``Security.settings`` and ``ProfileSessionSetting``
files for MFA-related values that often surprise teams during rollouts. Field names
follow the Metadata API Developer Guide, Summer '26 (SecuritySettings > SessionSettings
and SingleSignOnSettings; ProfileSessionSetting).

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_mfa_enforcement_strategy.py [--help]
    python3 check_mfa_enforcement_strategy.py
    python3 check_mfa_enforcement_strategy.py --skill-dir path/to/mfa-enforcement-strategy
    python3 check_mfa_enforcement_strategy.py --manifest-dir path/to/sfdx/project
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


SKILL_NAME = "mfa-enforcement-strategy"
DOMAIN = "security"
MIN_BODY_WORDS = 300

REQUIRED_REFERENCES = (
    "references/examples.md",
    "references/gotchas.md",
    "references/well-architected.md",
    "references/llm-anti-patterns.md",
)


def _local_tag(tag: str) -> str:
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag


def parse_frontmatter(skill_md: Path) -> tuple[dict[str, str], str]:
    """Return (frontmatter dict, body markdown) from SKILL.md."""
    text = skill_md.read_text(encoding="utf-8")
    if not text.startswith("---"):
        raise ValueError("SKILL.md must start with YAML frontmatter (---)")
    rest = text[3:].lstrip("\n")
    end = rest.find("\n---")
    if end == -1:
        raise ValueError("SKILL.md frontmatter not closed with ---")
    fm_block = rest[:end]
    body = rest[end + 4 :].lstrip("\n")
    fm: dict[str, str] = {}
    for line in fm_block.splitlines():
        m = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if not m:
            continue
        key, raw = m.group(1), m.group(2)
        if raw.startswith('"') and raw.endswith('"'):
            raw = raw[1:-1]
        elif raw.startswith("'") and raw.endswith("'"):
            raw = raw[1:-1]
        fm[key] = raw
    return fm, body


def count_words(text: str) -> int:
    return len(re.findall(r"[A-Za-z0-9'_-]+", text))


def check_skill_package(skill_dir: Path) -> tuple[list[str], list[str]]:
    """Return (errors, warnings) for the skill directory."""
    errors: list[str] = []
    warnings: list[str] = []

    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        errors.append(f"Missing SKILL.md under {skill_dir}")
        return errors, warnings

    try:
        fm, body = parse_frontmatter(skill_md)
    except ValueError as exc:
        errors.append(str(exc))
        return errors, warnings

    if fm.get("name") != SKILL_NAME:
        errors.append(
            f"Frontmatter name must be '{SKILL_NAME}', got {fm.get('name', '')!r}"
        )
    if fm.get("category") != DOMAIN:
        errors.append(
            f"Frontmatter category must be '{DOMAIN}', got {fm.get('category', '')!r}"
        )
    desc = fm.get("description", "")
    if "not for" not in desc.lower():
        errors.append(
            'Frontmatter description must include scope exclusion ("NOT for ...")'
        )

    if count_words(body) < MIN_BODY_WORDS:
        errors.append(
            f"SKILL.md body is under {MIN_BODY_WORDS} words "
            f"(found {count_words(body)}). Expand guidance in the markdown body."
        )

    for rel in REQUIRED_REFERENCES:
        p = skill_dir / rel
        if not p.is_file():
            errors.append(f"Missing required file: {rel}")

    wf = skill_dir / "references" / "well-architected.md"
    if wf.is_file():
        wtxt = wf.read_text(encoding="utf-8")
        if "## Official Sources Used" not in wtxt:
            errors.append("references/well-architected.md missing '## Official Sources Used'")
        else:
            after = wtxt.split("## Official Sources Used", 1)[1]
            bullets = [ln for ln in after.splitlines() if ln.strip().startswith("-")]
            if len(bullets) < 1:
                errors.append(
                    "references/well-architected.md Official Sources Used section has no bullets"
                )

    anti = skill_dir / "references" / "llm-anti-patterns.md"
    if anti.is_file():
        headings = re.findall(r"^## Anti-Pattern \d+:", anti.read_text(encoding="utf-8"), re.M)
        if len(headings) < 5:
            errors.append(
                f"references/llm-anti-patterns.md should document at least 5 anti-patterns "
                f"(found {len(headings)})."
            )

    return errors, warnings


def _child_text(parent: ET.Element, name: str) -> str | None:
    for el in parent:
        if _local_tag(el.tag) == name:
            return (el.text or "").strip()
    return None


def _child(parent: ET.Element, name: str) -> ET.Element | None:
    for el in parent:
        if _local_tag(el.tag) == name:
            return el
    return None


def check_security_settings_metadata(manifest_dir: Path) -> list[str]:
    """Return warning strings for Security.settings and ProfileSessionSetting files.

    Earlier versions of this checker looked for `enableMultiFactorAuthenticationInUi`
    and `mfaRegistrationRequirement`. Neither name appears in the SecuritySettings
    reference; the real fields are listed below.
    """
    warns: list[str] = []
    settings = sorted(p for p in manifest_dir.rglob("Security.settings-meta.xml") if p.is_file())
    profile_sessions = sorted(p for p in manifest_dir.rglob("*.profileSessionSetting-meta.xml") if p.is_file())
    if not settings and not profile_sessions:
        warns.append(f"{manifest_dir}: no Security.settings-meta.xml or ProfileSessionSetting files found; "
                     "retrieve Settings:Security and ProfileSessionSetting first")
        return warns

    for path in settings:
        try:
            root = ET.parse(path).getroot()
        except ET.ParseError as exc:
            warns.append(f"{path}: XML parse error: {exc}")
            continue
        ss = _child(root, "sessionSettings")
        if ss is not None:
            if _child_text(ss, "enableMFADirectUILoginOptIn") == "false":
                warns.append(f"{path}: sessionSettings.enableMFADirectUILoginOptIn is false; direct UI logins "
                             "don't require a verification method org-wide (users with the waiver permission are "
                             "exempt even when it is true, per the Summer '26 guide)")
            if _child_text(ss, "skipSFAWhenMFADirectUILogin") == "false":
                warns.append(f"{path}: sessionSettings.skipSFAWhenMFADirectUILogin is false; the registration "
                             "screen shows only Salesforce Authenticator")
            for field, label in (("enableBuiltInAuthenticator", "built-in authenticators (Touch ID, Windows Hello)"),
                                 ("enableU2F", "U2F-compatible security keys")):
                if _child_text(ss, field) == "false":
                    warns.append(f"{path}: sessionSettings.{field} is false; {label} can't be used, which "
                                 "limits options for privileged users")
        sso = _child(root, "singleSignOnSettings")
        if sso is not None and _child_text(sso, "isLoginWithSalesforceCredentialsDisabled") == "false" \
                and _child_text(sso, "enableSamlLogin") == "true":
            warns.append(f"{path}: SAML SSO is on but Salesforce credentials still work "
                         "(isLoginWithSalesforceCredentialsDisabled=false); SSO-only users keep a password path")

    for path in profile_sessions:
        try:
            root = ET.parse(path).getroot()
        except ET.ParseError as exc:
            warns.append(f"{path}: XML parse error: {exc}")
            continue
        level = _child_text(root, "requiredSessionLevel")
        if level and level != "HIGH_ASSURANCE":
            warns.append(f"{path}: requiredSessionLevel is {level}; MFA sessions are HIGH_ASSURANCE")
    return warns


def parse_args() -> argparse.Namespace:
    default_skill = Path(__file__).resolve().parents[1]
    p = argparse.ArgumentParser(
        description="Validate MFA enforcement strategy skill files and optional Security.settings.",
    )
    p.add_argument(
        "--skill-dir",
        type=Path,
        default=default_skill,
        help="Root of the skill package (default: directory containing this script's parent).",
    )
    p.add_argument(
        "--manifest-dir",
        type=Path,
        default=None,
        help="Optional SFDX/metadata root; Security.settings and ProfileSessionSetting files are found recursively.",
    )
    p.add_argument(
        "--skip-skill",
        action="store_true",
        help="Only run metadata checks (requires --manifest-dir).",
    )
    return p.parse_args()


def main() -> int:
    args = parse_args()
    skill_dir: Path = args.skill_dir
    errors: list[str] = []
    warnings: list[str] = []

    if not args.skip_skill:
        e, w = check_skill_package(skill_dir)
        errors.extend(e)
        warnings.extend(w)

    if args.manifest_dir is not None:
        md = Path(args.manifest_dir)
        if not md.is_dir():
            errors.append(f"--manifest-dir is not a directory: {md}")
        else:
            warnings.extend(check_security_settings_metadata(md))

    for msg in warnings:
        print(f"WARN: {msg}", file=sys.stderr)

    if errors:
        for msg in errors:
            print(f"ERROR: {msg}", file=sys.stderr)
        return 1

    if not args.skip_skill:
        print(f"OK: skill package at {skill_dir} passed structural checks.")
    if args.manifest_dir and not errors:
        print("OK: metadata scan complete (see WARN lines if any).")
    elif args.skip_skill and args.manifest_dir is None:
        print("ERROR: --skip-skill requires --manifest-dir", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
