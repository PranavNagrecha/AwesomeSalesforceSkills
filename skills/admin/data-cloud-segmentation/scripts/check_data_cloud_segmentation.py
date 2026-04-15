#!/usr/bin/env python3
"""Checker script for Data Cloud Segmentation skill.

Validates segment and activation configuration patterns exported as JSON
from the Data Cloud Metadata API or a manual export. Uses stdlib only.

Usage:
    python3 check_data_cloud_segmentation.py [--help]
    python3 check_data_cloud_segmentation.py --manifest-dir path/to/metadata
    python3 check_data_cloud_segmentation.py --segments-json path/to/segments.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Hard platform limits (as of Spring '25)
SEGMENT_ORG_LIMIT = 9950
RAPID_PUBLISH_ORG_LIMIT = 20
RELATED_ATTR_PER_ACTIVATION_LIMIT = 20
ACTIVATIONS_WITH_RELATED_ATTR_LIMIT = 100
POPULATION_RELATED_ATTR_THRESHOLD = 10_000_000  # 10M profiles
RAPID_PUBLISH_LOOKBACK_DAYS = 7


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Data Cloud segment and activation configuration for "
            "common issues and limit violations."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=None,
        help="Root directory of exported Salesforce metadata (looks for *.json files).",
    )
    parser.add_argument(
        "--segments-json",
        default=None,
        help=(
            "Path to a JSON file containing a list of segment objects. "
            "Each object may have: name, refreshType, filterCriteria, "
            "populationCount, activations."
        ),
    )
    return parser.parse_args()


def load_segments(segments_json: Path) -> list[dict]:
    """Load segment records from a JSON file."""
    try:
        with segments_json.open() as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
        if isinstance(data, dict) and "segments" in data:
            return data["segments"]
        return []
    except (json.JSONDecodeError, OSError) as exc:
        return []


def check_rapid_publish_quota(segments: list[dict]) -> list[str]:
    """Warn if Rapid Publish segment count meets or exceeds the org limit."""
    issues: list[str] = []
    rapid = [
        s for s in segments
        if str(s.get("refreshType", "")).lower() in ("rapid_publish", "rapidpublish", "rapid")
    ]
    count = len(rapid)
    if count >= RAPID_PUBLISH_ORG_LIMIT:
        issues.append(
            f"LIMIT: Org has {count} Rapid Publish segments (limit: {RAPID_PUBLISH_ORG_LIMIT}). "
            "Creating additional Rapid Publish segments will fail."
        )
    elif count >= RAPID_PUBLISH_ORG_LIMIT - 3:
        issues.append(
            f"WARN: Org has {count}/{RAPID_PUBLISH_ORG_LIMIT} Rapid Publish segments. "
            "Approaching org limit — review before adding new ones."
        )
    return issues


def check_segment_org_limit(segments: list[dict]) -> list[str]:
    """Warn if total segment count is near or at the org limit."""
    issues: list[str] = []
    count = len(segments)
    if count >= SEGMENT_ORG_LIMIT:
        issues.append(
            f"LIMIT: Org has {count} segments (hard limit: {SEGMENT_ORG_LIMIT}). "
            "No new segments can be created."
        )
    elif count >= SEGMENT_ORG_LIMIT - 200:
        issues.append(
            f"WARN: Org has {count}/{SEGMENT_ORG_LIMIT} segments. "
            "Approaching the org-wide segment limit — implement segment governance."
        )
    return issues


def check_rapid_publish_lookback(segments: list[dict]) -> list[str]:
    """Flag Rapid Publish segments that contain filter criteria with long date ranges."""
    issues: list[str] = []
    rapid = [
        s for s in segments
        if str(s.get("refreshType", "")).lower() in ("rapid_publish", "rapidpublish", "rapid")
    ]
    suspicious_keywords = [
        "last_n_days:8", "last_n_days:9", "last_n_days:10",
        "last_n_days:14", "last_n_days:30", "last_n_days:60",
        "last_n_days:90", "last_n_months", "last_n_years",
    ]
    for seg in rapid:
        criteria = str(seg.get("filterCriteria", "")).lower()
        for kw in suspicious_keywords:
            if kw in criteria:
                issues.append(
                    f"WARN: Segment '{seg.get('name', 'unknown')}' uses Rapid Publish "
                    f"but filter contains '{kw}'. Rapid Publish only evaluates the last "
                    f"{RAPID_PUBLISH_LOOKBACK_DAYS} days of data — contacts outside that "
                    "window will be silently excluded."
                )
                break
    return issues


def check_null_identity_filter(segments: list[dict]) -> list[str]:
    """Flag segments that appear to lack a null-exclusion filter on email or phone."""
    issues: list[str] = []
    null_filter_keywords = [
        "is not null", "isnotnull", "not null", "email != null",
        "email <> null", "email is not",
    ]
    for seg in segments:
        criteria = str(seg.get("filterCriteria", "")).lower()
        # Only check segments that have activations (publishing)
        activations = seg.get("activations", [])
        if not activations:
            continue
        has_null_filter = any(kw in criteria for kw in null_filter_keywords)
        if not has_null_filter and criteria:
            issues.append(
                f"WARN: Segment '{seg.get('name', 'unknown')}' has activations but "
                "no apparent null-exclusion filter on email/phone. Contacts with null "
                "identity fields will be activated by default."
            )
    return issues


def check_related_attribute_limits(segments: list[dict]) -> list[str]:
    """Check activation related attribute counts and population thresholds."""
    issues: list[str] = []
    total_activations_with_attrs = 0

    for seg in segments:
        pop = seg.get("populationCount", 0)
        activations = seg.get("activations", [])
        for act in activations:
            related_attrs = act.get("relatedAttributes", [])
            attr_count = len(related_attrs)

            if attr_count > RELATED_ATTR_PER_ACTIVATION_LIMIT:
                issues.append(
                    f"LIMIT: Activation '{act.get('name', 'unknown')}' on segment "
                    f"'{seg.get('name', 'unknown')}' has {attr_count} related attributes "
                    f"(limit: {RELATED_ATTR_PER_ACTIVATION_LIMIT})."
                )

            if attr_count > 0:
                total_activations_with_attrs += 1
                if pop and pop > POPULATION_RELATED_ATTR_THRESHOLD:
                    issues.append(
                        f"LIMIT: Segment '{seg.get('name', 'unknown')}' has population "
                        f"{pop:,} (> 10M) but activation '{act.get('name', 'unknown')}' "
                        "maps related attributes. Related attributes are not supported for "
                        "segments over 10 million profiles."
                    )

    if total_activations_with_attrs >= ACTIVATIONS_WITH_RELATED_ATTR_LIMIT:
        issues.append(
            f"LIMIT: Org has {total_activations_with_attrs} activations with related "
            f"attributes (limit: {ACTIVATIONS_WITH_RELATED_ATTR_LIMIT})."
        )
    elif total_activations_with_attrs >= ACTIVATIONS_WITH_RELATED_ATTR_LIMIT - 10:
        issues.append(
            f"WARN: Org has {total_activations_with_attrs}/{ACTIVATIONS_WITH_RELATED_ATTR_LIMIT} "
            "activations with related attributes. Approaching the org limit."
        )

    return issues


def check_activation_schedule_alignment(segments: list[dict]) -> list[str]:
    """Flag Rapid Publish segments whose activations still use a daily publish schedule."""
    issues: list[str] = []
    rapid = [
        s for s in segments
        if str(s.get("refreshType", "")).lower() in ("rapid_publish", "rapidpublish", "rapid")
    ]
    daily_keywords = ("daily", "24h", "24 hour", "once_a_day", "once per day")
    for seg in rapid:
        for act in seg.get("activations", []):
            sched = str(act.get("publishSchedule", "")).lower()
            if any(k in sched for k in daily_keywords):
                issues.append(
                    f"WARN: Segment '{seg.get('name', 'unknown')}' uses Rapid Publish "
                    f"but activation '{act.get('name', 'unknown')}' has a daily publish "
                    "schedule. Rapid Publish segment freshness provides no benefit when "
                    "the activation publishes only once per day."
                )
    return issues


def check_manifest_dir(manifest_dir: Path) -> list[str]:
    """Scan a metadata directory for segment-related JSON files and run checks."""
    issues: list[str] = []
    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    json_files = list(manifest_dir.rglob("*.json"))
    if not json_files:
        issues.append(
            f"No JSON files found in {manifest_dir}. "
            "Export segment metadata as JSON and pass via --segments-json."
        )
        return issues

    all_segments: list[dict] = []
    for jf in json_files:
        segs = load_segments(jf)
        all_segments.extend(segs)

    if not all_segments:
        issues.append(
            "No segment records parsed from JSON files. "
            "Ensure exported files contain segment objects with 'name' and 'refreshType' fields."
        )
        return issues

    issues += check_segment_org_limit(all_segments)
    issues += check_rapid_publish_quota(all_segments)
    issues += check_rapid_publish_lookback(all_segments)
    issues += check_null_identity_filter(all_segments)
    issues += check_related_attribute_limits(all_segments)
    issues += check_activation_schedule_alignment(all_segments)
    return issues


def main() -> int:
    args = parse_args()

    all_issues: list[str] = []

    if args.segments_json:
        segments_path = Path(args.segments_json)
        if not segments_path.exists():
            print(f"ERROR: Segments JSON file not found: {segments_path}", file=sys.stderr)
            return 2
        segments = load_segments(segments_path)
        if not segments:
            print(
                f"WARN: No segment records found in {segments_path}. "
                "Check file format (expected list of segment objects).",
                file=sys.stderr,
            )
            return 0
        all_issues += check_segment_org_limit(segments)
        all_issues += check_rapid_publish_quota(segments)
        all_issues += check_rapid_publish_lookback(segments)
        all_issues += check_null_identity_filter(segments)
        all_issues += check_related_attribute_limits(segments)
        all_issues += check_activation_schedule_alignment(segments)

    elif args.manifest_dir:
        all_issues += check_manifest_dir(Path(args.manifest_dir))

    else:
        print(
            "No input specified. Provide --segments-json or --manifest-dir. "
            "Run with --help for usage.",
            file=sys.stderr,
        )
        return 2

    if not all_issues:
        print("No issues found.")
        return 0

    for issue in all_issues:
        print(issue, file=sys.stderr)

    limit_issues = [i for i in all_issues if i.startswith("LIMIT:")]
    return 1 if limit_issues else 0


if __name__ == "__main__":
    sys.exit(main())
