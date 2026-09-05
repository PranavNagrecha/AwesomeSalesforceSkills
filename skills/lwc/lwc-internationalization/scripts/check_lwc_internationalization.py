#!/usr/bin/env python3
"""Check LWC bundles and CustomLabels metadata for internationalization defects.

Static, stdlib-only, no org connection. Point --manifest-dir at a Salesforce
source tree (for example force-app/main/default) or at any ancestor of one. The
script discovers LWC bundles by looking for a directory containing <name>.js and
<name>.html, and discovers custom labels by parsing every *.labels-meta.xml /
*.labels file anywhere under the root.

Checks implemented (each maps to a gotcha or anti-pattern in this skill):

  C1  WARN     A user-facing text node in an HTML template that is not a binding.
               Heuristic: a text node of >= 3 words with no {binding} in it.
               (references/gotchas.md -> "A String In The Template Is Invisible
               To Every Translator"; lwc_guide create-labels L3766)
  C2  ERROR    `@salesforce/label/c.X` imported for a label that no CustomLabels
               file in the tree defines. The import is silently unresolvable.
               (lwc_guide create-labels L3767-3768, L3773)
  C3  WARN     toLocaleDateString() / toLocaleString() / toLocaleTimeString()
               called with no locale argument -- falls back to the browser's
               locale, not the running user's Salesforce locale.
               (lwc_guide create-i18n L3841)
  C4  WARN     `new Date(<date-only value>)` -- parsing a Date field's
               "YYYY-MM-DD" string shifts the day for users west of UTC.
               (references/gotchas.md -> "A Date-Only Field Loses A Day")
  C5  WARN     A label symbol concatenated with a variable, or interpolated into
               a template literal, to build a sentence. Word order is not
               translatable. (references/llm-anti-patterns.md -> Anti-Pattern 2)
  C6  ADVISORY <labels> element with no <protected> child. api_meta.txt L41205
               lists `protected` as Required for CustomLabel; a packaged label
               without it cannot be reasoned about by the installing org.
  C7  ERROR    <value> longer than 1,000 characters. api_meta.txt L41152-41153,
               L41216-41217: "custom text values, up to 1,000 characters".
  C7b WARN     <value> in the 766-1,000 band: deployable as a master value, but no
               translation of it can ever carry the full text.
  C8  ERROR    A <label> in a *.translation file longer than 765 characters.
               api_meta.txt L135933-135935: CustomLabelTranslation.label is
               "Maximum of 765 characters" -- lower than the master value's cap.

Severity and exit codes:
  ERROR     always makes the run fail (exit 1)
  WARN      informational; makes the run fail only with --strict
  ADVISORY  never fails the run
  A --manifest-dir that does not exist exits 1.
  A --manifest-dir with no LWC bundle and no labels file emits a WARN.

Usage:
    python3 check_lwc_internationalization.py --manifest-dir force-app/main/default
    python3 check_lwc_internationalization.py --manifest-dir force-app --strict
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

MD_NS = "{http://soap.sforce.com/2006/04/metadata}"

ERROR, WARN, ADVISORY = "ERROR", "WARN", "ADVISORY"

# --- grounded numeric limits -------------------------------------------------
# api_meta.txt L41152-41153 / L41216-41217: CustomLabel.value max 1000 chars.
LABEL_VALUE_MAX = 1000
# api_meta.txt L135933-135935: CustomLabelTranslation.label max 765 chars.
TRANSLATION_LABEL_MAX = 765

# --- regexes -----------------------------------------------------------------
LABEL_IMPORT_RE = re.compile(
    r"""^\s*import\s+([A-Za-z_$][\w$]*)\s+from\s+['"]@salesforce/label/([^'"]+)['"]""",
    re.MULTILINE,
)
LABEL_AGGREGATOR_RE = re.compile(r"^\s*(?:const\s+)?([A-Za-z_$][\w$]*)\s*=\s*\{", re.MULTILINE)
TO_LOCALE_RE = re.compile(r"\.\s*(toLocaleDateString|toLocaleTimeString|toLocaleString)\s*\(\s*([^)]*)\)")
NEW_DATE_RE = re.compile(r"\bnew\s+Date\s*\(\s*([^)]*)\)")
DATE_ONLY_LITERAL_RE = re.compile(r"""^['"]\d{4}-\d{2}-\d{2}['"]$""")
DATE_ONLY_IDENT_RE = re.compile(r"(?:^|[a-z0-9_$])(?<!Time)Date$|^date$", re.IGNORECASE)

HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
HTML_STYLE_SCRIPT_RE = re.compile(r"<(style|script)\b.*?</\1\s*>", re.DOTALL | re.IGNORECASE)
HTML_TAG_RE = re.compile(r"<[^>]*>", re.DOTALL)
BINDING_RE = re.compile(r"\{[^}]*\}")
WORD_RE = re.compile(r"[A-Za-z][A-Za-z'’-]*")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check LWC bundles and CustomLabels metadata for internationalization defects.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root of the Salesforce source tree (default: current directory).",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Promote WARN findings to failures (exit 1). ADVISORY never fails.",
    )
    return parser.parse_args()


def first_child(element, tag: str):
    """ElementTree-safe child lookup.

    A leaf Element is falsy, so `el.find(a) or el.find(b)` silently returns the
    wrong branch. Always compare against None.
    """
    if element is None:
        return None
    found = element.find(tag)
    if found is None:
        found = element.find(MD_NS + tag)
    return found


def read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def skip(path: Path) -> bool:
    parts = set(path.parts)
    return bool(parts & {"node_modules", ".sfdx", ".sf", "__pycache__"})


# --- discovery ---------------------------------------------------------------
def find_bundles(root: Path) -> list[Path]:
    """A bundle is a directory holding <dirname>.js and <dirname>.html."""
    bundles = set()
    for js_path in root.rglob("*.js"):
        if skip(js_path) or "__tests__" in js_path.parts:
            continue
        bundle = js_path.parent
        if js_path.stem != bundle.name:
            continue
        if (bundle / f"{bundle.name}.html").exists():
            bundles.add(bundle)
    return sorted(bundles)


def find_label_files(root: Path) -> list[Path]:
    out = []
    for pattern in ("*.labels-meta.xml", "*.labels"):
        out.extend(p for p in root.rglob(pattern) if not skip(p))
    return sorted(set(out))


def find_translation_files(root: Path) -> list[Path]:
    out = []
    for pattern in ("*.translation-meta.xml", "*.translation"):
        out.extend(p for p in root.rglob(pattern) if not skip(p))
    return sorted(set(out))


# --- label metadata ----------------------------------------------------------
def check_label_files(paths: list[Path], root: Path) -> tuple[set[str], list[tuple[str, str]]]:
    """Return (defined label fullNames, findings)."""
    defined: set[str] = set()
    findings: list[tuple[str, str]] = []
    for path in paths:
        try:
            tree = ET.parse(path)
        except ET.ParseError as exc:
            findings.append((ERROR, f"{rel(path, root)}: not well-formed XML ({exc})"))
            continue
        root_el = tree.getroot()
        labels = root_el.findall(MD_NS + "labels") or root_el.findall("labels")
        if not labels:
            findings.append((ADVISORY, f"{rel(path, root)}: no <labels> elements found"))
        for label in labels:
            name_el = first_child(label, "fullName")
            name = (name_el.text or "").strip() if name_el is not None else ""
            if name:
                defined.add(name)
            shown = name or "<unnamed>"

            # C6
            if first_child(label, "protected") is None:
                findings.append((
                    ADVISORY,
                    f"{rel(path, root)}: label '{shown}' has no <protected> element "
                    f"(C6; api_meta CustomLabel lists protected as Required, and an "
                    f"installing org cannot reference an unprotected-by-default label predictably)",
                ))
            if first_child(label, "language") is None:
                findings.append((
                    ADVISORY,
                    f"{rel(path, root)}: label '{shown}' has no <language> element "
                    f"(C6; api_meta CustomLabel lists language as Required)",
                ))

            # C7
            value_el = first_child(label, "value")
            value = (value_el.text or "") if value_el is not None else ""
            if len(value) > LABEL_VALUE_MAX:
                findings.append((
                    ERROR,
                    f"{rel(path, root)}: label '{shown}' <value> is {len(value)} characters, "
                    f"over the {LABEL_VALUE_MAX}-character CustomLabel maximum (C7)",
                ))
            elif len(value) > TRANSLATION_LABEL_MAX:
                findings.append((
                    WARN,
                    f"{rel(path, root)}: label '{shown}' <value> is {len(value)} characters — "
                    f"deployable as a master value, but a translation of it caps at "
                    f"{TRANSLATION_LABEL_MAX} characters, so no language can carry the full text (C7b)",
                ))
    return defined, findings


