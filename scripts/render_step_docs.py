"""render_step_docs.py — deterministic documentation pass for one tested build step.

The renderer half of the build-doc-keeper: everything derivable from the builder's envelope and tests/<step>/results.json is written by this script (workbook rows per artefact, one traceability row, open items carried to decisions.md, the envelope pair, set-status, render); the judgement half (D- entries) is passed in as a markdown file the operator or a model wrote. Born from northwind-sales M3-S01/M3-S02 (2026-09-19), where a per-step doc-keeper agent cost ~200k-400k tokens for rows this script produces in seconds.
Usage: python3 doc_step.py <STEP> --req <REQ-id> --source "Qx, Ay" --requirement "<one sentence>" --workbook <file> --row-prefix CWB-XXX --row-start N [--extra-decisions <md file>]
Deterministic parts: workbook rows per artefact (from the builder envelope's extensions.artefacts and checker_results), one traceability row, O- entries from the builder's open items (either envelope shape), envelope pair, set-status, render. D- entries are the operator's (pass a markdown file)."""
import json, pathlib, datetime, subprocess, sys, argparse, re
a = argparse.ArgumentParser(); a.add_argument("step"); a.add_argument("--build-dir", required=True); a.add_argument("--repo-root", default="."); a.add_argument("--owner", default="Build owner (role; the plan names no individual)"); a.add_argument("--req", required=True); a.add_argument("--source", required=True); a.add_argument("--requirement", required=True)
a.add_argument("--workbook", required=True); a.add_argument("--row-prefix", required=True); a.add_argument("--row-start", type=int, required=True); a.add_argument("--extra-decisions"); a.add_argument("--skills", default="")
a.add_argument("--backfill", action="store_true", help="the step's REQ row already exists (a re-documentation or a pass whose rows were missed): write workbook rows, decisions and the envelope; skip the traceability row; flip tested -> documented only if the step is tested")
args = a.parse_args()
B = pathlib.Path(args.build_dir); R = pathlib.Path(args.repo_root); HERE = pathlib.Path(__file__).resolve().parent; step_id = args.step; sid = step_id.replace("-", "")
plan = json.loads((B/"plan.json").read_text()); step = next(s for s in plan["steps"] if s["id"]==step_id)
build_id = plan.get("build_id") or plan.get("id") or B.name
assert step["status"] in (("tested", "documented") if args.backfill else ("tested",)), step["status"]
res = json.loads((B/f"tests/{step_id}/results.json").read_text()); assert res.get("passed") is True
envs = sorted((B/f"envelopes/{step_id}").glob("*.json"))
builder = None; open_items = []; seen = set()
builders = [(p, json.loads(p.read_text())) for p in envs]
builders = [(p, e) for p, e in builders if e.get("agent") in ("metadata-builder","apex-builder","lwc-builder","build-step-runner", step.get("agent")) and not (e.get("agent") == "build-doc-keeper" and "render_step_docs" in (e.get("summary") or ""))]  # the step's own agent is its builder (a docs step is built by build-doc-keeper); never this script's own envelopes
assert builders, "no builder envelope"
bpath, builder = builders[-1]
for p, e in builders:  # merge open items across every build/repair pass, oldest first, dedupe by id or text
    x = e.get("extensions", {})
    for item in (x.get("open_items") or x.get("open_items_for_the_human") or []):
        key = item.get("id") if isinstance(item, dict) and item.get("id") else str(item)[:120]
        if key in seen: continue
        seen.add(key); open_items.append(item)
ext = builder.get("extensions", {})
# apex-builder and lwc-builder envelopes list artefacts under other keys (or not at all); the plan's declared
# outputs are the contract either way, so fall back to them (northwind M3-S03 got 0 rows without this).
artefacts = ext.get("artefacts") or [o if isinstance(o, str) else o.get("path") for o in (step.get("outputs") or [])]
# Verification text comes from the TESTER's record (results.json), which is the run that set `tested`;
# the builder envelope's checker_results vary in shape across agents and narrated "exit ?" / stale exits
# on northwind M2-S02 and M3-S03 (driver's log friction 66).
checker_lines = []
for x in (res.get("tests") or res.get("results") or []):
    if isinstance(x, dict) and x.get("type") == "checker":
        cmd = (x.get("command") or x.get("name") or x.get("id") or "checker")[:80]
        ex = x.get("exit_code", x.get("exit"))
        checker_lines.append(f"`{cmd}` exit {ex}" if ex is not None else f"`{cmd}` {x.get('verdict') or x.get('status') or 'pass'}")
