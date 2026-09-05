#!/usr/bin/env python3
"""Check LWC form bundles for validation and save-lifecycle defects.

Static, stdlib-only, no org connection. Point --manifest-dir at an LWC source
tree (for example force-app/main/default/lwc) or at any ancestor of one; the
script discovers bundles by looking for a directory that contains <name>.js and
<name>.html.

Checks implemented (each maps to a gotcha or anti-pattern in this skill):

  C1  lightning-record-edit-form without lightning-messages
      (references/gotchas.md -> "Validation-Rule Errors Already Carry Structured Detail";
       data-edit-record:5489)
  C2  lightning-record-edit-form without an onerror handler
      (data-edit-record:5501-5504)
  C3  onsubmit handler that builds or mutates a field map but never calls
      event.preventDefault() -- the augmentation is discarded and the raw form
      value is what saves
  C4  setCustomValidity() with no reportValidity() in the same file
      (references/gotchas.md -> "setCustomValidity() Needs reportValidity()")
  C5  createRecord/updateRecord/deleteRecord with no catch() and no try/catch
      (data-error:6568-6569 -- the write-error body is where field errors live)
  C6  lightning-input marked required with no label attribute
  C7  bundle with a form but no __tests__ directory containing a describe()
      (unit-testing-using-jest-create-tests:12328-12331)
  C8  bundle missing its .js-meta.xml, or a meta file without apiVersion/isExposed
      (create-components-meta-file:716-720)
  C9  document.querySelector / getElementById used instead of this.template
      inside a component

Exit code 0 when clean, 1 when any issue is reported.
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

MD_NS = "{http://soap.sforce.com/2006/04/metadata}"

RECORD_EDIT_FORM_RE = re.compile(r"<lightning-record-edit-form\b", re.IGNORECASE)
RECORD_FORM_ANY_RE = re.compile(r"<lightning-record-(edit-|view-)?form\b", re.IGNORECASE)
LIGHTNING_MESSAGES_RE = re.compile(r"<lightning-messages\b", re.IGNORECASE)
LIGHTNING_INPUT_RE = re.compile(r"<lightning-input\b(?!-field)", re.IGNORECASE)
FILE_UPLOAD_RE = re.compile(r"<lightning-file-upload\b", re.IGNORECASE)
RECORD_ID_ATTR_RE = re.compile(r"\brecord-id\s*=", re.IGNORECASE)
ONERROR_ATTR_RE = re.compile(r"\bonerror\s*=\s*\{([A-Za-z0-9_$]+)\}", re.IGNORECASE)
ONSUBMIT_ATTR_RE = re.compile(r"\bonsubmit\s*=\s*\{([A-Za-z0-9_$]+)\}", re.IGNORECASE)

SET_CUSTOM_VALIDITY_RE = re.compile(r"\bsetCustomValidity\s*\(")
REPORT_VALIDITY_RE = re.compile(r"\breportValidity\s*\(")
PREVENT_DEFAULT_RE = re.compile(r"\bpreventDefault\s*\(\s*\)")
FIELD_MUTATION_RE = re.compile(
    r"(detail\.fields|const\s+fields\s*=|let\s+fields\s*=|fields\[)"
)
LDS_WRITE_RE = re.compile(r"\b(createRecord|updateRecord|deleteRecord)\s*\(")
CATCH_RE = re.compile(r"\.catch\s*\(|\bcatch\s*\(")
DESCRIBE_RE = re.compile(r"\bdescribe\s*\(")
DOC_QUERY_RE = re.compile(r"\bdocument\.(querySelector|querySelectorAll|getElementById)\b")

# <lightning-input ...> element text, so attributes can be inspected together.
LIGHTNING_INPUT_TAG_RE = re.compile(r"<lightning-input\b(?!-field)[^>]*>", re.IGNORECASE | re.DOTALL)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Lightning Web Component form bundles for validation and save-lifecycle defects.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root of the Salesforce source tree, or an lwc/ directory (default: current directory).",
    )
    parser.add_argument(
        "--fail-on-warn",
        action="store_true",
        help="Also exit non-zero when only WARN-level findings are present.",
    )
    return parser.parse_args()


def first_child(element, tag: str):
    """ElementTree-safe child lookup.

    A leaf Element is falsy, so `el.find(a) or el.find(b)` is a bug. Always
    compare against None.
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


