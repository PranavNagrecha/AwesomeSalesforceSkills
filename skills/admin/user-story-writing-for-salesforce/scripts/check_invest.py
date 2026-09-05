#!/usr/bin/env python3
"""INVEST + structural lint for Salesforce user stories.

Checks a markdown file containing one or more user stories for:
  - Presence of an As-A / I-Want / So-That stem
  - A grounded persona (not "user" / "admin" / "the system")
  - A non-empty So-That clause
  - At least one Given-When-Then acceptance criterion
  - At least one sad-path acceptance criterion
  - Acceptance criteria in Given-When-Then form (not implementation steps)
  - A complexity field with one of S / M / L / XL
  - Story body word count below an INVEST-Small threshold

What counts as a story
----------------------
Only sections whose heading looks like a story are linted:

  * a heading carrying a story id -- `## US-FSALES-018 — Log Field Meeting`
  * a heading that is the word Story -- `## Story: Escalate a premier case`
  * a heading that is the stem itself -- `## As a Tier 1 agent, I want…`

Every other heading is skipped. A story backlog is normally one document with
a Summary, an RTM, a MoSCoW check, Process Observations and a Citations block
around the stories; linting each of those as a story produced one guaranteed
failure per section and made the exit code meaningless. A file with no headings
at all is still treated as a single story, so `check_invest.py one-story.md`
behaves as before.

Stdlib only — no pip dependencies.

Usage:
    python3 check_invest.py path/to/story.md
    python3 check_invest.py --file path/to/story.md
    python3 check_invest.py --manifest-dir artefacts/M5-S03
    python3 check_invest.py path/to/story.md --max-words 250
    python3 check_invest.py path/to/story.md --json

Exit codes:
    0 — every story found passes
    1 — at least one story failed, or no story was found at all
    2 — usage / IO error
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

DEFAULT_MAX_WORDS = 250
ALLOWED_COMPLEXITY = {"S", "M", "L", "XL"}

HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")

# A heading starts a story only when it looks like one. Anything else in the
# document -- Summary, Requirements Traceability Matrix, MoSCoW capacity check,
# Process Observations, Citations, Example N, Anti-Pattern -- is skipped.
STORY_HEADING_PATTERNS = (
    re.compile(r"^#{2,4}\s+.*\bUS-[A-Za-z0-9]", re.IGNORECASE),   # story id
    # "Story: …", "Story - …", "Story 4 …" -- but NOT a section heading such
    # as "Story backlog" or "Story map", which are containers, not stories.
    re.compile(r"^#{2,4}\s+(?:user\s+)?story\b\s*(?:[:#\-\u2013\u2014]|\d)", re.IGNORECASE),
    re.compile(r"^#{2,4}\s+as\s+a\b", re.IGNORECASE),             # the stem itself
)


def is_story_heading(line: str) -> bool:
    for pattern in STORY_HEADING_PATTERNS:
        if pattern.match(line):
            return True
    return False

# Personas that are NOT grounded — must be replaced with a profile / perm set / role.
GENERIC_PERSONAS = {
    "user",
    "users",
    "admin",
    "administrator",
    "the system",
    "system",
    "someone",
    "person",
    "individual",
    "stakeholder",
}

# Sad-path AC signal words. At least one AC should reference one of these patterns.
SAD_PATH_SIGNALS = [
    r"\berror\b",
    r"\bfail(s|ure|ed)?\b",
    r"\bcannot\b",
    r"\bblock(ed|s|ing)?\b",
    r"\bdenied\b",
    r"\breject(ed|s|ion)?\b",
    r"\binvalid\b",
    r"\bvalidation\b",
    r"\btimeout\b",
    r"\bnot\s+(create|save|update|allowed|permitted)",
    r"\bno\s+\w+\s+(is|are|fires|created|sent|made)\b",
    r"\bno\s+(record|task|email|case|callout|reassignment|change|update)\b",
    r"\bremains?\b",
    r"\bunchanged\b",
    r"\bskipped\b",
    r"\bwithout\b",
]

# Implementation-prescription signals. AC text containing these is testing the
# build, not the behavior — INVEST-Negotiable violation.
IMPLEMENTATION_SIGNALS = [
    r"\bRecord-Triggered Flow\b",
    r"\bScreen Flow\b",
    r"\bScheduled Flow\b",
    r"\bApex (class|trigger|method)\b",
    r"\bDecision element\b",
    r"\bUpdate Records element\b",
    r"\bAssignment element\b",
    r"\bGet Records element\b",
    r"\bbatch class\b",
    r"\bqueueable\b",
    r"@future",
]

# UI-styling AC signals — testing pixels not behavior.
UI_STYLING_SIGNALS = [
    r"\b(blue|red|green|yellow)\s+(button|background|color|text)\b",
    r"\b\d+\s*(px|pixels?)\b",
    r"\bfont[- ]size\b",
    r"\bbold\b",
    r"\bitalic\b",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="INVEST + structural lint for Salesforce user stories.",
    )
    parser.add_argument(
        "path",
        nargs="?",
        help="Path to a markdown file containing user stories.",
    )
    parser.add_argument(
        "--file",
        dest="file",
        help="Path to a markdown file containing user stories — an alias of the positional path.",
    )
    parser.add_argument(
        "--manifest-dir",
        dest="manifest_dir",
        help=(
            "Directory to scan recursively for *.md story documents. Files with no "
            "story heading are skipped; it is an error if the whole tree has none."
        ),
    )
    parser.add_argument(
        "--max-words",
        type=int,
        default=DEFAULT_MAX_WORDS,
        help=f"Max words per story body (default: {DEFAULT_MAX_WORDS}).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit findings as JSON instead of human-readable text.",
    )
    return parser.parse_args()


def split_stories(text: str) -> list[tuple[str, str]]:
    """Split a markdown file into (title, body) pairs, one per story section.

    A story section opens at a heading that `is_story_heading` recognises and
    closes at the next heading that is either another story heading or is at
    the same level or shallower. Non-story sections are not returned at all.

    A file with no markdown headings is treated as a single story titled
    '<root>' -- the single-story-file case.
    """
    lines = text.splitlines()

    if not any(HEADING_RE.match(line) for line in lines):
        if any(line.strip() for line in lines):
            return [("<root>", "\n".join(lines))]
        return []

    stories: list[tuple[str, str]] = []
    current_title: str | None = None
    current_level = 0
    current_body: list[str] = []

    for line in lines:
        heading = HEADING_RE.match(line)
        if heading is None:
            if current_title is not None:
                current_body.append(line)
            continue

        level = len(heading.group(1))
        story_heading = is_story_heading(line)

        if current_title is not None and (story_heading or level <= current_level):
            stories.append((current_title, "\n".join(current_body)))
            current_title = None
            current_body = []

        if story_heading:
            current_title = heading.group(2).strip()
            current_level = level
            current_body = []

    if current_title is not None:
        stories.append((current_title, "\n".join(current_body)))

    return stories


def extract_stem(body: str) -> dict[str, str | None]:
    """Pull the As-A / I-Want / So-That clauses from a story body."""
    # Tolerant of bold markers, italics, and line breaks.
    as_a = re.search(
        r"\**As\s+a\**\s+(.+?)(?=,\s*\**I\s+want\b|$|\n)",
        body,
        re.IGNORECASE | re.DOTALL,
    )
    i_want = re.search(
        r"\**I\s+want\**\s+(.+?)(?=,\s*\**So\s+that\b|$|\n)",
        body,
        re.IGNORECASE | re.DOTALL,
    )
    so_that = re.search(
        r"\**So\s+that\**\s+(.+?)(?=\n\n|\.\s*\n|$)",
        body,
        re.IGNORECASE | re.DOTALL,
    )
    return {
        "as_a": _clean(as_a.group(1)) if as_a else None,
        "i_want": _clean(i_want.group(1)) if i_want else None,
        "so_that": _clean(so_that.group(1)) if so_that else None,
    }


def _clean(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip(" ,.;\n*")


def extract_acs(body: str) -> list[str]:
    """Pull acceptance criterion blocks. An AC is any block containing 'Given' near 'Then'."""
    acs: list[str] = []
    # Strategy: look at bullet-list chunks that contain Given/When/Then markers.
    # Split by blank lines, then by bullet, then keep blocks that have all three.
    bullet_blocks = re.split(r"\n\s*-\s+", "\n" + body)
    for block in bullet_blocks:
        block = block.strip()
        if not block:
            continue
        has_given = re.search(r"\bGiven\b", block, re.IGNORECASE)
        has_then = re.search(r"\bThen\b", block, re.IGNORECASE)
        if has_given and has_then:
            acs.append(_clean(block))
    return acs


def extract_complexity(body: str) -> str | None:
    m = re.search(
        r"\**Complexity\**\s*[:\-]\s*\**\s*([A-Za-z]{1,3})\b",
        body,
    )
    if m:
        return m.group(1).upper()
    return None


def lint_story(title: str, body: str, max_words: int) -> list[str]:
    issues: list[str] = []

    stem = extract_stem(body)

    # 1. Stem presence
    if not stem["as_a"]:
        issues.append("Missing 'As a' clause — no persona declared.")
    if not stem["i_want"]:
        issues.append("Missing 'I want' clause — no observable capability declared.")
    if not stem["so_that"]:
        issues.append("Missing 'So that' clause — no business value declared.")

    # 2. Persona grounding
    if stem["as_a"]:
        first_phrase = stem["as_a"].lower().strip()
        # Strip leading articles
        first_phrase = re.sub(r"^(a|an|the)\s+", "", first_phrase)
        for generic in GENERIC_PERSONAS:
            # match whole-word/phrase only
            if re.fullmatch(rf"{re.escape(generic)}\b.*", first_phrase) or first_phrase == generic:
                issues.append(
                    f"Persona '{stem['as_a']}' is generic — must name a Salesforce profile, "
                    f"permission set, or role (not '{generic}')."
                )
                break

    # 3. So-that non-empty / non-vacuous
    if stem["so_that"]:
        vacuous_phrases = [
            "the system works",
            "data is captured",
            "it works",
            "things happen",
            "it functions",
        ]
        st_lower = stem["so_that"].lower()
        for vp in vacuous_phrases:
            if vp in st_lower:
                issues.append(
                    f"'So that' clause is vacuous ('{vp}') — must name a measurable "
                    f"business outcome (revenue, time, error, compliance)."
                )
                break

    # 4. Acceptance criteria
    acs = extract_acs(body)
    if not acs:
        issues.append(
            "No Given-When-Then acceptance criteria found — at least one AC is required."
        )
    else:
        # Each AC should have all three: Given, When, Then
        for i, ac in enumerate(acs, start=1):
            if not re.search(r"\bWhen\b", ac, re.IGNORECASE):
                issues.append(
                    f"AC #{i}: missing 'When' clause — must be in Given-When-Then form."
                )

        # Sad path detection
        has_sad_path = False
        for ac in acs:
            for pattern in SAD_PATH_SIGNALS:
                if re.search(pattern, ac, re.IGNORECASE):
                    has_sad_path = True
                    break
            if has_sad_path:
                break
        if not has_sad_path:
            issues.append(
                "No sad-path AC detected — at least one AC must cover failure / "
                "validation / permission denial / null path."
            )

        # Implementation prescription
        for i, ac in enumerate(acs, start=1):
            for pattern in IMPLEMENTATION_SIGNALS:
                if re.search(pattern, ac, re.IGNORECASE):
                    issues.append(
                        f"AC #{i}: prescribes implementation ('{pattern.strip(chr(92)+'b')}') — "
                        f"violates INVEST-Negotiable. Reshape as observable behavior."
                    )
                    break

        # UI styling tests
        for i, ac in enumerate(acs, start=1):
            for pattern in UI_STYLING_SIGNALS:
                if re.search(pattern, ac, re.IGNORECASE):
                    issues.append(
                        f"AC #{i}: tests UI styling, not behavior. Rewrite to test "
                        f"observable Salesforce outcome."
                    )
                    break

    # 5. Complexity present and valid
    complexity = extract_complexity(body)
    if complexity is None:
        issues.append("Missing 'Complexity' field — must be one of S / M / L / XL.")
    elif complexity not in ALLOWED_COMPLEXITY:
        issues.append(
            f"Complexity '{complexity}' is invalid — must be one of "
            f"{sorted(ALLOWED_COMPLEXITY)}."
        )
    elif complexity == "XL":
        issues.append(
            "Complexity is XL — XL stories are NOT committable. Split using "
            "workflow-step / business-rule / data / persona / happy-vs-sad-path technique."
        )

    # 6. Body word count (INVEST-Small smoke test)
    word_count = len(re.findall(r"\b\w+\b", body))
    if word_count > max_words:
        issues.append(
            f"Story body is {word_count} words (max {max_words}) — likely too large; "
            f"consider splitting."
        )

    # 7. "The system shall…" voice
    if re.search(r"\bthe\s+system\s+(shall|must|should|will)\b", body, re.IGNORECASE):
        issues.append(
            "'The system shall…' voice detected — rewrite as 'As a [persona], I want…'. "
            "User stories are observations of a persona's behavior, not SRS shall-statements."
        )

    return issues


def collect_targets(args: argparse.Namespace) -> tuple[list[Path], int, str]:
    """Resolve the CLI into a list of markdown files, or an error to report."""
    named: list[Path] = []
    for value in (args.path, args.file):
        if value:
            named.append(Path(value))

    if args.manifest_dir:
        directory = Path(args.manifest_dir)
        if not directory.is_dir():
            return [], 2, f"--manifest-dir is not a directory: {directory}"
        found = sorted(p for p in directory.rglob("*.md") if p.is_file())
        if not found and not named:
            return [], 1, f"no *.md file found under --manifest-dir {directory}"
        named.extend(found)

    if not named:
        return [], 2, "provide a path, --file, or --manifest-dir"

    for path in named:
        if not path.exists():
            return [], 2, f"File not found: {path}"
        if not path.is_file():
            return [], 2, f"Not a file: {path}"

    # Preserve order, drop duplicates.
    unique: list[Path] = []
    for path in named:
        if path not in unique:
            unique.append(path)
    return unique, 0, ""


def main() -> int:
    args = parse_args()

    paths, error_code, error_message = collect_targets(args)
    if error_code:
        print(f"ERROR: {error_message}", file=sys.stderr)
        return error_code

    all_findings: list[dict] = []
    skipped: list[Path] = []
    fail_count = 0
    story_count = 0

    for path in paths:
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as e:
            print(f"ERROR: Could not read {path}: {e}", file=sys.stderr)
            return 2

        stories = split_stories(text)
        if not stories:
            skipped.append(path)
            continue

        for title, body in stories:
            issues = lint_story(title, body, args.max_words)
            story_count += 1
            all_findings.append({
                "file": str(path),
                "title": title,
                "passed": not issues,
                "issues": issues,
            })
            if issues:
                fail_count += 1

    if story_count == 0:
        scanned = ", ".join(str(path) for path in paths)
        print(
            f"ERROR: No story section found in {scanned}. A story section is a "
            f"heading carrying a story id (## US-...), a heading that begins "
            f"'Story'/'User Story', or a heading that is the As-a stem itself.",
            file=sys.stderr,
        )
        return 1

    if args.json:
        print(json.dumps({
            "files": [str(path) for path in paths],
            "skipped_files": [str(path) for path in skipped],
            "story_count": story_count,
            "fail_count": fail_count,
            "findings": all_findings,
        }, indent=2))
    else:
        for path in skipped:
            print(f"[SKIP] {path} — no story heading; not linted as a story")
        for finding in all_findings:
            status = "PASS" if finding["passed"] else "FAIL"
            print(f"[{status}] {finding['title']}")
            for issue in finding["issues"]:
                print(f"    - {issue}")
        print()
        print(
            f"Summary: {story_count - fail_count}/{story_count} stories passed "
            f"({fail_count} failed)."
        )

    if fail_count:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
