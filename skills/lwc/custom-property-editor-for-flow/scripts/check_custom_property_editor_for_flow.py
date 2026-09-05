#!/usr/bin/env python3
"""check_custom_property_editor_for_flow.py — static checks for Flow custom property editors.

Scans an LWC source tree (and any Apex classes beside it) for the six failure modes that
break a custom property editor without breaking the build. Stdlib only.

Rules
  CPE-001 ERROR     a `configuration_editor_input_value_changed` dispatch whose `detail`
                    is missing `name`, `newValue` or `newValueDataType`
                    (lwc_guide use-flow-custom-property-editor-interface L9753-9756)
  CPE-002 WARN      a custom property editor bundle with no `@api validate()`
                    (lwc_guide L9731-9735 — validate() is the Done gate)
  CPE-003 WARN      a CPE bundle declaring page targets; every CPE configuration file in the
                    LWC Developer Guide is apiVersion + isExposed only, with no <targets>
                    (lwc_guide L9174, L9241, L9375, L9476, L9668)
  CPE-004 ERROR     a `configurationEditor` reference (js-meta.xml attribute or
                    @InvocableMethod modifier) with no matching bundle in the scanned tree
  CPE-005 ERROR     `inputVariables` / `genericTypeMappings` mutated in place instead of
                    dispatching an event (lwc_guide L9089, L9214 — it is a *copy*)
  CPE-006 ADVISORY  a `builderContext` read with no null guard; Flow Builder pushes it
                    asynchronously and `variables` is absent on a flow with no resources
  CPE-007 WARN      a configuration-editor event dispatched without `bubbles: true` and
                    `composed: true`; it never leaves the editor's shadow root
                    (lwc_guide L9736-9737)

Exit codes
  0  no ERROR findings (WARN / ADVISORY may be present)
  1  at least one ERROR, or --manifest-dir does not exist
     with --strict, WARN is promoted to ERROR

Usage
  python3 check_custom_property_editor_for_flow.py --manifest-dir force-app
  python3 check_custom_property_editor_for_flow.py --manifest-dir force-app --strict
  python3 check_custom_property_editor_for_flow.py --manifest-dir force-app --json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

MD_NS = "{http://soap.sforce.com/2006/04/metadata}"

CPE_EVENTS = (
    "configuration_editor_input_value_changed",
    "configuration_editor_input_value_deleted",
    "configuration_editor_generic_type_mapping_changed",
)
VALUE_CHANGED = "configuration_editor_input_value_changed"
REQUIRED_DETAIL_KEYS = ("name", "newValue", "newValueDataType")

PAGE_TARGETS = (
    "lightning__RecordPage",
    "lightning__AppPage",
    "lightning__HomePage",
    "lightning__Tab",
    "lightning__UtilityBar",
    "lightningCommunity__Page",
)

BUILDER_IFACES = ("inputVariables", "builderContext", "genericTypeMappings", "elementInfo")
VALIDATE_RE = re.compile(r"@api\s+(?:\r?\n\s*)?validate\s*\(", re.MULTILINE)
CONFIG_EDITOR_APEX_RE = re.compile(r"configurationEditor\s*=\s*['\"]([^'\"]+)['\"]")
MUTATE_INDEX_RE = re.compile(r"this\.(?:_)?(inputVariables|genericTypeMappings)\s*\[[^\]]*\]\s*=[^=]")
MUTATE_METHOD_RE = re.compile(
    r"this\.(?:_)?(inputVariables|genericTypeMappings)\s*\.\s*(push|pop|shift|unshift|splice|sort|reverse|fill)\s*\("
)
FIND_ASSIGN_RE = re.compile(
    r"(?:const|let|var)\s+(\w+)\s*=\s*this\.(?:_)?(?:inputVariables|genericTypeMappings)\s*\.\s*find\s*\("
)
BUILDER_READ_RE = re.compile(r"this\.(?:_)?builderContext\s*(\??\.)\s*(\w+)")


# --------------------------------------------------------------------------- helpers

def child(elem, tag):
    """Return the first child with `tag`, namespaced or not, or None.

    Never use `elem.find(a) or elem.find(b)`: an Element with no children is falsy,
    so a real match would be discarded. Always test `is not None`.
    """
    if elem is None:
        return None
    found = elem.find(MD_NS + tag)
    if found is not None:
        return found
    return elem.find(tag)


def children(elem, tag):
    if elem is None:
        return []
    found = elem.findall(MD_NS + tag)
    if found:
        return found
    return elem.findall(tag)


def kebab_to_bundle(reference: str) -> str:
    """`c-flow-record-summary-editor` -> `flowRecordSummaryEditor`."""
    ref = reference.strip()
    if "-" in ref:
        # drop the namespace segment
        ref = ref.split("-", 1)[1]
    parts = ref.split("-")
    if len(parts) == 1:
        return parts[0]
    return parts[0] + "".join(p[:1].upper() + p[1:] for p in parts[1:])


def strip_comments(js: str) -> str:
    js = re.sub(r"/\*.*?\*/", "", js, flags=re.DOTALL)
    js = re.sub(r"(?m)^\s*//.*$", "", js)
    return js


def brace_block(text: str, start: int) -> str:
    """Return the {...} block beginning at the first '{' at or after `start`."""
    open_idx = text.find("{", start)
    if open_idx == -1:
        return ""
    depth = 0
    for i in range(open_idx, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return text[open_idx : i + 1]
    return text[open_idx:]


def has_key(block: str, key: str) -> bool:
    """`key:` or the ES6 shorthand `key` as a bare property."""
    if re.search(r"\b" + re.escape(key) + r"\s*:", block):
        return True
    return bool(re.search(r"(?:[{,]\s*)" + re.escape(key) + r"\s*(?:,|\})", block))


# --------------------------------------------------------------------------- model

class Bundle:
    def __init__(self, directory: Path):
        self.dir = directory
        self.name = directory.name
        self.meta = directory / f"{directory.name}.js-meta.xml"
        self.js = directory / f"{directory.name}.js"
        self._js_text = None

    @property
    def js_text(self) -> str:
        if self._js_text is None:
            if self.js.exists():
                self._js_text = strip_comments(self.js.read_text(encoding="utf-8", errors="ignore"))
            else:
                self._js_text = ""
        return self._js_text

    @property
    def is_cpe(self) -> bool:
        text = self.js_text
        if any(evt in text for evt in CPE_EVENTS):
            return True
        # an @api / getter-setter pair over the Flow Builder interface
        return sum(1 for iface in BUILDER_IFACES if re.search(r"\b" + iface + r"\b", text)) >= 2


def discover_bundles(root: Path) -> dict[str, Bundle]:
    bundles: dict[str, Bundle] = {}
    for meta in root.rglob("*.js-meta.xml"):
        directory = meta.parent
        if meta.name != f"{directory.name}.js-meta.xml":
            continue
        bundles[directory.name] = Bundle(directory)
    return bundles


# --------------------------------------------------------------------------- rules

def check_events(bundle: Bundle, findings: list[dict]) -> None:
    text = bundle.js_text
    for match in re.finditer(r"['\"](" + "|".join(CPE_EVENTS) + r")['\"]", text):
        event = match.group(1)
        block = brace_block(text, match.end())
        line = text[: match.start()].count("\n") + 1
        location = f"{bundle.js}:{line}"
        if not block:
            continue
        if not re.search(r"\bbubbles\s*:\s*true", block) or not re.search(r"\bcomposed\s*:\s*true", block):
            findings.append(
                {
                    "rule": "CPE-007",
                    "severity": "WARN",
                    "location": location,
                    "message": (
                        f"`{event}` is dispatched without bubbles: true and composed: true; "
                        "it stops at the editor's shadow root and Flow Builder never sees it"
                    ),
                }
            )
        if event != VALUE_CHANGED:
            continue
        detail_idx = block.find("detail")
        if detail_idx == -1:
            findings.append(
                {
                    "rule": "CPE-001",
                    "severity": "ERROR",
                    "location": location,
                    "message": f"`{VALUE_CHANGED}` is dispatched with no `detail` object",
                }
            )
            continue
        detail = brace_block(block, detail_idx)
        missing = [k for k in REQUIRED_DETAIL_KEYS if not has_key(detail, k)]
        if missing:
            findings.append(
                {
                    "rule": "CPE-001",
                    "severity": "ERROR",
                    "location": location,
                    "message": (
                        f"`{VALUE_CHANGED}` detail is missing {', '.join('`' + m + '`' for m in missing)}; "
                        "Flow Builder requires name, newValue and newValueDataType"
                    ),
                }
            )


def check_validate(bundle: Bundle, findings: list[dict]) -> None:
    if VALIDATE_RE.search(bundle.js_text):
        return
    findings.append(
        {
            "rule": "CPE-002",
            "severity": "WARN",
            "location": str(bundle.js),
            "message": (
                "custom property editor has no `@api validate()`; Flow Builder cannot block "
                "Done on an incomplete configuration. Return an array of { key, errorString }"
            ),
        }
    )


def check_cpe_targets(bundle: Bundle, findings: list[dict]) -> None:
    if not bundle.meta.exists():
        return
    try:
        root = ET.parse(bundle.meta).getroot()
    except ET.ParseError as exc:
        findings.append(
            {
                "rule": "CPE-003",
                "severity": "ERROR",
                "location": str(bundle.meta),
                "message": f"js-meta.xml does not parse: {exc}",
            }
        )
        return
    targets_elem = child(root, "targets")
    if targets_elem is None:
        return
    declared = [t.text.strip() for t in children(targets_elem, "target") if t.text]
    offenders = [t for t in declared if t in PAGE_TARGETS]
    if offenders:
        findings.append(
            {
                "rule": "CPE-003",
                "severity": "WARN",
                "location": str(bundle.meta),
                "message": (
                    f"custom property editor bundle declares page target(s) {', '.join(offenders)}; "
                    "a CPE is not a page component — the guide's CPE configuration files carry "
                    "apiVersion and isExposed only"
                ),
            }
        )


def check_mutation(bundle: Bundle, findings: list[dict]) -> None:
    text = bundle.js_text
    for regex in (MUTATE_INDEX_RE, MUTATE_METHOD_RE):
        for match in regex.finditer(text):
            line = text[: match.start()].count("\n") + 1
            findings.append(
                {
                    "rule": "CPE-005",
                    "severity": "ERROR",
                    "location": f"{bundle.js}:{line}",
                    "message": (
                        f"`{match.group(1)}` is mutated in place; it is a copy of the flow metadata, "
                        "so the change is lost. Dispatch a configuration-editor event instead"
                    ),
                }
            )
    for match in FIND_ASSIGN_RE.finditer(text):
        var = match.group(1)
        tail = text[match.end() :]
        assign = re.search(r"\b" + re.escape(var) + r"\s*\.\s*(value|typeValue)\s*=[^=]", tail)
        if assign:
            line = text[: match.end() + assign.start()].count("\n") + 1
            findings.append(
                {
                    "rule": "CPE-005",
                    "severity": "ERROR",
                    "location": f"{bundle.js}:{line}",
                    "message": (
                        f"`{var}` came from a find() over the builder's copy and is written to in place; "
                        "dispatch configuration_editor_input_value_changed instead"
                    ),
                }
            )


def check_builder_guard(bundle: Bundle, findings: list[dict]) -> None:
    text = bundle.js_text
    # a setter that defaults to {} counts as the guard for the whole file
    if re.search(r"set\s+builderContext\s*\([^)]*\)\s*\{[^}]*\|\|\s*\{\s*\}", text, re.DOTALL):
        return
    lines = text.splitlines()
    for idx, line in enumerate(lines, start=1):
        match = BUILDER_READ_RE.search(line)
        if not match:
            continue
        if match.group(1) == "?.":
            continue
        if "||" in line or "&&" in line:
            continue
        findings.append(
            {
                "rule": "CPE-006",
                "severity": "ADVISORY",
                "location": f"{bundle.js}:{idx}",
                "message": (
                    f"`builderContext.{match.group(2)}` is read with no null guard; Flow Builder "
                    "pushes builderContext asynchronously and `variables` is absent on a new flow"
                ),
            }
        )


def check_references(root: Path, bundles: dict[str, Bundle], findings: list[dict]) -> set[str]:
    """Every configurationEditor reference must resolve to a bundle in the tree."""
    referenced: set[str] = set()

    for bundle in bundles.values():
        if not bundle.meta.exists():
            continue
        try:
            meta_root = ET.parse(bundle.meta).getroot()
        except ET.ParseError:
            continue
        configs = child(meta_root, "targetConfigs")
        for cfg in children(configs, "targetConfig"):
            ref = cfg.get("configurationEditor")
            if not ref:
                continue
            resolved = kebab_to_bundle(ref)
            referenced.add(resolved)
            if resolved not in bundles:
                findings.append(
                    {
                        "rule": "CPE-004",
                        "severity": "ERROR",
                        "location": str(bundle.meta),
                        "message": (
                            f"configurationEditor=\"{ref}\" resolves to bundle `{resolved}`, "
                            "which is not in the scanned tree; Flow Builder falls back to the "
                            "default property pane"
                        ),
                    }
                )
            elif resolved == bundle.name:
                findings.append(
                    {
                        "rule": "CPE-004",
                        "severity": "ERROR",
                        "location": str(bundle.meta),
                        "message": (
                            f"configurationEditor=\"{ref}\" points at this component's own bundle; "
                            "the editor must be a separate LWC"
                        ),
                    }
                )

    for cls in root.rglob("*.cls"):
        try:
            text = cls.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for match in CONFIG_EDITOR_APEX_RE.finditer(text):
            ref = match.group(1)
            resolved = kebab_to_bundle(ref)
            referenced.add(resolved)
            if resolved not in bundles:
                line = text[: match.start()].count("\n") + 1
                findings.append(
                    {
                        "rule": "CPE-004",
                        "severity": "ERROR",
                        "location": f"{cls}:{line}",
                        "message": (
                            f"@InvocableMethod(configurationEditor='{ref}') resolves to bundle "
                            f"`{resolved}`, which is not in the scanned tree"
                        ),
                    }
                )
    return referenced


# --------------------------------------------------------------------------- main

def run(root: Path) -> tuple[list[dict], int, int]:
    findings: list[dict] = []
    bundles = discover_bundles(root)
    check_references(root, bundles, findings)
    cpes = [b for b in bundles.values() if b.is_cpe]
    for bundle in sorted(cpes, key=lambda b: b.name):
        check_events(bundle, findings)
        check_validate(bundle, findings)
        check_cpe_targets(bundle, findings)
        check_mutation(bundle, findings)
        check_builder_guard(bundle, findings)
    findings.sort(key=lambda f: (f["location"], f["rule"]))
    return findings, len(bundles), len(cpes)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--manifest-dir", default=".", help="Root of the source tree to scan (e.g. force-app).")
    parser.add_argument("--strict", action="store_true", help="Promote WARN findings to ERROR.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text.")
    args = parser.parse_args()

    root = Path(args.manifest_dir)
    if not root.exists() or not root.is_dir():
        print(f"ERROR: --manifest-dir {root} does not exist", file=sys.stderr)
        return 1

    findings, bundle_count, cpe_count = run(root)

    if args.strict:
        for finding in findings:
            if finding["severity"] == "WARN":
                finding["severity"] = "ERROR"
                finding["promoted"] = True

    errors = sum(1 for f in findings if f["severity"] == "ERROR")
    warns = sum(1 for f in findings if f["severity"] == "WARN")
    advisories = sum(1 for f in findings if f["severity"] == "ADVISORY")

    if bundle_count == 0:
        print(f"WARN: no LWC bundles found under {root} (looked for <dir>/<dir>.js-meta.xml)")
        if args.json:
            print(json.dumps({"findings": [], "bundles": 0, "custom_property_editors": 0}, indent=2))
        return 0

    if args.json:
        print(
            json.dumps(
                {
                    "manifest_dir": str(root),
                    "bundles": bundle_count,
                    "custom_property_editors": cpe_count,
                    "errors": errors,
                    "warnings": warns,
                    "advisories": advisories,
                    "findings": findings,
                },
                indent=2,
            )
        )
    else:
        for finding in findings:
            print(f"{finding['severity']:9} {finding['rule']}  {finding['location']}\n          {finding['message']}")
        print(
            f"\nScanned {bundle_count} LWC bundle(s), {cpe_count} custom property editor(s): "
            f"{errors} ERROR, {warns} WARN, {advisories} ADVISORY."
        )
        if cpe_count == 0:
            print("No custom property editor bundle was recognised; CPE-001/002/003/005/006/007 did not run.")

    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
