#!/usr/bin/env python3
"""Lint a Salesforce-project RACI artefact (YAML or JSON).

This is the ONLY checker in this skill. It replaces the earlier pair
(``check_raci.py`` + a ``check_stakeholder_raci_for_sf_projects.py``
wrapper that only re-exec'd it).

Rules enforced (ERROR unless noted):

  1. required top-level keys are present
     (project, phase, version, stakeholders, activities, escalation_path)
  2. stakeholder codes are unique and each has a role
  3. activity ids are unique; every activity carries an ``activity`` slug
     from the required list, and every required slug appears at least once
  4. every cell value is from the enum {R, A, C, I, -, --, empty}
  5. exactly one A per activity row
  6. at least one R per activity row
  7. no role is both A and C on the same row (a Consulted role cannot be
     the decision-maker)
  8. a role that is both A and R on the same row is a WARN, not an error —
     the accountable person often does the work on small teams, but if it
     is true for most rows the matrix has no delegation in it
  9. every activity row has an escalation rule with trigger + target +
     time_box_business_days > 0
 10. a project-level ``escalation_path`` exists with at least one level,
     each carrying level + forum + time_box_business_days

WARN-level findings: unnamed stakeholders, cell codes outside the roster,
``executed_by`` repo paths that do not resolve, refusal-code map gaps, and
the A==R overlap in rule 8.

Usage:
    python3 check_raci.py --file path/to/raci.yaml
    python3 check_raci.py --file path/to/raci.json
    python3 check_raci.py --manifest-dir path/to/dir   # lints raci*.yaml|yml|json
    python3 check_raci.py --file path/to/raci.yaml --strict   # warnings fail too
    python3 check_raci.py --help

Stdlib only — the YAML reader below understands the restricted subset this
skill's template emits (block mappings, block sequences, scalars, inline
``[a, b]`` lists, ``#`` comments). It is deliberately not a general YAML
parser; anything fancier should be written as JSON instead.

Exit codes:
    0 - valid (or valid with warnings and no --strict)
    1 - errors found (or warnings found under --strict)
    2 - usage error
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

VALID_CELL_VALUES = {"R", "A", "C", "I", "-", "--", "—", ""}
INVOLVED_VALUES = {"R", "A", "C", "I"}
REQUIRED_TOP_KEYS = (
    "project",
    "phase",
    "version",
    "stakeholders",
    "activities",
    "escalation_path",
)
REQUIRED_ESCALATION_KEYS = ("trigger", "target", "time_box_business_days")
REQUIRED_ESCALATION_PATH_KEYS = ("level", "forum", "time_box_business_days")

# The Salesforce activity rows every project RACI must answer for. Sub-rows
# are allowed (two rows may both carry activity: data-model-change, e.g.
# "PHI" and "non-PHI"), but a missing slug means a decision nobody owns.
REQUIRED_ACTIVITIES = (
    "data-model-change",
    "sharing-model-change",
    "permission-set-change",
    "integration-change",
    "release-go-no-go",
    "sandbox-refresh-approval",
    "production-hotfix",
    "data-load-approval",
    "release-update-activation",
    "seasonal-release-preview",
)

PLACEHOLDER_NAMES = {"", "_____________", "tbd", "tba", "???", "n/a", "name here"}


# --------------------------------------------------------------------------
# Minimal YAML reader (restricted subset)
# --------------------------------------------------------------------------


def _strip_comment(raw: str) -> str:
    """Remove a trailing ``#`` comment that is not inside quotes."""
    out: list[str] = []
    quote: str | None = None
    prev = ""
    for ch in raw:
        if quote:
            out.append(ch)
            if ch == quote and prev != "\\":
                quote = None
        elif ch in ("'", '"'):
            quote = ch
            out.append(ch)
        elif ch == "#" and (not out or out[-1] in (" ", "\t")):
            break
        else:
            out.append(ch)
        prev = ch
    return "".join(out).rstrip()


