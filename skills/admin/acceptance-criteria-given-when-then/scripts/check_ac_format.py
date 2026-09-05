#!/usr/bin/env python3
"""Lint Salesforce acceptance criteria — as a criteria record, or as Gherkin inside a story.

Two input shapes, one linter:

**Criteria record** (the artefact this skill produces; see ``references/worked-examples.md`` § 5)
    A YAML file, or a fenced ``yaml`` block inside Markdown, with a top-level
    ``acceptance_criteria:`` list. Each row carries the criterion *and* everything needed to prove
    it: ``ac_id``, ``req_id``, ``persona``, ``test_type``, ``artefact``, ``given`` / ``when`` /
    ``then``, and optionally ``sandbox``, ``seed_data``, ``proof``, ``negative``, ``story_id``.

**Criteria table** (``references/worked-examples.md`` § 7)
    A Markdown table whose header names Given, When, Then plus the id/persona/test-type/artefact
    columns. Same checks, for story tools that hold a table but not YAML.

**Gherkin story** (the original mode, unchanged)
    A Markdown file with ``Scenario:`` / ``Scenario Outline:`` headers.

Record and table checks (ERROR unless marked WARN):

  1. Every criterion has ``given``, ``when``, ``then``, a ``req_id``, a ``persona``, a
     ``test_type`` and an ``artefact``.
  2. ``ac_id`` is present, shaped ``AC-...``, and unique within the document.
  3. ``req_id`` matches ``REQ-<digits>`` (an optional project prefix such as ``ACME-`` is allowed),
     per ``admin/requirements-traceability-matrix`` § ID Conventions.
  4. ``test_type`` is one of apex / flow / manual.
  5. ``then`` names an outcome, not an implementation — no Process Builder, Apex trigger, handler
     class, record-triggered flow or rule engine named in the Then clause.
  6. No ambiguous adjective ("quickly", "appropriate", "correctly", …) anywhere in given/when/then.
  7. Every rule-type requirement — one whose criteria name an assignment, auto-response,
     escalation, duplicate, matching, validation rule or entitlement process — has at least one
     criterion marked ``negative: true``. Rule engines all define a fall-through; the criteria are
     where it gets named.
  8. An ``artefact`` that looks like a repo path resolves against the repo root; one that looks like
     org metadata is format-checked only (WARN when it has no recognisable suffix).
  9. WARN: no ``proof`` (the query, checker or observation that makes the Then falsifiable);
     a ``persona`` that names no permission construct; a ``test_type: apex`` criterion whose Then
     depends on elapsed business time.
 10. A record whose rows are all still bracketed placeholders is reported as an unfilled template
     (one WARN) rather than as a wall of errors.

Gherkin checks (unchanged): missing Given/When/Then, happy-path bias, UI-coupled phrasing, missing
permission precondition on a sharing-relevant object, trigger/flow/validation behaviour with no bulk
Scenario, async outcome asserted synchronously, and a "Then … fails" clause with no exact message.

Stdlib only. The YAML reader understands the restricted block subset the worked examples use:
mappings, sequences of mappings, inline ``[a, b]`` lists, quoted or bare scalars, ``#`` comments.
Multi-line scalars (``|``, ``>``), anchors and flow mappings are rejected with a parse error.

Usage:
    python3 check_ac_format.py --file acceptance-criteria.yaml
    python3 check_ac_format.py --file docs/stories/US-CI-01.md
    python3 check_ac_format.py --manifest-dir ./docs/stories/
    python3 check_ac_format.py story.md          # positional form, still supported

Exit codes:
    0 — no errors (warnings may still print)
    1 — one or more errors
    2 — usage error / nothing to lint
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# --------------------------------------------------------------------------- shared vocabulary

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

# --------------------------------------------------------------------------- record vocabulary

REQUIRED_FIELDS = ("given", "when", "then", "req_id", "persona", "test_type", "artefact")

AC_ID_PATTERN = re.compile(r"^AC[-_][A-Za-z0-9][A-Za-z0-9._-]*$", re.IGNORECASE)
# REQ-001, REQ-0012, ACME-REQ-001 — a project prefix is allowed, per the RTM's ID Conventions.
REQ_ID_PATTERN = re.compile(r"^(?:[A-Z][A-Z0-9]{1,9}-)?REQ-\d{2,}$", re.IGNORECASE)

TEST_TYPES = ("apex", "flow", "manual")

# A Then clause describes what is observable, never which tool produced it.
IMPLEMENTATION_IN_THEN = [
    (r"\bprocess builder\b", "names Process Builder"),
    (r"\bworkflow rule\b", "names a workflow rule"),
    (r"\bapex (trigger|class|method)\b", "names Apex"),
    (r"\bthe trigger\b", "names the trigger"),
    (r"\brecord[- ]triggered flow\b", "names a record-triggered flow"),
    (r"\bthe (flow|subflow) (runs|fires|executes|is invoked)\b", "names the Flow that runs"),
    (r"\b(queueable|schedulable|batchable|@future)\b", "names the async mechanism"),
    (r"\b\w+(handler|controller|service|selector)\b", "names an Apex class role"),
    (r"\.cls\b", "names an Apex file"),
    (r"\bassignment rule (fires|runs|executes)\b", "names the rule engine rather than the outcome"),
    (r"\b(validation|escalation|duplicate|auto-response) rule (fires|runs|executes)\b",
     "names the rule engine rather than the outcome"),
    (r"\binvocable\b", "names an invocable action"),
    (r"\blightning web component\b", "names the component"),
]

AMBIGUOUS_WORDS = [
    "quickly", "fast enough", "slow", "appropriate", "appropriately", "properly", "correctly",
    "as expected", "as appropriate", "reasonable", "reasonably", "user-friendly", "user friendly",
    "intuitive", "seamless", "seamlessly", "robust", "efficiently", "sufficient", "adequate",
    "timely", "soon", "acceptable", "and so on", "etc.", "various", "some records",
]

# A requirement whose criteria touch one of these is criteria-driven: it has an evaluation order and
# a fall-through, so it needs a criterion for the no-match case.
RULE_TYPE_MARKERS = [
    (r"assignmentrules?\b", "assignment rule"),
    (r"autoresponserules?\b", "auto-response rule"),
    (r"escalationrules?\b", "escalation rule"),
    (r"validationrules?\b", "validation rule"),
    (r"duplicaterules?\b", "duplicate rule"),
    (r"matchingrules?\b", "matching rule"),
    (r"entitlementprocess(es)?\b", "entitlement process"),
    (r"\bassignment rule\b", "assignment rule"),
    (r"\bauto[- ]response rule\b", "auto-response rule"),
    (r"\bescalation rule\b", "escalation rule"),
    (r"\bvalidation rule\b", "validation rule"),
    (r"\bduplicate rule\b", "duplicate rule"),
    (r"\bmatching rule\b", "matching rule"),
    (r"\bentitlement process\b", "entitlement process"),
]

# Repo paths the artefact column may legitimately point at.
REPO_PATH_PREFIXES = ("skills/", "standards/", "templates/", "agents/", "evals/", "knowledge/")

METADATA_SUFFIXES = (
    "-meta.xml", ".xml", ".cls", ".trigger", ".flow", ".email", ".permissionset",
    ".object", ".field", ".layout", ".settings", ".queue", ".group", ".md", ".yaml", ".yml",
    ".json", ".csv", ".js", ".html",
)

# Persona must name a permission construct, not only a job title.
PERSONA_SIGNALS = [
    r"permission set", r"\bpsg\b", r"\bps\b", r"\bprofile\b", r"\bqueue\b",
    r"\bguest\b", r"\bexternal\b", r"\bunauthenticated\b", r"\bvisitor\b",
    r"\bcommunity\b", r"\bportal\b", r"\bintegration user\b",
    r"\b[A-Za-z][A-Za-z0-9]*_[A-Za-z0-9_]+\b",  # Support_Agent — an API name reads as one
]

ELAPSED_BUSINESS_TIME = re.compile(
    r"\bbusiness (hours?|minutes?|days?)\b|\bworking (hours?|days?)\b|\bholiday\b", re.IGNORECASE
)

TABLE_COLUMN_ALIASES = {
    "ac_id": "ac_id", "ac id": "ac_id", "ac": "ac_id", "criterion": "ac_id", "criterion id": "ac_id",
    "req_id": "req_id", "req id": "req_id", "req": "req_id", "requirement": "req_id",
    "requirement id": "req_id",
    "story_id": "story_id", "story id": "story_id", "story": "story_id",
    "persona": "persona", "actor": "persona", "user": "persona",
    "test_type": "test_type", "test type": "test_type", "automation": "test_type",
    "automatable": "test_type",
    "artefact": "artefact", "artifact": "artefact", "artefact under test": "artefact",
    "artifact under test": "artefact", "component": "artefact",
    "negative": "negative", "negative_path": "negative", "deny case": "negative",
    "given": "given", "when": "when", "then": "then",
    "sandbox": "sandbox", "seed_data": "seed_data", "seed data": "seed_data",
    "proof": "proof", "oracle": "proof", "evidence": "proof",
}


class ParseError(Exception):
    """The document is not in the restricted YAML subset this linter understands."""


# --------------------------------------------------------------------------- YAML subset parser


def _strip_comment(line: str) -> str:
    out: list[str] = []
    quote: str | None = None
    for i, ch in enumerate(line):
        if quote:
            out.append(ch)
            if ch == quote:
                quote = None
            continue
        if ch in ("'", '"'):
            quote = ch
            out.append(ch)
            continue
        if ch == "#" and (i == 0 or line[i - 1].isspace()):
            break
        out.append(ch)
    return "".join(out).rstrip()


def _scalar(raw: str) -> object:
    raw = raw.strip()
    if not raw:
        return ""
    if raw[0] in ("|", ">"):
        raise ParseError("multi-line scalars (| and >) are not supported in this criteria format")
    if raw[0] == "{":
        raise ParseError("flow mappings ({...}) are not supported in this criteria format")
    if raw[0] in ("&", "*"):
        raise ParseError("anchors and aliases are not supported in this criteria format")
    if raw.startswith("[") and raw.endswith("]"):
        inner = raw[1:-1].strip()
        return [] if not inner else [_scalar(part) for part in inner.split(",")]
    if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in ("'", '"'):
        return raw[1:-1]
    return raw


def _indent_of(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _parse_block(lines: list[tuple[int, str]], pos: int, indent: int) -> tuple[object, int]:
    """Parse one block at the given indent. Returns (value, next position)."""
    if pos >= len(lines):
        return {}, pos

    _, first = lines[pos]
    if first.lstrip().startswith("- "):
        seq: list[object] = []
        while pos < len(lines):
            lineno, line = lines[pos]
            cur = _indent_of(line)
            if cur < indent or not line.lstrip().startswith("- "):
                break
            if cur > indent:
                raise ParseError(f"line {lineno}: unexpected indent inside a sequence")
            body_indent = cur + 2
            rewritten = [(lineno, " " * body_indent + line.lstrip()[2:])]
            pos += 1
            while pos < len(lines) and _indent_of(lines[pos][1]) >= body_indent:
                rewritten.append(lines[pos])
                pos += 1
            item, _ = _parse_block(rewritten, 0, body_indent)
            seq.append(item)
        return seq, pos

    mapping: dict[str, object] = {}
    while pos < len(lines):
        lineno, line = lines[pos]
        cur = _indent_of(line)
        if cur < indent:
            break
        if cur > indent:
            raise ParseError(f"line {lineno}: unexpected indent in a mapping")
        stripped = line.strip()
        if stripped.startswith("- "):
            break
        if ":" not in stripped:
            raise ParseError(f"line {lineno}: expected 'key: value', got {stripped!r}")
        key, _, rest = stripped.partition(":")
        key = key.strip()
        rest = rest.strip()
        pos += 1
        if rest:
            mapping[key] = _scalar(rest)
            continue
        if pos < len(lines):
            nxt_indent = _indent_of(lines[pos][1])
            nxt_is_seq = lines[pos][1].lstrip().startswith("- ")
            if nxt_indent > indent or (nxt_is_seq and nxt_indent >= indent):
                value, pos = _parse_block(lines, pos, nxt_indent)
                mapping[key] = value
                continue
        mapping[key] = ""
    return mapping, pos


def parse_criteria_yaml(text: str) -> dict:
    lines: list[tuple[int, str]] = []
    for i, raw in enumerate(text.splitlines(), start=1):
        if raw.strip() in ("---", "..."):
            continue
        cleaned = _strip_comment(raw)
        if not cleaned.strip():
            continue
        if "\t" in cleaned[: _indent_of(cleaned) + 1]:
            raise ParseError(f"line {i}: tab used for indentation")
        lines.append((i, cleaned))
    if not lines:
        return {}
    doc, _ = _parse_block(lines, 0, _indent_of(lines[0][1]))
    return doc if isinstance(doc, dict) else {"acceptance_criteria": doc}


def extract_yaml_blocks(text: str) -> list[str]:
    """Return the bodies of fenced ```yaml blocks that declare an `acceptance_criteria:` key."""
    blocks: list[str] = []
    current: list[str] | None = None
    for line in text.splitlines():
        stripped = line.strip()
        if current is None:
            if stripped.startswith("```") and stripped[3:].strip().lower() in ("yaml", "yml"):
                current = []
            continue
        if stripped.startswith("```"):
            body = "\n".join(current)
            if re.search(r"^\s*acceptance_criteria:\s*$", body, re.MULTILINE):
                blocks.append(body)
            current = None
            continue
        current.append(line)
    return blocks


