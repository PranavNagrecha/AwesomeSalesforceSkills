#!/usr/bin/env python3
"""Check LWC bundles for navigation and routing anti-patterns.

Stdlib only. Walks a source tree (``--manifest-dir``), finds Lightning web
component bundles (a directory containing ``<name>.js`` and
``<name>.js-meta.xml``), and reports routing defects that the
lwc/navigation-and-routing skill documents.

Checks
    1.  Browser navigation APIs (``window.location.href = ...``, ``location.assign``,
        ``window.open``) used instead of the navigation service.
    2.  Hardcoded internal Salesforce URL segments (``/lightning/r/``, ``/lightning/o/``,
        ``/lightning/cmp/``, ``/s/``, ``/apex/``).
    3.  PageReference ``state`` keys that are not namespaced with ``<ns>__``.
    4.  ``NavigationMixin.Navigate`` / ``GenerateUrl`` used in a class that does not
        extend ``NavigationMixin(LightningElement)``.
    5.  ``GenerateUrl`` result consumed synchronously (no ``.then``/``await``).
    6.  ``standard__recordPage`` / ``standard__objectPage`` page references with no
        nearby ``actionName``.
    7.  ``standard__component`` navigation whose target bundle in this tree does not
        declare the ``lightning__UrlAddressable`` target.
    8.  Bundle completeness: ``.js`` + ``.html`` + ``.js-meta.xml``, a parseable
        ``-meta.xml`` with ``apiVersion`` / ``isExposed`` / ``targets``, and a
        ``__tests__`` folder holding at least one ``describe(``.

Usage
    python3 check_navigation_and_routing.py --manifest-dir force-app/main/default/lwc
    python3 check_navigation_and_routing.py --manifest-dir force-app --quiet
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

MDAPI_NS = "{http://soap.sforce.com/2006/04/metadata}"

BROWSER_NAV_RE = re.compile(
    r"\b(?:window\s*\.\s*)?location\s*\.\s*(?:href|assign|replace)\s*(?:=|\()"
    r"|\bwindow\s*\.\s*open\s*\("
)
HARDCODED_URL_RE = re.compile(r"""['"`]/(?:lightning/(?:r|o|n|cmp|page)|s|apex)/""")
PAGE_TYPE_RE = re.compile(r"""type\s*:\s*['"]([A-Za-z_]+__[A-Za-z]+)['"]""")
STATE_BLOCK_RE = re.compile(r"""state\s*:\s*\{(?P<body>[^{}]*)\}""", re.DOTALL)
STATE_KEY_RE = re.compile(r"""(?:^|[,{\s])(['"]?)([A-Za-z_][A-Za-z0-9_]*)\1\s*:""")
NAV_USE_RE = re.compile(r"NavigationMixin\s*\.\s*(Navigate|GenerateUrl)\b")
NAV_MIXIN_EXTENDS_RE = re.compile(r"extends\s+NavigationMixin\s*\(")
GENERATE_URL_CALL_RE = re.compile(
    r"""(?P<assign>(?:const|let|var)\s+\w+\s*=\s*|return\s+|await\s+)?"""
    r"""this\s*\[\s*NavigationMixin\.GenerateUrl\s*\]\s*\("""
)
COMPONENT_NAME_RE = re.compile(r"""componentName\s*:\s*['"]([A-Za-z0-9_]+)['"]""")
DESCRIBE_RE = re.compile(r"\bdescribe\s*\(")

# State keys the PageReference Types reference documents as platform-owned, so an
# un-namespaced occurrence of one of these is legal.
# Grounded: reference-page-reference-type — defaultFieldValues (L22178, L22187),
# filterName (L22177), nooverride (L22179, L22198); use-navigate-url-addressable
# uid (L10249). The remainder are widely used platform keys retained to avoid
# false positives.
# UNVERIFIED (2026-09-05): navigationLocation, backgroundContext, count,
# recordTypeId and useRecordTypeCheck are not stated in the LWC Developer Guide
# extraction used to build this checker; they are allowlisted only so the check
# does not produce false positives on them.
STANDARD_STATE_KEYS = {
    "defaultFieldValues",
    "filterName",
    "nooverride",
    "uid",
    "recordId",
    "recordID",
    "navigationLocation",
    "backgroundContext",
    "count",
    "recordTypeId",
    "useRecordTypeCheck",
    "retURL",
}

RECORD_LIKE_TYPES = {"standard__recordPage", "standard__objectPage"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Lightning web component bundles for routing and navigation issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce source tree (default: current directory).",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Print only the issue count, not each issue.",
    )
    return parser.parse_args()


def line_number(text: str, index: int) -> int:
    return text.count("\n", 0, index) + 1


def child_text(parent: ET.Element | None, tag: str) -> str | None:
    """Return the text of a direct child, namespaced or not.

    A leaf Element is falsy, so every lookup is compared against None explicitly
    rather than chained with ``or``.
    """
    if parent is None:
        return None
    node = parent.find(f"{MDAPI_NS}{tag}")
    if node is None:
        node = parent.find(tag)
    if node is None:
        return None
    return (node.text or "").strip()


def find_bundles(root: Path) -> list[Path]:
    """A bundle is a directory holding <dirname>.js and <dirname>.js-meta.xml."""
    bundles = []
    for meta in sorted(root.rglob("*.js-meta.xml")):
        bundle = meta.parent
        if meta.name == f"{bundle.name}.js-meta.xml":
            bundles.append(bundle)
    return bundles


def url_addressable_bundles(bundles: list[Path]) -> set[str]:
    """Bundle names in this tree that declare lightning__UrlAddressable."""
    exposed = set()
    for bundle in bundles:
        meta = bundle / f"{bundle.name}.js-meta.xml"
        try:
            tree = ET.parse(meta)
        except (ET.ParseError, OSError):
            continue
        for target in tree.getroot().iter():
            tag = target.tag.split("}")[-1]
            if tag == "target" and (target.text or "").strip() == "lightning__UrlAddressable":
                exposed.add(bundle.name)
    return exposed


def check_meta(bundle: Path, issues: list[str]) -> None:
    meta = bundle / f"{bundle.name}.js-meta.xml"
    try:
        root = ET.parse(meta).getroot()
    except ET.ParseError as exc:
        issues.append(f"{meta}: -meta.xml does not parse ({exc}).")
        return
    except OSError as exc:
        issues.append(f"{meta}: -meta.xml unreadable ({exc}).")
        return

    if child_text(root, "apiVersion") is None:
        issues.append(f"{meta}: no <apiVersion>; the deploy inherits an unpredictable version.")
    is_exposed = child_text(root, "isExposed")
    if is_exposed is None:
        issues.append(f"{meta}: no <isExposed>; a navigable component must set it to true.")
    targets = root.find(f"{MDAPI_NS}targets")
    if targets is None:
        targets = root.find("targets")
    if targets is None:
        if is_exposed == "true":
            issues.append(
                f"{meta}: <isExposed>true</isExposed> with no <targets>; the component "
                "is exposed but cannot be placed or navigated to."
            )
    elif len(list(targets)) == 0:
        issues.append(f"{meta}: <targets> is empty.")


def check_bundle_shape(bundle: Path, issues: list[str]) -> None:
    if not (bundle / f"{bundle.name}.html").exists():
        issues.append(
            f"{bundle}: bundle has no {bundle.name}.html; only a headless quick action "
            "or url-addressable wrapper legitimately omits the template."
        )
    tests_dir = bundle / "__tests__"
    if not tests_dir.is_dir():
        issues.append(
            f"{bundle}: no __tests__ folder; navigation cannot be regression-tested "
            "without the lightning/navigation Jest mock."
        )
        return
    test_files = list(tests_dir.glob("*.js")) + list(tests_dir.glob("*.ts"))
    if not test_files:
        issues.append(f"{bundle}/__tests__: no test files.")
        return
    if not any(DESCRIBE_RE.search(p.read_text(encoding="utf-8", errors="ignore")) for p in test_files):
        issues.append(f"{bundle}/__tests__: no describe( block found in any test file.")


def enclosing_object_literal(text: str, index: int) -> str:
    """Return the source of the object literal that contains position ``index``.

    Walks back to the nearest unmatched ``{`` and forward to its partner so a
    ``type:`` key is only judged against attributes in its own PageReference,
    not against whatever happens to sit a few hundred characters later.
    """
    depth = 0
    start = -1
    for i in range(index, -1, -1):
        ch = text[i]
        if ch == "}":
            depth += 1
        elif ch == "{":
            if depth == 0:
                start = i
                break
            depth -= 1
    if start == -1:
        return text[index: index + 320]
    depth = 0
    for j in range(start, len(text)):
        ch = text[j]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start: j + 1]
    return text[start:]


