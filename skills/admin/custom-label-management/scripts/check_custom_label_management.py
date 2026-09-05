#!/usr/bin/env python3
"""Checker script for the Custom Label Management skill.

Two families of checks over a Salesforce DX metadata tree:

1. The ``CustomLabels`` file itself (``labels/*.labels-meta.xml`` or
   ``labels/*.labels``) against the Metadata API ``CustomLabel`` field table
   (Metadata API Developer Guide, ``api_meta.txt:41187-41221``):
     - duplicate ``fullName``                                   ERROR
     - ``value`` over 1000 characters                           ERROR
       ("Required. The translated custom label. Maximum of 1000
        characters", ``api_meta.txt:41219-41220``)
     - ``categories`` over 255 characters                       ERROR
       ("Maximum of 255 characters", ``api_meta.txt:41191-41193``)
     - missing Required child element                           ERROR
     - empty or missing ``shortDescription``                    WARN
     - semicolon-separated ``categories``                       WARN
       (the guide defines the field as "A comma-separated list")
     - label with no ``categories`` while siblings have them    INFO

2. Cross-references between the labels file and the code that consumes it:
     - ``System.Label.X`` / ``@salesforce/label/c.X`` / ``$Label.X``
       referencing a label the file does not define                 WARN
     - a defined label referenced nowhere in the tree                INFO

Plus the original anti-pattern scans (hard-coded ``addError`` strings, prose in
LWC templates, a parallel ``Map<String,String>`` label mechanism), which stay
WARN because they are heuristics.

Exit code: 1 if any ERROR is reported (or the directory is unreadable), else 0.
WARN and INFO findings are printed but do not fail the run.

Usage:
    python3 check_custom_label_management.py [--manifest-dir path/to/metadata]
                                             [--fail-on-warn]
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

MDNS = "{http://soap.sforce.com/2006/04/metadata}"

# Metadata API Developer Guide, CustomLabel field table (api_meta.txt:41187-41221).
VALUE_MAX = 1000
CATEGORIES_MAX = 255
REQUIRED_CHILDREN = ("fullName", "value", "language", "protected", "shortDescription")

ADDERROR_LITERAL = re.compile(r"\.addError\(\s*'[^']{3,}'")
LWC_PROSE = re.compile(r">\s*[A-Z][a-z]+(?:\s+[A-Za-z]+){2,}\s*<")
LABEL_IN_MAP = re.compile(r"Map<String\s*,\s*String>\s+labels\b", re.IGNORECASE)

# Consumer reference forms.
APEX_LABEL_REF = re.compile(r"\bSystem\.Label\.([A-Za-z_][A-Za-z0-9_]*)")
LWC_LABEL_REF = re.compile(r"@salesforce/label/(?:[A-Za-z0-9_]+)\.([A-Za-z_][A-Za-z0-9_]*)")
MERGE_LABEL_REF = re.compile(r"\$Label\.([A-Za-z_][A-Za-z0-9_]*)")

CODE_SUFFIXES = (".cls", ".trigger", ".js", ".html", ".xml", ".page", ".cmp", ".apex")

ERROR, WARN, INFO = "ERROR", "WARN", "INFO"


class Finding:
    __slots__ = ("severity", "where", "message")

    def __init__(self, severity: str, where: str, message: str) -> None:
        self.severity = severity
        self.where = where
        self.message = message

    def __str__(self) -> str:
        return f"{self.severity}: {self.where}: {self.message}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Lint a CustomLabels file and its consumers in a DX metadata tree."
    )
    parser.add_argument("--manifest-dir", default=".", help="Root directory of metadata.")
    parser.add_argument(
        "--fail-on-warn",
        action="store_true",
        help="Exit 1 on WARN findings as well as ERROR findings.",
    )
    return parser.parse_args()


def child_text(element: ET.Element, tag: str) -> str | None:
    """Return the text of a direct child, namespace-agnostic.

    Never rely on the truthiness of an Element: a leaf Element with no children
    is falsy, so `el.find(a) or el.find(b)` silently discards a real match.
    """
    for candidate in (f"{MDNS}{tag}", tag):
        found = element.find(candidate)
        if found is not None:
            return (found.text or "").strip()
    return None


def iter_files(root: Path, suffixes: tuple[str, ...]):
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.suffix in suffixes:
            yield path


def find_label_files(root: Path) -> list[Path]:
    """Locate CustomLabels files: labels/*.labels-meta.xml or labels/*.labels."""
    found: list[Path] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        name = path.name
        if name.endswith(".labels-meta.xml") or name.endswith(".labels"):
            found.append(path)
    return found


def parse_labels(path: Path, root: Path, findings: list[Finding]) -> dict[str, dict]:
    """Return {fullName: {value, categories, shortDescription, line-ish index}}."""
    rel = str(path.relative_to(root))
    labels: dict[str, dict] = {}
    try:
        tree = ET.parse(str(path))
    except (ET.ParseError, OSError) as exc:
        findings.append(Finding(ERROR, rel, f"could not parse as XML: {exc}"))
        return labels

    root_el = tree.getroot()
    entries = root_el.findall(f"{MDNS}labels") or root_el.findall("labels")
    if not entries:
        findings.append(Finding(WARN, rel, "no <labels> elements found in this file"))
        return labels

    for index, entry in enumerate(entries, start=1):
        full_name = child_text(entry, "fullName")
        where = f"{rel} (<labels> #{index})"
        if not full_name:
            findings.append(
                Finding(ERROR, where, "missing required <fullName> (api_meta.txt:41195-41199)")
            )
            continue
        where = f"{rel} [{full_name}]"

        if full_name in labels:
            findings.append(
                Finding(
                    ERROR,
                    where,
                    "duplicate <fullName>; a CustomLabels file must define each label once",
                )
            )

        for tag in REQUIRED_CHILDREN:
            if child_text(entry, tag) is None:
                findings.append(
                    Finding(
                        ERROR,
                        where,
                        f"missing required <{tag}> (Metadata API CustomLabel field table, "
                        "api_meta.txt:41190-41221)",
                    )
                )

        value = child_text(entry, "value") or ""
        if len(value) > VALUE_MAX:
            findings.append(
                Finding(
                    ERROR,
                    where,
                    f"<value> is {len(value)} characters; the maximum is {VALUE_MAX} "
                    "(api_meta.txt:41219-41220)",
                )
            )

        categories = child_text(entry, "categories")
        if categories is not None and len(categories) > CATEGORIES_MAX:
            findings.append(
                Finding(
                    ERROR,
                    where,
                    f"<categories> is {len(categories)} characters; the maximum is "
                    f"{CATEGORIES_MAX} (api_meta.txt:41191-41193)",
                )
            )
        if categories and ";" in categories:
            findings.append(
                Finding(
                    WARN,
                    where,
                    "<categories> uses ';'; the guide defines it as a comma-separated list, "
                    "and list-view filters will not split on a semicolon "
                    "(api_meta.txt:41191-41193)",
                )
            )

        short_description = child_text(entry, "shortDescription")
        if short_description is not None and not short_description:
            findings.append(
                Finding(
                    WARN,
                    where,
                    "<shortDescription> is empty; it is the only context a translator gets",
                )
            )

        labels[full_name] = {
            "value": value,
            "categories": categories,
            "shortDescription": short_description,
            "file": rel,
        }

    categorised = sum(1 for meta in labels.values() if meta["categories"])
    if categorised and categorised < len(labels):
        for name, meta in labels.items():
            if not meta["categories"]:
                findings.append(
                    Finding(
                        INFO,
                        f"{meta['file']} [{name}]",
                        f"no <categories> while {categorised} of {len(labels)} sibling labels "
                        "have them; it will be invisible to category-filtered list views",
                    )
                )
    return labels


def collect_references(root: Path, label_files: set[Path]) -> dict[str, list[str]]:
    """Map referenced label name -> list of 'file:line' sites."""
    refs: dict[str, list[str]] = {}
    for path in iter_files(root, CODE_SUFFIXES):
        if path in label_files:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        rel = str(path.relative_to(root))
        for pattern in (APEX_LABEL_REF, LWC_LABEL_REF, MERGE_LABEL_REF):
            for match in pattern.finditer(text):
                name = match.group(1)
                line_no = text[: match.start()].count("\n") + 1
                refs.setdefault(name, []).append(f"{rel}:{line_no}")
    return refs


def check_cross_references(
    labels: dict[str, dict], refs: dict[str, list[str]], findings: list[Finding]
) -> None:
    for name, sites in sorted(refs.items()):
        if name not in labels:
            findings.append(
                Finding(
                    WARN,
                    sites[0],
                    f"references label '{name}' which is not defined in any CustomLabels file "
                    f"in this tree ({len(sites)} site(s)); Apex resolves System.Label at compile "
                    "time, so the label must ship in the same deployment payload",
                )
            )
    for name, meta in sorted(labels.items()):
        if name not in refs:
            findings.append(
                Finding(
                    INFO,
                    f"{meta['file']} [{name}]",
                    "defined but referenced nowhere in this tree; confirm it is consumed by "
                    "metadata outside this directory before deleting it",
                )
            )


def check_addError_literals(root: Path, findings: list[Finding]) -> None:
    for path in iter_files(root, (".cls", ".trigger")):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for match in ADDERROR_LITERAL.finditer(text):
            line_no = text[: match.start()].count("\n") + 1
            findings.append(
                Finding(
                    WARN,
                    f"{path.relative_to(root)}:{line_no}",
                    "addError with a hard-coded string; use System.Label so the message is "
                    "translatable",
                )
            )


def check_lwc_prose(root: Path, findings: list[Finding]) -> None:
    lwc_dir = root / "lwc"
    if not lwc_dir.is_dir():
        return
    for comp in sorted(lwc_dir.iterdir()):
        if not comp.is_dir():
            continue
        for path in sorted(comp.glob("*.html")):
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            if LWC_PROSE.search(text):
                findings.append(
                    Finding(
                        WARN,
                        str(path.relative_to(root)),
                        "prose text in template; consider an @salesforce/label import",
                    )
                )


def check_parallel_label_map(root: Path, findings: list[Finding]) -> None:
    for path in iter_files(root, (".cls",)):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if LABEL_IN_MAP.search(text):
            findings.append(
                Finding(
                    WARN,
                    str(path.relative_to(root)),
                    "parallel Map<String,String> labels; use System.Label instead so "
                    "Translation Workbench and dependency tooling can see the strings",
                )
            )


def main() -> int:
    args = parse_args()
    root = Path(args.manifest_dir)
    if not root.is_dir():
        print(f"ERROR: directory not found: {root}", file=sys.stderr)
        return 1

    findings: list[Finding] = []

    label_files = find_label_files(root)
    labels: dict[str, dict] = {}
    if not label_files:
        findings.append(
            Finding(
                INFO,
                str(root),
                "no labels/*.labels-meta.xml file found; skipping CustomLabels checks",
            )
        )
    else:
        for path in label_files:
            labels.update(parse_labels(path, root, findings))

    refs = collect_references(root, set(label_files))
    if label_files:
        check_cross_references(labels, refs, findings)

    check_addError_literals(root, findings)
    check_lwc_prose(root, findings)
    check_parallel_label_map(root, findings)

    errors = [f for f in findings if f.severity == ERROR]
    warns = [f for f in findings if f.severity == WARN]
    infos = [f for f in findings if f.severity == INFO]

    for finding in errors + warns:
        print(str(finding), file=sys.stderr)
    for finding in infos:
        print(str(finding))

    print(
        f"\n{len(labels)} label(s) defined, {len(refs)} label name(s) referenced; "
        f"{len(errors)} ERROR, {len(warns)} WARN, {len(infos)} INFO."
    )

    if errors:
        return 1
    if warns and args.fail_on_warn:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