# --------------------------------------------------------------------------- markdown table parser


def _split_row(line: str) -> list[str]:
    body = line.strip()
    if body.startswith("|"):
        body = body[1:]
    if body.endswith("|"):
        body = body[:-1]
    return [cell.strip() for cell in body.split("|")]


def extract_criteria_tables(text: str) -> list[tuple[int, list[dict]]]:
    """Return (header_line_number, rows) for every Markdown table that is a criteria table.

    A criteria table is one whose header maps to given, when and then plus at least one id column.
    """
    found: list[tuple[int, list[dict]]] = []
    lines = text.splitlines()
    in_fence = False
    i = 0
    while i < len(lines):
        stripped = lines[i].strip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            i += 1
            continue
        if in_fence or not stripped.startswith("|"):
            i += 1
            continue
        # Candidate header — the next line must be the separator row.
        if i + 1 >= len(lines) or not re.match(r"^\s*\|[\s:|-]+\|\s*$", lines[i + 1]):
            i += 1
            continue
        header_cells = [c.strip().lower().strip("*`") for c in _split_row(lines[i])]
        keys = [TABLE_COLUMN_ALIASES.get(c, "") for c in header_cells]
        if not {"given", "when", "then"}.issubset(set(keys)) or not (
            "ac_id" in keys or "req_id" in keys
        ):
            i += 1
            continue
        header_line = i + 1
        rows: list[dict] = []
        j = i + 2
        while j < len(lines) and lines[j].strip().startswith("|"):
            cells = _split_row(lines[j])
            row: dict = {"__line__": j + 1}
            for key, cell in zip(keys, cells):
                if key:
                    row[key] = cell
            rows.append(row)
            j += 1
        if rows:
            found.append((header_line, rows))
        i = j
    return found


