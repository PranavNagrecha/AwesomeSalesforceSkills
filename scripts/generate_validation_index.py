#!/usr/bin/env python3
"""Generate ``standards/validation-gates.md`` — the single index of every
gate enforced by the validators.

Walks the validator source files with ``ast`` and finds every construction
of a ``ValidationIssue(...)``. For each, records:

  - source file and line number
  - level (ERROR / WARN — extracted from the literal first arg when possible)
  - the enclosing function name and its first docstring line (the "intent")
  - the message format string (truncated for the index)

Renders the result as markdown grouped by source file. Used by:

  - direct invocation from a contributor: ``python3 scripts/generate_validation_index.py``
  - the sync engine (``pipelines/sync_engine.py``) — regenerates on every
    ``skill_sync.py`` run so the file never goes stale.

The output file is generated; do not hand-edit. The drift check inside
``scripts/validate_repo.py`` catches edits that don't match a fresh
generation.
"""

from __future__ import annotations

import argparse
import ast
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


# Files we walk for validator issues. Ordered the same way the gates run at
# validation time, so the generated index reads top-to-bottom in execution
# order.
VALIDATOR_SOURCES: list[Path] = [
    ROOT / "pipelines" / "validators.py",
    ROOT / "pipelines" / "agent_validators.py",
    ROOT / "scripts" / "validate_repo.py",
]

OUTPUT_PATH = ROOT / "standards" / "validation-gates.md"


@dataclass(frozen=True)
class GateRecord:
    source_path: Path  # absolute path
    line: int
    level: str  # "ERROR", "WARN", or "?"
    function_name: str
    function_intent: str  # first non-empty line of the function docstring
    message_excerpt: str  # truncated message string


def _string_value_from_node(node: ast.AST) -> str | None:
    """Best-effort literal string from an AST node. Returns None when the
    argument isn't a plain Constant / JoinedStr — those cases get rendered
    with a `?` placeholder so the index still shows the call site."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.JoinedStr):
        # f-string: concatenate the constant parts; leave format expressions as `{…}`
        out = []
        for part in node.values:
            if isinstance(part, ast.Constant) and isinstance(part.value, str):
                out.append(part.value)
            else:
                out.append("{…}")
        return "".join(out)
    return None


def _enclosing_function(stack: list[ast.AST]) -> ast.FunctionDef | ast.AsyncFunctionDef | None:
    """Walk an AST ancestor stack from innermost outward and return the
    enclosing FunctionDef / AsyncFunctionDef, or None for module-level calls."""
    for parent in reversed(stack):
        if isinstance(parent, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return parent
    return None


def _function_intent(func: ast.FunctionDef | ast.AsyncFunctionDef | None) -> str:
    """First non-empty line of a function's docstring, or ``""``."""
    if func is None:
        return ""
    doc = ast.get_docstring(func) or ""
    for line in doc.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return ""


def _truncate(text: str, limit: int = 140) -> str:
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


class _ValidationIssueVisitor(ast.NodeVisitor):
    """Visit a parsed module and record every ``ValidationIssue(...)`` call.

    Tracks the function-definition stack manually so we can map each call to
    its enclosing function for intent extraction.
    """

    def __init__(self, source_path: Path) -> None:
        self.source_path = source_path
        self.records: list[GateRecord] = []
        self._stack: list[ast.AST] = []

    def _is_validation_issue_call(self, node: ast.Call) -> bool:
        func = node.func
        if isinstance(func, ast.Name) and func.id == "ValidationIssue":
            return True
        if isinstance(func, ast.Attribute) and func.attr == "ValidationIssue":
            return True
        return False

    def visit(self, node: ast.AST) -> None:  # type: ignore[override]
        if isinstance(node, ast.Call) and self._is_validation_issue_call(node):
            self._record_call(node)
        self._stack.append(node)
        try:
            super().visit(node)
        finally:
            self._stack.pop()

    def _record_call(self, node: ast.Call) -> None:
        if not node.args:
            return
        level = _string_value_from_node(node.args[0]) or "?"
        message = ""
        if len(node.args) >= 3:
            message = _string_value_from_node(node.args[2]) or ""
        func = _enclosing_function(self._stack)
        self.records.append(
            GateRecord(
                source_path=self.source_path,
                line=node.lineno,
                level=level,
                function_name=func.name if func is not None else "<module>",
                function_intent=_function_intent(func),
                message_excerpt=_truncate(message),
            )
        )


