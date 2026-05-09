"""Unit tests for the v0.4.2 scoring rewrite in ``library.py``.

These cover the building blocks the integration tests in test_library.py
exercise via search_agents / search_templates / search_decision_trees.
Direct unit tests on the private helpers protect against silent regressions
when the scoring weights are tuned.

Specifically: the v0.4.2 release relies on slug-aware whole-word matching,
a light suffix stemmer, a slug coverage bonus, and a bigram bonus on top of
free-text title/heading/body counts. If any of those signals stops firing,
agent / template / tree retrieval falls back toward the old 18% / 25% /
56% Hit@1 numbers.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE.parent / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from sfskills_mcp import library  # noqa: E402


class IdentTokensTest(unittest.TestCase):
    """Identifier splitter handles kebab-case, snake_case, CamelCase, paths,
    and dotted extensions."""

    def test_kebab_case(self) -> None:
        self.assertEqual(
            library._ident_tokens("admin-skill-builder"),
            ["admin", "skill", "builder"],
        )

    def test_path_with_camelcase_and_dot(self) -> None:
        self.assertEqual(
            library._ident_tokens("apex/TriggerHandler.cls"),
            ["apex", "trigger", "handler", "cls"],
        )

    def test_snake_case(self) -> None:
        self.assertEqual(
            library._ident_tokens("test_data_factory"),
            ["test", "data", "factory"],
        )

    def test_consecutive_caps(self) -> None:
        # SOQLBuilder → ["soql", "builder"], not ["s","o","q","l","builder"].
        self.assertEqual(
            library._ident_tokens("SOQLBuilder"),
            ["soql", "builder"],
        )

    def test_empty_input(self) -> None:
        self.assertEqual(library._ident_tokens(""), [])
        self.assertEqual(library._ident_tokens(None), [])


class StemTest(unittest.TestCase):
    """Light suffix stripper for slug/query token matching.

    Goals:
    - Handle morphological pairs that appeared in the v0.4.2 audit:
      consolidate ↔ consolidator, build ↔ builder, stories ↔ story,
      review ↔ reviewer.
    - Don't be aggressive — short words stay intact ("audit" stays "audit").
    """

    def test_consolidator_consolidate_share_stem(self) -> None:
        self.assertEqual(library._stem("consolidator"), library._stem("consolidate"))

    def test_builder_builds_share_stem(self) -> None:
        self.assertEqual(library._stem("builder"), library._stem("build"))

    def test_stories_story_share_stem(self) -> None:
        self.assertEqual(library._stem("stories"), library._stem("story"))

    def test_short_words_unchanged(self) -> None:
        # ≤4 chars are never stemmed — avoid mangling "fls", "owd", "soql".
        for short in ("fls", "owd", "soql", "test"):
            self.assertEqual(library._stem(short), short)

    def test_audit_unchanged(self) -> None:
        # "audit" doesn't end in any of the suffix rules — should be stable.
        self.assertEqual(library._stem("audit"), "audit")


class BigramMatchCountTest(unittest.TestCase):
    def test_adjacent_pair_in_target(self) -> None:
        # ["a","b","c"] has bigrams (a,b) and (b,c).
        n = library._bigram_match_count(["a", "b", "c"], ["x", "a", "b", "y"])
        self.assertEqual(n, 1)  # only (a,b) appears adjacent in target

    def test_no_match(self) -> None:
        n = library._bigram_match_count(["a", "b"], ["x", "y", "z"])
        self.assertEqual(n, 0)

    def test_too_short_to_have_bigrams(self) -> None:
        self.assertEqual(library._bigram_match_count(["a"], ["a", "b", "c"]), 0)
        self.assertEqual(library._bigram_match_count(["a", "b"], ["a"]), 0)

    def test_pair_must_be_adjacent_in_target(self) -> None:
        # query bigram (a,c) — those tokens exist in target but aren't adjacent.
        n = library._bigram_match_count(["a", "c"], ["a", "b", "c"])
        self.assertEqual(n, 0)


class ScoreTest(unittest.TestCase):
    """End-to-end of the _score function — the core retrieval signal.

    The weights are public-API in spirit: changing them changes Hit@1 across
    the audits in evals/measurement/. These tests pin the relative ordering
    that drives the audit numbers, not exact float values.
    """

    def test_slug_match_dominates_body_match(self) -> None:
        """The reason agents went 18→95% Hit@1: slug match (15×) beats
        body substring counts even when body has many hits."""
        terms = ["consolid", "trigger"]
        # Slug match: 2 tokens hit, 0 body — should score high.
        slug_match = library._score(
            terms,
            name_tokens=["trigger", "consolidator"],
            title="",
            headings="",
            body="",
        )
        # Body-only: same query terms appear 50× in body, no slug match.
        body_only = library._score(
            terms,
            name_tokens=["apex", "builder"],
            title="",
            headings="",
            body=" trigger consolid " * 50,
        )
        self.assertGreater(slug_match, body_only)

    def test_slug_coverage_bonus_breaks_partial_match_ties(self) -> None:
        """Full-coverage slug match beats half-coverage even when both
        have the same number of slug hits."""
        terms = ["audit", "router"]
        full_cov = library._score(
            terms, name_tokens=["audit", "router"],
            title="", headings="", body="",
        )
        half_cov = library._score(
            terms, name_tokens=["audit", "router", "and", "more", "tokens"],
            title="", headings="", body="",
        )
        self.assertGreater(full_cov, half_cov)

    def test_bigram_bonus_fires_on_adjacent_match(self) -> None:
        """Two tokens adjacent in slug score higher than the same two
        tokens scattered."""
        terms_adjacent = ["agentforce", "action"]
        adjacent = library._score(
            terms_adjacent,
            name_tokens=["agentforce", "action", "builder"],
            title="", headings="", body="",
        )
        scattered = library._score(
            terms_adjacent,
            name_tokens=["agentforce", "stuff", "between", "action"],
            title="", headings="", body="",
        )
        self.assertGreater(adjacent, scattered)

    def test_stop_words_dropped(self) -> None:
        """A query of pure stopwords falls back to as-is rather than empty."""
        score_with_stops = library._score(
            ["the", "of", "is", "trigger"],
            name_tokens=["trigger", "consolidator"],
        )
        score_no_stops = library._score(
            ["trigger"],
            name_tokens=["trigger", "consolidator"],
        )
        # The stop words add nothing; only "trigger" should score.
        self.assertEqual(score_with_stops, score_no_stops)

    def test_body_count_sqrt_capped(self) -> None:
        """100× term frequency is capped close to sqrt(100)=10× contribution
        instead of 100×, so meta-documents can't drown specific docs."""
        terms = ["apex"]
        once = library._score(terms, name_tokens=[], body="apex")
        hundred = library._score(terms, name_tokens=[], body="apex " * 100)
        # If linear, hundred would be 100x once. With sqrt, ~10x.
        self.assertLess(hundred, once * 15)
        self.assertGreater(hundred, once)

    def test_empty_query_scores_zero(self) -> None:
        self.assertEqual(library._score([], name_tokens=["foo"]), 0.0)

    def test_stem_match_below_exact_match(self) -> None:
        """Exact slug match worth more than stem-match, but stem still
        contributes."""
        exact = library._score(
            ["builder"],
            name_tokens=["builder"],
            title="", headings="", body="",
        )
        stemmed = library._score(
            ["build"],
            name_tokens=["builder"],
            title="", headings="", body="",
        )
        no_match = library._score(
            ["xyz"],
            name_tokens=["builder"],
            title="", headings="", body="",
        )
        self.assertGreater(exact, stemmed)
        self.assertGreater(stemmed, no_match)