# --------------------------------------------------------------------------- repo root


def find_repo_root(start: Path) -> Path | None:
    for candidate in [start.resolve()] + list(start.resolve().parents):
        if (candidate / "standards").is_dir() and (candidate / "skills").is_dir():
            return candidate
    return None


# --------------------------------------------------------------------------- record checks


def _text_of(value: object) -> str:
    if isinstance(value, list):
        return ", ".join(str(v) for v in value)
    return "" if value is None else str(value)


def _is_true(value: object) -> bool:
    return _text_of(value).strip().lower() in ("true", "yes", "y", "1", "negative")


PLACEHOLDER = re.compile(r"^[\[<].*[\]>]$|\[[a-z_]+\]|<[a-z_]+>", re.IGNORECASE)


def _is_placeholder(value: object) -> bool:
    text = _text_of(value).strip()
    return bool(text) and bool(PLACEHOLDER.search(text))


def is_unfilled_template(rows: list[object]) -> bool:
    """True when every row's identity fields are still bracketed placeholders.

    An unfilled template is not a defective criteria file — it is a template. Reporting every
    placeholder as an error trains people to ignore the linter.
    """
    filled = [r for r in rows if isinstance(r, dict)]
    if not filled:
        return False
    return all(
        _is_placeholder(r.get("ac_id")) or _is_placeholder(r.get("req_id"))
        for r in filled
    )