def find_bundles(root: Path) -> list[Path]:
    """A bundle is a directory holding <dirname>.js and <dirname>.html."""
    bundles = []
    for js_path in root.rglob("*.js"):
        if "__tests__" in js_path.parts or "node_modules" in js_path.parts:
            continue
        bundle = js_path.parent
        if js_path.stem != bundle.name:
            continue
        if (bundle / f"{bundle.name}.html").exists():
            bundles.append(bundle)
    return sorted(set(bundles))


def check_bundle(bundle: Path) -> list[tuple[str, str]]:
    """Return (level, message) findings for one component bundle."""
    findings: list[tuple[str, str]] = []
    name = bundle.name
    html_path = bundle / f"{name}.html"
    js_path = bundle / f"{name}.js"
    meta_path = bundle / f"{name}.js-meta.xml"

    html = read(html_path)
    js = read(js_path)

    has_edit_form = bool(RECORD_EDIT_FORM_RE.search(html))
    has_any_form = bool(RECORD_FORM_ANY_RE.search(html)) or bool(LIGHTNING_INPUT_RE.search(html))
    writes_via_lds = bool(LDS_WRITE_RE.search(js))

    # C1 -- record-edit-form without lightning-messages
    if has_edit_form and not LIGHTNING_MESSAGES_RE.search(html):
        findings.append(
            (
                "ERROR",
                f"{html_path}: `lightning-record-edit-form` has no `lightning-messages`; "
                "platform save errors have nowhere to render (data-edit-record:5489).",
            )
        )

    # C2 -- record-edit-form without onerror
    if has_edit_form:
        onerror = ONERROR_ATTR_RE.search(html)
        if onerror is None:
            findings.append(
                (
                    "ERROR",
                    f"{html_path}: `lightning-record-edit-form` has no `onerror` handler; "
                    "validation-rule detail in `event.detail.output.fieldErrors` is dropped "
                    "(data-edit-record:5509).",
                )
            )
        elif f"{onerror.group(1)}(" not in js:
            findings.append(
                (
                    "ERROR",
                    f"{js_path}: `onerror={{{onerror.group(1)}}}` is bound in the template but "
                    f"`{onerror.group(1)}` is not defined in the JS.",
                )
            )

    # C3 -- onsubmit that touches the field map without preventDefault
    submit_match = ONSUBMIT_ATTR_RE.search(html)
    if submit_match:
        handler = submit_match.group(1)
        body = handler_body(js, handler)
        if body is None:
            findings.append(
                (
                    "ERROR",
                    f"{js_path}: `onsubmit={{{handler}}}` is bound in the template but "
                    f"`{handler}` is not defined in the JS.",
                )
            )
        elif FIELD_MUTATION_RE.search(body) and not PREVENT_DEFAULT_RE.search(body):
            findings.append(
                (
                    "ERROR",
                    f"{js_path}: `{handler}` builds or reads a field map but never calls "
                    "`event.preventDefault()`; the form submits the unmodified values and the "
                    "augmentation is discarded.",
                )
            )

    # C4 -- setCustomValidity without reportValidity
    if SET_CUSTOM_VALIDITY_RE.search(js) and not REPORT_VALIDITY_RE.search(js):
        findings.append(
            (
                "ERROR",
                f"{js_path}: calls `setCustomValidity()` with no `reportValidity()`; the message "
                "is stored and never rendered (reference-update-record:15403).",
            )
        )

    # C5 -- LDS write with no error path
    if writes_via_lds and not CATCH_RE.search(js):
        findings.append(
            (
                "ERROR",
                f"{js_path}: `createRecord`/`updateRecord`/`deleteRecord` is called with no "
                "`catch` or `try/catch`; the write-error body carrying field-level errors is lost "
                "(data-error:6568-6569).",
            )
        )

    # C6 -- required lightning-input with no label
    for tag in LIGHTNING_INPUT_TAG_RE.findall(html):
        flat = " ".join(tag.split())
        if re.search(r"\brequired\b", flat, re.IGNORECASE) and not re.search(
            r"\blabel\s*=", flat, re.IGNORECASE
        ):
            findings.append(
                (
                    "ERROR",
                    f"{html_path}: `lightning-input` is `required` but has no `label`; the "
                    "validation message has no accessible name to attach to. See "
                    "lwc/lwc-accessibility. Snippet: {}".format(flat[:110]),
                )
            )

    # C7 -- form bundle with no Jest test
    if has_any_form or writes_via_lds:
        tests_dir = bundle / "__tests__"
        test_files = sorted(tests_dir.glob("*.js")) if tests_dir.is_dir() else []
        if not test_files:
            findings.append(
                (
                    "ERROR",
                    f"{bundle}: form bundle has no `__tests__` directory with a test file "
                    "(unit-testing-using-jest-create-tests:12328-12331).",
                )
            )
        elif not any(DESCRIBE_RE.search(read(f)) for f in test_files):
            findings.append(
                ("ERROR", f"{tests_dir}: no `describe(` block found in any test file.")
            )

    # C8 -- configuration file
    if not meta_path.exists():
        findings.append(
            (
                "ERROR",
                f"{bundle}: missing `{name}.js-meta.xml`; every component must have a "
                "configuration file (create-components-meta-file:716).",
            )
        )
    else:
        try:
            root_el = ET.parse(meta_path).getroot()
        except ET.ParseError as exc:
            findings.append(("ERROR", f"{meta_path}: not well-formed XML ({exc})."))
        else:
            for tag in ("apiVersion", "isExposed"):
                if first_child(root_el, tag) is None:
                    findings.append(
                        ("ERROR", f"{meta_path}: missing `<{tag}>` (create-components-meta-file:718-720).")
                    )
            exposed = first_child(root_el, "isExposed")
            targets = first_child(root_el, "targets")
            if exposed is not None and (exposed.text or "").strip().lower() == "true" and targets is None:
                findings.append(
                    ("WARN", f"{meta_path}: `isExposed` is true but no `<targets>` are declared.")
                )

    # C9 -- DOM access outside the template
    if DOC_QUERY_RE.search(js):
        findings.append(
            (
                "ERROR",
                f"{js_path}: uses `document.querySelector`/`getElementById`; query the component's "
                "own shadow tree with `this.template.querySelector` instead.",
            )
        )

    # Retained from the original checker: upload without a record context.
    if FILE_UPLOAD_RE.search(html) and not RECORD_ID_ATTR_RE.search(html):
        findings.append(
            (
                "WARN",
                f"{html_path}: `lightning-file-upload` with no visible `record-id`; confirm the "
                "upload step runs after the record exists.",
            )
        )

    return findings


