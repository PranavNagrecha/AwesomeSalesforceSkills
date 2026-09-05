#!/usr/bin/env python3
"""check_lwc_data_table.py — static checks for lightning-datatable bundles.

Stdlib only. Walks a Salesforce source tree and inspects every LWC bundle that
renders a datatable (`<lightning-datatable>` or a component extending
`LightningDatatable`).

Checks implemented
------------------
1.  DT001  a datatable element with no `key-field`
            -> "The required key-field attribute associates each row with a
               record" (LWC Developer Guide, data-table-inline-edit L5675).
2.  DT002  `draft-values` bound with no `onsave` handler, or an `onsave`
            handler name that is not defined in the bundle's JS
            (data-table-inline-edit L5676).
3.  DT003  `enable-infinite-loading` with no `onloadmore` handler
            (data-table-performance L6313).
4.  DT004  a column `fieldName` that resolves to neither a field in the wired
            Apex method's SELECT list nor a key the shaping layer adds
            (data-table-custom-types L5812). Reported only when the Apex class
            is present in the tree, so the row shape is actually knowable.
5.  DT005  in-place mutation of the array bound to `data=` — `push`, `splice`,
            `sort`, `unshift`, `reverse`, `pop`, `shift`, or an indexed
            assignment. LWC compares with `===`, so the table will not
            rerender (reactivity-fields L2287-L2288).
6.  DT006  a class extending `LightningDatatable` with no `static customTypes`,
            an entry with `editTemplate` but no `standardCellLayout: true`
            (data-table-custom-types L5804-L5806;
            data-table-custom-types-styling L6092-L6097), or a
            `connectedCallback` override with no `super.connectedCallback()`
            (data-table-custom-types L5857-L5859).
7.  DT007  a datatable bundle with no `__tests__` folder, or a `__tests__`
            folder with no `describe(` block
            (unit-testing-using-jest-create-tests L12328, L12331).
8.  DT008  a `-meta.xml` that is missing, unparseable, or has no `apiVersion`.

Usage
-----
    python3 check_lwc_data_table.py --manifest-dir force-app/main/default
    python3 check_lwc_data_table.py --manifest-dir force-app --json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

MD_NS = "{http://soap.sforce.com/2006/04/metadata}"

# --- markup -----------------------------------------------------------------
# Any element carrying both data= and columns= is datatable-shaped, which
# catches `<c-my-datatable>` wrappers as well as `<lightning-datatable>`.
ELEMENT_RE = re.compile(r"<([a-zA-Z][\w-]*)((?:\s+[^<>]*?)?)/?>", re.S)
DATATABLE_TAG_RE = re.compile(r"^(lightning-datatable|lightning-tree-grid)$", re.I)
ATTR_BIND_RE = re.compile(r"([a-zA-Z][\w-]*)\s*=\s*\{\s*([A-Za-z_$][\w$.]*)\s*\}")
ATTR_LITERAL_RE = re.compile(r"([a-zA-Z][\w-]*)\s*=\s*\"([^\"]*)\"")
# Valueless attributes such as `enable-infinite-loading` carry no `=` at all.
ATTR_BARE_RE = re.compile(r"(?<![\w-])([a-zA-Z][\w-]*)(?!\s*=)(?=\s|/|$)")

# --- javascript -------------------------------------------------------------
FIELDNAME_RE = re.compile(r"\bfieldName\s*:\s*['\"]([^'\"]+)['\"]")
APEX_IMPORT_RE = re.compile(
    r"import\s+(\w+)\s+from\s+['\"]@salesforce/apex/(?:([\w]+)\.)?(\w+)\.(\w+)['\"]"
)
EXTENDS_DT_RE = re.compile(r"class\s+\w+\s+extends\s+LightningDatatable\b")
STATIC_CUSTOM_TYPES_RE = re.compile(r"\bstatic\s+(?:get\s+)?customTypes\b")
CUSTOM_TYPE_ENTRY_RE = re.compile(r"(\w+)\s*:\s*\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}", re.S)
CONNECTED_CB_RE = re.compile(r"\bconnectedCallback\s*\([^)]*\)\s*\{")
SUPER_CONNECTED_RE = re.compile(r"\bsuper\s*\.\s*connectedCallback\s*\(")
METHOD_DEF_RE = re.compile(r"^\s*(?:async\s+)?([A-Za-z_$][\w$]*)\s*\([^)]*\)\s*\{", re.M)
# Any `identifier:` in the file. Deliberately over-broad: this set only ever
# suppresses a DT004 warning, so over-collecting costs recall, never precision.
OBJECT_KEY_RE = re.compile(r"(?<![\w$.'\"])([A-Za-z_$][\w$]*)\s*:(?!:)")
MUTATORS = ("push", "splice", "sort", "unshift", "reverse", "pop", "shift", "fill", "copyWithin")

# --- apex -------------------------------------------------------------------
SELECT_RE = re.compile(r"\bSELECT\b(.*?)\bFROM\b", re.I | re.S)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Static checks for lightning-datatable LWC bundles.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root of the Salesforce source tree (default: current directory).",
    )
    parser.add_argument(
        "--json", action="store_true", help="Emit findings as JSON instead of text."
    )
    return parser.parse_args()


def read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def strip_comments(js: str) -> str:
    """Remove // and /* */ comments so they cannot trip the regexes."""
    js = re.sub(r"/\*.*?\*/", " ", js, flags=re.S)
    js = re.sub(r"(?m)^\s*//.*$", "", js)
    return js


