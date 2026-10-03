#!/usr/bin/env python3
"""Check Salesforce metadata for Einstein Trust Layer configuration gaps.

Stdlib only. Point --manifest-dir at a source-format project folder (for example
force-app/main/default) or an unzipped retrieve. Rules encode the Generative AI guide
(Spring '26) and the Metadata API Developer Guide (v67.0).

Correction (2026-10-03): the previous version of this checker looked for an
"EinsteinSettings" file with enableEinsteinGPTForSalesforce or generativeAiEnabled, and for
*.promptTemplate-meta.xml files. None of those exist in the Metadata API guide. The real
types are EinsteinAISettings (enableTrustPIIMasking, enableAIFeedbackWithDC), EinsteinGptSettings
(enableEinsteinGptPlatform, provider blocks, disableAIProviderRegionFallback), and
GenAiPromptTemplate (suffix .genAiPromptTemplate).

Rules
  TL-XML-01     ERROR  A settings or prompt template file does not parse (the guide's own
                       EinsteinGptSettings sample has mismatched tags).
  TL-SET-01     ERROR  EinsteinAISettings.enableTrustPIIMasking is false.
  TL-SET-02     WARN   EinsteinGptSettings.enableEinsteinGptPlatform is false.
  TL-SET-03     WARN   EinsteinAISettings.enableAIFeedbackWithDC is false or absent (no audit and feedback data).
  TL-REGION-01  ERROR  With --residency: EinsteinGptSettings.disableAIProviderRegionFallback is not true.
  TL-NOSET-01   WARN   Prompt templates present but no EinsteinAISettings/EinsteinGptSettings to verify.
  TL-PT-01      WARN   A *.promptTemplate-meta.xml file; prompt templates are GenAiPromptTemplate.
  TL-PT-02      WARN   A prompt template uses Flow or Apex data providers; field-based masking covers
                       only record merge fields and related lists.
  TL-AGENT-01   WARN   Agent metadata present and a prompt template references sensitive-looking fields;
                       data masking is disabled for agents.
  TL-DIRECT-01  WARN   Apex or credential metadata calls an LLM provider directly; Trust Layer
                       capabilities apply only to Einstein generative AI features.

Usage
  python3 check_einstein_trust_layer.py --manifest-dir force-app/main/default [--residency] [--strict]
  python3 check_einstein_trust_layer.py --self-test

Exit codes: 0 clean (WARN allowed unless --strict); 1 on ERROR, a missing folder, or WARN with --strict.
"""
from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

LLM_HOSTS = re.compile(
    r"(api\.openai\.com|openai\.azure\.com|api\.anthropic\.com|bedrock-runtime\.|"
    r"generativelanguage\.googleapis\.com|aiplatform\.googleapis\.com)",
    re.IGNORECASE,
)
SENSITIVE_FIELD = re.compile(r"\{![^}]*(ssn|social_?security|passport|credit_?card|tax_?id|date_?of_?birth|dob)[^}]*\}",
                             re.IGNORECASE)


def strip_comments(text: str) -> str:
    """Remove // and /* */ comments outside single-quoted Apex/SOQL string literals."""
    out: list[str] = []
    i, n = 0, len(text)
    in_string = False
    while i < n:
        ch = text[i]
        if in_string:
            out.append(ch)
            if ch == "\\" and i + 1 < n:
                out.append(text[i + 1])
                i += 2
                continue
            if ch == "'":
                in_string = False
            i += 1
            continue
        if ch == "'":
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


def _local(tag: str) -> str:
    return tag.split("}", 1)[1] if "}" in tag else tag


def _parse(path: Path) -> tuple[ET.Element | None, str | None]:
    try:
        return ET.parse(path).getroot(), None
    except ET.ParseError as exc:
        return None, str(exc)


def _flag(root: ET.Element, name: str) -> str | None:
    for el in root.iter():
        if _local(el.tag) == name:
            return (el.text or "").strip().lower()
    return None


