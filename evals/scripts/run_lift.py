#!/usr/bin/env python3
"""Knowledge-lift test: does loading a skill package change answer quality?

For every golden case the harness asks the same question twice with headless
`claude -p`:

    Arm A (without)  the case's question (and context, if any) only
    Arm B (with)     SKILL.md + references/llm-anti-patterns.md of the skill
                     under test, prepended under a one-line instruction, then
                     the same question

Each answer is graded by a SEPARATE call (default model: opus) that sees the
case rubric, MUST / MUST NOT lists and reference answer plus the candidate
answer, and nothing that says which arm produced it. The grader prompt is
byte-for-byte the same shape for both arms.

Fail closed: a non-zero `claude` exit, a call-level error, or a grade that is
not strict JSON with numeric rubric scores is recorded as an error for that
case/arm and counted in the summary; nothing is silently skipped. Answers and
grades are cached under --out so a rerun resumes.

Calls run from a neutral working directory with --setting-sources "" and
--strict-mcp-config so the repo's CLAUDE.md, the user's memory and MCP tool
lists do not leak into either arm.

Exit codes: 0 ok, 2 at least one call/grade error, 3 invalid usage.
"""

from __future__ import annotations

import argparse
import json
import re
import statistics
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_evals import REPO_ROOT, EvalFile, iter_eval_files, parse_eval_file  # noqa: E402

DEFAULT_OUT = Path("/private/tmp/claude-501/-Users-pranavnagrecha-VS-Code-Personal-SfSkills/"
                   "22639449-d0eb-436f-9880-7e985367ef94/scratchpad/lift")
SKILL_INSTRUCTION = "Use the following skill package when answering."
ARMS = ("A", "B")
CALL_TIMEOUT_S = 900
# Same system prompt for both arms. Without it Claude Code's default prompt makes the model
# emit pseudo tool calls ("let me look at the project layout") instead of answering.
ANSWER_SYSTEM = ("You are an expert Salesforce developer answering a colleague's question. No tools, "
                 "files or org access are available. Answer directly and completely in a single reply, "
                 "including code where the task calls for it. Do not ask to inspect the project.")
GRADER_SYSTEM = ("You are a strict, careful eval grader. No tools are available. "
                 "Reply with only the JSON object requested.")


class LiftError(Exception):
    """A single claude call or grade failed. Always recorded, never swallowed."""


# --------------------------------------------------------------------------- parsing

def _section(body: str, marker: str) -> str | None:
    """Text after `marker` up to the next bold-header line (`**Something`)."""
    lines = body.splitlines()
    for i, line in enumerate(lines):
        if line.startswith(marker):
            first = line[len(marker):].strip()
            rest: list[str] = [first] if first else []
            for nxt in lines[i + 1:]:
                if nxt.startswith("**") or nxt.startswith("## "):
                    break
                rest.append(nxt)
            return "\n".join(rest).strip()
    return None


def _unquote(text: str) -> str:
    out = [re.sub(r"^>\s?", "", ln) for ln in text.splitlines()]
    t = "\n".join(out).strip()
    if len(t) >= 2 and t[0] in "\"“" and t[-1] in "\"”":
        t = t[1:-1].strip()
    return t


def case_question(case_text: str) -> str:
    """The user-facing task: the prompt plus any provided context. Nothing else."""
    prompt = _section(case_text, "**User prompt:**")
    if not prompt:
        raise LiftError("case has no **User prompt:** text")
    q = _unquote(prompt)
    ctx = _section(case_text, "**Context provided:**")
    if ctx and ctx.strip().strip(".").lower() not in ("none", "n/a", ""):
        q += "\n\nContext provided:\n" + ctx
    return q


def rubric_items(case_text: str) -> list[str]:
    sec = _section(case_text, "**Rubric") or ""
    # the first line of the section is the remainder of the header line, e.g. "(0-5):"
    return [m.group(1).strip() for m in re.finditer(r"^- \*\*(.+?):?\*\*", sec, re.M)]


