#!/usr/bin/env python3
"""Lint a territory design before anyone builds it in Setup.

The artefact this skill produces is a territory-design file: the territories, their types and
priorities, their parents, the assignment rules or the explicit decision to assign manually, the
per-object access levels, and the realignment plan. ``templates/territory-design.yaml`` is the
skeleton; ``references/worked-examples.md`` §8 is a filled example.

The linter reads that design file and, where the same folder also holds ``Territory2Rule`` metadata,
checks the XML against the same rules. It never touches an org.

Checks (ERROR unless marked WARN):

  Design file
  ~~~~~~~~~~~
   1. ``territories`` and ``territory_types`` are present and non-empty.
   2. Every territory type has an integer ``priority``, and priorities are unique across types
      ("The priority field value on each territory type must be unique" — Metadata API Developer
      Guide, Territory2Type › priority).
   3. Every territory names a ``type`` that is declared in ``territory_types``.
   4. Every territory has a ``parent`` unless it is marked ``root: true``; exactly one root is
      expected (WARN on more than one); a named parent must resolve to a declared territory, and
      the parent chain must not cycle.
   5. Every territory carries at least one entry under ``rules`` OR ``manual_assignment: true``
      with a non-empty ``manual_assignment_owner``. A territory with neither is a coverage gap.
   6. Access levels are inside the documented enums: ``account`` in Read/Edit/All (there is no
      None); ``opportunity``/``case``/``contact`` in None/Read/Edit. Omitting a key is allowed and
      means "inherit the Territory2Settings default".
   7. No two rules inside one territory share an identical criteria set (same field, operation and
      value across the same number of items) — a duplicate assigns nothing extra and hides which
      rule the coverage actually came from.
   8. A rule has at most 10 rule items ("A territory rule can have up to 10 rule items" — Metadata
      API, Territory2Rule › Usage), every ``operation`` is in the documented enum, and any
      ``boolean_filter`` numbering starts at 1, is contiguous, and references no item beyond the
      ones present.
   9. A ``realignment`` block is present and names a ``cutover_date`` and a ``rule_runner`` — the
      rule run is user-initiated ("Rules can't be run via Metadata API") so it needs an owner.
  10. WARN: a territory with no ``forecast_reader``; a design with more than one root.

  Territory2Rule XML found alongside the design
  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
  11. Every ``*.territory2Rule*`` file parses as XML.
  12. Its ``ruleItems`` count is at most 10, and each ``operation`` is in the documented enum.
  13. Its ``booleanFilter``, when present, starts at 1, is contiguous, and stays inside the item
      count.
  14. WARN: ``objectType`` other than ``Account`` (the Metadata API guide documents Account as the
      object for Territory2Rule; Lead assignment is a separate Territory2Settings switch).

Stdlib only. Understands a restricted block-YAML subset: mappings, nested mappings, sequences of
mappings, inline ``[a, b]`` lists, quoted or bare scalars, ``#`` comments. Multi-line scalars
(``|``, ``>``), anchors and flow mappings are rejected with a parse error.

Usage:
    python3 check_territory_design_requirements.py --manifest-dir docs/design/fy27-territories/
    python3 check_territory_design_requirements.py --file territory-design.yaml
    python3 check_territory_design_requirements.py --file references/worked-examples.md

Exit code 0 when there are no ERRORs (WARNs may still print); 1 otherwise.
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# Metadata API Developer Guide, Territory2RuleItem > operation.
RULE_OPERATIONS = (
    "equals",
    "notEqual",
    "lessThan",
    "greaterThan",
    "lessOrEqual",
    "greaterOrEqual",
    "contains",
    "notContain",
    "startsWith",
    "includes",
    "excludes",
    "within",
)

# Metadata API Developer Guide, Territory2 > accountAccessLevel / opportunityAccessLevel /
# caseAccessLevel / contactAccessLevel. Note there is no None for accounts.
ACCESS_ENUMS = {
    "account": ("Read", "Edit", "All"),
    "opportunity": ("None", "Read", "Edit"),
    "case": ("None", "Read", "Edit"),
    "contact": ("None", "Read", "Edit"),
}

# Metadata API Developer Guide, Territory2Rule > Usage.
MAX_RULE_ITEMS = 10

REALIGNMENT_REQUIRED_KEYS = ("cutover_date", "rule_runner")


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
        raise ParseError("multi-line scalars (| and >) are not supported in this design format")
    if raw[0] == "{":
        raise ParseError("flow mappings ({...}) are not supported in this design format")
    if raw[0] in ("&", "*"):
        raise ParseError("anchors and aliases are not supported in this design format")
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
                raise ParseError("line {}: unexpected indent inside a sequence".format(lineno))
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
            raise ParseError("line {}: unexpected indent in a mapping".format(lineno))
        stripped = line.strip()
        if stripped.startswith("- "):
            break
        if ":" not in stripped:
            raise ParseError("line {}: expected 'key: value', got {!r}".format(lineno, stripped))
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


def parse_design_yaml(text: str) -> dict:
    lines: list[tuple[int, str]] = []
    for i, raw in enumerate(text.splitlines(), start=1):
        if raw.strip() in ("---", "..."):
            continue
        cleaned = _strip_comment(raw)
        if not cleaned.strip():
            continue
        if "\t" in cleaned[: _indent_of(cleaned) + 1]:
            raise ParseError("line {}: tab used for indentation".format(i))
        lines.append((i, cleaned))
    if not lines:
        return {}
    doc, _ = _parse_block(lines, 0, _indent_of(lines[0][1]))
    return doc if isinstance(doc, dict) else {"territories": doc}


def extract_yaml_blocks(text: str) -> list[str]:
    """Return the bodies of fenced ```yaml blocks that declare a `territories:` key."""
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
            if re.search(r"^\s*territories:\s*$", body, re.MULTILINE):
                blocks.append(body)
            current = None
            continue
        current.append(line)
    return blocks


# --------------------------------------------------------------------------- small helpers


def _as_list(value: object) -> list:
    if isinstance(value, list):
        return value
    if isinstance(value, dict):
        return [value]
    return []


def _text(value: object) -> str:
    return "" if value is None else str(value).strip()


def _is_true(value: object) -> bool:
    return _text(value).lower() in ("true", "yes", "y", "1")


def _is_int(value: object) -> bool:
    raw = _text(value)
    if not raw:
        return False
    if raw[0] in ("+", "-"):
        raw = raw[1:]
    return raw.isdigit()


def _strip_ns(tag: str) -> str:
    return tag.split("}")[-1] if "}" in tag else tag


def child_text(element, tag: str) -> str | None:
    """First direct child with this tag, as text. Returns None when absent.

    Never write ``el.find(a) or el.find(b)`` — a childless Element is falsy, so that idiom
    discards real matches. Test ``is not None`` instead, which is what this helper does for you.
    """
    if element is None:
        return None
    for child in element:
        if _strip_ns(child.tag) == tag:
            return (child.text or "").strip()
    return None


def children(element, tag: str) -> list:
    if element is None:
        return []
    return [child for child in element if _strip_ns(child.tag) == tag]


def check_boolean_filter(expr: str, item_count: int, origin: str) -> list[tuple[str, str]]:
    """booleanFilter numbering must start at 1, be contiguous, and stay inside the item count."""
    findings: list[tuple[str, str]] = []
    numbers = sorted({int(n) for n in re.findall(r"\d+", expr)})
    if not numbers:
        findings.append(("ERROR", "{}: boolean filter {!r} references no rule items".format(origin, expr)))
        return findings
    if numbers[0] != 1:
        findings.append((
            "ERROR",
            "{}: boolean filter {!r} starts at {} — numbering \"must start at 1 and must be "
            "contiguous\" (Metadata API, Territory2Rule > booleanFilter)".format(origin, expr, numbers[0]),
        ))
    if numbers != list(range(numbers[0], numbers[0] + len(numbers))):
        findings.append((
            "ERROR",
            "{}: boolean filter {!r} skips a number — numbering must be contiguous".format(origin, expr),
        ))
    if item_count and numbers[-1] > item_count:
        findings.append((
            "ERROR",
            "{}: boolean filter {!r} references item {} but the rule has {} item(s)".format(
                origin, expr, numbers[-1], item_count
            ),
        ))
    return findings


# --------------------------------------------------------------------------- design-file checks


def check_types(doc: dict, origin: str) -> tuple[dict, list[tuple[str, str]]]:
    findings: list[tuple[str, str]] = []
    types = _as_list(doc.get("territory_types"))
    known: dict[str, str] = {}
    if not types:
        findings.append((
            "ERROR",
            "{}: no territory_types declared — every Territory2 must have a Territory2Type, and the "
            "type is where the priority integer lives".format(origin),
        ))
        return known, findings

    seen_priority: dict[str, str] = {}
    for entry in types:
        if not isinstance(entry, dict):
            findings.append(("ERROR", "{}: territory_types entry is not a mapping".format(origin)))
            continue
        name = _text(entry.get("name"))
        if not name:
            findings.append(("ERROR", "{}: a territory type has no name".format(origin)))
            continue
        priority = entry.get("priority")
        if not _is_int(priority):
            findings.append((
                "ERROR",
                "{}: territory type '{}' has no integer priority. priority is Required on "
                "Territory2Type and the HIGHEST integer wins opportunity territory "
                "assignment".format(origin, name),
            ))
        else:
            key = _text(priority)
            if key in seen_priority:
                findings.append((
                    "ERROR",
                    "{}: territory types '{}' and '{}' share priority {} — \"The priority field "
                    "value on each territory type must be unique\", and a tie assigns no territory "
                    "to the opportunity".format(origin, seen_priority[key], name, key),
                ))
            else:
                seen_priority[key] = name
        known[name] = _text(priority)
    return known, findings


def check_access(territory: dict, name: str, origin: str) -> list[tuple[str, str]]:
    findings: list[tuple[str, str]] = []
    access = territory.get("access")
    if not isinstance(access, dict):
        if access not in (None, ""):
            findings.append(("ERROR", "{}: territory '{}' has a malformed access block".format(origin, name)))
        return findings
    for obj, value in access.items():
        key = obj.strip().lower()
        if key not in ACCESS_ENUMS:
            findings.append((
                "WARN",
                "{}: territory '{}' sets access for '{}', which is not one of "
                "account/opportunity/case/contact".format(origin, name, obj),
            ))
            continue
        level = _text(value)
        if not level:
            continue
        if level not in ACCESS_ENUMS[key]:
            findings.append((
                "ERROR",
                "{}: territory '{}' sets {} access to '{}'. Valid values are {} (Metadata API, "
                "Territory2). Omit the key to inherit the Territory2Settings default; use the "
                "Metadata API spelling, not the Setup label".format(
                    origin, name, key, level, "/".join(ACCESS_ENUMS[key])
                ),
            ))
    return findings


def _criteria_signature(rule: dict) -> tuple:
    items = _as_list(rule.get("items"))
    signature = []
    for item in items:
        if not isinstance(item, dict):
            continue
        signature.append((
            _text(item.get("field")).lower(),
            _text(item.get("operation")).lower(),
            _text(item.get("value")).lower(),
        ))
    return tuple(sorted(signature))


def check_rules(territory: dict, name: str, origin: str) -> list[tuple[str, str]]:
    findings: list[tuple[str, str]] = []
    rules = _as_list(territory.get("rules"))
    seen: dict[tuple, str] = {}

    for rule in rules:
        if not isinstance(rule, dict):
            findings.append(("ERROR", "{}: territory '{}' has a rule entry that is not a mapping".format(origin, name)))
            continue
        rule_name = _text(rule.get("name")) or "<unnamed>"
        where = "{}: territory '{}' rule '{}'".format(origin, name, rule_name)
        items = _as_list(rule.get("items"))

        if not items:
            findings.append(("ERROR", "{} has no rule items".format(where)))
        if len(items) > MAX_RULE_ITEMS:
            findings.append((
                "ERROR",
                "{} has {} rule items. \"A territory rule can have up to {} rule items\" "
                "(Metadata API, Territory2Rule > Usage) — collapse enumerations with the "
                "'includes' operation or move the segmentation to a proxy field on "
                "Account".format(where, len(items), MAX_RULE_ITEMS),
            ))

        for index, item in enumerate(items, start=1):
            if not isinstance(item, dict):
                findings.append(("ERROR", "{} item {} is not a mapping".format(where, index)))
                continue
            if not _text(item.get("field")):
                findings.append(("ERROR", "{} item {} has no field".format(where, index)))
            operation = _text(item.get("operation"))
            if not operation:
                findings.append(("ERROR", "{} item {} has no operation".format(where, index)))
            elif operation not in RULE_OPERATIONS:
                findings.append((
                    "ERROR",
                    "{} item {} uses operation '{}', which is not in the documented enum: {} "
                    "(Metadata API, Territory2RuleItem > operation)".format(
                        where, index, operation, ", ".join(RULE_OPERATIONS)
                    ),
                ))
            if "value" not in item:
                findings.append((
                    "WARN",
                    "{} item {} has no value key — write an explicit empty value if a blank field "
                    "is the criterion".format(where, index),
                ))

        boolean_filter = _text(rule.get("boolean_filter"))
        if boolean_filter:
            findings.extend(check_boolean_filter(boolean_filter, len(items), where))
        elif len(items) > 1:
            findings.append((
                "WARN",
                "{} has {} items and no boolean_filter — the implicit combination is not stated in "
                "the design, and rule item order is positional".format(where, len(items)),
            ))

        signature = _criteria_signature(rule)
        if signature and signature in seen:
            findings.append((
                "ERROR",
                "{} has the same criteria as rule '{}' on the same territory — a duplicate assigns "
                "nothing extra and hides which rule produced the coverage".format(where, seen[signature]),
            ))
        elif signature:
            seen[signature] = rule_name

    if not rules:
        if _is_true(territory.get("manual_assignment")):
            if not _text(territory.get("manual_assignment_owner")):
                findings.append((
                    "ERROR",
                    "{}: territory '{}' is manual-assignment but names no manual_assignment_owner. "
                    "Manual assignment lands as ObjectTerritory2Association.AssociationCause = "
                    "Territory2Manual and needs a person who maintains it".format(origin, name),
                ))
        else:
            findings.append((
                "ERROR",
                "{}: territory '{}' has neither an assignment rule nor manual_assignment: true. "
                "Accounts reach a territory only by rule or by manual assignment, so this territory "
                "is a coverage gap".format(origin, name),
            ))
    return findings


def check_hierarchy(territories: list, origin: str) -> list[tuple[str, str]]:
    findings: list[tuple[str, str]] = []
    parents: dict[str, str] = {}
    roots: list[str] = []

    names = set()
    for territory in territories:
        if isinstance(territory, dict):
            name = _text(territory.get("name"))
            if name:
                names.add(name)

    for territory in territories:
        if not isinstance(territory, dict):
            continue
        name = _text(territory.get("name"))
        if not name:
            continue
        parent = _text(territory.get("parent"))
        if _is_true(territory.get("root")):
            roots.append(name)
            if parent:
                findings.append((
                    "ERROR",
                    "{}: territory '{}' is marked root but also names a parent '{}'".format(origin, name, parent),
                ))
            continue
        if not parent:
            findings.append((
                "ERROR",
                "{}: territory '{}' has no parent and is not marked 'root: true'. Territory2 has "
                "exactly one parenting mechanism (parentTerritory, by developer name); an orphan "
                "silently sits outside every rollup".format(origin, name),
            ))
            continue
        if parent not in names:
            findings.append((
                "ERROR",
                "{}: territory '{}' names parent '{}', which is not declared in this "
                "design".format(origin, name, parent),
            ))
            continue
        parents[name] = parent

    if not roots:
        findings.append(("ERROR", "{}: no territory is marked 'root: true'".format(origin)))
    elif len(roots) > 1:
        findings.append((
            "WARN",
            "{}: {} territories are marked root ({}). A model normally has one".format(
                origin, len(roots), ", ".join(sorted(roots))
            ),
        ))

    for start in parents:
        seen = {start}
        node = parents.get(start)
        while node is not None:
            if node in seen:
                findings.append((
                    "ERROR",
                    "{}: territory '{}' is in a parent cycle through '{}'".format(origin, start, node),
                ))
                break
            seen.add(node)
            node = parents.get(node)
    return findings


def check_design(doc: dict, origin: str) -> list[tuple[str, str]]:
    findings: list[tuple[str, str]] = []
    known_types, type_findings = check_types(doc, origin)
    findings.extend(type_findings)

    territories = _as_list(doc.get("territories"))
    if not territories:
        findings.append(("ERROR", "{}: no territories declared".format(origin)))
        return findings

    seen_names: set[str] = set()
    for territory in territories:
        if not isinstance(territory, dict):
            findings.append(("ERROR", "{}: a territories entry is not a mapping".format(origin)))
            continue
        name = _text(territory.get("name"))
        if not name:
            findings.append(("ERROR", "{}: a territory has no name".format(origin)))
            continue
        if name in seen_names:
            findings.append(("ERROR", "{}: territory '{}' is declared twice".format(origin, name)))
        seen_names.add(name)

        type_name = _text(territory.get("type"))
        if not type_name:
            findings.append((
                "ERROR",
                "{}: territory '{}' has no type. Every Territory2 must have a Territory2Type, and "
                "the type carries the priority integer that decides opportunity territory "
                "assignment".format(origin, name),
            ))
        elif known_types and type_name not in known_types:
            findings.append((
                "ERROR",
                "{}: territory '{}' uses type '{}', which is not declared in "
                "territory_types".format(origin, name, type_name),
            ))

        if not _text(territory.get("forecast_reader")):
            findings.append((
                "WARN",
                "{}: territory '{}' names no forecast_reader — a hierarchy level nobody reads a "
                "forecast at is maintenance with no consumer".format(origin, name),
            ))

        findings.extend(check_access(territory, name, origin))
        findings.extend(check_rules(territory, name, origin))

    findings.extend(check_hierarchy(territories, origin))

    realignment = doc.get("realignment")
    if not isinstance(realignment, dict) or not realignment:
        findings.append((
            "ERROR",
            "{}: no realignment block. Archiving a model is one-way and a same-named archived model "
            "blocks a future deploy, so the plan to re-cut this model belongs in the design".format(origin),
        ))
    else:
        for key in REALIGNMENT_REQUIRED_KEYS:
            if not _text(realignment.get(key)):
                findings.append((
                    "ERROR",
                    "{}: realignment block has no '{}'. \"Rules can't be run via Metadata API\" "
                    "(Metadata API, Territory2Rule > Usage), so the run needs a named owner and a "
                    "date".format(origin, key),
                ))
    return findings


# --------------------------------------------------------------------------- XML checks


def check_rule_xml(path: Path) -> list[tuple[str, str]]:
    findings: list[tuple[str, str]] = []
    origin = path.name
    try:
        root = ET.parse(str(path)).getroot()
    except ET.ParseError as exc:
        findings.append(("ERROR", "{}: not well-formed XML ({})".format(origin, exc)))
        return findings

    items = children(root, "ruleItems")
    if not items:
        findings.append((
            "ERROR",
            "{}: Territory2Rule has no ruleItems — it deploys cleanly and assigns nothing".format(origin),
        ))
    if len(items) > MAX_RULE_ITEMS:
        findings.append((
            "ERROR",
            "{}: {} ruleItems. \"A territory rule can have up to {} rule items\" (Metadata API, "
            "Territory2Rule > Usage)".format(origin, len(items), MAX_RULE_ITEMS),
        ))

    for index, item in enumerate(items, start=1):
        field = child_text(item, "field")
        if field is None or not field:
            findings.append(("ERROR", "{}: ruleItem {} has no <field>".format(origin, index)))
        operation = child_text(item, "operation")
        if operation is None or not operation:
            findings.append(("ERROR", "{}: ruleItem {} has no <operation>".format(origin, index)))
        elif operation not in RULE_OPERATIONS:
            findings.append((
                "ERROR",
                "{}: ruleItem {} uses operation '{}', which is not in the documented enum: {} "
                "(Metadata API, Territory2RuleItem > operation)".format(
                    origin, index, operation, ", ".join(RULE_OPERATIONS)
                ),
            ))

    boolean_filter = child_text(root, "booleanFilter")
    if boolean_filter:
        findings.extend(check_boolean_filter(boolean_filter, len(items), origin))

    object_type = child_text(root, "objectType")
    if object_type is not None and object_type and object_type != "Account":
        findings.append((
            "WARN",
            "{}: objectType is '{}'. The Metadata API guide documents Account for Territory2Rule; "
            "Lead assignment is a separate Territory2Settings.supportedObjects switch".format(
                origin, object_type
            ),
        ))
    return findings


# --------------------------------------------------------------------------- collection


def load_designs(paths: list[Path]) -> list[tuple[str, dict]]:
    designs: list[tuple[str, dict]] = []
    for path in paths:
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as exc:
            print("ISSUE: ERROR: cannot read {} ({})".format(path, exc))
            continue
        if path.suffix.lower() in (".yaml", ".yml"):
            if not re.search(r"^\s*territories:\s*$", text, re.MULTILINE):
                continue
            bodies = [text]
        elif path.suffix.lower() == ".md":
            bodies = extract_yaml_blocks(text)
        else:
            continue
        for index, body in enumerate(bodies):
            label = str(path) if len(bodies) == 1 else "{} (block {})".format(path, index + 1)
            try:
                designs.append((label, parse_design_yaml(body)))
            except ParseError as exc:
                print("ISSUE: ERROR: {}: {}".format(label, exc))
    return designs


def collect(args: argparse.Namespace) -> tuple[list[Path], list[Path]]:
    if args.file:
        target = Path(args.file)
        if not target.exists():
            print("ISSUE: ERROR: file not found: {}".format(target))
            sys.exit(1)
        return [target], []
    root = Path(args.manifest_dir)
    if not root.exists():
        print("ISSUE: ERROR: manifest directory not found: {}".format(root))
        sys.exit(1)
    design_files = sorted(
        p for p in root.rglob("*")
        if p.is_file() and p.suffix.lower() in (".yaml", ".yml", ".md")
    )
    rule_files = sorted(p for p in root.rglob("*") if p.is_file() and ".territory2Rule" in p.name)
    return design_files, rule_files


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Lint a territory design file (and any Territory2Rule XML beside it) against the "
            "documented Territory2 constraints. Reads files only; never contacts an org."
        )
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Directory holding the territory design file and any Territory2Rule XML (default: .).",
    )
    parser.add_argument("--file", help="Lint a single design file (.yaml/.yml/.md) instead.")
    args = parser.parse_args()

    design_files, rule_files = collect(args)
    designs = load_designs(design_files)

    findings: list[tuple[str, str]] = []
    if not designs:
        findings.append((
            "ERROR",
            "no territory design found. Expected a YAML file with a top-level 'territories:' key, "
            "or a markdown file containing a fenced yaml block with one. See "
            "templates/territory-design.yaml",
        ))
    for origin, doc in designs:
        findings.extend(check_design(doc, origin))
    for path in rule_files:
        findings.extend(check_rule_xml(path))

    errors = [f for f in findings if f[0] == "ERROR"]
    warns = [f for f in findings if f[0] == "WARN"]

    for level, message in errors + warns:
        print("ISSUE: {}: {}".format(level, message))

    if not findings:
        print("No territory design issues found.")
        return 0

    print("\n{} error(s), {} warning(s).".format(len(errors), len(warns)))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
