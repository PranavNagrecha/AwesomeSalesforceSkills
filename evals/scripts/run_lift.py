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

v2 additions (they remove the v1 caveats, see evals/measurement/lift-baseline-2026-10-19.json):

    --probes [FILE]       Wrong-fact probes (evals/probes/wrong-fact-probes.json): one practitioner question per
                          claim a skill corrected, graded BINARY and convention-free by a grader that is told the
                          correct and the wrong answer: {"verdict": "correct"|"wrong"|"neither", "quote": ...}.
    --convention-free     Golden cases only: strip rubric / MUST lines that reward repo artefacts (templates/,
                          *_mdt, TriggerControl, sfskills, "this repo", "the template") and the "Citation of
                          official docs" rubric item before grading; the count per case is recorded.
    --repeats N           N fresh answers per arm per case (cache key includes the repeat index); the summary
                          reports mean +/- stdev of the paired deltas and an exact two-sided sign test.

Exit codes: 0 ok, 2 at least one call/grade error, 3 invalid usage.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import statistics
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_evals import REPO_ROOT, EvalFile, iter_eval_files, parse_eval_file  # noqa: E402

DEFAULT_OUT = Path("/private/tmp/claude-501/-Users-pranavnagrecha-VS-Code-Personal-SfSkills/"
                   "22639449-d0eb-436f-9880-7e985367ef94/scratchpad/lift")
DEFAULT_PROBES = REPO_ROOT / "evals" / "probes" / "wrong-fact-probes.json"
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


