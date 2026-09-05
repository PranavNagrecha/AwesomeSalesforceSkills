#!/usr/bin/env python3
"""Static analysis for static-resource loading in Lightning Web Components.

Scans a Salesforce source tree (``--manifest-dir``) covering both the ``lwc``
bundles that load resources and the ``staticresources`` folder that supplies
them, and reports the defects that break at run time rather than at deploy
time.

Checks
------
SR001  Remote <script src> / <link href> in an LWC template.
       "you can't load JavaScript resources from a third-party site, even from
       a trusted URL" - LWC Developer Guide, js-api-calls.
SR002  loadScript()/loadStyle() called outside renderedCallback().
       The guide invokes both in renderedCallback() so the container element
       exists before the library reaches for it - js-third-party-library.
SR003  loadScript()/loadStyle() in renderedCallback() with no one-time guard.
       "A component is usually rendered many times during the lifespan of an
       application ... use a boolean field like hasRendered" -
       create-lifecycle-hooks-rendered.
SR004  @salesforce/resourceUrl import naming a resource that is not in
       staticresources/ (namespaced ns__name imports are skipped).
SR005  StaticResource *-meta.xml missing/invalid cacheControl or contentType.
       Both are Required in the Metadata API StaticResource field table.
SR006  loadScript()/loadStyle() result neither awaited nor chained - library
       globals touched on the next line are not defined yet.
SR007  Library writes into the DOM but the bundle template has no
       lwc:dom="manual" container.
SR008  Static resource content file with no *-meta.xml (or the reverse).

Usage
-----
    python3 check_static_resources_in_lwc.py --manifest-dir force-app
    python3 check_static_resources_in_lwc.py --manifest-dir force-app --json

Exit code 0 when clean, 1 when any issue is reported, 2 on a usage error.
Stdlib only. No org connection, no deploy, no compilation.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

MD_NS = "{http://soap.sforce.com/2006/04/metadata}"

VALID_CACHE_CONTROL = {"Private", "Public"}

REMOTE_SCRIPT_RE = re.compile(
    r"<\s*(?:script[^>]*\bsrc|link[^>]*\bhref)\s*=\s*[\"'](?:https?:)?//", re.IGNORECASE
)
LOADER_CALL_RE = re.compile(r"\b(loadScript|loadStyle)\s*\(")
RESOURCE_IMPORT_RE = re.compile(
    r"""import\s+(\w+)\s+from\s+['"]@salesforce/resourceUrl/([A-Za-z0-9_]+)['"]"""
)
RENDERED_CALLBACK_RE = re.compile(r"\brenderedCallback\s*\(\s*\)\s*\{")
PROMISE_AGGREGATE_RE = re.compile(r"\bPromise\s*\.\s*(?:all|allSettled|race|any)\s*\(")
GUARD_SET_RE = re.compile(r"this\.\w+\s*=\s*true")
GUARD_RETURN_RE = re.compile(r"if\s*\(\s*this\.\w+\s*\)\s*\{?\s*(?:\n\s*)?return")
DOM_WRITE_RE = re.compile(
    r"\.appendChild\s*\(|\.innerHTML\s*=|\binsertAdjacentHTML\s*\(|\bd3\s*\.\s*select\s*\("
)
DOM_MANUAL_RE = re.compile(r"""lwc:dom\s*=\s*["']manual["']""")
DOC_QUERY_RE = re.compile(r"\bdocument\s*\.\s*(?:querySelector|getElementById|getElementsBy)")


# --------------------------------------------------------------------------
# small helpers
# --------------------------------------------------------------------------
def child(element, tag: str):
    """Return a direct child element by tag, namespace-tolerant.

    A leaf ``Element`` is falsy, so ``el.find(a) or el.find(b)`` silently drops
    real elements. Always compare against ``None``.
    """
    if element is None:
        return None
    found = element.find(MD_NS + tag)
    if found is None:
        found = element.find(tag)
    return found


def child_text(element, tag: str) -> str:
    node = child(element, tag)
    if node is None or node.text is None:
        return ""
    return node.text.strip()


def read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def strip_comments(source: str) -> str:
    """Blank out // and /* */ comments so keyword scans do not match prose."""
    source = re.sub(r"/\*.*?\*/", lambda m: " " * len(m.group(0)), source, flags=re.S)
    return re.sub(r"//[^\n]*", lambda m: " " * len(m.group(0)), source)


def balanced_span(source: str, open_index: int, opener: str = "{", closer: str = "}") -> int:
    """Return the index just past the delimiter that closes the one at open_index."""
    depth = 0
    for i in range(open_index, len(source)):
        ch = source[i]
        if ch == opener:
            depth += 1
        elif ch == closer:
            depth -= 1
            if depth == 0:
                return i + 1
    return len(source)