def collect_gates(sources: list[Path] = VALIDATOR_SOURCES) -> list[GateRecord]:
    """Parse each source and return every ValidationIssue construction."""
    out: list[GateRecord] = []
    for src in sources:
        if not src.exists():
            continue
        tree = ast.parse(src.read_text(encoding="utf-8"))
        visitor = _ValidationIssueVisitor(src)
        visitor.visit(tree)
        out.extend(visitor.records)
    return out


def render_markdown(gates: list[GateRecord], root: Path = ROOT) -> str:
    """Render the gates list as the public ``standards/validation-gates.md``
    document. Grouped by source file in the order of ``VALIDATOR_SOURCES``."""
    by_source: dict[Path, list[GateRecord]] = {}
    for g in gates:
        by_source.setdefault(g.source_path, []).append(g)
    for v in by_source.values():
        v.sort(key=lambda g: g.line)

    error_count = sum(1 for g in gates if g.level == "ERROR")
    warn_count = sum(1 for g in gates if g.level == "WARN")
    other_count = len(gates) - error_count - warn_count

    out: list[str] = []
    out.append("# Validation gates index\n")
    out.append(
        "Single source of truth for every gate the validators enforce. Generated\n"
        "by `scripts/generate_validation_index.py`. **Do not hand-edit.** The\n"
        "drift check in `scripts/validate_repo.py` catches stale copies.\n"
    )
    out.append("")
    out.append(
        f"- total gates: **{len(gates)}**  ·  errors: **{error_count}**  ·  "
        f"warnings: **{warn_count}**"
        + (f"  ·  other: **{other_count}**" if other_count else "")
    )
    out.append("")
    out.append(
        "Each gate links to its source line. The intent line is the first line of\n"
        "the enclosing function's docstring — read it for *why* the gate exists,\n"
        "not just what it checks."
    )
    out.append("")

    root_abs = root.resolve()
    for src in VALIDATOR_SOURCES:
        if src not in by_source:
            continue
        rel = src.resolve().relative_to(root_abs).as_posix()
        out.append(f"## `{rel}`")
        out.append("")
        out.append("| Line | Level | Function | Intent | Message |")
        out.append("|---|---|---|---|---|")
        for g in by_source[src]:
            line_link = f"[{g.line}]({rel}#L{g.line})"
            level_cell = (
                f"**{g.level}**" if g.level == "ERROR"
                else f"_{g.level}_" if g.level == "WARN"
                else g.level
            )
            intent = g.function_intent.replace("|", "\\|") or "—"
            message = g.message_excerpt.replace("|", "\\|") or "—"
            # Truncate intent so the table stays readable
            if len(intent) > 110:
                intent = intent[:109].rstrip() + "…"
            out.append(
                f"| {line_link} | {level_cell} | `{g.function_name}` | {intent} | {message} |"
            )
        out.append("")

    return "\n".join(out).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate standards/validation-gates.md from validator source files.",
    )
    parser.add_argument(
        "--check", action="store_true",
        help="Exit non-zero if the on-disk file differs from a fresh generation. "
             "Does not write the file. Used by the sync-engine drift check.",
    )
    parser.add_argument(
        "--out", type=Path, default=OUTPUT_PATH,
        help=f"Where to write (default {OUTPUT_PATH.relative_to(ROOT)}).",
    )
    args = parser.parse_args()

    gates = collect_gates()
    rendered = render_markdown(gates, root=ROOT)

    if args.check:
        if not args.out.exists() or args.out.read_text(encoding="utf-8") != rendered:
            print(
                f"DRIFT: {args.out.relative_to(ROOT)} is stale; "
                "run `python3 scripts/generate_validation_index.py`",
                file=sys.stderr,
            )
            return 1
        print(f"OK: {args.out.relative_to(ROOT)} is up-to-date.")
        return 0

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(rendered, encoding="utf-8")
    print(f"Wrote {args.out.relative_to(ROOT)} — {len(gates)} gate(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