def find_bundles(root: Path) -> list[Path]:
    """An LWC bundle is a directory holding <dirname>.js."""
    bundles: list[Path] = []
    for js in root.rglob("*.js"):
        if "__tests__" in js.parts or "node_modules" in js.parts:
            continue
        if js.stem == js.parent.name:
            bundles.append(js.parent)
    return sorted(set(bundles))


def markup_elements(html: str) -> list[tuple[str, str]]:
    return [(m.group(1), m.group(2) or "") for m in ELEMENT_RE.finditer(html)]


def is_datatable(tag: str, attrs: str) -> bool:
    if DATATABLE_TAG_RE.match(tag):
        return True
    bound = {m.group(1).lower() for m in ATTR_BIND_RE.finditer(attrs)}
    return "data" in bound and "columns" in bound


def apex_select_fields(root: Path, class_name: str, method_name: str) -> set[str] | None:
    """Return the SELECT list of the named Apex method, or None if not found."""
    for cls in root.rglob(f"{class_name}.cls"):
        body = read(cls)
        idx = body.find(f" {method_name}(")
        if idx == -1:
            idx = body.find(f"{method_name}(")
        if idx == -1:
            continue
        tail = body[idx:]
        match = SELECT_RE.search(tail)
        if not match:
            return set()
        fields: set[str] = set()
        for raw in match.group(1).split(","):
            token = raw.strip().split()[0] if raw.strip() else ""
            token = token.strip("()")
            if not token or "(" in token:
                continue
            fields.add(token)
            if "." in token:
                fields.add(token.split(".")[0])
        return fields
    return None


def derived_keys(js: str) -> set[str]:
    """Keys the component's own shaping layer adds to a row object."""
    return {m.group(1) for m in OBJECT_KEY_RE.finditer(js)}


