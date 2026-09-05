#!/usr/bin/env python3
"""check_lwc_base_component_recipes.py — audit an LWC source tree for base-component defects.

Stdlib only. Reads a Salesforce source tree (``--manifest-dir``) and reports the base-component
composition and contract failures that deploy cleanly and then misbehave at runtime.

Every rule below is grounded in the Lightning Web Components Developer Guide; the page slug and
crawled line number are printed with each finding so a reviewer can check the claim. The Component
Library remains the authority for per-component attribute contracts — this checker deliberately
tests only the rules the Developer Guide itself states.

Rules
-----
ERROR  ``lightning-input`` / ``lightning-combobox`` / ``lightning-select`` / ``lightning-radio-group``
       / ``lightning-checkbox-group`` with neither ``label`` nor ``aria-label``
       (create-components-accessibility-attributes L3987-L3988, L3999; base-components-accessibility L4958-L4960)
ERROR  ``lightning-output-field`` that is not a direct child of ``lightning-record-view-form``
       (migrate-map-aura-lwc-components L11727)
ERROR  ``lightning-datatable`` without a ``key-field`` attribute (data-table-inline-edit L5675)
ERROR  a ``*options*`` array literal in a bundle using ``lightning-combobox`` whose object items are
       missing a ``label`` or a ``value`` key (base-components-compose L4875; data-wire-base-components L6614)
WARN   a raw ``<button class="slds-button …">`` where ``lightning-button`` exists
       (base-components-all L4543; create-components-css-slds-blueprint L1737)
WARN   ``lightning-datatable`` / ``lightning-tree-grid`` in a bundle whose ``.js-meta.xml`` declares
       ``<supportedFormFactor type="Small"/>`` (data-table-vs-tree-grid L5600; targets-lightning-record-page L19373-L19375)
WARN   a Jest test calling ``getAttribute`` on a queried ``lightning-*`` stub
       (unit-testing-using-jest-patterns L12626)
WARN   ``lightning/platformShowToastEvent`` imported in a bundle targeting an LWR Experience Cloud
       page (base-components-all L4649; base-components-patterns L4773)
WARN   a component other than ``lightning-layout-item`` placed directly inside ``lightning-layout``
       (migrate-map-aura-lwc-components L11707)
WARN   editable datatable columns with no ``draft-values`` binding (data-table-inline-edit L5675)
WARN   a datatable bundle whose ``onsave`` / ``handleSave`` handler never resets ``this.draftValues``
       (data-table-inline-edit L5712)
WARN   ``lightning-record-edit-form`` with no ``lightning-messages`` child (data-edit-record L5489)
WARN   ``lightning-record-edit-form`` inside an ``if:true`` / ``lwc:if`` block (unsaved input is discarded)

Exit codes
----------
1  ``--manifest-dir`` does not exist, or any ERROR was reported
0  otherwise (WARNs alone do not fail unless ``--strict`` promotes them)

Usage
-----
    python3 check_lwc_base_component_recipes.py --manifest-dir force-app/main/default/lwc
    python3 check_lwc_base_component_recipes.py --manifest-dir force-app --strict
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

META_NS = "{http://soap.sforce.com/2006/04/metadata}"

# ---------------------------------------------------------------------------- patterns --

COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
TAG_RE = re.compile(r"<(/?)([A-Za-z][\w:.-]*)((?:\"[^\"]*\"|'[^']*'|[^>\"'])*?)(/?)>", re.DOTALL)
VOID_TAGS = {
    "area", "base", "br", "col", "embed", "hr", "img", "input",
    "link", "meta", "param", "source", "track", "wbr",
}
# Components that take a user-facing label as their accessibility contract.
LABEL_REQUIRED = (
    "lightning-input",
    "lightning-combobox",
    "lightning-select",
    "lightning-radio-group",
    "lightning-checkbox-group",
    "lightning-textarea",
    "lightning-dual-listbox",
)
LABEL_ATTR_RE = re.compile(r"(?:^|\s)(?:label|aria-label|aria-labelledby)\s*=", re.IGNORECASE)
SLDS_BUTTON_RE = re.compile(
    r"<button\b(?:\"[^\"]*\"|'[^']*'|[^>\"'])*?class\s*=\s*[\"'][^\"']*\bslds-button\b",
    re.IGNORECASE | re.DOTALL,
)
DATATABLE_RE = re.compile(r"<lightning-(?:datatable|tree-grid)\b", re.IGNORECASE)
KEY_FIELD_RE = re.compile(r"\bkey-field\s*=", re.IGNORECASE)
DRAFT_VALUES_RE = re.compile(r"\bdraft-values\s*=", re.IGNORECASE)
EDITABLE_RE = re.compile(r"\beditable\s*:\s*true", re.IGNORECASE)
DRAFT_RESET_RE = re.compile(r"this\s*\.\s*draftValues\s*=\s*\[\s*\]")
SAVE_HANDLER_RE = re.compile(r"\bhandleSave\s*\(|\bonsave\s*=", re.IGNORECASE)
EDIT_FORM_RE = re.compile(r"<lightning-record-edit-form\b", re.IGNORECASE)
MESSAGES_RE = re.compile(r"<lightning-messages\b", re.IGNORECASE)
CONDITIONAL_RE = re.compile(r"\bif:true\b|\bif:false\b|\blwc:if\b|\blwc:elseif\b", re.IGNORECASE)
TOAST_EVENT_RE = re.compile(r"lightning/platformShowToastEvent")
LWR_TARGET_RE = re.compile(r"lightningCommunity__")
QUERY_STUB_RE = re.compile(
    r"(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*[^;\n]*?querySelector(?:All)?\(\s*['\"]lightning-[\w-]+",
)
CHAINED_GET_ATTR_RE = re.compile(
    r"querySelector(?:All)?\(\s*['\"]lightning-[\w-]+['\"]\s*\)\s*(?:\??\.\s*[\w$]+\s*)*\??\.\s*getAttribute\s*\(",
)
OPTIONS_ARRAY_RE = re.compile(r"([A-Za-z_$][\w$]*[Oo]ptions)\s*=\s*\[(.*?)\]\s*;", re.DOTALL)
OBJECT_ITEM_RE = re.compile(r"\{[^{}]*\}")
LABEL_KEY_RE = re.compile(r"(?:^|[{,\s])(?:label|'label'|\"label\")\s*:")
VALUE_KEY_RE = re.compile(r"(?:^|[{,\s])(?:value|'value'|\"value\")\s*:")
COMBOBOX_RE = re.compile(r"<lightning-combobox\b", re.IGNORECASE)


# ---------------------------------------------------------------------------- finding --

class Finding:
    __slots__ = ("level", "where", "message")

    def __init__(self, level: str, where: str, message: str) -> None:
        self.level = level
        self.where = where
        self.message = message

    def render(self) -> str:
        return f"{self.level}: {self.where}: {self.message}"


def _line_of(text: str, index: int) -> int:
    return text.count("\n", 0, index) + 1


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _strip_comments(html: str) -> str:
    """Blank comment bodies but keep their length so offsets stay line-accurate."""
    return COMMENT_RE.sub(lambda m: re.sub(r"[^\n]", " ", m.group(0)), html)


# ---------------------------------------------------------------------- metadata (XML) --

def _find_first(parent, *tag_names):
    """Return the first matching child Element, or None.

    Never use ``parent.find(a) or parent.find(b)`` — an Element with no children is falsy,
    so a real match would be discarded. Test ``is not None`` explicitly.
    """
    for tag in tag_names:
        found = parent.find(tag)
        if found is not None:
            return found
    return None


def _iter_text(root, tag_name: str) -> list[str]:
    return [(el.text or "").strip() for el in root.iter(tag_name) if (el.text or "").strip()]


class BundleMeta:
    """What the ``.js-meta.xml`` says, with parse failures reported rather than swallowed."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.parse_error: str | None = None
        self.targets: list[str] = []
        self.form_factors: list[str] = []
        try:
            root = ET.fromstring(_read(path).encode("utf-8"))
        except ET.ParseError as exc:
            self.parse_error = str(exc)
            return
        self.targets = _iter_text(root, f"{META_NS}target") + _iter_text(root, "target")
        for tag in (f"{META_NS}supportedFormFactor", "supportedFormFactor"):
            for el in root.iter(tag):
                kind = el.get("type")
                if kind:
                    self.form_factors.append(kind)

    @property
    def has_small_form_factor(self) -> bool:
        return any(f.strip().lower() == "small" for f in self.form_factors)

    @property
    def is_lwr_site_component(self) -> bool:
        return any(LWR_TARGET_RE.search(t) for t in self.targets)


