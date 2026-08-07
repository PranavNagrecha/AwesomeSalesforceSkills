"""Unit tests for ``pipelines/ranking.py``.

``ranking.py`` decides which skill a query resolves to, for BOTH consumers:
``scripts/search_knowledge.py`` (CLI) and
``mcp/sfskills-mcp/src/sfskills_mcp/skills.py`` (MCP ``search_skill``). It had
no tests, and it has been changed twice for measured retrieval reasons — the
2026-07-31 name/description centrality bonus and the max_score-vs-cumulative
gate fix. Both changes are the kind that regress silently.

Everything here is pure-function and hermetic: synthetic row dicts, no
``vector_index/`` artifacts, no corpus, no embedding model.

Three properties are load-bearing enough to call out:

1. **Positional back-compat.** ``rows`` and ``limit`` must stay
   POSITIONAL_OR_KEYWORD. ``skills.py`` calls
   ``aggregate_skill_scores(ranked, bounded_limit, skill_meta=..., ...)`` —
   promoting either to keyword-only breaks the MCP server at runtime, not at
   import, so nothing else would catch it.
2. **``max_score`` and ``score`` are different units.** ``max_score`` is the
   single best chunk; ``score`` is the cumulative sum over every chunk the
   skill contributed. Ranking sorts on ``rank_score`` (derived from
   ``max_score``); the coverage gate in both callers reads ``max_score`` OR
   ``score``. Collapsing the two is the exact production bug the OR in that
   gate was written to fix.
3. **The bonus ranks, it does not gate.** ``rank_score`` carries the
   name/description bonus; ``score`` and ``max_score`` never do.
"""

from __future__ import annotations

import inspect
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pipelines import ranking  # noqa: E402
from pipelines.ranking import (  # noqa: E402
    _name_match_bonus,
    _tokens,
    aggregate_skill_scores,
    collect_official_sources,
    rerank_results,
)


def chunk_row(skill_id, score, path="skills/x/y/SKILL.md", **extra):
    """A minimal post-``rerank_results`` row as ``aggregate_skill_scores`` sees it."""
    row = {"skill_id": skill_id, "score": score, "path": path}
    row.update(extra)
    return row


def lexical_row(chunk_id, skill_id="apex/example", domain="apex", **extra):
    """A minimal pre-rerank row as ``search_index`` returns it."""
    row = {"chunk_id": chunk_id, "skill_id": skill_id, "domain": domain}
    row.update(extra)
    return row


class TokenizerTest(unittest.TestCase):
    """``_tokens`` is frozen by measurement — the +15pp Hit@1 number and the
    tuned name/description weights in config/retrieval-config.yaml are tied to
    this exact stopword set and >2-char rule."""

    def test_splits_on_non_alphanumerics_and_lowercases(self):
        self.assertEqual(_tokens("Trigger-Recursion_Guard"), {"trigger", "recursion", "guard"})

    def test_drops_stopwords(self):
        # "how", "do", "i", "in", "salesforce" are all in _STOPWORDS.
        self.assertEqual(_tokens("how do i bulkify in salesforce"), {"bulkify"})

    def test_drops_tokens_of_two_chars_or_fewer(self):
        self.assertEqual(_tokens("id vs ids"), {"ids"})

    def test_empty_and_none_are_empty_sets(self):
        self.assertEqual(_tokens(""), set())
        self.assertEqual(_tokens(None), set())

    def test_digits_are_kept_only_above_two_characters(self):
        """Characterization, not endorsement: the >2-char rule applies to
        digits too, so `api 67.0` yields no version token at all (`67` is two
        chars, `0` is one). The name/description bonus therefore carries zero
        API-version signal. Frozen by measurement — see _STOPWORDS comment."""
        self.assertEqual(_tokens("api 67.0"), {"api"})
        self.assertEqual(_tokens("bulk api 2000 records"), {"bulk", "api", "2000", "records"})


