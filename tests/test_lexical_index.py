"""Unit tests for ``pipelines/lexical_index.py``.

Lexical retrieval is the mandatory, no-API-key path — every `search_knowledge`
call and every MCP `search_skill` call goes through ``tokenize_query`` and
``search_index``. A raw user query reaches FTS5 through one thin translate
table, so query sanitisation is a correctness AND an availability concern.

Every test builds a three-chunk index in a temp dir. Nothing here touches
``vector_index/lexical.sqlite`` (which is gitignored, ~50 MB, and rebuilt from
chunks in CI).
"""

from __future__ import annotations

import shutil
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pipelines.lexical_index import (  # noqa: E402
    build_lexical_index,
    read_source_hash,
    search_index,
    tokenize_query,
)


CHUNKS = [
    {
        "id": "c-apex",
        "source_id": "src-apex",
        "skill_id": "apex/trigger-recursion",
        "domain": "apex",
        "chunk_kind": "skill",
        "source_trust": "local",
        "path": "skills/apex/trigger-recursion/SKILL.md",
        "title": "Trigger recursion guard",
        "tags": ["apex", "trigger"],
        "text": "Use a static Boolean guard so the trigger does not re-enter itself.",
    },
    {
        "id": "c-lwc",
        "source_id": "src-lwc",
        "skill_id": "lwc/wire-adapters",
        "domain": "lwc",
        "chunk_kind": "skill",
        "source_trust": "local",
        "path": "skills/lwc/wire-adapters/SKILL.md",
        "title": "Wire adapters",
        "tags": ["lwc", "wire"],
        "text": "A wire adapter provisions data reactively to a Lightning web component.",
    },
    {
        "id": "c-official",
        "source_id": "src-doc",
        "skill_id": None,
        "domain": None,
        "chunk_kind": "official",
        "source_trust": "official",
        "path": "knowledge/official/governor-limits.md",
        "title": "Apex governor limits",
        "tags": [],
        "text": "A trigger may process 200 records per batch under the governor limits.",
    },
]


class IndexFixtureMixin:
    """Builds one temp index per test class. Cheap: three rows, ~30 ms."""

    @classmethod
    def setUpClass(cls):
        cls._dir = Path(tempfile.mkdtemp(prefix="sfskills-lex-"))
        cls.index_path = cls._dir / "lexical.sqlite"
        build_lexical_index(cls.index_path, CHUNKS, "hash-v1")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls._dir, ignore_errors=True)


class TokenizeQueryTest(unittest.TestCase):
    """``tokenize_query`` output is an FTS5 MATCH expression, not a string
    literal — anything it emits is parsed as query syntax."""

    def test_words_become_lowercased_prefix_terms_joined_by_or(self):
        self.assertEqual(tokenize_query("Trigger Recursion"), "trigger* OR recursion*")

    def test_single_word(self):
        self.assertEqual(tokenize_query("bulkify"), "bulkify*")

    def test_empty_and_whitespace_only_return_empty_string(self):
        self.assertEqual(tokenize_query(""), "")
        self.assertEqual(tokenize_query("   \t\n "), "")

    def test_slashes_split_rather_than_concatenate(self):
        # skill ids are routinely pasted in as queries
        self.assertEqual(tokenize_query("apex/trigger-recursion"), "apex* OR trigger* OR recursion*")

    def test_punctuation_in_the_translate_table_becomes_whitespace(self):
        self.assertEqual(
            tokenize_query("what's a @future, really?"),
            "what* OR s* OR a* OR future* OR really*",
        )

    def test_quotes_are_stripped_so_phrase_syntax_cannot_be_injected(self):
        self.assertEqual(tokenize_query('"exact phrase"'), "exact* OR phrase*")

    def test_a_query_of_only_stripped_punctuation_returns_empty(self):
        self.assertEqual(tokenize_query("?!.,()"), "")

    def test_no_bare_star_is_emitted_for_a_star_only_query(self):
        # `*` alone would be an FTS5 syntax error if it reached MATCH.
        self.assertEqual(tokenize_query("***"), "")


