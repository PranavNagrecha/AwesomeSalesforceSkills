"""Unit tests for ``pipelines/frontmatter.py``.

``parse_markdown_with_frontmatter`` is the single entry point through which
every SKILL.md and AGENT.md reaches the registry, the chunker, the validators
and the MCP export. ``stable_hash_for_files`` is the drift detector that
decides whether generated artifacts are stale — and it carries a specific
cross-OS fix (relative-path encoding) that a CI matrix caught the hard way.

Hermetic: every fixture is written into a temp dir.
"""

from __future__ import annotations

import datetime as dt
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pipelines.frontmatter import (  # noqa: E402
    ParsedMarkdown,
    normalize_metadata,
    parse_markdown_with_frontmatter,
    stable_hash_for_files,
)


class TempDirMixin:
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp(prefix="sfskills-fm-"))
        self.addCleanup(shutil.rmtree, self.dir, ignore_errors=True)

    def write(self, name: str, text: str) -> Path:
        path = self.dir / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path


VALID = """---
name: trigger-recursion
description: "Prevent recursive trigger execution. NOT for Flow recursion."
category: apex
salesforce-version: "Summer '26+"
well-architected-pillars:
  - Reliability
tags:
  - apex
  - trigger
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-08-01
---

# Trigger Recursion

Body text.
"""


class ParseTest(TempDirMixin, unittest.TestCase):

    def test_returns_a_frozen_dataclass(self):
        parsed = parse_markdown_with_frontmatter(self.write("SKILL.md", VALID))
        self.assertIsInstance(parsed, ParsedMarkdown)
        with self.assertRaises(Exception):
            parsed.body = "mutated"  # frozen=True

    def test_scalars_lists_and_quoted_strings_round_trip(self):
        parsed = parse_markdown_with_frontmatter(self.write("SKILL.md", VALID))
        self.assertEqual(parsed.metadata["name"], "trigger-recursion")
        self.assertEqual(parsed.metadata["category"], "apex")
        self.assertEqual(parsed.metadata["tags"], ["apex", "trigger"])
        self.assertEqual(parsed.metadata["well-architected-pillars"], ["Reliability"])
        self.assertEqual(parsed.metadata["salesforce-version"], "Summer '26+")

    def test_version_stays_a_string_not_a_float(self):
        """`1.0.0` must not become 1.0 — the schema pattern is ^\\d+\\.\\d+\\.\\d+$."""
        parsed = parse_markdown_with_frontmatter(self.write("SKILL.md", VALID))
        self.assertIsInstance(parsed.metadata["version"], str)
        self.assertEqual(parsed.metadata["version"], "1.0.0")

    def test_unquoted_date_is_normalized_to_an_iso_string(self):
        """PyYAML parses a bare `2026-08-01` as datetime.date, which is not
        JSON-serializable and would break registry_builder. Normalization is
        what keeps unquoted dates legal in authored frontmatter."""
        parsed = parse_markdown_with_frontmatter(self.write("SKILL.md", VALID))
        self.assertEqual(parsed.metadata["updated"], "2026-08-01")
        self.assertIsInstance(parsed.metadata["updated"], str)

    def test_body_excludes_the_frontmatter_and_is_left_stripped(self):
        parsed = parse_markdown_with_frontmatter(self.write("SKILL.md", VALID))
        self.assertTrue(parsed.body.startswith("# Trigger Recursion"))
        self.assertNotIn("category: apex", parsed.body)

    def test_a_horizontal_rule_in_the_body_is_not_a_second_boundary(self):
        text = "---\nname: x\n---\nintro\n\n---\n\nmore\n"
        parsed = parse_markdown_with_frontmatter(self.write("SKILL.md", text))
        self.assertEqual(parsed.metadata, {"name": "x"})
        self.assertEqual(parsed.body, "intro\n\n---\n\nmore")

    def test_crlf_line_endings_parse(self):
        """A Windows-authored skill must not read as 'missing frontmatter'."""
        parsed = parse_markdown_with_frontmatter(
            self.write("SKILL.md", "---\r\nname: x\r\ncategory: apex\r\n---\r\nbody line\r\n")
        )
        self.assertEqual(parsed.metadata, {"name": "x", "category": "apex"})
        self.assertEqual(parsed.body, "body line")

    def test_trailing_whitespace_on_the_boundary_is_tolerated(self):
        parsed = parse_markdown_with_frontmatter(self.write("SKILL.md", "---  \nname: x\n---  \nbody"))
        self.assertEqual(parsed.metadata, {"name": "x"})

    def test_empty_frontmatter_block_is_an_empty_dict_not_an_error(self):
        parsed = parse_markdown_with_frontmatter(self.write("SKILL.md", "---\n---\nbody"))
        self.assertEqual(parsed.metadata, {})
        self.assertEqual(parsed.body, "body")

    def test_utf8_content_survives(self):
        parsed = parse_markdown_with_frontmatter(
            self.write("SKILL.md", "---\nname: x\ndescription: \"Em—dash · café\"\n---\nbody ✅")
        )
        self.assertEqual(parsed.metadata["description"], "Em—dash · café")
        self.assertEqual(parsed.body, "body ✅")