class NameMatchBonusTest(unittest.TestCase):
    """The centrality signal: 'is this skill ABOUT X', not 'does it mention X'."""

    META = {
        "apex/trigger-recursion": (
            "trigger-recursion",
            "Prevent recursive trigger execution with a static guard.",
        )
    }

    def test_empty_query_scores_zero(self):
        self.assertEqual(
            _name_match_bonus(set(), "apex/trigger-recursion", self.META, 1.5, 0.5), 0.0
        )

    def test_full_name_overlap_is_the_full_name_weight(self):
        # Both query tokens appear in the name -> name_overlap == 1.0.
        # Neither "trigger" nor "recursion"... both DO appear in the description
        # too ("recursive" stems differently, "trigger" matches), so assert the
        # exact composite rather than the name term alone.
        bonus = _name_match_bonus(
            {"trigger", "recursion"}, "apex/trigger-recursion", self.META, 1.5, 0.5
        )
        # name: 2/2 = 1.0 -> 1.5 ; description tokens are
        # {prevent, recursive, trigger, execution, with, static, guard}
        # -> overlap {trigger} = 1/2 = 0.5 -> 0.25
        self.assertAlmostEqual(bonus, 1.75)

    def test_overlap_is_a_fraction_of_the_query_not_the_name(self):
        """A long descriptive skill name must not be penalised, and a long
        query must not be trivially satisfied."""
        meta = {"apex/a-very-long-descriptive-skill-name-here": ("a-very-long-descriptive-skill-name-here", "")}
        one_of_one = _name_match_bonus(
            {"descriptive"}, "apex/a-very-long-descriptive-skill-name-here", meta, 1.5, 0.5
        )
        one_of_four = _name_match_bonus(
            {"descriptive", "alpha", "bravo", "charlie"},
            "apex/a-very-long-descriptive-skill-name-here",
            meta,
            1.5,
            0.5,
        )
        self.assertAlmostEqual(one_of_one, 1.5)
        self.assertAlmostEqual(one_of_four, 1.5 * 0.25)

    def test_unknown_skill_falls_back_to_the_slug(self):
        """A skill missing from skill_meta still gets a name signal from its own
        slug — registry lag must not silently zero the bonus."""
        bonus = _name_match_bonus({"picklist", "governance"}, "admin/picklist-governance", {}, 1.5, 0.5)
        self.assertAlmostEqual(bonus, 1.5)

    def test_no_overlap_scores_zero(self):
        self.assertEqual(
            _name_match_bonus({"omniscript"}, "apex/trigger-recursion", self.META, 1.5, 0.5), 0.0
        )

    def test_weights_are_applied_independently(self):
        meta = {"d/s": ("unrelated-name", "bulkify")}
        self.assertAlmostEqual(_name_match_bonus({"bulkify"}, "d/s", meta, 1.5, 0.5), 0.5)
        self.assertAlmostEqual(_name_match_bonus({"bulkify"}, "d/s", meta, 1.5, 2.0), 2.0)


class AggregateBackCompatTest(unittest.TestCase):
    """``mcp/sfskills-mcp/src/sfskills_mcp/skills.py`` calls this positionally."""

    def test_rows_and_limit_are_positional(self):
        params = list(inspect.signature(aggregate_skill_scores).parameters.values())
        self.assertEqual([p.name for p in params[:2]], ["rows", "limit"])
        for param in params[:2]:
            self.assertEqual(
                param.kind,
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
                f"`{param.name}` must stay positional — sfskills_mcp.skills.search_skill "
                "calls aggregate_skill_scores(ranked, bounded_limit) positionally",
            )

    def test_two_positional_args_is_a_working_call(self):
        result = aggregate_skill_scores([chunk_row("apex/a", 1.0)], 5)
        self.assertEqual([r["id"] for r in result], ["apex/a"])

    def test_every_other_parameter_is_keyword_only_and_defaulted(self):
        """Guards the other direction: a new positional parameter appended after
        ``limit`` would silently change what a 3-arg caller means."""
        params = list(inspect.signature(aggregate_skill_scores).parameters.values())
        for param in params[2:]:
            self.assertEqual(param.kind, inspect.Parameter.KEYWORD_ONLY, param.name)
            self.assertIsNot(param.default, inspect.Parameter.empty, param.name)

    def test_the_mcp_calling_convention_works_end_to_end(self):
        """Exercises the MCP server's exact calling convention BEHAVIOURALLY.

        ``sfskills_mcp.skills.search_skill`` calls::

            aggregate_skill_scores(
                ranked, bounded_limit,
                skill_meta=..., query=...,
                name_weight=..., description_weight=...,
            )

        i.e. two positional args plus four keyword args. This test makes that
        same call and asserts on the result, rather than grepping the call
        site's source text for an exact newline-and-indentation substring — the
        previous version of this test matched
        ``"aggregate_skill_scores(\\n        ranked,\\n        bounded_limit,"``
        and so was broken by any cosmetic reformat (black, a rename, a changed
        indent level) that left the contract perfectly intact.

        If the signature regresses — either arg promoted to keyword-only, or a
        new positional inserted — this raises TypeError or silently misbinds,
        and the shape assertions catch it."""
        rows = [
            chunk_row("apex/bulkify-triggers", 1.0, path="p-best"),
            chunk_row("apex/bulkify-triggers", 0.4, path="p-worse"),
            chunk_row("lwc/wire-adapters", 0.6),
        ]
        result = aggregate_skill_scores(
            rows,
            5,
            skill_meta={"apex/bulkify-triggers": ("Bulkify triggers", "Bulk-safe Apex")},
            query="bulkify",
            name_weight=1.5,
            description_weight=0.5,
        )

        self.assertEqual([r["id"] for r in result], ["apex/bulkify-triggers", "lwc/wire-adapters"])
        for record in result:
            for key in ("id", "score", "max_score", "rank_score", "hit_count", "path"):
                self.assertIn(key, record)
        best = result[0]
        self.assertAlmostEqual(best["max_score"], 1.0)
        self.assertAlmostEqual(best["score"], 1.4)
        self.assertEqual(best["hit_count"], 2)
        self.assertEqual(best["path"], "p-best")
        # the name bonus applies to rank_score only, never to the gate inputs
        self.assertGreater(best["rank_score"], best["max_score"])

    def test_limit_is_honoured_when_passed_positionally(self):
        """The second positional is ``limit``, not something else. A newly
        inserted positional parameter would make this bind the wrong value."""
        rows = [chunk_row(f"apex/s{i}", 1.0 - i / 100) for i in range(10)]
        self.assertEqual(len(aggregate_skill_scores(rows, 3)), 3)