def case_number(name: str) -> int:
    m = re.search(r"Case\s+(\d+)", name)
    return int(m.group(1)) if m else 0


def skill_dir(ef: EvalFile, repo_root: Path) -> Path:
    raw = ef.metadata.get("Skill under test", "").strip().strip("`")
    if not raw:
        raise LiftError(f"{ef.path.name}: no 'Skill under test' metadata")
    p = Path(raw)
    if p.name == "SKILL.md":
        p = p.parent
    d = (repo_root / p).resolve()
    if not (d / "SKILL.md").is_file():
        raise LiftError(f"{ef.path.name}: {d / 'SKILL.md'} not found")
    return d


def skill_package_text(sdir: Path) -> str:
    parts = [f"=== {sdir.name}/SKILL.md ===\n" + (sdir / "SKILL.md").read_text(encoding="utf-8")]
    ap = sdir / "references" / "llm-anti-patterns.md"
    if ap.is_file():
        parts.append(f"=== {sdir.name}/references/llm-anti-patterns.md ===\n" + ap.read_text(encoding="utf-8"))
    return "\n\n".join(parts)


def build_answer_prompts(question: str, package: str) -> dict[str, str]:
    return {
        "A": question,
        "B": f"{SKILL_INSTRUCTION}\n\n<skill_package>\n{package}\n</skill_package>\n\n{question}",
    }


def build_grader_prompt(case_text: str, answer: str, items: list[str]) -> str:
    keys = ", ".join(f'"{i}"' for i in items) if items else "(every rubric item in the case)"
    return (
        "You are an eval grader. Below is an eval case (task, MUST / MUST NOT lists, rubric and gold "
        "reference answer) followed by a candidate answer. Score the candidate against the case.\n"
        "- For each rubric item give an integer 1-5 (5 = fully meets the gold standard). "
        f"Use exactly these rubric item names as keys: {keys}.\n"
        "- List in \"must_violations\" every MUST item the candidate omits and every MUST NOT item it "
        "contains, one short string each; use [] if there are none.\n"
        "- Judge only the candidate text. Be strict: do not reward length or confidence.\n"
        "Reply with ONLY strict JSON, no prose, no code fence:\n"
        '{"rubric": {"<rubric item>": <1-5>}, "must_violations": ["..."], "notes": "<one sentence>"}\n\n'
        "=== EVAL CASE ===\n" + case_text.strip() + "\n\n=== CANDIDATE ANSWER ===\n" + answer.strip() + "\n"
    )


def parse_grade(text: str) -> dict:
    """Strict-ish: tolerate a code fence, nothing else. Raises LiftError on any fault."""
    t = text.strip()
    if "{" not in t or "}" not in t:
        raise LiftError("grader returned non-JSON")
    try:
        g = json.loads(t[t.index("{"): t.rindex("}") + 1])
    except json.JSONDecodeError:
        raise LiftError("grader returned non-JSON") from None
    rub = g.get("rubric") if isinstance(g, dict) else None
    if (not isinstance(rub, dict) or not rub
            or not all(isinstance(v, (int, float)) and not isinstance(v, bool) and 0 <= v <= 5
                       for v in rub.values())):
        raise LiftError("grader returned no numeric rubric scores in 0-5")
    mv = g.get("must_violations")
    if not isinstance(mv, list):
        raise LiftError("grader returned no must_violations list")
    return g


# --------------------------------------------------------------------------- claude

@dataclass
class Call:
    text: str
    cost_usd: float
    duration_s: float
    input_tokens: int
    output_tokens: int


