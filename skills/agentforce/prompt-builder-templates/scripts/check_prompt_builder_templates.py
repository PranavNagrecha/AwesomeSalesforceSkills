#!/usr/bin/env python3
"""Check GenAiPromptTemplate metadata and Apex grounding classes against Prompt Builder rules.

Stdlib only. Point --manifest-dir at a source-format folder (for example force-app/main/default).
Rules encode the Generative AI guide (Spring '26, Prompt Builder chapter) and the Metadata API
Developer Guide (v67.0, GenAiPromptTemplate, EinsteinGptSettings).

Correction (2026-10-03): the previous version of this checker required a permission set with a
"ManagePromptTemplates" user permission and treated any CapabilityType mismatch as a silent
grounding failure. Neither claim was found in a fetched source: access comes from the Prompt
Template Manager and Prompt Template User permission sets, CapabilityType is optional, and the
Flex capability "is no longer needed."

Rules
  PB-XML-01   ERROR  Template file does not parse.
  PB-TYPE-01  ERROR  <type> not one of the documented GenAiPromptTemplate types.
  PB-SIZE-01  ERROR  A version's content exceeds 128,000 characters.
  PB-VERS-01  ERROR  More than 50 versions.
  PB-LIM-01   ERROR  A version exceeds 50 merge fields, 5 Flow, 5 Apex, or 5 related list merge
                     fields, or a Flex template has more than 5 inputs.
  PB-ACT-01   ERROR  activeVersionIdentifier names a version that is missing or not Published.
  PB-ACT-02   WARN   No active version: unavailable to users, and fails deploys when
                     "Deploy Active Prompt Template Versions Only" is on.
  PB-VER-01   WARN   Uses activeVersion or versionNumber, which "will not work in 64.0 and later".
  PB-SYN-01   ERROR  Flow syntax in a prompt body ({!$Record. or {!Flow: without $).
  PB-CAP-01   ERROR  Apex CapabilityType not in the documented list, or set for einstein_gpt__caseEmailDraft.
  PB-CAP-02   WARN   Apex uses CapabilityType=FlexTemplate://, which the guide says to remove.
  PB-APEX-01  ERROR  Apex with a prompt CapabilityType lacks an @InvocableVariable String Prompt response.
  PB-APEX-02  ERROR  Field Generation CapabilityType without a RelatedEntity request variable.

Usage
  python3 check_prompt_builder_templates.py --manifest-dir force-app/main/default [--strict]
  python3 check_prompt_builder_templates.py --self-test

Exit codes: 0 clean (WARN allowed unless --strict); 1 on ERROR, a missing folder, or WARN with --strict.
"""
from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

VALID_TYPES = {"einstein_gpt__fieldCompletion", "einstein_gpt__salesEmail", "einstein_gpt__recordSummary",
               "einstein_gpt__flex", "einstein_gpt__caseEmailDraft"}
VALID_CAPS = {"PromptTemplateType://einstein_gpt__salesEmail", "PromptTemplateType://einstein_gpt__fieldCompletion",
              "PromptTemplateType://einstein_gpt__recordSummary", "PromptTemplateType://einstein_gpt__recordPrioritization"}
MAX_CONTENT, MAX_VERSIONS, MAX_MERGE, MAX_FLOW, MAX_APEX, MAX_RELATED, MAX_FLEX_INPUTS = 128_000, 50, 50, 5, 5, 5, 5
CAP_RE = re.compile(r"""CapabilityType\s*=\s*['"]([^'"]+)['"]""", re.IGNORECASE)


def _local(tag: str) -> str:
    return tag.split("}", 1)[1] if "}" in tag else tag


def _kids(el: ET.Element, name: str) -> list[ET.Element]:
    return [c for c in el if _local(c.tag) == name]


def _text(el: ET.Element, name: str) -> str | None:
    found = _kids(el, name)
    return (found[0].text or "").strip() if found else None


def strip_comments(text: str) -> str:
    """Remove // and /* */ comments outside single-quoted Apex string literals."""
    out: list[str] = []
    i, n, in_string = 0, len(text), False
    while i < n:
        ch = text[i]
        if in_string:
            out.append(ch)
            if ch == "\\" and i + 1 < n:
                out.append(text[i + 1])
                i += 2
                continue
            in_string = ch != "'"
            i += 1
        elif ch == "'":
            in_string = True
            out.append(ch)
            i += 1
        elif text.startswith("//", i):
            end = text.find("\n", i)
            i = n if end == -1 else end
        elif text.startswith("/*", i):
            end = text.find("*/", i + 2)
            out.append(" ")
            i = n if end == -1 else end + 2
        else:
            out.append(ch)
            i += 1
    return "".join(out)


