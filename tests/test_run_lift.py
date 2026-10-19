"""run_lift: the with-skill vs without-skill knowledge-lift harness.

Exercises prompt construction (--dry-run), the summary math, and the
fail-closed grading path against a fake `claude` binary. No network.
"""
from __future__ import annotations

import json
import stat
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "evals" / "scripts"))
import run_lift  # noqa: E402

EVAL = """# Eval: apex/demo-skill

- **Skill under test:** `skills/apex/demo-skill/SKILL.md`
- **Priority:** P0
- **Cases:** 1
- **Last verified:** 2026-10-19
- **Related templates:** none
- **Related decision trees:** none

## Case 1 - Demo case

**Priority:** P0

**User prompt:**

> "How do I bulkify the widget trigger?
> We have 200 rows per batch."

**Context provided:** None.

**Expected output MUST include:**

- A handler class.

**Expected output MUST NOT include:**

- SOQL in a loop.

**Rubric (0-5):**

- **Correctness:** Is it right?
- **Completeness:** Is it whole?

**Reference answer (gold):**

SECRET-REFERENCE-TEXT use a handler.
"""

SKILL_MARK = "UNIQUE-SKILL-BODY-MARKER"
ANTI_MARK = "UNIQUE-ANTIPATTERN-MARKER"

FAKE_CLAUDE = r'''#!/usr/bin/env python3
import json, os, sys
prompt = sys.stdin.read()
is_grader = "eval grader" in prompt
if is_grader:
    mode = os.environ.get("FAKE_GRADER", "good")
    if mode == "bad":
        text = "I cannot grade this, sorry."
    elif mode == "exit":
        sys.stderr.write("boom")
        sys.exit(7)
    else:
        score = 5 if "UNIQUE-SKILL-BODY-MARKER" not in prompt and "WITH-SKILL" in prompt else 3
        text = '```json\n' + json.dumps({"rubric": {"Correctness": score, "Completeness": score},
                "must_violations": [], "notes": "ok"}) + '\n```'
elif os.environ.get("FAKE_ANSWER") == "toolcall":
    text = 'let me look <invoke name="Glob"></invoke>'
else:
    text = "WITH-SKILL answer" if "UNIQUE-SKILL-BODY-MARKER" in prompt else "plain answer"
print(json.dumps({"result": text, "is_error": False, "total_cost_usd": 0.01, "duration_ms": 1000,
                  "usage": {"input_tokens": 10, "output_tokens": 20,
                            "cache_creation_input_tokens": 5, "cache_read_input_tokens": 1}}))
'''


@pytest.fixture
def world(tmp_path):
    root = tmp_path / "repo"
    skill = root / "skills" / "apex" / "demo-skill"
    (skill / "references").mkdir(parents=True)
    (skill / "SKILL.md").write_text(f"---\nname: demo-skill\n---\n{SKILL_MARK}\n")
    (skill / "references" / "llm-anti-patterns.md").write_text(f"# AP\n{ANTI_MARK}\n")
    ev = tmp_path / "apex__demo-skill.md"
    ev.write_text(EVAL)
    fake = tmp_path / "fake_claude"
    fake.write_text(FAKE_CLAUDE)
    fake.chmod(fake.stat().st_mode | stat.S_IEXEC)
    return {"root": root, "eval": ev, "fake": fake, "out": tmp_path / "out"}


def _argv(w, *extra):
    return ["--file", str(w["eval"]), "--out", str(w["out"]), "--repo-root", str(w["root"]),
            "--claude-bin", str(w["fake"]), *extra]


def test_dry_run_writes_two_prompts_and_arm_b_has_skill(world, capsys):
    assert run_lift.main(_argv(world, "--dry-run")) == 0
    a = (world["out"] / "prompts" / "apex__demo-skill__case1.A.txt").read_text()
    b = (world["out"] / "prompts" / "apex__demo-skill__case1.B.txt").read_text()
    assert SKILL_MARK not in a and ANTI_MARK not in a
    assert SKILL_MARK in b and ANTI_MARK in b
    assert "Use the following skill package when answering" in b
    # question text only: no rubric / reference leak in either arm
    for p in (a, b):
        assert "bulkify the widget trigger" in p
        assert "SECRET-REFERENCE-TEXT" not in p
        assert "Rubric" not in p
    assert b.rstrip().endswith("We have 200 rows per batch.")
    # dry run must not have created answers or results
    assert not (world["out"] / "results.json").exists()


