"""run_evals.grade() must fail closed: a grader that errors is a failed case."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "evals" / "scripts"))
import run_evals  # noqa: E402

CASE = """# Eval: demo

- **Skill under test:** apex/demo
- **Priority:** P0
- **Cases:** 1
- **Last verified:** 2026-10-19
- **Related templates:** none
- **Related decision trees:** none

## Case 1 - demo

**Priority:** P0

**User prompt:** x

**Expected output MUST include:** x

**Expected output MUST NOT include:** y

**Rubric (score 1-5):** a

**Reference answer:** z
"""

GOOD = """printf '{"rubric": {"a": 5}, "notes": "ok"}'"""
LOW = """printf '{"rubric": {"a": 2}, "notes": "weak"}'"""


@pytest.fixture
def files(tmp_path):
    p = tmp_path / "demo.md"
    p.write_text(CASE, encoding="utf-8")
    f = run_evals.parse_eval_file(p)
    assert not f.errors and len(f.cases) == 1
    return [f]


@pytest.mark.parametrize("cmd", ["false", "echo notjson", "printf '{}'", """printf '{"rubric": {}}'"""])
def test_grader_error_fails_the_run(files, cmd, capsys):
    assert run_evals.grade(files, cmd, None) != 0
    out = capsys.readouterr().out
    assert "[PASS]" not in out
    assert "1 grader error" in out


def test_low_score_fails_p0(files):
    assert run_evals.grade(files, LOW, None) == 2


def test_valid_grader_passes(files, tmp_path, capsys):
    out_path = tmp_path / "report.json"
    assert run_evals.grade(files, GOOD, out_path) == 0
    assert "[PASS]" in capsys.readouterr().out
    assert out_path.exists()
