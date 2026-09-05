#!/usr/bin/env python3
"""Lint a Salesforce requirements catalogue before it is handed to a downstream agent.

The catalogue is the artefact this skill produces: a flat list of requirement rows, one per
requirement, each carrying the Salesforce facts a downstream agent needs (object, automation tier,
sharing layer, volume, licence) plus its provenance (source stakeholder) and its destination
(downstream target). See ``references/worked-examples.md`` for a filled example and
``templates/requirements-catalogue.yaml`` for the skeleton.

Checks (ERROR unless marked WARN):

  1. Required fields present on every row: id, statement, type, source_stakeholder, priority,
     status, downstream.
  2. ``id`` matches ``REQ-<digits>`` and is unique across the catalogue.
  3. ``priority`` is a MoSCoW value: Must / Should / Could / Wont.
  4. ``status`` is one of draft / confirmed / deferred / descoped / blocked.
  5. ``downstream`` names at least one non-empty target (story, fit_gap_row, workbook_section).
  6. A row with ``automation_candidate`` also carries ``decision_tree_step`` (the tree branch that
     produced the tier, not the author's preference).
  7. A row with ``sharing_impact`` also carries a recognised ``sharing_layer`` — one of the seven
     ordered layers in standards/decision-trees/sharing-selection.md, or Field-Level Security.
  8. A ``type: nfr`` row carries ``measure`` (a number with a unit). An NFR with no number is an
     opinion.
  9. Any repo path named inside ``decision_tree_step`` resolves against the repo root (WARN when the
     repo root cannot be located, e.g. when the catalogue is linted outside a checkout).
 10. WARN: a ``type: functional`` row with no ``objects``, and a ``status: blocked`` row with no
     ``notes`` naming an owner or a date.

Stdlib only. Understands the restricted block-YAML subset the template uses: mappings, nested
mappings, sequences of mappings, inline ``[a, b]`` lists, quoted or bare scalars, ``#`` comments.
Multi-line scalars (``|``, ``>``), anchors and flow mappings are rejected with a parse error.

Usage:
    python3 check_requirements_catalogue.py --file requirements-catalogue.yaml
    python3 check_requirements_catalogue.py --file references/worked-examples.md
    python3 check_requirements_catalogue.py --manifest-dir docs/discovery/

Exit code 0 when there are no ERRORs (WARNs may still print); 1 otherwise.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REQUIRED_FIELDS = (
    "id",
    "statement",
    "type",
    "source_stakeholder",
    "priority",
    "status",
    "downstream",
)

ID_PATTERN = re.compile(r"^REQ-\d{2,}$")

MOSCOW = ("Must", "Should", "Could", "Wont")
STATUSES = ("draft", "confirmed", "deferred", "descoped", "blocked")
TYPES = ("functional", "nfr")
DOWNSTREAM_TARGETS = ("story", "fit_gap_row", "workbook_section")

# The seven ordered layers of standards/decision-trees/sharing-selection.md, plus the field-access
# mechanism people routinely confuse with them. Matched case-insensitively on a normalised string.
SHARING_LAYERS = {
    "owd": "OWD",
    "organization-wide default": "OWD",
    "organisation-wide default": "OWD",
    "role hierarchy": "Role Hierarchy",
    "sharing rules": "Sharing Rules",
    "sharing rule": "Sharing Rules",
    "teams": "Teams",
    "team": "Teams",
    "manual": "Manual / Apex",
    "manual / apex": "Manual / Apex",
    "apex managed sharing": "Manual / Apex",
    "restriction rules": "Restriction / Scoping Rules",
    "scoping rules": "Restriction / Scoping Rules",
    "restriction / scoping rules": "Restriction / Scoping Rules",
    "implicit": "Implicit",
    "field-level security": "Field-Level Security",
    "fls": "Field-Level Security",
}

# A number with something after it — "4,200 records/month", "18,000-row", "900 rows/night", "3 logins".
MEASURE_PATTERN = re.compile(r"\d[\d,\.]*\s*[A-Za-z%/\-]")

REPO_PATH_PATTERN = re.compile(r"\b((?:[\w.\-]+/)+[\w.\-]+\.md)\b")


class ParseError(Exception):
    """The file is not in the restricted YAML subset this linter understands."""


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
        raise ParseError("multi-line scalars (| and >) are not supported in this catalogue format")
    if raw[0] == "{":
        raise ParseError("flow mappings ({...}) are not supported in this catalogue format")
    if raw[0] == "&" or raw[0] == "*":
        raise ParseError("anchors and aliases are not supported in this catalogue format")
    if raw.startswith("[") and raw.endswith("]"):
        inner = raw[1:-1].strip()
        if not inner:
            return []
        return [_scalar(part) for part in inner.split(",")]
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
            # Re-write the "- " marker as spaces so the item body is a plain mapping block.
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
        # Nested block, if the next non-blank line is deeper (or is a sequence item at any depth).
        if pos < len(lines):
            nxt_indent = _indent_of(lines[pos][1])
            nxt_is_seq = lines[pos][1].lstrip().startswith("- ")
            if nxt_indent > indent or (nxt_is_seq and nxt_indent >= indent):
                value, pos = _parse_block(lines, pos, nxt_indent)
                mapping[key] = value
                continue
        mapping[key] = ""
    return mapping, pos


def parse_catalogue_yaml(text: str) -> dict:
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
    return doc if isinstance(doc, dict) else {"requirements": doc}


def extract_yaml_blocks(text: str) -> list[str]:
    """Return the bodies of fenced ```yaml blocks that declare a `requirements:` key."""
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
            if re.search(r"^\s*requirements:\s*$", body, re.MULTILINE):
                blocks.append(body)
            current = None
            continue
        current.append(line)
    return blocks


# --------------------------------------------------------------------------- repo root


def find_repo_root(start: Path) -> Path | None:
    for candidate in [start.resolve()] + list(start.resolve().parents):
        if (candidate / "standards" / "decision-trees").is_dir():
            return candidate
    return None


# --------------------------------------------------------------------------- checks


def _as_text(value: object) -> str:
    if isinstance(value, list):
        return ", ".join(str(v) for v in value)
    return "" if value is None else str(value)


def check_rows(rows: list[object], origin: str, repo_root: Path | None) -> list[tuple[str, str]]:
    findings: list[tuple[str, str]] = []
    seen_ids: dict[str, int] = {}

    def err(msg: str) -> None:
        findings.append(("ERROR", f"{origin}: {msg}"))

    def warn(msg: str) -> None:
        findings.append(("WARN", f"{origin}: {msg}"))

    if not rows:
        err("no `requirements:` rows found. A catalogue with no rows is not a catalogue.")
        return findings

    for index, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            err(f"row {index} is not a mapping of fields.")
            continue

        row_id = _as_text(row.get("id")).strip()
        label = row_id or f"row {index}"

        # 1 — required fields
        for field in REQUIRED_FIELDS:
            if not _as_text(row.get(field)).strip() and not row.get(field):
                err(f"{label}: missing required field `{field}`.")

        # 2 — id shape and uniqueness
        if row_id:
            if not ID_PATTERN.match(row_id):
                err(f"{label}: `id` must match REQ-<digits> (e.g. REQ-001) so the RTM can join on it.")
            if row_id in seen_ids:
                err(f"{label}: duplicate `id`, already used by row {seen_ids[row_id]}. Ids are permanent join keys.")
            else:
                seen_ids[row_id] = index

        # type
        row_type = _as_text(row.get("type")).strip().lower()
        if row_type and row_type not in TYPES:
            err(f"{label}: `type` is {row_type!r}; allowed values are {', '.join(TYPES)}.")

        # 3 — MoSCoW
        priority = _as_text(row.get("priority")).strip()
        if priority and priority not in MOSCOW:
            err(f"{label}: `priority` is {priority!r}; MoSCoW values are {', '.join(MOSCOW)}.")

        # 4 — status
        status = _as_text(row.get("status")).strip().lower()
        if status and status not in STATUSES:
            err(f"{label}: `status` is {status!r}; allowed values are {', '.join(STATUSES)}.")

        # 5 — downstream target
        downstream = row.get("downstream")
        if downstream:
            if not isinstance(downstream, dict):
                err(f"{label}: `downstream` must be a mapping with at least one of {', '.join(DOWNSTREAM_TARGETS)}.")
            else:
                unknown = [k for k in downstream if k not in DOWNSTREAM_TARGETS]
                if unknown:
                    warn(f"{label}: unrecognised downstream key(s) {', '.join(sorted(unknown))}.")
                if not any(_as_text(downstream.get(k)).strip() for k in DOWNSTREAM_TARGETS):
                    err(
                        f"{label}: `downstream` names no target. A row with no story, fit-gap row or "
                        "workbook section is a dropped requirement, not a finished one."
                    )

        # 6 — automation rows cite a tree step
        automation = _as_text(row.get("automation_candidate")).strip()
        tree_step = _as_text(row.get("decision_tree_step")).strip()
        if automation and not tree_step:
            err(
                f"{label}: `automation_candidate` is set but `decision_tree_step` is empty. Name the "
                "standards/decision-trees/ branch that produced the tier — otherwise it is a preference."
            )

        # 7 — sharing rows name a layer
        sharing_impact = _as_text(row.get("sharing_impact")).strip()
        sharing_layer = _as_text(row.get("sharing_layer")).strip()
        if sharing_impact:
            if not sharing_layer:
                err(
                    f"{label}: `sharing_impact` is set but `sharing_layer` is empty. "
                    "'Only managers see it' is not a requirement until it names a layer."
                )
            elif sharing_layer.strip().lower() not in SHARING_LAYERS:
                err(
                    f"{label}: `sharing_layer` is {sharing_layer!r}, which is not one of the seven "
                    "layers in standards/decision-trees/sharing-selection.md (or Field-Level Security)."
                )

        # 8 — NFR rows carry a measure
        if row_type == "nfr":
            measure = _as_text(row.get("measure")).strip()
            if not measure:
                err(f"{label}: `type: nfr` rows must carry `measure`. An NFR with no number is an opinion.")
            elif not MEASURE_PATTERN.search(measure):
                err(f"{label}: `measure` ({measure!r}) contains no quantity with a unit.")

        # 9 — repo paths inside the tree step resolve
        if tree_step:
            for path_text in REPO_PATH_PATTERN.findall(tree_step):
                if repo_root is None:
                    warn(f"{label}: cannot verify `{path_text}` — no repo root found above the catalogue.")
                elif not (repo_root / path_text).exists():
                    err(f"{label}: `decision_tree_step` names `{path_text}`, which does not exist in the repo.")

        # 10 — advisory
        if row_type == "functional" and not row.get("objects"):
            warn(f"{label}: functional row with no `objects`. The downstream builder has nothing to start from.")
        if status == "blocked":
            notes = _as_text(row.get("notes")).strip()
            if not notes:
                warn(f"{label}: `status: blocked` with no `notes`. Record the owner and the decision date.")

    return findings


# --------------------------------------------------------------------------- driver


def collect_documents(path: Path) -> list[tuple[str, str]]:
    """Return [(origin_label, yaml_text)] for one file."""
    text = path.read_text(encoding="utf-8", errors="ignore")
    if path.suffix.lower() in (".yaml", ".yml"):
        return [(str(path), text)]
    blocks = extract_yaml_blocks(text)
    return [(f"{path} (yaml block {i + 1})", block) for i, block in enumerate(blocks)]


def gather_paths(args: argparse.Namespace) -> list[Path]:
    if args.file:
        return [Path(args.file)]
    root = Path(args.manifest_dir)
    if not root.is_dir():
        return []
    found: list[Path] = []
    for pattern in ("*.yaml", "*.yml", "*.md"):
        found.extend(sorted(root.rglob(pattern)))
    keep: list[Path] = []
    for candidate in found:
        try:
            body = candidate.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if re.search(r"^\s*requirements:\s*$", body, re.MULTILINE):
            keep.append(candidate)
    return keep


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Lint a Salesforce requirements catalogue (YAML, or a Markdown file with a yaml fence).",
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--file", help="Path to one catalogue (.yaml/.yml) or a Markdown file containing one.")
    group.add_argument(
        "--manifest-dir",
        help="Directory to scan recursively for catalogues (.yaml/.yml/.md containing a `requirements:` key).",
    )
    parser.add_argument(
        "--repo-root",
        default=None,
        help="Repo root used to resolve paths named in decision_tree_step. Default: walk up from the catalogue.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    paths = gather_paths(args)

    if not paths:
        target = args.file or args.manifest_dir
        print(f"ERROR: no requirements catalogue found at {target}")
        return 1

    findings: list[tuple[str, str]] = []
    documents = 0

    for path in paths:
        if not path.exists():
            findings.append(("ERROR", f"{path}: file not found"))
            continue
        try:
            docs = collect_documents(path)
        except OSError as exc:
            findings.append(("ERROR", f"{path}: could not be read ({exc})"))
            continue
        if not docs:
            findings.append(("ERROR", f"{path}: no yaml catalogue block found"))
            continue

        repo_root = Path(args.repo_root).resolve() if args.repo_root else find_repo_root(path.parent)

        for origin, body in docs:
            documents += 1
            print(f"Checking: {origin}")
            try:
                doc = parse_catalogue_yaml(body)
            except ParseError as exc:
                findings.append(("ERROR", f"{origin}: {exc}"))
                continue
            rows = doc.get("requirements") if isinstance(doc, dict) else None
            if rows is None:
                findings.append(("ERROR", f"{origin}: no top-level `requirements:` key"))
                continue
            if not isinstance(rows, list):
                findings.append(("ERROR", f"{origin}: `requirements:` must be a list of rows"))
                continue
            findings.extend(check_rows(rows, origin, repo_root))

    errors = [m for level, m in findings if level == "ERROR"]
    warns = [m for level, m in findings if level == "WARN"]

    for message in warns:
        print(f"WARN: {message}")
    for message in errors:
        print(f"ERROR: {message}")

    print(f"\n{documents} catalogue(s) checked — {len(errors)} error(s), {len(warns)} warning(s).")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