# ------------------------------------------------------------------- html tag scanning --

class TagEvent:
    __slots__ = ("name", "attrs", "index", "parent")

    def __init__(self, name: str, attrs: str, index: int, parent: str | None) -> None:
        self.name = name
        self.attrs = attrs
        self.index = index
        self.parent = parent


def scan_tags(html: str) -> list[TagEvent]:
    """Walk the template keeping a tag stack so each open tag knows its immediate parent."""
    events: list[TagEvent] = []
    stack: list[str] = []
    for match in TAG_RE.finditer(html):
        closing, name, attrs, self_closing = match.groups()
        lowered = name.lower()
        if closing:
            for i in range(len(stack) - 1, -1, -1):
                if stack[i] == lowered:
                    del stack[i:]
                    break
            continue
        events.append(TagEvent(lowered, attrs or "", match.start(), stack[-1] if stack else None))
        if not self_closing and lowered not in VOID_TAGS:
            stack.append(lowered)
    return events


# ----------------------------------------------------------------------------- checks --

def check_labels(path: Path, html: str, events: list[TagEvent]) -> list[Finding]:
    out: list[Finding] = []
    for ev in events:
        if not ev.name.startswith("lightning-"):
            continue
        if ev.name not in LABEL_REQUIRED:
            continue
        if LABEL_ATTR_RE.search(ev.attrs):
            continue
        out.append(Finding(
            "ERROR",
            f"{path}:{_line_of(html, ev.index)}",
            f"<{ev.name}> has neither a `label` nor an `aria-label`. Base components associate the "
            f"label you provide with the input automatically; without one the control has no "
            f"programmatic label (lwc_guide create-components-accessibility-attributes L3987-L3988, "
            f"L3999; base-components-accessibility L4958-L4960).",
        ))
    return out