def test_grader_prompt_is_arm_blind(world):
    run_lift.main(_argv(world, "--dry-run"))
    g = (world["out"] / "prompts" / "apex__demo-skill__case1.grader.txt").read_text()
    assert "SECRET-REFERENCE-TEXT" in g and "Correctness" in g
    assert "Arm" not in g and "without skill" not in g.lower()


def test_full_run_with_fake_claude_and_cache(world, capsys):
    assert run_lift.main(_argv(world)) == 0
    res = json.loads((world["out"] / "results.json").read_text())
    arms = res["cases"][0]["arms"]
    assert arms["A"]["answer"] == "plain answer"
    assert arms["B"]["answer"] == "WITH-SKILL answer"
    assert arms["A"]["grade"]["rubric"]["Correctness"] == 3
    assert arms["B"]["grade"]["rubric"]["Correctness"] == 5
    out = capsys.readouterr().out
    assert "overall" in out.lower() and "B > A: 1" in out
    # rerun resumes from cache: break the claude binary and it must still succeed
    world["fake"].write_text("#!/bin/sh\nexit 9\n")
    assert run_lift.main(_argv(world)) == 0


def test_non_json_grade_is_an_error_not_a_skip(world, capsys, monkeypatch):
    monkeypatch.setenv("FAKE_GRADER", "bad")
    assert run_lift.main(_argv(world)) == 2
    res = json.loads((world["out"] / "results.json").read_text())
    arm = res["cases"][0]["arms"]["A"]
    assert arm["grade"] is None and "non-JSON" in arm["grade_error"]
    out = capsys.readouterr().out
    assert "errors: 2" in out.lower()


def test_tool_call_markup_answer_is_an_error(world, monkeypatch, capsys):
    monkeypatch.setenv("FAKE_ANSWER", "toolcall")
    assert run_lift.main(_argv(world)) == 2
    res = json.loads((world["out"] / "results.json").read_text())
    assert "tool-call markup" in res["cases"][0]["arms"]["A"]["answer_error"]
    assert not (world["out"] / "answers" / "apex__demo-skill__case1.A.txt").exists()


def test_nonzero_exit_is_recorded(world, monkeypatch):
    monkeypatch.setenv("FAKE_GRADER", "exit")
    assert run_lift.main(_argv(world)) == 2
    res = json.loads((world["out"] / "results.json").read_text())
    assert "exit" in res["cases"][0]["arms"]["B"]["grade_error"].lower()


def _case(skill, case, a, b, a_must=0, b_must=0, a_err=False):
    def arm(score, must, err=False):
        if err:
            return {"answer": "x", "grade": None, "grade_error": "boom", "cost_usd": 0.1,
                    "duration_s": 1.0, "tokens": {"input": 1, "output": 1}}
        return {"answer": "x", "grade": {"rubric": {"i": score, "j": score}, "must_violations": ["m"] * must},
                "grade_error": None, "cost_usd": 0.1, "duration_s": 1.0, "tokens": {"input": 1, "output": 1}}
    return {"id": f"{skill}-{case}", "skill": skill, "arms": {"A": arm(a, a_must, a_err), "B": arm(b, b_must)}}


def test_summary_math():
    cases = [
        _case("s1", 1, 2, 4, a_must=1),
        _case("s1", 2, 3, 3),
        _case("s2", 1, 5, 4, b_must=2),
        _case("s2", 2, 1, 5, a_err=True),  # error: excluded from deltas, counted as error
    ]
    s = run_lift.summarize(cases)
    assert s["skills"]["s1"]["mean_a"] == pytest.approx(2.5)
    assert s["skills"]["s1"]["mean_b"] == pytest.approx(3.5)
    assert s["skills"]["s1"]["delta"] == pytest.approx(1.0)
    assert s["skills"]["s1"]["must_a"] == 1 and s["skills"]["s1"]["must_b"] == 0
    assert s["skills"]["s2"]["delta"] == pytest.approx(-1.0)
    assert s["skills"]["s2"]["must_b"] == 2
    assert s["overall"]["paired"] == 3
    assert s["overall"]["mean_delta"] == pytest.approx((2 + 0 - 1) / 3)
    assert (s["overall"]["b_gt_a"], s["overall"]["b_lt_a"], s["overall"]["tie"]) == (1, 1, 1)
    assert s["overall"]["errors"] == 1
    assert s["cost_usd"] == pytest.approx(0.8)
    text = run_lift.format_summary(s)
    assert "B > A: 1" in text and "B < A: 1" in text and "tie: 1" in text