def run_claude(claude_bin: str, model: str, prompt: str, cwd: Path, system: str) -> Call:
    cmd = [claude_bin, "-p", "--model", model, "--system-prompt", system, "--tools", "", "--disable-slash-commands",
           "--no-session-persistence", "--setting-sources", "", "--strict-mcp-config",
           "--output-format", "json"]
    t0 = time.monotonic()
    try:
        proc = subprocess.run(cmd, input=prompt, capture_output=True, text=True, cwd=cwd,
                              timeout=CALL_TIMEOUT_S, check=False)
    except FileNotFoundError:
        raise LiftError(f"claude binary not found: {claude_bin}") from None
    except subprocess.TimeoutExpired:
        raise LiftError(f"claude timed out after {CALL_TIMEOUT_S}s") from None
    wall = time.monotonic() - t0
    if proc.returncode != 0:
        raise LiftError(f"claude exit {proc.returncode}: {(proc.stderr or proc.stdout).strip()[:300]}")
    try:
        env = json.loads(proc.stdout)
    except json.JSONDecodeError:
        raise LiftError(f"claude returned a non-JSON envelope: {proc.stdout.strip()[:200]!r}") from None
    if not isinstance(env, dict) or env.get("is_error") or not isinstance(env.get("result"), str):
        raise LiftError(f"claude reported an error: {str(env)[:300]}")
    if not env["result"].strip():
        raise LiftError("claude returned an empty answer")
    if "<invoke name=" in env["result"] or "<function_calls>" in env["result"]:
        raise LiftError("claude emitted tool-call markup instead of an answer")
    u = env.get("usage") or {}
    tin = sum(int(u.get(k) or 0) for k in ("input_tokens", "cache_creation_input_tokens",
                                           "cache_read_input_tokens"))
    return Call(env["result"], float(env.get("total_cost_usd") or 0.0),
                (env.get("duration_ms") or wall * 1000) / 1000.0, tin, int(u.get("output_tokens") or 0))


# --------------------------------------------------------------------------- one case/arm

def _meta(call: Call) -> dict:
    return {"cost_usd": call.cost_usd, "duration_s": call.duration_s,
            "input_tokens": call.input_tokens, "output_tokens": call.output_tokens}


def run_arm(cid: str, arm: str, prompt: str, case_text: str, items: list[str], out: Path,
            args: argparse.Namespace, cwd: Path) -> dict:
    ans_f = out / "answers" / f"{cid}.{arm}.txt"
    ans_meta_f = out / "answers" / f"{cid}.{arm}.meta.json"
    grade_f = out / "grades" / f"{cid}.{arm}.json"
    rec: dict = {"answer": None, "answer_error": None, "grade": None, "grade_error": None,
                 "cost_usd": 0.0, "duration_s": 0.0, "tokens": {"input": 0, "output": 0}}

    def add(meta: dict) -> None:
        rec["cost_usd"] += meta["cost_usd"]
        rec["duration_s"] += meta["duration_s"]
        rec["tokens"]["input"] += meta["input_tokens"]
        rec["tokens"]["output"] += meta["output_tokens"]

    if ans_f.is_file():  # cache hit
        rec["answer"] = ans_f.read_text(encoding="utf-8")
        if ans_meta_f.is_file():
            add(json.loads(ans_meta_f.read_text()))
    else:
        try:
            call = run_claude(args.claude_bin, args.answer_model, prompt, cwd, ANSWER_SYSTEM)
        except LiftError as exc:
            rec["answer_error"] = str(exc)
            return rec
        ans_f.write_text(call.text, encoding="utf-8")
        ans_meta_f.write_text(json.dumps(_meta(call)))
        rec["answer"] = call.text
        add(_meta(call))

    if grade_f.is_file():
        stored = json.loads(grade_f.read_text())
        rec["grade"] = stored["grade"]
        add(stored["meta"])
        return rec
    try:
        call = run_claude(args.claude_bin, args.grader_model,
                          build_grader_prompt(case_text, rec["answer"], items), cwd, GRADER_SYSTEM)
        add(_meta(call))
        grade = parse_grade(call.text)
    except LiftError as exc:
        rec["grade_error"] = str(exc)
        return rec
    rec["grade"] = grade
    grade_f.write_text(json.dumps({"grade": grade, "meta": _meta(call), "raw": call.text}, indent=2))
    return rec


