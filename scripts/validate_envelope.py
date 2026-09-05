#!/usr/bin/env python3
"""Validate one agent output envelope against `output-envelope.schema.json`.

    python3 scripts/validate_envelope.py <envelope.json> [...]

Prints `OK <path>` and exits 0 when the document validates; prints every
error (one per line, `ERROR <path>: <json-pointer>: <message>`) and exits 1
otherwise.

Why this exists: the envelope schema `$ref`s its sub-schemas by URN
(`urn:sfskills:observation`, `urn:sfskills:citation`), and a URN has no
retrievable location. A bare `Draft202012Validator(schema)` therefore raises
`Unresolvable` the moment an envelope carries a process observation or a
citation — which every real envelope does. The refs only resolve when the
sibling schemas are preloaded into a registry keyed by their `$id`. That
registry construction lives in exactly one other place in the repo
(`evals/agents/scripts/run_agent_evals.py`, `grade_envelope`); this module is
the standalone, reusable copy so agents in the build loop can check their own
envelope before writing it, without pulling in the eval runner.

Dependency: `jsonschema` (requirements.txt). `referencing` ships with
jsonschema >= 4.18 and is used when present; on older jsonschema the
`RefResolver` store is used instead, which resolves the same URNs.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

try:
    import jsonschema
except ImportError:  # pragma: no cover - environment without the documented dep
    print("ERROR: jsonschema is required (pip install -r requirements.txt)", file=sys.stderr)
    sys.exit(1)

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS_DIR = ROOT / "agents" / "_shared" / "schemas"
ENVELOPE_SCHEMA = "output-envelope.schema.json"

# Every schema the envelope $refs by URN. They are preloaded by `$id`; a URN
# is not fetchable, so an unresolved ref is a hard failure, not a warning.
REFERENCED_SCHEMAS = ("observation.schema.json", "citation.schema.json")


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def build_validator(schemas_dir: Path | None = None) -> Any:
    """A Draft 2020-12 validator whose URN `$ref`s resolve.

    Mirrors the registry construction in
    `evals/agents/scripts/run_agent_evals.py::grade_envelope`, with a
    `RefResolver` fallback for jsonschema < 4.18 (no `referencing` package).
    """
    schemas_dir = schemas_dir or SCHEMAS_DIR
    schema = _load(schemas_dir / ENVELOPE_SCHEMA)
    subs = []
    for rel in REFERENCED_SCHEMAS:
        sub_path = schemas_dir / rel
        if sub_path.is_file():
            subs.append(_load(sub_path))

    try:
        from referencing import Registry, Resource

        resources = [(schema.get("$id"), Resource.from_contents(schema))]
        for sub in subs:
            resources.append((sub.get("$id"), Resource.from_contents(sub)))
        registry = Registry().with_resources(
            [(uri, res) for uri, res in resources if uri])
        return jsonschema.Draft202012Validator(schema, registry=registry)
    except ImportError:  # pragma: no cover - jsonschema < 4.18
        store = {schema.get("$id"): schema}
        for sub in subs:
            store[sub.get("$id")] = sub
        resolver = jsonschema.RefResolver.from_schema(schema, store=store)
        return jsonschema.Draft202012Validator(schema, resolver=resolver)


def validate_envelope(envelope: Any, schemas_dir: Path | None = None) -> list[str]:
    """Return a list of human-readable errors. Empty list means valid."""
    validator = build_validator(schemas_dir)
    errors: list[str] = []
    for err in sorted(validator.iter_errors(envelope), key=lambda e: list(e.absolute_path)):
        pointer = "/".join(str(part) for part in err.absolute_path) or "<root>"
        errors.append(f"{pointer}: {err.message}")
    return errors


def validate_envelope_file(path: Path, schemas_dir: Path | None = None) -> list[str]:
    """Load one envelope file and validate it. A parse failure is one error."""
    try:
        envelope = _load(path)
    except FileNotFoundError:
        return [f"<file>: no such file: {path}"]
    except json.JSONDecodeError as exc:
        return [f"<file>: not valid JSON: {exc}"]
    return validate_envelope(envelope, schemas_dir)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="validate_envelope.py",
        description="Validate an agent output envelope against "
                    "agents/_shared/schemas/output-envelope.schema.json, with the "
                    "urn: sub-schema refs resolved.",
    )
    parser.add_argument("envelope", nargs="+", help="path(s) to an envelope JSON file")
    parser.add_argument("--schemas-dir", default=None,
                        help="override agents/_shared/schemas/")
    args = parser.parse_args(argv)

    schemas_dir = Path(args.schemas_dir) if args.schemas_dir else None
    failed = False
    for raw in args.envelope:
        path = Path(raw)
        errors = validate_envelope_file(path, schemas_dir)
        if errors:
            failed = True
            for message in errors:
                print(f"ERROR {path}: {message}")
            print(f"{len(errors)} error(s) in {path}")
        else:
            print(f"OK {path}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
