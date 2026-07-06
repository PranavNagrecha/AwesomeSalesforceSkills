#!/usr/bin/env python3
"""Checker for an AgentExchange listing plan.

Validates a filled-in listing-plan workbook (see
templates/agentexchange-publishing-template.md) against the documented
publishing rules from the ISVforce Packaging Guide (Checkout), Trailhead's
AgentExchange publishing module, and Salesforce Help — the same rules captured
in references/gotchas.md. Stdlib only, no pip deps.

Usage:
    python3 check_agentexchange_publishing.py --plan path/to/listing-plan.md

The plan is parsed from `**Field:** value` lines (HTML comments are stripped).
Exit code 0 = no issues, 1 = issues found.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

FIELD_RE = re.compile(r"^\*\*(?P<key>[^*]+):\*\*\s*(?P<value>.*)$")
COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)

LISTING_TYPES = {"solution", "consultant"}
PRICING_MODELS = {"free", "freemium", "revenue-share", "annual-fee", "n/a"}
YES = {"yes", "y", "true"}
NO = {"no", "n", "false"}

# Checkout requires the partner company to be based in the US, UK, or an EU
# country (AgentExchange Checkout Overview, ISVforce Packaging Guide).
EU_COUNTRIES = {
    "austria", "belgium", "bulgaria", "croatia", "cyprus", "czech republic",
    "czechia", "denmark", "estonia", "finland", "france", "germany", "greece",
    "hungary", "ireland", "italy", "latvia", "lithuania", "luxembourg",
    "malta", "netherlands", "poland", "portugal", "romania", "slovakia",
    "slovenia", "spain", "sweden",
}
CHECKOUT_ELIGIBLE = EU_COUNTRIES | {
    "united states", "us", "usa", "united states of america",
    "united kingdom", "uk", "great britain",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check an AgentExchange listing plan for documented publishing-rule violations.",
    )
    parser.add_argument(
        "--plan",
        required=True,
        help="Path to a filled-in listing-plan markdown file (templates/agentexchange-publishing-template.md shape).",
    )
    return parser.parse_args()


def parse_plan(text: str) -> dict[str, str]:
    """Extract `**Field:** value` pairs; last occurrence wins; comments stripped."""
    fields: dict[str, str] = {}
    for raw_line in COMMENT_RE.sub("", text).splitlines():
        match = FIELD_RE.match(raw_line.strip())
        if match:
            key = match.group("key").strip().lower()
            fields[key] = match.group("value").strip().lower()
    return fields


def _is_yes(fields: dict[str, str], key: str) -> bool:
    return fields.get(key, "") in YES


def _blank(fields: dict[str, str], key: str) -> bool:
    return fields.get(key, "") == ""


def check_plan(fields: dict[str, str]) -> list[str]:
    issues: list[str] = []

    if not fields:
        return [
            "No '**Field:** value' lines found — is this a filled-in copy of "
            "templates/agentexchange-publishing-template.md?"
        ]

    # --- Listing type and flow shape -------------------------------------
    listing_type = fields.get("listing type", "")
    if listing_type not in LISTING_TYPES:
        issues.append(
            f"'Listing type' is '{listing_type or '(missing)'}' — expected 'solution' "
            f"(5-step builder) or 'consultant' (3-step: Basics, Details, Grow)."
        )

    pricing_model = fields.get("pricing model", "")
    if listing_type == "solution":
        if pricing_model not in PRICING_MODELS or pricing_model == "n/a":
            issues.append(
                f"Solution listing needs a 'Pricing model' of free, freemium, "
                f"revenue-share, or annual-fee (got '{pricing_model or '(missing)'}')."
            )
        if fields.get("distribution", "") not in {"managed package", "managed-package"}:
            issues.append(
                "Solution listing 'Distribution' should be 'managed package' — the Link "
                "Your Solution step connects a managed package."
            )
    elif listing_type == "consultant":
        if pricing_model not in {"", "n/a"}:
            issues.append(
                "Consultant listings have no Set Pricing step — set 'Pricing model' to "
                "'n/a' (3-step flow: Fill in the Basics, Add Details, Grow Your Business)."
            )
        if _is_yes(fields, "checkout enabled"):
            issues.append(
                "Consultant listing has 'Checkout enabled: yes' — Checkout applies to "
                "solutions distributed in a managed package, not services listings."
            )

    # --- Security Review gate ---------------------------------------------
    if listing_type == "solution":
        review = fields.get("security review passed", "")
        status = fields.get("status", "")
        if review not in YES and status in {"in-review", "published"}:
            issues.append(
                f"Status is '{status}' but 'Security review passed' is "
                f"'{review or '(missing)'}' — a packaged solution must pass the Security "
                f"Review and Assessment (AgentExchange ISV Program Track) before it can "
                f"be distributed from a listing."
            )

    # --- Checkout eligibility gates ----------------------------------------
    if _is_yes(fields, "checkout enabled"):
        country = fields.get("company country", "")
        if not country:
            issues.append(
                "Checkout is enabled but 'Company country' is blank — the partner "
                "company must be based in the United States, United Kingdom, or an EU "
                "country."
            )
        elif country not in CHECKOUT_ELIGIBLE:
            issues.append(
                f"Checkout is enabled but 'Company country: {country}' is not in the "
                f"documented eligibility set (United States, United Kingdom, or an EU "
                f"country). Customers may pay from any Stripe-supported country, but the "
                f"partner-location rule still applies."
            )
        if fields.get("distribution", "") not in {"managed package", "managed-package"}:
            issues.append(
                "Checkout is enabled but 'Distribution' is not 'managed package' — "
                "Checkout solutions must be distributed in a managed package."
            )
        if _is_yes(fields, "oem app"):
            issues.append(
                "Checkout is enabled but 'OEM app' is 'yes' — Checkout can't be used "
                "with OEM apps; plan off-platform billing + Channel Order App instead."
            )
        if not _is_yes(fields, "stripe account connected"):
            issues.append(
                "Checkout is enabled but 'Stripe account connected' is not 'yes' — "
                "create a Stripe account and connect it to the listing in the Partner "
                "Console before pricing plans can take payments."
            )

    # --- Hygiene ------------------------------------------------------------
    if _blank(fields, "listing title"):
        issues.append("'Listing title' is blank — Fill in the Basics requires it.")
    if (
        listing_type == "solution"
        and _is_yes(fields, "private offers enabled")
        and fields.get("security review passed", "") not in YES
    ):
        issues.append(
            "'Private offers enabled: yes' on a plan whose 'Security review passed' is "
            "not 'yes' — Private Offers itself only requires AgentExchange Partner "
            "Program enrollment, but distributing the packaged solution the offer sells "
            "is separately gated on the passed Security Review (AgentExchange ISV "
            "Program Track)."
        )

    return issues


def main() -> int:
    args = parse_args()
    plan_path = Path(args.plan)
    if not plan_path.exists():
        print(f"WARN: plan file not found: {plan_path}", file=sys.stderr)
        return 1

    try:
        text = plan_path.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"WARN: could not read {plan_path}: {exc}", file=sys.stderr)
        return 1

    issues = check_plan(parse_plan(text))
    if not issues:
        print("No issues found.")
        return 0
    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
