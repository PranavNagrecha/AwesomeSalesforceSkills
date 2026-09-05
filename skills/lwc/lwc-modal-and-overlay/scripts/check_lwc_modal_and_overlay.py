#!/usr/bin/env python3
"""Check LWC overlay bundles for the modal anti-patterns this skill documents.

Stdlib only. Walks a Salesforce source tree, finds Lightning web component
bundles, and reports the specific failures grounded in
references/gotchas.md:

  1. Hand-rolled `slds-modal` markup in a bundle that never extends
     LightningModal (use-dialog-modal, L10374-L10375).
  2. A LightningModal subclass whose template has no `lightning-modal-body`,
     which the guide marks required (use-dialog-modal, L10376).
  3. A `.open(` call whose promise is not awaited, assigned, returned, or
     `.then`-ed - the resolved close() value is discarded
     (use-dialog-modal, L10379, L10387).
  4. A LightningModal subclass with no `close(` call on any path, so the
     caller's await never settles.
  5. An `@api` property on a modal that no launcher's `open({...})` config
     mentions - modal inputs come from open(), never from markup
     (use-dialog-modal, L10387).
  6. `NavigationMixin` applied to a LightningModal subclass, which is not
     supported (use-navigate-modal, L10258-L10259).
  7. A modal bundle no test exercises - neither its own __tests__ folder
     nor any test in the tree importing c/<bundleName>.
  8. window.alert / confirm / prompt instead of lightning/alert, /confirm,
     /prompt (base-components-patterns, L4767-L4769).

Usage:
    python3 check_lwc_modal_and_overlay.py --manifest-dir force-app/main/default/lwc
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

EXTENDS_MODAL_RE = re.compile(r"class\s+\w+\s+extends\s+(?:\w+\s*\(\s*)?LightningModal")
NAV_MIXIN_MODAL_RE = re.compile(r"extends\s+NavigationMixin\s*\(\s*LightningModal\s*\)")
NAMED_MODAL_IMPORT_RE = re.compile(r"import\s*\{[^}]*\bLightningModal\b[^}]*\}\s*from\s*['\"]lightning/modal['\"]")
CLOSE_CALL_RE = re.compile(r"\bthis\.close\s*\(")
WINDOW_DIALOG_RE = re.compile(r"\bwindow\.(?:alert|confirm|prompt)\s*\(")
SLDS_MODAL_RE = re.compile(r"slds-modal")
MODAL_BODY_RE = re.compile(r"<\s*lightning-modal-body\b")
API_PROP_RE = re.compile(r"@api\s+(?:get\s+|set\s+)?([A-Za-z_$][\w$]*)")
OPEN_CALL_RE = re.compile(r"\b([A-Za-z_$][\w$]*)\s*\.\s*open\s*\(")
DESCRIBE_RE = re.compile(r"\bdescribe\s*\(")
IDENT_KEY_RE = re.compile(r"([A-Za-z_$][\w$]*)\s*:")

# Modules whose .open() is a notification helper, not a custom modal class.
NOTIFICATION_CLASSES = {"LightningAlert", "LightningConfirm", "LightningPrompt"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check LWC overlay bundles for common modal and dialog issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root of the Salesforce source tree or lwc folder (default: current directory).",
    )
    return parser.parse_args()


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def strip_comments(text: str) -> str:
    """Remove // and /* */ comments so they cannot satisfy or trip a check."""
    text = re.sub(r"/\*.*?\*/", " ", text, flags=re.S)
    return re.sub(r"(?m)//.*$", "", text)


def find_bundles(root: Path) -> list[Path]:
    """A bundle is any directory holding <dirname>.js."""
    bundles: set[Path] = set()
    for js in root.rglob("*.js"):
        if "__tests__" in js.parts or "node_modules" in js.parts:
            continue
        if js.stem == js.parent.name:
            bundles.add(js.parent)
    return sorted(bundles)


def object_literal_keys(text: str, open_paren_index: int) -> list[str] | None:
    """Return the top-level keys of an object literal passed as the first argument.

    Returns None when the first argument is not an inline object literal
    (a spread variable, for instance), so the caller can skip the check
    instead of reporting a false positive.
    """
    i = open_paren_index
    n = len(text)
    while i < n and text[i] not in "{)":
        if not text[i].isspace():
            return None
        i += 1
    if i >= n or text[i] != "{":
        return None

    depth = 0
    start = i
    while i < n:
        ch = text[i]
        if ch in "{[(":
            depth += 1
        elif ch in "}])":
            depth -= 1
            if depth == 0:
                break
        i += 1
    if depth != 0:
        return None

    body = text[start + 1 : i]
    # Blank out nested structures and strings so only top-level keys survive.
    flat = []
    depth = 0
    quote = None
    for ch in body:
        if quote:
            flat.append(" ")
            if ch == quote:
                quote = None
            continue
        if ch in "\"'`":
            quote = ch
            flat.append(" ")
            continue
        if ch in "{[(":
            depth += 1
        elif ch in "}])":
            depth -= 1
        flat.append(ch if depth == 0 else " ")
    return IDENT_KEY_RE.findall("".join(flat))


