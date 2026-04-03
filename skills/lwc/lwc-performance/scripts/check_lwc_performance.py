#!/usr/bin/env python3
"""Check Lightning Web Component bundles for common performance smells."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
import xml.etree.ElementTree as ET


LIST_DIRECTIVE_RE = re.compile(r"(for:each=\{|iterator:[a-z0-9_]+=\{)")
LEGACY_IF_RE = re.compile(r"\bif:(true|false)=\{")
INDEX_KEY_RE = re.compile(r"key=\{(?:[A-Za-z_][\w]*\.)?index\}")
GET_RECORD_UI_RE = re.compile(r"\bgetRecordUi\b")
LAYOUT_FETCH_RE = re.compile(r"\blayoutTypes\s*:")
DYNAMIC_IMPORT_RE = re.compile(r"\bimport\s*\((?P<arg>[^)]+)\)")
NON_TRACKABLE_RE = re.compile(r"@track\s+\w+\s*=\s*new\s+(Date|Set|Map)\s*\(")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check LWC bundles for rendering and payload anti-patterns.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def line_number(text: str, index: int) -> int:
    return text.count("\n", 0, index) + 1


def component_meta_path(script_path: Path) -> Path:
    return script_path.with_name(f"{script_path.stem}.js-meta.xml")


def has_dynamic_component_capability(meta_path: Path) -> bool:
    if not meta_path.exists():
        return False
    try:
        root = ET.parse(meta_path).getroot()
    except ET.ParseError:
        return False
    return any(
        (element.text or "").strip() == "lightning__dynamicComponent"
        for element in root.iter()
        if element.tag.endswith("capability")
    )


def check_lwc_performance(manifest_dir: Path) -> list[str]:
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    for html_path in sorted(manifest_dir.rglob("*.html")):
        text = html_path.read_text(encoding="utf-8", errors="ignore")
        lines = text.splitlines()

        for match in LEGACY_IF_RE.finditer(text):
            issues.append(
                f"{html_path}:{line_number(text, match.start())}: uses legacy `if:true`/`if:false`; prefer `lwc:if` chains for current and lighter conditional rendering."
            )

        for index, line in enumerate(lines):
            if not LIST_DIRECTIVE_RE.search(line):
                continue

            window = "\n".join(lines[index : index + 12])
            if "key={" not in window:
                issues.append(
                    f"{html_path}:{index + 1}: list directive found without a nearby `key={{...}}`; repeated rows need stable keys."
                )
            if INDEX_KEY_RE.search(window):
                issues.append(
                    f"{html_path}:{index + 1}: list uses index as key; use a stable record-derived identifier instead."
                )

    for js_path in sorted(path for path in manifest_dir.rglob("*") if path.suffix in {".js", ".ts"}):
        text = js_path.read_text(encoding="utf-8", errors="ignore")

        for match in GET_RECORD_UI_RE.finditer(text):
            issues.append(
                f"{js_path}:{line_number(text, match.start())}: uses `getRecordUi`; review payload size because UI metadata responses are expensive."
            )

        for match in LAYOUT_FETCH_RE.finditer(text):
            issues.append(
                f"{js_path}:{line_number(text, match.start())}: record fetch requests `layoutTypes`; prefer explicit fields unless layout metadata is required."
            )

        for match in NON_TRACKABLE_RE.finditer(text):
            issues.append(
                f"{js_path}:{line_number(text, match.start())}: `@track` is applied to a non-trackable object type; reassign new instances instead of mutating in place."
            )

        dynamic_imports = list(DYNAMIC_IMPORT_RE.finditer(text))
        if dynamic_imports:
            meta_path = component_meta_path(js_path)
            if not has_dynamic_component_capability(meta_path):
                issues.append(
                    f"{js_path}: uses dynamic `import()` but {meta_path.name} does not declare `lightning__dynamicComponent`."
                )

        for match in dynamic_imports:
            import_arg = match.group("arg").strip()
            if not re.match(r"""^['"][^'"]+['"]$""", import_arg):
                issues.append(
                    f"{js_path}:{line_number(text, match.start())}: dynamic import is not statically analyzable; prefer a string-literal import map when possible."
                )

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_lwc_performance(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