class SearchIndexTest(IndexFixtureMixin, unittest.TestCase):

    def test_missing_index_file_returns_empty_not_raises(self):
        self.assertEqual(search_index(self._dir / "nope.sqlite", "trigger", None, 10), [])

    def test_empty_query_returns_empty_without_touching_sqlite(self):
        self.assertEqual(search_index(self.index_path, "   ", None, 10), [])

    def test_matches_across_title_tags_and_text(self):
        by_title = {r["chunk_id"] for r in search_index(self.index_path, "recursion", None, 10)}
        self.assertEqual(by_title, {"c-apex"})
        by_tag = {r["chunk_id"] for r in search_index(self.index_path, "wire", None, 10)}
        self.assertEqual(by_tag, {"c-lwc"})
        by_text = {r["chunk_id"] for r in search_index(self.index_path, "reactively", None, 10)}
        self.assertEqual(by_text, {"c-lwc"})

    def test_prefix_matching_is_on(self):
        self.assertEqual(
            {r["chunk_id"] for r in search_index(self.index_path, "recurs", None, 10)}, {"c-apex"}
        )

    def test_or_semantics_union_the_terms(self):
        hits = {r["chunk_id"] for r in search_index(self.index_path, "recursion wire", None, 10)}
        self.assertEqual(hits, {"c-apex", "c-lwc"})

    def test_domain_filter_restricts_results(self):
        hits = {r["chunk_id"] for r in search_index(self.index_path, "trigger", None, 10)}
        self.assertEqual(hits, {"c-apex", "c-official"})
        scoped = {r["chunk_id"] for r in search_index(self.index_path, "trigger", "apex", 10)}
        self.assertEqual(scoped, {"c-apex"})

    def test_domain_filter_excludes_null_domain_chunks(self):
        """The official-doc chunk has domain NULL; `AND domain = ?` drops it.
        Characterization — a domain-scoped search never surfaces unattached
        official-source chunks."""
        self.assertEqual(search_index(self.index_path, "governor", "apex", 10), [])

    def test_limit_is_applied(self):
        self.assertEqual(len(search_index(self.index_path, "trigger", None, 1)), 1)

    def test_rows_are_ordered_best_first_by_bm25(self):
        """``rerank_results`` assumes position 0 is the most relevant row and
        derives ``lexical_score = 1/(1+index)`` from that. bm25() is negative,
        so ORDER BY rank ascending is best-first."""
        rows = search_index(self.index_path, "trigger", None, 10)
        ranks = [r["rank"] for r in rows]
        self.assertEqual(ranks, sorted(ranks))
        self.assertLess(ranks[0], 0.0)

    def test_returned_columns_cover_what_rerank_results_reads(self):
        (row,) = search_index(self.index_path, "recursion", None, 10)
        for key in ("chunk_id", "source_id", "skill_id", "domain", "chunk_kind",
                    "source_trust", "path", "title", "text", "rank"):
            self.assertIn(key, row)
        self.assertEqual(row["skill_id"], "apex/trigger-recursion")
        self.assertEqual(row["domain"], "apex")

    def test_no_match_returns_empty(self):
        self.assertEqual(search_index(self.index_path, "zzzznonexistent", None, 10), [])