def open_call_is_consumed(text: str, match: re.Match) -> bool:
    """True when the promise from `.open(` is awaited, assigned, returned or chained."""
    tail = text[max(0, match.start() - 60) : match.start()].rstrip()
    if tail.endswith(("await", "return", "=", "(", ",", "&&", "||", "??", ":", "[")):
        return True
    if re.search(r"\b(?:await|return)\s*$", tail):
        return True
    # Walk to the matching close paren and look for a .then / .catch / .finally chain.
    i = match.end() - 1
    depth = 0
    n = len(text)
    while i < n:
        if text[i] in "([{":
            depth += 1
        elif text[i] in ")]}":
            depth -= 1
            if depth == 0:
                break
        i += 1
    after = text[i + 1 : i + 40]
    return bool(re.match(r"\s*\.\s*(?:then|catch|finally)\b", after))


def check_bundle(bundle: Path, all_js_text: str, tested: bool) -> list[str]:
    issues: list[str] = []
    name = bundle.name
    js_path = bundle / f"{name}.js"
    html_path = bundle / f"{name}.html"
    raw_js = _read(js_path)
    js = strip_comments(raw_js)
    html = _read(html_path)

    is_modal = bool(EXTENDS_MODAL_RE.search(js))

    if NAMED_MODAL_IMPORT_RE.search(js):
        issues.append(
            f"{js_path}: LightningModal imported with braces; it is a default export "
            f"(`import LightningModal from 'lightning/modal'`) and the named form yields undefined."
        )

    if NAV_MIXIN_MODAL_RE.search(js):
        issues.append(
            f"{js_path}: NavigationMixin applied to a LightningModal subclass; the mixin supports "
            f"only components extending LightningElement. Return the PageReference through close() "
            f"and navigate from the launcher."
        )

    if WINDOW_DIALOG_RE.search(js):
        issues.append(
            f"{js_path}: browser alert/confirm/prompt detected; use lightning/alert, "
            f"lightning/confirm, or lightning/prompt, which return a promise instead of halting."
        )

    if is_modal:
        if not CLOSE_CALL_RE.search(js):
            issues.append(
                f"{js_path}: component extends LightningModal but never calls this.close(); "
                f"the caller's await on open() can never settle."
            )
        if html_path.exists() and not MODAL_BODY_RE.search(html):
            issues.append(
                f"{html_path}: LightningModal subclass template has no <lightning-modal-body>, "
                f"which the LWC guide marks as required."
            )
        if not tested:
            issues.append(
                f"{bundle}: no __tests__ file exercises this modal - neither the bundle's own "
                f"__tests__ folder nor any test importing c/{name} contains a describe() block; "
                f"the open()/close() result contract is untested."
            )
        for prop in sorted(set(API_PROP_RE.findall(js))):
            if not re.search(rf"\b{re.escape(prop)}\s*:", all_js_text):
                issues.append(
                    f"{js_path}: @api {prop} on a modal is never named in any open({{...}}) config; "
                    f"modal inputs are set by open(), not by parent markup, so this arrives undefined."
                )
    else:
        if SLDS_MODAL_RE.search(html):
            issues.append(
                f"{html_path}: hand-rolled slds-modal markup in a bundle that does not extend "
                f"LightningModal; LightningModal already implements the SLDS modals blueprint and "
                f"supplies the open/close mechanisms."
            )

    for m in OPEN_CALL_RE.finditer(js):
        caller = m.group(1)
        if caller in {"this", "window", "document", "jest"}:
            continue
        if not open_call_is_consumed(js, m):
            issues.append(
                f"{js_path}: {caller}.open(...) result is not awaited, assigned, returned, or "
                f".then()-ed; the value passed to close() is discarded."
            )

    return issues


def check_lwc_modal_and_overlay(manifest_dir: Path) -> list[str]:
    if not manifest_dir.exists():
        return [f"Manifest directory not found: {manifest_dir}"]

    bundles = find_bundles(manifest_dir)
    if not bundles:
        return [f"No Lightning web component bundles found under {manifest_dir}"]

    # Every open() config key seen anywhere in the tree, used to decide whether a
    # modal's @api input is actually supplied by some launcher.
    keys: set[str] = set()
    all_js: list[str] = []
    for js in manifest_dir.rglob("*.js"):
        if "node_modules" in js.parts:
            continue
        text = strip_comments(_read(js))
        all_js.append(text)
        for m in OPEN_CALL_RE.finditer(text):
            found = object_literal_keys(text, m.end())
            if found:
                keys.update(found)
    joined = "\n".join(all_js)

    # A modal counts as tested when its own __tests__ folder has a describe(),
    # or when any test in the tree that has a describe() imports c/<bundleName>.
    # The result-contract test usually lives with the launcher, not the modal.
    tested_bundles: set[Path] = set()
    test_texts: list[str] = []
    for test_js in manifest_dir.rglob("__tests__/*.js"):
        if "node_modules" in test_js.parts:
            continue
        text = _read(test_js)
        if not DESCRIBE_RE.search(text):
            continue
        test_texts.append(text)
        owner = test_js.parent.parent
        if (owner / f"{owner.name}.js").exists():
            tested_bundles.add(owner)
    for bundle in bundles:
        ref = re.compile(rf"['\"]c/{re.escape(bundle.name)}['\"]")
        if any(ref.search(text) for text in test_texts):
            tested_bundles.add(bundle)

    issues: list[str] = []
    for bundle in bundles:
        issues.extend(check_bundle(bundle, joined, bundle in tested_bundles))
    return issues


def main() -> int:
    args = parse_args()
    issues = check_lwc_modal_and_overlay(Path(args.manifest_dir))

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