def build_grader_prompt(case_text: str, answer: str, items: list[str], convention_free: bool = False) -> str:
    keys = ", ".join(f'"{i}"' for i in items) if items else "(every rubric item in the case)"
    note = ("- The reference answer may use repo-specific templates or custom-metadata names. Do not penalise "
            "the candidate for not using them; judge the engineering substance only.\n") if convention_free else ""
    return (
        "You are an eval grader. Below is an eval case (task, MUST / MUST NOT lists, rubric and gold "
        "reference answer) followed by a candidate answer. Score the candidate against the case.\n"
        "- For each rubric item give an integer 1-5 (5 = fully meets the gold standard). "
        f"Use exactly these rubric item names as keys: {keys}.\n"
        "- List in \"must_violations\" every MUST item the candidate omits and every MUST NOT item it "
        "contains, one short string each; use [] if there are none.\n"
        "- Judge only the candidate text. Be strict: do not reward length or confidence.\n"
        + note +
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


# --------------------------------------------------------------------------- v2: convention-free

# Lines that reward the repo's own artefacts rather than Salesforce correctness.
REPO_ARTEFACT = re.compile(
    r"templates/|\b\w*_mdt\b|__mdt\b|TriggerControl|Trigger_Setting|sfskills|this repo|the template",
    re.IGNORECASE)
# Beyond the spec'd patterns: the class names the repo's templates/ ship (the golden cases reward "uses
# HttpClient / ApplicationLogger / SecurityUtils / the canonical TriggerHandler"), counted separately.
REPO_TEMPLATE_NAMES = re.compile(
    r"\b(ApplicationLogger|HttpClient|SecurityUtils|TriggerHandler|BaseDomain|BaseService|BaseSelector|"
    r"TestDataFactory|TestRecordBuilder|MockHttpResponseGenerator|TestUserFactory|BulkTestPattern|"
    r"Application_Log__c)\b|\bcanonical\b", re.IGNORECASE)
_STRIP_SECTIONS = ("**Expected output MUST include", "**Expected output MUST NOT include", "**Rubric")


@dataclass
class Stripped:
    text: str
    repo: int = 0        # MUST / MUST NOT / rubric bullets matching REPO_ARTEFACT (the spec'd patterns)
    names: int = 0       # bullets that only name a repo template class (REPO_TEMPLATE_NAMES)
    citation: int = 0    # the "Citation of official docs" rubric bullets

    @property
    def stripped(self) -> int:
        return self.repo + self.names + self.citation


def strip_conventions(case_text: str) -> Stripped:
    """Drop repo-convention bullets from the MUST / MUST NOT / Rubric sections, and the citation rubric item.

    A bullet is one `- ` line plus its indented continuation lines and counts once. The question, the
    context and the gold reference answer are never touched."""
    lines = case_text.splitlines()
    out: list[str] = []
    res = Stripped("")
    section = None
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("**") or line.startswith("## "):
            section = line if line.startswith(_STRIP_SECTIONS) else None
        if section and re.match(r"^[-*] ", line):
            j = i + 1
            while j < len(lines) and lines[j].strip() and re.match(r"^\s+\S", lines[j]):
                j += 1
            bullet = lines[i:j]
            joined = " ".join(bullet)
            name = re.match(r"^[-*] \*\*(.+?):?\*\*", line)
            if section.startswith("**Rubric") and name and name.group(1).strip().lower().startswith("citation"):
                res.citation += 1
            elif REPO_ARTEFACT.search(joined):
                res.repo += 1
            elif REPO_TEMPLATE_NAMES.search(joined):
                res.names += 1
            else:
                out.extend(bullet)
            i = j
            continue
        out.append(line)
        i += 1
    res.text = "\n".join(out)
    return res


# --------------------------------------------------------------------------- v2: wrong-fact probes

VERDICTS = ("correct", "wrong", "neither")
_PROBE_FIELDS = ("id", "skill", "question", "wrong_answer", "correct_answer", "source")


def load_probes(path: Path) -> list[dict]:
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise LiftError(f"cannot read probe file {path}: {exc}") from None
    probes = data.get("probes") if isinstance(data, dict) else data
    if not isinstance(probes, list) or not probes:
        raise LiftError(f"{path}: no probes")
    seen: set[str] = set()
    for n, p in enumerate(probes, 1):
        if not isinstance(p, dict):
            raise LiftError(f"probe #{n} is not an object")
        for f in _PROBE_FIELDS:
            if not isinstance(p.get(f), str) or not p[f].strip():
                raise LiftError(f"probe #{n} ({p.get('id', '?')}): missing or empty '{f}'")
        if not re.fullmatch(r"[A-Za-z0-9._-]+", p["id"]):
            raise LiftError(f"probe #{n}: id {p['id']!r} must be filename-safe")
        if p["id"] in seen:
            raise LiftError(f"duplicate probe id {p['id']}")
        seen.add(p["id"])
        if not re.fullmatch(r"[a-z0-9-]+/[a-z0-9-]+", p["skill"]):
            raise LiftError(f"probe {p['id']}: skill must be '<domain>/<slug>', got {p['skill']!r}")
        if not re.search(r"\bL\d+", p["source"]):
            raise LiftError(f"probe {p['id']}: source needs a '<corpus file> L<n>' line cite")
    return probes


def build_probe_grader_prompt(probe: dict, answer: str) -> str:
    return (
        "You are an eval grader checking ONE fact. Below is a practitioner question, the CORRECT fact, the "
        "WRONG fact a careless answer would give, and a candidate answer.\n"
        "Decide what the candidate answer asserts about that fact:\n"
        '- "correct": it states the correct fact (extra detail is fine).\n'
        '- "wrong": it asserts the wrong fact, or something that contradicts the correct fact.\n'
        '- "neither": it states neither, is silent on the point, or hedges without committing. '
        "If it asserts both, judge by what it finally tells the reader to do or believe; if that is "
        "unclear, answer neither.\n"
        "Ignore style, length and everything else. Do not use outside knowledge to overrule the CORRECT fact "
        "given here.\n"
        'Reply with ONLY strict JSON, no prose, no code fence:\n'
        '{"verdict": "correct" | "wrong" | "neither", "quote": "<the sentence of the candidate answer you '
        'judged, copied verbatim; empty if neither>"}\n\n'
        f"=== QUESTION ===\n{probe['question'].strip()}\n\n"
        f"=== CORRECT FACT ===\n{probe['correct_answer'].strip()}\n\n"
        f"=== WRONG FACT ===\n{probe['wrong_answer'].strip()}\n\n"
        f"=== CANDIDATE ANSWER ===\n{answer.strip()}\n"
    )


def _flat(t: str) -> str:
    return re.sub(r"[\s*`_]+", " ", t).strip().lower()


def parse_probe_grade(text: str, answer: str) -> dict:
    """Fail closed: anything but a verdict in VERDICTS plus a string quote is an error."""
    t = text.strip()
    if "{" not in t or "}" not in t:
        raise LiftError("grader returned non-JSON")
    try:
        g = json.loads(t[t.index("{"): t.rindex("}") + 1])
    except json.JSONDecodeError:
        raise LiftError("grader returned non-JSON") from None
    if not isinstance(g, dict) or g.get("verdict") not in VERDICTS:
        raise LiftError(f"grader returned no valid verdict (want one of {VERDICTS})")
    if not isinstance(g.get("quote"), str):
        raise LiftError("grader returned no quote string")
    q = g["quote"]
    return {"verdict": g["verdict"], "quote": q,
            "quote_found": bool(q.strip()) and _flat(q) in _flat(answer)}


def probe_package(probe: dict, repo_root: Path) -> str:
    d = (repo_root / "skills" / probe["skill"]).resolve()
    if not (d / "SKILL.md").is_file():
        raise LiftError(f"probe {probe['id']}: {d / 'SKILL.md'} not found")
    return skill_package_text(d)


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


# --------------------------------------------------------------------------- one task/repeat/arm

@dataclass
class Task:
    """One thing to answer and grade: a golden case or a wrong-fact probe."""
    tid: str
    skill: str
    prompts: dict[str, str]                       # arm -> answer prompt
    make_grader: Callable[[str], str]             # candidate answer -> grader prompt
    parse: Callable[[str, str], dict]             # (grader text, candidate answer) -> grade
    meta: dict = field(default_factory=dict)


def cache_key(tid: str, repeat: int, arm: str) -> str:
    """Answer and grade files are named by this: a new repeat index is always a fresh call."""
    return f"{tid}.r{repeat}.{arm}"


def _meta(call: Call) -> dict:
    return {"cost_usd": call.cost_usd, "duration_s": call.duration_s,
            "input_tokens": call.input_tokens, "output_tokens": call.output_tokens}


def run_arm(task: Task, repeat: int, arm: str, out: Path, args: argparse.Namespace, cwd: Path) -> dict:
    key = cache_key(task.tid, repeat, arm)
    ans_f = out / "answers" / f"{key}.txt"
    ans_meta_f = out / "answers" / f"{key}.meta.json"
    grade_f = out / "grades" / f"{key}.json"
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
            call = run_claude(args.claude_bin, args.answer_model, task.prompts[arm], cwd, ANSWER_SYSTEM)
        except LiftError as exc:
            rec["answer_error"] = str(exc)
            return rec
        ans_f.write_text(call.text, encoding="utf-8")
        ans_meta_f.write_text(json.dumps(_meta(call)))
        rec["answer"] = call.text
        add(_meta(call))

    gprompt = task.make_grader(rec["answer"])
    sha = hashlib.sha256(gprompt.encode("utf-8")).hexdigest()[:16]
    if grade_f.is_file():
        stored = json.loads(grade_f.read_text())
        if stored.get("prompt_sha") == sha:   # a changed grader prompt (e.g. --convention-free) is a miss
            rec["grade"] = stored["grade"]
            add(stored["meta"])
            return rec
    try:
        call = run_claude(args.claude_bin, args.grader_model, gprompt, cwd, GRADER_SYSTEM)
        add(_meta(call))
        grade = task.parse(call.text, rec["answer"])
    except LiftError as exc:
        rec["grade_error"] = str(exc)
        return rec
    rec["grade"] = grade
    grade_f.write_text(json.dumps({"grade": grade, "meta": _meta(call), "raw": call.text, "prompt_sha": sha},
                                  indent=2))
    return rec


# --------------------------------------------------------------------------- summary

def sign_test_p(gt: int, lt: int) -> float | None:
    """Exact two-sided sign test on the non-tied pairs; None when there are none."""
    n = gt + lt
    if n == 0:
        return None
    k = min(gt, lt)
    return min(1.0, 2 * sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n)


def _case_mean(arm: dict) -> float | None:
    g = arm.get("grade")
    if not g or arm.get("grade_error") or arm.get("answer_error"):
        return None
    return statistics.fmean(g["rubric"].values())


def _fmt(x: float | None) -> str:
    return "n/a" if x is None else f"{x:.2f}"


def _runs(rec: dict) -> list[dict]:
    return rec.get("repeats") or ([rec["arms"]] if "arms" in rec else rec.get("runs", []))


def _arm_failed(a: dict) -> bool:
    return bool(a.get("answer_error") or a.get("grade_error") or not a.get("grade"))


def summarize(cases: list[dict]) -> dict:
    skills: dict[str, dict] = {}
    deltas: list[float] = []
    by_repeat: dict[int, list[float]] = {}
    b_gt = b_lt = tie = errors = 0
    cost = secs = 0.0
    tin = tout = 0
    nrep = 1
    for c in cases:
        s = skills.setdefault(c["skill"], {"a": [], "b": [], "must_a": 0, "must_b": 0,
                                           "paired": 0, "errors": 0, "cases": 0})
        s["cases"] += 1
        runs = _runs(c)
        nrep = max(nrep, len(runs))
        for r, arms in enumerate(runs):
            ma, mb = _case_mean(arms["A"]), _case_mean(arms["B"])
            for arm in ARMS:
                a = arms[arm]
                cost += a["cost_usd"]
                secs += a["duration_s"]
                tin += a["tokens"]["input"]
                tout += a["tokens"]["output"]
                if _arm_failed(a):
                    errors += 1
                    s["errors"] += 1
            if ma is not None and mb is not None:  # means/MUST counts cover paired runs only
                s["a"].append(ma)
                s["b"].append(mb)
                s["must_a"] += len(arms["A"]["grade"]["must_violations"])
                s["must_b"] += len(arms["B"]["grade"]["must_violations"])
                s["paired"] += 1
                d = mb - ma
                deltas.append(d)
                by_repeat.setdefault(r, []).append(d)
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
            "overall": {"cases": len(cases), "repeats": nrep, "paired": len(deltas),
                        "mean_delta": statistics.fmean(deltas) if deltas else None,
                        "stdev_delta": statistics.stdev(deltas) if len(deltas) > 1 else None,
                        "repeat_means": [statistics.fmean(by_repeat[r]) if r in by_repeat else None
                                         for r in range(nrep)],
                        "b_gt_a": b_gt, "b_lt_a": b_lt, "tie": tie, "sign_p": sign_test_p(b_gt, b_lt),
                        "errors": errors},
            "cost_usd": cost, "call_seconds": secs, "input_tokens": tin, "output_tokens": tout}


