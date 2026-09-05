#!/usr/bin/env python3
"""Static save-order checks for record-triggered Flow metadata.

Parses every ``*.flow-meta.xml`` (and ``*.flow``) under ``--manifest-dir`` and
reports the shapes that deploy cleanly but sit in the wrong place in the
Salesforce order of execution. Stdlib only; never contacts an org; never
claims to have run a flow.

Checks
------
R1 ERROR    A ``RecordAfterSave`` flow whose ``recordUpdates`` element takes
            ``inputReference`` ``$Record`` — that is a second write of the row
            that was just saved, and a second pass over save-order steps 1-8.
            The same field assignment in a ``RecordBeforeSave`` flow (step 3)
            costs no extra save. Apex Developer Guide, order of execution:
            "When a process or flow executes a DML operation, the affected
            record goes through the save procedure" (apexdev.txt L15468).

R2 WARN     A ``RecordAfterSave`` flow that can fire on ``Update`` and writes
            back to its own triggering object, with neither
            ``doesRequireRecordChangedToMeetCriteria`` nor a ``filterFormula``
            on the Start element. Both are documented entry-criteria levers
            (api_meta.txt L72322-L72325 and L72390-L72392); without one of
            them, the flow's own write can re-satisfy its own entry filter.

R3 WARN     Two or more ``Active`` flows share an object plus ``triggerType``
            plus ``recordTriggerType`` and at least one of them declares no
            ``triggerOrder``. Step 14 is a single step in the order of
            execution (apexdev.txt L15470) and does not rank flows inside
            itself; ``triggerOrder`` (int 1-2,000, API 54.0+, api_meta.txt
            L68438-L68441) is the only rank the Metadata API exposes.
            ``flow/flow-governance`` owns the portfolio-wide version of this
            rule and the tie case.

R4 ADVISORY A ``RecordBeforeSave`` flow contains ``actionCalls``,
            ``recordCreates``, ``recordDeletes``, ``recordUpdates``,
            ``subflows`` or ``waits``. Advisory, not an error:
            ``api_meta.txt`` defines these element arrays on ``Flow`` without
            restricting them by ``triggerType``, and the prohibition is
            documented only on help.salesforce.com, which is not in the
            grounded corpus. Confirm in a sandbox before quoting it as a
            platform rule.

The run also prints a save-order map: every record-triggered flow in the tree,
grouped by object, placed at step 3 or step 14, ordered by ``triggerOrder``.
That map is the artifact to paste into ``templates/save-order-map.md``.

Exit codes
----------
1   ``--manifest-dir`` does not exist, or any ERROR/WARN finding was reported.
0   clean, ADVISORY-only, or no flow files found (a WARN line is printed).

Usage
-----
    python3 check_flow_record_save_order_interaction.py --manifest-dir force-app/main/default
    python3 check_flow_record_save_order_interaction.py --manifest-dir . --map-only
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

NS = "{http://soap.sforce.com/2006/04/metadata}"

BEFORE_SAVE = "RecordBeforeSave"
AFTER_SAVE = "RecordAfterSave"
SAVE_ORDER_STEP = {BEFORE_SAVE: "3", AFTER_SAVE: "14", "RecordBeforeDelete": "n/a (delete)"}
# sort rank for the map: before-save runs at step 3, after-save at step 14,
# before-delete is outside the insert/update list entirely.
STEP_RANK = {BEFORE_SAVE: 3, AFTER_SAVE: 14, "RecordBeforeDelete": 99}

DML_ARRAYS = ("recordCreates", "recordUpdates", "recordDeletes")
BEFORE_SAVE_DISALLOWED = DML_ARRAYS + ("actionCalls", "subflows", "waits")


def _child(parent, tag):
    """Return the first child element with ``tag`` or None.

    A leaf Element is falsy, so ``parent.find(a) or parent.find(b)`` silently
    discards a real match. Everything in this file goes through this helper.
    """
    if parent is None:
        return None
    found = parent.find(f"{NS}{tag}")
    return found if found is not None else None


def _text(parent, tag, default=None):
    el = _child(parent, tag)
    if el is None or el.text is None:
        return default
    return el.text.strip()


def _all(parent, tag):
    if parent is None:
        return []
    return list(parent.findall(f"{NS}{tag}"))


class FlowFacts:
    """The subset of a Flow's metadata that the save order cares about."""

    def __init__(self, path: Path, root: ET.Element):
        self.path = path
        self.name = path.name.split(".")[0]
        start = _child(root, "start")
        self.trigger_type = _text(start, "triggerType")
        self.record_trigger_type = _text(start, "recordTriggerType")
        self.object = _text(start, "object")
        self.filter_formula = _text(start, "filterFormula")
        self.requires_change = (_text(start, "doesRequireRecordChangedToMeetCriteria") or "").lower() == "true"
        self.has_filters = bool(_all(start, "filters"))
        self.scheduled_paths = [
            (_text(p, "name"), _text(p, "pathType") or "null")
            for p in _all(start, "scheduledPaths")
        ]
        self.status = _text(root, "status")
        self.api_version = _text(root, "apiVersion")
        order = _text(root, "triggerOrder")
        self.trigger_order = int(order) if order and order.lstrip("-").isdigit() else None
        self.elements = {tag: _all(root, tag) for tag in BEFORE_SAVE_DISALLOWED}

    @property
    def is_record_triggered(self) -> bool:
        return self.trigger_type in SAVE_ORDER_STEP

    @property
    def is_active(self) -> bool:
        return self.status == "Active"

    def updates_of_record_variable(self):
        """recordUpdates elements whose inputReference is the triggering record."""
        out = []
        for upd in self.elements.get("recordUpdates", []):
            ref = _text(upd, "inputReference")
            if ref and ref.split(".")[0] == "$Record":
                out.append(_text(upd, "name") or "(unnamed)")
        return out

    def updates_of_own_object(self):
        """recordUpdates elements that write rows of the triggering object."""
        out = []
        for upd in self.elements.get("recordUpdates", []):
            name = _text(upd, "name") or "(unnamed)"
            ref = _text(upd, "inputReference")
            if ref and ref.split(".")[0] == "$Record":
                out.append(name)
                continue
            if self.object and _text(upd, "object") == self.object:
                out.append(name)
        return out


