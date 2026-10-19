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
if is_grader and '"verdict"' in prompt:
    mode = os.environ.get("FAKE_GRADER", "good")
    if mode == "bad":
        text = "no verdict from me"
    else:
        # the probe grader prompt quotes the candidate answer; WITH-SKILL answers state the fact
        verdict = "correct" if "WITH-SKILL" in prompt.split("=== CANDIDATE ANSWER ===")[-1] else "wrong"
        text = json.dumps({"verdict": verdict, "quote": "WITH-SKILL answer" if verdict == "correct" else "plain answer"})
elif is_grader:
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


# --------------------------------------------------------------------------- v2: probes

PROBE = {"id": "demo-1", "skill": "apex/demo-skill",
         "question": "A trigger needs a handler. Where do I put the logic?",
         "wrong_answer": "In the trigger body.", "correct_answer": "In a handler class.",
         "source": "apex_dev.txt L10"}


def _write_probes(path, probes):
    path.write_text(json.dumps({"probes": probes}))
    return path


def test_load_probes_roundtrip(tmp_path):
    f = _write_probes(tmp_path / "p.json", [PROBE])
    probes = run_lift.load_probes(f)
    assert [p["id"] for p in probes] == ["demo-1"]


@pytest.mark.parametrize("mutate", [
    lambda p: p.pop("wrong_answer"),
    lambda p: p.update(correct_answer="  "),
    lambda p: p.update(skill="demo-skill"),          # must be <domain>/<slug>
    lambda p: p.update(source="somewhere"),           # must carry an L<n> line cite
])
def test_load_probes_rejects_malformed(tmp_path, mutate):
    bad = dict(PROBE)
    mutate(bad)
    with pytest.raises(run_lift.LiftError):
        run_lift.load_probes(_write_probes(tmp_path / "p.json", [bad]))


def test_load_probes_rejects_duplicate_ids(tmp_path):
    with pytest.raises(run_lift.LiftError, match="duplicate"):
        run_lift.load_probes(_write_probes(tmp_path / "p.json", [PROBE, dict(PROBE)]))


def test_shipped_probe_set_meets_the_spec():
    probes = run_lift.load_probes(run_lift.DEFAULT_PROBES)
    assert len(probes) >= 30
    assert len({p["skill"] for p in probes}) >= 12
    root = Path(__file__).resolve().parents[1]
    for p in probes:
        assert (root / "skills" / p["skill"] / "SKILL.md").is_file(), p["id"]
        assert p["wrong_answer"].strip() != p["correct_answer"].strip()


def test_probe_grader_prompt_is_arm_blind_and_carries_both_answers():
    g = run_lift.build_probe_grader_prompt(PROBE, "My candidate text.")
    assert "In a handler class." in g and "In the trigger body." in g and "My candidate text." in g
    assert "Arm" not in g and "skill package" not in g.lower() and "without skill" not in g.lower()


def test_parse_probe_grade():
    g = run_lift.parse_probe_grade('```json\n{"verdict": "correct", "quote": "Use a handler."}\n```',
                                   "Use a handler. Then test it.")
    assert g["verdict"] == "correct" and g["quote_found"] is True
    g = run_lift.parse_probe_grade('{"verdict": "neither", "quote": ""}', "anything")
    assert g["verdict"] == "neither"
    g = run_lift.parse_probe_grade('{"verdict": "wrong", "quote": "invented sentence"}', "real text")
    assert g["quote_found"] is False          # recorded, not an error
    for bad in ('not json', '{"verdict": "maybe", "quote": "x"}', '{"quote": "x"}',
                '{"verdict": "correct"}', '{"verdict": "correct", "quote": 3}'):
        with pytest.raises(run_lift.LiftError):
            run_lift.parse_probe_grade(bad, "answer")


