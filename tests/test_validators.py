"""Unit tests for ``pipelines/validators.py``.

Every gate in this module decides whether a skill may ship. The pattern is one
test per gate, in pairs: a PASS case built from a known-good synthetic skill,
and a FAIL case that mutates exactly one thing. Anything that only asserts the
FAIL side can pass against a validator that always errors; anything that only
asserts the PASS side can pass against a validator that always returns [].

Fixtures are built in a temp dir by ``make_skill``. The only thing read from
the real repository is ``config/skill-frontmatter.schema.json`` — that IS the
contract under test, it is ~3 KB, and vendoring a copy here would let the two
drift. No corpus walk, no ``vector_index/``.

``standards/validation-gates.md`` is the generated index of these gates; when a
level (ERROR vs WARN) changes here, that file changes too.
"""

from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

REPO_ROOT = Path(__file__).resolve().parents[1]

from pipelines import validators as V  # noqa: E402
from pipelines.validators import (  # noqa: E402
    ValidationIssue,
    validate_frontmatter,
    validate_knowledge_source,
    validate_official_sources_uniqueness,
    validate_skill_authoring_style,
    validate_skill_registry_record,
    validate_skill_similarity,
    validate_skill_structure,
)


FRONTMATTER = """---
name: {name}
description: "Prevent recursive trigger execution using a static guard. NOT for Flow recursion."
category: {category}
salesforce-version: "Summer '26+"
well-architected-pillars:
  - Reliability
tags:
  - apex
  - trigger
triggers:
  - trigger fires twice on update
  - recursive trigger execution guard
  - static boolean recursion flag
inputs:
  - the trigger source to review
outputs:
  - a refactored handler class
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-08-01
---
"""

_PARA = (
    "A static Boolean on the handler is the cheapest recursion guard, and it "
    "resets between transactions because static state is per-transaction. "
    "Paragraph {n} of the synthetic body, long enough to clear the word floor. "
)
BODY = (
    "\n# Trigger Recursion\n\n## Recommended Workflow\n\n"
    "1. Identify the re-entrant DML.\n2. Add the guard.\n3. Prove it with a bulk test.\n\n"
    + "\n\n".join(_PARA.format(n=i) for i in range(30))
    + "\n"
)

WAF = (
    "# Well-Architected\n\nReliability: the guard keeps the transaction from re-entering "
    "itself, which is what makes the operation predictable under bulk load. This paragraph "
    "exists to push the file past the 200-character threshold that turns on the § 6.4 "
    "pillar-duplication gate.\n\n## Official Sources Used\n\n"
    "- https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_triggers.htm\n"
)

# Five entries, each deep enough that the file clears MIN_ANTI_PATTERNS_BYTES.
ANTI_PATTERNS = "# LLM Anti-Patterns\n\n" + "\n\n".join(
    f"## Anti-Pattern {i}\n\n"
    "**Mistake.** The assistant writes the recursion guard as an instance field instead of a "
    "static, so it resets on every handler construction and stops guarding anything.\n\n"
    "**Why the LLM does it.** Instance state is the default shape in most languages, and the "
    "per-transaction lifetime of Apex statics has no analogue the model can transfer from "
    "its general training data.\n\n"
    "**Correct form.** A private static Boolean on the handler class, checked and set inside "
    "the same method, with a bulk test that fires the trigger twice in one transaction.\n"
    for i in range(1, 6)
)

CHECKER = (
    "#!/usr/bin/env python3\n"
    "import sys\n"
    "from pathlib import Path\n"
    "\n"
    "def main() -> int:\n"
    "    problems = []\n"
    "    for path in Path('.').glob('*.cls'):\n"
    "        text = path.read_text()\n"
    "        if 'static Boolean' not in text:\n"
    "            problems.append(path)\n"
    "    for path in problems:\n"
    "        print(f'ERROR {path}: no static recursion guard')\n"
    "    if problems:\n"
    "        sys.exit(1)\n"
    "    return 0\n"
    "\n"
    "if __name__ == '__main__':\n"
    "    sys.exit(main())\n"
)


def make_skill(root: Path, domain: str = "apex", name: str = "trigger-recursion") -> Path:
    """Write a synthetic skill that passes every gate, and return its directory."""
    skill = root / "skills" / domain / name
    (skill / "references").mkdir(parents=True, exist_ok=True)
    (skill / "templates").mkdir(exist_ok=True)
    (skill / "scripts").mkdir(exist_ok=True)
    (skill / "SKILL.md").write_text(
        FRONTMATTER.format(name=name, category=domain) + BODY, encoding="utf-8"
    )
    (skill / "references" / "examples.md").write_text(
        "# Examples\n\n```apex\npublic class TriggerHandler { private static Boolean run = true; }\n```\n",
        encoding="utf-8",
    )
    (skill / "references" / "gotchas.md").write_text(
        "# Gotchas\n\nStatics reset per transaction, not per DML statement.\n", encoding="utf-8"
    )
    (skill / "references" / "well-architected.md").write_text(WAF, encoding="utf-8")
    (skill / "references" / "llm-anti-patterns.md").write_text(ANTI_PATTERNS, encoding="utf-8")
    (skill / "templates" / "TriggerHandler.cls").write_text("public class TriggerHandler {}\n", encoding="utf-8")
    (skill / "scripts" / "check_guard.py").write_text(CHECKER, encoding="utf-8")
    return skill


