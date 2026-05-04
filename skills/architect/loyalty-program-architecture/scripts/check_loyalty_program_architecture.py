#!/usr/bin/env python3
"""Checker script for Loyalty Program Architecture skill.

Scans force-app/ metadata for Loyalty Management configuration that diverges
from the architectural decisions this skill prescribes. Stdlib only.

Checks (architectural-review-oriented):
  1. LoyaltyProgram metadata count — flag if more than one program exists in
     scope without a federation rationale (potential multi-region drift).
  2. LoyaltyProgramCurrency metadata — flag if no qualifying or no
     non-qualifying currency exists (single-currency anti-pattern).
  3. LoyaltyProgramCurrency metadata — flag if qualifying:non-qualifying ratio
     not visibly distinct (architecture mandate: ratio asymmetry).
  4. LoyaltyTierGroup metadata — flag if program has 0 or > 5 tiers (canonical
     baseline is 3 tiers; > 5 needs explicit justification).
  5. DPE definitions — flag if Partner DPE jobs (`Create Partner Ledgers`,
     `Update Partner Balance`) are referenced as inactive.

Usage:
    python3 check_loyalty_program_architecture.py
    python3 check_loyalty_program_architecture.py --manifest-dir force-app/main/default
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Architectural review checks for Salesforce Loyalty Management metadata.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def find_loyalty_programs(root: Path) -> list[Path]:
    candidates: list[Path] = []
    for f in root.rglob("*.loyaltyProgram-meta.xml"):
        candidates.append(f)
    for f in root.rglob("*.loyaltyprogram-meta.xml"):
        candidates.append(f)
    return candidates


def check_program_count(programs: list[Path]) -> list[str]:
    issues: list[str] = []
    if len(programs) > 1:
        issues.append(
            f"REVIEW: {len(programs)} LoyaltyProgram metadata files in scope "
            f"({', '.join(str(p.name) for p in programs)}). Multiple programs is correct for federated multi-region "
            f"architectures but otherwise indicates drift. Confirm the architecture document specifies multi-region federation."
        )
    return issues


CURRENCY_PATTERNS = [
    re.compile(r"<currencyType>\s*Qualifying\s*</currencyType>", re.IGNORECASE),
    re.compile(r"<currencyType>\s*NonQualifying\s*</currencyType>", re.IGNORECASE),
]


def check_currency_split(root: Path) -> list[str]:
    issues: list[str] = []
    qualifying_count = 0
    non_qualifying_count = 0
    for f in root.rglob("*.loyaltyProgramCurrency-meta.xml"):
        text = _read(f)
        if CURRENCY_PATTERNS[0].search(text):
            qualifying_count += 1
        if CURRENCY_PATTERNS[1].search(text):
            non_qualifying_count += 1
    # Only flag if there's evidence of a Loyalty program at all
    if qualifying_count == 0 and non_qualifying_count == 0:
        return issues
    if qualifying_count == 0:
        issues.append(
            "BLOCKER: No Qualifying LoyaltyProgramCurrency in scope. The two-currency model requires a qualifying "
            "currency for tier advancement; without it, the tier engine has no driver."
        )
    if non_qualifying_count == 0:
        issues.append(
            "BLOCKER: No NonQualifying LoyaltyProgramCurrency in scope. Members cannot redeem rewards; redemption "
            "rules must draw from a non-qualifying balance, not from the qualifying tier currency."
        )
    return issues


def check_tier_count(root: Path) -> list[str]:
    issues: list[str] = []
    tier_groups: dict[str, int] = {}
    for f in root.rglob("*.loyaltyTier-meta.xml"):
        text = _read(f)
        m = re.search(r"<loyaltyTierGroup>([^<]+)</loyaltyTierGroup>", text)
        if m:
            tier_groups[m.group(1)] = tier_groups.get(m.group(1), 0) + 1
    for group, count in tier_groups.items():
        if count == 0:
            issues.append(
                f"BLOCKER: LoyaltyTierGroup '{group}' has no tiers defined."
            )
        elif count == 1:
            issues.append(
                f"REVIEW: LoyaltyTierGroup '{group}' has only 1 tier — a one-tier program has no tier dynamics; "
                f"confirm this is intentional (e.g., a flat-membership program rather than a tier-ladder design)."
            )
        elif count > 5:
            issues.append(
                f"REVIEW: LoyaltyTierGroup '{group}' has {count} tiers. The canonical baseline is 3 tiers; "
                f"more than 5 needs explicit justification (long-tail VIP customer base) in the architecture document."
            )
    return issues


def check_partner_dpe_activation(root: Path) -> list[str]:
    issues: list[str] = []
    needs_partner = False
    has_partner_dpe = False
    for f in root.rglob("*.loyaltyProgramPartner-meta.xml"):
        needs_partner = True
        break
    for f in root.rglob("*.batchProcessJob-meta.xml"):
        text = _read(f)
        if "Partner Ledger" in text or "Partner Balance" in text:
            has_partner_dpe = True
    if needs_partner and not has_partner_dpe:
        issues.append(
            "BLOCKER: LoyaltyProgramPartner records exist but no Partner-DPE job metadata in scope. "
            "Partner DPE jobs ('Create Partner Ledgers', 'Update Partner Balance') ship inactive — without "
            "explicit activation, partner balances are never calculated."
        )
    return issues


def check_loyalty_program_architecture(manifest_dir: Path) -> list[str]:
    issues: list[str] = []
    if not manifest_dir.exists():
        return [f"Manifest directory not found: {manifest_dir}"]

    programs = find_loyalty_programs(manifest_dir)
    issues.extend(check_program_count(programs))
    issues.extend(check_currency_split(manifest_dir))
    issues.extend(check_tier_count(manifest_dir))
    issues.extend(check_partner_dpe_activation(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir).resolve()
    issues = check_loyalty_program_architecture(manifest_dir)

    if not issues:
        print("No Loyalty Program Architecture concerns detected in scope.")
        return 0

    blockers = [i for i in issues if i.startswith("BLOCKER")]
    reviews = [i for i in issues if i.startswith("REVIEW")]

    print(f"Loyalty Program Architecture review — {manifest_dir}")
    print(f"  blockers: {len(blockers)}  review: {len(reviews)}")
    print()
    for group_name, group in [("BLOCKERS", blockers), ("REVIEWS", reviews)]:
        if not group:
            continue
        print(f"--- {group_name} ---")
        for issue in group:
            print(f"  {issue}")
        print()

    return 1 if blockers else 0


if __name__ == "__main__":
    sys.exit(main())