verified = "; ".join(checker_lines) or f"declared tests per tests/{step_id}/results.json (passed: true)"
now = datetime.datetime.now(datetime.timezone.utc); run_id = now.strftime("%Y-%m-%dT%H-%M-%SZ"); today = now.strftime("%Y-%m-%d")
# ---- decisions.md: O- entries (append-only), plus operator D- entries from file
dec = ((B/"decisions.md").read_text() if (B/"decisions.md").exists() else "# Decisions\n"); add = ""
if args.extra_decisions: add += "\n\n" + pathlib.Path(args.extra_decisions).read_text().strip()
existing = set(re.findall(rf"^## (O-{sid}-\d+)", dec + add, flags=re.M)); n = max([0] + [int(x.rsplit("-", 1)[1]) for x in existing])  # number past every id already on file, including the operator's extra entries
for item in open_items:
    n += 1; oid = f"O-{sid}-{n:02d}"
    if isinstance(item, dict):
        oid = item.get("id") or oid; topic = item.get("topic") or item.get("title") or oid; body = item.get("what_to_do") or item.get("detail") or json.dumps(item)
    else:
        topic = str(item)[:110].rstrip(" .") ; body = str(item)
    if oid in existing: continue
    add += f"\n\n## {oid} — {topic}\n\n- **Date:** {today} · **Recorded by:** dry-run operator (Fable), from the builder's envelope (`{bpath.relative_to(B)}`)\n- {body}\n"
(B/"decisions.md").write_text(dec.rstrip("\n") + add + "\n")
# ---- workbook rows, one per artefact
(B/"workbook").mkdir(exist_ok=True); wb = (B/"workbook"/args.workbook); w = wb.read_text() if wb.exists() else f"## {args.workbook.split('-',1)[1].rsplit('.',1)[0].replace('-',' ').capitalize()}\n\n| row_id | target_value | owner | source_req_id | source_story_id | recommended_agent | recommended_skills | status | notes |\n|---|---|---|---|---|---|---|---|---|\n"
owner = args.owner; skills = args.skills or "; ".join(step.get("skills") or [])
rows = []; k = args.row_start
for art in artefacts:
    rid = f"{args.row_prefix}-{k:03d}"; assert rid not in w, rid; k += 1
    kind = "manifest" if art.endswith("package.xml") else ("deploy notes" if art.endswith("deploy-order.md") else "component")
    notes = ("Deploy position: not a component. Verified by: `manifest` two-way and `xml` parse." if kind=="manifest" else
             "Deploy position: not a component. Verified by: `check-outputs` ok (declared in `outputs[]`, present, non-empty)." if kind=="deploy notes" else
             f"Verified by: {verified}; `manifest`; `xml`. Open items: see `decisions.md` O-{sid}-*. Manual tests outstanding at the milestone gate: `tests/{step_id}/results.json` → `skipped_manual`.")
    rows.append(f"| {rid} | `{art}` | {owner} | {args.req} | none (no story-drafter step in this build) | {builder.get('agent')} | {skills} | executed | {notes} |")
wb.write_text(w.rstrip("\n") + "\n" + "\n".join(rows) + "\n")
# ---- traceability row
tr = (B/"traceability.md"); t = tr.read_text() if tr.exists() else "# Traceability\n\n| req_id | source | requirement | step_id | artefact | agent | decision_ref | test_id | test_type | status | artefact_paths | test_result |\n|---|---|---|---|---|---|---|---|---|---|---|---|\n| REQ-000 | - | (header row placeholder) | - | - | - | - | - | - | - | - | - |"
if args.backfill and f"| {args.req} " in t:
    write_req_row = False
else:
    assert f"| {args.req} " not in t, f"{args.req} already in traceability.md — pass --backfill for a re-documentation"
    write_req_row = True
tests = res.get("tests") or res.get("results") or []
tid = next((x.get("id") or x.get("test_id") for x in tests if isinstance(x,dict) and x.get("type")=="checker"), f"{step_id}-T1")
line = (f"| {args.req} | {args.source} | {args.requirement} | {step_id} | " + "; ".join(f"`{a}`" for a in artefacts if not a.endswith(('package.xml','deploy-order.md'))) +
        f" | {builder.get('agent')} | see decisions.md D-{sid}-* | {tid} | checker | In UAT | `artefacts/{step_id}/` | pass — {verified}; `manifest`; `xml`. Open items O-{sid}-01..{n:02d} in `decisions.md`; manual tests outstanding at the milestone gate (`tests/{step_id}/results.json` → `skipped_manual`). |")
