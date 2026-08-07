"""Unit tests for ``pipelines/lexical_index.py``.

Lexical retrieval is the mandatory, no-API-key path — every `search_knowledge`
call and every MCP `search_skill` call goes through ``tokenize_query`` and
``search_index``. A raw user query reaches FTS5 through one sanitisation pass,
so query sanitisation is a correctness AND an availability concern.

Call sites, and how much sanitisation each one has (checked 2026-08-01):

- ``scripts/search_knowledge.py:225`` — GUARDED TWICE. ``run_search`` runs the
  query through its own ``_sanitize_query_for_fts5`` (defined :204, applied
  :224, allow-list ``[^A-Za-z0-9\\-]+`` at :201) before calling
  ``search_index``, and then ``tokenize_query`` sanitises again.
- ``mcp/sfskills-mcp/src/sfskills_mcp/skills.py:188`` — GUARDED ONCE. It
  passes the caller's ``query`` string to ``search_index`` untouched; the file
  has no sanitiser of its own. ``tokenize_query`` is the only thing standing
  between an MCP client and the FTS5 parser.

That asymmetry is why the pre-2026-08-01 deny-list bug was reachable in
practice: it was an MCP-only crash, NOT a crash "in both the CLI and the MCP
server" as an earlier revision of this file claimed. The CLI's extra pass had
been absorbing it. The fix now lives in ``tokenize_query``, which both paths
share, so the single-guard MCP path is covered too.

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
    """User input reaches FTS5 MATCH through one sanitisation pass.

    `search_index` has no try/except, so any character `tokenize_query` leaves
    behind that FTS5 treats as syntax raises `sqlite3.OperationalError` out of
    the retrieval call. This class covers ordinary metacharacters; the
    regression cases for the 2026-08-01 allow-list fix are in
    `FTS5MetacharacterRegressionTest` below.
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


class FTS5MetacharacterRegressionTest(IndexFixtureMixin, unittest.TestCase):
    """Regression suite for the 2026-08-01 allow-list fix in
    ``pipelines/lexical_index.py``.

    ``tokenize_query`` used to sanitise with a DENY-list that stripped
    ``'".,$@#!?()[]{}|\\^~*:-`` and nothing else. It leaked in two directions,
    both of which are asserted-against below:

    CRASH — ``% & ; < = > \\`` and a leading ``+`` reached MATCH and raised
    ``sqlite3.OperationalError: fts5: syntax error near "%"`` straight out of
    ``search_index``, on inputs users type constantly (``100% test coverage``,
    ``A&B testing``, ``field<>value``, ``salesforce + slack``).

    SILENT — the worse arm, because nothing is raised. An INFIX ``+`` survived,
    so ``trigger+recursion`` became the expression ``trigger+recursion*``. Per
    the FTS5 grammar ``+`` concatenates two phrases, so the documented OR
    became an ADJACENCY requirement and the caller got zero rows back with no
    error to notice.

    Grounded in the FTS5 spec (https://sqlite.org/fts5.html, § "Full-text Query
    Syntax"): a bareword may contain only ASCII letters, ASCII digits, the
    underscore, codepoint 26, and non-ASCII codepoints above 127 — "Strings
    that include any other characters must be quoted" — and "Two phrases can be
    concatenated into a single large phrase using the '+' operator".

    The fix replaced the deny-list with an allow-list, so these tests are
    deliberately written against the CLASS of defect (sweep every ASCII
    punctuation character) rather than the eight characters that happened to be
    reported. A deny-list regression would fail `test_no_ascii_punctuation_
    character_can_reach_fts5_as_syntax` even for a character nobody has
    reported yet.
    """

    # Each of these raised `sqlite3.OperationalError` before the fix.
    PREVIOUSLY_CRASHING = [
        "100% test coverage", "salesforce + slack", "a=b", "field<>value",
        "A&B testing", "trigger; recursion", "c++", "100% CPU",
        "field = value", "<apex:page>", "a;b", "50%+", "cost ~= $5",
        "SELECT Id FROM Account WHERE Name = 'x'",
    ]

    def test_previously_crashing_queries_no_longer_raise(self):
        for query in self.PREVIOUSLY_CRASHING:
            with self.subTest(query=query):
                search_index(self.index_path, query, None, 10)

    def test_no_ascii_punctuation_character_can_reach_fts5_as_syntax(self):
        """The allow-list's real contract: no ASCII punctuation character, in
        any position, is passed through to MATCH. Catches a future leak the
        moment it is introduced, not the next time a user reports a crash."""
        for code in range(1, 127):
            ch = chr(code)
            if ch.isalnum():
                continue
            for query in (f"trigger{ch}recursion", f"{ch}trigger", f"trigger{ch}", ch):
                with self.subTest(char=repr(ch), query=repr(query)):
                    search_index(self.index_path, query, None, 10)

    # -- the silent arm: `+` must mean OR, not adjacency --------------------

    def test_infix_plus_produces_or_not_phrase_concatenation(self):
        """String-level assertion. Before the fix this returned the single
        token `trigger+recursion*` — one FTS5 phrase, not two OR'd terms."""
        self.assertEqual(tokenize_query("trigger+recursion"), "trigger* OR recursion*")
        self.assertEqual(tokenize_query("recursion+wire"), "recursion* OR wire*")

    def test_infix_plus_matches_documents_that_share_no_term(self):
        """Behavioural proof that the semantics are OR and not adjacency.

        `recursion` appears only in c-apex and `wire` only in c-lwc, in
        different documents. Under OR both rows match; under `+` phrase
        concatenation the terms would have to be ADJACENT in one document, so
        neither matches and the caller silently gets an empty result."""
        joined = {r["chunk_id"] for r in search_index(self.index_path, "recursion+wire", None, 10)}
        spaced = {r["chunk_id"] for r in search_index(self.index_path, "recursion wire", None, 10)}
        self.assertEqual(joined, {"c-apex", "c-lwc"})
        self.assertEqual(joined, spaced, "`a+b` must be identical to `a b`")

    def test_plus_separated_query_is_not_silently_empty(self):
        """The narrowest statement of the bug that was shipping: a non-empty
        query over terms that ARE in the corpus returned zero rows."""
        self.assertNotEqual(search_index(self.index_path, "recursion+wire", None, 10), [])

    # -- the allow-list must not over-strip --------------------------------

    def test_underscore_is_kept_because_it_is_a_legal_bareword_character(self):
        """Underscore is valid inside an FTS5 bareword and appears in real API
        names, so stripping it would split `Account_c` into two weaker terms."""
        self.assertEqual(tokenize_query("my_custom_field"), "my_custom_field*")

    def test_non_ascii_is_kept(self):
        """Codepoints above 127 are legal barewords; dropping them would make
        an accented or CJK query unsearchable rather than merely odd."""
        self.assertEqual(tokenize_query("café"), "café*")
        self.assertEqual(tokenize_query("承認"), "承認*")

    def test_hyphen_and_slash_still_split_into_separate_terms(self):
        """Neither is a legal bareword character, and splitting is load-bearing
        — skill ids get pasted in as queries."""
        self.assertEqual(
            tokenize_query("apex/trigger-recursion"), "apex* OR trigger* OR recursion*"
        )


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