class QuerySanitisationTest(IndexFixtureMixin, unittest.TestCase):
    """User input reaches FTS5 MATCH through one translate table.

    `search_index` has no try/except, so any character `tokenize_query` leaves
    behind that FTS5 treats as syntax raises `sqlite3.OperationalError` out of
    the retrieval call. The characters CURRENTLY stripped are handled here; the
    ones that are not are in `UnsanitisedQueryCrashTest` below.
    """

    SAFE = [
        "trigger (recursion)",
        "what's the @future limit?",
        "apex: bulkification",
        "trigger-recursion",
        "100.0 * records",
        'he said "trigger"',
        "a^b",
        "cost ~ $5",
        "[bracket] {brace}",
        "path\\to\\thing",
        "a|b",
        "NEAR/2 trigger",
        "trigger AND recursion",
        "trigger OR recursion",
        "NOT trigger",
        "column:value",
        "***",
        "?!.,",
        "",
        "   ",
        "trigger\nrecursion",
        "emoji 🎉 trigger",
    ]

    def test_known_safe_metacharacters_do_not_raise(self):
        for query in self.SAFE:
            with self.subTest(query=query):
                search_index(self.index_path, query, None, 10)

    def test_fts5_boolean_keywords_are_neutralised_by_lowercasing(self):
        """`AND` / `OR` / `NOT` / `NEAR` are only FTS5 operators in upper case.
        Lowercasing turns them into ordinary prefix terms, so a user typing
        `trigger AND recursion` gets OR semantics, not an operator."""
        self.assertEqual(tokenize_query("trigger AND recursion"), "trigger* OR and* OR recursion*")
        hits = {r["chunk_id"] for r in search_index(self.index_path, "trigger NOT wire", None, 10)}
        self.assertIn("c-lwc", hits)  # `NOT` did not exclude anything


class UnsanitisedQueryCrashTest(IndexFixtureMixin, unittest.TestCase):
    """OPEN BUG — `pipelines/lexical_index.py:9` `_FTS5_SPECIAL`.

    The translate table strips ``'".,$@#!?()[]{}|\\^~*:-`` but NOT
    ``% + & = < > ;``. Those are FTS5 query syntax, so a query containing one
    raises ``sqlite3.OperationalError: fts5: syntax error near "%"`` straight
    out of ``search_index`` — an uncaught 500-equivalent in both the CLI and
    the MCP server, on inputs a Salesforce user types constantly
    (``100% CPU``, ``c++``, ``A&B``, ``field = value``, ``<apex:page>``).

    ``+`` is worse than a crash in one shape: ``trigger+recursion`` survives as
    ``trigger+recursion*``, which FTS5 parses as a PHRASE concatenation, so the
    documented OR semantics silently become an adjacency requirement.

    Grounded in the FTS5 spec (https://sqlite.org/fts5.html, § "Full-text Query
    Syntax"): a bareword may contain only ASCII letters, ASCII digits, the
    underscore, codepoint 26, and non-ASCII codepoints above 127 — "Strings
    that include any other characters must be quoted" — and "Two phrases can be
    concatenated into a single large phrase using the '+' operator".

    These tests are marked ``expectedFailure`` so the suite is green against
    HEAD and turns RED (unexpected success) the moment the bug is fixed —
    at which point delete the decorators. They are NOT an assertion that
    crashing is correct.

    Fix belongs in ``pipelines/lexical_index.py`` (not owned by this item):
    add ``%+&=<>;`` to ``_FTS5_SPECIAL``.
    """

    CRASHERS = [
        "100% CPU", "c++", "A&B testing", "field = value", "<apex:page>", "a;b",
        "50%+", "cost ~= $5",
    ]

    def test_each_unsanitised_character_currently_raises(self):
        """Documents the live blast radius. Delete alongside the fix."""
        for query in self.CRASHERS:
            with self.subTest(query=query):
                with self.assertRaises(sqlite3.OperationalError):
                    search_index(self.index_path, query, None, 10)

    @unittest.expectedFailure
    def test_percent_should_not_raise(self):
        search_index(self.index_path, "100% CPU time", None, 10)

    @unittest.expectedFailure
    def test_plus_should_not_raise(self):
        search_index(self.index_path, "c++ style trigger", None, 10)

    @unittest.expectedFailure
    def test_ampersand_should_not_raise(self):
        search_index(self.index_path, "A&B record types", None, 10)

    @unittest.expectedFailure
    def test_equals_and_angle_brackets_should_not_raise(self):
        search_index(self.index_path, "<apex:page> field = value", None, 10)

    @unittest.expectedFailure
    def test_semicolon_should_not_raise(self):
        search_index(self.index_path, "trigger; recursion", None, 10)

    @unittest.expectedFailure
    def test_plus_should_not_become_a_phrase_operator(self):
        """`trigger+recursion` must mean the same as `trigger recursion`."""
        self.assertEqual(tokenize_query("trigger+recursion"), "trigger* OR recursion*")


