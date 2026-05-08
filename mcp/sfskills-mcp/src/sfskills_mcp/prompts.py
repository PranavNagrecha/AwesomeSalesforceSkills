"""Expose ``commands/*.md`` slash-command wrappers as MCP Prompts.

Every file in ``commands/`` is a ready-made instruction wrapper that loads a
specific run-time agent and walks the user through inputs → execution → output.
Today these only flow into Claude Code (because the file lives in the
``commands/`` directory the Claude Code harness reads). Surfacing them as MCP
Prompts gives every MCP-capable client a native picker — type ``/refactor-apex``
in Cursor, Cline, Claude Desktop, etc. and the wrapper loads.

This is the **B2a** scope from ``.planning/mcp-v0.2-plan.md``: register each
command as an argument-less prompt that returns the full wrapper body. The
client's model then asks the user for the inputs the wrapper itself prompts
for. A later iteration (B2b) will parse the wrapper's "Step 1 — Collect
inputs" section into typed prompt arguments; that requires a one-time rewrite
of all 68 wrappers and is intentionally deferred.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING

from . import paths

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP


# Skip wrappers that aren't prompts in the user-facing sense — README, indexes,
# anything starting with an underscore. The pattern matches every legitimate
# slash command but excludes meta-files.
_SKIP_NAMES = frozenset({"README"})

# Some wrappers use `# /name — description`, others just `# /name`.
# We accept both shapes.
_TITLE_PATTERN = re.compile(
    r"^\s*#\s+/(?P<name>[a-z][a-z0-9-]*)\s*(?:[—\-:]\s*(?P<desc>.+?))?\s*$",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class PromptDef:
    name: str
    description: str
    body: str


def _commands_dir() -> Path:
    return paths.repo_root() / "commands"


def _parse_prompt_file(path: Path) -> PromptDef | None:
    """Return a ``PromptDef`` for a wrapper file, or ``None`` if it doesn't
    look like a slash command (file is malformed, README, etc.)."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None
    # First non-empty line is expected to be the title.
    title_line: str | None = None
    for line in text.splitlines():
        if line.strip():
            title_line = line
            break
    if not title_line:
        return None
    m = _TITLE_PATTERN.match(title_line)
    if not m:
        # File doesn't lead with `# /name …`; treat as not-a-prompt.
        return None
    name = m.group("name")
    description = (m.group("desc") or "").strip()
    if not description:
        # Fall back to the first non-empty line after the title — usually a
        # one-line "Wraps [agents/X]" sentence.
        rest = text.split("\n", 1)[1] if "\n" in text else ""
        for line in rest.splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                # Strip markdown link noise for a cleaner description.
                description = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", line)
                description = description[:240]
                break
    return PromptDef(name=name, description=description or f"/{name}", body=text)


@lru_cache(maxsize=1)
def discover() -> tuple[PromptDef, ...]:
    """Return every parseable wrapper in ``commands/``.

    Cached — the file set rarely changes during a server lifetime. Restart
    the server after adding a new wrapper.
    """
    cmd_dir = _commands_dir()
    if not cmd_dir.exists():
        return ()
    out: list[PromptDef] = []
    for path in sorted(cmd_dir.iterdir()):
        if path.suffix != ".md" or path.stem in _SKIP_NAMES:
            continue
        defn = _parse_prompt_file(path)
        if defn is None:
            continue
        out.append(defn)
    return tuple(out)


def register_all(mcp: "FastMCP") -> int:
    """Register every discovered wrapper as an MCP prompt on ``mcp``.

    Returns the number registered. The wrapper body is the prompt's only
    output; clients render it as the assistant's first message and then
    execute the wrapper's "Step 1 — Collect inputs" interactively.
    """
    count = 0
    seen: set[str] = set()
    for defn in discover():
        if defn.name in seen:
            # Two wrappers shouldn't share a slash command, but if they do
            # (e.g. the file pair `audit-sharing.md` + `audit-sharing-v2.md`)
            # the first one wins.
            continue
        seen.add(defn.name)
        # Bind the body to the inner function via default arg — closure
        # capture would otherwise leak the loop variable and every prompt
        # would return the last wrapper's body.
        def _factory(body: str = defn.body):
            def _render() -> str:
                return body
            return _render
        render = _factory()
        # FastMCP infers the prompt's name from the function unless we pass
        # it explicitly; pass it so the slash command stays stable even if
        # we rename the local function.
        mcp.prompt(name=defn.name, description=defn.description)(render)
        count += 1
    return count
