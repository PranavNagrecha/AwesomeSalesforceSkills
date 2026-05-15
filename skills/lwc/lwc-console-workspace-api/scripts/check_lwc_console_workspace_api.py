#!/usr/bin/env python3
"""Static checker for LWC bundles using lightning/platformWorkspaceApi.

Scans LWC source under `force-app/**/lwc/*` and flags console-API hygiene issues:

- bundles that import workspace-API lifecycle functions (openTab, openSubtab,
  refreshTab, closeTab, focusTab, setTabLabel, setTabIcon, setTabHighlighted)
  but do NOT also import or wire IsConsoleNavigation
- bundles that persist tabId-looking values to sessionStorage / localStorage
- bundles using Aura-style child-component access for workspace API
  (e.g., `<lightning-workspace-api>` in HTML, or `.openSubtab(` on a
  template.querySelector result)
- bundles that read this.isConsole inside connectedCallback (wire not yet
  resolved on first render)

Stdlib only. Regex-based.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

WORKSPACE_LIFECYCLE_FUNCS = {
    "openTab", "openSubtab", "closeTab", "refreshTab", "focusTab",
    "getFocusedTabInfo", "getAllTabInfo", "getTabInfo",
    "setTabLabel", "setTabIcon", "setTabHighlighted",
    "getEnclosingTabId", "EnclosingTabId",
}

WORKSPACE_IMPORT_RE = re.compile(
    r"import\s*\{([^}]+)\}\s*from\s*['\"]lightning/platformWorkspaceApi['\"]"
)
UTILITY_IMPORT_RE = re.compile(
    r"import\s*\{([^}]+)\}\s*from\s*['\"]lightning/platformUtilityBarApi['\"]"
)
IS_CONSOLE_USED_RE = re.compile(r"\bIsConsoleNavigation\b")
STORAGE_TABID_RE = re.compile(
    r"(sessionStorage|localStorage)\s*\.\s*setItem\s*\(\s*[^,]+,\s*[^)]*tabId",
    re.IGNORECASE,
)
AURA_WORKSPACE_TEMPLATE_RE = re.compile(r"<lightning[-:]workspace[-:]api\b", re.IGNORECASE)
AURA_WORKSPACE_QS_RE = re.compile(
    r"querySelector\(\s*['\"]lightning-workspace-api['\"]"
)
CONNECTED_CALLBACK_RE = re.compile(
    r"connectedCallback\s*\(\s*\)\s*\{([^{}]|\{[^{}]*\})*\}", re.DOTALL
)
THIS_IS_CONSOLE_RE = re.compile(r"this\.\s*isConsole\b")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit LWC bundles for workspace-API hygiene.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce project (default: current directory).",
    )
    return parser.parse_args()


def lwc_bundles(root: Path) -> list[Path]:
    """Return LWC bundle directories under force-app."""
    bundles: list[Path] = []
    fa = root / "force-app"
    if not fa.exists():
        return bundles
    for lwc_dir in fa.rglob("lwc"):
        if not lwc_dir.is_dir():
            continue
        for sub in lwc_dir.iterdir():
            if sub.is_dir() and (sub / f"{sub.name}.js").exists():
                bundles.append(sub)
    return bundles


def imports_from_module(text: str, regex: re.Pattern) -> set[str]:
    out: set[str] = set()
    for match in regex.finditer(text):
        names = match.group(1)
        for raw in names.split(","):
            name = raw.strip().split(" as ")[0].strip()
            if name:
                out.add(name)
    return out


def check_bundle(bundle: Path) -> list[str]:
    issues: list[str] = []
    js_file = bundle / f"{bundle.name}.js"
    if not js_file.exists():
        return issues
    try:
        js_text = js_file.read_text(encoding="utf-8")
    except OSError:
        return issues

    ws_imports = imports_from_module(js_text, WORKSPACE_IMPORT_RE)
    lifecycle_used = ws_imports & WORKSPACE_LIFECYCLE_FUNCS

    if lifecycle_used:
        if "IsConsoleNavigation" not in ws_imports and not IS_CONSOLE_USED_RE.search(js_text):
            issues.append(
                f"{js_file}: imports workspace-API lifecycle functions "
                f"({', '.join(sorted(lifecycle_used))}) without IsConsoleNavigation "
                f"gate — component will throw outside a console host"
            )

    if STORAGE_TABID_RE.search(js_text):
        issues.append(
            f"{js_file}: persists a tabId to session/localStorage — tabIds are "
            f"ephemeral and do not survive page reload; persist recordId and "
            f"re-resolve via getAllTabInfo()"
        )

    # Aura-style workspace API access in LWC template
    for html_file in bundle.glob("*.html"):
        try:
            html_text = html_file.read_text(encoding="utf-8")
        except OSError:
            continue
        if AURA_WORKSPACE_TEMPLATE_RE.search(html_text):
            issues.append(
                f"{html_file}: uses <lightning-workspace-api> as a child "
                f"component — LWC exposes platformWorkspaceApi as a module, "
                f"not an embedded element"
            )

    if AURA_WORKSPACE_QS_RE.search(js_text):
        issues.append(
            f"{js_file}: queries for 'lightning-workspace-api' element in DOM "
            f"— LWC pattern is module import, not template element"
        )

    # connectedCallback referencing this.isConsole
    for cb_match in CONNECTED_CALLBACK_RE.finditer(js_text):
        body = cb_match.group(0)
        if THIS_IS_CONSOLE_RE.search(body):
            issues.append(
                f"{js_file}: connectedCallback reads this.isConsole — wire "
                f"adapter has not emitted on first render; defer to "
                f"renderedCallback or user-event handler"
            )
            break

    return issues


def main() -> int:
    args = parse_args()
    root = Path(args.manifest_dir)
    if not (root / "force-app").exists():
        print(f"ERROR: no force-app/ directory under {root}", file=sys.stderr)
        return 1

    bundles = lwc_bundles(root)
    if not bundles:
        print("[lwc-console-workspace-api] no LWC bundles found under force-app/")
        return 0

    issues: list[str] = []
    for bundle in bundles:
        issues.extend(check_bundle(bundle))

    if not issues:
        print(f"[lwc-console-workspace-api] no issues across {len(bundles)} bundle(s)")
        return 0

    for i in issues:
        print(f"WARN: {i}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
