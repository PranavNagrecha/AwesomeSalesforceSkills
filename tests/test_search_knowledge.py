"""Unit tests for ``scripts/search_knowledge.load_official_source_chunks``.

This loader replaced a ``load_chunks`` that read all 130,151 records of the
126 MB ``vector_index/chunks.jsonl`` into a dict so that
``pipelines.ranking.collect_official_sources`` could read one field off ~30 of
them. It now keeps only the records with a non-empty ``official_source_ids``.

The equivalence that makes that safe is not obvious, so it is pinned here
rather than left to a comment: ``collect_official_sources`` skips a chunk it
cannot find AND iterates an empty list for a chunk it does find, so dropping
the empty records is a no-op on both the output and the insertion order of its
``seen`` dict. :meth:`EquivalenceTest` asserts that directly against the full
mapping the old loader would have produced.

The second thing pinned here is the ``_EMPTY_OFFICIAL_SOURCE_IDS`` fast path.
It is a substring skip over raw lines, which is a serialisation assumption, and
it is fail-safe in exactly one direction: it may only cause a line to be parsed
that could have been skipped, never a line to be skipped that was needed. The
two ``FastPath`` tests cover both directions — a changed separator must
degrade to "slower but correct", and the marker must not fire on a record whose
chunk TEXT happens to contain the marker's characters.
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pipelines.ranking import collect_official_sources  # noqa: E402
from scripts.search_knowledge import load_official_source_chunks  # noqa: E402


def write_jsonl(records, *, sort_keys=True, separators=None):
    """Write records the way ``sync_engine.build_chunks_jsonl`` does."""
    handle = tempfile.NamedTemporaryFile(
        "w", suffix=".jsonl", delete=False, encoding="utf-8"
    )
    with handle:
        for record in records:
            handle.write(json.dumps(record, sort_keys=sort_keys, separators=separators))
            handle.write("\n")
    return Path(handle.name)


def chunk(chunk_id, source_ids, text="body text"):
    return {
        "id": chunk_id,
        "official_source_ids": source_ids,
        "path": f"skills/x/{chunk_id}/SKILL.md",
        "text": text,
    }


class LoadOfficialSourceChunksTest(unittest.TestCase):
    def test_keeps_only_records_with_non_empty_official_source_ids(self):
        path = write_jsonl(
            [
                chunk("c0", []),
                chunk("c1", ["src-a"]),
                chunk("c2", []),
                chunk("c3", ["src-b", "src-c"]),
            ]
        )
        loaded = load_official_source_chunks(path)
        self.assertEqual(sorted(loaded), ["c1", "c3"])
        self.assertEqual(loaded["c3"]["official_source_ids"], ["src-b", "src-c"])

    def test_record_missing_the_key_entirely_is_dropped(self):
        # `collect_official_sources` reads `chunk.get("official_source_ids", [])`,
        # so an absent key contributes nothing. Dropping it is equivalent.
        path = write_jsonl([{"id": "c0", "path": "p", "text": "t"}, chunk("c1", ["s"])])
        self.assertEqual(sorted(load_official_source_chunks(path)), ["c1"])

    def test_missing_file_returns_empty_mapping(self):
        # A PyPI MCP install ships no chunks.jsonl. The old loader returned {}
        # rather than raising, and callers depend on that.
        self.assertEqual(
            load_official_source_chunks(Path("/nonexistent/chunks.jsonl")), {}
        )

    def test_blank_lines_are_skipped(self):
        path = write_jsonl([chunk("c1", ["s"])])
        path.write_text(path.read_text(encoding="utf-8") + "\n\n", encoding="utf-8")
        self.assertEqual(sorted(load_official_source_chunks(path)), ["c1"])


class FastPathTest(unittest.TestCase):
    """The ``_EMPTY_OFFICIAL_SOURCE_IDS`` substring skip must be fail-safe."""

    def test_marker_does_not_fire_on_chunk_text_containing_it(self):
        # JSON escapes the quotes of a string value, so an occurrence inside
        # `text` reads `\"official_source_ids\": []` and must not match.
        path = write_jsonl(
            [chunk("c1", ["src-a"], text='look: "official_source_ids": [] here')]
        )
        loaded = load_official_source_chunks(path)
        self.assertEqual(sorted(loaded), ["c1"], "fast path skipped a needed record")

    def test_changed_separators_degrade_to_correct_not_wrong(self):
        # If build_chunks_jsonl ever stops using default separators the marker
        # stops matching, every line falls through to json.loads, and the
        # result must be unchanged.
        records = [chunk("c0", []), chunk("c1", ["src-a"])]
        compact = write_jsonl(records, separators=(",", ":"))
        self.assertEqual(sorted(load_official_source_chunks(compact)), ["c1"])


class EquivalenceTest(unittest.TestCase):
    """The filtered mapping and the full mapping are indistinguishable to the
    one function that consumes either."""

    def test_collect_official_sources_agrees_with_the_full_mapping(self):
        records = [
            chunk("c0", []),
            chunk("c1", ["src-b"]),
            chunk("c2", []),
            chunk("c3", ["src-a", "src-b"]),
            chunk("c4", []),
        ]
        path = write_jsonl(records)
        full = {record["id"]: record for record in records}
        filtered = load_official_source_chunks(path)

        # Rows deliberately interleave empty and non-empty chunks so that a
        # difference in `seen` INSERTION ORDER, not just membership, would show.
        rows = [{"chunk_id": f"c{i}"} for i in (0, 3, 2, 1, 4)]
        self.assertEqual(
            collect_official_sources(rows, filtered, 10),
            collect_official_sources(rows, full, 10),
        )
        self.assertEqual(
            [s["id"] for s in collect_official_sources(rows, filtered, 10)],
            ["src-a", "src-b"],
        )

    def test_agreement_holds_under_the_limit_truncation(self):
        records = [chunk(f"c{i}", [f"src-{i}"]) for i in range(5)] + [
            chunk("empty", [])
        ]
        path = write_jsonl(records)
        full = {record["id"]: record for record in records}
        filtered = load_official_source_chunks(path)
        rows = [{"chunk_id": "empty"}] + [{"chunk_id": f"c{i}"} for i in range(5)]
        for limit in (1, 2, 3, 5, 10):
            with self.subTest(limit=limit):
                self.assertEqual(
                    collect_official_sources(rows, filtered, limit),
                    collect_official_sources(rows, full, limit),
                )


if __name__ == "__main__":
    unittest.main()