def _probe_run(pid, skill, va, vb, ea=False):
    def arm(v, err=False):
        base = {"answer": "x", "cost_usd": 0.1, "duration_s": 1.0, "tokens": {"input": 1, "output": 1},
                "answer_error": None}
        if err:
            return {**base, "grade": None, "grade_error": "boom"}
        return {**base, "grade": {"verdict": v, "quote": "q", "quote_found": True}, "grade_error": None}
    return {"id": pid, "skill": skill, "runs": [{"A": arm(va, ea), "B": arm(vb)}]}


def test_summarize_probes_binary_counts():
    recs = [_probe_run("p1", "d/s1", "wrong", "correct"),
            _probe_run("p2", "d/s1", "neither", "correct"),
            _probe_run("p3", "d/s2", "correct", "correct"),
            _probe_run("p4", "d/s2", "wrong", "wrong"),
            _probe_run("p5", "d/s2", "wrong", "correct", ea=True)]   # error: excluded from rates
    s = run_lift.summarize_probes(recs)
    assert s["skills"]["d/s1"] == {"correct_a": 0, "correct_b": 2, "wrong_a": 1, "wrong_b": 0,
                                   "neither_a": 1, "neither_b": 0, "paired": 2, "errors": 0}
    assert s["skills"]["d/s2"]["correct_a"] == 1 and s["skills"]["d/s2"]["wrong_a"] == 1
    assert s["skills"]["d/s2"]["errors"] == 1 and s["skills"]["d/s2"]["paired"] == 2
    o = s["overall"]
    assert o["paired"] == 4 and o["errors"] == 1
    assert o["pct_correct_a"] == pytest.approx(25.0) and o["pct_correct_b"] == pytest.approx(75.0)
    assert o["pct_wrong_a"] == pytest.approx(50.0) and o["pct_wrong_b"] == pytest.approx(25.0)
    text = run_lift.format_probe_summary(s)
    assert "d/s1" in text and "correct" in text.lower()


def test_probe_run_end_to_end_with_fake_claude(world, tmp_path, capsys):
    pf = _write_probes(tmp_path / "p.json", [PROBE])
    argv = ["--probes", str(pf), "--out", str(world["out"]), "--repo-root", str(world["root"]),
            "--claude-bin", str(world["fake"])]
    assert run_lift.main(argv) == 0
    res = json.loads((world["out"] / "probe-results.json").read_text())
    arms = res["probes"][0]["runs"][0]
    assert arms["A"]["grade"]["verdict"] == "wrong" and arms["B"]["grade"]["verdict"] == "correct"
    assert "demo-1" in capsys.readouterr().out
    # probe B prompt carries the skill package, A does not
    assert run_lift.main(argv + ["--dry-run"]) == 0
    a = (world["out"] / "prompts" / "demo-1.A.txt").read_text()
    b = (world["out"] / "prompts" / "demo-1.B.txt").read_text()
    assert SKILL_MARK in b and SKILL_MARK not in a and "handler" in a
    g = (world["out"] / "prompts" / "demo-1.grader.txt").read_text()
    assert "In a handler class." in g


def test_probe_bad_verdict_is_a_recorded_error(world, tmp_path, monkeypatch):
    monkeypatch.setenv("FAKE_GRADER", "bad")
    pf = _write_probes(tmp_path / "p.json", [PROBE])
    assert run_lift.main(["--probes", str(pf), "--out", str(world["out"]), "--repo-root", str(world["root"]),
                          "--claude-bin", str(world["fake"])]) == 2
    res = json.loads((world["out"] / "probe-results.json").read_text())
    assert res["probes"][0]["runs"][0]["A"]["grade"] is None
    assert res["summary"]["overall"]["errors"] == 2


# --------------------------------------------------------------------------- v2: convention-free

CONV_CASE = """## Case 1 - Conventions

**User prompt:**

> "Add a trigger."

**Expected output MUST include:**

- A handler class extending `TriggerHandler` (see `templates/apex/TriggerHandler.cls`).
- A bypass record in `Trigger_Setting__mdt` so ops can deactivate it.
- Bulk-safe parent lookup with one SOQL.
- Use the repo skill via sfskills guidance,
  continued on an indented second line.

**Expected output MUST NOT include:**

- SOQL in a loop.
- A second framework when the template is available.

**Rubric (0-5):**

- **Correctness:** Does it enforce both rules?
- **Convention:** Follows this repo's TriggerControl pattern.
- **Citation of official docs:** Links to developer.salesforce.com.

**Reference answer (gold):**

Use a handler; templates/apex/TriggerHandler.cls is the base.
"""