def handler_body(js: str, handler: str) -> str | None:
    """Best-effort extraction of a class method body by brace matching."""
    match = re.search(r"\b" + re.escape(handler) + r"\s*\([^)]*\)\s*\{", js)
    if match is None:
        return None
    depth = 0
    start = match.end() - 1
    for i in range(start, len(js)):
        if js[i] == "{":
            depth += 1
        elif js[i] == "}":
            depth -= 1
            if depth == 0:
                return js[start : i + 1]
    return js[start:]


def main() -> int:
    args = parse_args()
    root = Path(args.manifest_dir)

    if not root.exists():
        print(f"ISSUE: Manifest directory not found: {root}")
        return 1

    bundles = find_bundles(root)
    if not bundles:
        print(f"No Lightning Web Component bundles found under {root}.")
        return 0

    findings: list[tuple[str, str]] = []
    for bundle in bundles:
        findings.extend(check_bundle(bundle))

    errors = [f for f in findings if f[0] == "ERROR"]
    warns = [f for f in findings if f[0] == "WARN"]

    if not findings:
        print(f"No issues found across {len(bundles)} bundle(s).")
        return 0

    for level, message in findings:
        print(f"{level}: {message}")

    print(f"\n{len(errors)} error(s), {len(warns)} warning(s) across {len(bundles)} bundle(s).")

    if errors:
        return 1
    return 1 if args.fail_on_warn else 0


if __name__ == "__main__":
    sys.exit(main())
