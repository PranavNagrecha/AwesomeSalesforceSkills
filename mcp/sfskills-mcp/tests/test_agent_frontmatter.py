"""Round-trip test: every AGENT.md frontmatter validates against the schema.

This is the Wave-0 safety net. If someone commits an AGENT.md with a typo
(historically ``modes: [n, audit]`` or ``modes: [s]``), this test fails
BEFORE the agent can be used — instead of silently passing the old loose
regex and failing only when the MCP server tries to resolve the mode.

Run with:

    cd mcp/sfskills-mcp
    python3 -m unittest discover -s tests

Requires PyYAML + jsonschema (both in the repo's root ``requirements.txt``).
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent.parent  # mcp/sfskills-mcp/tests -> repo root
AGENTS_DIR = REPO / "agents"
SCHEMA_PATH = AGENTS_DIR / "_shared" / "schemas" / "agent-frontmatter.schema.json"


def _parse_frontmatter(text: str) -> dict:
    """Extract and parse the YAML frontmatter block from AGENT.md content.

    PyYAML auto-coerces ISO dates (``2026-04-16``) into ``datetime.date``
    objects; the schema requires strings. We coerce back to ``YYYY-MM-DD``
    strings so the round-trip matches the schema's ``pattern`` constraint.
    Returns {} if the file doesn't start with a ``---`` delimiter so the test
    can surface a structural failure with a clear message.
    """
    import datetime
    import yaml  # imported lazily so import errors surface in the test body

    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    end = None
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end = i
            break
    if end is None:
        return {}
    block = "\n".join(lines[1:end])
    data = yaml.safe_load(block) or {}

    # Coerce date fields back to ISO strings for schema validation.
    for key in ("created", "updated"):
        val = data.get(key)
        if isinstance(val, datetime.date):
            data[key] = val.isoformat()
    return data


def _iter_agent_files():
    for path in sorted(AGENTS_DIR.glob("*/AGENT.md")):
        # Skip the shared docs directory explicitly (it has no AGENT.md but
        # the glob above only catches direct-child folders, so this is belt+
        # suspenders).
        if path.parent.name.startswith("_"):
            continue
        yield path


class TestAgentFrontmatter(unittest.TestCase):
    """Validates every agents/<slug>/AGENT.md frontmatter against the schema."""

    @classmethod
    def setUpClass(cls):
        try:
            import yaml  # noqa: F401
            import jsonschema  # noqa: F401
        except ImportError as exc:  # pragma: no cover - environment issue
            raise unittest.SkipTest(f"PyYAML + jsonschema required: {exc}")

        cls.schema = json.loads(SCHEMA_PATH.read_text())
        cls.agent_files = list(_iter_agent_files())

    def test_schema_file_exists(self):
        self.assertTrue(SCHEMA_PATH.exists(), f"Schema missing: {SCHEMA_PATH}")

    def test_at_least_one_agent(self):
        self.assertGreater(
            len(self.agent_files),
            0,
            "No agents/*/AGENT.md files found — check repo layout",
        )

    def test_every_agent_frontmatter_validates(self):
        import jsonschema

        failures = []
        for path in self.agent_files:
            try:
                fm = _parse_frontmatter(path.read_text())
            except Exception as exc:
                failures.append(f"{path.relative_to(REPO)}: YAML parse error — {exc}")
                continue
            if not fm:
                failures.append(
                    f"{path.relative_to(REPO)}: missing or malformed frontmatter block"
                )
                continue
            try:
                jsonschema.validate(instance=fm, schema=self.schema)
            except jsonschema.ValidationError as exc:
                failures.append(
                    f"{path.relative_to(REPO)}: {exc.message} (at {list(exc.absolute_path)})"
                )

        if failures:
            msg = "Frontmatter validation failed for the following files:\n  - " + "\n  - ".join(
                failures
            )
            self.fail(msg)

    def test_folder_name_matches_id(self):
        """Every agent's ``id`` must equal its folder name."""
        mismatches = []
        for path in self.agent_files:
            fm = _parse_frontmatter(path.read_text())
            folder = path.parent.name
            agent_id = fm.get("id")
            if agent_id != folder:
                mismatches.append(
                    f"{path.relative_to(REPO)}: id={agent_id!r} != folder={folder!r}"
                )
        if mismatches:
            self.fail(
                "Folder/id mismatches:\n  - " + "\n  - ".join(mismatches)
            )

    def test_deprecated_agents_have_replacement(self):
        """Schema enforces this via allOf-if, but we assert explicitly for
        a clearer failure message than a generic jsonschema error."""
        missing = []
        for path in self.agent_files:
            fm = _parse_frontmatter(path.read_text())
            if fm.get("status") == "deprecated" and not fm.get("deprecated_in_favor_of"):
                missing.append(str(path.relative_to(REPO)))
        if missing:
            self.fail(
                "Deprecated agents missing deprecated_in_favor_of:\n  - "
                + "\n  - ".join(missing)
            )

    def test_modes_are_from_enum(self):
        """Redundant with schema validation but produces a more actionable
        error specifically for the historical mode-typo class of bug."""
        allowed = set(self.schema["properties"]["modes"]["items"]["enum"])
        offenders = []
        for path in self.agent_files:
            fm = _parse_frontmatter(path.read_text())
            modes = fm.get("modes") or []
            bad = [m for m in modes if m not in allowed]
            if bad:
                offenders.append(
                    f"{path.relative_to(REPO)}: unknown modes {bad!r} "
                    f"(allowed: {sorted(allowed)})"
                )
        if offenders:
            self.fail("Unknown modes in frontmatter:\n  - " + "\n  - ".join(offenders))


if __name__ == "__main__":
    unittest.main()