class AggregateScoringTest(unittest.TestCase):

    def test_rolls_chunks_up_and_counts_hits(self):
        rows = [
            chunk_row("apex/a", 1.0, path="p-best"),
            chunk_row("apex/a", 0.4, path="p-worse"),
            chunk_row("apex/a", 0.25, path="p-worst"),
        ]
        (record,) = aggregate_skill_scores(rows, 5)
        self.assertAlmostEqual(record["score"], 1.65)
        self.assertAlmostEqual(record["max_score"], 1.0)
        self.assertEqual(record["hit_count"], 3)
        self.assertEqual(record["path"], "p-best")

    def test_path_tracks_the_best_chunk_not_the_first(self):
        rows = [chunk_row("apex/a", 0.3, path="p-weak"), chunk_row("apex/a", 0.9, path="p-strong")]
        (record,) = aggregate_skill_scores(rows, 5)
        self.assertEqual(record["path"], "p-strong")

    def test_rows_without_a_skill_id_are_dropped(self):
        rows = [chunk_row(None, 5.0), chunk_row("", 5.0), chunk_row("apex/a", 0.1)]
        self.assertEqual([r["id"] for r in aggregate_skill_scores(rows, 5)], ["apex/a"])

    def test_limit_truncates(self):
        rows = [chunk_row(f"apex/s{i}", 1.0 - i / 100) for i in range(10)]
        self.assertEqual(len(aggregate_skill_scores(rows, 3)), 3)

    def test_empty_rows_is_empty_list(self):
        self.assertEqual(aggregate_skill_scores([], 5), [])

    # -- the units bug -----------------------------------------------------

    def test_max_score_and_cumulative_score_are_distinct_units(self):
        """One precise chunk vs three weak ones.

        ``one-precise`` wins on ``max_score`` (1.0 vs 0.5) and therefore on
        ``rank_score``; ``three-weak`` wins on cumulative ``score``
        (1.5 vs 1.0). The coverage gate in scripts/search_knowledge.py and
        sfskills_mcp/skills.py reads ``max_score >= min_skill_max_score OR
        score >= min_skill_score`` precisely because these disagree. If a
        refactor makes ``score`` an alias of ``max_score`` (or vice versa)
        that OR silently becomes a tautology.
        """
        rows = [
            chunk_row("apex/one-precise", 1.0),
            chunk_row("apex/three-weak", 0.5),
            chunk_row("apex/three-weak", 0.5),
            chunk_row("apex/three-weak", 0.5),
        ]
        by_id = {r["id"]: r for r in aggregate_skill_scores(rows, 5)}

        self.assertAlmostEqual(by_id["apex/one-precise"]["max_score"], 1.0)
        self.assertAlmostEqual(by_id["apex/one-precise"]["score"], 1.0)
        self.assertAlmostEqual(by_id["apex/three-weak"]["max_score"], 0.5)
        self.assertAlmostEqual(by_id["apex/three-weak"]["score"], 1.5)

        # They disagree about which skill is better — that is the whole point.
        self.assertGreater(
            by_id["apex/one-precise"]["max_score"], by_id["apex/three-weak"]["max_score"]
        )
        self.assertLess(by_id["apex/one-precise"]["score"], by_id["apex/three-weak"]["score"])

    def test_ordering_follows_max_score_not_cumulative_score(self):
        rows = [
            chunk_row("apex/one-precise", 1.0),
            chunk_row("apex/three-weak", 0.5),
            chunk_row("apex/three-weak", 0.5),
            chunk_row("apex/three-weak", 0.5),
        ]
        self.assertEqual(
            [r["id"] for r in aggregate_skill_scores(rows, 5)],
            ["apex/one-precise", "apex/three-weak"],
        )

    def test_cumulative_score_breaks_max_score_ties(self):
        rows = [
            chunk_row("apex/lonely", 0.5),
            chunk_row("apex/broad", 0.5),
            chunk_row("apex/broad", 0.5),
        ]
        self.assertEqual(
            [r["id"] for r in aggregate_skill_scores(rows, 5)], ["apex/broad", "apex/lonely"]
        )

    def test_full_tie_breaks_on_skill_id_for_determinism(self):
        rows = [chunk_row("apex/zeta", 0.5), chunk_row("apex/alpha", 0.5)]
        self.assertEqual(
            [r["id"] for r in aggregate_skill_scores(rows, 5)], ["apex/alpha", "apex/zeta"]
        )

    # -- the bonus ---------------------------------------------------------

    META = {
        "apex/trigger-recursion": ("trigger-recursion", "Static guard for recursive triggers."),
        "apex/soql-basics": ("soql-basics", "Query fundamentals."),
    }

    def test_without_metadata_rank_score_equals_max_score(self):
        """Pre-2026-07-31 behaviour must be recoverable exactly."""
        rows = [chunk_row("apex/trigger-recursion", 0.4), chunk_row("apex/soql-basics", 0.9)]
        for record in aggregate_skill_scores(rows, 5):
            self.assertAlmostEqual(record["rank_score"], record["max_score"])

    def test_query_without_skill_meta_applies_no_bonus(self):
        rows = [chunk_row("apex/trigger-recursion", 0.4)]
        (record,) = aggregate_skill_scores(rows, 5, query="trigger recursion")
        self.assertAlmostEqual(record["rank_score"], 0.4)

    def test_skill_meta_without_query_applies_no_bonus(self):
        rows = [chunk_row("apex/trigger-recursion", 0.4)]
        (record,) = aggregate_skill_scores(rows, 5, skill_meta=self.META)
        self.assertAlmostEqual(record["rank_score"], 0.4)

    def test_all_stopword_query_applies_no_bonus(self):
        rows = [chunk_row("apex/trigger-recursion", 0.4)]
        (record,) = aggregate_skill_scores(
            rows, 5, skill_meta=self.META, query="how do i set up the"
        )
        self.assertAlmostEqual(record["rank_score"], 0.4)

    def test_bonus_can_overturn_the_chunk_level_ordering(self):
        """The centrality signal exists to beat raw chunk evidence.

        ``soql-basics`` has the better chunk (0.9 vs 0.4) but the query is
        ABOUT trigger recursion.
        """
        rows = [chunk_row("apex/trigger-recursion", 0.4), chunk_row("apex/soql-basics", 0.9)]
        ordered = aggregate_skill_scores(
            rows, 5, skill_meta=self.META, query="trigger recursion", name_weight=1.5, description_weight=0.5
        )
        self.assertEqual([r["id"] for r in ordered], ["apex/trigger-recursion", "apex/soql-basics"])
        # name 2/2 -> 1.5 ; description {static,guard,recursive,triggers} ∩
        # {trigger,recursion} = {} -> 0.0
        self.assertAlmostEqual(ordered[0]["rank_score"], 0.4 + 1.5)

    def test_bonus_never_leaks_into_the_gated_fields(self):
        """``score`` and ``max_score`` feed the coverage gate. A title
        coincidence must not manufacture coverage the corpus lacks."""
        rows = [chunk_row("apex/trigger-recursion", 0.4)]
        (record,) = aggregate_skill_scores(
            rows, 5, skill_meta=self.META, query="trigger recursion"
        )
        self.assertAlmostEqual(record["score"], 0.4)
        self.assertAlmostEqual(record["max_score"], 0.4)
        self.assertGreater(record["rank_score"], record["max_score"])

    def test_bonus_is_applied_before_truncation(self):
        """A skill outside the top-``limit`` on chunk evidence alone can still
        be promoted on centrality. With the bonus applied after the slice it
        would be truncated away first."""
        meta = {"apex/trigger-recursion": ("trigger-recursion", "")}
        rows = [chunk_row(f"apex/noise{i}", 0.9 - i / 1000) for i in range(20)]
        rows.append(chunk_row("apex/trigger-recursion", 0.05))
        ordered = aggregate_skill_scores(rows, 3, skill_meta=meta, query="trigger recursion")
        self.assertEqual(ordered[0]["id"], "apex/trigger-recursion")

    def test_weights_are_honoured_from_the_caller(self):
        """Both callers read these out of config/retrieval-config.yaml; a
        hardcoded default here would silently ignore a retuning."""
        rows = [chunk_row("apex/trigger-recursion", 0.4)]
        meta = {"apex/trigger-recursion": ("trigger-recursion", "")}
        (low,) = aggregate_skill_scores(
            rows, 5, skill_meta=meta, query="trigger recursion", name_weight=0.0, description_weight=0.0
        )
        (high,) = aggregate_skill_scores(
            rows, 5, skill_meta=meta, query="trigger recursion", name_weight=10.0, description_weight=0.0
        )
        self.assertAlmostEqual(low["rank_score"], 0.4)
        self.assertAlmostEqual(high["rank_score"], 10.4)