def check_criteria(rows: list[object], origin: str, repo_root: Path | None) -> list[tuple[str, str]]:
    """Lint a list of criterion rows. Returns (level, message) tuples."""
    findings: list[tuple[str, str]] = []

    def err(msg: str) -> None:
        findings.append(("ERROR", f"{origin}: {msg}"))

    def warn(msg: str) -> None:
        findings.append(("WARN", f"{origin}: {msg}"))

    if not rows:
        err("no `acceptance_criteria` rows found — a criteria file with no criteria is not one.")
        return findings

    if is_unfilled_template(rows):
        warn(
            "every row still holds bracketed placeholders — this is an unfilled template, not a "
            "criteria record. Fill it and re-run."
        )
        return findings

    seen_ids: dict[str, str] = {}
    # req_id -> {"rule_types": set, "has_negative": bool, "labels": [...]}
    per_requirement: dict[str, dict] = {}

    for index, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            err(f"row {index} is not a mapping of fields.")
            continue

        ac_id = _text_of(row.get("ac_id")).strip()
        label = ac_id or f"row {index}"

        # 1 — required fields
        for field in REQUIRED_FIELDS:
            if not _text_of(row.get(field)).strip():
                err(f"{label}: missing required field `{field}`.")

        # 2 — ac_id shape and uniqueness
        if not ac_id:
            err(f"row {index}: missing `ac_id` — the UAT script and the RTM join on it.")
        else:
            if not AC_ID_PATTERN.match(ac_id):
                err(f"{label}: `ac_id` should read AC-<requirement>.<n> (e.g. AC-001.2).")
            if ac_id in seen_ids:
                err(f"{label}: duplicate `ac_id`, already used at {seen_ids[ac_id]}.")
            else:
                seen_ids[ac_id] = label

        # 3 — req_id shape
        req_id = _text_of(row.get("req_id")).strip()
        if req_id and not REQ_ID_PATTERN.match(req_id):
            err(
                f"{label}: `req_id` is {req_id!r}; use REQ-<digits> (an ACME- style project prefix "
                "is allowed) per admin/requirements-traceability-matrix § ID Conventions. "
                "An FG- id is a fit-gap row id — translate it, do not store it here."
            )

        # 4 — test_type
        test_type = _text_of(row.get("test_type")).strip().lower()
        if test_type and test_type not in TEST_TYPES:
            err(f"{label}: `test_type` is {test_type!r}; allowed values are {', '.join(TEST_TYPES)}.")

        given = _text_of(row.get("given"))
        when = _text_of(row.get("when"))
        then = _text_of(row.get("then"))

        # 5 — implementation detail in Then
        for pattern, why in IMPLEMENTATION_IN_THEN:
            if re.search(pattern, then, re.IGNORECASE):
                err(
                    f"{label}: `then` {why} — a Then names the observable outcome, not the tool "
                    "that produced it (references/gotchas.md gotcha 3)."
                )
                break

        # 6 — ambiguous words
        clause_text = f"{given}\n{when}\n{then}".lower()
        for word in AMBIGUOUS_WORDS:
            if re.search(rf"(?<![\w-]){re.escape(word)}(?![\w-])", clause_text):
                err(
                    f"{label}: ambiguous wording {word!r} in a Given/When/Then clause — replace it "
                    "with a named observable (references/gotchas.md gotcha 4)."
                )
                break

        # 7 — collect rule-type coverage
        artefact = _text_of(row.get("artefact"))
        haystack = f"{artefact}\n{given}\n{when}\n{then}".lower()
        bucket = per_requirement.setdefault(
            req_id or f"(row {index} has no req_id)",
            {"rule_types": set(), "has_negative": False, "labels": []},
        )
        bucket["labels"].append(label)
        for pattern, name in RULE_TYPE_MARKERS:
            if re.search(pattern, haystack):
                bucket["rule_types"].add(name)
        if _is_true(row.get("negative")):
            bucket["has_negative"] = True

        # 8 — artefact resolution
        if artefact:
            first = artefact.split(",")[0].split(";")[0].strip().strip("`")
            if first.startswith(REPO_PATH_PREFIXES):
                if repo_root is None:
                    warn(f"{label}: cannot resolve repo path {first!r} — repo root not found.")
                elif not (repo_root / first).exists():
                    err(f"{label}: `artefact` path {first!r} does not exist in the repo.")
            elif not first.lower().endswith(METADATA_SUFFIXES) and "/" not in first:
                warn(
                    f"{label}: `artefact` {first!r} names no file — point at the metadata file or "
                    "repo path under test so the criterion is checkable."
                )

        # 9 — WARN-level quality signals
        if not _text_of(row.get("proof")).strip():
            warn(
                f"{label}: no `proof` — name the query, checker or observation that makes the Then "
                "falsifiable, or the criterion cannot fail (references/gotchas.md gotcha 13)."
            )

        persona = _text_of(row.get("persona"))
        if persona and not any(re.search(p, persona, re.IGNORECASE) for p in PERSONA_SIGNALS):
            warn(
                f"{label}: `persona` {persona!r} names a job title but no permission construct — "
                "name the profile, permission set or PSG (references/gotchas.md gotcha 5)."
            )

        if test_type == "apex" and ELAPSED_BUSINESS_TIME.search(then):
            warn(
                f"{label}: marked `test_type: apex` but the Then depends on elapsed business time; "
                "a synchronous test cannot advance the business-hours clock "
                "(references/gotchas.md gotcha 12)."
            )

    # 7 — one negative criterion per rule-type requirement
    for req_id, bucket in sorted(per_requirement.items()):
        if bucket["rule_types"] and not bucket["has_negative"]:
            kinds = ", ".join(sorted(bucket["rule_types"]))
            findings.append((
                "ERROR",
                f"{origin}: {req_id} is a rule-type requirement ({kinds}) with no criterion marked "
                f"`negative: true`. Every rule engine defines an evaluation order and a "
                f"fall-through; the criteria are where the no-match outcome gets named "
                f"(references/gotchas.md gotcha 10). Criteria seen: {', '.join(bucket['labels'])}."
            ))

    return findings


