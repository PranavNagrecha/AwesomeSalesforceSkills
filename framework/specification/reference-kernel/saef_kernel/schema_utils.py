from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_json(path: str | Path) -> Any:
    with Path(path).open(encoding="utf-8") as handle:
        return json.load(handle)


def validate_json(instance_path: str | Path, schema_path: str | Path) -> list[str]:
    instance=load_json(instance_path)
    schema=load_json(schema_path)
    try:
        import jsonschema
    except ImportError:
        return ["jsonschema is not installed; structural validation not performed"]
    validator=jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker())
    errors=[]
    for error in sorted(validator.iter_errors(instance), key=lambda e: list(e.path)):
        loc="/"+"/".join(str(x) for x in error.path)
        errors.append(f"{loc}: {error.message}")
    return errors