def levels(issues: list[ValidationIssue]) -> set[str]:
    return {issue.level for issue in issues}


def messages(issues: list[ValidationIssue]) -> str:
    return " | ".join(issue.message for issue in issues)


class SkillFixtureMixin:
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="sfskills-val-"))
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        self.skill = make_skill(self.root)
        self.skill_md = self.skill / "SKILL.md"

    def rewrite_frontmatter(self, **overrides) -> None:
        """Replace `key: value` lines in the frontmatter block."""
        lines = self.skill_md.read_text(encoding="utf-8").split("\n")
        for key, value in overrides.items():
            for i, line in enumerate(lines):
                if line.startswith(f"{key}:"):
                    lines[i] = f"{key}: {value}"
                    break
            else:  # pragma: no cover - test authoring error
                raise AssertionError(f"no `{key}:` line to override")
        self.skill_md.write_text("\n".join(lines), encoding="utf-8")

    def drop_frontmatter_key(self, key: str) -> None:
        lines = self.skill_md.read_text(encoding="utf-8").split("\n")
        out, skipping = [], False
        for line in lines:
            if line.startswith(f"{key}:"):
                skipping = True
                continue
            if skipping:
                if line.startswith(("  ", "- ")) or line.strip() == "":
                    if line.startswith("  "):
                        continue
                skipping = False
            out.append(line)
        self.skill_md.write_text("\n".join(out), encoding="utf-8")


class FrontmatterGateTest(SkillFixtureMixin, unittest.TestCase):

    def test_pass_a_well_formed_skill_produces_no_issues(self):
        self.assertEqual(validate_frontmatter(REPO_ROOT, self.skill_md), [])

    def test_fail_missing_required_key(self):
        self.drop_frontmatter_key("outputs")
        issues = validate_frontmatter(REPO_ROOT, self.skill_md)
        self.assertIn("missing frontmatter key `outputs`", messages(issues))
        self.assertEqual(levels(issues), {"ERROR"})

    def test_fail_category_outside_the_enum(self):
        self.rewrite_frontmatter(category="marketing")
        self.assertIn("invalid category", messages(validate_frontmatter(REPO_ROOT, self.skill_md)))

    def test_fail_name_does_not_match_the_folder(self):
        self.rewrite_frontmatter(name="something-else")
        self.assertIn(
            "does not match folder name", messages(validate_frontmatter(REPO_ROOT, self.skill_md))
        )

    def test_fail_category_does_not_match_the_parent_domain_folder(self):
        self.rewrite_frontmatter(category="lwc")
        self.assertIn(
            "does not match parent domain folder",
            messages(validate_frontmatter(REPO_ROOT, self.skill_md)),
        )

    def test_fail_description_without_a_scope_exclusion(self):
        self.rewrite_frontmatter(description='"Prevent recursive trigger execution with a guard."')
        self.assertIn(
            "must include a scope exclusion", messages(validate_frontmatter(REPO_ROOT, self.skill_md))
        )

    def test_fail_scalar_field_that_should_be_a_list(self):
        self.rewrite_frontmatter(dependencies="notalist")
        self.assertIn("`dependencies` must be a list", messages(validate_frontmatter(REPO_ROOT, self.skill_md)))

    def test_fail_todo_marker_in_a_list_field(self):
        text = self.skill_md.read_text(encoding="utf-8").replace(
            "  - the trigger source to review", "  - TODO fill in the input"
        )
        self.skill_md.write_text(text, encoding="utf-8")
        self.assertIn("unfilled TODO marker", messages(validate_frontmatter(REPO_ROOT, self.skill_md)))

    def test_fail_todo_with_a_colon_in_a_list_field_is_caught_by_the_schema(self):
        """Characterization worth knowing: `- TODO: fill this in` is valid YAML
        for a one-key MAPPING, so `item.startswith("TODO")` never fires — the
        item is a dict, not a str. It is still rejected, but by the schema's
        `type: string`, with a less obvious message. Both paths must ERROR."""
        text = self.skill_md.read_text(encoding="utf-8").replace(
            "  - the trigger source to review", "  - TODO: fill in the input"
        )
        self.skill_md.write_text(text, encoding="utf-8")
        issues = validate_frontmatter(REPO_ROOT, self.skill_md)
        self.assertTrue(issues)
        self.assertEqual(levels(issues), {"ERROR"})
        self.assertIn("is not of type 'string'", messages(issues))

    def test_fail_todo_marker_in_the_body(self):
        self.skill_md.write_text(
            self.skill_md.read_text(encoding="utf-8") + "\n\nTODO: write the rest\n", encoding="utf-8"
        )
        self.assertIn(
            "unfilled TODO marker(s)", messages(validate_frontmatter(REPO_ROOT, self.skill_md))
        )

    def test_pass_todo_inside_an_html_comment_is_allowed(self):
        """Scaffold hints in comments are how new_skill.py annotates a template."""
        self.skill_md.write_text(
            self.skill_md.read_text(encoding="utf-8") + "\n\n<!-- TODO: reviewer note -->\n",
            encoding="utf-8",
        )
        self.assertEqual(validate_frontmatter(REPO_ROOT, self.skill_md), [])

    def test_fail_body_under_the_word_floor(self):
        self.skill_md.write_text(
            FRONTMATTER.format(name="trigger-recursion", category="apex") + "\n# Short\n\nToo brief.\n",
            encoding="utf-8",
        )
        self.assertIn(
            f"minimum is {V.SKILL_BODY_MIN_WORDS}", messages(validate_frontmatter(REPO_ROOT, self.skill_md))
        )

    def test_fail_schema_violation_bad_version_string(self):
        self.rewrite_frontmatter(version="1.0")
        self.assertTrue(validate_frontmatter(REPO_ROOT, self.skill_md))

    def test_fail_schema_violation_unknown_key(self):
        """`additionalProperties: false` — a typo'd key must not sail through."""
        self.skill_md.write_text(
            self.skill_md.read_text(encoding="utf-8").replace(
                "version: 1.0.0", "verison: 1.0.0\nversion: 1.0.0"
            ),
            encoding="utf-8",
        )
        self.assertTrue(validate_frontmatter(REPO_ROOT, self.skill_md))