def test_strip_conventions_counts_and_keeps():
    r = run_lift.strip_conventions(CONV_CASE)
    # repo lines: templates/, Trigger_Setting__mdt, sfskills (+continuation), "the template", TriggerControl
    assert r.repo == 5 and r.citation == 1 and r.stripped == 6
    t = r.text
    for gone in ("templates/apex/TriggerHandler.cls)", "Trigger_Setting__mdt", "sfskills", "continued on an indented",
                 "the template is available", "TriggerControl", "Citation of official docs"):
        assert gone not in t
    for kept in ("Bulk-safe parent lookup", "SOQL in a loop", "Correctness"):
        assert kept in t
    # the question and the gold answer are not rubric/MUST lines: untouched
    assert "Add a trigger." in t and "templates/apex/TriggerHandler.cls is the base" in t
    assert run_lift.rubric_items(t) == ["Correctness"]


def test_strip_conventions_exactly_three_repo_lines():
    text = CONV_CASE.replace("- Use the repo skill via sfskills guidance,\n  continued on an indented second line.\n", "")
    text = text.replace("- A second framework when the template is available.\n", "- A second ad-hoc framework.\n")
    text = text.replace("- **Citation of official docs:** Links to developer.salesforce.com.\n", "")
    r = run_lift.strip_conventions(text)
    assert r.stripped == 3 and r.repo == 3 and r.citation == 0


def test_strip_conventions_noop_on_clean_case():
    clean = EVAL.split("## Case 1")[1]
    r = run_lift.strip_conventions("## Case 1" + clean)
    assert r.stripped == 0 and r.text.strip() == ("## Case 1" + clean).strip()


def test_convention_free_dry_run_hides_repo_lines_and_reports_counts(world, capsys):
    ev = world["eval"]
    ev.write_text(EVAL.replace("- A handler class.", "- A handler class from `templates/apex/TriggerHandler.cls`.\n- A handler class.")
                  .replace("- **Completeness:** Is it whole?",
                           "- **Completeness:** Is it whole?\n- **Citation of official docs:** Link them."))
    assert run_lift.main(_argv(world, "--dry-run", "--convention-free")) == 0
    g = (world["out"] / "prompts" / "apex__demo-skill__case1.grader.txt").read_text()
    assert "templates/apex" not in g and "Citation of official docs" not in g and "Completeness" in g
    assert "stripped 2" in capsys.readouterr().out.lower()
    # without the flag nothing is stripped
    assert run_lift.main(_argv(world, "--dry-run")) == 0
    g = (world["out"] / "prompts" / "apex__demo-skill__case1.grader.txt").read_text()
    assert "templates/apex" in g and "Citation of official docs" in g


def test_convention_free_results_record_stripped_per_case(world):
    world["eval"].write_text(EVAL.replace("- A handler class.", "- A handler class from `templates/apex/TriggerHandler.cls`."))
    assert run_lift.main(_argv(world, "--convention-free")) == 0
    res = json.loads((world["out"] / "results.json").read_text())
    assert res["cases"][0]["stripped"] == {"repo": 1, "names": 0, "citation": 0, "total": 1}
    assert res["convention_free"] is True


def test_grade_cache_is_invalidated_when_the_grader_prompt_changes(world):
    world["eval"].write_text(EVAL.replace("- A handler class.", "- A handler class from `templates/apex/TriggerHandler.cls`."))
    assert run_lift.main(_argv(world)) == 0
    first = json.loads((world["out"] / "results.json").read_text())["cases"][0]["arms"]["A"]["cost_usd"]
    gf = next((world["out"] / "grades").glob("*.json"))
    before = json.loads(gf.read_text())["prompt_sha"]
    assert run_lift.main(_argv(world, "--convention-free")) == 0   # same --out, different grader prompt
    assert json.loads(gf.read_text())["prompt_sha"] != before
    assert first > 0


