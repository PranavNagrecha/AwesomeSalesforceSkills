#!/usr/bin/env python3
"""Checker for Lightning Out 2.0 embed markup and host-page code.

Scans an external host app's `.html` / `.js` files for the common mistakes
documented in references/gotchas.md and references/llm-anti-patterns.md when
embedding a custom LWC with Lightning Out 2.0 (the Winter '26 GA feature).
Stdlib only — no pip dependencies.

Usage:
    python3 check_lightning_out_2_embedding.py [--host-dir path]

Checks performed:
  - <lightning-out-application> present and carries `components` + `app-id`
    (`app-id` is advisory: apps created before Spring '26 don't require it)
  - `frontdoor-url` is not a hard-coded session (sid= / raw token) in static markup
  - the lightning.out <script> is included on the host page
  - legacy Aura Lightning Out (beta) usage ($Lightning.use / lightning:out)
  - loading the lightning.out library from inside a component (LWS blocks it)
  - `lightning/navigation` / NavigationMixin in embedded component JS (unsupported)
  - OAuth client credentials flow (unsupported — no user context)

Exit code 0 = no issues, 1 = issues found.
"""

from __future__ import annotations

import argparse
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

# A frontdoor URL / token that must not be hard-coded in served markup.
SECRET_IN_FRONTDOOR = re.compile(r"(?:[?&]sid=|access[_-]?token=|frontdoor\.jsp\?[^\"'>]*sid=)", re.I)
LEGACY_AURA = re.compile(r"\$Lightning\.(?:use|createComponent)\s*\(|<\s*lightning:out\b", re.I)
LIB_IN_LWC = re.compile(r"loadScript\s*\([^)]*lightning\.out|createElement\(\s*['\"]script['\"]", re.I)
NAV_SERVICE = re.compile(r"from\s+['\"]lightning/navigation['\"]|NavigationMixin")
CLIENT_CREDS = re.compile(r"grant_type\s*=\s*['\"]?client_credentials", re.I)
LIB_SCRIPT_SRC = re.compile(r"lightning\.out\.latest|/lightning/lightning\.out", re.I)
PLACEHOLDER_TOKENS = ("...", "my_domain", "redacted", "your", "example", "xxxx")


class _LightningOutFinder(HTMLParser):
    """Collects <lightning-out-application> tags and detects the library <script>."""

    def __init__(self) -> None:
        super().__init__()
        self.apps: list[dict[str, str | None]] = []
        self.has_lib_script = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_map = {name.lower(): value for name, value in attrs}
        if tag == "lightning-out-application":
            self.apps.append(attr_map)
        elif tag == "script":
            src = attr_map.get("src") or ""
            if LIB_SCRIPT_SRC.search(src):
                self.has_lib_script = True

    # Custom elements may be reported as startendtag in some documents.
    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)


def _looks_like_placeholder(value: str) -> bool:
    low = value.lower()
    return any(tok in low for tok in PLACEHOLDER_TOKENS)


def _check_html(path: Path, issues: list[str]) -> None:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        issues.append(f"{path}: could not read ({exc})")
        return

    parser = _LightningOutFinder()
    try:
        parser.feed(text)
    except Exception as exc:  # malformed HTML shouldn't crash the checker
        issues.append(f"{path}: could not parse HTML ({exc})")
        return

    for app in parser.apps:
        if not parser.has_lib_script and not LIB_SCRIPT_SRC.search(text):
            issues.append(
                f"{path}: <lightning-out-application> present but no lightning.out <script> "
                f"found on the host page — the library must load from the host page HTML"
            )
        if "components" not in app or not (app.get("components") or "").strip():
            issues.append(
                f"{path}: <lightning-out-application> is missing a non-empty `components` "
                f"attribute (comma-separated kebab-case LWCs, e.g. 'c-my-lwc')"
            )
        else:
            for comp in (app["components"] or "").split(","):
                comp = comp.strip()
                if comp and not re.fullmatch(r"[a-z][a-z0-9_]*-[a-z0-9-]+", comp):
                    issues.append(
                        f"{path}: component '{comp}' in `components` is not kebab-case "
                        f"(expected e.g. 'c-my-lwc' or 'ns_x-my-lwc')"
                    )
        if "app-id" not in app or not (app.get("app-id") or "").strip():
            issues.append(
                f"{path}: <lightning-out-application> is missing an `app-id` "
                f"(the 18-digit id from the Lightning Out 2.0 App Manager). Apps created "
                f"before Spring '26 don't require it — on any org release — so treat this as "
                f"an advisory unless the app was created in Spring '26 or later"
            )
        fd = app.get("frontdoor-url")
        if fd and SECRET_IN_FRONTDOOR.search(fd) and not _looks_like_placeholder(fd):
            issues.append(
                f"{path}: `frontdoor-url` appears to hard-code a session/token — set it at "
                f"runtime from the UI Bridge API, never in static markup"
            )

    # Textual checks that apply to any HTML (inline scripts, etc.)
    _check_text_patterns(path, text, issues)


def _check_text_patterns(path: Path, text: str, issues: list[str]) -> None:
    if LEGACY_AURA.search(text):
        issues.append(
            f"{path}: legacy Aura Lightning Out (beta) usage detected "
            f"($Lightning.use / lightning:out) — Lightning Out 2.0 uses "
            f"<lightning-out-application> + a frontdoor URL and replaces the beta"
        )
    if LIB_IN_LWC.search(text):
        issues.append(
            f"{path}: attempt to load the lightning.out library via script insertion — "
            f"Lightning Web Security blocks this; include the <script> in the host page HTML"
        )
    if CLIENT_CREDS.search(text):
        issues.append(
            f"{path}: OAuth client credentials flow detected — unsupported for Lightning Out "
            f"2.0 (no user context); use a user token via the UI Bridge exchange"
        )
    if SECRET_IN_FRONTDOOR.search(text) and not _looks_like_placeholder(text):
        # Catch a hard-coded frontdoor/token in inline JS too, de-duped by message.
        msg = (
            f"{path}: a hard-coded frontdoor session/token (sid= or access_token) is present "
            f"— fetch it at runtime and never serve it in static content"
        )
        if msg not in issues:
            issues.append(msg)


def _check_js(path: Path, issues: list[str]) -> None:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        issues.append(f"{path}: could not read ({exc})")
        return
    if NAV_SERVICE.search(text):
        issues.append(
            f"{path}: `lightning/navigation` / NavigationMixin used — page navigation is not "
            f"supported for components embedded via Lightning Out 2.0"
        )
    _check_text_patterns(path, text, issues)


def check(host_dir: Path) -> list[str]:
    issues: list[str] = []
    if not host_dir.exists():
        return [f"Host directory not found: {host_dir}"]

    html_files = sorted(host_dir.rglob("*.html"))
    js_files = sorted(host_dir.rglob("*.js"))
    if not html_files and not js_files:
        return [f"No .html or .js files found under {host_dir} — nothing to check."]

    for path in html_files:
        _check_html(path, issues)
    for path in js_files:
        _check_js(path, issues)
    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Lightning Out 2.0 host-page markup and JS for common embed mistakes.",
    )
    parser.add_argument(
        "--host-dir",
        default=".",
        help="Root of the external host app (scans .html and .js beneath it).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    issues = check(Path(args.host_dir))
    if not issues:
        print("No issues found.")
        return 0
    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
