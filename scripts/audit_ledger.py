#!/usr/bin/env python3
"""Append-only ledger of skill-audit batches and the one number that shows learning.

Each writer + adversarial-reviewer batch appends ONE line to
evals/measurement/audit-ledger.jsonl. The learning KPI is
``writer_defects / skills`` — how many defects the reviewer had to fix per
skill. If the Learned rules in standards/skill-writer-brief.md are being
read, that number falls batch over batch; if it does not fall over five
batches, the rules are not reaching writers and the orchestrator escalates.

Usage
  python3 scripts/audit_ledger.py add --item R3-06 --batch 1 --writer opus \\
      --reviewer opus --skills 9 --grounded 124 --contradicted 4 --not-found 86 \\
      --writer-defects 58 --defect-classes "over-marked-unverified=42,cite=9,checker-demoted=6,marker-placement=1" \\
      --learned-rules-added 5 --commit 743e6331e
  python3 scripts/audit_ledger.py report            # table + trend verdict
  python3 scripts/audit_ledger.py report --json     # machine-readable summary

Stdlib only. Lines are never edited; a correction is a new line with
``--supersedes <batch>``.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
LEDGER = REPO / "evals" / "measurement" / "audit-ledger.jsonl"
TREND_WINDOW = 5  # batches over which the KPI must fall


def load(path: Path | None = None) -> list[dict]:
    path = LEDGER if path is None else path  # resolved at call time so tests can repoint LEDGER
    if not path.exists():
        return []
    rows = []
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as exc:  # pragma: no cover - guard
            raise SystemExit(f"ERROR {path}:{n}: not JSON ({exc})")
    # a superseding line replaces the earlier batch of the same item
    by_key: dict[tuple[str, int], dict] = {}
    for r in rows:
        key = (r["item"], int(r.get("supersedes") or r["batch"]))
        by_key[key] = r
    return [by_key[k] for k in sorted(by_key, key=lambda k: (k[0], k[1]))]


def parse_classes(text: str) -> dict[str, int]:
    out: dict[str, int] = {}
    for part in filter(None, (p.strip() for p in text.split(","))):
        if "=" not in part:
            raise SystemExit(f"ERROR defect class '{part}' must be name=count")
        name, count = part.rsplit("=", 1)
        out[name.strip()] = int(count)
    return out


def cmd_add(args: argparse.Namespace) -> int:
    classes = parse_classes(args.defect_classes or "")
    if classes and sum(classes.values()) != args.writer_defects:
        raise SystemExit(
            f"ERROR defect classes sum to {sum(classes.values())}, not --writer-defects {args.writer_defects}"
        )
    row = {
        "date": args.date or date.today().isoformat(),
        "item": args.item,
        "batch": args.batch,
        "writer_model": args.writer,
        "reviewer_model": args.reviewer,
        "skills": args.skills,
        "claims": {"grounded": args.grounded, "contradicted": args.contradicted, "not_found": args.not_found},
        "writer_defects": args.writer_defects,
        "defect_classes": classes,
        "learned_rules_added": args.learned_rules_added,
        "commit": args.commit,
    }
    if args.probe_result:
        row["probe_result"] = args.probe_result
    if args.supersedes is not None:
        row["supersedes"] = args.supersedes
    if args.note:
        row["note"] = args.note
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    with LEDGER.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    kpi = row["writer_defects"] / max(1, row["skills"])
    print(f"{row['item']} batch {row['batch']}: {row['skills']} skills, {row['writer_defects']} writer defects -> {kpi:.2f} per skill")
    return 0


def summarize(rows: list[dict]) -> dict:
    per = []
    for r in rows:
        per.append(
            {
                "item": r["item"],
                "batch": r["batch"],
                "writer": r["writer_model"],
                "skills": r["skills"],
                "contradicted": r["claims"]["contradicted"],
                "writer_defects": r["writer_defects"],
                "defects_per_skill": round(r["writer_defects"] / max(1, r["skills"]), 2),
                "learned_rules_added": r.get("learned_rules_added", 0),
                "probe_result": r.get("probe_result"),
            }
        )
    audited = sum(p["skills"] for p in per)
    kpis = [p["defects_per_skill"] for p in per]
    verdict = "insufficient data (need 2+ batches)"
    if len(kpis) >= 2:
        window = kpis[-TREND_WINDOW:]
        if window[-1] < window[0]:
            verdict = f"falling: {window[0]} -> {window[-1]} over last {len(window)} batches"
        elif len(kpis) >= TREND_WINDOW:
            verdict = f"NOT FALLING over {TREND_WINDOW} batches ({window[0]} -> {window[-1]}): learned rules are not reaching writers — escalate"
        else:
            verdict = f"not yet falling ({window[0]} -> {window[-1]}); {TREND_WINDOW - len(kpis)} more batch(es) before it counts"
    by_writer: dict[str, list[float]] = {}
    for p in per:
        by_writer.setdefault(p["writer"], []).append(p["defects_per_skill"])
    return {
        "batches": per,
        "skills_audited": audited,
        "contradicted_claims_fixed": sum(p["contradicted"] for p in per),
        "defects_per_skill_by_writer": {w: round(sum(v) / len(v), 2) for w, v in by_writer.items()},
        "trend": verdict,
    }


def cmd_report(args: argparse.Namespace) -> int:
    rows = load()
    if not rows:
        print("ledger empty:", LEDGER)
        return 0
    s = summarize(rows)
    if args.json:
        print(json.dumps(s, indent=2))
        return 0
    print(f"{'item':7} {'b':>2} {'writer':7} {'skills':>6} {'contra':>6} {'defects':>7} {'per skill':>9} {'rules+':>6}  probe")
    for p in s["batches"]:
        print(
            f"{p['item']:7} {p['batch']:>2} {p['writer']:7} {p['skills']:>6} {p['contradicted']:>6} "
            f"{p['writer_defects']:>7} {p['defects_per_skill']:>9} {p['learned_rules_added']:>6}  {p['probe_result'] or '-'}"
        )
    print()
    print(f"skills audited: {s['skills_audited']}   contradicted claims fixed: {s['contradicted_claims_fixed']}")
    print(f"defects per skill by writer model: {s['defects_per_skill_by_writer']}")
    print(f"learning trend: {s['trend']}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("add", help="append one batch line")
    a.add_argument("--item", required=True)
    a.add_argument("--batch", type=int, required=True)
    a.add_argument("--writer", required=True, choices=["opus", "sonnet", "haiku", "fable"])
    a.add_argument("--reviewer", required=True, choices=["opus", "sonnet", "fable"])
    a.add_argument("--skills", type=int, required=True)
    a.add_argument("--grounded", type=int, required=True)
    a.add_argument("--contradicted", type=int, required=True)
    a.add_argument("--not-found", type=int, required=True)
    a.add_argument("--writer-defects", type=int, required=True, help="defects the reviewer found in the writer's work")
    a.add_argument("--defect-classes", default="", help="name=count,name=count (must sum to --writer-defects)")
    a.add_argument("--learned-rules-added", type=int, default=0)
    a.add_argument("--commit", required=True)
    a.add_argument("--probe-result", default="", help="e.g. 'A 2/6 B 6/6' from run_lift on this batch's probes")
    a.add_argument("--supersedes", type=int, default=None)
    a.add_argument("--note", default="")
    a.add_argument("--date", default="")
    a.set_defaults(func=cmd_add)
    r = sub.add_parser("report", help="table, by-writer averages, trend verdict")
    r.add_argument("--json", action="store_true")
    r.set_defaults(func=cmd_report)
    args = ap.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
