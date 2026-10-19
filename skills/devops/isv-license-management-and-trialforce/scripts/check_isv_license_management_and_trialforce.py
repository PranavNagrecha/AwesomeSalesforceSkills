#!/usr/bin/env python3
"""Checker for the ISV License Management and Trialforce skill.

Audits a Salesforce DX source tree (or MDAPI tree) for ISV-licensing defects.
Grounded in the Summer '26 docs: FeatureParameterBoolean/Date/Integer
(api_meta.txt L66289-66600: fields dataFlowDirection, masterLabel, value;
directions LmoToSubscriber / SubscriberToLmo) and System.FeatureManagement
(Apex Reference L215378-215527: checkPackage*Value(String apiName),
setPackage*Value(String apiName, value) -- no namespace overload).

ERROR (exit 1):
  - Feature Parameter file that does not parse, has the wrong root element,
    lacks masterLabel / value / direction, has a direction other than
    LmoToSubscriber or SubscriberToLmo, or a value of the wrong type (an
    integer longer than nine digits included -- pkg2_dev.txt L23616)
  - checkPackage*Value called with other than one argument, or setPackage*Value
    with other than two (no such overload; the class does not compile)
WARN (exit 0, or 1 with --strict):
  - empty directory, or nothing ISV-licensing related found
  - unknown element in a Feature Parameter file (e.g. <defaultValue>; the
    default is <value>). Element names are case-sensitive: the direction is
    accepted as dataFlowDirection (field table, api_meta.txt L66321) or
    dataflowDirection (every sample, L66352; pkg2_dev.txt L23607), nothing else
  - setPackage*Value and checkPackage*Value on the same parameter in one class
    (propagation is not synchronous)
  - custom object / setting named like a hand-rolled license store

Stdlib only.

Usage:
    python3 check_isv_license_management_and_trialforce.py --manifest-dir force-app
    python3 check_isv_license_management_and_trialforce.py --manifest-dir force-app --strict
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

FP_TYPES = ("FeatureParameterBoolean", "FeatureParameterDate", "FeatureParameterInteger")
# Case-sensitive. The Metadata API field table spells the direction
# dataFlowDirection; every sample in both guides spells it dataflowDirection.
DIRECTION_TAGS = ("dataFlowDirection", "dataflowDirection")
FP_FIELDS = {*DIRECTION_TAGS, "masterLabel", "value", "fullName"}
DIRECTIONS = {"LmoToSubscriber", "SubscriberToLmo"}
LICENSE_STORE_RE = re.compile(
    r"^(license[_-]?(config|settings?|state|enforcement|guard|info)?"
    r"|subscription[_-]?(config|state|info)?"
    r"|trial[_-]?(config|settings?|state|info)?"
    r"|app[_-]?license)(__c)?$",
    re.IGNORECASE,
)
CALL_RE = re.compile(r"FeatureManagement\s*\.\s*(check|set)Package(Boolean|Date|Integer)Value\s*\(", re.IGNORECASE)


def _local(tag: str) -> str:
    return tag.split("}", 1)[-1]


def _strip_comments(src: str) -> str:
    src = re.sub(r"/\*.*?\*/", lambda m: "\n" * m.group(0).count("\n"), src, flags=re.S)
    return re.sub(r"//[^\n]*", "", src)


def _args(src: str, start: int) -> list[str]:
    """Split the argument list that begins after the '(' at src[start-1]."""
    depth, cur, out, i, quote = 0, [], [], start, None
    while i < len(src):
        ch = src[i]
        if quote:
            cur.append(ch)
            if ch == "\\":
                cur.append(src[i + 1:i + 2]); i += 2; continue
            if ch == quote:
                quote = None
        elif ch == "'":
            quote = ch; cur.append(ch)
        elif ch in "([{":
            depth += 1; cur.append(ch)
        elif ch in ")]}":
            if depth == 0:
                break
            depth -= 1; cur.append(ch)
        elif ch == "," and depth == 0:
            out.append("".join(cur).strip()); cur = []
        else:
            cur.append(ch)
        i += 1
    last = "".join(cur).strip()
    if last or out:
        out.append(last)
    return out


def check_feature_parameters(root: Path, errors: list[str], warns: list[str]) -> int:
    files = [p for p in root.rglob("*") if p.is_file()
             and re.search(r"\.featureParameter(Boolean|Date|Integer)(-meta\.xml)?$", p.name)]
    for f in files:
        kind = "FeatureParameter" + re.search(r"featureParameter(Boolean|Date|Integer)", f.name).group(1)
        try:
            el = ET.parse(f).getroot()
        except ET.ParseError as exc:
            errors.append(f"{f}: does not parse: {exc}")
            continue
        if _local(el.tag) != kind:
            errors.append(f"{f}: root element <{_local(el.tag)}> does not match the file suffix ({kind})")
            continue
        fields = {_local(c.tag): (c.text or "").strip() for c in el}
        direction = next((fields[t] for t in DIRECTION_TAGS if t in fields), None)
        if not direction:
            errors.append(f"{f}: missing dataFlowDirection (LmoToSubscriber or SubscriberToLmo)")
        elif direction not in DIRECTIONS:
            errors.append(f"{f}: dataFlowDirection '{direction}' is not LmoToSubscriber or SubscriberToLmo")
        if not fields.get("masterLabel"):
            errors.append(f"{f}: missing masterLabel")
        value = fields.get("value")
        if value is None or value == "":
            errors.append(f"{f}: missing <value> -- it holds the parameter's default")
        elif kind.endswith("Boolean") and value not in ("true", "false"):
            errors.append(f"{f}: <value> '{value}' is not true or false")
        elif kind.endswith("Integer") and not re.fullmatch(r"-?\d+", value):
            errors.append(f"{f}: <value> '{value}' is not an integer")
        elif kind.endswith("Integer") and len(value.lstrip("-")) > 9:
            errors.append(f"{f}: <value> '{value}' exceeds nine digits")
        elif kind.endswith("Date") and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
            errors.append(f"{f}: <value> '{value}' is not a YYYY-MM-DD date")
        unknown = sorted(_local(c.tag) for c in el if _local(c.tag) not in FP_FIELDS)
        if unknown:
            warns.append(f"{f}: element(s) {unknown} are not Feature Parameter fields (dataFlowDirection, masterLabel, value)")
    return len(files)


def check_apex(root: Path, errors: list[str], warns: list[str]) -> int:
    hits = 0
    for f in sorted(p for p in root.rglob("*") if p.is_file() and p.suffix in (".cls", ".trigger")):
        try:
            src = _strip_comments(f.read_text(encoding="utf-8", errors="ignore"))
        except OSError:
            continue
        set_keys: dict[str, int] = {}
        checks: list[tuple[str, int]] = []
        for m in CALL_RE.finditer(src):
            hits += 1
            verb = m.group(1).lower()
            args = _args(src, m.end())
            line = src[:m.start()].count("\n") + 1
            limit = 1 if verb == "check" else 2
            if len(args) != limit:
                errors.append(f"{f}:{line}: {verb}Package{m.group(2)}Value takes {limit} argument(s), got {len(args)} -- there is no other overload")
                continue
            key = args[0].strip("'") if args and args[0].startswith("'") else None
            if key and verb == "set":
                set_keys[key] = line
            elif key:
                checks.append((key, line))
        for key, line in checks:
            if key in set_keys:
                warns.append(f"{f}:{line}: checkPackage*Value('{key}') in the same class that sets it (line {set_keys[key]}) -- do not read back a just-written value")
    return hits


def check_license_stores(root: Path, warns: list[str]) -> int:
    n = 0
    for f in root.rglob("*"):
        if not f.is_file() or not re.search(r"\.object(-meta\.xml)?$", f.name):
            continue
        stem = re.sub(r"\.object(-meta\.xml)?$", "", f.name)
        if LICENSE_STORE_RE.match(stem):
            n += 1
            warns.append(f"{f}: object '{stem}' looks like a hand-rolled license store; subscriber admins can edit it -- use the LMA and Feature Parameters")
    return n


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--manifest-dir", required=True, help="Source tree root (e.g. force-app).")
    ap.add_argument("--strict", action="store_true", help="Treat WARN findings as errors (exit 1).")
    args = ap.parse_args()

    root = Path(args.manifest_dir)
    if not root.is_dir():
        print(f"ERROR: manifest directory not found: {root}")
        sys.exit(1)
    if not any(p.is_file() for p in root.rglob("*")):
        print(f"WARN: {root} is empty -- nothing to check")
        return 1 if args.strict else 0

    errors: list[str] = []
    warns: list[str] = []
    found = check_feature_parameters(root, errors, warns)
    found += check_apex(root, errors, warns)
    found += check_license_stores(root, warns)
    if not found:
        warns.append(f"{root}: no Feature Parameter files, FeatureManagement calls or license-store objects found -- nothing was checked")

    for e in errors:
        print(f"ERROR: {e}")
    for w in warns:
        print(f"WARN: {w}")
    if errors:
        sys.exit(1)
    if warns:
        return 1 if args.strict else 0
    print("OK: no ISV licensing issues found.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
