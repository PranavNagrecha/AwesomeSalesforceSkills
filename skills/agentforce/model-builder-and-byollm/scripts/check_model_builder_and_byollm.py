#!/usr/bin/env python3
"""Check model choices, provider policy, and LLM credentials in Salesforce metadata.

Stdlib only. Point --manifest-dir at a source-format folder (for example force-app/main/default).
Rules encode the Data Cloud guide (Summer '26, Bring Your Own Large Language Model), the
Generative AI guide (Spring '26, Large Language Model Support), and the Metadata API v67.0
(EinsteinGptSettings, GenAiPromptTemplate).

Correction (2026-10-03): the previous version of this checker required Named Credentials,
External Credentials, and Named Credential permission sets for every external model, and read
an "AI model" metadata file. The documented BYOLLM flow connects the model in Einstein Studio
(Add Foundation Model takes the endpoint and authentication details), and no fetched source
documents a Named Credential requirement for it.

Rules
  MB-XML-01     ERROR  A settings or template file does not parse (the guide's own EinsteinGptSettings
                       sample has mismatched tags).
  MB-PROV-01    ERROR  A template version's primaryModel names a provider that EinsteinGptSettings blocks.
  MB-DEPR-01    WARN   primaryModel names a deprecated family (GPT-4 32K, GPT-3.5 Turbo 16K); requests are rerouted.
  MB-KEY-01     ERROR  A provider API key literal in Apex, flows, or custom metadata.
  MB-DIRECT-01  WARN   Apex calls an LLM provider directly instead of through Einstein Studio or Prompt Builder.
  MB-HTTPS-01   ERROR  An LLM endpoint in metadata uses http:// or a port other than 443
                       ("a standard HTTPS 443 port is required").
  MB-BETA-01    WARN   enableAIModelBeta is true in EinsteinGptSettings.

Usage
  python3 check_model_builder_and_byollm.py --manifest-dir force-app/main/default [--strict]
  python3 check_model_builder_and_byollm.py --self-test

Exit codes: 0 clean (WARN allowed unless --strict); 1 on ERROR, a missing folder, or WARN with --strict.
"""
from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

PROVIDER_FLAGS = {
    "disableAIProvOpenAI": re.compile(r"openai(?!.*azure)|gpt", re.IGNORECASE),
    "disableAIProvAzureOpenAI": re.compile(r"azure", re.IGNORECASE),
    "disableAIProvAWSBedrock": re.compile(r"bedrock|anthropic|claude", re.IGNORECASE),
    "disableAIProvVertexGemini": re.compile(r"vertex|gemini|google", re.IGNORECASE),
}
DEPRECATED = re.compile(r"32k|16k", re.IGNORECASE)
KEY_LITERAL = re.compile(r"(['\"])(sk-[A-Za-z0-9_-]{20,}|sk-ant-[A-Za-z0-9_-]{20,})\1|"
                         r"setHeader\(\s*'(api-key|x-api-key)'\s*,\s*'[^']{12,}'", re.IGNORECASE)
LLM_HOST = re.compile(r"(https?)://([a-z0-9.-]*(openai\.azure\.com|api\.openai\.com|api\.anthropic\.com|"
                      r"bedrock-runtime\.[a-z0-9.-]+|aiplatform\.googleapis\.com|generativelanguage\.googleapis\.com))(:\d+)?",
                      re.IGNORECASE)


def _local(tag: str) -> str:
    return tag.split("}", 1)[1] if "}" in tag else tag


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