class ParseErrorTest(TempDirMixin, unittest.TestCase):
    """Every failure mode must be a ValueError naming the file — these surface
    to authors through validate_repo.py, so a bare KeyError or a yaml error
    with no path is a materially worse experience."""

    def test_no_frontmatter_at_all(self):
        path = self.write("SKILL.md", "# Just a heading\n")
        with self.assertRaises(ValueError) as ctx:
            parse_markdown_with_frontmatter(path)
        self.assertIn("missing YAML frontmatter", str(ctx.exception))
        self.assertIn("SKILL.md", str(ctx.exception))

    def test_completely_empty_file(self):
        with self.assertRaises(ValueError):
            parse_markdown_with_frontmatter(self.write("SKILL.md", ""))

    def test_unterminated_frontmatter(self):
        path = self.write("SKILL.md", "---\nname: x\ncategory: apex\n")
        with self.assertRaises(ValueError) as ctx:
            parse_markdown_with_frontmatter(path)
        self.assertIn("unterminated", str(ctx.exception))

    def test_scalar_frontmatter_is_rejected(self):
        path = self.write("SKILL.md", "---\njust a bare string\n---\nbody")
        with self.assertRaises(ValueError) as ctx:
            parse_markdown_with_frontmatter(path)
        self.assertIn("must parse to an object", str(ctx.exception))

    def test_list_frontmatter_is_rejected(self):
        with self.assertRaises(ValueError):
            parse_markdown_with_frontmatter(self.write("SKILL.md", "---\n- a\n- b\n---\nbody"))

    def test_malformed_yaml_propagates(self):
        import yaml

        with self.assertRaises(yaml.YAMLError):
            parse_markdown_with_frontmatter(self.write("SKILL.md", "---\nname: [unclosed\n---\nbody"))


class NormalizeMetadataTest(unittest.TestCase):

    def test_top_level_dates_become_iso_strings(self):
        self.assertEqual(normalize_metadata({"updated": dt.date(2026, 8, 1)}), {"updated": "2026-08-01"})

    def test_datetimes_are_normalized_too(self):
        """datetime.datetime subclasses datetime.date, so the isinstance check
        catches a quoted-then-unquoted timestamp as well."""
        out = normalize_metadata({"updated": dt.datetime(2026, 8, 1, 12, 30)})
        self.assertEqual(out["updated"], "2026-08-01T12:30:00")

    def test_other_types_pass_through_untouched(self):
        payload = {"tags": ["a", "b"], "n": 3, "ok": True, "nil": None, "s": "x"}
        self.assertEqual(normalize_metadata(payload), payload)

    def test_nested_dates_are_not_normalized(self):
        """Characterization: normalization is one level deep. No frontmatter key
        nests a date today; if one ever does, the registry JSON dump will fail
        and this test is the breadcrumb."""
        nested = {"meta": {"d": dt.date(2026, 8, 1)}}
        self.assertIsInstance(normalize_metadata(nested)["meta"]["d"], dt.date)

    def test_empty_dict(self):
        self.assertEqual(normalize_metadata({}), {})