def check_translation_files(paths: list[Path], root: Path) -> list[tuple[str, str]]:
    findings: list[tuple[str, str]] = []
    for path in paths:
        try:
            tree = ET.parse(path)
        except ET.ParseError as exc:
            findings.append((ERROR, f"{rel(path, root)}: not well-formed XML ({exc})"))
            continue
        root_el = tree.getroot()
        entries = root_el.findall(MD_NS + "customLabels") or root_el.findall("customLabels")
        for entry in entries:
            name_el = first_child(entry, "name")
            name = (name_el.text or "").strip() if name_el is not None else "<unnamed>"
            label_el = first_child(entry, "label")
            text = (label_el.text or "") if label_el is not None else ""
            if len(text) > TRANSLATION_LABEL_MAX:
                findings.append((
                    ERROR,
                    f"{rel(path, root)}: translation of '{name}' is {len(text)} characters, "
                    f"over the {TRANSLATION_LABEL_MAX}-character CustomLabelTranslation maximum (C8)",
                ))
    return findings


# --- bundle checks -----------------------------------------------------------
def visible_text_nodes(html: str) -> list[str]:
    stripped = HTML_STYLE_SCRIPT_RE.sub(" ", html)
    stripped = HTML_COMMENT_RE.sub(" ", stripped)
    chunks = HTML_TAG_RE.split(stripped)
    return [c for c in chunks if c and c.strip()]


def check_html(bundle: Path, root: Path) -> list[tuple[str, str]]:
    findings: list[tuple[str, str]] = []
    html_path = bundle / f"{bundle.name}.html"
    html = read(html_path)
    for chunk in visible_text_nodes(html):
        # A chunk that is entirely bindings and punctuation is already localized.
        residue = BINDING_RE.sub(" ", chunk)
        words = WORD_RE.findall(residue)
        if len(words) >= 3:
            snippet = " ".join(residue.split())[:70]
            findings.append((
                WARN,
                f"{rel(html_path, root)}: literal text node \"{snippet}\" — "
                f"{len(words)} words with no label binding; no translator can see this string (C1)",
            ))
    return findings