def _cost_line(s: dict) -> str:
    return (f"cost: ${s['cost_usd']:.2f}   claude call time: {s['call_seconds']:.0f}s "
            f"(sum across calls)   tokens in/out: {s['input_tokens']}/{s['output_tokens']}")


def format_summary(s: dict) -> str:
    rows = [f"{'skill':34} {'meanA':>6} {'meanB':>6} {'delta':>6} {'MUST A/B':>9} {'paired':>6} {'err':>3}"]
    for name, k in sorted(s["skills"].items()):
        d = "n/a" if k["delta"] is None else f"{k['delta']:+.2f}"
        rows.append(f"{name:34} {_fmt(k['mean_a']):>6} {_fmt(k['mean_b']):>6} {d:>6} "
                    f"{str(k['must_a']) + '/' + str(k['must_b']):>9} {k['paired']:>6} {k['errors']:>3}")
    o = s["overall"]
    md = "n/a" if o["mean_delta"] is None else f"{o['mean_delta']:+.3f}"
    sd = "" if o["stdev_delta"] is None else f" ± {o['stdev_delta']:.3f} (sd)"
    p = "n/a" if o["sign_p"] is None else f"{o['sign_p']:.4f}"
    rows += ["", f"overall: mean delta (B - A) {md}{sd} over {o['paired']} paired runs of {o['cases']} cases "
                 f"x {o['repeats']} repeat(s)",
             f"  B > A: {o['b_gt_a']}   B < A: {o['b_lt_a']}   tie: {o['tie']}",
             f"  sign test (ties excluded, exact two-sided): p = {p}"]
    if o["repeats"] > 1:
        rows.append("  mean delta per repeat: " + ", ".join(_fmt(x) if x is None else f"{x:+.3f}"
                                                            for x in o["repeat_means"]))
    rows += [f"  errors: {o['errors']} (call/arm failures, excluded from deltas)", _cost_line(s)]
    return "\n".join(rows)


