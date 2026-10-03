#!/usr/bin/env python3
"""Check CRM Analytics XMD files and External Data API metadata JSON before you upload or deploy.

Stdlib only. Scans a folder for:
  * WaveXmd metadata files (*.xmd, *.xmd-meta.xml)       -> XMD-* rules
  * XMD JSON documents (JSON with dimensions/measures/dates at top level) -> XMD-* rules
  * External Data API metadata JSON (JSON with fileFormat or objects[].fields) -> EXT-* rules

Rules and the source each one encodes (Summer '26 guides):
  XMD-PARSE-01  ERROR  File does not parse (the Metadata API WaveXmd sample itself opens <dimesions>).
  XMD-EMPTY-01  ERROR  Empty string in an XMD document. XMD guide: "XMD doesn't support empty strings."
  XMD-REQ-01    ERROR  WaveXmd missing a required element: dataset; field/isDerived/sortIndex on
                       dimensions and measures; member/sortIndex on members (Metadata API, WaveXmd).
  XMD-DUP-01    WARN   Same field listed twice in dimensions or measures; the later entry is ambiguous.
  XMD-HIDE-01   WARN   A sensitive-looking field is hidden. XMD guide: hidden fields remain reachable
                       in dashboard JSON, SAQL, and the REST API.
  EXT-PARSE-01  ERROR  External metadata JSON does not parse (the guide's own sample is missing commas).
  EXT-NUM-01    ERROR  Numeric field without defaultValue. "All numeric types require a default value."
  EXT-NUM-02    ERROR  Numeric precision above 18, or scale not less than precision.
  EXT-DATE-01   ERROR  Date field without format (format is required for Date values).
  EXT-UID-01    ERROR  More than one isUniqueId field, or a non-Text unique ID.
  EXT-NAME-01   ERROR  Field or object name breaks the Field Name Restrictions.
  EXT-LINES-01  WARN   fileFormat.numberOfLinesToIgnore not set; header-less CSVs lose the first row
                       of every part when it is not 0.
  EXT-ORDER-01  ERROR  A sibling CSV's header does not match the metadata fields order ("The fields
                       must be in the same order as the CSV columns are in").

Usage
  python3 check_analytics_data_preparation.py --manifest-dir path/to/folder [--strict]
  python3 check_analytics_data_preparation.py --self-test

Exit codes: 0 clean (WARN allowed unless --strict); 1 on any ERROR, a missing folder, or WARN with --strict.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

NAME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")
SENSITIVE_RE = re.compile(r"(ssn|social|salary|tax_?id|dob|birth|passport|credit_?card)", re.IGNORECASE)
XMD_KEYS = {"dimensions", "measures", "dates", "derivedDimensions", "derivedMeasures"}


def _local(tag: str) -> str:
    return tag.split("}", 1)[1] if "}" in tag else tag


def _child_text(el: ET.Element, name: str) -> str | None:
    for child in el:
        if _local(child.tag) == name:
            return (child.text or "").strip()
    return None


def valid_name(name: str) -> bool:
    if not NAME_RE.match(name) or name.endswith("_"):
        return False
    core = name[:-3] if name.endswith("__c") else name
    return "__" not in core


def check_wavexmd(path: Path) -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        return [("ERROR", "XMD-PARSE-01", f"{path}: WaveXmd does not parse ({exc}).")]
    if _child_text(root, "dataset") in (None, ""):
        out.append(("ERROR", "XMD-REQ-01", f"{path}: WaveXmd requires <dataset>."))
    for section in ("dimensions", "measures"):
        seen: set[str] = set()
        for entry in (c for c in root if _local(c.tag) == section):
            field = _child_text(entry, "field")
            for req in ("field", "isDerived", "sortIndex"):
                if _child_text(entry, req) in (None, ""):
                    out.append(("ERROR", "XMD-REQ-01", f"{path}: <{section}> entry {field or '?'} missing <{req}>."))
            if field:
                if field in seen:
                    out.append(("WARN", "XMD-DUP-01", f"{path}: {field} listed twice in <{section}>."))
                seen.add(field)
                if _child_text(entry, "showInExplorer") == "false" and SENSITIVE_RE.search(field):
                    out.append(("WARN", "XMD-HIDE-01",
                                f"{path}: {field} is hidden; hidden fields stay reachable in SAQL and REST."))
            for member in (c for c in entry if _local(c.tag) == "members"):
                for req in ("member", "sortIndex"):
                    if _child_text(member, req) in (None, ""):
                        out.append(("ERROR", "XMD-REQ-01", f"{path}: member of {field or '?'} missing <{req}>."))
    for el in root.iter():
        if el is root or len(el) or el.attrib:
            continue  # containers and xsi:nil elements are not empty strings
        if (el.text or "").strip() == "":
            out.append(("ERROR", "XMD-EMPTY-01", f"{path}: <{_local(el.tag)}> is an empty string."))
    return out


def _walk_empty(obj, trail: str, found: list[str]) -> None:
    if isinstance(obj, dict):
        for key, value in obj.items():
            _walk_empty(value, f"{trail}.{key}", found)
    elif isinstance(obj, list):
        for i, value in enumerate(obj):
            _walk_empty(value, f"{trail}[{i}]", found)
    elif obj == "":
        found.append(trail)


def check_xmd_json(path: Path, doc: dict) -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    empties: list[str] = []
    _walk_empty({k: v for k, v in doc.items() if k != "dataset"}, "$", empties)
    for trail in empties:
        out.append(("ERROR", "XMD-EMPTY-01", f"{path}: empty string at {trail}; XMD doesn't support empty strings."))
    for section in ("dimensions", "measures"):
        seen: set[str] = set()
        for entry in doc.get(section) or []:
            field = entry.get("field") if isinstance(entry, dict) else None
            if not field:
                continue
            if field in seen:
                out.append(("WARN", "XMD-DUP-01", f"{path}: {field} listed twice in {section}."))
            seen.add(field)
            if entry.get("showInExplorer") is False and SENSITIVE_RE.search(field):
                out.append(("WARN", "XMD-HIDE-01",
                            f"{path}: {field} is hidden; hidden fields stay reachable in SAQL and REST."))
    return out


def check_external_metadata(path: Path, doc: dict) -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    file_format = doc.get("fileFormat") or {}
    if "numberOfLinesToIgnore" not in file_format:
        out.append(("WARN", "EXT-LINES-01",
                    f"{path}: set fileFormat.numberOfLinesToIgnore (1 with a header row, 0 without)."))
    for obj in doc.get("objects") or []:
        oname = obj.get("name", "")
        if oname and not valid_name(oname):
            out.append(("ERROR", "EXT-NAME-01", f"{path}: object name '{oname}' breaks the name restrictions."))
        fields = obj.get("fields") or []
        unique = [f for f in fields if f.get("isUniqueId") is True]
        if len(unique) > 1:
            out.append(("ERROR", "EXT-UID-01",
                        f"{path}: {len(unique)} fields set isUniqueId; only one field can be the unique ID."))
        for f in fields:
            name = f.get("name", "")
            ftype = f.get("type", "")
            if name and not valid_name(name):
                out.append(("ERROR", "EXT-NAME-01", f"{path}: field name '{name}' breaks the name restrictions."))
            if f.get("isUniqueId") is True and ftype != "Text":
                out.append(("ERROR", "EXT-UID-01", f"{path}: {name} is {ftype}; only Text fields can be unique IDs."))
            if ftype == "Numeric":
                if "defaultValue" not in f:
                    out.append(("ERROR", "EXT-NUM-01", f"{path}: Numeric field {name} needs a defaultValue."))
                precision, scale = f.get("precision"), f.get("scale")
                if not isinstance(precision, int) or not isinstance(scale, int):
                    out.append(("ERROR", "EXT-NUM-02", f"{path}: Numeric field {name} needs integer precision and scale."))
                elif precision > 18 or scale >= precision:
                    out.append(("ERROR", "EXT-NUM-02",
                                f"{path}: {name} precision {precision} / scale {scale}; precision max 18, scale < precision."))
            if ftype == "Date" and not f.get("format"):
                out.append(("ERROR", "EXT-DATE-01", f"{path}: Date field {name} needs a format."))
        out.extend(check_csv_order(path, file_format, fields))
    return out


def check_csv_order(meta_path: Path, file_format: dict, fields: list[dict]) -> list[tuple[str, str, str]]:
    stem = meta_path.name.split(".")[0]
    csv_path = meta_path.with_name(f"{stem}.csv")
    if not csv_path.exists() or file_format.get("numberOfLinesToIgnore") == 0:
        return []
    with csv_path.open(newline="", encoding="utf-8") as handle:
        header = next(csv.reader(handle, delimiter=file_format.get("fieldsDelimitedBy", ",")), [])
    expected = [f.get("name", "") for f in fields]
    if [h.strip() for h in header] != expected:
        return [("ERROR", "EXT-ORDER-01",
                 f"{meta_path}: CSV header {header} does not match metadata field order {expected}.")]
    return []


def classify_and_check(path: Path) -> list[tuple[str, str, str]]:
    if path.name.endswith((".xmd", ".xmd-meta.xml")):
        return check_wavexmd(path)
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        text = path.read_text(encoding="utf-8", errors="replace")
        rule = "EXT-PARSE-01" if "fileFormat" in text or "fieldsDelimitedBy" in text else "XMD-PARSE-01"
        return [("ERROR", rule, f"{path}: JSON does not parse ({exc}).")]
    if not isinstance(doc, dict):
        return []
    if "fileFormat" in doc or any(isinstance(o, dict) and "fields" in o for o in doc.get("objects") or []):
        return check_external_metadata(path, doc)
    if XMD_KEYS & set(doc):
        return check_xmd_json(path, doc)
    return []


def scan(root: Path) -> tuple[int, list[tuple[str, str, str]]]:
    files = sorted(p for p in root.rglob("*") if p.is_file()
                   and (p.name.endswith((".xmd", ".xmd-meta.xml", ".json"))))
    findings: list[tuple[str, str, str]] = []
    checked = 0
    for path in files:
        result = classify_and_check(path)
        if result or path.name.endswith((".xmd", ".xmd-meta.xml")) or _is_relevant_json(path):
            checked += 1
        findings.extend(result)
    return checked, findings


def _is_relevant_json(path: Path) -> bool:
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return True
    return isinstance(doc, dict) and bool(XMD_KEYS & set(doc) or "fileFormat" in doc or "objects" in doc)


def _fences(md: Path, lang: str) -> list[str]:
    return re.findall(rf"```{lang}\n(.*?)```", md.read_text(encoding="utf-8"), flags=re.DOTALL)


def self_test() -> int:
    import tempfile
    here = Path(__file__).resolve().parent
    _, good = scan(here / "fixtures" / "good")
    _, bad = scan(here / "fixtures" / "bad")
    expected = {"XMD-PARSE-01", "XMD-EMPTY-01", "XMD-REQ-01", "XMD-DUP-01", "XMD-HIDE-01",
                "EXT-PARSE-01", "EXT-NUM-01", "EXT-NUM-02", "EXT-DATE-01", "EXT-UID-01",
                "EXT-NAME-01", "EXT-LINES-01", "EXT-ORDER-01"}
    seen = {rule for _, rule, _ in bad}
    refs = here.parent / "references"
    own: list[tuple[str, str, str]] = []
    with tempfile.TemporaryDirectory() as tmp:
        for i, block in enumerate(_fences(refs / "examples.md", "json")):
            target = Path(tmp) / f"example{i + 1}.json"
            target.write_text(block, encoding="utf-8")
            own.extend(classify_and_check(target))
        for i, block in enumerate(_fences(refs / "metadata-examples.md", "xml")):
            if "<WaveXmd" in block:
                target = Path(tmp) / f"example{i + 1}.xmd"
                target.write_text(block, encoding="utf-8")
                own.extend(classify_and_check(target))
    own_errors = [f for f in own if f[0] == "ERROR"]
    ok = not good and expected <= seen and not own_errors
    print(f"good fixtures: {len(good)} finding(s) (expected 0)")
    for f in good:
        print("   ", *f)
    print(f"bad fixtures: rules seen {sorted(seen)}; missing {sorted(expected - seen)}")
    print(f"skill examples: {len(own_errors)} ERROR(s) (expected 0)")
    for f in own:
        print("   ", *f)
    print("SELF-TEST", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description="Check CRM Analytics XMD and External Data API metadata files.")
    ap.add_argument("--manifest-dir", default=".", help="Folder to scan recursively (default: current directory).")
    ap.add_argument("--strict", action="store_true", help="Treat WARN findings as failures.")
    ap.add_argument("--self-test", action="store_true", help="Run the bundled fixtures and exit.")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    root = Path(args.manifest_dir)
    if not root.is_dir():
        print(f"ERROR: manifest directory not found: {root}")
        sys.exit(1)
    checked, findings = scan(root)
    if checked == 0:
        print(f"WARN: no WaveXmd, XMD JSON, or external metadata JSON found under {root}; nothing checked.")
        return 0
    for severity, rule, message in findings:
        print(f"{severity} {rule}: {message}")
    errors = sum(1 for f in findings if f[0] == "ERROR")
    warns = sum(1 for f in findings if f[0] == "WARN")
    print(f"Checked {checked} file(s): {errors} error(s), {warns} warning(s).")
    return 1 if errors or (args.strict and warns) else 0


if __name__ == "__main__":
    sys.exit(main())
