#!/usr/bin/env python3
"""Checker script for B2C Commerce Store Setup skill.

Validates SFCC-related configuration artifacts for common B2C Commerce store
setup issues. Accepts a directory of exported Business Manager XML or SFRA
cartridge source code and reports actionable issues.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_b2c_commerce_store_setup.py [--help]
    python3 check_b2c_commerce_store_setup.py --manifest-dir path/to/metadata
    python3 check_b2c_commerce_store_setup.py --manifest-dir . --cartridge-path "int_pay:app_storefront_base"
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SFRA_BASE_CARTRIDGE = "app_storefront_base"
PROMOTION_PERFORMANCE_THRESHOLD = 1000
BASKET_LINE_ITEM_HARD_LIMIT = 400
SESSION_SIZE_KB_LIMIT = 10
CUSTOM_OBJECT_REPLICATION_LIMIT = 400_000
SITE_ID_MAX_LEN = 32
SITE_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,32}$")

# Detects B2B Commerce objects referenced in SFCC context
B2B_OBJECT_PATTERN = re.compile(
    r"\b(WebStore|BuyerGroup|CommerceEntitlementPolicy|IsBuyer)\b"
)

# Detects large session writes (serialized JSON objects assigned to session.custom)
SESSION_LARGE_WRITE_PATTERN = re.compile(
    r"session\.custom\.\w+\s*=\s*JSON\.stringify\(.{50,}",
    re.DOTALL,
)

# Detects direct edits targeting app_storefront_base internals
BASE_CARTRIDGE_EDIT_PATH = re.compile(
    r"app_storefront_base[/\\]cartridge[/\\]",
)


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------


def check_cartridge_path(cartridge_path: str) -> list[str]:
    """Validate that app_storefront_base is the rightmost cartridge."""
    issues: list[str] = []
    if not cartridge_path.strip():
        return issues

    cartridges = [c.strip() for c in cartridge_path.split(":") if c.strip()]
    if not cartridges:
        return issues

    if cartridges[-1] != SFRA_BASE_CARTRIDGE:
        issues.append(
            f"CARTRIDGE PATH: '{SFRA_BASE_CARTRIDGE}' must be the rightmost cartridge. "
            f"Found path: '{cartridge_path}'. "
            f"All custom/integration cartridges must be placed to the LEFT of "
            f"'{SFRA_BASE_CARTRIDGE}'."
        )

    # Check if base cartridge appears anywhere except last
    for idx, name in enumerate(cartridges[:-1]):
        if name == SFRA_BASE_CARTRIDGE:
            issues.append(
                f"CARTRIDGE PATH: '{SFRA_BASE_CARTRIDGE}' appears at position {idx + 1} "
                f"(1-indexed) in a {len(cartridges)}-cartridge path. "
                "Cartridges listed after it will never be reached."
            )

    return issues


def check_site_id(site_id: str) -> list[str]:
    """Validate site ID format rules."""
    issues: list[str] = []
    if not site_id:
        return issues

    if len(site_id) > SITE_ID_MAX_LEN:
        issues.append(
            f"SITE ID: '{site_id}' is {len(site_id)} characters — "
            f"exceeds the 32-character maximum."
        )

    if " " in site_id:
        issues.append(
            f"SITE ID: '{site_id}' contains spaces — site IDs must be alphanumeric with "
            "no spaces (hyphens and underscores are permitted)."
        )

    if not SITE_ID_PATTERN.match(site_id):
        issues.append(
            f"SITE ID: '{site_id}' contains characters outside the allowed set "
            "(A-Z, a-z, 0-9, hyphen, underscore)."
        )

    return issues


def check_source_files_for_anti_patterns(manifest_dir: Path) -> list[str]:
    """Scan .isml, .js, and .ds source files for B2C Commerce anti-patterns."""
    issues: list[str] = []

    # Patterns to scan and file extensions to target
    scan_targets = [
        ("**/*.isml", [B2B_OBJECT_PATTERN]),
        ("**/*.js", [B2B_OBJECT_PATTERN, SESSION_LARGE_WRITE_PATTERN]),
        ("**/*.ds", [B2B_OBJECT_PATTERN]),
    ]

    for glob_pattern, patterns in scan_targets:
        for filepath in manifest_dir.glob(glob_pattern):
            try:
                content = filepath.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue

            # Check for B2B objects in SFCC source
            for match in B2B_OBJECT_PATTERN.finditer(content):
                line_num = content[: match.start()].count("\n") + 1
                issues.append(
                    f"B2B OBJECT IN SFCC SOURCE: '{match.group()}' found in "
                    f"{filepath.relative_to(manifest_dir)} line {line_num}. "
                    "B2B Commerce objects (WebStore, BuyerGroup, CommerceEntitlementPolicy) "
                    "do not exist in SFCC — check if the wrong platform is targeted."
                )

            # Check for large session writes
            for match in SESSION_LARGE_WRITE_PATTERN.finditer(content):
                line_num = content[: match.start()].count("\n") + 1
                issues.append(
                    f"LARGE SESSION WRITE: Possible oversized session assignment in "
                    f"{filepath.relative_to(manifest_dir)} line {line_num}. "
                    f"SFCC session is capped at {SESSION_SIZE_KB_LIMIT} KB — "
                    "store only IDs/keys in session, not full objects."
                )

    return issues


def check_base_cartridge_modifications(manifest_dir: Path) -> list[str]:
    """Warn if any files are located inside an app_storefront_base directory."""
    issues: list[str] = []
    for filepath in manifest_dir.rglob("*"):
        if filepath.is_file() and BASE_CARTRIDGE_EDIT_PATH.search(str(filepath)):
            issues.append(
                f"BASE CARTRIDGE MODIFICATION RISK: File found inside "
                f"app_storefront_base at {filepath.relative_to(manifest_dir)}. "
                "Do not modify app_storefront_base directly — override files in a "
                "custom cartridge positioned left of app_storefront_base in the "
                "cartridge path. Direct modifications break SFRA upgrade compatibility."
            )
            # Report first 5 matches max to avoid flooding output
            if len(issues) >= 5:
                issues.append(
                    "BASE CARTRIDGE MODIFICATION RISK: Additional files found in "
                    "app_storefront_base — output truncated. Review the full directory."
                )
                break

    return issues


def check_promotion_xml(manifest_dir: Path) -> list[str]:
    """Count active promotions in exported BM promotion XML files."""
    issues: list[str] = []
    active_count = 0
    promo_files = list(manifest_dir.glob("**/*promotion*.xml")) + list(
        manifest_dir.glob("**/*promotions*.xml")
    )

    for filepath in promo_files:
        try:
            content = filepath.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        # Simple heuristic: count <promotion> or <enabled>true</enabled> tags
        active_count += content.lower().count("<enabled>true</enabled>")

    if active_count >= PROMOTION_PERFORMANCE_THRESHOLD:
        issues.append(
            f"PROMOTION QUOTA: Detected approximately {active_count} active promotions "
            f"in XML exports — at or above the {PROMOTION_PERFORMANCE_THRESHOLD} "
            "performance threshold. Basket and checkout performance will degrade. "
            "Archive or deactivate expired promotions to stay below 800 active."
        )
    elif active_count > 0:
        headroom = PROMOTION_PERFORMANCE_THRESHOLD - active_count
        if headroom < 200:
            issues.append(
                f"PROMOTION QUOTA WARNING: {active_count} active promotions detected "
                f"— only {headroom} below the {PROMOTION_PERFORMANCE_THRESHOLD} "
                "performance threshold. Begin archiving expired promotions proactively."
            )

    return issues


# ---------------------------------------------------------------------------
# Top-level orchestration
# ---------------------------------------------------------------------------


def check_b2c_commerce_store_setup(
    manifest_dir: Path,
    cartridge_path: str = "",
    site_id: str = "",
) -> list[str]:
    """Run all checks and return a consolidated list of issue strings."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    if cartridge_path:
        issues.extend(check_cartridge_path(cartridge_path))

    if site_id:
        issues.extend(check_site_id(site_id))

    issues.extend(check_source_files_for_anti_patterns(manifest_dir))
    issues.extend(check_base_cartridge_modifications(manifest_dir))
    issues.extend(check_promotion_xml(manifest_dir))

    return issues


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check B2C Commerce (SFCC) store setup configuration and source code "
            "for common issues: cartridge path order, B2B object references, "
            "session size risks, base cartridge modifications, and promotion quotas."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of SFCC metadata exports or cartridge source (default: current directory).",
    )
    parser.add_argument(
        "--cartridge-path",
        default="",
        help="Colon-separated cartridge path string to validate (e.g. 'int_pay:app_storefront_base').",
    )
    parser.add_argument(
        "--site-id",
        default="",
        help="Site ID to validate against naming rules (max 32 alphanumeric chars, no spaces).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_b2c_commerce_store_setup(
        manifest_dir=manifest_dir,
        cartridge_path=args.cartridge_path,
        site_id=args.site_id,
    )

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