class RerankResultsTest(unittest.TestCase):
    """Pure-lexical path (query_vector=None) plus the two boosts."""

    def test_rank_based_lexical_score_decays_with_position(self):
        rows = [lexical_row("c0", skill_id=None, domain=None) for _ in range(3)]
        ranked = rerank_results(None, rows, {}, None)
        self.assertAlmostEqual(ranked[0]["lexical_score"], 1.0)
        self.assertAlmostEqual(ranked[1]["lexical_score"], 0.5)
        self.assertAlmostEqual(ranked[2]["lexical_score"], 1 / 3)

    def test_input_order_is_preserved_when_no_boost_applies(self):
        rows = [lexical_row(f"c{i}", skill_id=None, domain=None) for i in range(5)]
        ranked = rerank_results(None, rows, {}, None)
        self.assertEqual([r["chunk_id"] for r in ranked], [f"c{i}" for i in range(5)])
        self.assertEqual([r["position"] for r in ranked], list(range(5)))

    def test_skill_attached_chunks_get_a_flat_boost(self):
        rows = [lexical_row("c0", skill_id=None, domain=None), lexical_row("c1", skill_id="apex/a", domain=None)]
        ranked = rerank_results(None, rows, {}, None)
        self.assertAlmostEqual(ranked[0]["score"], 1.0)  # c0: 1.0 + 0
        self.assertAlmostEqual(ranked[1]["score"], 0.6)  # c1: 0.5 + 0.1

    def test_domain_filter_boost_can_reorder(self):
        """A same-domain chunk at position 1 (0.5 + 0.2 + 0.1 = 0.8) beats an
        off-domain chunk at position 0 (1.0 + 0.1 = 1.1)? No — it does not.
        Assert the arithmetic rather than a guess."""
        rows = [
            lexical_row("off", skill_id="lwc/x", domain="lwc"),
            lexical_row("on", skill_id="apex/y", domain="apex"),
        ]
        ranked = rerank_results(None, rows, {}, "apex")
        self.assertAlmostEqual(ranked[0]["score"], 1.1)
        self.assertAlmostEqual(ranked[1]["score"], 0.8)
        self.assertEqual(ranked[0]["chunk_id"], "off")

    def test_domain_boost_flips_a_near_tie(self):
        rows = [lexical_row(f"c{i}", skill_id="lwc/x", domain="lwc") for i in range(3)]
        rows[2] = lexical_row("target", skill_id="apex/y", domain="apex")
        ranked = rerank_results(None, rows, {}, "apex")
        # target: 1/3 + 0.2 + 0.1 = 0.633 vs c1: 0.5 + 0.1 = 0.6
        self.assertEqual([r["chunk_id"] for r in ranked][:2], ["c0", "target"])

    def test_vector_score_is_zero_without_a_query_vector(self):
        rows = [lexical_row("c0", skill_id="apex/a", domain="apex")]
        ranked = rerank_results(None, rows, {"c0": {"vector": [1.0, 0.0]}}, None)
        self.assertEqual(ranked[0]["vector_score"], 0.0)

    def test_skill_embeddings_take_precedence_over_chunk_embeddings(self):
        """Skill-level vectors answer 'which skill applies'; chunk-level is the
        fallback. Orthogonal fixtures make the choice observable."""
        rows = [lexical_row("c0", skill_id="apex/a", domain="apex")]
        ranked = rerank_results(
            [1.0, 0.0],
            rows,
            {"c0": {"vector": [0.0, 1.0]}},          # cosine 0.0
            None,
            skill_embeddings={"apex/a": {"vector": [1.0, 0.0]}},  # cosine 1.0
        )
        self.assertAlmostEqual(ranked[0]["vector_score"], 1.0)
        self.assertAlmostEqual(ranked[0]["score"], 1.0 + 0.1 + 0.2)

    def test_falls_back_to_chunk_embeddings_when_the_skill_has_none(self):
        rows = [lexical_row("c0", skill_id="apex/a", domain="apex")]
        ranked = rerank_results(
            [1.0, 0.0], rows, {"c0": {"vector": [1.0, 0.0]}}, None, skill_embeddings={}
        )
        self.assertAlmostEqual(ranked[0]["vector_score"], 1.0)

    def test_vector_contribution_is_capped_at_the_0_2_weight(self):
        rows = [lexical_row("c0", skill_id=None, domain=None)]
        with_vec = rerank_results(
            [1.0, 0.0], rows, {"c0": {"vector": [1.0, 0.0]}}, None
        )[0]["score"]
        without_vec = rerank_results(None, rows, {}, None)[0]["score"]
        self.assertAlmostEqual(with_vec - without_vec, 0.2)

    def test_empty_input(self):
        self.assertEqual(rerank_results(None, [], {}, None), [])

    def test_original_row_fields_survive(self):
        rows = [lexical_row("c0", skill_id="apex/a", domain="apex", title="T", text="body")]
        ranked = rerank_results(None, rows, {}, None)
        self.assertEqual(ranked[0]["title"], "T")
        self.assertEqual(ranked[0]["text"], "body")


