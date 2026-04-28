#!/usr/bin/env python3
"""
check_lwc_shadow_vs_light_dom_decision.py

Static checker for the LWC Shadow vs Light DOM render-mode decision skill.

Scans an LWC bundle (or a directory containing many bundles) for drift
between the declared render mode and the supporting CSS / event /
template wiring.

Findings:

  P0  Light DOM bundle (JS declares `static renderMode = 'light'`
      OR template uses `lwc:render-mode="light"`) has a CSS file with
      one or more `:host` selectors. `:host` is silently dropped under
      Light DOM. Hoist to a real selector or remove the rule.

  P0  Bundle CSS file is named `<componentName>.css` AND the bundle
      is Light DOM. That stylesheet is GLOBAL — every selector leaks
      to the whole page. Rename to `<componentName>.scoped.css` for
      component-local rules.

  P1  Light DOM bundle dispatches a CustomEvent with explicit
      `composed: false`. That is dead configuration: Light DOM has no
      shadow boundary, so the flag does nothing. Remove it.

  P1  Shadow DOM bundle (no Light DOM opt-in) dispatches a CustomEvent
      with `bubbles: true` but no `composed` flag set, AND the event
      name suggests an external listener (e.g. ends with 'save',
      'change', 'select', 'submit', 'close'). Likely missing
      `composed: true`. Manual review required.

  P2  Shadow DOM bundle CSS file uses a top-level global selector
      (`html`, `body`, `*`) inside its `.css`. These selectors are
      scoped to the shadow root and almost certainly do nothing —
      the developer probably meant to target the host element via
      `:host` or a class.

stdlib only. Exits 1 on any P0 or P1 finding, 0 otherwise (P2 is
informational).

Usage:
    python3 check_lwc_shadow_vs_light_dom_decision.py <path> [<path> ...]

Each <path> may be:
  - an LWC bundle directory (containing `<name>.js`, `<name>.html`, etc.)
  - a parent directory (e.g. `force-app/main/default/lwc`) — every
    immediate subdirectory is treated as an LWC bundle
"""

from __future__ import annotations

import os
import re
import sys
from typing import Dict, Iterable, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Regexes
# ---------------------------------------------------------------------------

# JS — `static renderMode = 'light'` (allow double quotes, whitespace)
JS_LIGHT_RE = re.compile(
    r"static\s+renderMode\s*=\s*['\"]light['\"]",
)

# Template — `lwc:render-mode="light"` (the canonical attribute on <template>)
TPL_LIGHT_RE = re.compile(
    r"lwc:render-mode\s*=\s*['\"]light['\"]",
    re.IGNORECASE,
)

# CSS — `:host` selector (start of selector or after a comma)
HOST_SELECTOR_RE = re.compile(r"(^|[\s,{])\s*:host\b")

# CSS — global selectors leaking out under Shadow DOM (informational P2)
GLOBAL_SELECTOR_RE = re.compile(
    r"(^|[\}])\s*(html|body|\*)\s*[\{,\s]",
    re.IGNORECASE,
)

# JS — CustomEvent options with composed: false
COMPOSED_FALSE_RE = re.compile(
    r"composed\s*:\s*false",
)

# JS — CustomEvent options with composed: true
COMPOSED_TRUE_RE = re.compile(
    r"composed\s*:\s*true",
)

# JS — bubbles: true (used to detect "external" event candidates)
BUBBLES_TRUE_RE = re.compile(
    r"bubbles\s*:\s*true",
)

# JS — CustomEvent dispatch with event name (best-effort capture)
CUSTOM_EVENT_NAME_RE = re.compile(
    r"new\s+CustomEvent\s*\(\s*['\"]([a-zA-Z0-9_:-]+)['\"]",
)

# Event names that strongly suggest an external listener
EXTERNAL_EVENT_HINTS = (
    "save", "saved", "change", "changed", "select", "selected",
    "submit", "submitted", "close", "closed", "open", "opened",
    "navigate", "click", "delete", "deleted", "create", "created",
    "update", "updated", "cancel", "cancelled", "confirm",
)