def summarize_probes(probes: list[dict]) -> dict:
    keys = ("correct_a", "correct_b", "wrong_a", "wrong_b", "neither_a", "neither_b", "paired", "errors")
    skills: dict[str, dict] = {}
    tot = dict.fromkeys(keys, 0)
    cost = secs = 0.0
    tin = tout = 0
    nq = 0
    for pr in probes:
        sk = skills.setdefault(pr["skill"], dict.fromkeys(keys, 0))
        for arms in _runs(pr):
            for arm in ARMS:
                a = arms[arm]
                cost += a["cost_usd"]
                secs += a["duration_s"]
                tin += a["tokens"]["input"]
                tout += a["tokens"]["output"]
                if _arm_failed(a):
                    sk["errors"] += 1
                    tot["errors"] += 1
            if _arm_failed(arms["A"]) or _arm_failed(arms["B"]):
                continue
            sk["paired"] += 1
            tot["paired"] += 1
            for arm in ARMS:
                g = arms[arm]["grade"]
                col = f"{g['verdict']}_{arm.lower()}"
                sk[col] += 1
                tot[col] += 1
                nq += 0 if g.get("quote_found", True) else 1

    def pct(n: int) -> float | None:
        return 100.0 * n / tot["paired"] if tot["paired"] else None

    overall = {**tot, "probes": len(probes), "quotes_not_found": nq,
               "pct_correct_a": pct(tot["correct_a"]), "pct_correct_b": pct(tot["correct_b"]),
               "pct_wrong_a": pct(tot["wrong_a"]), "pct_wrong_b": pct(tot["wrong_b"]),
               "pct_neither_a": pct(tot["neither_a"]), "pct_neither_b": pct(tot["neither_b"])}
    return {"skills": skills, "overall": overall,
            "cost_usd": cost, "call_seconds": secs, "input_tokens": tin, "output_tokens": tout}


