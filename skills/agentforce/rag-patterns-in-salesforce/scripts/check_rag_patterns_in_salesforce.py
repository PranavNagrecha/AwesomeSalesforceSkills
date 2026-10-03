#!/usr/bin/env python3
"""Check RAG content and prompt template metadata before indexing or deploying.

Stdlib only. Point --manifest-dir at a folder holding any of: source documents bound for a
Data Cloud search index or Einstein Data Library (*.html, *.htm, *.txt, *.pdf),
GenAiPromptTemplate files, and Apex. Rules encode the Data Cloud guide (Summer '26: Chunking
Strategies, How the Max Token Setting Affects Chunking, Unstructured Data and Search Index
Guidelines and Limits, Search Index Reference) and the Generative AI guide (Prompt Builder
Limitations, Ground with Retrieval Augmented Generation).

Correction (2026-10-03): the previous version of this checker read "*.aiGrounding" files for a
"topK" element and required a "{!grounding.chunks}" merge field. Neither exists in the Metadata
API guide or the Prompt Builder chapter; those constructs are now reported as legacy errors.

Rules
  RAG-LEGACY-01  ERROR  {!grounding.chunks}, {!Grounding...}, *.aiGrounding files, or <topK> elements:
                        undocumented constructs from older guidance.
  RAG-SIZE-01    ERROR  TXT or HTML over 4 MB, or PDF over 100 MB: stored but "aren't chunked or vectorized".
  RAG-HTML-01    WARN   HTML with no heading tags: semantic passage extraction has no boundaries and falls
                        back to window-based extraction.
  RAG-HTML-02    WARN   HTML or text containing tables: "Can't chunk files with tabular data".
  RAG-LANG-01    WARN   Mostly non-Latin text: 512-token chunks can overflow; set a lower max token limit.
  RAG-STRIP-01   WARN   Apex strips HTML from Knowledge or body text; that removes passage boundaries.
  RAG-DEPLOY-01  WARN   A prompt template references a retriever; create the retriever in the target org
                        first (change sets and Metadata API don't carry it).

Usage
  python3 check_rag_patterns_in_salesforce.py --manifest-dir path/to/folder [--strict]
  python3 check_rag_patterns_in_salesforce.py --self-test

Exit codes: 0 clean (WARN allowed unless --strict); 1 on ERROR, a missing folder, or WARN with --strict.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

MAX_TEXT_BYTES = 4 * 1024 * 1024
MAX_PDF_BYTES = 100 * 1024 * 1024
LEGACY = re.compile(r"\{!\s*grounding\.chunks\s*\}|\{!\s*Grounding[^}]*\}|<\s*topK\s*>", re.IGNORECASE)
HEADING = re.compile(r"<h[1-6][\s>]", re.IGNORECASE)
TABLE = re.compile(r"<table[\s>]|^\s*\|.*\|\s*$", re.IGNORECASE | re.MULTILINE)
STRIP = re.compile(r"stripHtmlTags\s*\(|replaceAll\(\s*'<\[\^>\]\+>'", re.IGNORECASE)
RETRIEVER_HINT = re.compile(r"einstein_?search|retriever|\{!\$EinsteinSearch:", re.IGNORECASE)


def non_latin_share(text: str) -> float:
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return 0.0
    return sum(1 for c in letters if ord(c) > 0x024F) / len(letters)


def check_content(path: Path) -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    size = path.stat().st_size
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        if size > MAX_PDF_BYTES:
            out.append(("ERROR", "RAG-SIZE-01", f"{path}: PDF is {size:,} bytes; over 100 MB it is stored but not chunked or vectorized."))
        return out
    if size > MAX_TEXT_BYTES:
        out.append(("ERROR", "RAG-SIZE-01", f"{path}: {size:,} bytes; TXT or HTML over 4 MB is stored but not chunked or vectorized."))
    text = path.read_text(encoding="utf-8", errors="replace")
    if suffix in (".html", ".htm") and not HEADING.search(text):
        out.append(("WARN", "RAG-HTML-01", f"{path}: no <h1>-<h6> headings; passages won't follow document sections."))
    if TABLE.search(text):
        out.append(("WARN", "RAG-HTML-02", f"{path}: contains a table; tabular data can't be chunked, convert it to prose."))
    if non_latin_share(re.sub(r"<[^>]+>", " ", text)) > 0.5:
        out.append(("WARN", "RAG-LANG-01", f"{path}: mostly non-Latin text; set the search index max tokens below 512."))
    if LEGACY.search(text):
        out.append(("ERROR", "RAG-LEGACY-01", f"{path}: contains an undocumented grounding construct."))
    return out


def check_metadata(path: Path) -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    text = path.read_text(encoding="utf-8", errors="replace")
    if path.name.endswith((".aiGrounding", ".aiGrounding-meta.xml")):
        out.append(("ERROR", "RAG-LEGACY-01", f"{path}: 'aiGrounding' is not a Metadata API type; retrievers are built in Einstein Studio."))
    if LEGACY.search(text):
        out.append(("ERROR", "RAG-LEGACY-01",
                    f"{path}: {{!grounding.chunks}} or <topK> is undocumented; add the retriever from the Resource picker instead."))
    if ".genAiPromptTemplate" in path.name and RETRIEVER_HINT.search(text):
        out.append(("WARN", "RAG-DEPLOY-01",
                    f"{path}: references a retriever; create and activate it in the target org before deploying this template."))
    return out


def check_apex(path: Path) -> list[tuple[str, str, str]]:
    text = path.read_text(encoding="utf-8", errors="replace")
    if STRIP.search(text) and re.search(r"knowledge|__kav|body", text, flags=re.IGNORECASE):
        return [("WARN", "RAG-STRIP-01", f"{path}: strips HTML from Knowledge or body text; passage extraction needs the headings and lists.")]
    return []


def scan(root: Path) -> tuple[int, list[tuple[str, str, str]]]:
    findings: list[tuple[str, str, str]] = []
    count = 0
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        name = path.name
        if path.suffix.lower() in (".html", ".htm", ".txt", ".pdf"):
            findings.extend(check_content(path))
            count += 1
        elif ".genAiPromptTemplate" in name or name.endswith((".aiGrounding", ".aiGrounding-meta.xml")):
            findings.extend(check_metadata(path))
            count += 1
        elif path.suffix == ".cls":
            findings.extend(check_apex(path))
            count += 1
    return count, findings


def self_test() -> int:
    import tempfile
    here = Path(__file__).resolve().parent
    _, good = scan(here / "fixtures" / "good")
    _, bad = scan(here / "fixtures" / "bad")
    with tempfile.TemporaryDirectory() as tmp:
        big = Path(tmp) / "manual.html"
        big.write_text("<h1>Manual</h1>" + "<p>step</p>" * 450_000, encoding="utf-8")  # over 4 MB
        bad.extend(check_content(big))
    expected = {"RAG-LEGACY-01", "RAG-SIZE-01", "RAG-HTML-01", "RAG-HTML-02", "RAG-LANG-01", "RAG-STRIP-01", "RAG-DEPLOY-01"}
    seen = {rule for _, rule, _ in bad}
    md = (here.parent / "references" / "metadata-examples.md").read_text(encoding="utf-8")
    own: list[tuple[str, str, str]] = []
    with tempfile.TemporaryDirectory() as tmp:
        for i, block in enumerate(re.findall(r"```xml\n(.*?)```", md, flags=re.DOTALL)):
            if "<GenAiPromptTemplate" in block:
                target = Path(tmp) / f"Example{i}.genAiPromptTemplate-meta.xml"
                target.write_text(block, encoding="utf-8")
                own.extend(check_metadata(target))
    own_errors = [f for f in own if f[0] == "ERROR"]
    ok = not good and expected <= seen and not own_errors
    print(f"good fixtures: {len(good)} finding(s) (expected 0)")
    for f in good:
        print("   ", *f)
    print(f"bad fixtures: rules seen {sorted(seen)}; missing {sorted(expected - seen)}")
    print(f"skill examples: {len(own_errors)} ERROR(s) (expected 0); {len(own)} finding(s) total")
    print("SELF-TEST", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description="Check RAG source content and prompt template metadata.")
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
    count, findings = scan(root)
    if count == 0:
        print(f"WARN: no content files, prompt templates, or Apex found under {root}; nothing checked.")
        return 0
    for severity, rule, message in findings:
        print(f"{severity} {rule}: {message}")
    errors = sum(1 for f in findings if f[0] == "ERROR")
    warns = sum(1 for f in findings if f[0] == "WARN")
    print(f"Checked {count} file(s): {errors} error(s), {warns} warning(s).")
    return 1 if errors or (args.strict and warns) else 0


if __name__ == "__main__":
    sys.exit(main())