def check_template(path: Path) -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        return [("ERROR", "PB-XML-01", f"{path}: does not parse ({exc}).")]
    ttype = _text(root, "type") or ""
    if ttype not in VALID_TYPES:
        out.append(("ERROR", "PB-TYPE-01", f"{path}: type '{ttype}' is not a documented GenAiPromptTemplate type."))
    if _text(root, "activeVersion") is not None:
        out.append(("WARN", "PB-VER-01", f"{path}: activeVersion will not work in 64.0 and later; use activeVersionIdentifier."))
    versions = _kids(root, "templateVersions")
    if len(versions) > MAX_VERSIONS:
        out.append(("ERROR", "PB-VERS-01", f"{path}: {len(versions)} versions; the limit is 50."))
    by_id: dict[str, str] = {}
    for idx, version in enumerate(versions, start=1):
        label = _text(version, "versionIdentifier") or f"version {idx}"
        if _text(version, "versionNumber") is not None:
            out.append(("WARN", "PB-VER-01", f"{path}: {label} uses versionNumber; use versionIdentifier (64.0+)."))
        content = _text(version, "content") or ""
        if len(content) > MAX_CONTENT:
            out.append(("ERROR", "PB-SIZE-01", f"{path}: {label} content is {len(content)} characters; the limit is 128,000."))
        merges = re.findall(r"\{!\$?[^}]*\}", content)
        flows = [m for m in merges if m.startswith("{!$Flow:")]
        apex = [m for m in merges if m.startswith("{!$Apex:")]
        related = [m for m in merges if m.startswith("{!$RelatedList:")]
        for count, limit, kind in ((len(merges), MAX_MERGE, "merge fields"), (len(flows), MAX_FLOW, "Flow merge fields"),
                                   (len(apex), MAX_APEX, "Apex merge fields"), (len(related), MAX_RELATED, "related list merge fields")):
            if count > limit:
                out.append(("ERROR", "PB-LIM-01", f"{path}: {label} has {count} {kind}; the limit is {limit}."))
        inputs = _kids(version, "inputs")
        if ttype == "einstein_gpt__flex" and len(inputs) > MAX_FLEX_INPUTS:
            out.append(("ERROR", "PB-LIM-01", f"{path}: {label} has {len(inputs)} Flex inputs; the limit is 5."))
        if re.search(r"\{!\$Record\.|\{!Flow:", content):
            out.append(("ERROR", "PB-SYN-01",
                        f"{path}: {label} uses Flow syntax; record merge fields are {{!$Input:Object.Field}} and flow fields {{!$Flow:Name.Prompt}}."))
        vid = _text(version, "versionIdentifier")
        if vid:
            by_id[vid] = _text(version, "status") or ""
    active = _text(root, "activeVersionIdentifier")
    if active:
        if active not in by_id:
            out.append(("ERROR", "PB-ACT-01", f"{path}: activeVersionIdentifier '{active}' matches no version."))
        elif by_id[active] != "Published":
            out.append(("ERROR", "PB-ACT-01", f"{path}: active version '{active}' must be Published (found '{by_id[active]}')."))
    elif _text(root, "activeVersion") is None:
        out.append(("WARN", "PB-ACT-02",
                    f"{path}: no active version; users can't run it, and active-only deploys fail on it."))
    return out


def check_apex(path: Path) -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    text = strip_comments(path.read_text(encoding="utf-8", errors="replace"))
    for cap in CAP_RE.findall(text):
        if cap.startswith("FlexTemplate://"):
            out.append(("WARN", "PB-CAP-02", f"{path}: CapabilityType {cap}; the Flex capability is no longer needed, remove it."))
        elif "einstein_gpt__caseEmailDraft" in cap:
            out.append(("ERROR", "PB-CAP-01", f"{path}: don't specify a CapabilityType for einstein_gpt__caseEmailDraft."))
        elif cap not in VALID_CAPS:
            out.append(("ERROR", "PB-CAP-01", f"{path}: CapabilityType '{cap}' is not in the documented list."))
            continue
        if not re.search(r"@InvocableVariable[^;{]*?\s+public\s+String\s+Prompt\s*;", text, flags=re.IGNORECASE):
            out.append(("ERROR", "PB-APEX-01", f"{path}: needs a Response class with an @InvocableVariable String Prompt."))
        if cap.endswith("einstein_gpt__fieldCompletion") and not re.search(
                r"@InvocableVariable[^;{]*?\s+public\s+\w+\s+RelatedEntity\s*;", text, flags=re.IGNORECASE):
            out.append(("ERROR", "PB-APEX-02", f"{path}: Field Generation CapabilityType requires a RelatedEntity request variable."))
    return out