LINE_COMMENT_RE = re.compile(r"//.*$", re.MULTILINE)
BLOCK_COMMENT_RE = re.compile(r"/\*.*?\*/", re.DOTALL)
CSS_BLOCK_COMMENT_RE = re.compile(r"/\*.*?\*/", re.DOTALL)


# ---------------------------------------------------------------------------
# Bundle discovery
# ---------------------------------------------------------------------------

def looks_like_lwc_bundle(path: str) -> bool:
    """A directory whose immediate children include a `<name>.js` matching the dir name."""
    if not os.path.isdir(path):
        return False
    name = os.path.basename(os.path.normpath(path))
    js_path = os.path.join(path, f"{name}.js")
    return os.path.isfile(js_path)


def iter_bundles(paths: Iterable[str]) -> Iterable[str]:
    seen = set()
    for raw in paths:
        if not os.path.exists(raw):
            print(f"WARN: skipping missing path: {raw}", file=sys.stderr)
            continue
        if looks_like_lwc_bundle(raw):
            ap = os.path.abspath(raw)
            if ap not in seen:
                seen.add(ap)
                yield raw
            continue
        if os.path.isdir(raw):
            # treat each immediate subdirectory as a possible bundle
            for child in sorted(os.listdir(raw)):
                full = os.path.join(raw, child)
                if looks_like_lwc_bundle(full):
                    ap = os.path.abspath(full)
                    if ap not in seen:
                        seen.add(ap)
                        yield full


# ---------------------------------------------------------------------------
# File loading
# ---------------------------------------------------------------------------

def read_text(path: str) -> Optional[str]:
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            return fh.read()
    except OSError:
        return None


def strip_js_comments(src: str) -> str:
    src = BLOCK_COMMENT_RE.sub("", src)
    src = LINE_COMMENT_RE.sub("", src)
    return src


def strip_css_comments(src: str) -> str:
    return CSS_BLOCK_COMMENT_RE.sub("", src)


def collect_bundle_files(bundle_dir: str) -> Dict[str, List[str]]:
    """Group bundle files by extension."""
    grouped: Dict[str, List[str]] = {"js": [], "html": [], "css": [], "scoped_css": []}
    for entry in os.listdir(bundle_dir):
        full = os.path.join(bundle_dir, entry)
        if not os.path.isfile(full):
            continue
        if entry.endswith(".scoped.css"):
            grouped["scoped_css"].append(full)
        elif entry.endswith(".css"):
            grouped["css"].append(full)
        elif entry.endswith(".js"):
            grouped["js"].append(full)
        elif entry.endswith(".html"):
            grouped["html"].append(full)
    return grouped


# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------

def is_light_dom(files: Dict[str, List[str]]) -> bool:
    """Detect Light DOM opt-in by scanning JS and HTML."""
    for js in files["js"]:
        text = read_text(js) or ""
        clean = strip_js_comments(text)
        if JS_LIGHT_RE.search(clean):
            return True
    for tpl in files["html"]:
        text = read_text(tpl) or ""
        if TPL_LIGHT_RE.search(text):
            return True
    return False


