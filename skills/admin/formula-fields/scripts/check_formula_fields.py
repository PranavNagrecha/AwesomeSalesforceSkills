#!/usr/bin/env python3
"""Review formula field metadata for complexity, correctness, and portability smells.

Usage:
    python3 check_formula_fields.py --manifest-dir force-app/main/default/objects
    python3 check_formula_fields.py path/to/Field__c.field-meta.xml [more paths...]

Scans decomposed DX ``*.field-meta.xml`` files (root ``<CustomField>``). Fields with no
``<formula>`` element are skipped. Stdlib only; exits 1 when any finding is emitted.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


SUFFIX = ".field-meta.xml"
SEVERITY_WEIGHTS = {"CRITICAL": 20, "HIGH": 10, "MEDIUM": 5, "LOW": 1, "REVIEW": 0}

# Return types whose arithmetic is governed by formulaTreatBlanksAs. A blank operand
# behaves differently under BlankAsBlank (result is blank) and BlankAsZero (operand is 0),
# so leaving the element out ships an undeclared default.
NUMERIC_RETURN_TYPES = {"Number", "Currency", "Percent"}
VALID_TREAT_BLANKS = {"BlankAsBlank", "BlankAsZero"}

# Environment-specific merge fields: their values differ between sandbox and production,
# so a formula that branches on them behaves differently after a deploy or a refresh.
ENV_SPECIFIC = (
    ("$Profile", r"\$Profile\b"),
    ("$User.Id", r"\$User\.Id\b"),
    ("$UserRole", r"\$UserRole\b"),
    ("$Setup", r"\$Setup\b"),
)

# One relationship hop in a formula is a "__r." segment (custom) or a standard
# relationship name followed by a dot. Depth is counted per field reference.
HOP_LIMIT = 3
REFERENCE_RE = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*(?:__r)?(?:\.[A-Za-z_][A-Za-z0-9_]*(?:__r|__c)?)+)")
STRING_LITERAL_RE = re.compile(r"\"[^\"]*\"|'[^']*'")


def local_name(tag: str) -> str:
    return tag.split("}", 1)[-1]


def find_child(element: ET.Element, child_name: str) -> ET.Element | None:
    """Return the first child with this local name, or None.

    Never use ``element.find(a) or element.find(b)``: an ElementTree element with no
    children is falsy, so a real element is discarded. Always test ``is not None``.
    """
    for child in element:
        if local_name(child.tag) == child_name:
            return child
    return None


def child_text(element: ET.Element, child_name: str) -> str:
    child = find_child(element, child_name)
    if child is None:
        return ""
    return (child.text or "").strip()


def has_child(element: ET.Element, child_name: str) -> bool:
    return find_child(element, child_name) is not None


def iter_files(paths: list[Path]) -> list[Path]:
    files: list[Path] = []
    for path in paths:
        if path.is_dir():
            files.extend(candidate for candidate in path.rglob(f"*{SUFFIX}") if candidate.is_file())
        elif path.is_file() and path.name.endswith(SUFFIX):
            files.append(path)
    return sorted(set(files))


def normalize_finding(finding: str) -> dict[str, str]:
    severity, _, remainder = finding.partition(" ")
    location = ""
    message = remainder
    if ": " in remainder:
        location, message = remainder.split(": ", 1)
    return {"severity": severity or "INFO", "location": location, "message": message}


def emit_result(findings: list[str], summary: str) -> int:
    normalized = [normalize_finding(finding) for finding in findings]
    score = max(0, 100 - sum(SEVERITY_WEIGHTS.get(item["severity"], 0) for item in normalized))
    print(json.dumps({"score": score, "findings": normalized, "summary": summary}, indent=2))
    if normalized:
        print(f"WARN: {len(normalized)} finding(s) detected", file=sys.stderr)
    return 1 if normalized else 0


def max_relationship_depth(formula: str) -> tuple[int, str]:
    """Return the deepest dotted field reference in the formula and the reference itself.

    Depth is the number of relationship hops, i.e. dots in the reference. String
    literals are stripped first so decimal-free text like "Acme.Inc" is not counted.
    """
    stripped = STRING_LITERAL_RE.sub('""', formula)
    deepest = 0
    deepest_ref = ""
    for match in REFERENCE_RE.finditer(stripped):
        reference = match.group(1)
        hops = reference.count(".")
        if hops > deepest:
            deepest = hops
            deepest_ref = reference
    return deepest, deepest_ref


def audit_field(path: Path) -> list[str]:
    findings: list[str] = []
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as error:
        # Unescaped &, < or " inside <formula> is the usual cause; it fails the deploy
        # before the formula is ever compiled.
        return [f"CRITICAL {path}: file is not well-formed XML ({error})"]

    if local_name(root.tag) != "CustomField":
        return findings

    formula = child_text(root, "formula")
    if not formula:
        return findings

    upper_formula = formula.upper()
    return_type = child_text(root, "type")

    # 1. Undocumented formula: nothing else in the metadata records the business rule.
    if not child_text(root, "description"):
        findings.append(f"MEDIUM {path}: formula field has no <description>; the business rule is unrecorded")

    # 2. Blank handling on numeric return types must be an explicit decision.
    treat_blanks = child_text(root, "formulaTreatBlanksAs")
    if return_type in NUMERIC_RETURN_TYPES and not treat_blanks:
        findings.append(
            f"HIGH {path}: <type>{return_type}</type> formula has no <formulaTreatBlanksAs>; "
            "BlankAsZero and BlankAsBlank give different results for a blank operand"
        )
    elif treat_blanks and treat_blanks not in VALID_TREAT_BLANKS:
        findings.append(
            f"CRITICAL {path}: formulaTreatBlanksAs is '{treat_blanks}'; "
            "only BlankAsBlank and BlankAsZero are valid"
        )

    # 3. Numeric return types need precision and scale to deploy predictably.
    if return_type in NUMERIC_RETURN_TYPES:
        missing = [name for name in ("precision", "scale") if not has_child(root, name)]
        if missing:
            findings.append(
                f"MEDIUM {path}: <type>{return_type}</type> formula is missing {', '.join(missing)}"
            )

    # 4. Environment-specific merge fields behave differently after a refresh or deploy.
    for label, pattern in ENV_SPECIFIC:
        if re.search(pattern, formula, re.IGNORECASE):
            findings.append(
                f"HIGH {path}: formula references {label}, which resolves differently per org/user; "
                "use Custom Permissions or Custom Metadata instead"
            )

    # 5. Relationship traversal depth.
    depth, reference = max_relationship_depth(formula)
    if depth > HOP_LIMIT:
        findings.append(
            f"HIGH {path}: {reference} traverses {depth} relationship hops "
            f"(> {HOP_LIMIT}); add an intermediate formula on the parent object"
        )
    elif depth >= 2:
        findings.append(f"REVIEW {path}: cross-object reference {reference} spans {depth} hops")

    # 6. Existing complexity and decorative-function smells.
    if len(formula) > 3500:
        findings.append(f"REVIEW {path}: formula text is {len(formula)} characters")
    if upper_formula.count("IF(") >= 5:
        findings.append(f"MEDIUM {path}: nested IF usage suggests readability debt")
    if "HYPERLINK(" in upper_formula or "IMAGE(" in upper_formula:
        findings.append(f"REVIEW {path}: decorative formula function in use")

    return findings


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check Salesforce formula field metadata for complexity, correctness, and portability smells."
    )
    parser.add_argument(
        "--manifest-dir",
        type=Path,
        help="Directory to scan recursively for *.field-meta.xml (e.g. force-app/main/default/objects)",
    )
    parser.add_argument("paths", nargs="*", help="Field metadata files or directories")
    args = parser.parse_args()

    targets = [Path(value) for value in args.paths]
    if args.manifest_dir is not None:
        targets.append(args.manifest_dir)
    if not targets:
        parser.error("provide --manifest-dir or at least one path")

    findings: list[str] = []
    files = iter_files(targets)
    if not files:
        return emit_result(
            ["HIGH no custom field metadata files found"],
            "Scanned 0 custom field metadata file(s); no files matched the provided paths.",
        )

    for path in files:
        findings.extend(audit_field(path))

    summary = f"Scanned {len(files)} custom field metadata file(s); {len(findings)} finding(s) detected."
    return emit_result(findings, summary)


if __name__ == "__main__":
    sys.exit(main())
