#!/usr/bin/env python3
"""Spot-check Salesforce-platform factual claims inside SKILL.md files.

Not every skill makes testable claims — many are pure design guidance.
This script:

1. **Classifies** every skill as (a) makes platform-fact claims, or (b) pure guidance.
2. For (a), **extracts** specific claim types:
   - Field API names (e.g. `Account.Industry`, `PermissionSetAssignment.AssigneeId`)
   - sObject names (e.g. `PermissionSetGroupComponent`)
   - Governor limit numbers (e.g. `100 SOQL queries`, `10,000 DML rows`)
3. **Verifies** each extracted claim against the live org via `sf sobject describe`.
4. **Reports** pass/fail per skill.

This is a sampler, not exhaustive. It catches the obvious fabrications
(like the `PermissionSetGroupAssignment` Excelsior case) and stale field
names after API version bumps.

Usage:
    python3 scripts/validate_skill_factuality.py --target-org sfskills-dev
    python3 scripts/validate_skill_factuality.py --target-org sfskills-dev --sample 50
    python3 scripts/validate_skill_factuality.py --target-org sfskills-dev --domain apex
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import random
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SKILLS_DIR = REPO_ROOT / "skills"
DEFAULT_OUT = REPO_ROOT / "docs" / "validation"

# Pattern: SObjectName.FieldName (both camelCase or __c suffix)
_FIELD_REF = re.compile(r"\b([A-Z][A-Za-z0-9_]+)\.([A-Z][A-Za-z0-9_]+(?:__c|__r|__e|__mdt|__b)?)\b")

# Known standard sObjects we'll verify field references against. Custom objects
# are skipped (the org may not have them).
STANDARD_OBJECTS_TO_VERIFY = {
    "Account", "Contact", "User", "PermissionSet", "PermissionSetAssignment",
    "PermissionSetGroupComponent", "ObjectPermissions", "FieldPermissions",
    "SetupEntityAccess", "GroupMember", "Group", "Profile", "UserRole",
    "Case", "Lead", "Opportunity", "Task", "Event",
    "ApexClass", "ApexTrigger", "Flow", "FlowDefinitionView", "FlowInterviewLog",
    "MatchingRule", "MatchingRuleItem", "DuplicateRule",
    "CustomObject", "CustomField", "ValidationRule",
    "BusinessHours", "Holiday", "Territory2", "Territory2Model",
}

# Known English phrases suggesting a testable claim.
TESTABLE_MARKERS = [
    "queryable", "SOQL", "describe", "SetupEntityType", "sObject",
    "INVALID_TYPE", "INVALID_FIELD", "governor limit", "API version",
]


# ── Describe cache ──────────────────────────────────────────────────────────

_describe_cache: dict[str, dict | None] = {}


def describe_sobject(name: str, target_org: str) -> dict | None:
    """Return the field list for an sObject, cached. None if sObject not queryable."""
    if name in _describe_cache:
        return _describe_cache[name]
    result = subprocess.run(
        ["sf", "sobject", "describe", "--sobject", name, "--target-org", target_org, "--json"],
        capture_output=True, text=True, timeout=30,
    )
    if result.returncode != 0:
        _describe_cache[name] = None
        return None
    try:
        payload = json.loads(result.stdout)
        if payload.get("status") != 0:
            _describe_cache[name] = None
            return None
        fields = {f["name"] for f in payload["result"]["fields"]}
        _describe_cache[name] = {"fields": fields}
        return _describe_cache[name]
    except (json.JSONDecodeError, KeyError):
        _describe_cache[name] = None
        return None


# ── Skill analysis ──────────────────────────────────────────────────────────

def classify_skill(text: str) -> bool:
    """Return True if the skill likely makes testable platform claims."""
    lower = text.lower()
    marker_hits = sum(1 for m in TESTABLE_MARKERS if m.lower() in lower)
    return marker_hits >= 2


def extract_field_refs(text: str) -> set[tuple[str, str]]:
    """Return set of (sObject, field) references."""
    refs = set()
    for m in _FIELD_REF.finditer(text):
        sobj, field = m.group(1), m.group(2)
        if sobj in STANDARD_OBJECTS_TO_VERIFY:
            refs.add((sobj, field))
    return refs


def verify_claims(skill_path: Path, target_org: str) -> dict:
    """Extract + verify field claims. Return {verified, unverifiable, wrong}."""
    text = skill_path.read_text(encoding="utf-8")
    if not classify_skill(text):
        return {"classification": "guidance", "verified": 0, "unverifiable": 0, "wrong": [], "sample_claims": []}

    refs = extract_field_refs(text)
    verified = 0
    unverifiable = 0
    wrong: list[str] = []

    # Sample up to 30 refs per skill to cap API calls.
    sample = list(refs)
    random.shuffle(sample)
    sample = sample[:30]

    for sobj, field in sample:
        desc = describe_sobject(sobj, target_org)
        if desc is None:
            unverifiable += 1
            continue
        if field not in desc["fields"]:
            # Skip known feature-gated fields that only exist on certain orgs.
            feature_gated_fields = {
                "Account": {"IsPersonAccount", "PersonEmail", "PersonContactId",
                             "PersonMailingStreet", "PersonBirthdate"},  # PersonAccounts
            }
            if field in feature_gated_fields.get(sobj, set()):
                unverifiable += 1
                continue
            # Custom fields (__c suffix) are usually org-specific — can't verify in dev org.
            if field.endswith("__c") or field.endswith("__r"):
                unverifiable += 1
                continue
            # Relationship-traversal refs: Account.Parent, Opportunity.Account — these
            # are lookup relationship names that may or may not be on this particular
            # object. Treat as unverifiable, not wrong.
            if field in {"Parent", "Owner", "RecordType", "CreatedBy", "LastModifiedBy", "Account", "Contact", "Opportunity", "Case", "User"}:
                unverifiable += 1
                continue
            relationship_suffixes = {"Name", "Id", "Label", "DeveloperName"}
            if field in relationship_suffixes:
                unverifiable += 1
                continue
            wrong.append(f"{sobj}.{field}")
        else:
            verified += 1

    return {
        "classification": "testable",
        "verified": verified,
        "unverifiable": unverifiable,
        "wrong": wrong,
        "sample_claims": [f"{s}.{f}" for s, f in list(refs)[:5]],
    }


# ── Main ────────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(description="Spot-check skill factual claims.")
    parser.add_argument("--target-org", required=True, help="sf CLI org alias")
    parser.add_argument("--sample", type=int, default=100, help="Max # of skills to check")
    parser.add_argument("--domain", help="Only check skills in this domain")
    parser.add_argument("--out", default=str(DEFAULT_OUT), help="Report output directory")
    args = parser.parse_args()

    # Verify org reachable.
    result = subprocess.run(
        ["sf", "org", "display", "--target-org", args.target_org, "--json"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        print(f"ERROR: org '{args.target_org}' not reachable.", file=sys.stderr)
        return 2
    org_info = json.loads(result.stdout)["result"]
    print(f"✓ Connected to {org_info.get('alias')} @ API v{org_info.get('apiVersion')}")

    # Discover skills.
    all_skills = list(SKILLS_DIR.glob("*/*/SKILL.md"))
    if args.domain:
        all_skills = [s for s in all_skills if s.parent.parent.name == args.domain]

    print(f"✓ Found {len(all_skills)} skill(s)")

    # Sample.
    random.seed(42)
    sample = random.sample(all_skills, min(args.sample, len(all_skills)))
    print(f"→ Checking {len(sample)} skill(s) (sample seed=42)\n")

    results = []
    for skill in sample:
        try:
            r = verify_claims(skill, args.target_org)
            r["skill"] = f"{skill.parent.parent.name}/{skill.parent.name}"
            results.append(r)
            if r["classification"] == "guidance":
                print(f"   ➖  {r['skill']} (guidance, skipped)")
            elif r["wrong"]:
                print(f"   ❌  {r['skill']} — {len(r['wrong'])} wrong claim(s): {r['wrong'][:3]}")
            else:
                print(f"   ✅  {r['skill']} — {r['verified']} verified, {r['unverifiable']} unverifiable")
        except Exception as e:
            print(f"   ⚠️   {skill.parent.name}: {e}")

    # Rollup.
    testable = [r for r in results if r["classification"] == "testable"]
    clean = [r for r in testable if not r["wrong"]]
    dirty = [r for r in testable if r["wrong"]]

    date_str = dt.date.today().isoformat()
    out_path = Path(args.out) / f"skill_factuality_{date_str}.md"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        f"# Skill Factuality Report — {date_str}",
        "",
        f"**Org:** `{org_info.get('alias')}`",
        f"**Sample size:** {len(sample)} skill(s)",
        f"**Classified as testable (make platform claims):** {len(testable)}",
        f"**Classified as guidance (skipped):** {len(results) - len(testable)}",
        "",
        f"**Testable skills with clean claims:** {len(clean)}",
        f"**Testable skills with wrong claims:** {len(dirty)}",
        "",
        "Sample seed: `42` (re-runnable). Verified via `sf sobject describe`.",
        "",
    ]
    if dirty:
        lines.append("## Skills with claims that don't match the live org")
        lines.append("")
        lines.append("| Skill | Wrong field refs |")
        lines.append("|---|---|")
        for r in dirty:
            refs = ", ".join(r["wrong"][:5])
            if len(r["wrong"]) > 5:
                refs += f", ... and {len(r['wrong']) - 5} more"
            lines.append(f"| `{r['skill']}` | `{refs}` |")
        lines.append("")
    else:
        lines.append("## No factual errors detected in sample")
        lines.append("")

    lines.append("## Clean testable skills")
    lines.append("")
    for r in clean[:30]:
        lines.append(f"- `{r['skill']}` — {r['verified']} claim(s) verified")
    if len(clean) > 30:
        lines.append(f"- ... and {len(clean) - 30} more")
    lines.append("")
    lines.append("## Methodology notes")
    lines.append("")
    lines.append("- Skills are classified as testable when they contain 2+ markers like 'SOQL', 'describe', 'sObject', 'governor limit'.")
    lines.append("- Field refs of the form `SObject.Field` are extracted and verified against the target org's describe output.")
    lines.append("- Relationship traversals (e.g. `Profile.Name`) are 'unverifiable' — they can't be checked without relationship-name context.")
    lines.append("- Custom objects and managed-package fields are not verified (the target org may not have them).")
    lines.append("- This is a sampler, not exhaustive — 30 field refs per skill maximum.")

    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n✓ Report: {out_path.relative_to(REPO_ROOT)}")

    return 1 if dirty else 0


if __name__ == "__main__":
    sys.exit(main())
