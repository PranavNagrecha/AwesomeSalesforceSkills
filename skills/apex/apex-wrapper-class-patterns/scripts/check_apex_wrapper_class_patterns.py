#!/usr/bin/env python3
"""Check Apex wrapper classes for unsupported component contracts and unsafe sorting.

Stdlib only. Scans *.cls files under --manifest-dir. Every rule cites the source it encodes.

Rules
  WRAP-INNER-01  ERROR  An @AuraEnabled static method returns or takes an inner class.
                        LWC Developer Guide, "Expose Apex Methods to Lightning Web Components":
                        an Apex inner class as a parameter or return value "isn't supported";
                        Aura Components Developer Guide (262) says the same for Aura.
  WRAP-MIX-01    WARN   One class declares both static @AuraEnabled methods and @AuraEnabled
                        instance properties. Aura Components Developer Guide (262), "AuraEnabled
                        Annotation": "Don't mix-and-match these different uses of @AuraEnabled in
                        the same Apex class."
  WRAP-AURA-01   WARN   A class returned by or passed to an @AuraEnabled method has public instance
                        properties without @AuraEnabled. Aura guide: only public instance properties
                        and methods annotated with @AuraEnabled are serialized.
  WRAP-PARAM-01  WARN   A class used as an @AuraEnabled method parameter has @AuraEnabled
                        properties without a getter and setter. Aura guide, custom Apex class
                        parameter example.
  WRAP-CMP-01    WARN   compareTo() or compare() with no null check. Apex Reference Guide (262),
                        Comparable and Comparator: implementations "must explicitly handle null inputs."

Usage
  python3 check_apex_wrapper_class_patterns.py --manifest-dir force-app/main/default/classes
  python3 check_apex_wrapper_class_patterns.py --manifest-dir path --strict   # WARN fails too
  python3 check_apex_wrapper_class_patterns.py --self-test

Exit codes: 0 clean (or WARN only without --strict); 1 any ERROR, a missing folder,
or WARN under --strict.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

Finding = tuple[str, str, str]
CLASS_RE = re.compile(r"\bclass\s+(\w+)", re.IGNORECASE)
AURA_METHOD_RE = re.compile(
    r"@AuraEnabled\b[^\n]*\n?\s*(?:(?:public|global)\s+)?static\s+([\w<>,\s\.]+?)\s+(\w+)\s*\(([^)]*)\)",
    re.IGNORECASE,
)
AURA_PROP_RE = re.compile(
    r"@AuraEnabled\b(?:\([^)]*\))?[ \t]*\n?[ \t]*(?:public|global)[ \t]+(?!static\b)([\w<>,\.]+(?:[ \t]*<[^>\n]*>)?)[ \t]+(\w+)[ \t]*(\{[^}]*\}|;|=)",
    re.IGNORECASE,
)
PUBLIC_PROP_RE = re.compile(
    r"^\s*(?:public|global)\s+(?!static\b|class\b|interface\b|enum\b|virtual\b|abstract\b|override\b)([\w<>,\.]+(?:\s*<[^>]*>)?)\s+(\w+)\s*(\{[^}]*\}|;|=)",
    re.IGNORECASE | re.MULTILINE,
)
COMPARE_RE = re.compile(r"\b(?:public|global)\s+Integer\s+(compareTo|compare)\s*\(([^)]*)\)\s*\{", re.IGNORECASE)


def strip_comments_and_strings(text: str) -> str:
    text = re.sub(r"/\*.*?\*/", " ", text, flags=re.DOTALL)
    text = re.sub(r"//[^\n]*", "", text)
    return re.sub(r"'(?:\\.|[^'\\])*'", "''", text)


def depth_at(text: str, index: int) -> int:
    return text.count("{", 0, index) - text.count("}", 0, index)


def block_after(text: str, open_index: int) -> str:
    depth = 0
    for i in range(open_index, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return text[open_index:i + 1]
    return text[open_index:]


def class_blocks(text: str) -> dict[str, tuple[str, int]]:
    """Return {class name: (body text, depth of the class keyword)}."""
    blocks: dict[str, tuple[str, int]] = {}
    for match in CLASS_RE.finditer(text):
        brace = text.find("{", match.end())
        if brace == -1:
            continue
        blocks[match.group(1)] = (block_after(text, brace), depth_at(text, match.start()))
    return blocks


def type_tokens(type_text: str) -> set[str]:
    return set(re.findall(r"\w+", type_text))


def scan(folder: Path) -> list[Finding]:
    findings: list[Finding] = []
    files = sorted(p for p in folder.rglob("*.cls") if p.is_file())
    parsed: dict[Path, str] = {}
    all_classes: dict[str, tuple[Path, str, int]] = {}
    for path in files:
        try:
            text = strip_comments_and_strings(path.read_text(encoding="utf-8", errors="ignore"))
        except OSError:
            continue
        parsed[path] = text
        for name, (body, depth) in class_blocks(text).items():
            all_classes[name.lower()] = (path, body, depth)

    returned_or_param: dict[str, set[str]] = {}
    for path, text in parsed.items():
        blocks = class_blocks(text)
        inner = {name.lower() for name, (_, depth) in blocks.items() if depth >= 1}
        top = [name for name, (_, depth) in blocks.items() if depth == 0]
        for m in AURA_METHOD_RE.finditer(text):
            return_type, method, params = m.group(1), m.group(2), m.group(3)
            tokens = {t.lower() for t in type_tokens(return_type) | type_tokens(params)}
            hit = tokens & inner
            if hit:
                findings.append(("ERROR", "WRAP-INNER-01",
                                 f"{path}: @AuraEnabled method {method} uses inner class {sorted(hit)[0]} as a "
                                 "parameter or return type; declare the wrapper as a top-level class."))
            for t in type_tokens(return_type):
                returned_or_param.setdefault(t.lower(), set()).add("return")
            for t in type_tokens(params):
                returned_or_param.setdefault(t.lower(), set()).add("param")
        for name in top:
            body, _ = blocks[name]
            has_static_aura = AURA_METHOD_RE.search(body) is not None
            own_props = [p for p in AURA_PROP_RE.finditer(body) if depth_at(body, p.start()) == 1]
            if has_static_aura and own_props:
                findings.append(("WARN", "WRAP-MIX-01",
                                 f"{path}: class {name} mixes static @AuraEnabled methods with @AuraEnabled "
                                 "instance properties; move the properties to a separate wrapper class."))
        for m in COMPARE_RE.finditer(text):
            body = block_after(text, m.end() - 1)
            if "== null" not in body and "!= null" not in body and "==null" not in body:
                findings.append(("WARN", "WRAP-CMP-01",
                                 f"{path}: {m.group(1)}() has no null check; handle null arguments and keys."))

    for type_name, uses in sorted(returned_or_param.items()):
        if type_name not in all_classes:
            continue
        path, body, depth = all_classes[type_name]
        if depth != 0:
            continue
        annotated = {p.group(2).lower(): p.group(3) for p in AURA_PROP_RE.finditer(body)}
        for prop in PUBLIC_PROP_RE.finditer(body):
            if depth_at(body, prop.start()) != 1:
                continue
            name = prop.group(2).lower()
            preceding = body[max(0, prop.start() - 120):prop.start()]
            preceding = re.split(r"[;{}]", preceding)[-1]
            if name not in annotated and "@auraenabled" not in preceding.lower():
                findings.append(("WARN", "WRAP-AURA-01",
                                 f"{path}: public property {prop.group(2)} on {type_name} lacks @AuraEnabled "
                                 "and is not serialized to the component."))
        if "param" in uses:
            for name, tail in annotated.items():
                if "get" not in tail.lower() or "set" not in tail.lower():
                    findings.append(("WARN", "WRAP-PARAM-01",
                                     f"{path}: @AuraEnabled property {name} on parameter type {type_name} "
                                     "needs { get; set; }."))
    return findings


def report(findings: list[Finding], strict: bool) -> int:
    for level, rule, message in findings:
        print(f"{level}: [{rule}] {message}")
    errors = sum(1 for f in findings if f[0] == "ERROR")
    warns = sum(1 for f in findings if f[0] == "WARN")
    print(f"{errors} error(s), {warns} warning(s)")
    return 1 if errors or (strict and warns) else 0


def self_test() -> int:
    base = Path(__file__).resolve().parent / "fixtures"
    good, bad = base / "good", base / "bad"
    if not good.is_dir() or not bad.is_dir():
        print("ERROR: fixtures/good or fixtures/bad is missing")
        return 1
    failures = 0
    good_findings = scan(good)
    if good_findings:
        failures += 1
        print("ERROR: self-test: fixtures/good produced findings:")
        for finding in good_findings:
            print(f"  {finding}")
    bad_findings = scan(bad)
    expected = {"WRAP-INNER-01", "WRAP-MIX-01", "WRAP-AURA-01", "WRAP-PARAM-01", "WRAP-CMP-01"}
    missing = expected - {f[1] for f in bad_findings}
    if missing:
        failures += 1
        print(f"ERROR: self-test: fixtures/bad did not trigger {sorted(missing)}")
    if failures:
        return 1
    print("self-test passed")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Check Apex wrapper classes for component and sorting issues.")
    parser.add_argument("--manifest-dir", help="folder of .cls files to scan")
    parser.add_argument("--strict", action="store_true", help="treat WARN as failure")
    parser.add_argument("--self-test", action="store_true", help="run against scripts/fixtures")
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    if not args.manifest_dir:
        parser.print_help()
        return 1
    folder = Path(args.manifest_dir)
    if not folder.is_dir():
        print(f"ERROR: {folder} is not a folder")
        sys.exit(1)
    if not any(folder.rglob("*.cls")):
        print(f"WARN: no .cls files under {folder}")
        return 1 if args.strict else 0
    return report(scan(folder), args.strict)


if __name__ == "__main__":
    sys.exit(main())