class EnumHintTest(unittest.TestCase):
    """`_humanize_jsonschema_error` turns 'not one of [...]' into a fix."""

    SCHEMA = {
        "type": "object",
        "properties": {"pillar": {"enum": ["Security", "Performance", "Operational Excellence"]}},
    }

    def test_aws_waf_alias_gets_a_named_suggestion(self):
        (message,) = V.validate_with_jsonschema({"pillar": "Performance Efficiency"}, self.SCHEMA)
        self.assertIn("did you mean 'Performance'?", message)
        self.assertIn("AWS WAF", message)

    def test_near_miss_gets_a_fuzzy_suggestion(self):
        (message,) = V.validate_with_jsonschema({"pillar": "Securty"}, self.SCHEMA)
        self.assertIn("did you mean 'Security'?", message)

    def test_unrelated_value_is_left_alone(self):
        (message,) = V.validate_with_jsonschema({"pillar": "Bananas"}, self.SCHEMA)
        self.assertNotIn("did you mean", message)

    def test_non_enum_failures_are_not_rewritten(self):
        schema = {"type": "object", "properties": {"n": {"type": "integer"}}}
        (message,) = V.validate_with_jsonschema({"n": "x"}, schema)
        self.assertNotIn("did you mean", message)

    def test_a_valid_instance_produces_no_messages(self):
        self.assertEqual(V.validate_with_jsonschema({"pillar": "Security"}, self.SCHEMA), [])