def check_bundle(bundle: Path, root: Path) -> list[dict]:
    name = bundle.name
    issues: list[dict] = []
    html_files = sorted(bundle.glob("*.html"))
    js_main = bundle / f"{name}.js"
    js_raw = read(js_main)
    js = strip_comments(js_raw)
    all_js = strip_comments("".join(read(p) for p in bundle.glob("*.js")))

    extends_dt = bool(EXTENDS_DT_RE.search(js))
    renders_dt = False
    data_props: set[str] = set()

    for html_path in html_files:
        html = read(html_path)
        for tag, attrs in markup_elements(html):
            if not is_datatable(tag, attrs):
                continue
            renders_dt = True
            bound = {m.group(1).lower(): m.group(2) for m in ATTR_BIND_RE.finditer(attrs)}
            literal = {m.group(1).lower(): m.group(2) for m in ATTR_LITERAL_RE.finditer(attrs)}
            bare = {m.group(1).lower() for m in ATTR_BARE_RE.finditer(attrs)}
            present = set(bound) | set(literal) | bare

            if "key-field" not in present:
                issues.append(
                    {
                        "code": "DT001",
                        "file": str(html_path),
                        "message": (
                            f"<{tag}> has no `key-field`. It is a required attribute and is "
                            "what associates a row with a record (data-table-inline-edit L5675)."
                        ),
                    }
                )
            if "data" in bound:
                data_props.add(bound["data"].split(".")[0])

            if "draft-values" in present and "onsave" not in present:
                issues.append(
                    {
                        "code": "DT002",
                        "file": str(html_path),
                        "message": (
                            f"<{tag}> binds `draft-values` with no `onsave` handler; edits can "
                            "never be persisted (data-table-inline-edit L5676)."
                        ),
                    }
                )
            elif "onsave" in bound:
                handler = bound["onsave"]
                defined = {m.group(1) for m in METHOD_DEF_RE.finditer(all_js)}
                if handler not in defined and f"{handler} =" not in all_js:
                    issues.append(
                        {
                            "code": "DT002",
                            "file": str(html_path),
                            "message": (
                                f"<{tag}> binds onsave={{{handler}}} but no `{handler}` is "
                                f"defined in the {name} bundle."
                            ),
                        }
                    )

            if "enable-infinite-loading" in present and "onloadmore" not in present:
                issues.append(
                    {
                        "code": "DT003",
                        "file": str(html_path),
                        "message": (
                            f"<{tag}> sets `enable-infinite-loading` with no `onloadmore` "
                            "handler; the table will ask for rows nobody supplies "
                            "(data-table-performance L6313)."
                        ),
                    }
                )

    # --- DT006: custom-type subclass hygiene ---------------------------------
    if extends_dt:
        if not STATIC_CUSTOM_TYPES_RE.search(js):
            issues.append(
                {
                    "code": "DT006",
                    "file": str(js_main),
                    "message": (
                        "class extends LightningDatatable but declares no `static customTypes`. "
                        "Extending LightningDatatable is supported only to register custom data "
                        "types (data-table-custom-types L5795)."
                    ),
                }
            )
        else:
            block_start = STATIC_CUSTOM_TYPES_RE.search(js).end()
            block = js[block_start : block_start + 4000]
            for entry in CUSTOM_TYPE_ENTRY_RE.finditer(block):
                body = entry.group(2)
                if "template" not in body:
                    continue
                if "editTemplate" in body and "standardCellLayout" not in body:
                    issues.append(
                        {
                            "code": "DT006",
                            "file": str(js_main),
                            "message": (
                                f"custom type `{entry.group(1)}` is editable but does not set "
                                "`standardCellLayout: true`. The default bare layout drops "
                                "keyboard navigation and accessibility for editable types "
                                "(data-table-custom-types-styling L6092-L6097)."
                            ),
                        }
                    )
        if CONNECTED_CB_RE.search(js) and not SUPER_CONNECTED_RE.search(js):
            issues.append(
                {
                    "code": "DT006",
                    "file": str(js_main),
                    "message": (
                        "connectedCallback() override with no `super.connectedCallback()`. It "
                        "overrides the datatable's own initialization "
                        "(data-table-custom-types L5857-L5859)."
                    ),
                }
            )

    if not (renders_dt or extends_dt):
        return issues

    # --- DT005: in-place mutation of the wired array -------------------------
    for prop in sorted(data_props):
        for mutator in MUTATORS:
            if re.search(rf"\bthis\.{re.escape(prop)}\s*\.\s*{mutator}\s*\(", js):
                issues.append(
                    {
                        "code": "DT005",
                        "file": str(js_main),
                        "message": (
                            f"`this.{prop}.{mutator}(...)` mutates the array bound to the "
                            "datatable's `data` in place. LWC compares with `===`, so the table "
                            "will not rerender; assign a new array instead "
                            "(reactivity-fields L2287-L2288)."
                        ),
                    }
                )
        if re.search(rf"\bthis\.{re.escape(prop)}\s*=\s*this\.{re.escape(prop)}\s*\.\s*sort\s*\(", js):
            issues.append(
                {
                    "code": "DT005",
                    "file": str(js_main),
                    "message": (
                        f"`this.{prop} = this.{prop}.sort(...)` assigns the same reference back; "
                        "Array.prototype.sort is in place. Spread first: "
                        f"`this.{prop} = [...this.{prop}].sort(...)`."
                    ),
                }
            )
        if re.search(rf"\bthis\.{re.escape(prop)}\s*\[[^\]]+\]\s*(?:\.[\w$]+\s*)?=[^=]", js):
            issues.append(
                {
                    "code": "DT005",
                    "file": str(js_main),
                    "message": (
                        f"indexed assignment into `this.{prop}` is an in-place mutation; rebuild "
                        "the row with `map` and a spread instead "
                        "(reactivity-fields L2287-L2288)."
                    ),
                }
            )

    # --- DT004: fieldName vs the knowable row shape --------------------------
    field_names = {m.group(1) for m in FIELDNAME_RE.finditer(js)}
    if field_names:
        apex_fields: set[str] = set()
        resolved_any = False
        for imp in APEX_IMPORT_RE.finditer(js):
            cls_name, method = imp.group(3), imp.group(4)
            found = apex_select_fields(root, cls_name, method)
            if found is not None:
                resolved_any = True
                apex_fields |= found
        if resolved_any and apex_fields:
            known = {f.lower() for f in apex_fields}
            known |= {k.lower() for k in derived_keys(js)}
            for field in sorted(field_names):
                if field.lower() not in known and field.split(".")[0].lower() not in known:
                    issues.append(
                        {
                            "code": "DT004",
                            "file": str(js_main),
                            "message": (
                                f"column fieldName '{field}' matches neither a field in the "
                                "wired Apex SELECT list nor a key the shaping layer adds. "
                                "fieldName names a key on the provisioned row, not a field "
                                "label (data-table-custom-types L5812)."
                            ),
                        }
                    )

    # --- DT007: tests --------------------------------------------------------
    tests_dir = bundle / "__tests__"
    if not tests_dir.is_dir():
        issues.append(
            {
                "code": "DT007",
                "file": str(bundle),
                "message": (
                    "datatable bundle has no `__tests__` folder. Jest tests live at the top "
                    "level of the component bundle "
                    "(unit-testing-using-jest-create-tests L12328)."
                ),
            }
        )
    else:
        test_text = "".join(read(p) for p in tests_dir.rglob("*.js"))
        if "describe(" not in test_text:
            issues.append(
                {
                    "code": "DT007",
                    "file": str(tests_dir),
                    "message": "`__tests__` folder contains no `describe(` block.",
                }
            )

    # --- DT008: bundle configuration file ------------------------------------
    meta = bundle / f"{name}.js-meta.xml"
    if not meta.is_file():
        issues.append(
            {
                "code": "DT008",
                "file": str(bundle),
                "message": f"missing {name}.js-meta.xml; the bundle cannot deploy.",
            }
        )
    else:
        try:
            root_el = ET.parse(meta).getroot()
        except ET.ParseError as exc:
            issues.append(
                {"code": "DT008", "file": str(meta), "message": f"is not well-formed XML: {exc}"}
            )
        else:
            # A leaf Element is falsy, so test identity explicitly.
            api = root_el.find(f"{MD_NS}apiVersion")
            if api is None:
                api = root_el.find("apiVersion")
            if api is None or not (api.text or "").strip():
                issues.append(
                    {"code": "DT008", "file": str(meta), "message": "has no <apiVersion>."}
                )

    return issues


def main() -> int:
    args = parse_args()
    root = Path(args.manifest_dir)
    if not root.exists():
        print(f"ISSUE: manifest directory not found: {root}", file=sys.stderr)
        return 2

    issues: list[dict] = []
    for bundle in find_bundles(root):
        issues.extend(check_bundle(bundle, root))

    if args.json:
        print(json.dumps(issues, indent=2))
        return 1 if issues else 0

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE [{issue['code']}] {issue['file']}: {issue['message']}")
    print(f"\n{len(issues)} issue(s).")
    return 1


if __name__ == "__main__":
    sys.exit(main())
