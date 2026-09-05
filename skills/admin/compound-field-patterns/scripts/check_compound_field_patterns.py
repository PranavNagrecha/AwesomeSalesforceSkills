#!/usr/bin/env python3
"""Checker for the Compound Field Patterns skill.

Scans a Salesforce DX / Metadata API source tree for the compound-field
mistakes that deploy cleanly and then behave wrong.

Metadata checks (*.field-meta.xml, *.object):
  WARN  a `Location` custom field with no `scale` or no `displayLocationInDecimal`
  INFO  a `*_Latitude__c` / `*_Longitude__c` custom field sitting next to a
        `Location` field on the same object (the same coordinates stored twice)
  INFO  three or more separate address-part text fields on one object where a
        compound address would serve

Query and Apex checks (*.cls, *.trigger, *.soql, *.apex):
  ERROR a compound field used as a filter value in a WHERE clause
  ERROR `DISTANCE(...)` with fewer than three arguments (no unit)
  ERROR `DISTANCE(...)` whose unit is not a literal 'mi' or 'km'
  ERROR `DISTANCE(GEOLOCATION(...), field, unit)` — operands the wrong way round
  ERROR `DISTANCE(...)` compared with =, ==, >= or <=
  ERROR assignment to a compound Address field (compounds are read-only for DML)
  ERROR assignment to a compound `Name` on Contact / Lead / User

Grounding for every rule is in ../references/gotchas.md and
../references/metadata-examples.md, with Object Reference and Metadata API
line citations.

Exit status: 1 if any ERROR (or, with --strict, any ERROR or WARN); else 0.

Usage:
    python3 check_compound_field_patterns.py --manifest-dir force-app/main/default
    python3 check_compound_field_patterns.py --manifest-dir . --strict
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

MD_NS = "{http://soap.sforce.com/2006/04/metadata}"

# Standard address compound fields. Person Account variants included.
STANDARD_ADDRESS_COMPOUNDS = [
    "BillingAddress",
    "ShippingAddress",
    "MailingAddress",
    "OtherAddress",
    "PersonMailingAddress",
    "PersonOtherAddress",
    "Address",
]

ADDRESS_PART_TOKENS = ("street", "city", "state", "postalcode", "zip", "country")

ASSIGN_COMPOUND = re.compile(
    r"\.(?:Billing|Shipping|Mailing|Other|PersonMailing|PersonOther)Address\s*=(?!=)",
    re.IGNORECASE,
)
ASSIGN_READONLY_NAME = re.compile(r"\b(?:Contact|Lead|User)\w*\.Name\s*=(?!=)")
# Locals declared with a compound-Name type: `Contact c = ...` -> flag `c.Name =`.
DECLARED_NAME_TYPE = re.compile(r"\b(?:Contact|Lead|User)\s+([A-Za-z_]\w*)\s*[=;,)]")

SCANNED_CODE_SUFFIXES = (".cls", ".trigger", ".soql", ".apex")


# --------------------------------------------------------------------------
# XML helpers. A leaf Element is falsy, so `a.find(x) or a.find(y)` silently
# discards a real match. Every lookup here tests `is not None`.
# --------------------------------------------------------------------------

def find_child(parent, tag):
    """Return the child element named `tag`, namespaced or not, else None."""
    node = parent.find(MD_NS + tag)
    if node is not None:
        return node
    node = parent.find(tag)
    if node is not None:
        return node
    return None


def child_text(parent, tag):
    """Return the stripped text of child `tag`, or None if absent or empty."""
    node = find_child(parent, tag)
    if node is None:
        return None
    if node.text is None:
        return None
    text = node.text.strip()
    if text == "":
        return None
    return text


def iter_field_elements(path):
    """Yield (field_element, source_label) for every field definition in a file.

    Handles both DX-decomposed `<CustomField>` files and package-format
    `<CustomObject>` files whose fields are `<fields>` children.
    """
    try:
        root = ET.parse(str(path)).getroot()
    except (ET.ParseError, OSError):
        return
    tag = root.tag.split("}")[-1]
    if tag == "CustomField":
        yield root, path.name
    elif tag == "CustomObject":
        for node in list(root.findall(MD_NS + "fields")) + list(root.findall("fields")):
            yield node, path.name


class Finding:
    def __init__(self, severity, location, message):
        self.severity = severity
        self.location = location
        self.message = message

    def __str__(self):
        return "{}: {}: {}".format(self.severity, self.location, self.message)


# --------------------------------------------------------------------------
# Metadata checks
# --------------------------------------------------------------------------

def check_metadata(root):
    """Inspect field metadata. Returns (findings, set_of_location_field_names)."""
    findings = []
    by_object = {}  # object dir name -> {"location": [...], "text": [...]}
    location_field_names = set()

    candidates = list(root.rglob("*.field-meta.xml")) + list(root.rglob("*.object"))
    for path in candidates:
        # objects/<Object>/fields/<Field>.field-meta.xml -> "<Object>"
        if path.name.endswith(".object"):
            obj = path.name[: -len(".object")]
        elif path.parent.name == "fields":
            obj = path.parent.parent.name
        else:
            obj = path.parent.name
        bucket = by_object.setdefault(obj, {"location": [], "text": []})

        for field, label in iter_field_elements(path):
            full_name = child_text(field, "fullName")
            if full_name is None:
                continue
            field_type = child_text(field, "type")
            rel = path.relative_to(root)

            if field_type == "Location":
                location_field_names.add(full_name)
                bucket["location"].append(full_name)
                missing = []
                if child_text(field, "scale") is None:
                    missing.append("scale")
                if child_text(field, "displayLocationInDecimal") is None:
                    missing.append("displayLocationInDecimal")
                if missing:
                    findings.append(Finding(
                        "WARN",
                        "{} ({})".format(rel, full_name),
                        "Location field is missing <{}>. scale fixes stored precision and "
                        "displayLocationInDecimal fixes decimal-vs-DMS display; both default "
                        "silently and widening scale later rewrites stored values "
                        "(api_meta.txt L43364-L43368, L43608-L43612).".format(
                            "> and <".join(missing)),
                    ))
            else:
                bucket["text"].append(full_name)

    for obj in sorted(by_object):
        bucket = by_object[obj]
        lower_text = [n.lower() for n in bucket["text"]]

        # Duplicate coordinate storage next to a real Location field.
        if bucket["location"]:
            for name in sorted(bucket["text"]):
                low = name.lower()
                if low.endswith("latitude__c") or low.endswith("longitude__c"):
                    findings.append(Finding(
                        "INFO",
                        "{} ({})".format(obj, name),
                        "Coordinate-named custom field alongside Location field(s) {}. A Location "
                        "field already exposes __Latitude__s / __Longitude__s components "
                        "(object_reference.txt L2915-L2917); storing the same coordinates twice "
                        "costs extra fields and lets the two copies drift.".format(
                            ", ".join(sorted(bucket["location"]))),
                    ))

        # Address modelled as loose text fields.
        parts = set()
        for token in ADDRESS_PART_TOKENS:
            for name in lower_text:
                if token in name:
                    parts.add("postalcode" if token == "zip" else token)
                    break
        if len(parts) >= 3:
            findings.append(Finding(
                "INFO",
                obj,
                "{} address-part custom fields ({}) look like a hand-rolled address. Consider a "
                "compound: standard address components, or an Address custom field if "
                "CustomAddressFieldSettings.enableCustomAddressField is on — note that "
                "enablement cannot be reversed (api_meta.txt L113905-L113909).".format(
                    len(parts), ", ".join(sorted(parts))),
            ))

    return findings, location_field_names


# --------------------------------------------------------------------------
# SOQL / Apex checks
# --------------------------------------------------------------------------

def split_top_level_args(text):
    """Split a balanced argument list on top-level commas."""
    args = []
    depth = 0
    current = ""
    for ch in text:
        if ch == "(":
            depth += 1
            current += ch
        elif ch == ")":
            depth -= 1
            current += ch
        elif ch == "," and depth == 0:
            args.append(current.strip())
            current = ""
        else:
            current += ch
    if current.strip() != "":
        args.append(current.strip())
    return args


def find_call_spans(text, name):
    """Yield (start, end, inner) for every balanced `name(...)` call."""
    pattern = re.compile(r"\b" + name + r"\s*\(", re.IGNORECASE)
    for match in pattern.finditer(text):
        depth = 0
        i = match.end() - 1
        while i < len(text):
            if text[i] == "(":
                depth += 1
            elif text[i] == ")":
                depth -= 1
                if depth == 0:
                    yield match.start(), i + 1, text[match.end():i]
                    break
            i += 1


def blank_out(text, spans):
    """Replace character ranges with spaces, preserving offsets for line numbers."""
    chars = list(text)
    for start, end in spans:
        for i in range(start, end):
            chars[i] = " "
    return "".join(chars)


def line_of(text, index):
    return text[:index].count("\n") + 1


def check_code(root, location_field_names):
    findings = []
    compound_names = list(STANDARD_ADDRESS_COMPOUNDS) + sorted(location_field_names)
    compound_re = re.compile(
        r"(?<![\w.])(" + "|".join(re.escape(n) for n in compound_names) + r")\b",
        re.IGNORECASE,
    )

    paths = []
    for suffix in SCANNED_CODE_SUFFIXES:
        paths.extend(root.rglob("*" + suffix))

    for path in sorted(set(paths)):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        rel = path.relative_to(root)

        # --- DISTANCE() argument checks ---
        distance_spans = []
        for start, end, inner in find_call_spans(text, "DISTANCE"):
            distance_spans.append((start, end))
            line = line_of(text, start)
            args = split_top_level_args(inner)

            if len(args) < 3:
                findings.append(Finding(
                    "ERROR", "{}:{}".format(rel, line),
                    "DISTANCE() called with {} argument(s); it needs three, the third a literal "
                    "unit. Supported units are 'mi' and 'km' "
                    "(object_reference.txt L2984-L2990).".format(len(args)),
                ))
            else:
                unit = args[2].strip()
                if unit.lower() not in ("'mi'", "'km'", '"mi"', '"km"'):
                    findings.append(Finding(
                        "ERROR", "{}:{}".format(rel, line),
                        "DISTANCE() unit is {}; it must be the literal 'mi' or 'km'. \"Apex bind "
                        "variables aren't supported for the units parameter in the DISTANCE "
                        "function\" (object_reference.txt L2984-L2986).".format(unit or "empty"),
                    ))
                if args[0].upper().startswith("GEOLOCATION"):
                    findings.append(Finding(
                        "ERROR", "{}:{}".format(rel, line),
                        "DISTANCE() operands are reversed. \"The geolocation field must precede "
                        "the latitude and longitude coordinates\" — put the location field first "
                        "and GEOLOCATION second (object_reference.txt L2980-L2983).",
                    ))

            trailing = text[end:end + 8].lstrip()
            if trailing.startswith("==") or trailing.startswith(">=") or \
               trailing.startswith("<=") or (trailing.startswith("=") and
                                             not trailing.startswith("=>")):
                findings.append(Finding(
                    "ERROR", "{}:{}".format(rel, line),
                    "DISTANCE() compared with an equality or inclusive operator. It \"supports "
                    "only the logical operators > and <, returning values within (<) or beyond "
                    "(>) a specified radius\" (object_reference.txt L2979).",
                ))

        # --- compound field as a filter value in WHERE ---
        # Blank out DISTANCE(...) spans first: a compound is a legitimate
        # location operand there (object_reference.txt L2836-L2841).
        masked = blank_out(text, distance_spans)
        for where in re.finditer(r"\bWHERE\b", masked, re.IGNORECASE):
            clause = masked[where.start():where.start() + 600]
            for hit in compound_re.finditer(clause):
                after = clause[hit.end():hit.end() + 6].lstrip()
                if after[:2] in ("!=", "<>", ">=", "<=") or \
                   (after[:1] in ("=", "<", ">") and not after.startswith("=>")) or \
                   re.match(r"(?i)\b(LIKE|IN|NOT|INCLUDES|EXCLUDES)\b", after):
                    findings.append(Finding(
                        "ERROR",
                        "{}:{}".format(rel, line_of(masked, where.start() + hit.start())),
                        "Compound field '{}' used as a filter value in WHERE. \"Address fields "
                        "can't be used in WHERE statements in SOQL. Address fields aren't "
                        "filterable\" — and isFilterable() reports true anyway "
                        "(object_reference.txt L2950-L2951). Filter the components."
                        .format(hit.group(1)),
                    ))
                    break

        # --- DML assignment of a compound ---
        for match in ASSIGN_COMPOUND.finditer(text):
            findings.append(Finding(
                "ERROR", "{}:{}".format(rel, line_of(text, match.start())),
                "Assignment to a compound Address field. \"Compound fields are read-only. To "
                "update field values, modify the individual field components\" "
                "(object_reference.txt L2912-L2913).",
            ))

        name_hits = {}
        for match in ASSIGN_READONLY_NAME.finditer(text):
            name_hits[match.start()] = match.group(0).split(".")[0].strip()

        declared = set(DECLARED_NAME_TYPE.findall(text))
        if declared:
            local_assign = re.compile(
                r"\b(" + "|".join(re.escape(v) for v in sorted(declared)) + r")\.Name\s*=(?!=)")
            for match in local_assign.finditer(text):
                name_hits.setdefault(match.start(), match.group(1))

        for offset in sorted(name_hits):
            findings.append(Finding(
                "ERROR", "{}:{}".format(rel, line_of(text, offset)),
                "Assignment to the compound Name on '{}'. Name is a read-only concatenation on "
                "Contact, Lead, User, and on Person Account records; assign FirstName / "
                "LastName / Salutation instead.".format(name_hits[offset]),
            ))

    return findings


# --------------------------------------------------------------------------

def parse_args():
    parser = argparse.ArgumentParser(
        description="Check a Salesforce source tree for compound-field mistakes.")
    parser.add_argument("--manifest-dir", default=".",
                        help="Root of the metadata / source tree to scan.")
    parser.add_argument("--strict", action="store_true",
                        help="Exit 1 on WARN findings as well as ERROR findings.")
    return parser.parse_args()


def main():
    args = parse_args()
    root = Path(args.manifest_dir)
    if not root.is_dir():
        print("ERROR: directory not found: {}".format(root), file=sys.stderr)
        sys.exit(1)

    metadata_findings, location_fields = check_metadata(root)
    findings = metadata_findings + check_code(root, location_fields)

    order = {"ERROR": 0, "WARN": 1, "INFO": 2}
    findings.sort(key=lambda f: (order[f.severity], f.location))

    errors = sum(1 for f in findings if f.severity == "ERROR")
    warns = sum(1 for f in findings if f.severity == "WARN")
    infos = sum(1 for f in findings if f.severity == "INFO")

    if not findings:
        print("No compound-field issues detected under {}.".format(root))
        sys.exit(0)

    for finding in findings:
        stream = sys.stderr if finding.severity == "ERROR" else sys.stdout
        print(str(finding), file=stream)

    print("\n{} ERROR, {} WARN, {} INFO".format(errors, warns, infos))

    if errors > 0:
        sys.exit(1)
    if args.strict and warns > 0:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
