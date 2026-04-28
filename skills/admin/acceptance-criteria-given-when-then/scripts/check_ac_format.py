#!/usr/bin/env python3
"""Lint a markdown user-story file for Given/When/Then acceptance-criteria quality.

Flags:
- AC blocks missing Given OR When OR Then keywords
- Happy-path Scenarios missing a paired negative-path Scenario
- UI-coupled phrases ("click", "button", "tab", named UI chrome)
- Missing permission preconditions when the story tags a sharing-relevant object
- Trigger / flow / validation behavior with no bulk-volume Scenario
- Async / callout outcomes asserted synchronously (no "eventually" clause)
- Vague validation-error assertions ("fails with a validation error" without exact message)

Stdlib-only. No pip dependencies.

Usage:
    python3 check_ac_format.py <story.md>
    python3 check_ac_format.py --file <story.md>
    python3 check_ac_format.py --help

Exit codes:
    0 — no issues
    1 — one or more issues found
    2 — usage error / file not found
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Iterable

# Sharing-relevant objects — if the story mentions any of these, AC must
# include a permission/PSG/profile precondition.
SHARING_RELEVANT_OBJECTS = {
    "account", "contact", "opportunity", "case", "lead", "campaign",
    "asset", "contract", "order", "quote", "task", "event",
    "knowledge", "service appointment", "work order",
}

# Phrases that indicate the AC is bound to a trigger / flow / validation rule
# and therefore must include a bulk-volume Scenario.
TRIGGER_BOUND_PHRASES = [
    r"\btrigger\b",
    r"\bflow\b",
    r"\brecord[- ]triggered\b",
    r"\bvalidation rule\b",
    r"\bbatch\b",
    r"\bbulk api\b",
    r"\bdata loader\b",
]

# Phrases that signal an async / callout boundary — requires "eventually" clause.
ASYNC_BOUND_PHRASES = [
    r"\bcallout\b",
    r"\bnamed credential\b",
    r"\bplatform event\b",
    r"\bqueueable\b",
    r"\bschedulable\b",
    r"\bfuture method\b",
    r"\bexternal system\b",
    r"\b(post|put|get|delete) to\b",
]

# UI-chrome phrases that should not appear in AC.
UI_COUPLED_PATTERNS = [
    r"\bclick(s|ed|ing)? (the )?(save|cancel|edit|new|delete|submit|next|continue|back) (button|link)\b",
    r"\b(navigate|go|click) (to )?the .* (tab|page|menu)\b",
    r"\b(red|green|yellow|blue) (color|background|text|highlight)\b",
    r"\btoast (message|appears|popup)\b",
    r"\bmodal (opens|appears|popup)\b",
    r"\bscroll(s|ed|ing) (down|up)\b",
    r"\bhover(s|ed|ing)? over\b",
    r"\bbutton labeled\b",
    r"\bsays the text\b",
]

# Permission-precondition signals — at least one must be present in the AC
# block when a sharing-relevant object is tagged.
PERMISSION_SIGNALS = [
    r"permission set",
    r"\bpsg\b",
    r"profile\s+\"",
    r"\bowd\b",
    r"\bowner\b",
    r"\brole hierarchy\b",
    r"\bsharing rule\b",
    r"opportunity team",
    r"account team",
    r"\bqueue\b",
]

# Threshold to qualify as a bulk Scenario (one trigger batch).
BULK_THRESHOLD = 200

GHERKIN_KEYWORDS = ("given", "when", "then")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Lint a markdown user-story file for Given/When/Then AC quality.",
    )
    parser.add_argument(
        "file",
        nargs="?",
        help="Path to the markdown story file to lint.",
    )
    parser.add_argument(
        "--file",
        dest="file_flag",
        help="Alternate way to pass the file path.",
    )
    return parser.parse_args()


def extract_scenarios(content: str) -> list[tuple[int, str, list[str]]]:
    """Return a list of (start_line_index, scenario_header, body_lines) tuples.

    A Scenario starts at a line beginning with `Scenario:` or `Scenario Outline:`
    and ends at the next Scenario header, the next H2/H3 heading, or end of file.
    """
    lines = content.splitlines()
    scenarios: list[tuple[int, str, list[str]]] = []
    current_start: int | None = None
    current_header: str = ""
    current_body: list[str] = []

    def flush(end_idx: int) -> None:
        nonlocal current_start, current_header, current_body
        if current_start is not None:
            scenarios.append((current_start, current_header, current_body[:]))
        current_start = None
        current_header = ""
        current_body = []

    for i, line in enumerate(lines):
        stripped = line.strip()
        # Boundary detectors
        is_scenario_header = bool(re.match(r"^\s*Scenario(\s+Outline)?\s*:", line))
        is_top_section = bool(re.match(r"^#{1,3}\s", line)) and not stripped.lower().startswith(
            ("# acceptance criteria", "## acceptance criteria", "### acceptance criteria")
        )

        if is_scenario_header:
            flush(i)
            current_start = i
            current_header = stripped
            current_body = []
        elif current_start is not None:
            if is_top_section:
                flush(i)
            else:
                current_body.append(line)

    flush(len(lines))
    return scenarios


def check_gherkin_completeness(scenarios: list[tuple[int, str, list[str]]]) -> list[str]:
    issues: list[str] = []
    for line_idx, header, body in scenarios:
        body_text = "\n".join(body).lower()
        missing: list[str] = []
        for kw in GHERKIN_KEYWORDS:
            # Allow either "Given" / "And" implicitly, but require Given explicitly.
            if not re.search(rf"\b{kw}\b", body_text):
                missing.append(kw.capitalize())
        if missing:
            issues.append(
                f"Line {line_idx + 1}: Scenario {header!r} is missing required clause(s): {', '.join(missing)}"
            )
    return issues


def check_negative_path_pairing(scenarios: list[tuple[int, str, list[str]]]) -> list[str]:
    """Heuristic: count happy-path vs deny-case Then assertions.

    Happy markers: 'succeeds', 'is created', 'is visible', 'is saved', 'is updated',
                   'returns', 'is sent', 'is enabled'.
    Deny markers:  'fails', 'is denied', 'is hidden', 'is not created',
                   'is rejected', 'is blocked', 'error', 'cannot'.
    """
    happy_re = re.compile(
        r"\bthen\b.*?\b(succeeds?|is created|is visible|is saved|is updated|returns?|is sent|is enabled|is granted)\b",
        re.IGNORECASE | re.DOTALL,
    )
    deny_re = re.compile(
        r"\bthen\b.*?\b(fails?|is denied|is hidden|is not created|is rejected|is blocked|access is denied|insufficient privileges|cannot|error)\b",
        re.IGNORECASE | re.DOTALL,
    )
    happy_count = 0
    deny_count = 0
    for _, _, body in scenarios:
        body_text = "\n".join(body)
        if happy_re.search(body_text):
            happy_count += 1
        if deny_re.search(body_text):
            deny_count += 1

    issues: list[str] = []
    if happy_count > 0 and deny_count == 0:
        issues.append(
            f"AC block has {happy_count} happy-path Scenario(s) but 0 negative-path Scenarios. "
            "Every 'should' needs a paired 'should not'."
        )
    elif happy_count >= 3 * max(deny_count, 1):
        issues.append(
            f"AC block is happy-path-biased: {happy_count} success Scenarios vs {deny_count} deny-case Scenarios. "
            "Add paired deny-case Scenarios for permission boundaries and validation failures."
        )
    return issues


def check_ui_coupled_language(content: str) -> list[str]:
    issues: list[str] = []
    lines = content.splitlines()
    for i, line in enumerate(lines):
        for pattern in UI_COUPLED_PATTERNS:
            if re.search(pattern, line, re.IGNORECASE):
                issues.append(
                    f"Line {i + 1}: UI-coupled phrasing detected — describe behavior, not UI chrome: {line.strip()[:100]!r}"
                )
                break
    return issues


def check_permission_precondition(content: str) -> list[str]:
    """If the story tags a sharing-relevant object, the AC must mention permission context."""
    lower = content.lower()

    tagged_objects = [obj for obj in SHARING_RELEVANT_OBJECTS if re.search(rf"\b{re.escape(obj)}\b", lower)]
    if not tagged_objects:
        return []

    has_permission_signal = any(re.search(pat, lower) for pat in PERMISSION_SIGNALS)
    if has_permission_signal:
        return []

    return [
        f"Story tags sharing-relevant object(s) ({', '.join(sorted(set(tagged_objects))[:5])}) "
        "but no permission/PSG/profile/OWD/owner precondition is declared in the AC. "
        "Add a Background block naming the running user(s) and PSG."
    ]


def check_bulk_path(content: str) -> list[str]:
    """Trigger / flow / validation behavior must include a Scenario with volume >= 200."""
    lower = content.lower()
    is_trigger_bound = any(re.search(pat, lower) for pat in TRIGGER_BOUND_PHRASES)
    if not is_trigger_bound:
        return []

    # Look for any number >= 200 inside the file.
    has_bulk_count = False
    for m in re.finditer(r"\b(\d{3,})\b", content):
        try:
            if int(m.group(1)) >= BULK_THRESHOLD:
                has_bulk_count = True
                break
        except ValueError:
            continue

    if has_bulk_count:
        return []

    return [
        f"AC mentions trigger / flow / validation rule / bulk behavior but no Scenario "
        f"contains a record-count >= {BULK_THRESHOLD}. "
        "Add a bulk Scenario asserting governor-limit safety at one trigger batch."
    ]


def check_async_eventually(content: str) -> list[str]:
    """Async / callout boundaries must use 'eventually within N' phrasing in the Then."""
    lower = content.lower()
    is_async_bound = any(re.search(pat, lower) for pat in ASYNC_BOUND_PHRASES)
    if not is_async_bound:
        return []

    if re.search(r"\beventually\s+within\b", lower):
        return []

    return [
        "AC mentions an async / callout / Platform Event / Queueable boundary but no Then "
        "clause uses 'eventually within N seconds'. Synchronous Then on async behavior produces "
        "flaky tests."
    ]


def check_vague_validation(content: str) -> list[str]:
    """A 'fails with a validation error' clause without an exact message string is vague."""
    issues: list[str] = []
    lines = content.splitlines()
    for i, line in enumerate(lines):
        lower = line.lower()
        if not re.search(r"\bthen\b.*\b(fails?|error)\b", lower):
            continue
        # Check this line and the next 4 lines (And ...) for a quoted message or a TBD marker.
        block = "\n".join(lines[i : i + 5])
        has_quoted_msg = bool(re.search(r"\".+?\"", block))
        has_tbd = "tbd" in block.lower() or "# todo" in block.lower()
        if not has_quoted_msg and not has_tbd:
            issues.append(
                f"Line {i + 1}: Then-fails clause has no exact error message in quotes "
                f"and no '# TBD' marker: {line.strip()[:100]!r}"
            )
    return issues


def has_acceptance_criteria(content: str) -> bool:
    """Return True if the file appears to contain an AC block."""
    lower = content.lower()
    if "acceptance criteria" in lower:
        return True
    if re.search(r"\bscenario\s*:", lower) or re.search(r"\bscenario outline\s*:", lower):
        return True
    if any(re.search(rf"\b{kw}\b", lower) for kw in GHERKIN_KEYWORDS):
        return True
    return False


def lint(path: Path) -> list[str]:
    if not path.exists():
        return [f"File not found: {path}"]
    if not path.is_file():
        return [f"Not a file: {path}"]

    try:
        content = path.read_text(encoding="utf-8")
    except OSError as exc:
        return [f"Could not read {path}: {exc}"]

    if not has_acceptance_criteria(content):
        return [
            f"{path} does not contain an AC block, Gherkin keywords, or a 'Scenario:' heading. "
            "Nothing to lint."
        ]

    issues: list[str] = []
    scenarios = extract_scenarios(content)

    if scenarios:
        issues.extend(check_gherkin_completeness(scenarios))
        issues.extend(check_negative_path_pairing(scenarios))
    else:
        issues.append(
            "No 'Scenario:' or 'Scenario Outline:' headers detected. "
            "Use the Given/When/Then format from templates/ac-template.md."
        )

    issues.extend(check_ui_coupled_language(content))
    issues.extend(check_permission_precondition(content))
    issues.extend(check_bulk_path(content))
    issues.extend(check_async_eventually(content))
    issues.extend(check_vague_validation(content))

    return issues


def main() -> int:
    args = parse_args()
    target = args.file or args.file_flag
    if not target:
        print("Usage: check_ac_format.py <story.md>", file=sys.stderr)
        return 2

    path = Path(target)
    issues = lint(path)

    if not issues:
        print(f"OK: {path} — no AC-format issues detected.")
        return 0

    print(f"Found {len(issues)} issue(s) in {path}:", file=sys.stderr)
    for issue in issues:
        print(f"  - {issue}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
