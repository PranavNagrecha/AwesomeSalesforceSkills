#!/usr/bin/env python3
"""Checker for the Batch Job Scheduling And Monitoring skill.

Lints the scheduling registry (`*scheduled-jobs-registry.y*ml`, see
references/metadata-examples.md section 5) and reconciles it against the Apex
and Flow metadata in the manifest directory.

Checks
------
ERROR  1. Registry entries are missing a required key
       2. Registry job names are not unique
       3. `cron` is not a 6- or 7-field expression with in-range values
       4. `window` is not `HH:MM-HH:MM`
WARN   5. Two entries share an `apex_class` and their windows overlap
       6. A registry entry names an Apex class that is not in the manifest
INFO   7. A Schedulable class in the manifest has no registry entry
       8. A Flow with <triggerType>Scheduled</triggerType> has no registry entry

Exit status: 1 if any ERROR was reported, otherwise 0. WARN and INFO do not
fail the run.

Stdlib only — no pip dependencies, no PyYAML (the registry is a deliberately
flat subset of YAML so it can be parsed here without one).

Usage:
    python3 check_batch_job_scheduling_and_monitoring.py --manifest-dir path/to/project
    python3 check_batch_job_scheduling_and_monitoring.py --manifest-dir . --registry config/scheduled-jobs-registry.yaml
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

MDAPI_NS = "{http://soap.sforce.com/2006/04/metadata}"

REQUIRED_KEYS = ("name", "apex_class", "cron", "owner", "window", "alert_channel")

# Seconds Minutes Hours Day_of_month Month Day_of_week [Optional_year]
# Apex Reference Guide, System.schedule(jobName, cronExpression, schedulableClass).
CRON_FIELDS = (
    ("Seconds", 0, 59),
    ("Minutes", 0, 59),
    ("Hours", 0, 23),
    ("Day_of_month", 1, 31),
    ("Month", 1, 12),
    ("Day_of_week", 1, 7),
    ("Optional_year", 1970, 2099),
)
MONTH_NAMES = {"JAN", "FEB", "MAR", "APR", "MAY", "JUN",
               "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"}
DAY_NAMES = {"SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT"}

WINDOW_RE = re.compile(r"^(\d{1,2}):(\d{2})-(\d{1,2}):(\d{2})$")

SCHEDULABLE_RE = re.compile(r"\bimplements\b[^{]*\bSchedulable\b", re.IGNORECASE)
CLASS_NAME_RE = re.compile(
    r"\b(?:global|public|private)\s+(?:with\s+sharing\s+|without\s+sharing\s+|"
    r"inherited\s+sharing\s+|abstract\s+|virtual\s+)*class\s+(\w+)",
    re.IGNORECASE,
)


class Finding:
    """One reported problem, carrying its own severity."""

    def __init__(self, severity: str, message: str) -> None:
        self.severity = severity
        self.message = message

    def __str__(self) -> str:
        return f"{self.severity}: {self.message}"


# --------------------------------------------------------------------------
# XML helpers
# --------------------------------------------------------------------------

def first_child_text(element, *tag_names: str) -> str | None:
    """Return the text of the first present child among tag_names.

    Written explicitly against `is not None` because an ElementTree Element with
    no children is falsy, so `element.find(a) or element.find(b)` silently skips
    a leaf element that WAS found. Never use `or` to chain find() calls.
    """
    for tag in tag_names:
        for candidate in (tag, MDAPI_NS + tag):
            found = element.find(candidate)
            if found is not None and found.text is not None:
                return found.text.strip()
    return None


def find_child(element, tag: str):
    """Namespace-tolerant single-child lookup; returns None when absent."""
    found = element.find(tag)
    if found is not None:
        return found
    return element.find(MDAPI_NS + tag)


# --------------------------------------------------------------------------
# Registry parsing (flat YAML subset)
# --------------------------------------------------------------------------

def parse_registry(path: Path) -> tuple[list[dict], list[Finding]]:
    """Parse a `jobs:` list of flat `key: value` mappings.

    Deliberately narrow: comments, blank lines, `jobs:`, `- key: value` and
    `  key: value` are understood; nested structures are not, and are reported
    rather than silently dropped.
    """
    findings: list[Finding] = []
    entries: list[dict] = []
    current: dict | None = None
    seen_jobs_key = False

    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError as exc:
        findings.append(Finding("ERROR", f"{path}: cannot be read ({exc})"))
        return entries, findings

    for lineno, raw in enumerate(lines, start=1):
        line = raw.split(" #", 1)[0].rstrip() if " #" in raw else raw.rstrip()
        if not line.strip() or line.lstrip().startswith("#"):
            continue

        stripped = line.strip()

        if stripped == "jobs:":
            seen_jobs_key = True
            continue

        if stripped.startswith("- "):
            current = {}
            entries.append(current)
            stripped = stripped[2:].strip()

        if current is None:
            findings.append(Finding(
                "ERROR",
                f"{path}:{lineno}: '{stripped}' sits outside any job entry — "
                "the registry must be a `jobs:` list of `- name: ...` blocks",
            ))
            continue

        if ":" not in stripped:
            findings.append(Finding(
                "ERROR", f"{path}:{lineno}: '{stripped}' is not a `key: value` pair"))
            continue

        key, _, value = stripped.partition(":")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if not value:
            findings.append(Finding(
                "ERROR", f"{path}:{lineno}: key '{key}' has no value"))
            continue
        current[key] = value
        current.setdefault("__line__", str(lineno))

    if not seen_jobs_key:
        findings.append(Finding(
            "ERROR", f"{path}: no top-level `jobs:` key found"))

    return entries, findings


# --------------------------------------------------------------------------
# Individual checks
# --------------------------------------------------------------------------

def check_cron_field(value: str, name: str, low: int, high: int) -> str | None:
    """Return an error string for one cron field, or None when it is legal."""
    if value in ("*", "?"):
        return None
    for token in re.split(r"[,\-/#]", value):
        token = token.strip().upper()
        if not token or token in ("L", "W"):
            continue
        token = token.rstrip("LW")
        if not token:
            continue
        if name == "Month" and token in MONTH_NAMES:
            continue
        if name == "Day_of_week" and token in DAY_NAMES:
            continue
        if not token.isdigit():
            return f"{name} field contains '{token}', which is not a number or a recognised name"
        number = int(token)
        if number < low or number > high:
            return f"{name} value {number} is outside the documented range {low}-{high}"
    return None


def check_cron(expression: str) -> list[str]:
    """Validate a Salesforce CRON expression's shape and field ranges."""
    errors: list[str] = []
    fields = expression.split()
    if len(fields) not in (6, 7):
        return [
            f"'{expression}' has {len(fields)} fields; a Salesforce CRON expression has 6 or 7 "
            "(Seconds Minutes Hours Day_of_month Month Day_of_week [Optional_year])"
        ]

    for value, (name, low, high) in zip(fields, CRON_FIELDS):
        problem = check_cron_field(value, name, low, high)
        if problem:
            errors.append(f"'{expression}': {problem}")

    day_of_month, day_of_week = fields[3], fields[5]
    if "?" not in (day_of_month, day_of_week):
        errors.append(
            f"'{expression}': exactly one of Day_of_month / Day_of_week must be '?' — "
            "'?' means no specific value and is legal only in those two fields"
        )
    return errors