class StructureGateTest(SkillFixtureMixin, unittest.TestCase):

    def test_pass_a_complete_package_produces_no_issues(self):
        self.assertEqual(validate_skill_structure(self.skill), [])

    def test_fail_missing_required_reference_file(self):
        (self.skill / "references" / "gotchas.md").unlink()
        issues = validate_skill_structure(self.skill)
        self.assertIn("missing required file `references/gotchas.md`", messages(issues))
        self.assertIn("ERROR", levels(issues))

    def test_fail_empty_templates_directory(self):
        (self.skill / "templates" / "TriggerHandler.cls").unlink()
        self.assertIn("templates/ must contain at least one file", messages(validate_skill_structure(self.skill)))

    def test_fail_templates_holding_only_a_subdirectory(self):
        (self.skill / "templates" / "TriggerHandler.cls").unlink()
        (self.skill / "templates" / "nested").mkdir()
        self.assertIn("templates/ must contain at least one file", messages(validate_skill_structure(self.skill)))

    def test_fail_scripts_without_a_python_file(self):
        (self.skill / "scripts" / "check_guard.py").unlink()
        (self.skill / "scripts" / "check.sh").write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        self.assertIn("at least one Python file", messages(validate_skill_structure(self.skill)))

    def test_fail_missing_llm_anti_patterns_file(self):
        (self.skill / "references" / "llm-anti-patterns.md").unlink()
        self.assertIn(
            "missing `references/llm-anti-patterns.md`", messages(validate_skill_structure(self.skill))
        )

    def test_fail_todo_in_llm_anti_patterns_is_an_error(self):
        path = self.skill / "references" / "llm-anti-patterns.md"
        path.write_text(path.read_text(encoding="utf-8") + "\nTODO: add two more\n", encoding="utf-8")
        issues = validate_skill_structure(self.skill)
        self.assertIn("unfilled TODO marker(s)", messages(issues))
        self.assertIn("ERROR", levels(issues))

    def test_warn_fewer_than_five_anti_patterns(self):
        path = self.skill / "references" / "llm-anti-patterns.md"
        text = path.read_text(encoding="utf-8")
        path.write_text(text.split("## Anti-Pattern 5")[0], encoding="utf-8")
        issues = validate_skill_structure(self.skill)
        self.assertIn("only 4 anti-pattern(s)", messages(issues))
        self.assertEqual(levels(issues), {"WARN"})

    def test_warn_anti_patterns_file_under_the_depth_floor(self):
        (self.skill / "references" / "llm-anti-patterns.md").write_text(
            "\n\n".join(f"## Anti-Pattern {i}\n\nDon't." for i in range(1, 6)), encoding="utf-8"
        )
        issues = validate_skill_structure(self.skill)
        self.assertIn(f"{V.MIN_ANTI_PATTERNS_BYTES}-byte depth floor", messages(issues))
        self.assertEqual(levels(issues), {"WARN"})

    def test_warn_examples_without_a_fenced_block(self):
        (self.skill / "references" / "examples.md").write_text(
            "# Examples\n\nImagine a handler class with a static guard on it.\n", encoding="utf-8"
        )
        issues = validate_skill_structure(self.skill)
        self.assertIn("no fenced block", messages(issues))
        self.assertEqual(levels(issues), {"WARN"})

    def test_pass_a_non_code_fenced_block_satisfies_the_examples_gate(self):
        """Deliberately language-agnostic: a governance skill's worked artifact
        is YAML or metadata XML, not fabricated Apex."""
        (self.skill / "references" / "examples.md").write_text(
            "# Examples\n\n```yaml\nrule: require-guard\nseverity: error\n```\n", encoding="utf-8"
        )
        self.assertEqual(validate_skill_structure(self.skill), [])

    def test_warn_skill_md_without_a_recommended_workflow(self):
        self.skill_md.write_text(
            self.skill_md.read_text(encoding="utf-8").replace("## Recommended Workflow", "## Steps"),
            encoding="utf-8",
        )
        issues = validate_skill_structure(self.skill)
        self.assertIn("no `## Recommended Workflow` section", messages(issues))
        self.assertEqual(levels(issues), {"WARN"})

    def test_fail_well_architected_without_official_sources_used(self):
        (self.skill / "references" / "well-architected.md").write_text(
            "# Well-Architected\n\nReliability discussion.\n", encoding="utf-8"
        )
        issues = validate_skill_structure(self.skill)
        self.assertIn("missing `## Official Sources Used` section", messages(issues))
        self.assertIn("ERROR", levels(issues))

    def test_fail_official_sources_heading_with_no_content(self):
        """The heading alone is the exact rubber-stamp this gate exists to stop."""
        (self.skill / "references" / "well-architected.md").write_text(
            "# Well-Architected\n\nReliability discussion.\n\n## Official Sources Used\n\n",
            encoding="utf-8",
        )
        self.assertIn(
            "section is empty", messages(validate_skill_structure(self.skill))
        )


class CheckerScriptGateTest(SkillFixtureMixin, unittest.TestCase):
    """Always-pass stubs in skill checker scripts."""

    def write_checker(self, source: str) -> None:
        (self.skill / "scripts" / "check_guard.py").write_text(source, encoding="utf-8")

    def test_pass_a_real_checker(self):
        self.assertEqual(validate_skill_structure(self.skill), [])

    def test_warn_too_few_meaningful_lines(self):
        self.write_checker("#!/usr/bin/env python3\n# a comment\nprint('ok')\n")
        self.assertIn("may be a stub", messages(validate_skill_structure(self.skill)))

    def test_comments_and_blank_lines_do_not_count_as_meaningful(self):
        self.write_checker("\n".join(["# c"] * 40 + ["", "print('ok')"]))
        self.assertIn("may be a stub", messages(validate_skill_structure(self.skill)))

    def test_warn_no_conditional_branch(self):
        self.write_checker("\n".join(f"value_{i} = {i}" for i in range(15)) + "\nprint('ERROR nope')\n")
        self.assertIn("no conditional branches", messages(validate_skill_structure(self.skill)))

    def test_warn_no_error_output_path(self):
        source = "\n".join(f"value_{i} = {i}" for i in range(15)) + "\nif value_1:\n    print('fine')\n"
        self.write_checker(source)
        self.assertIn("no error-output path", messages(validate_skill_structure(self.skill)))

    def test_short_file_short_circuits_the_other_two_checks(self):
        """Documented behaviour: a stub gets one message, not three."""
        self.write_checker("print('ok')\n")
        stub_issues = [i for i in validate_skill_structure(self.skill) if "check_guard.py" in i.path]
        self.assertEqual(len(stub_issues), 1)