# --------------------------------------------------------------------------- summary

def _case_mean(arm: dict) -> float | None:
    g = arm.get("grade")
    if not g or arm.get("grade_error") or arm.get("answer_error"):
        return None
    return statistics.fmean(g["rubric"].values())


def _fmt(x: float | None) -> str:
    return "n/a" if x is None else f"{x:.2f}"


def summarize(cases: list[dict]) -> dict:
    skills: dict[str, dict] = {}
    deltas: list[float] = []
    b_gt = b_lt = tie = errors = 0
    cost = secs = 0.0
    tin = tout = 0
    for c in cases:
        s = skills.setdefault(c["skill"], {"a": [], "b": [], "must_a": 0, "must_b": 0,
                                           "paired": 0, "errors": 0, "cases": 0})
        s["cases"] += 1
        ma, mb = _case_mean(c["arms"]["A"]), _case_mean(c["arms"]["B"])
        for arm in ARMS:
            a = c["arms"][arm]
            cost += a["cost_usd"]
            secs += a["duration_s"]
            tin += a["tokens"]["input"]
            tout += a["tokens"]["output"]
            if a.get("answer_error") or a.get("grade_error") or not a.get("grade"):
                errors += 1
                s["errors"] += 1
        if ma is not None and mb is not None:  # means/MUST counts cover paired cases only
            s["a"].append(ma)
            s["b"].append(mb)
            s["must_a"] += len(c["arms"]["A"]["grade"]["must_violations"])
            s["must_b"] += len(c["arms"]["B"]["grade"]["must_violations"])
            s["paired"] += 1
            d = mb - ma
            deltas.append(d)
            if abs(d) < 1e-9:
                tie += 1
            elif d > 0:
                b_gt += 1
            else:
                b_lt += 1
    out_skills = {}
    for name, s in skills.items():
        ma = statistics.fmean(s["a"]) if s["a"] else None
        mb = statistics.fmean(s["b"]) if s["b"] else None
        out_skills[name] = {"mean_a": ma, "mean_b": mb,
                            "delta": (mb - ma) if ma is not None and mb is not None else None,
                            "must_a": s["must_a"], "must_b": s["must_b"],
                            "cases": s["cases"], "paired": s["paired"], "errors": s["errors"]}
    return {"skills": out_skills,
            "overall": {"cases": len(cases), "paired": len(deltas),
                        "mean_delta": statistics.fmean(deltas) if deltas else None,
                        "b_gt_a": b_gt, "b_lt_a": b_lt, "tie": tie, "errors": errors},
            "cost_usd": cost, "call_seconds": secs, "input_tokens": tin, "output_tokens": tout}


def format_summary(s: dict) -> str:
    rows = [f"{'skill':34} {'meanA':>6} {'meanB':>6} {'delta':>6} {'MUST A/B':>9} {'paired':>6} {'err':>3}"]
    for name, k in sorted(s["skills"].items()):
        d = "n/a" if k["delta"] is None else f"{k['delta']:+.2f}"
        rows.append(f"{name:34} {_fmt(k['mean_a']):>6} {_fmt(k['mean_b']):>6} {d:>6} "
                    f"{str(k['must_a']) + '/' + str(k['must_b']):>9} {k['paired']:>6} {k['errors']:>3}")
    o = s["overall"]
    md = "n/a" if o["mean_delta"] is None else f"{o['mean_delta']:+.3f}"
    rows += ["", f"overall: mean delta (B - A) {md} over {o['paired']} paired of {o['cases']} cases",
             f"  B > A: {o['b_gt_a']}   B < A: {o['b_lt_a']}   tie: {o['tie']}",
             f"  errors: {o['errors']} (call/arm failures, excluded from deltas)",
             f"cost: ${s['cost_usd']:.2f}   claude call time: {s['call_seconds']:.0f}s "
             f"(sum across calls)   tokens in/out: {s['input_tokens']}/{s['output_tokens']}"]
    return "\n".join(rows)