def parse_window(value: str) -> tuple[int, int] | None:
    """Return (start_minutes, end_minutes) for an HH:MM-HH:MM window."""
    match = WINDOW_RE.match(value)
    if not match:
        return None
    sh, sm, eh, em = (int(g) for g in match.groups())
    if sh > 23 or eh > 23 or sm > 59 or em > 59:
        return None
    start = sh * 60 + sm
    end = eh * 60 + em
    if end <= start:          # window crosses midnight
        end += 24 * 60
    return start, end


def check_registry(entries: list[dict], path: Path) -> list[Finding]:
    findings: list[Finding] = []
    seen_names: dict[str, str] = {}
    windows_by_class: dict[str, list[tuple[str, int, int]]] = {}

    for entry in entries:
        label = entry.get("name") or f"{path}:{entry.get('__line__', '?')}"

        for key in REQUIRED_KEYS:
            if key not in entry:
                findings.append(Finding(
                    "ERROR",
                    f"{label}: missing required key '{key}'. Every registry entry needs "
                    f"{', '.join(REQUIRED_KEYS)} — an entry without an owner or alert_channel "
                    "cannot page anyone when the job fails.",
                ))

        name = entry.get("name")
        if name:
            if name in seen_names:
                findings.append(Finding(
                    "ERROR",
                    f"{label}: duplicate job name. 'name' must match CronJobDetail.Name, which "
                    f"is how the registry reconciles to the org (first seen at line "
                    f"{seen_names[name]}).",
                ))
            else:
                seen_names[name] = entry.get("__line__", "?")

        cron = entry.get("cron")
        if cron:
            for problem in check_cron(cron):
                findings.append(Finding("ERROR", f"{label}: {problem}"))

        window = entry.get("window")
        if window:
            bounds = parse_window(window)
            if bounds is None:
                findings.append(Finding(
                    "ERROR",
                    f"{label}: window '{window}' is not HH:MM-HH:MM with in-range times.",
                ))
            elif entry.get("apex_class"):
                windows_by_class.setdefault(entry["apex_class"], []).append(
                    (label, bounds[0], bounds[1]))

    for apex_class, windows in windows_by_class.items():
        for i in range(len(windows)):
            for j in range(i + 1, len(windows)):
                a_label, a_start, a_end = windows[i]
                b_label, b_start, b_end = windows[j]
                if a_start < b_end and b_start < a_end:
                    findings.append(Finding(
                        "WARN",
                        f"{apex_class}: runtime windows of '{a_label}' and '{b_label}' overlap. "
                        "A second instance attempted while one is running puts the CronTrigger "
                        "into BLOCKED state and the window is simply missed — see gotcha 7.",
                    ))

    return findings