# --------------------------------------------------------------------------- v2: repeats

def test_cache_key_includes_repeat_index():
    keys = {run_lift.cache_key("c1", r, a) for r in range(3) for a in run_lift.ARMS}
    assert len(keys) == 6
    assert run_lift.cache_key("c1", 0, "A") != run_lift.cache_key("c1", 1, "A")


def test_repeats_default_one_and_two_runs_are_fresh_calls(world):
    assert run_lift.main(_argv(world)) == 0
    assert len(list((world["out"] / "answers").glob("*.txt"))) == 2
    assert run_lift.main(_argv(world, "--repeats", "2")) == 0          # r0 cached, r1 fresh
    assert len(list((world["out"] / "answers").glob("*.txt"))) == 4
    res = json.loads((world["out"] / "results.json").read_text())
    assert len(res["cases"][0]["repeats"]) == 2
    assert res["summary"]["overall"]["paired"] == 2 and res["summary"]["overall"]["repeats"] == 2
    world["fake"].write_text("#!/bin/sh\nexit 9\n")
    assert run_lift.main(_argv(world, "--repeats", "2")) == 0          # all cached


def test_repeats_must_be_positive(world):
    assert run_lift.main(_argv(world, "--repeats", "0")) == 3


def _rep_case(skill, name, pairs):
    """pairs: [(a_score, b_score), ...], one per repeat"""
    def arm(score):
        return {"answer": "x", "answer_error": None, "grade_error": None, "cost_usd": 0.0, "duration_s": 0.0,
                "tokens": {"input": 0, "output": 0},
                "grade": {"rubric": {"i": score}, "must_violations": []}}
    return {"id": name, "skill": skill, "repeats": [{"A": arm(a), "B": arm(b)} for a, b in pairs]}


def test_summary_repeats_mean_stdev_and_sign_test():
    cases = [_rep_case("s", "c1", [(2, 4), (3, 4)]),     # +2, +1
             _rep_case("s", "c2", [(3, 3), (4, 3)])]     # 0, -1
    s = run_lift.summarize(cases)
    o = s["overall"]
    assert o["paired"] == 4 and o["repeats"] == 2
    assert o["mean_delta"] == pytest.approx(0.5)
    assert o["stdev_delta"] == pytest.approx(statistics_stdev([2, 1, 0, -1]))
    assert (o["b_gt_a"], o["b_lt_a"], o["tie"]) == (2, 1, 1)
    assert o["sign_p"] == pytest.approx(1.0)              # 2 vs 1, two-sided exact
    # per-repeat means: repeat 0 -> (2+0)/2 = 1.0, repeat 1 -> (1-1)/2 = 0.0
    assert o["repeat_means"] == [pytest.approx(1.0), pytest.approx(0.0)]
    text = run_lift.format_summary(s)
    assert "±" in text and "sign test" in text.lower()


def statistics_stdev(xs):
    import statistics
    return statistics.stdev(xs)


def test_sign_test_p_values():
    assert run_lift.sign_test_p(10, 0) == pytest.approx(2 * 0.5 ** 10)
    assert run_lift.sign_test_p(5, 5) == pytest.approx(1.0)
    assert run_lift.sign_test_p(0, 0) is None


def test_strip_conventions_counts_template_class_names_separately():
    text = CONV_CASE.replace("- Bulk-safe parent lookup with one SOQL.",
                             "- Bulk-safe parent lookup with one SOQL.\n- Logs failures through `ApplicationLogger`.")
    r = run_lift.strip_conventions(text)
    assert (r.repo, r.names, r.citation, r.stripped) == (5, 1, 1, 7)
    assert "ApplicationLogger" not in r.text and "Bulk-safe parent lookup" in r.text
