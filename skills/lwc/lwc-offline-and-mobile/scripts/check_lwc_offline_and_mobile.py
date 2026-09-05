#!/usr/bin/env python3
"""Static checks for LWC bundles that target the Salesforce mobile app or Mobile Offline.

Stdlib only. Point --manifest-dir at a source tree (for example
force-app/main/default) and the script walks every `lwc/<bundle>/` folder it finds.

Rules, each grounded in the Lightning Web Components Developer Guide
(https://developer.salesforce.com/docs/platform/lwc/guide/<page>.html):

  MC1  mobileCapabilities API called with no isAvailable() guard anywhere in the file.
       Mobile capability APIs exist only inside a supported mobile app on a mobile
       device (reference-lightning-mobilecapabilities).
  MC2  scan()/beginCapture() with no dismiss()/endCapture() teardown. The OS scanner
       interface stays on screen until it is dismissed
       (reference-lightning-barcodescanner-scan).
  MC3  Legacy scanning API (beginCapture/resumeCapture/endCapture) — retiring in a
       future release (reference-lightning-barcodescanner-begincapture).
  MC4  mobileCapabilities call chain with no .catch() — isAvailable() is not a
       substitute for error handling (reference-lightning-barcodescanner-isavailable).
  OF1  Apex (@wire or imperative) used as a data path in a bundle that declares itself
       mobile-offline. Apex shares no data cache with LDS, so the two disagree online
       and offline (data-guidelines).
  OF2  lightning/graphql (v2) imported in a bundle that declares itself mobile-offline.
       Only lightning/uiGraphQLApi (v1) supports Mobile Offline (reference-graphql-intro).
  OF3  Browser storage (localStorage/sessionStorage) used as an offline data store.
  DM1  document.querySelector / document.getElementById — code cannot use document to
       reach a component's shadow tree (create-components-javascript-share-shadow-dom).
  DM2  Viewport size inferred from window.innerWidth / screen.width / navigator.userAgent
       instead of @salesforce/client/formFactor (create-client-form-factor).
  MX1  -meta.xml missing, unparseable, or missing apiVersion / isExposed / targets.
  MX2  isExposed is false while targets are declared — the component cannot be placed.
  MX3  Component reads recordId but the -meta.xml declares no lightning__RecordPage
       target, so recordId is never populated.
  MX4  supportedFormFactor type outside {Large, Small} — the config file accepts no
       other values, notably not Medium (targets-lightning-record-action).
  MX5  Bundle allows the Small form factor and uses lightning-datatable or
       lightning-tree-grid, which aren't supported on mobile (data-table-vs-tree-grid).
  TS1  No __tests__ folder, or no `describe(` in it.

Exit codes: 0 clean, 1 issues found or --manifest-dir missing.
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

MD_NS = "{http://soap.sforce.com/2006/04/metadata}"

CAPABILITY_CALLS = (
    "scan(",
    "beginCapture(",
    "resumeCapture(",
    "endCapture(",
    "getCurrentPosition(",
    "startWatchingPosition(",
    "requestAppReview(",
    "getContacts(",
    "getCalendars(",
    "startCapture(",
)
LEGACY_SCAN_CALLS = ("beginCapture(", "resumeCapture(", "endCapture(")
OFFLINE_MARKERS = ("mobile offline", "mobile-offline", "offline-capable", "works offline", "briefcase")
MOBILE_UNSUPPORTED_TAGS = ("lightning-datatable", "lightning-tree-grid")
VALID_FORM_FACTORS = {"Large", "Small"}


def child(elem, tag):
    """Return the first child with this tag, or None. Never use `or` on an Element:
    a leaf Element is falsy, so `a.find(x) or a.find(y)` silently skips real nodes."""
    found = elem.find(f"{MD_NS}{tag}")
    if found is None:
        found = elem.find(tag)
    return found


def findall(elem, tag):
    out = elem.findall(f".//{MD_NS}{tag}")
    if not out:
        out = elem.findall(f".//{tag}")
    return out


def strip_comments(js: str) -> str:
    js = re.sub(r"/\*.*?\*/", "", js, flags=re.S)
    return re.sub(r"(?m)^\s*//.*$", "", js)


def find_bundles(root: Path) -> list[Path]:
    bundles: list[Path] = []
    for meta in root.rglob("*.js-meta.xml"):
        if meta.parent.parent.name == "lwc":
            bundles.append(meta.parent)
    if bundles:
        return sorted(set(bundles))
    # Fall back to any folder holding a same-named .js + .html pair.
    for js in root.rglob("*.js"):
        if js.stem == js.parent.name and (js.parent / f"{js.stem}.html").exists():
            bundles.append(js.parent)
    return sorted(set(bundles))


def check_bundle(bundle: Path) -> list[str]:
    issues: list[str] = []
    name = bundle.name
    js_files = [p for p in bundle.glob("*.js") if "__tests__" not in p.parts]
    html_files = list(bundle.glob("*.html"))
    meta_path = bundle / f"{name}.js-meta.xml"

    js_all = "\n".join(strip_comments(p.read_text(encoding="utf-8", errors="ignore")) for p in js_files)
    js_raw = "\n".join(p.read_text(encoding="utf-8", errors="ignore") for p in js_files)
    html_all = "\n".join(p.read_text(encoding="utf-8", errors="ignore") for p in html_files)

    # ---------------- -meta.xml ----------------
    targets: list[str] = []
    form_factors: list[str] = []
    is_exposed = None
    if not meta_path.exists():
        issues.append(f"MX1 {name}: no {name}.js-meta.xml — every component must have a configuration file.")
    else:
        try:
            root_el = ET.parse(meta_path).getroot()
        except ET.ParseError as exc:
            issues.append(f"MX1 {name}: {meta_path.name} does not parse ({exc}).")
            root_el = None
        if root_el is not None:
            for tag in ("apiVersion", "isExposed"):
                if child(root_el, tag) is None:
                    issues.append(f"MX1 {name}: {meta_path.name} has no <{tag}>.")
            exposed_el = child(root_el, "isExposed")
            if exposed_el is not None and exposed_el.text is not None:
                is_exposed = exposed_el.text.strip().lower() == "true"
            targets = [t.text.strip() for t in findall(root_el, "target") if t.text]
            form_factors = [
                ff.attrib.get("type", "").strip()
                for ff in findall(root_el, "supportedFormFactor")
            ]
            if is_exposed is False and targets:
                issues.append(
                    f"MX2 {name}: isExposed is false but {len(targets)} target(s) are declared — "
                    "the component cannot be placed on any page."
                )
            bad = [f for f in form_factors if f not in VALID_FORM_FACTORS]
            if bad:
                issues.append(
                    f"MX4 {name}: supportedFormFactor type(s) {sorted(set(bad))} are invalid; "
                    "only Large and Small are accepted (there is no Medium in the config file)."
                )

    uses_record_id = bool(re.search(r"@api\s+recordId\b", js_all)) or "recordId" in html_all
    if uses_record_id and meta_path.exists() and "lightning__RecordPage" not in targets:
        issues.append(
            f"MX3 {name}: the component uses recordId but the -meta.xml declares no "
            "lightning__RecordPage target, so recordId is never populated."
        )

    allows_small = ("Small" in form_factors) or (bool(targets) and not form_factors)
    if allows_small:
        for tag in MOBILE_UNSUPPORTED_TAGS:
            if tag in html_all:
                issues.append(
                    f"MX5 {name}: <{tag}> is used on a bundle that can render at the Small form "
                    "factor; datatable and tree-grid aren't supported on mobile devices."
                )

    # ---------------- mobile capabilities ----------------
    uses_capabilities = "lightning/mobileCapabilities" in js_all
    if uses_capabilities:
        called = [c for c in CAPABILITY_CALLS if c in js_all]
        if called and "isAvailable(" not in js_all:
            issues.append(
                f"MC1 {name}: calls {sorted(called)} from lightning/mobileCapabilities with no "
                "isAvailable() guard; the module resolves only inside a supported mobile app."
            )
        if ("scan(" in js_all or "beginCapture(" in js_all) and not (
            "dismiss(" in js_all or "endCapture(" in js_all
        ):
            issues.append(
                f"MC2 {name}: starts a scanning session with no dismiss()/endCapture() teardown; "
                "the OS scanner interface stays on screen after success or error."
            )
        legacy = [c for c in LEGACY_SCAN_CALLS if c in js_all]
        if legacy:
            issues.append(
                f"MC3 {name}: uses the legacy scanning API {sorted(legacy)}; "
                "migrate to scan() / dismiss() before it is retired."
            )
        if called and ".catch(" not in js_all and "try {" not in js_all:
            issues.append(
                f"MC4 {name}: mobile capability call with no .catch() or try/catch; "
                "isAvailable() does not remove the need to handle permission and service errors."
            )

    # ---------------- offline data path ----------------
    declares_offline = any(m in (js_raw + html_all).lower() for m in OFFLINE_MARKERS)
    if declares_offline:
        apex_import = re.search(r"from\s+['\"]@salesforce/apex/", js_all)
        if apex_import:
            issues.append(
                f"OF1 {name}: imports Apex in a bundle documented as mobile-offline; Apex shares "
                "no data cache with LDS, so the two disagree both online and offline."
            )
        if re.search(r"from\s+['\"]lightning/graphql['\"]", js_all):
            issues.append(
                f"OF2 {name}: imports lightning/graphql (v2) in a bundle documented as "
                "mobile-offline; only lightning/uiGraphQLApi (v1) supports Mobile Offline."
            )
    if "localStorage" in js_all or "sessionStorage" in js_all:
        issues.append(
            f"OF3 {name}: uses browser storage; record data that must survive offline belongs in "
            "an LDS-backed wire adapter, not a hand-rolled store."
        )

    # ---------------- DOM / sizing assumptions ----------------
    if re.search(r"\bdocument\.(querySelector|querySelectorAll|getElementById)\s*\(", js_all):
        issues.append(
            f"DM1 {name}: uses document.querySelector/getElementById; code cannot reach a "
            "component's shadow tree through document — use this.template.querySelector()."
        )
    size_globals = [
        g
        for g in ("window.innerWidth", "window.innerHeight", "screen.width", "navigator.userAgent")
        if g in js_all
    ]
    if size_globals and "@salesforce/client/formFactor" not in js_all:
        issues.append(
            f"DM2 {name}: infers device class from {sorted(size_globals)} with no "
            "@salesforce/client/formFactor import; use the documented Large/Medium/Small values."
        )

    # ---------------- tests ----------------
    tests_dir = bundle / "__tests__"
    if not tests_dir.is_dir():
        issues.append(f"TS1 {name}: no __tests__ folder.")
    elif not any("describe(" in p.read_text(encoding="utf-8", errors="ignore") for p in tests_dir.glob("*.js")):
        issues.append(f"TS1 {name}: __tests__ exists but contains no describe( block.")

    return issues


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check LWC bundles for mobile-app and Mobile Offline problems.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    args = parser.parse_args()

    root = Path(args.manifest_dir)
    if not root.is_dir():
        print(f"ERROR: manifest directory not found: {root}", file=sys.stderr)
        return 1

    bundles = find_bundles(root)
    if not bundles:
        print(f"WARN: no LWC bundles found under {root}")
        return 0

    issues: list[str] = []
    for bundle in bundles:
        issues.extend(check_bundle(bundle))

    print(f"Scanned {len(bundles)} LWC bundle(s) under {root}.")
    if not issues:
        print("No issues found.")
        return 0
    for issue in issues:
        print(f"ISSUE: {issue}")
    print(f"\n{len(issues)} issue(s) found.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