def _scalar(token: str) -> Any:
    token = token.strip()
    if token == "":
        return ""
    if len(token) >= 2 and token[0] == token[-1] and token[0] in ("'", '"'):
        return token[1:-1]
    if token.startswith("{"):
        raise YamlError(
            f"flow mapping {token!r} is not supported — write it as an indented block mapping"
        )
    if token.startswith("[") and token.endswith("]"):
        inner = token[1:-1].strip()
        if not inner:
            return []
        return [_scalar(part) for part in inner.split(",")]
    low = token.lower()
    if low in ("true", "yes"):
        return True
    if low in ("false", "no"):
        return False
    if low in ("null", "~"):
        return None
    try:
        return int(token)
    except ValueError:
        pass
    try:
        return float(token)
    except ValueError:
        pass
    return token


def _tokenize(text: str) -> list[tuple[int, str, int]]:
    """Return [(indent, content, source_line_no)] with blanks/comments dropped
    and ``- key: value`` split into a bare ``-`` plus an indented mapping line."""
    tokens: list[tuple[int, str, int]] = []
    for lineno, raw in enumerate(text.splitlines(), start=1):
        if raw.strip().startswith("#") or not raw.strip():
            continue
        if raw.lstrip().startswith("---"):
            continue
        body = _strip_comment(raw)
        if not body.strip():
            continue
        indent = len(body) - len(body.lstrip(" "))
        content = body.strip()
        if content.startswith("- "):
            tokens.append((indent, "-", lineno))
            tokens.append((indent + 2, content[2:].strip(), lineno))
        elif content == "-":
            tokens.append((indent, "-", lineno))
        else:
            tokens.append((indent, content, lineno))
    return tokens


class YamlError(ValueError):
    """Raised when the restricted YAML subset cannot be read."""


def _die(message: str) -> None:
    """Usage / input error — exit code 2, distinct from a lint failure (1)."""
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(2)


def _parse_block(tokens: list[tuple[int, str, int]], idx: int, indent: int) -> tuple[Any, int]:
    if idx >= len(tokens):
        return "", idx
    if tokens[idx][1] == "-":
        return _parse_sequence(tokens, idx, indent)
    return _parse_mapping(tokens, idx, indent)


_MAPPING_KEY_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_.\-]*\s*:(\s|$)")


def _is_mapping_start(content: str) -> bool:
    return bool(_MAPPING_KEY_RE.match(content))


def _parse_sequence(tokens: list[tuple[int, str, int]], idx: int, indent: int) -> tuple[list, int]:
    items: list[Any] = []
    while idx < len(tokens) and tokens[idx][0] == indent and tokens[idx][1] == "-":
        idx += 1  # consume the "-" marker
        if idx < len(tokens) and tokens[idx][0] > indent:
            content = tokens[idx][1]
            if content == "-" or _is_mapping_start(content):
                value, idx = _parse_block(tokens, idx, tokens[idx][0])
                items.append(value)
            else:  # plain scalar list item
                items.append(_scalar(content))
                idx += 1
        else:
            items.append("")
    return items, idx


def _parse_mapping(tokens: list[tuple[int, str, int]], idx: int, indent: int) -> tuple[dict, int]:
    mapping: dict[str, Any] = {}
    while idx < len(tokens) and tokens[idx][0] == indent and tokens[idx][1] != "-":
        _, content, lineno = tokens[idx]
        if ":" not in content:
            raise YamlError(f"line {lineno}: expected 'key: value', got {content!r}")
        key, _, rest = content.partition(":")
        key = key.strip()
        rest = rest.strip()
        idx += 1
        if rest:
            mapping[key] = _scalar(rest)
            continue
        if idx < len(tokens) and tokens[idx][0] > indent:
            mapping[key], idx = _parse_block(tokens, idx, tokens[idx][0])
        else:
            mapping[key] = None
    return mapping, idx


def read_yaml(text: str) -> Any:
    tokens = _tokenize(text)
    if not tokens:
        return {}
    value, idx = _parse_block(tokens, 0, tokens[0][0])
    if idx != len(tokens):
        raise YamlError(f"line {tokens[idx][2]}: unexpected indentation")
    return value


