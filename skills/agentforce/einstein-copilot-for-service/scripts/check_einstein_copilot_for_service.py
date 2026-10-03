#!/usr/bin/env python3
"""Check Einstein for Service settings metadata (Case Classification, Article and Reply Recommendations).

Stdlib only. Point --manifest-dir at a source-format folder (for example force-app/main/default)
plus any manifest folder. Rules encode the Metadata API Developer Guide v67.0 (EinsteinAgentSettings,
AIReplyRecommendationsSettings, ServiceAISetupDefinition, ServiceAISetupField, ExternalAIModel).

Correction (2026-10-03): the previous version of this checker required permission sets named
ServiceCloudEinsteinUser, EinsteinForServiceUser, or EinsteinCaseClassification and layout
components with guessed names. No fetched source documents those names, so those rules are gone.

Rules
  ES-XML-01    ERROR  A settings or setup file does not parse.
  ES-CLS-01    WARN   einsteinAgentRecommendations is true but runAssignmentRules and reRunAttributeBasedRules
                      are both off (both default false), so classified values don't re-route cases.
  ES-CLS-02    WARN   A CaseClassification settings file (renamed to EinsteinAgentSettings in API 52.0).
  ES-REPLY-01  WARN   enableGenReplyRecommendations is true while enableServiceEinsteinGPTGrounding is false.
  ES-ART-01    ERROR  ServiceAISetupDefinition for ARTICLE_RECOMMENDATION has no supportedLanguages (required).
  ES-ART-02    ERROR  ServiceAISetupField maps CASE_* types to a non-Case entity or ARTICLE_* types to Case,
                      has a fieldPosition below 1, or repeats a position within one setup definition.
  ES-ART-03    WARN   ServiceAISetupDefinition setupStatus is RETIRED or ARCHIVED in a deployment.
  ES-MODEL-01  ERROR  package.xml uses a wildcard member for ExternalAIModel, which doesn't support it.
  ES-MODEL-02  WARN   ExternalAIModel externalModelStatus is PAUSED or DISABLED.

Usage
  python3 check_einstein_copilot_for_service.py --manifest-dir force-app/main/default [--strict]
  python3 check_einstein_copilot_for_service.py --self-test

Exit codes: 0 clean (WARN allowed unless --strict); 1 on ERROR, a missing folder, or WARN with --strict.
"""
from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

CASE_TYPES = {"CASE_DESC", "CASE_SUBJ"}
ARTICLE_TYPES = {"ARTICLE_TITLE", "ARTICLE_CONTENT", "ARTICLE_SUMMARY"}


def _local(tag: str) -> str:
    return tag.split("}", 1)[1] if "}" in tag else tag


def _values(root: ET.Element) -> dict[str, str]:
    return {_local(el.tag): (el.text or "").strip() for el in root}


def _parse(path: Path, out: list[tuple[str, str, str]]) -> ET.Element | None:
    try:
        return ET.parse(path).getroot()
    except ET.ParseError as exc:
        out.append(("ERROR", "ES-XML-01", f"{path}: does not parse ({exc})."))
        return None