class AntiPatternCounterTest(unittest.TestCase):
    """`_count_anti_patterns` takes the MAX across formats, never the sum."""

    def test_named_headings(self):
        text = "\n".join(f"## Anti-Pattern {i}\n\nbody\n" for i in range(1, 8))
        self.assertEqual(V._count_anti_patterns(text), 7)

    def test_alternate_heading_nouns(self):
        for noun in ("Pattern", "Mistake", "Common Mistake", "Trap", "Gotcha"):
            text = "\n".join(f"## {noun} {i}\n\nbody\n" for i in range(1, 6))
            self.assertEqual(V._count_anti_patterns(text), 5, noun)

    def test_numbered_headings(self):
        text = "\n".join(f"## {i}. Something wrong\n\nbody\n" for i in range(1, 6))
        self.assertEqual(V._count_anti_patterns(text), 5)

    def test_top_level_numbered_list(self):
        text = "\n".join(f"{i}. Something wrong" for i in range(1, 7))
        self.assertEqual(V._count_anti_patterns(text), 6)

    def test_repeated_list_markers_count_once(self):
        """Markdown lets every item be `1.`; counting the raw matches would
        inflate a 1-item file to 5."""
        self.assertEqual(V._count_anti_patterns("1. a\n1. b\n1. c\n1. d\n1. e"), 1)

    def test_mixed_formats_take_the_max_not_the_sum(self):
        text = "## Anti-Pattern 1\n\nbody\n\n## Anti-Pattern 2\n\nbody\n\n1. one\n2. two\n3. three\n"
        self.assertEqual(V._count_anti_patterns(text), 3)

    def test_numbered_lines_inside_a_code_fence_are_not_counted(self):
        text = "```\n1. not an anti pattern\n2. also not\n3. nope\n4. no\n5. no\n```\n\n## Anti-Pattern 1\n\nbody\n"
        self.assertEqual(V._count_anti_patterns(text), 1)

    def test_inline_backticks_in_prose_do_not_eat_headings(self):
        text = "Use the ```json fence like so.\n\n" + "\n".join(
            f"## Anti-Pattern {i}\n\nbody\n" for i in range(1, 6)
        )
        self.assertEqual(V._count_anti_patterns(text), 5)

    def test_empty_text(self):
        self.assertEqual(V._count_anti_patterns(""), 0)