def check_js(path: Path, root: Path, defined_labels: set[str]) -> list[tuple[str, str]]:
    findings: list[tuple[str, str]] = []
    src = read(path)
    if not src:
        return findings

    # C2 -- imported label must exist somewhere in the tree.
    label_symbols: set[str] = set()
    for match in LABEL_IMPORT_RE.finditer(src):
        symbol, reference = match.group(1), match.group(2)
        label_symbols.add(symbol)
        short = reference.split(".")[-1]
        namespaced = "." in reference and not reference.startswith("c.")
        if namespaced:
            continue  # a managed-package label is not in this source tree
        if defined_labels and short not in defined_labels:
            findings.append((
                ERROR,
                f"{rel(path, root)}: imports '@salesforce/label/{reference}' but no CustomLabels "
                f"file under the manifest dir defines '{short}' (C2)",
            ))

    # C3 -- toLocale* with no locale argument.
    for match in TO_LOCALE_RE.finditer(src):
        if not match.group(2).strip():
            line = src.count("\n", 0, match.start()) + 1
            findings.append((
                WARN,
                f"{rel(path, root)}:{line}: {match.group(1)}() called with no locale — "
                f"uses the browser's locale, not @salesforce/i18n/locale (C3)",
            ))

    # C4 -- new Date() over a date-only value.
    for match in NEW_DATE_RE.finditer(src):
        arg = match.group(1).strip()
        if not arg:
            continue
        tail = arg.split(".")[-1].strip()
        looks_date_only = bool(DATE_ONLY_LITERAL_RE.match(arg)) or (
            tail.isidentifier() and bool(DATE_ONLY_IDENT_RE.search(tail))
        )
        if looks_date_only:
            line = src.count("\n", 0, match.start()) + 1
            findings.append((
                WARN,
                f"{rel(path, root)}:{line}: new Date({arg}) parses a date-only value as UTC "
                f"midnight; users west of UTC render the previous day (C4)",
            ))

    # C5 -- label concatenated into a sentence.
    aggregators = set()
    for match in LABEL_AGGREGATOR_RE.finditer(src):
        block_start = match.end()
        block = src[block_start:block_start + 800]
        if any(sym in block for sym in label_symbols):
            aggregators.add(match.group(1))
    watched = label_symbols | {f"this.{a}" for a in aggregators} | aggregators
    for symbol in sorted(watched):
        pattern = re.escape(symbol) + r"(?:\.[\w$]+)?"
        concat = re.compile(rf"(?:{pattern}\s*\+(?!=)|\+\s*{pattern}\b|\$\{{\s*{pattern}\b)")
        for match in concat.finditer(src):
            line = src.count("\n", 0, match.start()) + 1
            findings.append((
                WARN,
                f"{rel(path, root)}:{line}: label '{symbol}' concatenated into a larger string — "
                f"word order is fixed in the source language; use one label with a {{0}} "
                f"placeholder and .replace() instead (C5)",
            ))
    return findings


def main() -> int:
    args = parse_args()
    root = Path(args.manifest_dir).resolve()
    if not root.is_dir():
        print(f"ERROR [lwc-internationalization] --manifest-dir not found: {root}", file=sys.stderr)
        return 1

    findings: list[tuple[str, str]] = []
    bundles = find_bundles(root)
    label_files = find_label_files(root)
    translation_files = find_translation_files(root)

    if not bundles and not label_files:
        findings.append((
            WARN,
            f"{root}: no LWC bundle (<name>.js + <name>.html) and no *.labels-meta.xml found — "
            f"nothing to check; is --manifest-dir pointing at the source root?",
        ))

    defined_labels, label_findings = check_label_files(label_files, root)
    findings.extend(label_findings)
    findings.extend(check_translation_files(translation_files, root))

    for bundle in bundles:
        findings.extend(check_html(bundle, root))
        for js_path in sorted(bundle.rglob("*.js")):
            if skip(js_path):
                continue
            findings.extend(check_js(js_path, root, defined_labels))

    errors = [f for f in findings if f[0] == ERROR]
    warns = [f for f in findings if f[0] == WARN]
    advisories = [f for f in findings if f[0] == ADVISORY]

    for level in (ERROR, WARN, ADVISORY):
        for lvl, message in findings:
            if lvl == level:
                print(f"{lvl} [lwc-internationalization] {message}")

    print(
        f"\n[lwc-internationalization] {len(bundles)} bundle(s), {len(label_files)} labels file(s), "
        f"{len(translation_files)} translation file(s), {len(defined_labels)} label(s) defined; "
        f"{len(errors)} error(s), {len(warns)} warning(s), {len(advisories)} advisory(ies)."
    )

    if errors:
        return 1
    if warns and args.strict:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
