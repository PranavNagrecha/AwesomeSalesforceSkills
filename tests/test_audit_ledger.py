"""audit_ledger.py: append-only batch ledger with a falling-defects trend verdict."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import audit_ledger  # noqa: E402


def _row(batch: int, defects: int, skills: int = 9, writer: str = "opus") -> dict:
    return {
        "date": "2026-10-20",
        "item": "R3-06",
        "batch": batch,
        "writer_model": writer,
        "reviewer_model": "opus",
        "skills": skills,
        "claims": {"grounded": 100, "contradicted": 4, "not_found": 20},
        "writer_defects": defects,
        "defect_classes": {"cite": defects},
        "learned_rules_added": 1,
        "commit": "abc1234",
    }


def test_add_rejects_class_sum_mismatch(tmp_path, monkeypatch):
    monkeypatch.setattr(audit_ledger, "LEDGER", tmp_path / "ledger.jsonl")
    with pytest.raises(SystemExit, match="sum to 5, not --writer-defects 6"):
        audit_ledger.main(
            ["add", "--item", "R3-06", "--batch", "1", "--writer", "opus", "--reviewer", "opus",
             "--skills", "9", "--grounded", "1", "--contradicted", "0", "--not-found", "0",
             "--writer-defects", "6", "--defect-classes", "cite=5", "--commit", "abc"]
        )
    assert not (tmp_path / "ledger.jsonl").exists()


def test_add_appends_one_json_line_and_report_counts(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(audit_ledger, "LEDGER", tmp_path / "ledger.jsonl")
    for b, d in ((1, 58), (2, 27)):
        audit_ledger.main(
            ["add", "--item", "R3-06", "--batch", str(b), "--writer", "opus", "--reviewer", "opus",
             "--skills", "9", "--grounded", "100", "--contradicted", "4", "--not-found", "20",
             "--writer-defects", str(d), "--defect-classes", f"cite={d}", "--commit", "abc", "--date", "2026-10-20"]
        )
    lines = (tmp_path / "ledger.jsonl").read_text().splitlines()
    assert len(lines) == 2 and json.loads(lines[1])["batch"] == 2
    capsys.readouterr()  # drop the two add() lines
    audit_ledger.main(["report", "--json"])
    out = json.loads(capsys.readouterr().out)
    assert out["skills_audited"] == 18
    assert out["batches"][0]["defects_per_skill"] == 6.44
    assert out["trend"].startswith("falling: 6.44 -> 3.0")


def test_trend_escalates_when_not_falling_over_window(tmp_path, monkeypatch):
    monkeypatch.setattr(audit_ledger, "LEDGER", tmp_path / "ledger.jsonl")
    rows = [_row(b, 30 + b) for b in range(1, 6)]  # rising
    (tmp_path / "ledger.jsonl").write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    s = audit_ledger.summarize(audit_ledger.load(tmp_path / "ledger.jsonl"))
    assert s["trend"].startswith("NOT FALLING")


def test_supersedes_replaces_earlier_batch(tmp_path, monkeypatch):
    rows = [_row(1, 58), dict(_row(1, 50), batch=3, supersedes=1)]
    (tmp_path / "ledger.jsonl").write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    loaded = audit_ledger.load(tmp_path / "ledger.jsonl")
    assert len(loaded) == 1 and loaded[0]["writer_defects"] == 50
