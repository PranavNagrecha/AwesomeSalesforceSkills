#!/usr/bin/env python3
"""
check_lwc_custom_event_patterns.py

Static checker for the LWC custom-event patterns documented in this skill.
Scans `.js` source files inside Lightning Web Component folders for four
classes of dispatch / listener bugs:

  P0  `dispatchEvent(...)` called with a first argument that is NOT a
      `new CustomEvent(...)` or `new Event(...)` instance (e.g. a string,
      object literal, or legacy `fireEvent` call).

  P0  `new CustomEvent('<name>', ...)` whose name contains an uppercase
      letter, hyphen, underscore, or starts with `on` — silently fails
      to bind to the declarative `on<eventname>` attribute.

  P1  `dispatchEvent(new CustomEvent(...))` inside a nested LWC
      (a component whose folder lives more than one `lwc/` level deep,
      OR which contains another component as a child element) that sets
      `bubbles: true` but does not set `composed: true`. Heuristic:
      any LWC that itself imports another LWC is treated as "potentially
      nested" and warned if it dispatches with bubbles-but-no-composed.

  P1  Handler methods that read `event.target.dataset` or
      `event.target.value` without also referencing `event.currentTarget`
      — likely retargeting bug across shadow boundaries.

stdlib only. Exits 1 on any P0 or P1 finding, 0 otherwise.

Usage:
    python3 check_lwc_custom_event_patterns.py <path> [<path> ...]

Each <path> may be a `.js` file, an LWC component folder, or any directory
(recursively scanned for `.js` files under `lwc/` folders).
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from typing import Iterable, List, Tuple

Finding = Tuple[str, str]  # (severity, message)

# --- Regexes ---------------------------------------------------------------

# Match dispatchEvent(<arg>) and capture <arg> up to a matching close paren
# at the same nesting level. We do this by capturing a flexible body.
DISPATCH_CALL_RE = re.compile(
    r"\.dispatchEvent\s*\(\s*",
)

NEW_CUSTOM_EVENT_RE = re.compile(
    r"new\s+(?:CustomEvent|Event)\s*\(",
)

# Capture event name in `new CustomEvent('name', ...)` or `new Event('name', ...)`
EVENT_NAME_RE = re.compile(
    r"new\s+(?:CustomEvent|Event)\s*\(\s*['\"]([^'\"]+)['\"]",
)

# Bubbles / composed flag detection inside a CustomEvent options block.
# We grab a window of text after `new CustomEvent('name'` and look for the
# flags inside it.
CUSTOMEVENT_BLOCK_RE = re.compile(
    r"new\s+CustomEvent\s*\(\s*['\"]([^'\"]+)['\"]\s*,\s*\{([^}]*)\}",
    re.DOTALL,
)

BUBBLES_TRUE_RE = re.compile(r"\bbubbles\s*:\s*true\b")
COMPOSED_TRUE_RE = re.compile(r"\bcomposed\s*:\s*true\b")

EVENT_TARGET_DATASET_RE = re.compile(r"\bevent\.target\.(?:dataset|value)\b")
EVENT_CURRENTTARGET_RE = re.compile(r"\bevent\.currentTarget\b")

# Detect that this LWC composes / nests another LWC by scanning for
# `from 'c/<other>'` or `from "c/<other>"` imports — a strong signal that
# it sits as a parent of another LWC and may itself be nested.
LWC_IMPORT_RE = re.compile(r"from\s+['\"]c/[a-zA-Z0-9_]+['\"]")

# Legacy fireEvent (pubsub.js) — called out as the deprecated pattern.
FIRE_EVENT_RE = re.compile(r"\bfireEvent\s*\(")

# Valid LWC event-name token: lowercase letters and digits only, no hyphens,
# does not start with `on`. (Numbers in event names are rare but tolerated.)
VALID_EVENT_NAME_RE = re.compile(r"^[a-z][a-z0-9]*$")


# --- Helpers ---------------------------------------------------------------


def iter_js_files(paths: Iterable[str]) -> Iterable[str]:
    for raw in paths:
        if os.path.isfile(raw) and raw.endswith(".js"):
            yield raw
        elif os.path.isdir(raw):
            for root, _dirs, files in os.walk(raw):
                # Skip node_modules and hidden folders.
                if "node_modules" in root.split(os.sep):
                    continue
                for name in files:
                    if name.endswith(".js") and not name.endswith(".test.js"):
                        yield os.path.join(root, name)
        else:
            print(
                f"WARN: skipping non-.js or missing path: {raw}", file=sys.stderr
            )


def slice_after(text: str, idx: int, max_len: int = 400) -> str:
    """Return up to max_len chars starting at idx (for window scans)."""
    return text[idx : idx + max_len]


def find_dispatch_arg_kind(text: str, paren_idx: int) -> str:
    """Given the index of `(` after `dispatchEvent`, peek the first token
    and classify the argument as 'newcustomevent', 'newevent', 'string',
    'object', 'fireevent', or 'other'."""
    # Skip whitespace
    i = paren_idx
    n = len(text)
    while i < n and text[i].isspace():
        i += 1
    if i >= n:
        return "other"
    rest = text[i : i + 60]
    if rest.startswith("new CustomEvent"):
        return "newcustomevent"
    if rest.startswith("new Event"):
        return "newevent"
    if rest.startswith("'") or rest.startswith('"') or rest.startswith("`"):
        return "string"
    if rest.startswith("{"):
        return "object"
    return "other"


# --- Analysis --------------------------------------------------------------


def analyse(path: str) -> List[Finding]:
    findings: List[Finding] = []
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            text = fh.read()
    except OSError as exc:
        return [("P0", f"{path}: could not read file ({exc})")]

    # -- P0: dispatchEvent without new CustomEvent / new Event ----
    # Find all `.dispatchEvent(` occurrences and inspect the first token
    # of the argument.
    for m in DISPATCH_CALL_RE.finditer(text):
        # m.end() points just AFTER the `(`. We want the index of the `(`,
        # which is m.end() - 1, and we want to scan starting at m.end().
        kind = find_dispatch_arg_kind(text, m.end())
        if kind not in ("newcustomevent", "newevent"):
            line_no = text.count("\n", 0, m.start()) + 1
            findings.append(
                (
                    "P0",
                    f"{path}:{line_no}: `dispatchEvent(...)` called with a "
                    f"non-Event argument (kind={kind}). Use "
                    f"`dispatchEvent(new CustomEvent('name', { '{...}' }))` instead.",
                )
            )

    # -- P0: legacy fireEvent (pubsub.js) ----
    for m in FIRE_EVENT_RE.finditer(text):
        line_no = text.count("\n", 0, m.start()) + 1
        findings.append(
            (
                "P0",
                f"{path}:{line_no}: legacy `fireEvent(...)` (pubsub.js) call "
                f"detected. This idiom is deprecated; switch to a CustomEvent "
                f"or Lightning Message Service.",
            )
        )

    # -- P0: invalid event names ----
    for m in EVENT_NAME_RE.finditer(text):
        name = m.group(1)
        line_no = text.count("\n", 0, m.start()) + 1
        if not VALID_EVENT_NAME_RE.match(name):
            findings.append(
                (
                    "P0",
                    f"{path}:{line_no}: event name '{name}' is invalid — must "
                    f"be a single lowercase token (no hyphens, no underscores, "
                    f"no camelCase, no uppercase).",
                )
            )
        elif name.startswith("on") and len(name) > 2:
            findings.append(
                (
                    "P0",
                    f"{path}:{line_no}: event name '{name}' starts with 'on'. "
                    f"The 'on' prefix is added by the listener attribute "
                    f"(`on{name[2:]}={'{handler}'}`), not by the dispatcher. "
                    f"Rename to '{name[2:]}'.",
                )
            )

    # -- P1: bubbles:true without composed:true in a (likely) nested LWC ----
    is_nested_candidate = bool(LWC_IMPORT_RE.search(text))
    # Even non-nested components can dispatch composed events that need to
    # reach Aura — but the strongest heuristic for "this listener is across
    # a shadow boundary" is "this LWC composes another LWC, so it's a
    # parent/grandparent in some tree." For safety we always check the
    # bubbles-without-composed combination, but mark P1 only when nested.
    for m in CUSTOMEVENT_BLOCK_RE.finditer(text):
        name = m.group(1)
        block = m.group(2)
        bubbles_true = bool(BUBBLES_TRUE_RE.search(block))
        composed_true = bool(COMPOSED_TRUE_RE.search(block))
        if bubbles_true and not composed_true:
            line_no = text.count("\n", 0, m.start()) + 1
            severity = "P1" if is_nested_candidate else "P1"
            findings.append(
                (
                    severity,
                    f"{path}:{line_no}: event '{name}' dispatched with "
                    f"`bubbles: true` but no `composed: true`. The event will "
                    f"bubble inside the dispatcher's shadow root only — it "
                    f"cannot reach an Aura host or grandparent LWC. Add "
                    f"`composed: true` if the listener lives across a shadow "
                    f"boundary.",
                )
            )

    # -- P1: event.target.dataset/value without event.currentTarget ----
    if EVENT_TARGET_DATASET_RE.search(text) and not EVENT_CURRENTTARGET_RE.search(text):
        # Report once per file at the first occurrence.
        m = EVENT_TARGET_DATASET_RE.search(text)
        if m is not None:
            line_no = text.count("\n", 0, m.start()) + 1
            findings.append(
                (
                    "P1",
                    f"{path}:{line_no}: handler reads `event.target.dataset` / "
                    f"`event.target.value` but never references "
                    f"`event.currentTarget`. Across shadow boundaries "
                    f"`event.target` is retargeted to the host element — use "
                    f"`event.currentTarget` to read the listener-bound "
                    f"element, or read from `event.detail` instead.",
                )
            )

    return findings


# --- CLI -------------------------------------------------------------------


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Lightning Web Component .js files for custom-event "
            "dispatch / listener anti-patterns."
        ),
    )
    parser.add_argument(
        "paths",
        nargs="+",
        help="One or more .js files or directories to scan.",
    )
    return parser.parse_args(argv)


def main(argv: List[str]) -> int:
    if len(argv) < 2:
        print(__doc__, file=sys.stderr)
        return 2

    args = parse_args(argv[1:])

    files = list(iter_js_files(args.paths))
    if not files:
        print("No .js files found in the supplied paths.", file=sys.stderr)
        return 0

    all_findings: List[Finding] = []
    for path in files:
        all_findings.extend(analyse(path))

    if not all_findings:
        print(
            f"OK - scanned {len(files)} file(s); no custom-event violations found."
        )
        return 0

    p0 = [f for f in all_findings if f[0] == "P0"]
    p1 = [f for f in all_findings if f[0] == "P1"]

    for severity, message in all_findings:
        # P0 -> ERROR, P1 -> WARN, so the substring filter in the
        # repo-level checker validator can confirm an error path exists.
        label = "ERROR" if severity == "P0" else "WARN"
        print(f"[{severity}] {label}: {message}")

    print("")
    print(
        f"Summary: {len(p0)} P0, {len(p1)} P1, scanned {len(files)} file(s)."
    )

    if p0 or p1:
        sys.exit(1)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