class AuthoringStyleGateTest(SkillFixtureMixin, unittest.TestCase):

    def test_pass_a_clean_skill(self):
        self.assertEqual(validate_skill_authoring_style(self.skill), [])

    def test_fail_when_to_use_section_duplicates_the_description(self):
        self.skill_md.write_text(
            self.skill_md.read_text(encoding="utf-8") + "\n## When To Use\n\nWhen a trigger re-enters.\n",
            encoding="utf-8",
        )
        issues = validate_skill_authoring_style(self.skill)
        self.assertIn("§ 6.1", messages(issues))
        self.assertIn("ERROR", levels(issues))

    def test_fail_lowercase_and_extended_when_to_use_variants(self):
        for heading in ("## When to use", "## When to use this skill", "## When To Use It"):
            with self.subTest(heading=heading):
                self.skill_md.write_text(
                    FRONTMATTER.format(name="trigger-recursion", category="apex")
                    + BODY
                    + f"\n{heading}\n\ntext\n",
                    encoding="utf-8",
                )
                self.assertIn("§ 6.1", messages(validate_skill_authoring_style(self.skill)))

    def test_pass_an_h3_when_to_use_subheading_is_legitimate(self):
        """`### When to Use Flow` is a decision-tree branch, not a duplicate."""
        self.skill_md.write_text(
            self.skill_md.read_text(encoding="utf-8") + "\n### When to Use Flow\n\ntext\n",
            encoding="utf-8",
        )
        self.assertEqual(validate_skill_authoring_style(self.skill), [])

    def test_fail_inline_pillar_mapping_when_the_reference_has_content(self):
        self.skill_md.write_text(
            self.skill_md.read_text(encoding="utf-8")
            + "\n## Well-Architected Pillars\n\nReliability: guards.\n",
            encoding="utf-8",
        )
        self.assertIn("§ 6.4", messages(validate_skill_authoring_style(self.skill)))

    def test_pass_inline_pillar_mapping_when_the_reference_is_a_stub(self):
        """The gate is 'map once', not 'never map' — with no real reference
        file the SKILL.md section is the only mapping there is."""
        (self.skill / "references" / "well-architected.md").write_text("# WAF\n", encoding="utf-8")
        self.skill_md.write_text(
            self.skill_md.read_text(encoding="utf-8")
            + "\n## Well-Architected Pillars\n\nReliability: guards.\n",
            encoding="utf-8",
        )
        self.assertEqual(validate_skill_authoring_style(self.skill), [])

    def test_fail_paragraph_duplicated_verbatim_into_gotchas(self):
        shared = (
            "A static Boolean on the handler is the cheapest recursion guard, and it resets "
            "between transactions because static state is per-transaction. It is not a lock "
            "and it does not survive a chained asynchronous context.\n"
        )
        self.skill_md.write_text(
            self.skill_md.read_text(encoding="utf-8") + "\n" + shared, encoding="utf-8"
        )
        (self.skill / "references" / "gotchas.md").write_text(
            "# Gotchas\n\n" + shared, encoding="utf-8"
        )
        issues = validate_skill_authoring_style(self.skill)
        self.assertIn("§ 6.6", messages(issues))
        self.assertIn("ERROR", levels(issues))

    def test_pass_short_shared_phrasing_is_not_duplication(self):
        short = "Statics reset per transaction.\n"
        self.skill_md.write_text(self.skill_md.read_text(encoding="utf-8") + "\n" + short, encoding="utf-8")
        (self.skill / "references" / "gotchas.md").write_text("# Gotchas\n\n" + short, encoding="utf-8")
        self.assertEqual(validate_skill_authoring_style(self.skill), [])

    def test_pass_a_shared_citation_list_is_not_duplication(self):
        """URLs are legitimately repeated across a skill's files."""
        citations = (
            "- https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_triggers.htm\n"
            "- https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_gov_limits.htm\n"
            "- https://architect.salesforce.com/well-architected/adaptable/resilient/\n"
        )
        self.skill_md.write_text(
            self.skill_md.read_text(encoding="utf-8") + "\n" + citations, encoding="utf-8"
        )
        (self.skill / "references" / "gotchas.md").write_text(
            "# Gotchas\n\n" + citations, encoding="utf-8"
        )
        self.assertEqual(validate_skill_authoring_style(self.skill), [])

    def test_missing_skill_md_returns_no_issues(self):
        self.skill_md.unlink()
        self.assertEqual(validate_skill_authoring_style(self.skill), [])


class ParallelProseGateTest(SkillFixtureMixin, unittest.TestCase):
    """§ 6.2 — runs of 4+ `- **X** — ...` bullets should be a table."""

    def body_with(self, section: str) -> None:
        self.skill_md.write_text(
            FRONTMATTER.format(name="trigger-recursion", category="apex") + BODY + section,
            encoding="utf-8",
        )

    BULLET = "- **Term {i}** — a short parallel definition of the term.\n"

    def test_warn_at_four_consecutive_bullets(self):
        self.body_with("\n## Terms\n\n" + "".join(self.BULLET.format(i=i) for i in range(4)))
        issues = validate_skill_authoring_style(self.skill)
        self.assertIn("consecutive", messages(issues))
        self.assertEqual(levels(issues), {"WARN"})

    def test_pass_at_three_consecutive_bullets(self):
        self.body_with("\n## Terms\n\n" + "".join(self.BULLET.format(i=i) for i in range(3)))
        self.assertEqual(validate_skill_authoring_style(self.skill), [])

    def test_pass_when_the_run_is_broken_by_a_heading(self):
        """No blank line anywhere — only the heading can end the run, so this
        fails if the heading branch stops flushing."""
        half = "".join(self.BULLET.format(i=i) for i in range(3))
        self.body_with(f"\n## A\n{half}## B\n{half}")
        self.assertEqual(validate_skill_authoring_style(self.skill), [])

    def test_pass_when_the_run_is_broken_by_a_paragraph(self):
        half = "".join(self.BULLET.format(i=i) for i in range(3))
        self.body_with(f"\n## Terms\n\n{half}\nAn intervening sentence.\n\n{half}")
        self.assertEqual(validate_skill_authoring_style(self.skill), [])

    def test_warn_when_six_bullets_run_unbroken_under_one_heading(self):
        """The control for the two tests above: same bullet count, no break."""
        self.body_with("\n## Terms\n" + "".join(self.BULLET.format(i=i) for i in range(6)))
        self.assertIn("6 consecutive", messages(validate_skill_authoring_style(self.skill)))

    def test_pass_under_the_related_skills_exemption(self):
        self.body_with("\n## Related Skills\n\n" + "".join(self.BULLET.format(i=i) for i in range(6)))
        self.assertEqual(validate_skill_authoring_style(self.skill), [])

    def test_pass_when_bullets_are_paragraph_length(self):
        """Median > 220 chars means these are prose, not a table in disguise."""
        long_bullet = "- **Term {i}** — " + ("a genuinely long explanatory clause " * 8) + "\n"
        self.body_with("\n## Terms\n\n" + "".join(long_bullet.format(i=i) for i in range(5)))
        self.assertEqual(validate_skill_authoring_style(self.skill), [])

    def test_pass_when_the_bullets_are_inside_a_code_fence(self):
        fenced = "\n## Terms\n\n```markdown\n" + "".join(self.BULLET.format(i=i) for i in range(6)) + "```\n"
        self.body_with(fenced)
        self.assertEqual(validate_skill_authoring_style(self.skill), [])

    def test_warn_names_the_line_range(self):
        self.body_with("\n## Terms\n\n" + "".join(self.BULLET.format(i=i) for i in range(5)))
        (issue,) = validate_skill_authoring_style(self.skill)
        self.assertRegex(issue.message, r"^L\d+–L\d+: 5 consecutive")

    def test_frontmatter_bullets_are_not_counted(self):
        """The scanner skips the frontmatter block — `tags:` list items must
        never trip § 6.2."""
        self.body_with("")
        self.assertEqual(validate_skill_authoring_style(self.skill), [])


