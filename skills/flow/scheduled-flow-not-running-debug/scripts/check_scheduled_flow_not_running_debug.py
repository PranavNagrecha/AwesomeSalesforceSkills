#!/usr/bin/env python3
"""Detect Schedule-Triggered Flows in retrieved org metadata and surface
risk indicators that commonly cause "scheduled flow not running"
incidents.

Walks an SFDX-style metadata tree (force-app/) and reports:

1. Every flow whose `<start>` element has a Schedule trigger
   (`<triggerType>Scheduled</triggerType>`), with its scheduledStart,
   frequency, and start-element filter conditions.
2. Schedule-triggered flows whose start filter is empty / missing
   (will fire but match zero records — a frequent "active but no work"
   complaint).
3. Schedule-triggered flows configured for a fire time inside the
   2 AM – 3 AM local window (DST-spring-forward risk).
4. Schedule-triggered flows that invoke an Apex action class — these
   are at risk of CronTrigger abort if the class is redeployed.

Stdlib only — no pip dependencies.

Usage:
    python3 check_scheduled_flow_not_running_debug.py [--root force-app/main/default]

Exit codes:
    0  no findings (no schedule-triggered flows, or all clean)
    1  findings present (informational, non-blocking)
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

NS = {"s": "http://soap.sforce.com/2006/04/metadata"}

DST_RISK_HOUR_RE = re.compile(r"^0?2:\d{2}")  # matches "02:00", "2:30" etc.


def find_scheduled_flows(flows_dir: Path) -> list[dict]:
    """Return one dict per Schedule-Triggered Flow found."""
    findings: list[dict] = []
    if not flows_dir.exists():
        return findings
    for fp in flows_dir.rglob("*.flow-meta.xml"):
        try:
            tree = ET.parse(fp)
        except ET.ParseError:
            continue
        root = tree.getroot()
        # Find <start> element
        start_el = root.find("s:start", NS)
        if start_el is None:
            continue
        trigger_type_el = start_el.find("s:triggerType", NS)
        if trigger_type_el is None or trigger_type_el.text != "Scheduled":
            continue

        info: dict = {"path": fp, "flow_name": fp.stem.replace(".flow-meta", "")}

        # Schedule details
        schedule_el = start_el.find("s:schedule", NS)
        if schedule_el is not None:
            freq_el = schedule_el.find("s:frequency", NS)
            start_dt_el = schedule_el.find("s:startDate", NS)
            start_time_el = schedule_el.find("s:startTime", NS)
            info["frequency"] = freq_el.text if freq_el is not None else "(unset)"
            info["start_date"] = start_dt_el.text if start_dt_el is not None else "(unset)"
            info["start_time"] = start_time_el.text if start_time_el is not None else "(unset)"
        else:
            info["frequency"] = "(unset)"
            info["start_date"] = "(unset)"
            info["start_time"] = "(unset)"

        # Object + filter
        obj_el = start_el.find("s:object", NS)
        info["object"] = obj_el.text if obj_el is not None else "(none)"
        filters = start_el.findall("s:filters", NS)
        info["filter_count"] = len(filters)
        info["filter_empty"] = len(filters) == 0

        # DST risk: start time begins with "02:" or "2:" -> in DST gap window
        info["dst_risk"] = bool(
            info["start_time"] != "(unset)"
            and DST_RISK_HOUR_RE.match(info["start_time"])
        )

        # Invocable Apex action references (CronTrigger-abort risk on deploy)
        action_calls = root.findall(".//s:actionCalls", NS)
        apex_actions: list[str] = []
        for ac in action_calls:
            atype = ac.find("s:actionType", NS)
            aname = ac.find("s:actionName", NS)
            if (
                atype is not None
                and atype.text == "apex"
                and aname is not None
                and aname.text
            ):
                apex_actions.append(aname.text)
        info["apex_actions"] = apex_actions

        findings.append(info)
    return findings


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", default="force-app/main/default")
    args = p.parse_args()

    root = Path(args.root)
    if not root.exists():
        print(f"metadata root not found: {root}", file=sys.stderr)
        return 0

    flows_dir = root / "flows"
    findings = find_scheduled_flows(flows_dir)

    if not findings:
        print("No Schedule-Triggered Flows found in this metadata tree.")
        return 0

    print(f"\n## Schedule-Triggered Flows in this metadata tree ({len(findings)} total)\n")
    for f in findings:
        print(
            f"- {f['flow_name']}  "
            f"[freq={f['frequency']}, start={f['start_date']} {f['start_time']}, "
            f"object={f['object']}, filters={f['filter_count']}]"
        )

    risk_findings = 0

    empty_filter = [f for f in findings if f["filter_empty"]]
    if empty_filter:
        print(f"\n## Risk: Scheduled flows with NO start filter ({len(empty_filter)})")
        print("  Will fire on schedule but match every record of the object — review intentionality.")
        for f in empty_filter:
            print(f"  - {f['flow_name']} (object={f['object']})")
        risk_findings += len(empty_filter)

    dst_risk = [f for f in findings if f["dst_risk"]]
    if dst_risk:
        print(f"\n## Risk: Scheduled flows in DST gap window 2 AM – 3 AM ({len(dst_risk)})")
        print("  Spring-forward day skips this hour. Reschedule to a non-DST-impacted time.")
        for f in dst_risk:
            print(f"  - {f['flow_name']} (start_time={f['start_time']})")
        risk_findings += len(dst_risk)

    apex_using = [f for f in findings if f["apex_actions"]]
    if apex_using:
        print(f"\n## Risk: Scheduled flows invoking Apex actions ({len(apex_using)})")
        print("  Deploying these Apex classes may auto-abort the CronTrigger.")
        print("  Add a post-deploy step to verify CronTrigger persists.")
        for f in apex_using:
            print(f"  - {f['flow_name']} -> {', '.join(f['apex_actions'])}")
        risk_findings += len(apex_using)

    if risk_findings == 0:
        print("\nNo risk indicators detected.")
        return 0

    print(f"\nTotal risk indicators: {risk_findings}")
    print("Refer to skills/flow/scheduled-flow-not-running-debug/SKILL.md for remediation.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