if write_req_row:
    lines = t.split("\n"); last = max(i for i,l in enumerate(lines) if l.startswith("| REQ-0")); lines.insert(last+1, line); tr.write_text("\n".join(lines))
# ---- envelope pair, built from scratch on the output-envelope schema
summary = ((f"Backfilled {step_id} by render_step_docs.py:" if args.backfill else f"Documented {step_id} by render_step_docs.py:") + f" {len(rows)} workbook rows in {args.workbook}, {args.req} minted, {n - len(existing)} open items carried from the builder envelope(s) to decisions.md" + (", operator D- entries appended" if args.extra_decisions else "") + f". " + ("Set " + step_id + " tested -> documented." if step["status"] == "tested" else "Status unchanged (already documented)."))
rel = lambda p: str(p) if not str(p).startswith(str(R)) else str(pathlib.Path(p).relative_to(R))
env = {
  "agent": "build-doc-keeper", "mode": "single", "run_id": run_id,
  "report_path": f".sfskills/builds/{build_id}/envelopes/{step_id}/{run_id}.md", "envelope_path": f".sfskills/builds/{build_id}/envelopes/{step_id}/{run_id}.json",
  "inputs_received": {"build_dir": str(B), "step_id": step_id, "builder_envelope": str(bpath.relative_to(B)), "results": f"tests/{step_id}/results.json", "renderer": "scripts/render_step_docs.py"},
  "summary": summary, "confidence": "MEDIUM",
  "confidence_rationale": "Rows are derived, not narrated: every workbook row carries a real source_req_id and the verification the tester recorded; the traceability row joins artefact to test result. MEDIUM because the requirement sentence and any D- entries came from the operator, not from a re-read of the clarifications.",
  "outcome": "completed", "dimensions_compared": ["decisions-appended", "workbook-rows-written", "traceability-row-written"], "dimensions_skipped": [],
  "process_observations": [{"category": "healthy", "severity": 'info', "domain": '', "observation": f"Renderer pass for {step_id}: deterministic rows from the builder envelope and results.json.", "evidence": {"source": "envelope", "path": str(bpath.relative_to(B))}, "suggested_followup_agent": "step-tester", "followup_reason": "the next step in the chain, once built"}],
  "citations": [{"type": "agent", "id": "build-doc-keeper", "path": "agents/build-doc-keeper/AGENT.md", "used_for": "the row schema, the append-only decisions rule, the traceability column set and the status transition this renderer reproduces"}],
  "extensions": {"step_id": step_id, "rows": [r.split("|")[1].strip() for r in rows], "req": args.req, "open_items_carried": n - len(existing)}, "followups": [{"agent": "step-tester", "because": "the next step in the chain, once built"}],
}
(B/f"envelopes/{step_id}/{run_id}.json").write_text(json.dumps(env, indent=2, ensure_ascii=False)+"\n")
(B/f"envelopes/{step_id}/{run_id}.md").write_text(f"# build-doc-keeper (render_step_docs.py) — {step_id} — {run_id}\n\n{summary}\n")
r = subprocess.run([sys.executable, str(HERE/"validate_envelope.py"), f"{B}/envelopes/{step_id}/{run_id}.json"], capture_output=True, text=True); print(r.stdout.strip() or r.stderr.strip())
if r.returncode != 0:
    print(f"refusing to set {step_id} documented: the renderer's own envelope failed validation (rows and decisions were written; fix the envelope and run set-status by hand)", file=sys.stderr); sys.exit(1)
if step["status"] != "tested":
    print(f"{step_id} is already documented — rows/decisions/envelope written, no status change (backfill)"); sys.exit(0)
r = subprocess.run([sys.executable, str(HERE/"build_plan.py"), "set-status", str(B/"plan.json"), step_id, "documented", "--run-agent", "build-doc-keeper", "--envelope", f"envelopes/{step_id}/{run_id}.json", "--result", summary[:200], "--repo-root", str(R)], capture_output=True, text=True)
print([l for l in (r.stdout+r.stderr).splitlines() if not l.startswith("WARN")][-1:])
subprocess.run([sys.executable, str(HERE/"build_plan.py"), "render", str(B/"plan.json"), "--repo-root", str(R)], capture_output=True, text=True)
