#!/usr/bin/env python3
"""INVEST + structural lint for Salesforce user stories.

Checks a markdown file containing one or more user stories for:
  - Presence of an As-A / I-Want / So-That stem
  - A grounded persona (not "user" / "admin" / "the system")
  - A non-empty So-That clause
  - At least one Given-When-Then acceptance criterion (the story's observable outcome)
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

Where one acceptance criterion ends
------------------------------------
A bullet's own Given/When/Then paragraph ends at the next blank line. The
canonical story shape (`templates/story-shape.md`) always has a Complexity
line, a Notes line, and a fenced handoff-JSON block sitting right after the
acceptance criteria in the same section — with no story heading between them
to end the story early. Without this rule, the last acceptance criterion's
extracted text would run on and swallow that trailing Complexity / Notes /
JSON content, which routinely contains build-agent names and skill paths
("flow-builder", "apex/queueable-callouts") that look like implementation
prescription and produce false failures on well-formed stories.

Severity — ERROR vs WARN
-------------------------
Findings are either ERROR (a structural INVEST violation: no persona, no
observable outcome / no acceptance criteria, an unresolved complexity, a
"the system shall" rewrite) or WARN (a heuristic pattern match that is a
strong hint but not conclusive on its own: a vacuous So-That phrase, a
missing sad path, a suspected implementation/UI-styling phrase inside an AC,
or an over-long body). By default only ERROR findings fail the run; pass
`--strict` to fail on WARN findings too.

Stdlib only — no pip dependencies.

Usage:
    python3 check_invest.py path/to/story.md
    python3 check_invest.py --file path/to/story.md
    python3 check_invest.py --manifest-dir artefacts/M5-S03
    python3 check_invest.py path/to/story.md --max-words 250
    python3 check_invest.py path/to/story.md --strict
    python3 check_invest.py path/to/story.md --json

Exit codes:
    0 — every story passed (no ERROR findings; under --strict, no WARN
        findings either), including the case where there was nothing to
        check (an empty file, or a --manifest-dir with no story content —
        a WARN is printed, but an empty target is not a failure)
    1 — at least one ERROR finding (or, under --strict, any finding), OR
        the input itself is missing/unusable (no path given, a path that
        does not exist, a --manifest-dir that is not a directory, or a
        named path that is not a file)
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

DEFAULT_MAX_WORDS = 250
ALLOWED_COMPLEXITY = {"S", "M", "L", "XL"}
ERROR = "ERROR"
WARN = "WARN"

HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")

# A heading starts a story only when it looks like one. Anything else in the
# document -- Summary, Requirements Traceability Matrix, MoSCoW capacity check,
# Process Observations, Citations, Example N, Anti-Pattern -- is skipped.
STORY_HEADING_PATTERNS = (
    re.compile(r"^#{2,4}\s+.*\bUS-[A-Za-z0-9]", re.IGNORECASE),   # story id
    # "Story: …", "Story - …", "Story 4 …" -- but NOT a section heading such
    # as "Story backlog" or "Story map", which are containers, not stories.
    re.compile(r"^#{2,4}\s+(?:user\s+)?story\b\s*(?:[:#\-–—]|\d)", re.IGNORECASE),
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
            "story heading are skipped; a tree with none found is reported as empty "
            "(WARN, exit 0), not as a failure."
        ),
    )
    parser.add_argument(
        "--max-words",
        type=int,
        default=DEFAULT_MAX_WORDS,
        help=f"Max words per story body (default: {DEFAULT_MAX_WORDS}).",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Also fail (exit 1) on WARN-level findings, not just ERROR-level ones.",
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
    """Pull acceptance criterion blocks. An AC is any bullet's own paragraph
    containing 'Given' near 'Then'.

    Strategy: split on bullet markers as before, but then cut each resulting
    block at the first blank line. A markdown bullet's paragraph ends at the
    next blank line whether or not another bullet follows it — without this
    cut, the last acceptance criterion in a section absorbs everything that
    comes after it in the same story (Complexity, Notes, the handoff JSON
    block), which routinely contains agent/skill names that look like
    implementation prescription. See the module docstring.
    """
    acs: list[str] = []
    bullet_blocks = re.split(r"\n\s*-\s+", "\n" + body)
    for block in bullet_blocks:
        block = block.strip()
        if not block:
            continue
        block = re.split(r"\n\s*\n", block, maxsplit=1)[0].strip()
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


def lint_story(title: str, body: str, max_words: int) -> list[tuple[str, str]]:
    """Return a list of (severity, message) findings for one story body."""
    issues: list[tuple[str, str]] = []

    stem = extract_stem(body)

    # 1. Stem presence — no persona / no capability / no business value at all.
    if not stem["as_a"]:
        issues.append((ERROR, "Missing 'As a' clause — no persona declared."))
    if not stem["i_want"]:
        issues.append((ERROR, "Missing 'I want' clause — no observable capability declared."))
    if not stem["so_that"]:
        issues.append((ERROR, "Missing 'So that' clause — no business value declared."))

    # 2. Persona grounding
    if stem["as_a"]:
        first_phrase = stem["as_a"].lower().strip()
        # Strip leading articles
        first_phrase = re.sub(r"^(a|an|the)\s+", "", first_phrase)
        for generic in GENERIC_PERSONAS:
            # match whole-word/phrase only
            if re.fullmatch(rf"{re.escape(generic)}\b.*", first_phrase) or first_phrase == generic:
                issues.append((
                    ERROR,
                    f"Persona '{stem['as_a']}' is generic — must name a Salesforce profile, "
                    f"permission set, or role (not '{generic}').",
                ))
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
                issues.append((
                    WARN,
                    f"'So that' clause is vacuous ('{vp}') — must name a measurable "
                    f"business outcome (revenue, time, error, compliance).",
                ))
                break

    # 4. Acceptance criteria — this is also the "no observable outcome" check:
    # a story with zero Given-When-Then blocks has stated no observable outcome.
    acs = extract_acs(body)
    if not acs:
        issues.append((
            ERROR,
            "No Given-When-Then acceptance criteria found — no observable outcome is "
            "stated; at least one AC is required.",
        ))
    else:
        # Each AC should have all three: Given, When, Then
        for i, ac in enumerate(acs, start=1):
            if not re.search(r"\bWhen\b", ac, re.IGNORECASE):
                issues.append((
                    ERROR,
                    f"AC #{i}: missing 'When' clause — must be in Given-When-Then form.",
                ))

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
            issues.append((
                WARN,
                "No sad-path AC detected — at least one AC should cover failure / "
                "validation / permission denial / null path.",
            ))

        # Implementation prescription
        for i, ac in enumerate(acs, start=1):
            for pattern in IMPLEMENTATION_SIGNALS:
                if re.search(pattern, ac, re.IGNORECASE):
                    issues.append((
                        WARN,
                        f"AC #{i}: looks like it prescribes implementation ('{pattern.strip(chr(92)+'b')}') — "
                        f"possible INVEST-Negotiable violation. Reshape as observable behavior if so.",
                    ))
                    break

        # UI styling tests
        for i, ac in enumerate(acs, start=1):
            for pattern in UI_STYLING_SIGNALS:
                if re.search(pattern, ac, re.IGNORECASE):
                    issues.append((
                        WARN,
                        f"AC #{i}: looks like it tests UI styling, not behavior. Consider rewriting "
                        f"to test an observable Salesforce outcome.",
                    ))
                    break

    # 5. Complexity present and valid
    complexity = extract_complexity(body)
    if complexity is None:
        issues.append((ERROR, "Missing 'Complexity' field — must be one of S / M / L / XL."))
    elif complexity not in ALLOWED_COMPLEXITY:
        issues.append((
            ERROR,
            f"Complexity '{complexity}' is invalid — must be one of {sorted(ALLOWED_COMPLEXITY)}.",
        ))
    elif complexity == "XL":
        issues.append((
            ERROR,
            "Complexity is XL — XL stories are NOT committable. Split using "
            "workflow-step / business-rule / data / persona / happy-vs-sad-path technique.",
        ))

    # 6. Body word count (INVEST-Small smoke test) — heuristic, WARN only.
    word_count = len(re.findall(r"\b\w+\b", body))
    if word_count > max_words:
        issues.append((
            WARN,
            f"Story body is {word_count} words (max {max_words}) — likely too large; "
            f"consider splitting.",
        ))

    # 7. "The system shall…" voice — deterministic, ERROR.
    if re.search(r"\bthe\s+system\s+(shall|must|should|will)\b", body, re.IGNORECASE):
        issues.append((
            ERROR,
            "'The system shall…' voice detected — rewrite as 'As a [persona], I want…'. "
            "User stories are observations of a persona's behavior, not SRS shall-statements.",
        ))

    return issues


def collect_targets(args: argparse.Namespace) -> tuple[list[Path], bool, str]:
    """Resolve the CLI into a list of markdown files, or a fatal usage error.

    Returns (paths, fatal, message). `fatal` means the input itself is
    missing or unusable (exit 1) — distinct from an input that resolves to
    zero stories, which is reported later as empty (WARN, exit 0).
    """
    named: list[Path] = []
    for value in (args.path, args.file):
        if value:
            named.append(Path(value))

    manifest_found: list[Path] = []
    if args.manifest_dir:
        directory = Path(args.manifest_dir)
        if not directory.is_dir():
            return [], True, f"--manifest-dir is not a directory: {directory}"
        manifest_found = sorted(p for p in directory.rglob("*.md") if p.is_file())
        named.extend(manifest_found)

    if not named:
        if args.manifest_dir:
            # A real, empty directory — nothing to check, not a usage error.
            return [], False, ""
        return [], True, "provide a path, --file, or --manifest-dir"

    for path in named:
        if not path.exists():
            return [], True, f"File not found: {path}"
        if not path.is_file():
            return [], True, f"Not a file: {path}"

    # Preserve order, drop duplicates.
    unique: list[Path] = []
    for path in named:
        if path not in unique:
            unique.append(path)
    return unique, False, ""


def main() -> int:
    args = parse_args()

    paths, fatal, message = collect_targets(args)
    if fatal:
        print(f"ERROR: {message}", file=sys.stderr)
        return 1

    if not paths:
        print(f"WARN: no *.md file found under --manifest-dir {args.manifest_dir}; nothing to lint.")
        return 0

    all_findings: list[dict] = []
    skipped: list[Path] = []
    error_count = 0
    warn_count = 0
    story_count = 0

    for path in paths:
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as e:
            print(f"ERROR: Could not read {path}: {e}", file=sys.stderr)
            return 1

        stories = split_stories(text)
        if not stories:
            skipped.append(path)
            continue

        for title, body in stories:
            issues = lint_story(title, body, args.max_words)
            story_count += 1
            story_errors = sum(1 for sev, _ in issues if sev == ERROR)
            story_warns = sum(1 for sev, _ in issues if sev == WARN)
            error_count += story_errors
            warn_count += story_warns
            all_findings.append({
                "file": str(path),
                "title": title,
                "passed": story_errors == 0,
                "issues": [{"severity": sev, "message": msg} for sev, msg in issues],
            })

    if story_count == 0:
        scanned = ", ".join(str(path) for path in paths) or "(no files)"
        print(f"WARN: no story section found in {scanned}; nothing to lint.")
        return 0

    if args.json:
        print(json.dumps({
            "files": [str(path) for path in paths],
            "skipped_files": [str(path) for path in skipped],
            "story_count": story_count,
            "error_count": error_count,
            "warn_count": warn_count,
            "strict": args.strict,
            "findings": all_findings,
        }, indent=2))
    else:
        for path in skipped:
            print(f"[SKIP] {path} — no story heading; not linted as a story")
        for finding in all_findings:
            status = "PASS" if finding["passed"] else "FAIL"
            print(f"[{status}] {finding['title']}")
            for issue in finding["issues"]:
                print(f"    - {issue['severity']}: {issue['message']}")
        print()
        fail_count = sum(1 for f in all_findings if not f["passed"])
        print(
            f"Summary: {story_count - fail_count}/{story_count} stories passed "
            f"({error_count} ERROR, {warn_count} WARN)."
        )
        if args.strict and warn_count:
            print("--strict: WARN findings also fail this run.")

    if error_count or (args.strict and warn_count):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