class CollectOfficialSourcesTest(unittest.TestCase):

    def test_dedupes_across_chunks_and_preserves_first_seen_order(self):
        rows = [{"chunk_id": "c0"}, {"chunk_id": "c1"}]
        lookup = {
            "c0": {"official_source_ids": ["src-b", "src-a"]},
            "c1": {"official_source_ids": ["src-a", "src-c"]},
        }
        self.assertEqual(
            [s["id"] for s in collect_official_sources(rows, lookup, 10)],
            ["src-b", "src-a", "src-c"],
        )

    def test_unknown_chunk_ids_are_skipped_not_fatal(self):
        rows = [{"chunk_id": "missing"}, {"chunk_id": "c0"}]
        lookup = {"c0": {"official_source_ids": ["src-a"]}}
        self.assertEqual([s["id"] for s in collect_official_sources(rows, lookup, 10)], ["src-a"])

    def test_limit_truncates(self):
        rows = [{"chunk_id": "c0"}]
        lookup = {"c0": {"official_source_ids": [f"s{i}" for i in range(10)]}}
        self.assertEqual(len(collect_official_sources(rows, lookup, 3)), 3)

    def test_title_and_url_are_placeholders_for_the_caller_to_canonicalize(self):
        rows = [{"chunk_id": "c0"}]
        lookup = {"c0": {"official_source_ids": ["src-a"]}}
        (source,) = collect_official_sources(rows, lookup, 10)
        self.assertEqual(source, {"id": "src-a", "title": "src-a", "url": ""})

    def test_chunks_without_official_sources_contribute_nothing(self):
        rows = [{"chunk_id": "c0"}]
        self.assertEqual(collect_official_sources(rows, {"c0": {}}, 10), [])


class StopwordSetTest(unittest.TestCase):
    """Regression guard on the frozen stopword list itself. Adding or removing
    a word retunes name_match_weight / description_match_weight without anyone
    re-running the held-out measurement."""

    def test_stopword_set_is_unchanged(self):
        self.assertEqual(
            ranking._STOPWORDS,
            {
                "a", "an", "the", "how", "do", "i", "my", "is", "in", "to", "for", "of", "on",
                "and", "or", "with", "what", "why", "set", "up", "get", "can", "does",
                "salesforce",
            },
            "the stopword set is frozen by the 2026-07-31 held-out Hit@1 measurement; "
            "changing it invalidates the tuned weights in config/retrieval-config.yaml",
        )


if __name__ == "__main__":
    unittest.main()