def load(path: Path):
    try:
        return FlowFacts(path, ET.parse(path).getroot())
    except ET.ParseError as exc:
        return exc


def check(flows, findings):
    for f in flows:
        if not f.is_record_triggered:
            continue

        # R1 — after-save flow re-writing the record that was just saved.
        if f.trigger_type == AFTER_SAVE:
            for el in f.updates_of_record_variable():
                findings.append((
                    "ERROR", f.path,
                    f"R1 {f.name}: after-save element '{el}' updates $Record itself. "
                    "That is a second save procedure for a row already saved at step 7. "
                    "Move the field assignment into a RecordBeforeSave flow (step 3), "
                    "where the write costs no extra save.",
                ))

        # R2 — after-save flow writing its own object with no transition guard.
        if f.trigger_type == AFTER_SAVE and (f.record_trigger_type or "") in ("Update", "CreateAndUpdate"):
            same_object = f.updates_of_own_object()
            if same_object and not f.requires_change and not f.filter_formula:
                findings.append((
                    "WARN", f.path,
                    f"R2 {f.name}: after-save flow on {f.object} writes back to {f.object} "
                    f"({', '.join(sorted(set(same_object)))}) with neither "
                    "doesRequireRecordChangedToMeetCriteria nor filterFormula on <start>. "
                    "Its own write re-enters the save order and can re-satisfy its own entry filter.",
                ))

        # R4 — before-save flow carrying elements that belong after the save.
        if f.trigger_type == BEFORE_SAVE:
            offenders = sorted(tag for tag in BEFORE_SAVE_DISALLOWED if f.elements.get(tag))
            if offenders:
                findings.append((
                    "ADVISORY", f.path,
                    f"R4 {f.name}: before-save flow contains {', '.join(offenders)}. "
                    "Step 3 exists to mutate $Record before the step-7 save; anything that "
                    "touches another row belongs in an after-save flow. "
                    "Advisory only — api_meta.txt does not restrict these arrays by triggerType.",
                ))

    # R3 — undeclared run order among co-resident active flows.
    buckets = defaultdict(list)
    for f in flows:
        if f.is_record_triggered and f.is_active and f.object:
            buckets[(f.object, f.trigger_type, f.record_trigger_type)].append(f)
    for (obj, tt, rtt), group in sorted(buckets.items(), key=lambda kv: str(kv[0])):
        if len(group) < 2:
            continue
        unset = [f for f in group if f.trigger_order is None]
        if unset:
            step = SAVE_ORDER_STEP.get(tt, "?")
            findings.append((
                "WARN", unset[0].path,
                f"R3 {obj}/{tt}/{rtt}: {len(group)} active flows share save-order step {step}; "
                f"{len(unset)} of them declare no <triggerOrder> "
                f"({', '.join(sorted(f.name for f in unset))}). "
                "The order of execution names the step once and does not rank flows inside it.",
            ))