class BuildLexicalIndexTest(unittest.TestCase):

    def setUp(self):
        self._dir = Path(tempfile.mkdtemp(prefix="sfskills-lexbuild-"))
        self.addCleanup(shutil.rmtree, self._dir, ignore_errors=True)
        self.path = self._dir / "lexical.sqlite"

    def test_builds_and_records_the_source_hash_and_count(self):
        build_lexical_index(self.path, CHUNKS, "hash-v1")
        self.assertTrue(self.path.exists())
        self.assertEqual(read_source_hash(self.path), "hash-v1")
        connection = sqlite3.connect(self.path)
        try:
            value = connection.execute(
                "SELECT value FROM meta WHERE key = 'chunk_count'"
            ).fetchone()[0]
        finally:
            connection.close()
        self.assertEqual(value, str(len(CHUNKS)))

    def test_matching_hash_is_a_no_op_rebuild(self):
        """The hash short-circuit is what keeps `build_index.py` cheap. If it
        stopped firing, every sync would rewrite a ~50 MB file."""
        build_lexical_index(self.path, CHUNKS, "hash-v1")
        mtime = self.path.stat().st_mtime_ns
        build_lexical_index(self.path, [], "hash-v1")  # would empty the index if it ran
        self.assertEqual(self.path.stat().st_mtime_ns, mtime)
        self.assertEqual(
            {r["chunk_id"] for r in search_index(self.path, "recursion", None, 10)}, {"c-apex"}
        )

    def test_changed_hash_rebuilds_from_scratch(self):
        build_lexical_index(self.path, CHUNKS, "hash-v1")
        build_lexical_index(self.path, [CHUNKS[1]], "hash-v2")
        self.assertEqual(read_source_hash(self.path), "hash-v2")
        self.assertEqual(search_index(self.path, "recursion", None, 10), [])
        self.assertEqual(
            {r["chunk_id"] for r in search_index(self.path, "wire", None, 10)}, {"c-lwc"}
        )

    def test_optional_chunk_fields_may_be_absent(self):
        """`skill_id`, `domain` and `tags` are read with `.get` — official-source
        chunks legitimately omit all three."""
        minimal = {
            "id": "c-min",
            "source_id": "s",
            "chunk_kind": "official",
            "source_trust": "official",
            "path": "knowledge/x.md",
            "title": "Sharing rules",
            "text": "Owner-based sharing rules extend record access.",
        }
        build_lexical_index(self.path, [minimal], "hash-min")
        (row,) = search_index(self.path, "sharing", None, 10)
        self.assertIsNone(row["skill_id"])
        self.assertIsNone(row["domain"])

    def test_empty_corpus_produces_a_valid_queryable_index(self):
        build_lexical_index(self.path, [], "hash-empty")
        self.assertEqual(read_source_hash(self.path), "hash-empty")
        self.assertEqual(search_index(self.path, "anything", None, 10), [])


class ReadSourceHashTest(unittest.TestCase):

    def setUp(self):
        self._dir = Path(tempfile.mkdtemp(prefix="sfskills-lexhash-"))
        self.addCleanup(shutil.rmtree, self._dir, ignore_errors=True)

    def test_missing_file_is_none(self):
        self.assertIsNone(read_source_hash(self._dir / "absent.sqlite"))

    def test_non_sqlite_file_is_none_not_an_exception(self):
        """A truncated or half-written index must degrade to 'rebuild me', not
        crash the sync."""
        corrupt = self._dir / "corrupt.sqlite"
        corrupt.write_bytes(b"this is not a database" * 100)
        self.assertIsNone(read_source_hash(corrupt))

    def test_sqlite_file_without_a_meta_table_is_none(self):
        stray = self._dir / "stray.sqlite"
        connection = sqlite3.connect(stray)
        connection.execute("CREATE TABLE unrelated (x INTEGER)")
        connection.commit()
        connection.close()
        self.assertIsNone(read_source_hash(stray))


if __name__ == "__main__":
    unittest.main()