def load_artefact(path: Path) -> dict[str, Any]:
    if not path.exists():
        _die(f"file not found: {path}")
    text = path.read_text(encoding="utf-8")
    try:
        if path.suffix.lower() == ".json":
            data = json.loads(text)
        else:
            data = read_yaml(text)
    except (json.JSONDecodeError, YamlError) as exc:
        _die(f"cannot parse {path}: {exc}")
    if not isinstance(data, dict):
        _die(f"{path}: top level must be a mapping, got {type(data).__name__}")
    return data


# --------------------------------------------------------------------------
# Checks
# --------------------------------------------------------------------------


def check_top_level(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for key in REQUIRED_TOP_KEYS:
        if key not in data or data[key] in (None, "", [], {}):
            errors.append(f"missing or empty top-level key: '{key}'")
    if "stakeholders" in data and data["stakeholders"] and not isinstance(data["stakeholders"], list):
        errors.append("'stakeholders' must be a list")
    if "activities" in data and data["activities"] and not isinstance(data["activities"], list):
        errors.append("'activities' must be a list")
    return errors


def check_stakeholders(stakeholders: list[Any]) -> tuple[list[str], list[str], set[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    codes: set[str] = set()
    for pos, sh in enumerate(stakeholders):
        if not isinstance(sh, dict):
            errors.append(f"stakeholders[{pos}]: must be a mapping")
            continue
        code = sh.get("code")
        if not code:
            errors.append(f"stakeholders[{pos}]: missing 'code'")
        else:
            if code in codes:
                errors.append(f"stakeholders[{pos}]: duplicate code '{code}'")
            codes.add(code)
        if not sh.get("role"):
            errors.append(f"stakeholders[{pos}] ({code}): missing 'role'")
        named = sh.get("named")
        if not isinstance(named, str) or named.strip().lower() in PLACEHOLDER_NAMES:
            warnings.append(
                f"stakeholders[{pos}] ({code}): no named individual — surface as a project risk"
            )
    return errors, warnings, codes


def _resolvable(repo_root: Path, ref: str) -> bool:
    """A reference that looks like a repo path must exist on disk."""
    if "/" not in ref or ref.startswith(("http://", "https://", "(")):
        return True
    return (repo_root / ref).exists()


def check_activity(
    pos: int,
    row: Any,
    stakeholder_codes: set[str],
    repo_root: Path,
) -> tuple[list[str], list[str], str, str]:
    """Return (errors, warnings, activity_slug, row_id)."""
    errors: list[str] = []
    warnings: list[str] = []
    if not isinstance(row, dict):
        return [f"activities[{pos}]: must be a mapping"], warnings, "", ""

    row_id = str(row.get("id") or "")
    slug = str(row.get("activity") or "")
    label = row_id or slug or f"<activity {pos}>"

    if not row_id:
        errors.append(f"activities[{pos}] ({label}): missing 'id'")
    if not slug:
        errors.append(f"activities[{pos}] ({label}): missing 'activity' slug")
    elif slug not in REQUIRED_ACTIVITIES:
        errors.append(
            f"activities[{pos}] ({label}): activity '{slug}' is not one of the required slugs "
            f"({', '.join(REQUIRED_ACTIVITIES)})"
        )

    cells = row.get("cells")
    if not isinstance(cells, dict):
        errors.append(f"activities[{pos}] ({label}): 'cells' must be a mapping")
        return errors, warnings, slug, row_id

    a_holders: list[str] = []
    c_holders: list[str] = []
    r_holders: list[str] = []

    for code, value in cells.items():
        if value is None:
            value = ""
        if not isinstance(value, str):
            errors.append(
                f"activities[{pos}] ({label}) cell '{code}': value must be a string from "
                f"{sorted(v for v in VALID_CELL_VALUES if v)}"
            )
            continue
        stripped = value.strip()
        normalized = stripped.upper() if stripped not in ("-", "--", "—") else stripped
        if normalized not in VALID_CELL_VALUES:
            errors.append(
                f"activities[{pos}] ({label}) cell '{code}': invalid value '{value}' "
                f"(must be one of R / A / C / I / - / empty)"
            )
            continue
        if normalized == "A":
            a_holders.append(code)
        elif normalized == "C":
            c_holders.append(code)
        elif normalized == "R":
            r_holders.append(code)
        if code not in stakeholder_codes and normalized in INVOLVED_VALUES:
            warnings.append(
                f"activities[{pos}] ({label}) cell '{code}': stakeholder code not in roster"
            )

    if len(a_holders) == 0:
        errors.append(f"activities[{pos}] ({label}): no A — every activity must have exactly one A")
    elif len(a_holders) > 1:
        errors.append(
            f"activities[{pos}] ({label}): {len(a_holders)} As ({', '.join(a_holders)}) — "
            "exactly one A allowed per activity"
        )

    a_and_c = sorted(set(a_holders) & set(c_holders))
    if a_and_c:
        errors.append(
            f"activities[{pos}] ({label}): role(s) {a_and_c} are both A and C — "
            "a Consulted role cannot also be Accountable"
        )

    a_and_r = sorted(set(a_holders) & set(r_holders))
    if a_and_r:
        warnings.append(
            f"activities[{pos}] ({label}): role(s) {a_and_r} are both A and R — allowed, but if "
            "most rows look like this the matrix delegates nothing"
        )

    if not r_holders:
        errors.append(
            f"activities[{pos}] ({label}): no R — every activity must have at least one Responsible"
        )

    escalation = row.get("escalation")
    if not isinstance(escalation, dict):
        errors.append(
            f"activities[{pos}] ({label}): no escalation rule "
            "(need trigger + target + time_box_business_days)"
        )
    else:
        for key in REQUIRED_ESCALATION_KEYS:
            if key not in escalation or escalation[key] in (None, ""):
                errors.append(f"activities[{pos}] ({label}): escalation rule missing '{key}'")
        tb = escalation.get("time_box_business_days")
        if isinstance(tb, bool) or not isinstance(tb, (int, float)):
            if tb not in (None, ""):
                errors.append(
                    f"activities[{pos}] ({label}): escalation 'time_box_business_days' "
                    f"must be a number, got '{tb}'"
                )
        elif tb <= 0:
            errors.append(
                f"activities[{pos}] ({label}): escalation 'time_box_business_days' must be > 0"
            )

    executed_by = row.get("executed_by")
    refs = executed_by if isinstance(executed_by, list) else [executed_by] if executed_by else []
    for ref in refs:
        if isinstance(ref, str) and not _resolvable(repo_root, ref):
            warnings.append(
                f"activities[{pos}] ({label}): executed_by '{ref}' does not resolve under {repo_root}"
            )

    return errors, warnings, slug, row_id


def check_escalation_path(path_rows: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(path_rows, list) or not path_rows:
        return ["'escalation_path' must be a non-empty list of levels"]
    for pos, level in enumerate(path_rows):
        if not isinstance(level, dict):
            errors.append(f"escalation_path[{pos}]: must be a mapping")
            continue
        for key in REQUIRED_ESCALATION_PATH_KEYS:
            if key not in level or level[key] in (None, ""):
                errors.append(f"escalation_path[{pos}]: missing '{key}'")
    return errors


def check_refusal_map(data: dict[str, Any], stakeholder_codes: set[str]) -> list[str]:
    warnings: list[str] = []
    rmap = data.get("refusal_code_map")
    if rmap is None:
        return [
            "no 'refusal_code_map' present — runtime agents that emit REFUSAL_* codes "
            "will not have a routing target"
        ]
    if not isinstance(rmap, dict):
        return ["'refusal_code_map' must be a mapping"]
    for code, entry in rmap.items():
        if not isinstance(entry, dict):
            warnings.append(f"refusal_code_map['{code}']: must be a mapping")
            continue
        ping = entry.get("ping")
        if not ping:
            warnings.append(f"refusal_code_map['{code}']: missing 'ping' (the named A to page)")
        elif (
            isinstance(ping, str)
            and not ping.startswith("(")  # "(matching A)" placeholders are intentional
            and ping not in stakeholder_codes
        ):
            warnings.append(
                f"refusal_code_map['{code}']: 'ping' value '{ping}' not in stakeholder roster"
            )
    return warnings


def lint_file(path: Path, repo_root: Path) -> tuple[list[str], list[str]]:
    data = load_artefact(path)
    errors: list[str] = []
    warnings: list[str] = []

    errors.extend(check_top_level(data))
    if errors:
        return errors, warnings

    sh_errors, sh_warnings, codes = check_stakeholders(data["stakeholders"])
    errors.extend(sh_errors)
    warnings.extend(sh_warnings)

    seen_slugs: set[str] = set()
    seen_ids: set[str] = set()
    for pos, row in enumerate(data["activities"]):
        row_errors, row_warnings, slug, row_id = check_activity(pos, row, codes, repo_root)
        errors.extend(row_errors)
        warnings.extend(row_warnings)
        if slug:
            seen_slugs.add(slug)
        if row_id:
            if row_id in seen_ids:
                errors.append(f"activities[{pos}]: duplicate id '{row_id}'")
            seen_ids.add(row_id)

    for required in REQUIRED_ACTIVITIES:
        if required not in seen_slugs:
            errors.append(
                f"required activity '{required}' has no row — that decision has no accountable owner"
            )

    errors.extend(check_escalation_path(data.get("escalation_path")))
    warnings.extend(check_refusal_map(data, codes))
    return errors, warnings


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Lint a Salesforce-project RACI artefact (YAML or JSON).",
    )
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--file", help="Path to a single RACI YAML or JSON artefact.")
    source.add_argument(
        "--manifest-dir",
        help="Directory to scan for raci*.yaml / raci*.yml / raci*.json artefacts.",
    )
    parser.add_argument(
        "--json",
        help="Deprecated alias for --file (kept so older runbooks keep working).",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as errors (non-zero exit on warnings).",
    )
    parser.add_argument(
        "--repo-root",
        default=".",
        help="Root used to resolve executed_by repo paths (default: current directory).",
    )
    return parser.parse_args()


def collect_targets(args: argparse.Namespace) -> list[Path]:
    if args.manifest_dir:
        root = Path(args.manifest_dir)
        if not root.is_dir():
            _die(f"not a directory: {root}")
        targets = sorted(
            p
            for p in root.rglob("*")
            if p.is_file()
            and p.name.lower().startswith("raci")
            and p.suffix.lower() in (".yaml", ".yml", ".json")
        )
        if not targets:
            _die(f"no raci*.yaml|yml|json artefact found under {root}")
        return targets
    single = args.file or args.json
    if not single:
        _die("pass --file <artefact> or --manifest-dir <dir>")
    return [Path(single)]


def report(path: Path, errors: list[str], warnings: list[str]) -> None:
    if not errors and not warnings:
        print(f"OK: {path} — RACI artefact is valid.")
        return
    if errors:
        print(f"{path}: ERRORS ({len(errors)}):", file=sys.stderr)
        for item in errors:
            print(f"  ERROR: {item}", file=sys.stderr)
    if warnings:
        print(f"{path}: WARNINGS ({len(warnings)}):", file=sys.stderr)
        for item in warnings:
            print(f"  WARN: {item}", file=sys.stderr)
    if not errors:
        print(f"OK with warnings: {path}")


def main() -> int:
    args = parse_args()
    targets = collect_targets(args)
    repo_root = Path(args.repo_root)

    total_errors = 0
    total_warnings = 0
    for target in targets:
        errors, warnings = lint_file(target, repo_root)
        report(target, errors, warnings)
        total_errors += len(errors)
        total_warnings += len(warnings)

    if total_errors:
        return 1
    if args.strict and total_warnings:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