def format_probe_summary(s: dict) -> str:
    rows = [f"{'skill':44} {'cor A':>5} {'cor B':>5} {'wrg A':>5} {'wrg B':>5} {'nei A':>5} {'nei B':>5} "
            f"{'pair':>4} {'err':>3}"]
    for name, k in sorted(s["skills"].items()):
        rows.append(f"{name:44} {k['correct_a']:>5} {k['correct_b']:>5} {k['wrong_a']:>5} {k['wrong_b']:>5} "
                    f"{k['neither_a']:>5} {k['neither_b']:>5} {k['paired']:>4} {k['errors']:>3}")
    o = s["overall"]

    def f(x: float | None) -> str:
        return "n/a" if x is None else f"{x:.1f}%"
    rows += ["", f"overall over {o['paired']} paired trials of {o['probes']} probes (errors: {o['errors']}, "
                 "excluded):",
             f"  correct: A {f(o['pct_correct_a'])}   B {f(o['pct_correct_b'])}",
             f"  wrong:   A {f(o['pct_wrong_a'])}   B {f(o['pct_wrong_b'])}",
             f"  neither: A {f(o['pct_neither_a'])}   B {f(o['pct_neither_b'])}",
             f"  grader quotes not found verbatim in the answer: {o['quotes_not_found']}",
             _cost_line(s)]
    return "\n".join(rows)