def check_output_field_parent(path: Path, html: str, events: list[TagEvent]) -> list[Finding]:
    out: list[Finding] = []
    for ev in events:
        if ev.name != "lightning-output-field":
            continue
        if ev.parent == "lightning-record-view-form":
            continue
        out.append(Finding(
            "ERROR",
            f"{path}:{_line_of(html, ev.index)}",
            f"<lightning-output-field> is nested inside <{ev.parent or 'template'}>. It must be a "
            f"direct child of lightning-record-view-form and must not be nested in another element "
            f"such as lightning-layout — it renders nothing otherwise "
            f"(lwc_guide migrate-map-aura-lwc-components L11727).",
        ))
    return out


def check_layout_children(path: Path, html: str, events: list[TagEvent]) -> list[Finding]:
    out: list[Finding] = []
    for ev in events:
        if ev.parent != "lightning-layout":
            continue
        if ev.name == "lightning-layout-item":
            continue
        if not (ev.name.startswith("lightning-") or ev.name.startswith("c-")):
            continue  # plain HTML tags and text are allowed between layout items
        out.append(Finding(
            "WARN",
            f"{path}:{_line_of(html, ev.index)}",
            f"<{ev.name}> sits directly inside <lightning-layout>. lightning-layout does not allow "
            f"expressions or other components between lightning-layout-item components — only HTML "
            f"tags and text. Wrap it in a lightning-layout-item "
            f"(lwc_guide migrate-map-aura-lwc-components L11707).",
        ))
    return out


def check_slds_button(path: Path, html: str) -> list[Finding]:
    out: list[Finding] = []
    for match in SLDS_BUTTON_RE.finditer(html):
        out.append(Finding(
            "WARN",
            f"{path}:{_line_of(html, match.start())}",
            "raw <button class=\"slds-button …\"> where lightning-button exists. Use base components "
            "instead of building from an SLDS guideline: Salesforce updates base components when SLDS "
            "updates the blueprint, but blueprint markup you copied is yours to maintain "
            "(lwc_guide base-components-all L4543; create-components-css-slds-blueprint L1737).",
        ))
    return out


def check_datatable_contract(path: Path, html: str) -> list[Finding]:
    out: list[Finding] = []
    if not DATATABLE_RE.search(html):
        return out
    if not KEY_FIELD_RE.search(html):
        out.append(Finding(
            "ERROR",
            str(path),
            "lightning-datatable without a `key-field` attribute. key-field is required — it is what "
            "associates each row with a record (lwc_guide data-table-inline-edit L5675).",
        ))
    if EDITABLE_RE.search(html) and not DRAFT_VALUES_RE.search(html):
        out.append(Finding(
            "WARN",
            str(path),
            "editable datatable columns with no `draft-values` binding. Edited values are stored in "
            "draft-values; without the binding the inline edits are not readable on save "
            "(lwc_guide data-table-inline-edit L5675).",
        ))
    return out


