#!/usr/bin/env python3
"""Check Lightning Web Component source for communication anti-patterns."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


PUBSUB_RE = re.compile(r"""['"]c/pubsub['"]""")
DOCUMENT_COMPONENT_RE = re.compile(r"""document\.querySelector(?:All)?\(\s*['"][^'"]*c-[^'"]*['"]""")
SHADOW_ROOT_COMPONENT_RE = re.compile(r"""\.shadowRoot\b""")
CUSTOM_EVENT_RE = re.compile(r"""new\s+CustomEvent\(\s*['"]([^'"]+)['"]""")
SUBSCRIBE_RE = re.compile(r"""\bsubscribe\s*\(""")
UNSUBSCRIBE_RE = re.compile(r"""\bunsubscribe\s*\(""")
MESSAGE_CONTEXT_RE = re.compile(r"""MessageContext|createMessageContext\s*\(""")
VALID_EVENT_NAME_RE = re.compile(r"^[a-z][a-z0-9_]*$")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Lightning Web Components for communication-pattern issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def line_number(text: str, index: int) -> int:
    return text.count("\n", 0, index) + 1


def check_component_communication(manifest_dir: Path) -> list[str]:
    issues: list[str] = []

    if not manifest_dir.exists():
        return [f"Manifest directory not found: {manifest_dir}"]

    for path in sorted(p for p in manifest_dir.rglob("*") if p.suffix in {".js", ".ts"}):
        text = path.read_text(encoding="utf-8", errors="ignore")

        for match in PUBSUB_RE.finditer(text):
            issues.append(
                f"{path}:{line_number(text, match.start())}: imports legacy `c/pubsub`; review whether custom events or Lightning Message Service is the supported contract."
            )

        for match in DOCUMENT_COMPONENT_RE.finditer(text):
            issues.append(
                f"{path}:{line_number(text, match.start())}: queries a component with `document.querySelector`; review whether communication is bypassing ownership boundaries."
            )

        for match in SHADOW_ROOT_COMPONENT_RE.finditer(text):
            issues.append(
                f"{path}:{line_number(text, match.start())}: reaches into `shadowRoot`; review whether a public child API or event contract should replace DOM coupling."
            )

        for match in CUSTOM_EVENT_RE.finditer(text):
            event_name = match.group(1)
            if event_name.startswith("on") or not VALID_EVENT_NAME_RE.match(event_name):
                issues.append(
                    f"{path}:{line_number(text, match.start())}: custom event `{event_name}` does not follow a stable lowercase listener-friendly naming convention."
                )

        if SUBSCRIBE_RE.search(text):
            if not MESSAGE_CONTEXT_RE.search(text):
                issues.append(
                    f"{path}: uses `subscribe()` without an obvious `MessageContext` or `createMessageContext()` source."
                )
            if not UNSUBSCRIBE_RE.search(text):
                issues.append(
                    f"{path}: subscribes to Lightning Message Service without an `unsubscribe()` call; review lifecycle cleanup."
                )

    return issues


def main() -> int:
    args = parse_args()
    issues = check_component_communication(Path(args.manifest_dir))

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
