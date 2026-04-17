"""Wave 10 tests: Deliverable Contract compliance.

Every class: runtime, status != deprecated agent MUST:

1. Declare `default_output_dir` in frontmatter following `docs/reports/<id>/` pattern.
2. Declare `output_formats` in frontmatter (defaults to ["markdown", "json"]).
3. Cite `agents/_shared/DELIVERABLE_CONTRACT.md` in Mandatory Reads.
4. Have an "Output Contract" section containing:
   - a "Persistence" sub-section naming docs/reports/<id>/<run_id>.{md,json}
   - a "Scope Guardrails" sub-section naming the no-ad-hoc-code rule
5. If `multi_dimensional: true`, its Output Contract enumerates the dimensions.

This test fails initially on every agent that hasn't been migrated. That's
the TDD target: Phase 2's migration script makes all 42 pass.

Run:
    cd mcp/sfskills-mcp
    python3 -m unittest tests.test_deliverable_contract -v
"""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent.parent
AGENTS_DIR = REPO / "agents"
CONTRACT_DOC = AGENTS_DIR / "_shared" / "DELIVERABLE_CONTRACT.md"


def _parse_frontmatter_and_body(path: Path) -> tuple[dict, str]:
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n(.*)", text, re.DOTALL)
    if not m:
        return {}, text

    meta: dict = {}
    current_top: str | None = None
    current_sub: str | None = None
    raw = m.group(1)
    body = m.group(2)

    for line in raw.splitlines():
        if not line.strip():
            continue
        if re.match(r"^[a-z_]+:\s*\S", line):
            key, _, val = line.partition(":")
            meta[key.strip()] = val.strip().strip('"').strip("'")
            current_top = None
            current_sub = None
            continue
        if re.match(r"^[a-z_]+:\s*$", line):
            key = line.split(":")[0].strip()
            meta[key] = {}
            current_top = key
            current_sub = None
            continue
        m2 = re.match(r"^  ([a-z_]+):\s*\S.*$", line)
        if m2 and current_top:
            if not isinstance(meta[current_top], dict):
                meta[current_top] = {}
            meta[current_top][m2.group(1)] = line.split(":", 1)[1].strip().strip('"')
            continue
        m2 = re.match(r"^  ([a-z_]+):\s*$", line)
        if m2 and current_top is not None:
            current_sub = m2.group(1)
            if not isinstance(meta[current_top], dict):
                meta[current_top] = {}
            meta[current_top][current_sub] = []
            continue
        m2 = re.match(r"^    - (.+)$", line)
        if m2 and current_top and current_sub:
            meta[current_top][current_sub].append(m2.group(1).strip())
            continue
        m2 = re.match(r"^  - (.+)$", line)
        if m2 and current_top:
            if not isinstance(meta[current_top], list):
                meta[current_top] = []
            meta[current_top].append(m2.group(1).strip())
            continue

    return meta, body


def _runtime_agents() -> list[tuple[str, Path, dict, str]]:
    out = []
    for f in sorted(AGENTS_DIR.glob("*/AGENT.md")):
        meta, body = _parse_frontmatter_and_body(f)
        if meta.get("class") != "runtime":
            continue
        if meta.get("status") == "deprecated":
            continue
        out.append((f.parent.name, f, meta, body))
    return out


class TestDeliverableContractExists(unittest.TestCase):
    def test_contract_doc_present(self) -> None:
        self.assertTrue(CONTRACT_DOC.exists(),
                        f"agents/_shared/DELIVERABLE_CONTRACT.md must exist")


class TestDefaultOutputDir(unittest.TestCase):
    """Every runtime agent declares default_output_dir: docs/reports/<id>/"""

    def test_every_runtime_agent_has_output_dir(self) -> None:
        failures = []
        for agent_id, path, meta, _ in _runtime_agents():
            dod = meta.get("default_output_dir", "")
            expected = f"docs/reports/{agent_id}/"
            if dod != expected:
                failures.append(f"{agent_id}: default_output_dir should be '{expected}', got '{dod or '<missing>'}'")
        if failures:
            msg = "\n".join(failures[:15])
            if len(failures) > 15:
                msg += f"\n... and {len(failures) - 15} more"
            self.fail(f"{len(failures)} agent(s) missing/wrong default_output_dir:\n{msg}")