def analyse_bundle(bundle_dir: str) -> List[Tuple[str, str]]:
    findings: List[Tuple[str, str]] = []
    files = collect_bundle_files(bundle_dir)
    if not files["js"]:
        return findings

    bundle_name = os.path.basename(os.path.normpath(bundle_dir))
    light = is_light_dom(files)

    # ---- CSS: :host under Light DOM (P0) ----
    if light:
        all_css_paths = files["css"] + files["scoped_css"]
        for css_path in all_css_paths:
            text = read_text(css_path) or ""
            clean = strip_css_comments(text)
            if HOST_SELECTOR_RE.search(clean):
                findings.append((
                    "P0",
                    f"{css_path}: bundle '{bundle_name}' is Light DOM but the CSS contains "
                    f"a `:host` selector. `:host` is silently dropped under Light DOM. "
                    f"Hoist to a real selector (e.g. `.{bundle_name}-root`) and add a "
                    f"wrapping element in the template.",
                ))

    # ---- CSS: unscoped <name>.css under Light DOM (P0) ----
    if light and files["css"]:
        # Only flag if the file name matches the bundle name AND there is content
        # beyond a comment/empty file.
        for css_path in files["css"]:
            base = os.path.basename(css_path)
            if base == f"{bundle_name}.css":
                text = read_text(css_path) or ""
                if strip_css_comments(text).strip():
                    findings.append((
                        "P0",
                        f"{css_path}: bundle '{bundle_name}' is Light DOM and ships a "
                        f"global `{base}`. Every selector in this file leaks to the whole "
                        f"page. Rename to `{bundle_name}.scoped.css` for component-local "
                        f"rules.",
                    ))

    # ---- JS: composed: false in Light DOM (P1) ----
    if light:
        for js_path in files["js"]:
            text = read_text(js_path) or ""
            clean = strip_js_comments(text)
            if COMPOSED_FALSE_RE.search(clean):
                findings.append((
                    "P1",
                    f"{js_path}: bundle '{bundle_name}' is Light DOM but a CustomEvent "
                    f"explicitly sets `composed: false`. Light DOM has no shadow boundary, "
                    f"so the flag is dead configuration. Remove it.",
                ))

    # ---- JS: Shadow DOM external-looking event without composed:true (P1) ----
    if not light:
        for js_path in files["js"]:
            text = read_text(js_path) or ""
            clean = strip_js_comments(text)
            event_names = CUSTOM_EVENT_NAME_RE.findall(clean)
            if not event_names:
                continue
            has_bubbles = bool(BUBBLES_TRUE_RE.search(clean))
            has_composed_true = bool(COMPOSED_TRUE_RE.search(clean))
            if not has_bubbles or has_composed_true:
                continue
            external_hits = [n for n in event_names if any(h in n.lower() for h in EXTERNAL_EVENT_HINTS)]
            if external_hits:
                findings.append((
                    "P1",
                    f"{js_path}: bundle '{bundle_name}' is Shadow DOM and dispatches "
                    f"event(s) {sorted(set(external_hits))!r} with `bubbles: true` but "
                    f"no `composed: true`. External listeners in another shadow root "
                    f"will not receive the event. Set `composed: true` if listeners "
                    f"are external.",
                ))

    # ---- CSS: global selectors under Shadow DOM (P2) ----
    if not light:
        for css_path in files["css"] + files["scoped_css"]:
            text = read_text(css_path) or ""
            clean = strip_css_comments(text)
            if GLOBAL_SELECTOR_RE.search(clean):
                findings.append((
                    "P2",
                    f"{css_path}: bundle '{bundle_name}' is Shadow DOM and uses a "
                    f"top-level global selector (`html`, `body`, or `*`). These are "
                    f"scoped to the shadow root and almost certainly do nothing — "
                    f"target the host via `:host` or a class instead.",
                ))

    return findings


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

def main(argv: List[str]) -> int:
    if len(argv) < 2:
        print(__doc__, file=sys.stderr)
        return 2

    bundles = list(iter_bundles(argv[1:]))
    if not bundles:
        print("No LWC bundles found in the supplied paths.", file=sys.stderr)
        return 0

    all_findings: List[Tuple[str, str]] = []
    for bundle in bundles:
        all_findings.extend(analyse_bundle(bundle))

    if not all_findings:
        print(f"OK - scanned {len(bundles)} LWC bundle(s); no render-mode drift found.")
        return 0

    p0 = [f for f in all_findings if f[0] == "P0"]
    p1 = [f for f in all_findings if f[0] == "P1"]
    p2 = [f for f in all_findings if f[0] == "P2"]

    for severity, message in all_findings:
        print(f"[{severity}] {message}")

    print("")
    print(f"Summary: {len(p0)} P0, {len(p1)} P1, {len(p2)} P2 (info), "
          f"scanned {len(bundles)} bundle(s).")

    if p0 or p1:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