def scan(root: Path) -> tuple[int, list[tuple[str, str, str]]]:
    out: list[tuple[str, str, str]] = []
    files = [p for p in root.rglob("*") if p.is_file()]
    agent = [p for p in files if p.name.startswith("EinsteinAgent.settings")]
    legacy = [p for p in files if p.name.startswith("CaseClassification.settings")]
    reply = [p for p in files if p.name.startswith("AIReplyRecommendations.settings")]
    definitions = [p for p in files if ".serviceAISetupDescription" in p.name or ".serviceAISetupDefinition" in p.name]
    fields = [p for p in files if ".serviceAiSetupField" in p.name or ".serviceAISetupField" in p.name]
    models = [p for p in files if ".externalAIModel" in p.name]
    manifests = [p for p in files if p.name == "package.xml"]

    for path in agent:
        node = _parse(path, out)
        if node is None:
            continue
        v = _values(node)
        if v.get("einsteinAgentRecommendations", "").lower() == "true" and \
                v.get("runAssignmentRules", "false").lower() != "true" and \
                v.get("reRunAttributeBasedRules", "false").lower() != "true":
            out.append(("WARN", "ES-CLS-01",
                        f"{path}: classification is on but neither assignment rules nor skills-based rules re-run after it updates fields."))
    for path in legacy:
        out.append(("WARN", "ES-CLS-02", f"{path}: CaseClassificationSettings was renamed EinsteinAgentSettings in API 52.0; use EinsteinAgent.settings."))
    for path in reply:
        node = _parse(path, out)
        if node is None:
            continue
        v = _values(node)
        if v.get("enableGenReplyRecommendations", "").lower() == "true" and v.get("enableServiceEinsteinGPTGrounding", "").lower() == "false":
            out.append(("WARN", "ES-REPLY-01", f"{path}: Einstein Service Replies is on with Service AI Grounding off."))
    for path in definitions:
        node = _parse(path, out)
        if node is None:
            continue
        v = _values(node)
        if v.get("appSourceType") == "ARTICLE_RECOMMENDATION" and not v.get("supportedLanguages"):
            out.append(("ERROR", "ES-ART-01", f"{path}: supportedLanguages is required for ARTICLE_RECOMMENDATION."))
        if v.get("setupStatus") in ("RETIRED", "ARCHIVED"):
            out.append(("WARN", "ES-ART-03", f"{path}: setupStatus {v.get('setupStatus')} deploys an inactive configuration."))
    positions: dict[str, list[int]] = defaultdict(list)
    for path in fields:
        node = _parse(path, out)
        if node is None:
            continue
        v = _values(node)
        mapping, entity = v.get("fieldMappingType", ""), v.get("entity", "")
        if (mapping in CASE_TYPES and entity != "Case") or (mapping in ARTICLE_TYPES and entity == "Case"):
            out.append(("ERROR", "ES-ART-02", f"{path}: fieldMappingType {mapping} does not fit entity {entity}."))
        try:
            pos = int(v.get("fieldPosition", "0"))
        except ValueError:
            pos = 0
        if pos < 1:
            out.append(("ERROR", "ES-ART-02", f"{path}: fieldPosition must be a positive number (1 is most important)."))
        else:
            positions[v.get("setupDefinition", "")].append(pos)
    for definition, used in positions.items():
        duplicates = sorted({p for p in used if used.count(p) > 1})
        if duplicates:
            out.append(("ERROR", "ES-ART-02", f"{root}: setup definition {definition} repeats fieldPosition {duplicates}."))
    for path in models:
        node = _parse(path, out)
        if node is None:
            continue
        status = _values(node).get("externalModelStatus", "")
        if status in ("PAUSED", "DISABLED"):
            out.append(("WARN", "ES-MODEL-02", f"{path}: externalModelStatus {status}; confirm before promoting."))
    for path in manifests:
        node = _parse(path, out)
        if node is None:
            continue
        for types in (t for t in node if _local(t.tag) == "types"):
            name = next(((c.text or "").strip() for c in types if _local(c.tag) == "name"), "")
            members = [(c.text or "").strip() for c in types if _local(c.tag) == "members"]
            if name == "ExternalAIModel" and "*" in members:
                out.append(("ERROR", "ES-MODEL-01", f"{path}: ExternalAIModel doesn't support the * wildcard; list members by name."))
    count = len(agent) + len(legacy) + len(reply) + len(definitions) + len(fields) + len(models) + len(manifests)
    return count, out


def self_test() -> int:
    import tempfile
    here = Path(__file__).resolve().parent
    _, good = scan(here / "fixtures" / "good")
    _, bad = scan(here / "fixtures" / "bad")
    expected = {"ES-XML-01", "ES-CLS-01", "ES-CLS-02", "ES-REPLY-01", "ES-ART-01", "ES-ART-02", "ES-ART-03",
                "ES-MODEL-01", "ES-MODEL-02"}
    seen = {rule for _, rule, _ in bad}
    md = (here.parent / "references" / "metadata-examples.md").read_text(encoding="utf-8")
    names = {"<EinsteinAgentSettings": "EinsteinAgent.settings-meta.xml",
             "<AIReplyRecommendationsSettings": "AIReplyRecommendations.settings-meta.xml",
             "<ServiceAISetupDefinition": "Def.serviceAISetupDescription-meta.xml",
             "<ServiceAISetupField": "Fld.serviceAiSetupField-meta.xml",
             "<Package": "package.xml"}
    own: list[tuple[str, str, str]] = []
    with tempfile.TemporaryDirectory() as tmp:
        for block in re.findall(r"```xml\n(.*?)```", md, flags=re.DOTALL):
            for marker, filename in names.items():
                if marker in block:
                    (Path(tmp) / filename).write_text(block, encoding="utf-8")
        _, own = scan(Path(tmp))
    ok = not good and expected <= seen and not own
    print(f"good fixtures: {len(good)} finding(s) (expected 0)")
    for f in good:
        print("   ", *f)
    print(f"bad fixtures: rules seen {sorted(seen)}; missing {sorted(expected - seen)}")
    print(f"skill examples: {len(own)} finding(s) (expected 0)")
    for f in own:
        print("   ", *f)
    print("SELF-TEST", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description="Check Einstein for Service settings metadata.")
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
        print(f"WARN: no Einstein for Service settings, setup definitions, models, or package.xml under {root}; nothing checked.")
        return 0
    for severity, rule, message in findings:
        print(f"{severity} {rule}: {message}")
    errors = sum(1 for f in findings if f[0] == "ERROR")
    warns = sum(1 for f in findings if f[0] == "WARN")
    print(f"Checked {count} file(s): {errors} error(s), {warns} warning(s).")
    return 1 if errors or (args.strict and warns) else 0


if __name__ == "__main__":
    sys.exit(main())