def scan(root: Path, residency: bool) -> tuple[int, list[tuple[str, str, str]]]:
    findings: list[tuple[str, str, str]] = []
    files = [p for p in root.rglob("*") if p.is_file()]
    relevant = 0
    ai_settings = [p for p in files if p.name.startswith(("EinsteinAI.settings", "EinsteinAISettings.settings"))]
    gpt_settings = [p for p in files if p.name.startswith("EinsteinGpt.settings")]
    templates = [p for p in files if ".genAiPromptTemplate" in p.name]
    legacy = [p for p in files if p.name.endswith(".promptTemplate-meta.xml")]
    agents = [p for p in files if any(part in ("genAiPlannerBundles", "genAiPlanners", "bots", "genAiPlugins")
                                      for part in p.parts)]
    code = [p for p in files if p.suffix in (".cls", ".trigger")
            or p.name.endswith((".namedCredential-meta.xml", ".externalCredential-meta.xml",
                                ".remoteSite-meta.xml", ".namedCredential", ".remoteSite"))]
    relevant = len(ai_settings) + len(gpt_settings) + len(templates) + len(legacy) + len(code)

    for path in ai_settings:
        node, err = _parse(path)
        if node is None:
            findings.append(("ERROR", "TL-XML-01", f"{path}: does not parse ({err})."))
            continue
        if _flag(node, "enableTrustPIIMasking") == "false":
            findings.append(("ERROR", "TL-SET-01", f"{path}: enableTrustPIIMasking is false; PII masking for AI trust features is off."))
        if _flag(node, "enableAIFeedbackWithDC") != "true":
            findings.append(("WARN", "TL-SET-03", f"{path}: enableAIFeedbackWithDC is not true; audit and feedback data will not reach Data 360."))
    for path in gpt_settings:
        node, err = _parse(path)
        if node is None:
            findings.append(("ERROR", "TL-XML-01", f"{path}: does not parse ({err})."))
            continue
        if _flag(node, "enableEinsteinGptPlatform") == "false":
            findings.append(("WARN", "TL-SET-02", f"{path}: enableEinsteinGptPlatform is false; generative AI features are off."))
        if residency and _flag(node, "disableAIProviderRegionFallback") != "true":
            findings.append(("ERROR", "TL-REGION-01",
                             f"{path}: disableAIProviderRegionFallback is not true; Azure OpenAI requests can fall back outside the endpoint region."))
    if (templates or legacy) and not (ai_settings or gpt_settings):
        findings.append(("WARN", "TL-NOSET-01", f"{root}: prompt templates found but no EinsteinAI or EinsteinGpt settings to verify masking."))
    for path in legacy:
        findings.append(("WARN", "TL-PT-01", f"{path}: not a Metadata API type; prompt templates are GenAiPromptTemplate (.genAiPromptTemplate)."))
    sensitive_templates: list[Path] = []
    for path in templates:
        node, err = _parse(path)
        if node is None:
            findings.append(("ERROR", "TL-XML-01", f"{path}: does not parse ({err})."))
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        definitions = [(el.text or "") for el in node.iter() if _local(el.tag) == "definition"]
        if any(d.startswith(("flow://", "apex://")) for d in definitions) or re.search(r"\{!\$(Flow|Apex):", text):
            findings.append(("WARN", "TL-PT-02",
                             f"{path}: Flow or Apex merge fields get pattern-based masking only; field-based masking covers record merge fields and related lists."))
        if SENSITIVE_FIELD.search(text):
            sensitive_templates.append(path)
    if agents and sensitive_templates:
        for path in sensitive_templates:
            findings.append(("WARN", "TL-AGENT-01",
                             f"{path}: references sensitive-looking fields and the project has agents; data masking is disabled for agents."))
    for path in code:
        raw = path.read_text(encoding="utf-8", errors="replace")
        if path.suffix in (".cls", ".trigger"):
            raw = strip_comments(raw)
        match = LLM_HOSTS.search(raw)
        if match:
            findings.append(("WARN", "TL-DIRECT-01",
                             f"{path}: calls {match.group(1)} directly; Trust Layer masking, toxicity scoring, and audit apply only to Einstein generative AI features."))
    return relevant, findings


def self_test() -> int:
    import re as _re
    import tempfile
    here = Path(__file__).resolve().parent
    _, good = scan(here / "fixtures" / "good", residency=True)
    _, bad = scan(here / "fixtures" / "bad", residency=True)
    expected = {"TL-XML-01", "TL-SET-01", "TL-SET-02", "TL-SET-03", "TL-REGION-01", "TL-PT-01",
                "TL-PT-02", "TL-AGENT-01", "TL-DIRECT-01"}
    seen = {rule for _, rule, _ in bad}
    own: list[tuple[str, str, str]] = []
    md = (here.parent / "references" / "metadata-examples.md").read_text(encoding="utf-8")
    with tempfile.TemporaryDirectory() as tmp:
        settings = Path(tmp) / "settings"
        settings.mkdir()
        for block in _re.findall(r"```xml\n(.*?)```", md, flags=_re.DOTALL):
            if "<EinsteinAISettings" in block:
                (settings / "EinsteinAI.settings-meta.xml").write_text(block, encoding="utf-8")
            elif "<EinsteinGptSettings" in block:
                (settings / "EinsteinGpt.settings-meta.xml").write_text(block, encoding="utf-8")
        _, own = scan(Path(tmp), residency=True)
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
    ap = argparse.ArgumentParser(description="Check metadata for Einstein Trust Layer configuration gaps.")
    ap.add_argument("--manifest-dir", default=".", help="Project or retrieve folder to scan (default: current directory).")
    ap.add_argument("--residency", action="store_true", help="Require disableAIProviderRegionFallback = true.")
    ap.add_argument("--strict", action="store_true", help="Treat WARN findings as failures.")
    ap.add_argument("--self-test", action="store_true", help="Run the bundled fixtures and exit.")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    root = Path(args.manifest_dir)
    if not root.is_dir():
        print(f"ERROR: manifest directory not found: {root}")
        sys.exit(1)
    relevant, findings = scan(root, args.residency)
    if relevant == 0:
        print(f"WARN: no Einstein settings, prompt templates, Apex, or credential metadata under {root}; nothing checked.")
        return 0
    for severity, rule, message in findings:
        print(f"{severity} {rule}: {message}")
    errors = sum(1 for f in findings if f[0] == "ERROR")
    warns = sum(1 for f in findings if f[0] == "WARN")
    print(f"Checked {relevant} file(s): {errors} error(s), {warns} warning(s).")
    return 1 if errors or (args.strict and warns) else 0


if __name__ == "__main__":
    sys.exit(main())