# --------------------------------------------------------------------------- gherkin checks


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
            if not re.search(rf"\b{kw}\b", body_text):
                missing.append(kw.capitalize())
        if missing:
            issues.append(
                f"Line {line_idx + 1}: Scenario {header!r} is missing required clause(s): {', '.join(missing)}"
            )
    return issues


def check_negative_path_pairing(scenarios: list[tuple[int, str, list[str]]]) -> list[str]:
    """Heuristic: count happy-path vs deny-case Then assertions."""
    happy_re = re.compile(
        r"\bthen\b.*?\b(succeeds?|is created|is visible|is saved|is updated|returns?|is sent|is enabled|is granted)\b",
        re.IGNORECASE | re.DOTALL,
    )
    deny_re = re.compile(
        r"\bthen\b.*?\b(fails?|is denied|is hidden|is not created|is rejected|is blocked|access is denied|insufficient privileges|cannot|error|never|no )\b",
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

    if any(re.search(pat, lower) for pat in PERMISSION_SIGNALS):
        return []

    return [
        f"Story tags sharing-relevant object(s) ({', '.join(sorted(set(tagged_objects))[:5])}) "
        "but no permission/PSG/profile/OWD/owner precondition is declared in the AC. "
        "Add a Background block naming the running user(s) and PSG."
    ]


def check_bulk_path(content: str) -> list[str]:
    """Trigger / flow / validation behavior must include a Scenario with volume >= 200."""
    lower = content.lower()
    if not any(re.search(pat, lower) for pat in TRIGGER_BOUND_PHRASES):
        return []

    for m in re.finditer(r"\b(\d{3,})\b", content):
        try:
            if int(m.group(1)) >= BULK_THRESHOLD:
                return []
        except ValueError:
            continue

    return [
        f"AC mentions trigger / flow / validation rule / bulk behavior but no Scenario "
        f"contains a record-count >= {BULK_THRESHOLD}. "
        "Add a bulk Scenario asserting governor-limit safety at one trigger batch."
    ]


def check_async_eventually(content: str) -> list[str]:
    """Async / callout boundaries must use 'eventually within N' phrasing in the Then."""
    lower = content.lower()
    if not any(re.search(pat, lower) for pat in ASYNC_BOUND_PHRASES):
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
        block = "\n".join(lines[i : i + 5])
        has_quoted_msg = bool(re.search(r"\".+?\"", block))
        has_tbd = "tbd" in block.lower() or "# todo" in block.lower()
        if not has_quoted_msg and not has_tbd:
            issues.append(
                f"Line {i + 1}: Then-fails clause has no exact error message in quotes "
                f"and no '# TBD' marker: {line.strip()[:100]!r}"
            )
    return issues


def lint_gherkin(content: str, origin: str) -> list[tuple[str, str]]:
    issues: list[str] = []
    scenarios = extract_scenarios(content)
    if scenarios:
        issues.extend(check_gherkin_completeness(scenarios))
        issues.extend(check_negative_path_pairing(scenarios))
    issues.extend(check_ui_coupled_language(content))
    issues.extend(check_permission_precondition(content))
    issues.extend(check_bulk_path(content))
    issues.extend(check_async_eventually(content))
    issues.extend(check_vague_validation(content))
    return [("ERROR", f"{origin}: {issue}") for issue in issues]


# --------------------------------------------------------------------------- driver


def has_gherkin(content: str) -> bool:
    return bool(re.search(r"^\s*Scenario(\s+Outline)?\s*:", content, re.MULTILINE))


def looks_like_ac_file(content: str) -> bool:
    """True when the file holds something this linter can actually check.

    Deliberately narrow: prose that merely mentions "acceptance criteria" is not a criteria file,
    and treating it as one turns a folder scan into noise.
    """
    if re.search(r"^\s*acceptance_criteria:\s*$", content, re.MULTILINE):
        return True
    if has_gherkin(content):
        return True
    return bool(extract_criteria_tables(content))


def lint_path(path: Path, repo_root: Path | None) -> tuple[list[tuple[str, str]], int]:
    """Lint one file. Returns (findings, number of documents checked)."""
    try:
        content = path.read_text(encoding="utf-8")
    except OSError as exc:
        return [("ERROR", f"{path}: could not be read ({exc})")], 0

    findings: list[tuple[str, str]] = []
    documents = 0

    # 1 — criteria records
    bodies: list[tuple[str, str]] = []
    if path.suffix.lower() in (".yaml", ".yml"):
        if re.search(r"^\s*acceptance_criteria:\s*$", content, re.MULTILINE):
            bodies.append((str(path), content))
    else:
        bodies.extend(
            (f"{path} (yaml block {i + 1})", block)
            for i, block in enumerate(extract_yaml_blocks(content))
        )

    for origin, body in bodies:
        documents += 1
        try:
            doc = parse_criteria_yaml(body)
        except ParseError as exc:
            findings.append(("ERROR", f"{origin}: {exc}"))
            continue
        rows = doc.get("acceptance_criteria") if isinstance(doc, dict) else None
        if rows is None:
            findings.append(("ERROR", f"{origin}: no top-level `acceptance_criteria:` key"))
            continue
        if not isinstance(rows, list):
            findings.append(("ERROR", f"{origin}: `acceptance_criteria:` must be a list of rows"))
            continue
        findings.extend(check_criteria(rows, origin, repo_root))

    # 2 — criteria tables
    for header_line, rows in extract_criteria_tables(content):
        documents += 1
        findings.extend(check_criteria(rows, f"{path} (table at line {header_line})", repo_root))

    # 3 — Gherkin story
    if has_gherkin(content):
        documents += 1
        findings.extend(lint_gherkin(content, str(path)))

    if documents == 0:
        findings.append((
            "ERROR",
            f"{path}: no `acceptance_criteria:` record, no criteria table and no 'Scenario:' "
            "header. Nothing to lint — start from templates/ac-template.md or "
            "references/worked-examples.md § 5.",
        ))

    return findings, documents


def gather_paths(args: argparse.Namespace) -> list[Path]:
    target = args.file or args.file_flag
    if target:
        return [Path(target)]
    root = Path(args.manifest_dir)
    if not root.is_dir():
        return []
    keep: list[Path] = []
    for pattern in ("*.yaml", "*.yml", "*.md"):
        for candidate in sorted(root.rglob(pattern)):
            try:
                body = candidate.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            if looks_like_ac_file(body):
                keep.append(candidate)
    return keep


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Lint Salesforce acceptance criteria — a criteria record (YAML or markdown "
                    "table) or a Gherkin story file.",
    )
    parser.add_argument("file", nargs="?", help="Path to the criteria or story file to lint.")
    parser.add_argument("--file", dest="file_flag", help="Alternate way to pass the file path.")
    parser.add_argument(
        "--manifest-dir",
        dest="manifest_dir",
        help="Directory to scan recursively for criteria records, criteria tables and story files.",
    )
    parser.add_argument(
        "--repo-root",
        default=None,
        help="Repo root used to resolve repo paths named in `artefact`. Default: walk up from the file.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if not (args.file or args.file_flag or args.manifest_dir):
        print(
            "Usage: check_ac_format.py --file <criteria.yaml|story.md> | --manifest-dir <dir>",
            file=sys.stderr,
        )
        return 2

    paths = gather_paths(args)
    if not paths:
        target = args.file or args.file_flag or args.manifest_dir
        print(f"ERROR: nothing to lint at {target}", file=sys.stderr)
        return 2

    findings: list[tuple[str, str]] = []
    documents = 0
    for path in paths:
        if not path.exists():
            findings.append(("ERROR", f"{path}: file not found"))
            continue
        if not path.is_file():
            findings.append(("ERROR", f"{path}: not a file"))
            continue
        repo_root = Path(args.repo_root).resolve() if args.repo_root else find_repo_root(path.parent)
        print(f"Checking: {path}")
        path_findings, count = lint_path(path, repo_root)
        findings.extend(path_findings)
        documents += count

    errors = [m for level, m in findings if level == "ERROR"]
    warns = [m for level, m in findings if level == "WARN"]

    for message in warns:
        print(f"WARN: {message}")
    for message in errors:
        print(f"ERROR: {message}", file=sys.stderr)

    print(f"\n{documents} document(s) checked — {len(errors)} error(s), {len(warns)} warning(s).")
    if errors:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