def scan(root: Path) -> tuple[int, list[tuple[str, str, str]]]:
    templates = sorted(p for p in root.rglob("*") if p.is_file() and ".genAiPromptTemplate" in p.name)
    classes = sorted(p for p in root.rglob("*.cls") if p.is_file())
    grounding = [c for c in classes if CAP_RE.search(c.read_text(encoding="utf-8", errors="replace"))]
    findings: list[tuple[str, str, str]] = []
    for path in templates:
        findings.extend(check_template(path))
    for path in grounding:
        findings.extend(check_apex(path))
    return len(templates) + len(grounding), findings


def self_test() -> int:
    import tempfile
    here = Path(__file__).resolve().parent
    _, good = scan(here / "fixtures" / "good")
    _, bad = scan(here / "fixtures" / "bad")
    # The size fixture is generated here rather than stored (128,001 characters).
    flows = " ".join("{!$Flow:F%d.Prompt}" % i for i in range(6))
    big = ('<?xml version="1.0" encoding="UTF-8"?>\n'
           '<GenAiPromptTemplate xmlns="http://soap.sforce.com/2006/04/metadata">'
           f"<masterLabel>Too Big</masterLabel><templateVersions><content>{flows} {'x' * 128001}</content>"
           "<status>Draft</status></templateVersions><type>einstein_gpt__flex</type>"
           "<visibility>Global</visibility></GenAiPromptTemplate>")
    with tempfile.TemporaryDirectory() as tmp:
        target = Path(tmp) / "Too_Big.genAiPromptTemplate-meta.xml"
        target.write_text(big, encoding="utf-8")
        bad.extend(check_template(target))
    expected = {"PB-XML-01", "PB-TYPE-01", "PB-SIZE-01", "PB-LIM-01", "PB-ACT-01", "PB-ACT-02", "PB-VER-01",
                "PB-SYN-01", "PB-CAP-01", "PB-CAP-02", "PB-APEX-01", "PB-APEX-02"}
    seen = {rule for _, rule, _ in bad}
    md = (here.parent / "references" / "metadata-examples.md").read_text(encoding="utf-8")
    own: list[tuple[str, str, str]] = []
    with tempfile.TemporaryDirectory() as tmp:
        for i, block in enumerate(re.findall(r"```apex\n(.*?)```", md, flags=re.DOTALL)):
            (Path(tmp) / f"Example{i}.cls").write_text(block, encoding="utf-8")
        for i, block in enumerate(re.findall(r"```xml\n(.*?)```", md, flags=re.DOTALL)):
            if "<GenAiPromptTemplate" in block:
                (Path(tmp) / f"Example{i}.genAiPromptTemplate-meta.xml").write_text(block, encoding="utf-8")
        _, own = scan(Path(tmp))
    own_errors = [f for f in own if f[0] == "ERROR"]
    ok = not good and expected <= seen and not own_errors
    print(f"good fixtures: {len(good)} finding(s) (expected 0)")
    for f in good:
        print("   ", *f)
    print(f"bad fixtures: rules seen {sorted(seen)}; missing {sorted(expected - seen)}")
    print(f"skill examples: {len(own_errors)} ERROR(s) (expected 0); {len(own)} finding(s) total")
    for f in own:
        print("   ", *f)
    print("SELF-TEST", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description="Check GenAiPromptTemplate metadata and Apex grounding classes.")
    ap.add_argument("--manifest-dir", default=".", help="Source folder to scan (default: current directory).")
    ap.add_argument("--strict", action="store_true", help="Treat WARN findings as failures.")
    ap.add_argument("--self-test", action="store_true", help="Run the bundled fixtures and exit.")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    root = Path(args.manifest_dir)
    if not root.is_dir():
        print(f"ERROR: manifest directory not found: {root}")
        sys.exit(1)
    count, findings = scan(root)
    if count == 0:
        print(f"WARN: no GenAiPromptTemplate files or prompt-grounding Apex found under {root}; nothing checked.")
        return 0
    for severity, rule, message in findings:
        print(f"{severity} {rule}: {message}")
    errors = sum(1 for f in findings if f[0] == "ERROR")
    warns = sum(1 for f in findings if f[0] == "WARN")
    print(f"Checked {count} file(s): {errors} error(s), {warns} warning(s).")
    return 1 if errors or (args.strict and warns) else 0


if __name__ == "__main__":
    sys.exit(main())