class TestOutputFormats(unittest.TestCase):
    """Every runtime agent declares output_formats including at least markdown + json."""

    def test_every_runtime_agent_declares_formats(self) -> None:
        failures = []
        for agent_id, path, meta, _ in _runtime_agents():
            formats = meta.get("output_formats")
            if not isinstance(formats, list):
                failures.append(f"{agent_id}: output_formats missing or not a list")
                continue
            missing = {"markdown", "json"} - set(formats)
            if missing:
                failures.append(f"{agent_id}: output_formats missing {sorted(missing)}")
        if failures:
            msg = "\n".join(failures[:15])
            if len(failures) > 15:
                msg += f"\n... and {len(failures) - 15} more"
            self.fail(f"{len(failures)} agent(s) with wrong output_formats:\n{msg}")


class TestContractCitation(unittest.TestCase):
    """Every runtime agent cites DELIVERABLE_CONTRACT.md in its body."""

    def test_every_runtime_agent_cites_contract(self) -> None:
        failures = []
        for agent_id, path, meta, body in _runtime_agents():
            if "DELIVERABLE_CONTRACT.md" not in body:
                failures.append(f"{agent_id}: body does not cite DELIVERABLE_CONTRACT.md")
        if failures:
            msg = "\n".join(failures[:15])
            if len(failures) > 15:
                msg += f"\n... and {len(failures) - 15} more"
            self.fail(f"{len(failures)} agent(s) missing contract citation:\n{msg}")


class TestOutputContractShape(unittest.TestCase):
    """Output Contract section contains required Wave 10 sub-sections."""

    def test_persistence_sub_section(self) -> None:
        failures = []
        for agent_id, path, meta, body in _runtime_agents():
            # Find the "Output Contract" section.
            m = re.search(r"^## Output Contract\s*$(.*?)^## ", body, re.MULTILINE | re.DOTALL)
            if not m:
                failures.append(f"{agent_id}: no '## Output Contract' section found")
                continue
            section = m.group(1)
            # Must mention the canonical persistence paths.
            has_persistence = (
                "docs/reports/" in section and
                ".md" in section and
                ".json" in section
            )
            if not has_persistence:
                failures.append(f"{agent_id}: Output Contract missing persistence paths (docs/reports/<id>/<run_id>.{{md,json}})")
        if failures:
            msg = "\n".join(failures[:15])
            if len(failures) > 15:
                msg += f"\n... and {len(failures) - 15} more"
            self.fail(f"{len(failures)} agent(s) missing persistence paths:\n{msg}")

    def test_scope_guardrails_sub_section(self) -> None:
        failures = []
        for agent_id, path, meta, body in _runtime_agents():
            m = re.search(r"^## Output Contract\s*$(.*?)^## ", body, re.MULTILINE | re.DOTALL)
            if not m:
                continue  # Covered by persistence test.
            section = m.group(1)
            # Look for scope-guardrails language — at least one of these phrases.
            guards = [
                "Scope Guardrails",
                "ad-hoc code",
                "canonical data surface",
                "does NOT generate ad-hoc",
            ]
            has_guardrails = any(g in section for g in guards)
            if not has_guardrails:
                failures.append(f"{agent_id}: Output Contract missing Scope Guardrails sub-section")
        if failures:
            msg = "\n".join(failures[:15])
            if len(failures) > 15:
                msg += f"\n... and {len(failures) - 15} more"
            self.fail(f"{len(failures)} agent(s) missing Scope Guardrails:\n{msg}")


class TestMultiDimensionalDeclaration(unittest.TestCase):
    """Agents with multi_dimensional: true must enumerate dimensions in their
    Output Contract section."""

    def test_multi_dimensional_agents_enumerate_dimensions(self) -> None:
        failures = []
        for agent_id, path, meta, body in _runtime_agents():
            if not meta.get("multi_dimensional"):
                continue
            m = re.search(r"^## Output Contract\s*$(.*?)^## ", body, re.MULTILINE | re.DOTALL)
            if not m:
                failures.append(f"{agent_id}: no Output Contract section to check")
                continue
            section = m.group(1)
            has_dimensions = "Dimensions" in section or "dimensions_compared" in section
            if not has_dimensions:
                failures.append(
                    f"{agent_id}: multi_dimensional=true but Output Contract doesn't "
                    f"enumerate dimensions or reference dimensions_compared"
                )
        if failures:
            msg = "\n".join(failures[:15])
            if len(failures) > 15:
                msg += f"\n... and {len(failures) - 15} more"
            self.fail(f"{len(failures)} multi-dimensional agent(s) missing dimension enumeration:\n{msg}")


if __name__ == "__main__":
    unittest.main()