# --------------------------------------------------------------------------
# Manifest scanning
# --------------------------------------------------------------------------

def find_source_dirs(manifest_dir: Path, leaf: str) -> list[Path]:
    candidates = [
        manifest_dir / "force-app" / "main" / "default" / leaf,
        manifest_dir / "src" / leaf,
        manifest_dir / leaf,
    ]
    return [c for c in candidates if c.is_dir()]


def collect_schedulable_classes(manifest_dir: Path) -> set[str]:
    names: set[str] = set()
    for classes_dir in find_source_dirs(manifest_dir, "classes"):
        for cls_file in sorted(classes_dir.glob("*.cls")):
            try:
                content = cls_file.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            if not SCHEDULABLE_RE.search(content):
                continue
            match = CLASS_NAME_RE.search(content)
            names.add(match.group(1) if match else cls_file.stem)
    return names


def collect_scheduled_flows(manifest_dir: Path) -> set[str]:
    names: set[str] = set()
    for flows_dir in find_source_dirs(manifest_dir, "flows"):
        for flow_file in sorted(flows_dir.glob("*.flow-meta.xml")) + sorted(flows_dir.glob("*.flow")):
            try:
                root = ET.parse(flow_file).getroot()
            except (ET.ParseError, OSError):
                continue
            start = find_child(root, "start")
            if start is None:
                continue
            trigger_type = first_child_text(start, "triggerType")
            if trigger_type == "Scheduled":
                names.add(flow_file.name.split(".")[0])
    return names


def find_registry(manifest_dir: Path, explicit: str | None) -> Path | None:
    if explicit:
        candidate = Path(explicit)
        if not candidate.is_absolute():
            candidate = manifest_dir / candidate
        return candidate if candidate.is_file() else None
    for pattern in ("**/*scheduled-jobs-registry.yaml", "**/*scheduled-jobs-registry.yml"):
        for hit in sorted(manifest_dir.glob(pattern)):
            return hit
    return None


# --------------------------------------------------------------------------
# Driver
# --------------------------------------------------------------------------

def run_checks(manifest_dir: Path, registry_arg: str | None) -> list[Finding]:
    findings: list[Finding] = []

    if not manifest_dir.exists():
        return [Finding("ERROR", f"Manifest directory not found: {manifest_dir}")]

    schedulable = collect_schedulable_classes(manifest_dir)
    scheduled_flows = collect_scheduled_flows(manifest_dir)

    registry_path = find_registry(manifest_dir, registry_arg)
    if registry_path is None:
        severity = "ERROR" if (schedulable or scheduled_flows) else "INFO"
        findings.append(Finding(
            severity,
            "No scheduling registry found (looked for *scheduled-jobs-registry.yaml|yml under "
            f"{manifest_dir}). Schedules are org data and are not deployed or copied on sandbox "
            "refresh, so the registry is the only record of what should be scheduled. See "
            "references/metadata-examples.md section 5.",
        ))
        return findings

    entries, parse_findings = parse_registry(registry_path)
    findings.extend(parse_findings)
    findings.extend(check_registry(entries, registry_path))

    registered_classes = {e["apex_class"] for e in entries if e.get("apex_class")}
    registered_names = {e["name"] for e in entries if e.get("name")}

    for cls in sorted(registered_classes - schedulable):
        if schedulable:
            findings.append(Finding(
                "WARN",
                f"Registry names Apex class '{cls}', which is not a Schedulable class in "
                f"{manifest_dir}. Either the class was renamed or the registry is stale — a "
                "reschedule after refresh will fail on this entry.",
            ))

    for cls in sorted(schedulable - registered_classes):
        findings.append(Finding(
            "INFO",
            f"Schedulable class '{cls}' has no registry entry. If it is scheduled in any org, "
            "add it so the reschedule runbook can rebuild it.",
        ))

    for flow in sorted(scheduled_flows - registered_names - registered_classes):
        findings.append(Finding(
            "INFO",
            f"Scheduled Flow '{flow}' has no registry entry. Its schedule ships with the Flow "
            "metadata, but its owner, runtime window and alert channel do not.",
        ))

    return findings


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Lint the scheduled-jobs registry and reconcile it against Schedulable Apex "
            "classes and scheduled Flows in the manifest directory."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    parser.add_argument(
        "--registry",
        default=None,
        help=(
            "Path to the scheduling registry YAML. Default: the first "
            "*scheduled-jobs-registry.yaml|yml found under --manifest-dir."
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    findings = run_checks(Path(args.manifest_dir), args.registry)

    if not findings:
        print("No issues found.")
        return 0

    order = {"ERROR": 0, "WARN": 1, "INFO": 2}
    for finding in sorted(findings, key=lambda f: order.get(f.severity, 3)):
        print(finding)

    errors = sum(1 for f in findings if f.severity == "ERROR")
    warns = sum(1 for f in findings if f.severity == "WARN")
    infos = len(findings) - errors - warns
    print(f"\n{errors} error(s), {warns} warning(s), {infos} note(s).")

    if errors:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