# --------------------------------------------------------------------------- main

def _case_tasks(files: list[EvalFile], args: argparse.Namespace) -> tuple[list[Task], list[dict]]:
    tasks: list[Task] = []
    recs: list[dict] = []
    for ef in files:
        if ef.errors:
            raise LiftError(f"{ef.path.name}: {'; '.join(ef.errors)}")
        package = skill_package_text(skill_dir(ef, args.repo_root))
        skill = ef.metadata.get("Skill under test", "").strip().strip("`")
        skill = Path(skill).parent.name if skill.endswith("SKILL.md") else skill
        for case in ef.cases:
            cid = f"{ef.path.stem}__case{case_number(case.name)}"
            st = strip_conventions(case.text) if args.convention_free else Stripped(case.text)
            gtext = st.text
            items = rubric_items(gtext)
            tasks.append(Task(
                cid, skill, build_answer_prompts(case_question(case.text), package),
                lambda ans, gtext=gtext, items=items: build_grader_prompt(gtext, ans, items, args.convention_free),
                lambda text, ans: parse_grade(text), {}))
            recs.append({"id": cid, "skill": skill, "file": ef.path.name, "case": case.name,
                         "stripped": {"repo": st.repo, "names": st.names, "citation": st.citation,
                                      "total": st.stripped}})
    return tasks, recs