class IntegrationRegressionTest(unittest.TestCase):
    """Pin the v0.4.2 audit headline numbers as integration regressions.

    If any of these assertions starts failing, retrieval quality degraded —
    likely because the scorer was edited in a way that broke the
    measurements committed to CHANGELOG.md / config/retrieval-config.yaml.
    """

    def test_admin_skill_builder_query_lands(self) -> None:
        """The v0.4.2 motivating example: 'admin skill builder' was hitting
        object-designer at the old scorer. Should now hit admin-skill-builder
        within top 3."""
        out = library.search_agents("admin skill builder", limit=5)
        names = [a["name"] for a in out["agents"][:3]]
        self.assertIn("admin-skill-builder", names, f"top3: {names}")

    def test_consolidate_my_apex_triggers_lands_specific_agent(self) -> None:
        """Stem match (consolidate ↔ consolidator) plus slug coverage means
        trigger-consolidator should beat the broader apex-builder."""
        out = library.search_agents("consolidate my apex triggers", limit=5)
        names = [a["name"] for a in out["agents"][:3]]
        self.assertIn("trigger-consolidator", names, f"top3: {names}")

    def test_trigger_handler_template_top1(self) -> None:
        out = library.search_templates("trigger handler skeleton", limit=5)
        paths = [t["path"] for t in out["templates"][:1]]
        self.assertEqual(
            paths,
            ["apex/TriggerHandler.cls"],
            f"top1: {paths}",
        )

    def test_decision_tree_async_for_queueable_query(self) -> None:
        out = library.search_decision_trees("queueable vs batch", limit=5)
        names = [t["name"] for t in out["trees"][:1]]
        self.assertEqual(names, ["async-selection"], f"top1: {names}")


if __name__ == "__main__":
    unittest.main()