def scan(root: Path) -> tuple[int, list[tuple[str, str, str]]]:
    findings: list[tuple[str, str, str]] = []
    files = [p for p in root.rglob("*") if p.is_file()]
    settings = [p for p in files if p.name.startswith("EinsteinGpt.settings")]
    templates = [p for p in files if ".genAiPromptTemplate" in p.name]
    code = [p for p in files if p.suffix in (".cls", ".trigger") or p.name.endswith((".flow-meta.xml", ".md-meta.xml"))]
    creds = [p for p in files if p.name.endswith((".namedCredential-meta.xml", ".externalCredential-meta.xml",
                                                  ".remoteSite-meta.xml", ".namedCredential", ".remoteSite"))]
    blocked: set[str] = set()
    for path in settings:
        try:
            root_el = ET.parse(path).getroot()
        except ET.ParseError as exc:
            findings.append(("ERROR", "MB-XML-01", f"{path}: does not parse ({exc})."))
            continue
        values = {_local(el.tag): (el.text or "").strip().lower() for el in root_el}
        blocked |= {flag for flag in PROVIDER_FLAGS if values.get(flag) == "true"}
        if values.get("enableAIModelBeta") == "true":
            findings.append(("WARN", "MB-BETA-01", f"{path}: enableAIModelBeta is true; beta models are on for generative AI features."))
    for path in templates:
        try:
            root_el = ET.parse(path).getroot()
        except ET.ParseError as exc:
            findings.append(("ERROR", "MB-XML-01", f"{path}: does not parse ({exc})."))
            continue
        for el in root_el.iter():
            if _local(el.tag) != "primaryModel":
                continue
            model = (el.text or "").strip()
            for flag in blocked:
                if PROVIDER_FLAGS[flag].search(model):
                    findings.append(("ERROR", "MB-PROV-01", f"{path}: model '{model}' uses a provider blocked by {flag}."))
            if DEPRECATED.search(model):
                findings.append(("WARN", "MB-DEPR-01", f"{path}: model '{model}' looks like a deprecated family; retest on the replacement."))
    for path in code:
        raw = path.read_text(encoding="utf-8", errors="replace")
        text = strip_comments(raw) if path.suffix in (".cls", ".trigger") else raw
        if KEY_LITERAL.search(text):
            findings.append(("ERROR", "MB-KEY-01", f"{path}: contains a provider API key literal; remove it and rotate the key."))
        if path.suffix in (".cls", ".trigger") and LLM_HOST.search(text):
            findings.append(("WARN", "MB-DIRECT-01", f"{path}: calls an LLM provider directly; connect it in Einstein Studio and use Prompt Builder or the Models API."))
    for path in creds + [p for p in code if p.suffix in (".cls", ".trigger")]:
        text = path.read_text(encoding="utf-8", errors="replace")
        for match in LLM_HOST.finditer(text):
            scheme, port = match.group(1).lower(), match.group(4)
            if scheme != "https" or (port and port != ":443"):
                findings.append(("ERROR", "MB-HTTPS-01", f"{path}: LLM endpoint {match.group(0)} must be HTTPS on port 443."))
    return len(settings) + len(templates) + len(code) + len(creds), findings


def self_test() -> int:
    import tempfile
    here = Path(__file__).resolve().parent
    _, good = scan(here / "fixtures" / "good")
    _, bad = scan(here / "fixtures" / "bad")
    expected = {"MB-XML-01", "MB-PROV-01", "MB-DEPR-01", "MB-KEY-01", "MB-DIRECT-01", "MB-HTTPS-01", "MB-BETA-01"}
    seen = {rule for _, rule, _ in bad}
    md = (here.parent / "references" / "metadata-examples.md").read_text(encoding="utf-8")
    own: list[tuple[str, str, str]] = []
    with tempfile.TemporaryDirectory() as tmp:
        for i, block in enumerate(re.findall(r"```xml\n(.*?)```", md, flags=re.DOTALL)):
            if "<EinsteinGptSettings" in block:
                (Path(tmp) / "EinsteinGpt.settings-meta.xml").write_text(block, encoding="utf-8")
            elif "<GenAiPromptTemplate" in block:
                (Path(tmp) / f"T{i}.genAiPromptTemplate-meta.xml").write_text(block, encoding="utf-8")
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
    ap = argparse.ArgumentParser(description="Check model choices, provider policy, and LLM credentials.")
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
        print(f"WARN: no EinsteinGpt settings, prompt templates, Apex, flows, or credentials under {root}; nothing checked.")
        return 0
    for severity, rule, message in findings:
        print(f"{severity} {rule}: {message}")
    errors = sum(1 for f in findings if f[0] == "ERROR")
    warns = sum(1 for f in findings if f[0] == "WARN")
    print(f"Checked {count} file(s): {errors} error(s), {warns} warning(s).")
    return 1 if errors or (args.strict and warns) else 0


if __name__ == "__main__":
    sys.exit(main())