def _probe_tasks(probes: list[dict], args: argparse.Namespace) -> tuple[list[Task], list[dict]]:
    tasks: list[Task] = []
    recs: list[dict] = []
    for p in probes:
        package = probe_package(p, args.repo_root)
        tasks.append(Task(
            p["id"], p["skill"], build_answer_prompts(p["question"].strip(), package),
            lambda ans, p=p: build_probe_grader_prompt(p, ans), parse_probe_grade, {}))
        recs.append({"id": p["id"], "skill": p["skill"], "source": p["source"]})
    return tasks, recs


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Knowledge-lift test over the golden evals and wrong-fact probes.")
    ap.add_argument("--file", type=Path, help="Run one eval file (default: all of evals/golden/).")
    ap.add_argument("--probes", nargs="?", const=DEFAULT_PROBES, default=None, type=Path,
                    help="Run the wrong-fact probes (default file: evals/probes/wrong-fact-probes.json) "
                         "instead of the golden cases.")
    ap.add_argument("--convention-free", action="store_true",
                    help="Golden cases: strip repo-convention rubric/MUST lines and the citation item "
                         "before grading.")
    ap.add_argument("--repeats", type=int, default=1, help="Fresh answers per arm per case (default 1).")
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT, help="Output/cache directory.")
    ap.add_argument("--answer-model", default="sonnet")
    ap.add_argument("--grader-model", default="opus")
    ap.add_argument("--dry-run", action="store_true",
                    help="Write the prompts to --out/prompts without calling claude.")
    ap.add_argument("--jobs", type=int, default=1, help="Concurrent task/arm workers (default 1).")
    ap.add_argument("--claude-bin", default="claude")
    ap.add_argument("--repo-root", type=Path, default=REPO_ROOT, help=argparse.SUPPRESS)
    args = ap.parse_args(argv)
    if args.repeats < 1:
        print("[ERROR] --repeats must be >= 1", file=sys.stderr)
        return 3
    if args.probes and args.convention_free:
        print("[ERROR] --convention-free applies to the golden cases; probes are already convention-free",
              file=sys.stderr)
        return 3

    out: Path = args.out
    for sub in ("prompts", "answers", "grades", "cwd"):
        (out / sub).mkdir(parents=True, exist_ok=True)

    try:
        if args.probes:
            tasks, order = _probe_tasks(load_probes(args.probes), args)
        else:
            tasks, order = _case_tasks(
                [parse_eval_file(p) for p in iter_eval_files(args.file.resolve() if args.file else None)], args)
    except LiftError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 3

    for t in tasks:
        (out / "prompts" / f"{t.tid}.grader.txt").write_text(t.make_grader("[CANDIDATE ANSWER GOES HERE]"),
                                                            encoding="utf-8")
        for arm in ARMS:
            (out / "prompts" / f"{t.tid}.{arm}.txt").write_text(t.prompts[arm], encoding="utf-8")

    if args.dry_run:
        extra = ""
        if args.convention_free and not args.probes:
            extra = (f"; convention-free: stripped {sum(r['stripped']['total'] for r in order)} lines "
                     f"across {len(order)} cases (" + ", ".join(
                         f"{r['id']}={r['stripped']['total']}" for r in order if r['stripped']['total']) + ")")
        print(f"dry run: wrote {len(tasks) * len(ARMS)} answer prompts + {len(tasks)} grader templates to "
              f"{out / 'prompts'} ({args.repeats} repeat(s) would run){extra}")
        return 0

    t0 = time.monotonic()
    cwd = out / "cwd"
    by_id = {r["id"]: r for r in order}
    runs_key = "runs" if args.probes else "repeats"
    for r in order:
        r[runs_key] = [{} for _ in range(args.repeats)]
    with ThreadPoolExecutor(max_workers=max(1, args.jobs)) as pool:
        futs = {(t.tid, rep, arm): pool.submit(run_arm, t, rep, arm, out, args, cwd)
                for t in tasks for rep in range(args.repeats) for arm in ARMS}
        for (tid, rep, arm), f in futs.items():
            rec = f.result()
            by_id[tid][runs_key][rep][arm] = rec
            tag = rec["answer_error"] or rec["grade_error"]
            print(f"[{'ERR' if tag else 'ok '}] {tid} r{rep} arm {arm}" + (f": {tag}" if tag else ""), flush=True)
    elapsed = time.monotonic() - t0

    if args.probes:
        summary = summarize_probes(order)
        summary["elapsed_s"] = elapsed
        (out / "probe-results.json").write_text(json.dumps(
            {"answer_model": args.answer_model, "grader_model": args.grader_model, "repeats": args.repeats,
             "probes": order, "summary": summary}, indent=2))
        print()
        print(format_probe_summary(summary))
        print(f"elapsed wall time: {elapsed:.0f}s   results: {out / 'probe-results.json'}")
        return 2 if summary["overall"]["errors"] else 0

    for r in order:
        r["arms"] = r["repeats"][0]
    summary = summarize(order)
    summary["elapsed_s"] = elapsed
    summary["stripped_lines"] = sum(r["stripped"]["total"] for r in order)
    (out / "results.json").write_text(json.dumps(
        {"answer_model": args.answer_model, "grader_model": args.grader_model,
         "convention_free": args.convention_free, "repeats": args.repeats,
         "cases": order, "summary": summary}, indent=2))
    print()
    print(format_summary(summary))
    if args.convention_free:
        print(f"convention-free: stripped {summary['stripped_lines']} lines across {len(order)} cases")
    print(f"elapsed wall time: {elapsed:.0f}s   results: {out / 'results.json'}")
    return 2 if summary["overall"]["errors"] else 0


if __name__ == "__main__":
    sys.exit(main())