# --------------------------------------------------------------------------- main

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Knowledge-lift test over the golden evals.")
    ap.add_argument("--file", type=Path, help="Run one eval file (default: all of evals/golden/).")
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT, help="Output/cache directory.")
    ap.add_argument("--answer-model", default="sonnet")
    ap.add_argument("--grader-model", default="opus")
    ap.add_argument("--dry-run", action="store_true",
                    help="Write the prompts to --out/prompts without calling claude.")
    ap.add_argument("--jobs", type=int, default=1, help="Concurrent case/arm workers (default 1).")
    ap.add_argument("--claude-bin", default="claude")
    ap.add_argument("--repo-root", type=Path, default=REPO_ROOT, help=argparse.SUPPRESS)
    args = ap.parse_args(argv)

    files = [parse_eval_file(p) for p in iter_eval_files(args.file.resolve() if args.file else None)]
    out: Path = args.out
    for sub in ("prompts", "answers", "grades", "cwd"):
        (out / sub).mkdir(parents=True, exist_ok=True)

    jobs: list[tuple] = []  # (cid, skill, arm, prompt, case_text, items)
    order: list[dict] = []
    for ef in files:
        if ef.errors:
            print(f"[ERROR] {ef.path.name}: {'; '.join(ef.errors)}", file=sys.stderr)
            return 3
        try:
            package = skill_package_text(skill_dir(ef, args.repo_root))
        except LiftError as exc:
            print(f"[ERROR] {exc}", file=sys.stderr)
            return 3
        skill = ef.metadata.get("Skill under test", "").strip().strip("`")
        skill = Path(skill).parent.name if skill.endswith("SKILL.md") else skill
        for case in ef.cases:
            cid = f"{ef.path.stem}__case{case_number(case.name)}"
            items = rubric_items(case.text)
            prompts = build_answer_prompts(case_question(case.text), package)
            grader_preview = build_grader_prompt(case.text, "[CANDIDATE ANSWER GOES HERE]", items)
            (out / "prompts" / f"{cid}.grader.txt").write_text(grader_preview, encoding="utf-8")
            for arm in ARMS:
                (out / "prompts" / f"{cid}.{arm}.txt").write_text(prompts[arm], encoding="utf-8")
                jobs.append((cid, arm, prompts[arm], case.text, items))
            order.append({"id": cid, "skill": skill, "file": ef.path.name, "case": case.name})

    if args.dry_run:
        print(f"dry run: wrote {len(jobs)} answer prompts + {len(order)} grader templates to {out / 'prompts'}")
        return 0

    t0 = time.monotonic()
    cwd = out / "cwd"
    with ThreadPoolExecutor(max_workers=max(1, args.jobs)) as pool:
        futs = {(cid, arm): pool.submit(run_arm, cid, arm, prompt, ctext, items, out, args, cwd)
                for cid, arm, prompt, ctext, items in jobs}
        for (cid, arm), f in futs.items():
            rec = f.result()
            for meta in order:
                if meta["id"] == cid:
                    meta.setdefault("arms", {})[arm] = rec
            tag = rec["answer_error"] or rec["grade_error"]
            print(f"[{'ERR' if tag else 'ok '}] {cid} arm {arm}" + (f": {tag}" if tag else ""), flush=True)
    elapsed = time.monotonic() - t0

    summary = summarize(order)
    summary["elapsed_s"] = elapsed
    (out / "results.json").write_text(json.dumps(
        {"answer_model": args.answer_model, "grader_model": args.grader_model,
         "cases": order, "summary": summary}, indent=2))
    print()
    print(format_summary(summary))
    print(f"elapsed wall time: {elapsed:.0f}s   results: {out / 'results.json'}")
    return 2 if summary["overall"]["errors"] else 0


if __name__ == "__main__":
    sys.exit(main())
