#!/usr/bin/env python3
"""Static checker for FLS-in-async-context anti-patterns in Apex source.

Scans `force-app/.../classes/*.cls` and `*.trigger` files and flags:

- Triggers on Platform Event objects (`__e`) that use `WITH USER_MODE`,
  `WITH SECURITY_ENFORCED`, or `Security.stripInaccessible`. These calls
  are no-ops in PE subscribers because the running user is Automated Process.
- Async classes (`implements Queueable | Schedulable | Database.Batchable`)
  that use `WITH USER_MODE` but do not capture an originating user ID at
  enqueue/construction time. Without the assertion, the SOQL clause may
  evaluate against an unintended user identity.
- `System.runAs(...)` calls in non-test code paths (heuristic: in classes
  not annotated `@isTest`).
- `@future` methods accepting non-primitive parameters.

Stdlib only. Heuristic regex.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

PE_TRIGGER = re.compile(r"^\s*trigger\s+\w+\s+on\s+(\w+__e)\b", re.IGNORECASE | re.MULTILINE)
WITH_USER_MODE = re.compile(r"\bWITH\s+(USER_MODE|SECURITY_ENFORCED)\b", re.IGNORECASE)
STRIP_INACCESSIBLE = re.compile(r"\bSecurity\.stripInaccessible\b", re.IGNORECASE)
ASYNC_INTERFACE = re.compile(
    r"\bimplements\b[^\{]*\b(Queueable|Schedulable|Database\.Batchable)\b",
    re.IGNORECASE,
)
ORIGINATING_USER_CAPTURE = re.compile(
    r"UserInfo\.getUserId\(\)\s*[;,)]",  # liberal; counts any capture
)
RUN_AS = re.compile(r"\bSystem\.runAs\s*\(", re.IGNORECASE)
IS_TEST = re.compile(r"@isTest\b", re.IGNORECASE)
FUTURE_METHOD = re.compile(
    r"@future[^)]*\)[^{]*?\b(public|private|global|protected)\s+static\s+\w+\s+\w+\s*\(([^)]*)\)",
    re.IGNORECASE | re.DOTALL,
)
PRIMITIVE_TYPES = {
    "Id", "String", "Integer", "Long", "Double", "Decimal", "Boolean",
    "Date", "DateTime", "Time", "Blob",
}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Detect FLS-in-async anti-patterns in Apex sources."
    )
    p.add_argument("--manifest-dir", default=".", help="Project root.")
    return p.parse_args()


def source_files(root: Path) -> list[Path]:
    out: list[Path] = []
    for ext in ("*.cls", "*.trigger"):
        out.extend((root / "force-app").rglob(ext))
    return out


def is_param_primitive(param: str) -> bool:
    """Best-effort: returns True if the param's type is a known primitive
    or a collection of primitives."""
    p = param.strip()
    if not p:
        return True
    # Strip annotations and the parameter name
    parts = p.split()
    if len(parts) < 2:
        return False
    type_token = parts[-2] if len(parts) >= 2 else parts[0]
    # Handle generics: List<Id>, Set<String>, Map<Id, String>
    m = re.match(r"(\w+)\s*<\s*([\w<>,\s]+)\s*>", type_token)
    if m:
        outer, inner = m.group(1), m.group(2)
        if outer.lower() in {"list", "set"}:
            return inner.strip() in PRIMITIVE_TYPES
        if outer.lower() == "map":
            inner_types = [t.strip() for t in inner.split(",")]
            return all(t in PRIMITIVE_TYPES for t in inner_types)
        return False
    return type_token in PRIMITIVE_TYPES


def check_pe_trigger(path: Path, text: str) -> list[str]:
    issues: list[str] = []
    m = PE_TRIGGER.search(text)
    if not m:
        return issues
    pe_obj = m.group(1)
    if WITH_USER_MODE.search(text):
        issues.append(
            f"{path}: PE trigger on `{pe_obj}` uses WITH USER_MODE / SECURITY_ENFORCED — "
            "this is a no-op in Automated Process context. Filter at publish instead."
        )
    if STRIP_INACCESSIBLE.search(text):
        issues.append(
            f"{path}: PE trigger on `{pe_obj}` calls Security.stripInaccessible — "
            "this is a no-op in Automated Process context. Filter at publish instead."
        )
    return issues


def check_async_class(path: Path, text: str) -> list[str]:
    issues: list[str] = []
    if not ASYNC_INTERFACE.search(text):
        return issues
    if not WITH_USER_MODE.search(text):
        return issues
    # If WITH USER_MODE is present, we expect a UserInfo.getUserId() capture
    # that is later asserted. Liberal heuristic: just look for any capture.
    if not ORIGINATING_USER_CAPTURE.search(text):
        issues.append(
            f"{path}: async class uses WITH USER_MODE without capturing originating user id. "
            "Capture UserInfo.getUserId() at construction and assert in execute()."
        )
    return issues


def check_run_as(path: Path, text: str) -> list[str]:
    if IS_TEST.search(text):
        return []
    if not RUN_AS.search(text):
        return []
    return [
        f"{path}: System.runAs(...) outside test context — runAs only works in tests. "
        "Use a cross-user FLS helper or filter at publish."
    ]


def check_future_methods(path: Path, text: str) -> list[str]:
    issues: list[str] = []
    for m in FUTURE_METHOD.finditer(text):
        params = m.group(2)
        if not params.strip():
            continue
        for param in params.split(","):
            if not is_param_primitive(param):
                issues.append(
                    f"{path}: @future method has non-primitive parameter `{param.strip()}` "
                    "— @future accepts only primitives and collections of primitives."
                )
                break
    return issues


def check_file(path: Path) -> list[str]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return []
    out: list[str] = []
    out.extend(check_pe_trigger(path, text))
    out.extend(check_async_class(path, text))
    out.extend(check_run_as(path, text))
    out.extend(check_future_methods(path, text))
    return out


def main() -> int:
    args = parse_args()
    root = Path(args.manifest_dir)
    if not (root / "force-app").exists():
        print(f"ERROR: no force-app/ directory under {root}", file=sys.stderr)
        return 1

    issues: list[str] = []
    for f in source_files(root):
        issues.extend(check_file(f))

    if not issues:
        print("[field-level-security-in-async-contexts] no issues found")
        return 0
    for i in issues:
        print(f"WARN: {i}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