def aggregate_spans(source: str) -> list[tuple[int, int]]:
    """Character spans of Promise.all(...) / Promise.allSettled(...) argument lists.

    A loader call inside one of these is already part of a promise chain, so
    SR006 must not flag it.
    """
    spans: list[tuple[int, int]] = []
    for match in PROMISE_AGGREGATE_RE.finditer(source):
        open_index = match.end() - 1
        spans.append((open_index, balanced_span(source, open_index, "(", ")")))
    return spans


def rendered_callback_body(source: str) -> str:
    match = RENDERED_CALLBACK_RE.search(source)
    if match is None:
        return ""
    start = match.end() - 1
    return source[start : balanced_span(source, start)]


def line_of(source: str, index: int) -> int:
    return source.count("\n", 0, index) + 1


# --------------------------------------------------------------------------
# discovery
# --------------------------------------------------------------------------
def find_static_resources(root: Path) -> tuple[set[str], list[str]]:
    """Return (resource names, SR005/SR008 issues) for every staticresources dir."""
    names: set[str] = set()
    issues: list[str] = []

    for sr_dir in sorted(p for p in root.rglob("staticresources") if p.is_dir()):
        metas: dict[str, Path] = {}
        contents: set[str] = set()

        for entry in sorted(sr_dir.iterdir()):
            if entry.name.endswith(".resource-meta.xml"):
                metas[entry.name[: -len(".resource-meta.xml")]] = entry
            elif not entry.name.startswith("."):
                contents.add(entry.name.split(".")[0])

        names.update(metas)
        names.update(contents)

        for name, meta_path in sorted(metas.items()):
            issues.extend(check_resource_meta(meta_path))
            if name not in contents:
                issues.append(
                    f"SR008 {meta_path}: -meta.xml has no matching content file or folder "
                    f"named '{name}'; the deploy fails with a missing content error."
                )
        for name in sorted(contents - set(metas)):
            issues.append(
                f"SR008 {sr_dir / name}: static resource content has no "
                f"'{name}.resource-meta.xml'; contentType and cacheControl are Required "
                f"fields on StaticResource, so the deploy has nothing to read them from."
            )

    return names, issues


def check_resource_meta(meta_path: Path) -> list[str]:
    issues: list[str] = []
    try:
        root = ET.parse(meta_path).getroot()
    except ET.ParseError as exc:
        return [f"SR005 {meta_path}: not well-formed XML ({exc})."]

    cache_control = child_text(root, "cacheControl")
    content_type = child_text(root, "contentType")

    if not cache_control:
        issues.append(
            f"SR005 {meta_path}: <cacheControl> is missing; it is a Required field on "
            f"StaticResource and must be Private or Public."
        )
    elif cache_control not in VALID_CACHE_CONTROL:
        issues.append(
            f"SR005 {meta_path}: <cacheControl>{cache_control}</cacheControl> is not a valid "
            f"StaticResourceCacheControl value (Private, Public)."
        )

    if not content_type:
        issues.append(
            f"SR005 {meta_path}: <contentType> is missing; it is a Required field on "
            f"StaticResource (for example application/zip or text/javascript)."
        )
    return issues


def find_lwc_bundles(root: Path) -> list[tuple[Path, Path, Path | None]]:
    """Return (bundle_dir, js_path, html_path) for every LWC bundle found."""
    bundles: list[tuple[Path, Path, Path | None]] = []
    seen: set[Path] = set()

    for meta in sorted(root.rglob("*.js-meta.xml")):
        base = meta.name[: -len(".js-meta.xml")]
        js_path = meta.parent / f"{base}.js"
        if js_path.exists():
            html = meta.parent / f"{base}.html"
            bundles.append((meta.parent, js_path, html if html.exists() else None))
            seen.add(meta.parent)

    # Bundles whose -meta.xml has not been written yet still deserve a scan.
    for js_path in sorted(root.rglob("*.js")):
        parent = js_path.parent
        if parent in seen or parent.name != js_path.stem:
            continue
        if parent.parent.name != "lwc":
            continue
        html = parent / f"{js_path.stem}.html"
        bundles.append((parent, js_path, html if html.exists() else None))
        seen.add(parent)

    return bundles


# --------------------------------------------------------------------------
# per-bundle checks
# --------------------------------------------------------------------------
def check_template(html_path: Path) -> list[str]:
    text = read(html_path)
    issues: list[str] = []
    if REMOTE_SCRIPT_RE.search(text):
        issues.append(
            f"SR001 {html_path}: remote <script src>/<link href> in an LWC template. "
            f"JavaScript cannot be loaded from a third-party site even through a "
            f"Trusted URL; package the file as a static resource and use "
            f"lightning/platformResourceLoader."
        )
    return issues