class MedianTest(unittest.TestCase):

    def test_odd_length(self):
        self.assertEqual(V._median_int([3, 1, 2]), 2.0)

    def test_even_length_averages_the_middle_pair(self):
        self.assertEqual(V._median_int([1, 2, 3, 4]), 2.5)

    def test_empty(self):
        self.assertEqual(V._median_int([]), 0.0)


class RecordAndSourceSchemaTest(unittest.TestCase):
    """The registry/knowledge schema wrappers — thin, but they choose the
    `path` field that the CLI prints, and a wrong one sends authors to the
    wrong file."""

    RECORD = {
        "id": "apex/trigger-recursion",
        "name": "trigger-recursion",
        "category": "apex",
        "description": "Prevent recursive trigger execution. NOT for Flow.",
        "file_location": "skills/apex/trigger-recursion/SKILL.md",
    }

    def test_a_structurally_invalid_record_reports_against_its_file_location(self):
        issues = validate_skill_registry_record(REPO_ROOT, {**self.RECORD, "category": 17})
        self.assertTrue(issues)
        self.assertEqual(issues[0].path, "skills/apex/trigger-recursion/SKILL.md")
        self.assertEqual(levels(issues), {"ERROR"})

    def test_a_record_without_a_file_location_falls_back_to_registry(self):
        issues = validate_skill_registry_record(REPO_ROOT, {"category": 17})
        self.assertTrue(issues)
        self.assertEqual(issues[0].path, "registry")

    def test_an_invalid_knowledge_source_reports_against_its_id(self):
        issues = validate_knowledge_source(REPO_ROOT, {"id": "src-x", "trust": 42})
        self.assertTrue(issues)
        self.assertEqual(issues[0].path, "src-x")


class SimilarityGateTest(unittest.TestCase):
    """Near-duplicate detection is WARN by design — the corpus has intentional
    parallels (bitbucket-pipelines vs gitlab-ci vs github-actions)."""

    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="sfskills-sim-"))
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)

    def test_a_near_clone_is_flagged_as_warn(self):
        a = make_skill(self.root, "apex", "trigger-recursion")
        make_skill(self.root, "apex", "trigger-recursion-guard")
        issues = validate_skill_similarity(self.root, [a / "SKILL.md"], threshold=0.5)
        self.assertTrue(issues, "an all-but-identical sibling must be flagged")
        self.assertEqual(levels(issues), {"WARN"})
        self.assertIn("near-duplicate of `apex/trigger-recursion-guard`", messages(issues))

    def test_a_distinct_skill_is_not_flagged(self):
        a = make_skill(self.root, "apex", "trigger-recursion")
        lwc = make_skill(self.root, "lwc", "wire-adapters")
        text = (lwc / "SKILL.md").read_text(encoding="utf-8")
        text = text.replace(
            '"Prevent recursive trigger execution using a static guard. NOT for Flow recursion."',
            '"Provision data reactively into a Lightning web component. NOT for imperative Apex calls."',
        ).replace("  - apex\n  - trigger\n", "  - lwc\n  - wire\n").replace(
            "  - trigger fires twice on update\n"
            "  - recursive trigger execution guard\n"
            "  - static boolean recursion flag\n",
            "  - wire adapter returns undefined\n"
            "  - reactive property in a wire\n"
            "  - refreshApex after a mutation\n",
        )
        (lwc / "SKILL.md").write_text(text, encoding="utf-8")
        self.assertEqual(validate_skill_similarity(self.root, [a / "SKILL.md"], threshold=0.5), [])

    def test_a_pair_is_reported_once_not_twice(self):
        a = make_skill(self.root, "apex", "trigger-recursion")
        b = make_skill(self.root, "apex", "trigger-recursion-guard")
        issues = validate_skill_similarity(
            self.root, [a / "SKILL.md", b / "SKILL.md"], threshold=0.5
        )
        self.assertEqual(len(issues), 1)

    def test_empty_input_short_circuits(self):
        self.assertEqual(validate_skill_similarity(self.root, []), [])

    def test_threshold_of_one_flags_nothing(self):
        a = make_skill(self.root, "apex", "trigger-recursion")
        make_skill(self.root, "apex", "trigger-recursion-guard")
        self.assertEqual(validate_skill_similarity(self.root, [a / "SKILL.md"], threshold=1.01), [])