def check_js(path: Path, addressable: set[str], issues: list[str]) -> None:
    text = path.read_text(encoding="utf-8", errors="ignore")

    for match in BROWSER_NAV_RE.finditer(text):
        issues.append(
            f"{path}:{line_number(text, match.start())}: browser navigation API "
            f"`{match.group(0).strip()}` — use a PageReference with NavigationMixin instead."
        )

    for match in HARDCODED_URL_RE.finditer(text):
        issues.append(
            f"{path}:{line_number(text, match.start())}: hardcoded internal Salesforce URL "
            "segment; PageReference navigation insulates the component from URL-format changes."
        )

    uses_nav = NAV_USE_RE.search(text)
    if uses_nav and not NAV_MIXIN_EXTENDS_RE.search(text):
        issues.append(
            f"{path}:{line_number(text, uses_nav.start())}: NavigationMixin.{uses_nav.group(1)} "
            "is used but the class does not `extends NavigationMixin(LightningElement)`; "
            "importing the mixin does not add the APIs to the class."
        )

    for match in GENERATE_URL_CALL_RE.finditer(text):
        tail = text[match.end(): match.end() + 400]
        assigned = (match.group("assign") or "").strip()
        if assigned.startswith("await") or "await" in (match.group("assign") or ""):
            continue
        if ".then" in tail or ".catch" in tail:
            continue
        issues.append(
            f"{path}:{line_number(text, match.start())}: GenerateUrl result is used without "
            "`.then(...)` or `await`; GenerateUrl returns a promise that resolves to the URL."
        )

    for match in STATE_BLOCK_RE.finditer(text):
        body = match.group("body")
        for key_match in STATE_KEY_RE.finditer(body):
            key = key_match.group(2)
            if "__" in key or key in STANDARD_STATE_KEYS:
                continue
            issues.append(
                f"{path}:{line_number(text, match.start() + key_match.start(2))}: PageReference "
                f"state key `{key}` has no namespace prefix; custom state keys must be "
                "`<namespace>__key` (use `c__` outside a managed package)."
            )

    for match in PAGE_TYPE_RE.finditer(text):
        page_type = match.group(1)
        window = enclosing_object_literal(text, match.start())
        if page_type in RECORD_LIKE_TYPES and "actionName" not in window:
            issues.append(
                f"{path}:{line_number(text, match.start())}: `{page_type}` with no nearby "
                "`actionName`; actionName is a required attribute for this page type."
            )
        if page_type == "standard__component" and addressable:
            name_match = COMPONENT_NAME_RE.search(window)
            if name_match:
                raw = name_match.group(1)
                bundle_name = raw.split("__")[-1]
                candidates = {bundle_name, bundle_name[:1].lower() + bundle_name[1:]}
                if not candidates & addressable:
                    issues.append(
                        f"{path}:{line_number(text, match.start())}: standard__component targets "
                        f"`{raw}`, but no bundle in this tree declares the "
                        "lightning__UrlAddressable target for it."
                    )


def check_navigation_and_routing(manifest_dir: Path) -> list[str]:
    issues: list[str] = []

    if not manifest_dir.exists():
        return [f"Manifest directory not found: {manifest_dir}"]

    bundles = find_bundles(manifest_dir)
    addressable = url_addressable_bundles(bundles)

    for bundle in bundles:
        check_meta(bundle, issues)
        check_bundle_shape(bundle, issues)

    scanned = {p for b in bundles for p in b.rglob("*.js")}
    scanned |= {p for b in bundles for p in b.rglob("*.ts")}
    if not bundles:
        scanned = set(manifest_dir.rglob("*.js")) | set(manifest_dir.rglob("*.ts"))

    for path in sorted(scanned):
        check_js(path, addressable, issues)

    return issues


def main() -> int:
    args = parse_args()
    issues = check_navigation_and_routing(Path(args.manifest_dir))

    if not issues:
        print("No issues found.")
        return 0

    if not args.quiet:
        for issue in issues:
            print(f"ISSUE: {issue}")
    print(f"{len(issues)} issue(s) found.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
