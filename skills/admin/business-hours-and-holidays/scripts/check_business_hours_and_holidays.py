#!/usr/bin/env python3
"""Checker for Business Hours and Holidays metadata.

Parses ``settings/BusinessHours.settings-meta.xml`` (or ``BusinessHours.settings``
from a retrieved package) and flags the configuration mistakes that make an SLA
clock keep running: no or several default calendars, inactive defaults, holidays
attached to no calendar or to an unknown one, calendars with no weekday window,
calendars stored as midnight-to-midnight on every day (the shipped 24/7 shape),
and one-off holidays already in the past.

Stdlib only.

Usage:
    python3 check_business_hours_and_holidays.py --manifest-dir force-app/main/default
"""

from __future__ import annotations

import argparse
import datetime as dt
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

SF_NS = "http://soap.sforce.com/2006/04/metadata"
DAYS = ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")
MIDNIGHT = "00:00:00.000Z"


def _tag(local: str) -> str:
    return f"{{{SF_NS}}}{local}"


def _find(parent: ET.Element, name: str) -> ET.Element | None:
    """Namespaced-or-bare child lookup. Never use ``a or b`` on Elements: a leaf
    Element is falsy, which silently discards a found node."""
    el = parent.find(_tag(name))
    return el if el is not None else parent.find(name)


def _findall(parent: ET.Element, name: str) -> list[ET.Element]:
    return parent.findall(_tag(name)) or parent.findall(name)


def _text(parent: ET.Element, name: str) -> str | None:
    el = _find(parent, name)
    return el.text.strip() if el is not None and el.text else None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check BusinessHoursSettings metadata for SLA-clock mistakes.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root of the Salesforce project or retrieved metadata (default: current directory).",
    )
    parser.add_argument(
        "--today",
        default=None,
        help="Override today's date (YYYY-MM-DD) for the past-holiday check; used by tests.",
    )
    return parser.parse_args()


def find_settings_files(root: Path) -> list[Path]:
    results = list(root.rglob("BusinessHours.settings-meta.xml"))
    results += [p for p in root.rglob("BusinessHours.settings") if p.is_file()]
    return results


def check_file(path: Path, today: dt.date) -> list[str]:
    issues: list[str] = []
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        return [f"{path.name}: XML parse error — {exc}"]

    calendars = _findall(root, "businessHours")
    holidays = _findall(root, "holidays")
    names: list[str] = []
    defaults: list[str] = []

    for cal in calendars:
        name = _text(cal, "name") or "<unnamed>"
        names.append(name)
        active = (_text(cal, "active") or "false").lower() == "true"
        is_default = (_text(cal, "default") or "false").lower() == "true"
        if is_default:
            defaults.append(name)
            if not active:
                issues.append(f"{path.name} / calendar '{name}': marked default but inactive.")
        if not _text(cal, "timeZoneId"):
            issues.append(f"{path.name} / calendar '{name}': no timeZoneId — windows have no frame.")

        windows = 0
        all_midnight = True
        for day in DAYS:
            start = _text(cal, f"{day}StartTime")
            end = _text(cal, f"{day}EndTime")
            if start or end:
                windows += 1
                if not (start == MIDNIGHT and end == MIDNIGHT):
                    all_midnight = False
                if (start is None) != (end is None):
                    issues.append(
                        f"{path.name} / calendar '{name}': {day} has a start or end time but not both."
                    )
        if windows == 0:
            issues.append(
                f"{path.name} / calendar '{name}': no day has a window — the calendar is never open."
            )
        elif windows == 7 and all_midnight:
            issues.append(
                f"{path.name} / calendar '{name}': every day is 00:00:00.000Z to 00:00:00.000Z — "
                "this is the shipped 24/7 shape; SLA clocks on this calendar never pause."
            )

    if not calendars:
        issues.append(f"{path.name}: no businessHours entries found.")
    elif not defaults:
        issues.append(f"{path.name}: no calendar is marked default — consumers with no calendar have nothing to fall back to.")
    elif len(defaults) > 1:
        issues.append(f"{path.name}: more than one default calendar: {defaults}. Exactly one is allowed.")

    for hol in holidays:
        hname = _text(hol, "name") or "<unnamed>"
        attached = [el.text.strip() for el in _findall(hol, "businessHours") if el.text]
        if not attached:
            issues.append(
                f"{path.name} / holiday '{hname}': attached to no calendar — it suspends nothing."
            )
        for cal_name in attached:
            if cal_name not in names:
                issues.append(
                    f"{path.name} / holiday '{hname}': attached to unknown calendar '{cal_name}'."
                )
        recurring = (_text(hol, "isRecurring") or "false").lower() == "true"
        activity = _text(hol, "activityDate")
        start_t, end_t = _text(hol, "startTime"), _text(hol, "endTime")
        if (start_t is None) != (end_t is None):
            issues.append(
                f"{path.name} / holiday '{hname}': startTime and endTime must both be set or both be absent."
            )
        if not recurring:
            if not activity:
                issues.append(f"{path.name} / holiday '{hname}': non-recurring holiday has no activityDate.")
            else:
                try:
                    when = dt.date.fromisoformat(activity[:10])
                    if when < today:
                        issues.append(
                            f"{path.name} / holiday '{hname}': activityDate {activity[:10]} is in the past — "
                            "stale one-off holiday; add next year's date."
                        )
                except ValueError:
                    issues.append(f"{path.name} / holiday '{hname}': activityDate '{activity}' is not a date.")
        elif not _text(hol, "recurrenceStartDate"):
            issues.append(f"{path.name} / holiday '{hname}': recurring holiday has no recurrenceStartDate.")

    return issues


def check_business_hours_and_holidays(manifest_dir: Path, today: dt.date | None = None) -> list[str]:
    today = today or dt.date.today()
    if not manifest_dir.exists():
        return [f"Manifest directory not found: {manifest_dir}"]
    files = find_settings_files(manifest_dir)
    if not files:
        print(f"INFO: No BusinessHours settings file found under {manifest_dir}.")
        return []
    issues: list[str] = []
    for f in files:
        issues.extend(check_file(f, today))
    return issues


def main() -> int:
    args = parse_args()
    today = dt.date.fromisoformat(args.today) if args.today else None
    issues = check_business_hours_and_holidays(Path(args.manifest_dir), today)
    if not issues:
        print("No business hours issues found.")
        return 0
    for issue in issues:
        print(f"ISSUE: {issue}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