def check_datatable_form_factor(bundle: Path, html_has_table: bool, meta: BundleMeta) -> list[Finding]:
    if not html_has_table or not meta.has_small_form_factor:
        return []
    return [Finding(
        "WARN",
        str(meta.path),
        f"bundle {bundle.name} contains lightning-datatable or lightning-tree-grid and declares "
        f"<supportedFormFactor type=\"Small\"/>. Neither component is supported on mobile devices "
        f"(lwc_guide data-table-vs-tree-grid L5600); Small is the phone form factor "
        f"(targets-lightning-record-page L19373-L19375). Drop Small, or compose the rows from "
        f"lightning-layout / lightning-tile instead.",
    )]


def check_draft_values_reset(path: Path, js: str, bundle_has_datatable: bool) -> list[Finding]:
    # Only a datatable has a draft-values contract; a save handler in any other component is
    # unrelated and must not be flagged.
    if not bundle_has_datatable:
        return []
    if not SAVE_HANDLER_RE.search(js):
        return []
    if DRAFT_RESET_RE.search(js):
        return []
    return [Finding(
        "WARN",
        str(path),
        "a save handler exists but `draftValues = []` never runs. Clearing draftValues is what hides "
        "the datatable's Save/Cancel footer; a stale array replays edits on the next save "
        "(lwc_guide data-table-inline-edit L5712).",
    )]


def check_edit_form(path: Path, html: str) -> list[Finding]:
    out: list[Finding] = []
    for match in EDIT_FORM_RE.finditer(html):
        line = _line_of(html, match.start())
        preceding = html[max(0, match.start() - 400):match.start()]
        if CONDITIONAL_RE.search(preceding):
            out.append(Finding(
                "WARN",
                f"{path}:{line}",
                "lightning-record-edit-form appears inside an if:true / lwc:if block. Toggling the "
                "condition destroys the form element and discards unsaved field values — hide it with "
                "an slds-hide class toggle instead.",
            ))
        break
    if EDIT_FORM_RE.search(html) and not MESSAGES_RE.search(html):
        out.append(Finding(
            "WARN",
            str(path),
            "lightning-record-edit-form with no lightning-messages child. Include lightning-messages "
            "before or after the input fields to display server-side save errors automatically "
            "(lwc_guide data-edit-record L5489).",
        ))
    return out


def check_toast_on_lwr(path: Path, js: str, meta: BundleMeta) -> list[Finding]:
    if not meta.is_lwr_site_component:
        return []
    if not TOAST_EVENT_RE.search(js):
        return []
    return [Finding(
        "WARN",
        str(path),
        "lightning/platformShowToastEvent imported in a bundle targeting an Experience Cloud page "
        f"({', '.join(sorted(t for t in meta.targets if LWR_TARGET_RE.search(t)))}). It uses an "
        "event-based mechanism and is not supported in LWR sites — use lightning/toast instead "
        "(lwc_guide base-components-all L4649; base-components-patterns L4773).",
    )]


def check_stub_get_attribute(path: Path, js: str) -> list[Finding]:
    out: list[Finding] = []
    stub_vars = {m.group(1) for m in QUERY_STUB_RE.finditer(js)}
    for match in CHAINED_GET_ATTR_RE.finditer(js):
        out.append(Finding(
            "WARN",
            f"{path}:{_line_of(js, match.start())}",
            "getAttribute() called on a queried lightning-* stub. Base components have properties "
            "that are not reflected as DOM attributes, so the assertion passes or fails for reasons "
            "unrelated to the component — read the property off the stub instead "
            "(lwc_guide unit-testing-using-jest-patterns L12626).",
        ))
    for var in sorted(stub_vars):
        for match in re.finditer(rf"\b{re.escape(var)}\s*\??\.\s*getAttribute\s*\(", js):
            out.append(Finding(
                "WARN",
                f"{path}:{_line_of(js, match.start())}",
                f"`{var}` holds a lightning-* stub and getAttribute() is called on it. Base component "
                f"properties are not all reflected as attributes; read `{var}.<property>` instead "
                f"(lwc_guide unit-testing-using-jest-patterns L12626).",
            ))
    return out


def check_combobox_options(path: Path, js: str, bundle_has_combobox: bool) -> list[Finding]:
    if not bundle_has_combobox:
        return []
    out: list[Finding] = []
    for match in OPTIONS_ARRAY_RE.finditer(js):
        name, body = match.group(1), match.group(2)
        for item in OBJECT_ITEM_RE.finditer(body):
            text = item.group(0)
            missing = []
            if not LABEL_KEY_RE.search(text):
                missing.append("label")
            if not VALUE_KEY_RE.search(text):
                missing.append("value")
            if not missing:
                continue
            out.append(Finding(
                "ERROR",
                f"{path}:{_line_of(js, match.start(2) + item.start())}",
                f"`{name}` item is missing {' and '.join(missing)}. lightning-combobox takes the "
                f"label and value that describe a menu item on its options attribute; save `value` "
                f"(the untranslated API name) and display `label` "
                f"(lwc_guide base-components-compose L4875; data-wire-base-components L6614; "
                f"reference-wire-adapters-picklist-values L14963-L14964).",
            ))
    return out


