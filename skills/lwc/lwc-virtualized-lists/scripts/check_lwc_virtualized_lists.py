#!/usr/bin/env python3
"""Static checks for LWC virtualized-list anti-patterns.

Scans LWC bundles for the high-confidence smells documented in this
skill's references:

  1. `new IntersectionObserver(cb)` with no second argument (no `root`
     option) — fires unreliably inside Lightning shadow DOM.
  2. `connectedCallback` body containing both `template.querySelector`
     and `IntersectionObserver` / `observe(` — the observer should
     wire in `renderedCallback`, after the sentinel exists.
  3. LWC class declaring `_observer` (or similar) but with no
     `disconnectedCallback` defined — observer leak.
  4. `key={i}` where `i` comes from `for:index` — unstable key in a
     virtualized context.

Stdlib only. Conservative regexes; signal tool, not a parser.

Usage:
    python3 check_lwc_virtualized_lists.py --src-root .
    python3 check_lwc_virtualized_lists.py --src-root force-app/main/default
    python3 check_lwc_virtualized_lists.py --help
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# Smell 1: new IntersectionObserver(...) with NO second argument.
# Match `new IntersectionObserver(<expr>)` where <expr> doesn't contain a comma
# at top level. We approximate with "no comma before the closing paren".
_OBSERVER_NO_OPTS_RE = re.compile(
    r"\bnew\s+IntersectionObserver\s*\(\s*[^,()]+\)",
    re.IGNORECASE,
)

# Smell 2: connectedCallback wiring observer
_CONNECTED_OBSERVER_RE = re.compile(
    r"\bconnectedCallback\s*\([^)]*\)\s*\{[^}]*?(?:IntersectionObserver|\.observe\s*\()",
    re.IGNORECASE | re.DOTALL,
)

# Smell 3: class declares _observer but no disconnectedCallback
_OBSERVER_FIELD_RE = re.compile(r"\b_observer\b")
_DISCONNECTED_RE = re.compile(r"\bdisconnectedCallback\s*\(", re.IGNORECASE)

# Smell 4: key={i} where i is the for:index. Need to match HTML templates.
_FOR_INDEX_RE = re.compile(
    r"for:index\s*=\s*['\"](\w+)['\"]",
    re.IGNORECASE,
)


def _line_no(text: str, pos: int) -> int:
    return text[:pos].count("\n") + 1


def _scan_js(path: Path) -> list[str]:
    findings: list[str] = []
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError as exc:
        return [f"could not read {path}: {exc}"]

    for m in _OBSERVER_NO_OPTS_RE.finditer(text):
        findings.append(
            f"{path}:{_line_no(text, m.start())}: `new IntersectionObserver(cb)` with no "
            "options — pass `{ root: <in-shadow-root scrollable ancestor>, "
            "rootMargin, threshold }` (references/gotchas.md § 2)"
        )

    for m in _CONNECTED_OBSERVER_RE.finditer(text):
        findings.append(
            f"{path}:{_line_no(text, m.start())}: IntersectionObserver wired in "
            "`connectedCallback` — sentinel may not be rendered yet; move to "
            "`renderedCallback` with an idempotent guard "
            "(references/gotchas.md § 6)"
        )

    if _OBSERVER_FIELD_RE.search(text) and not _DISCONNECTED_RE.search(text):
        findings.append(
            f"{path}: declares `_observer` but no `disconnectedCallback` — "
            "observer will leak when the component unmounts "
            "(references/gotchas.md § 9)"
        )

    return findings


def _scan_html(path: Path) -> list[str]:
    findings: list[str] = []
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError as exc:
        return [f"could not read {path}: {exc}"]

    for m in _FOR_INDEX_RE.finditer(text):
        idx_var = m.group(1)
        # Look for key={<idx_var>} within ~200 chars of the for:index.
        nearby = text[m.start() : m.start() + 400]
        key_re = re.compile(r"key\s*=\s*\{\s*" + re.escape(idx_var) + r"\s*\}")
        if key_re.search(nearby):
            findings.append(
                f"{path}:{_line_no(text, m.start())}: `key={{{idx_var}}}` uses the "
                "for-each index — unstable across window shifts. Use "
                "`key={item.id}` or another stable property "
                "(references/gotchas.md § 8)"
            )

    return findings


def scan_tree(root: Path) -> list[str]:
    if not root.exists():
        return [f"src-root does not exist: {root}"]
    if not root.is_dir():
        return [f"src-root is not a directory: {root}"]

    findings: list[str] = []
    for js in root.rglob("*.js"):
        # Heuristic: only scan files inside LWC bundles
        if "lwc" not in str(js).lower() and "force-app" not in str(js).lower():
            continue
        findings.extend(_scan_js(js))

    for html in root.rglob("*.html"):
        if "lwc" not in str(html).lower() and "force-app" not in str(html).lower():
            continue
        findings.extend(_scan_html(html))

    return findings


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Scan LWC bundles for virtualized-list anti-patterns "
            "(IntersectionObserver without root, observer wired in connectedCallback, "
            "missing disconnectedCallback cleanup, for-index used as key)."
        ),
    )
    parser.add_argument(
        "--src-root", default=".",
        help="Root of the LWC source tree (default: current directory).",
    )
    args = parser.parse_args()

    findings = scan_tree(Path(args.src_root))

    if not findings:
        print("OK: no LWC virtualized-list anti-patterns detected.")
        return 0

    for f in findings:
        print(f"WARN: {f}", file=sys.stderr)
    print(f"\n{len(findings)} finding(s).", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