class StableHashTest(TempDirMixin, unittest.TestCase):
    """Drift detection. A hash that is unstable across machines produces
    spurious 'generated artifacts are stale' CI failures; a hash that is too
    stable misses real drift."""

    def files(self, **contents) -> list[Path]:
        return [self.write(name, text) for name, text in contents.items()]

    def test_deterministic_for_the_same_inputs(self):
        paths = self.files(a="alpha", b="beta")
        self.assertEqual(stable_hash_for_files(paths, self.dir), stable_hash_for_files(paths, self.dir))

    def test_input_order_does_not_matter(self):
        paths = self.files(a="alpha", b="beta")
        self.assertEqual(
            stable_hash_for_files(paths, self.dir), stable_hash_for_files(list(reversed(paths)), self.dir)
        )

    def test_content_change_changes_the_hash(self):
        paths = self.files(a="alpha", b="beta")
        before = stable_hash_for_files(paths, self.dir)
        paths[0].write_text("alpha!", encoding="utf-8")
        self.assertNotEqual(before, stable_hash_for_files(paths, self.dir))

    def test_a_rename_changes_the_hash(self):
        """Paths are folded into the digest, so moving a file is drift even
        when no byte of content changed."""
        one = stable_hash_for_files(self.files(a="same"), self.dir)
        two = stable_hash_for_files(self.files(b="same"), self.dir)
        self.assertNotEqual(one, two)

    def test_content_cannot_be_shuffled_between_files_unnoticed(self):
        """The NUL separators after the path and after the bytes are what stop
        ('ab', '') and ('a', 'b') colliding."""
        one = stable_hash_for_files(self.files(a="ab", b=""), self.dir)
        two = stable_hash_for_files(self.files(a="a", b="b"), self.dir)
        self.assertNotEqual(one, two)

    def test_adding_a_file_changes_the_hash(self):
        base = self.files(a="alpha")
        before = stable_hash_for_files(base, self.dir)
        self.assertNotEqual(before, stable_hash_for_files(base + self.files(b="beta"), self.dir))

    def test_hash_is_machine_independent_when_root_is_given(self):
        """The Wave-1.1 hotfix: macOS dev boxes hash under /Users/... while
        GitHub runners hash under /home/runner/... . With `root` the digest
        must depend only on the tree, not on where it lives."""
        other = Path(tempfile.mkdtemp(prefix="sfskills-fm-alt-"))
        self.addCleanup(shutil.rmtree, other, ignore_errors=True)
        for name, text in (("a", "alpha"), ("b", "beta")):
            (other / name).write_text(text, encoding="utf-8")

        here = stable_hash_for_files(self.files(a="alpha", b="beta"), self.dir)
        there = stable_hash_for_files([other / "a", other / "b"], other)
        self.assertEqual(here, there)

    def test_omitting_root_reintroduces_absolute_path_dependence(self):
        """Characterization of the legacy call form. Callers that care about
        cross-machine determinism must pass `root` — this proves the parameter
        is doing real work rather than being cosmetic."""
        other = Path(tempfile.mkdtemp(prefix="sfskills-fm-alt2-"))
        self.addCleanup(shutil.rmtree, other, ignore_errors=True)
        (other / "a").write_text("alpha", encoding="utf-8")

        self.assertNotEqual(
            stable_hash_for_files(self.files(a="alpha")),
            stable_hash_for_files([other / "a"]),
        )

    def test_paths_outside_root_fall_back_to_the_basename(self):
        """Documented guard against pathological inputs — it must not raise."""
        outside = Path(tempfile.mkdtemp(prefix="sfskills-fm-out-"))
        self.addCleanup(shutil.rmtree, outside, ignore_errors=True)
        (outside / "a").write_text("alpha", encoding="utf-8")
        self.assertEqual(
            stable_hash_for_files([outside / "a"], self.dir),
            stable_hash_for_files(self.files(a="alpha"), self.dir),
        )

    def test_empty_input_is_the_sha256_of_nothing(self):
        self.assertEqual(
            stable_hash_for_files([], self.dir),
            "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        )

    def test_binary_content_is_handled(self):
        blob = self.dir / "blob.bin"
        blob.write_bytes(bytes(range(256)))
        self.assertEqual(len(stable_hash_for_files([blob], self.dir)), 64)


if __name__ == "__main__":
    unittest.main()