# ------------------------------------------------------------------------ file finding --

def component_bundles(root: Path) -> list[Path]:
    """A bundle is a directory holding <dirname>.js next to <dirname>.js-meta.xml."""
    bundles: list[Path] = []
    for meta in sorted(root.rglob("*.js-meta.xml")):
        bundle = meta.parent
        if (bundle / f"{bundle.name}.js").exists():
            bundles.append(bundle)
    return bundles


def loose_templates(root: Path, bundles: list[Path]) -> list[Path]:
    """HTML templates that are not inside a recognised bundle — still worth checking."""
    known = {b.resolve() for b in bundles}
    out: list[Path] = []
    for html in sorted(root.rglob("*.html")):
        if html.parent.resolve() not in known:
            out.append(html)
    return out


def _check_template(path: Path, findings: list[Finding]) -> tuple[bool, bool]:
    """Run every template rule. Returns (has_datatable, has_combobox)."""
    raw = _read(path)
    html = _strip_comments(raw)
    events = scan_tags(html)
    findings.extend(check_labels(path, html, events))
    findings.extend(check_output_field_parent(path, html, events))
    findings.extend(check_layout_children(path, html, events))
    findings.extend(check_slds_button(path, html))
    findings.extend(check_datatable_contract(path, html))
    findings.extend(check_edit_form(path, html))
    return bool(DATATABLE_RE.search(html)), bool(COMBOBOX_RE.search(html))


def run(root: Path) -> tuple[list[Finding], int, int]:
    findings: list[Finding] = []
    bundles = component_bundles(root)

    for bundle in bundles:
        meta = BundleMeta(bundle / f"{bundle.name}.js-meta.xml")
        if meta.parse_error:
            findings.append(Finding(
                "ERROR", str(meta.path), f"could not be parsed as XML — {meta.parse_error}",
            ))
        has_datatable = False
        has_combobox = False
        for html_path in sorted(bundle.glob("*.html")):
            table, combo = _check_template(html_path, findings)
            has_datatable = has_datatable or table
            has_combobox = has_combobox or combo
        findings.extend(check_datatable_form_factor(bundle, has_datatable, meta))

        for js_path in sorted(bundle.rglob("*.js")):
            js = _read(js_path)
            is_test = "__tests__" in js_path.parts or js_path.name.endswith((".test.js", ".spec.js"))
            if is_test:
                findings.extend(check_stub_get_attribute(js_path, js))
                continue
            findings.extend(check_draft_values_reset(js_path, js, has_datatable))
            findings.extend(check_toast_on_lwr(js_path, js, meta))
            findings.extend(check_combobox_options(js_path, js, has_combobox))

    extra = loose_templates(root, bundles)
    for html_path in extra:
        _check_template(html_path, findings)

    return findings, len(bundles), len(extra)


# ------------------------------------------------------------------------------- main --

def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Audit an LWC source tree for base-component composition and contract defects "
            "(labels, output-field nesting, layout children, datatable form factor, combobox "
            "options, raw SLDS markup, LWR toasts, Jest stub assertions)."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root of the LWC source tree (for example force-app/main/default/lwc).",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Promote every WARN to an ERROR (use in CI).",
    )
    args = parser.parse_args()

    root = Path(args.manifest_dir)
    if not root.is_dir():
        print(f"ERROR: --manifest-dir not found: {root}")
        return 1

    findings, bundle_count, extra_count = run(root)

    if bundle_count == 0 and extra_count == 0:
        print(f"WARN: {root}: no LWC bundles and no HTML templates found — nothing to check.")
        return 0

    if args.strict:
        for finding in findings:
            if finding.level == "WARN":
                finding.level = "ERROR"

    for finding in sorted(findings, key=lambda f: (f.level != "ERROR", f.where)):
        print(finding.render())

    errors = sum(1 for f in findings if f.level == "ERROR")
    warns = len(findings) - errors
    print(
        f"\n{bundle_count} bundle(s), {extra_count} loose template(s) scanned — "
        f"{errors} ERROR, {warns} WARN"
    )
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