class OfficialSourcesUniquenessTest(unittest.TestCase):
    """A per-domain source list pasted across N skills satisfies the structural
    gate but is not grounding for any of them."""

    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="sfskills-src-"))
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)

    def set_sources(self, skill: Path, block: str) -> None:
        (skill / "references" / "well-architected.md").write_text(
            "# Well-Architected\n\nDiscussion.\n\n## Official Sources Used\n\n" + block,
            encoding="utf-8",
        )

    def test_identical_blocks_in_the_same_domain_are_flagged(self):
        a = make_skill(self.root, "apex", "trigger-recursion")
        make_skill(self.root, "apex", "trigger-recursion-guard")
        issues = validate_official_sources_uniqueness(self.root, [a / "SKILL.md"])
        self.assertEqual(len(issues), 1)
        self.assertEqual(levels(issues), {"WARN"})
        self.assertIn("apex/trigger-recursion-guard", messages(issues))
        self.assertTrue(issues[0].path.endswith("well-architected.md"))

    def test_distinct_blocks_are_not_flagged(self):
        a = make_skill(self.root, "apex", "trigger-recursion")
        b = make_skill(self.root, "apex", "trigger-recursion-guard")
        self.set_sources(a, "- https://example.salesforce.com/one\n")
        self.set_sources(b, "- https://example.salesforce.com/two\n")
        self.assertEqual(validate_official_sources_uniqueness(self.root, [a / "SKILL.md"]), [])

    def test_cross_domain_reuse_is_deliberately_allowed(self):
        a = make_skill(self.root, "security", "named-credential-hardening")
        make_skill(self.root, "integration", "named-credential-setup")
        self.assertEqual(validate_official_sources_uniqueness(self.root, [a / "SKILL.md"]), [])

    def test_whitespace_only_differences_still_collide(self):
        """The fingerprint strips per-line whitespace, so reindenting a pasted
        block is not a fix."""
        a = make_skill(self.root, "apex", "trigger-recursion")
        b = make_skill(self.root, "apex", "trigger-recursion-guard")
        self.set_sources(a, "- https://example.salesforce.com/one\n")
        self.set_sources(b, "   - https://example.salesforce.com/one   \n\n")
        self.assertEqual(len(validate_official_sources_uniqueness(self.root, [a / "SKILL.md"])), 1)

    def test_only_skills_in_skill_paths_are_reported(self):
        """Corpus-level by construction — the map covers everything, but a
        shard must only report on its own members."""
        make_skill(self.root, "apex", "trigger-recursion")
        make_skill(self.root, "apex", "trigger-recursion-guard")
        c = make_skill(self.root, "apex", "trigger-recursion-third")
        issues = validate_official_sources_uniqueness(self.root, [c / "SKILL.md"])
        self.assertEqual(len(issues), 1)
        self.assertTrue(issues[0].path.endswith("trigger-recursion-third/references/well-architected.md"))

    def test_a_skill_with_no_official_sources_section_is_skipped(self):
        a = make_skill(self.root, "apex", "trigger-recursion")
        make_skill(self.root, "apex", "trigger-recursion-guard")
        (a / "references" / "well-architected.md").write_text("# WAF\n\nNo sources heading.\n", encoding="utf-8")
        self.assertEqual(validate_official_sources_uniqueness(self.root, [a / "SKILL.md"]), [])

    def test_an_empty_sources_block_is_skipped_not_grouped(self):
        """Otherwise every empty block would collide with every other one and
        bury the real signal."""
        a = make_skill(self.root, "apex", "trigger-recursion")
        b = make_skill(self.root, "apex", "trigger-recursion-guard")
        for skill in (a, b):
            self.set_sources(skill, "\n")
        self.assertEqual(validate_official_sources_uniqueness(self.root, [a / "SKILL.md"]), [])


if __name__ == "__main__":
    unittest.main()