def check_bundle_js(
    js_path: Path, html_path: Path | None, resource_names: set[str], strict_manifest: bool
) -> list[str]:
    raw = read(js_path)
    source = strip_comments(raw)
    issues: list[str] = []

    loader_calls = list(LOADER_CALL_RE.finditer(source))
    imports = RESOURCE_IMPORT_RE.findall(source)

    # SR004 - imported resource is not in the source tree
    if strict_manifest:
        for _binding, resource in imports:
            if "__" in resource:  # ns__name: the resource lives in a managed package
                continue
            if resource not in resource_names:
                issues.append(
                    f"SR004 {js_path}: imports @salesforce/resourceUrl/{resource} but no "
                    f"'{resource}' exists under staticresources/. Either the resource is "
                    f"missing from the deployment or the name is misspelled - the import "
                    f"fails at compile time in the org, not in Jest."
                )

    if not loader_calls:
        return issues

    rc_body = rendered_callback_body(source)
    rc_loader_count = len(LOADER_CALL_RE.findall(rc_body)) if rc_body else 0

    # SR002 - loader used outside renderedCallback()
    if rc_loader_count < len(loader_calls):
        outside = len(loader_calls) - rc_loader_count
        issues.append(
            f"SR002 {js_path}: {outside} loadScript()/loadStyle() call(s) outside "
            f"renderedCallback(). Load from renderedCallback() so the container element "
            f"the library reaches for is already in the DOM."
        )

    # SR003 - no one-time guard around the load
    if rc_loader_count and not (
        GUARD_SET_RE.search(rc_body) and GUARD_RETURN_RE.search(rc_body)
    ):
        issues.append(
            f"SR003 {js_path}: renderedCallback() loads a resource with no one-time guard "
            f"(a boolean field set to true plus an early return). renderedCallback() runs "
            f"on every render, so the library re-initializes on each one."
        )

    # SR006 - loader promise neither awaited nor chained
    aggregated = aggregate_spans(source)
    for match in loader_calls:
        prefix = source[max(0, match.start() - 24) : match.start()]
        end = balanced_span(source, match.end() - 1, "(", ")")
        tail = source[end : end + 16].lstrip()
        awaited = "await" in prefix or "return" in prefix
        inside_aggregate = any(lo <= match.start() < hi for lo, hi in aggregated)
        chained = tail.startswith((".then", ".catch", ".finally", ","))
        if not awaited and not chained and not inside_aggregate:
            issues.append(
                f"SR006 {js_path}:{line_of(source, match.start())}: the "
                f"{match.group(1)}() promise is neither awaited nor chained. Anything the "
                f"library defines is still undefined on the next line."
            )

    # SR007 - DOM-writing library without an lwc:dom=\"manual\" container
    if DOM_WRITE_RE.search(source):
        html_text = read(html_path) if html_path else ""
        if not DOM_MANUAL_RE.search(html_text):
            target = html_path if html_path else js_path.with_suffix(".html")
            issues.append(
                f"SR007 {target}: the component loads a library that writes into the DOM "
                f"(appendChild / innerHTML / d3.select) but no element carries "
                f'lwc:dom="manual". Without the directive the engine does not preserve '
                f"encapsulation and styling is not applied to appended elements."
            )

    # DOM access containment - a library callback reaching for document
    if DOC_QUERY_RE.search(source):
        issues.append(
            f"SR007 {js_path}: document.querySelector/getElementById found. In a Lightning "
            f"web component use this.template to reach the container you hand to the "
            f"library."
        )

    return issues


# --------------------------------------------------------------------------
# driver
# --------------------------------------------------------------------------
def run(manifest_dir: Path) -> list[str]:
    if not manifest_dir.exists():
        return [f"SR000 manifest directory not found: {manifest_dir}"]

    resource_names, issues = find_static_resources(manifest_dir)
    strict_manifest = bool(resource_names)

    bundles = find_lwc_bundles(manifest_dir)
    for _bundle_dir, js_path, html_path in bundles:
        if html_path is not None:
            issues.extend(check_template(html_path))
        issues.extend(check_bundle_js(js_path, html_path, resource_names, strict_manifest))

    # Templates that are not part of a detected bundle still get the SR001 scan.
    scanned = {h for _b, _j, h in bundles if h is not None}
    for html_path in sorted(manifest_dir.rglob("*.html")):
        if html_path not in scanned:
            issues.extend(check_template(html_path))

    return issues


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check LWC bundles and staticresources/ for static-resource loading defects."
        )
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root of the Salesforce source tree to scan (default: current directory).",
    )
    parser.add_argument(
        "--json", action="store_true", help="Emit findings as a JSON array."
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    issues = run(Path(args.manifest_dir))

    if args.json:
        print(json.dumps(issues, indent=2))
        return 1 if issues else 0

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")
    print(f"\n{len(issues)} issue(s) found.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