def print_map(flows) -> None:
    record_triggered = [f for f in flows if f.is_record_triggered]
    if not record_triggered:
        return
    print("\nSave-order map")
    print("-" * 72)
    by_object = defaultdict(list)
    for f in record_triggered:
        by_object[f.object or "(no object)"].append(f)
    for obj in sorted(by_object):
        print(f"\n{obj}")
        rows = sorted(
            by_object[obj],
            key=lambda f: (STEP_RANK.get(f.trigger_type, 999),
                           f.trigger_order if f.trigger_order is not None else 10 ** 6,
                           f.name),
        )
        for f in rows:
            order = f.trigger_order if f.trigger_order is not None else "-"
            paths = ", ".join(f"{n}:{t}" for n, t in f.scheduled_paths) or "-"
            print(
                f"  step {SAVE_ORDER_STEP.get(f.trigger_type, '?'):>3}  "
                f"order {str(order):>4}  {f.status or '?':<8} "
                f"{f.record_trigger_type or '?':<16} {f.name}"
            )
            if f.scheduled_paths:
                print(f"{'':>16}scheduled paths (step 20 / later transaction): {paths}")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Save-order checks for record-triggered flows.")
    p.add_argument("--manifest-dir", required=True,
                   help="source tree to scan, e.g. force-app/main/default")
    p.add_argument("--map-only", action="store_true",
                   help="print the save-order map and skip the findings")
    p.add_argument("--strict", action="store_true",
                   help="exit 1 on WARN as well as ERROR (default: ERROR only; WARN and ADVISORY are reported but do not fail)")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(args.manifest_dir)
    if not root.exists() or not root.is_dir():
        print(f"ERROR: --manifest-dir not found: {root}")
        return 1

    files = sorted(set(root.rglob("*.flow-meta.xml")) | set(root.rglob("*.flow")))
    if not files:
        print(f"WARN: no *.flow-meta.xml or *.flow files under {root} — nothing to check.")
        return 0

    flows = []
    findings: list[tuple[str, Path, str]] = []
    for path in files:
        loaded = load(path)
        if isinstance(loaded, ET.ParseError):
            findings.append(("ERROR", path, f"unparseable XML — {loaded}"))
            continue
        flows.append(loaded)

    if not args.map_only:
        check(flows, findings)

    rank = {"ERROR": 0, "WARN": 1, "ADVISORY": 2}
    blocking_levels = ("ERROR", "WARN") if args.strict else ("ERROR",)
    hard = 0
    for level, path, msg in sorted(findings, key=lambda f: (rank[f[0]], str(f[1]))):
        print(f"{level}: {path}: {msg}")
        if level in blocking_levels:
            hard += 1

    print_map(flows)

    print(f"\n{len(flows)} flow file(s) scanned; {len(findings)} finding(s), {hard} blocking.")
    return 1 if hard else 0


if __name__ == "__main__":
    sys.exit(main())
