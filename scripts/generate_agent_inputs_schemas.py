#!/usr/bin/env python3
"""Generate inputs.schema.json for runtime agents that lack one.

Parses the "## Inputs" table in each AGENT.md and emits a JSON Schema
(draft 2020-12) under agents/<slug>/inputs.schema.json. Only writes when
a schema is missing — never overwrites hand-crafted schemas.

Type inference is best-effort from the Example column:
  - example contains "A | B | C" with backticks  -> enum of strings
  - example is true/false                         -> boolean
  - example is digits or N_NNN formatted          -> integer
  - example starts with "["                        -> array
  - otherwise                                      -> string

Required detection: first token of the Required column, lowercased.
  - "yes"                                          -> required
  - "no" | "optional" | "alt" | "conditional"      -> not required
  - column missing                                 -> all required
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
AGENTS_DIR = REPO_ROOT / "agents"

SECTION_RE = re.compile(r"^##\s+.*Inputs.*$", re.M)
NEXT_SECTION_RE = re.compile(r"^##\s+", re.M)


def parse_frontmatter_class(path: Path) -> tuple[str, str]:
    """Cheap frontmatter reader — returns (class, status)."""
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return "", ""
    end = text.find("\n---", 3)
    if end < 0:
        return "", ""
    fm = text[3:end]
    cls = re.search(r"^class:\s*([^\s#]+)", fm, re.M)
    st = re.search(r"^status:\s*([^\s#]+)", fm, re.M)
    return (cls.group(1).strip() if cls else ""), (st.group(1).strip() if st else "")


def extract_inputs_section(agent_md: Path) -> str | None:
    text = agent_md.read_text(encoding="utf-8")
    m = SECTION_RE.search(text)
    if not m:
        return None
    start = m.end()
    nxt = NEXT_SECTION_RE.search(text, start + 1)
    return text[start : nxt.start() if nxt else len(text)]


PIPE_PLACEHOLDER = "\x00PIPE\x00"


def _split_cells(line: str) -> list[str]:
    """Split a markdown table row, respecting `\\|` escaped pipes inside cells."""
    body = line.strip().strip("|")
    # Preserve escaped pipes so they don't act as column separators.
    body = body.replace(r"\|", PIPE_PLACEHOLDER)
    cells = [c.strip().replace(PIPE_PLACEHOLDER, "|") for c in body.split("|")]
    return cells


def parse_table(section: str) -> list[dict]:
    """Return a list of {name, required, example, raw_name}."""
    lines = [ln.rstrip() for ln in section.splitlines()]
    rows: list[dict] = []
    headers: list[str] | None = None
    for i, ln in enumerate(lines):
        if not ln.strip().startswith("|"):
            continue
        cells = _split_cells(ln)
        if headers is None:
            # Header row: must contain "Input"
            if any("input" in c.lower() for c in cells):
                headers = [c.lower() for c in cells]
            continue
        # Separator row like |---|---|
        if all(set(c) <= set("-: ") for c in cells) and any("-" in c for c in cells):
            continue
        if len(cells) < 2:
            continue
        row: dict[str, str] = {}
        for h, c in zip(headers, cells):
            row[h] = c
        # Normalize
        raw_name = row.get("input", "").strip()
        if not raw_name:
            continue
        required_col = row.get("required", "").strip().lower()
        # Some tables only have Input|Example
        example = row.get("example", "")
        rows.append({
            "raw_name": raw_name,
            "required": required_col,
            "example": example,
        })
    return rows


def split_compound_names(raw: str) -> list[str]:
    """A cell like `` `a` or `b` `` -> ["a", "b"]. Also handles "`a` / `b`"."""
    names = re.findall(r"`([A-Za-z_][A-Za-z0-9_]*)`", raw)
    if names:
        return names
    bare = raw.strip().strip("*")
    return [bare] if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", bare) else []


def extract_enum(example: str) -> list[str] | None:
    """Find `A` \\| `B` \\| `C` pattern."""
    # Normalize escaped pipes used in markdown tables.
    cleaned = example.replace(r"\|", "|")
    # Must contain at least two backticked tokens separated by |
    if "|" not in cleaned:
        return None
    # Enum token class: identifiers, hyphens, dots, and optional wrapping quotes.
    token_re = r'"?([A-Za-z0-9_\-:.]+)"?'
    chain_re = rf"`{token_re}`(?:\s*\|\s*`{token_re}`)+"
    if not re.search(chain_re, cleaned):
        return None
    tokens = re.findall(rf"`{token_re}`", cleaned)
    # Deduplicate while preserving order; drop obvious non-enum junk.
    seen: list[str] = []
    for t in tokens:
        if t not in seen and re.fullmatch(r"[A-Za-z0-9_\-:.]+", t):
            seen.append(t)
    return seen if len(seen) >= 2 else None


def infer_type(example: str, name: str) -> tuple[str, list[str] | None]:
    """Return (json_type, enum_values_or_None)."""
    enum_vals = extract_enum(example)
    if enum_vals:
        return "string", enum_vals
    # Prefer the first backticked token (typical example marker) for type detection;
    # fall back to the trimmed cell.
    first_tick = re.search(r"`([^`]+)`", example)
    sample = first_tick.group(1) if first_tick else example.strip().strip("`")
    ex = sample.strip()
    low = ex.lower()
    if low in ("true", "false"):
        return "boolean", None
    # Name-prefix + boolean-ish example: "default `true`", "default `false`", or blank.
    bool_prefix = re.match(r"^(include_|is_|has_|enable_|disable_|reuse_)", name)
    if bool_prefix and (
        ex == ""
        or re.search(r"default\s+`?(true|false)`?", example, re.I)
        or low in ("true", "false")
    ):
        return "boolean", None
    # Integer: digits, possibly with thousands separators.
    if re.fullmatch(r"[\d_,]+", ex) and any(ch.isdigit() for ch in ex):
        return "integer", None
    if ex.startswith("["):
        return "array", None
    # Arrays hinted by clearly-plural name suffix.
    plural_hints = ("_paths", "_names", "_ids", "_fields", "_objects", "_classes",
                    "_rules", "_tests", "_tags", "_steps", "_aliases", "_types",
                    "_scopes", "_flows", "_triggers")
    if any(name.endswith(h) for h in plural_hints):
        return "array", None
    return "string", None


def first_token(s: str) -> str:
    s = s.strip()
    return s.split()[0].rstrip(",:;.") if s else ""


def clean_example(example: str) -> str:
    """Strip markdown noise for the schema example/description."""
    return example.replace(r"\|", "|").strip()


def build_property(name: str, required_col: str, example: str) -> dict:
    json_type, enum_vals = infer_type(example, name)
    prop: dict = {"type": json_type}
    parts: list[str] = []
    if example:
        parts.append(f"Example from AGENT.md: {clean_example(example)}")
    if required_col:
        parts.append(f"Required column: '{required_col}'.")
    if not parts:
        parts.append(f"Input `{name}` as documented in AGENT.md.")
    prop["description"] = " ".join(parts)
    if enum_vals:
        prop["enum"] = enum_vals
    if json_type == "array":
        prop["items"] = {"type": "string"}
    if example.strip():
        # Parse example into a stable scalar where sensible.
        ex = clean_example(example)
        # Strip leading backticked token as the canonical example value.
        m = re.match(r"`([^`]+)`", ex)
        sample = m.group(1) if m else ex
        if json_type == "boolean":
            prop["example"] = sample.lower() == "true"
        elif json_type == "integer":
            digits = re.sub(r"[_,]", "", sample)
            if digits.isdigit():
                prop["example"] = int(digits)
        elif json_type == "array":
            # Best-effort: leave as string form in description only.
            pass
        else:
            prop["example"] = sample
    return prop


def is_required(required_col: str) -> bool:
    if not required_col:
        # If the table omits the Required column, assume required.
        return True
    tok = first_token(required_col)
    if tok.startswith("yes"):
        return True
    if tok in ("no", "optional", "alt", "conditional"):
        return False
    # Fallback: not required if it starts with common optional markers.
    return False


def build_schema(agent_slug: str, rows: list[dict]) -> dict:
    properties: dict = {}
    required: list[str] = []
    compound_notes: list[str] = []
    for row in rows:
        names = split_compound_names(row["raw_name"])
        if not names:
            # Couldn't parse name — skip silently (keeps schema conservative).
            continue
        req = is_required(row["required"])
        if len(names) > 1:
            # One-of group: emit each as optional + describe the constraint.
            compound_notes.append(
                f"At least one of {', '.join('`' + n + '`' for n in names)} must be provided."
            )
            for n in names:
                if n in properties:
                    continue
                prop = build_property(n, row["required"], row["example"])
                prop["description"] = (
                    prop["description"]
                    + f" One of a mutually-exclusive group: {', '.join(names)}."
                )
                properties[n] = prop
        else:
            n = names[0]
            if n in properties:
                continue
            properties[n] = build_property(n, row["required"], row["example"])
            if req:
                required.append(n)

    schema: dict = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"https://sfskills.local/agents/{agent_slug}/inputs.schema.json",
        "title": f"{agent_slug} inputs",
        "description": (
            "Typed inputs for the "
            f"{agent_slug} runtime agent. Machine-readable mirror of the Inputs table in "
            "AGENT.md. The harness validates caller-supplied input packets against this "
            "schema before the agent begins work; validation failures surface the offending "
            "field to the caller rather than failing mid-run."
        ),
        "type": "object",
        "properties": properties,
    }
    if required:
        schema["required"] = required
    if compound_notes:
        schema["description"] += " " + " ".join(compound_notes)
    return schema


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true", help="Print actions; don't write.")
    ap.add_argument("--agent", help="Limit to one agent slug.")
    args = ap.parse_args()

    agent_mds = sorted(AGENTS_DIR.glob("*/AGENT.md"))
    generated = 0
    skipped_existing = 0
    skipped_no_inputs = 0
    errors: list[tuple[str, str]] = []

    for md in agent_mds:
        slug = md.parent.name
        if args.agent and slug != args.agent:
            continue
        cls, status = parse_frontmatter_class(md)
        if cls != "runtime" or status == "deprecated":
            continue
        out = md.parent / "inputs.schema.json"
        if out.exists():
            skipped_existing += 1
            continue
        section = extract_inputs_section(md)
        if section is None:
            skipped_no_inputs += 1
            errors.append((slug, "no Inputs section found"))
            continue
        rows = parse_table(section)
        if not rows:
            skipped_no_inputs += 1
            errors.append((slug, "Inputs section present but no parseable rows"))
            continue
        schema = build_schema(slug, rows)
        if not schema["properties"]:
            errors.append((slug, "parsed rows but no properties produced"))
            continue
        if args.dry_run:
            print(f"WOULD WRITE {out.relative_to(REPO_ROOT)} "
                  f"({len(schema['properties'])} props, "
                  f"{len(schema.get('required', []))} required)")
        else:
            out.write_text(
                json.dumps(schema, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            print(f"wrote {out.relative_to(REPO_ROOT)} "
                  f"({len(schema['properties'])} props, "
                  f"{len(schema.get('required', []))} required)")
        generated += 1

    print()
    print(f"generated: {generated}")
    print(f"skipped (already had schema): {skipped_existing}")
    print(f"skipped (no Inputs section parseable): {skipped_no_inputs}")
    if errors:
        print("errors:")
        for slug, msg in errors:
            print(f"  - {slug}: {msg}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
