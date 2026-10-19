#!/usr/bin/env python3
"""Deterministic CLI over RELEASES.yaml: what to do next, slot an ask, record status, measure.

The header comment of RELEASES.yaml defines sizes, slotting and job types; this
script implements those rules and nothing else. Writes keep the header comment
block (everything before the first top-level key) verbatim.

    python3 scripts/release_plan.py status
    python3 scripts/release_plan.py next --batch 10 [--json]
    python3 scripts/release_plan.py set-status R1-07 done --evidence "sha abc" --done-skills data/foo,data/bar
    python3 scripts/release_plan.py add "ask text" --size M
    python3 scripts/release_plan.py measure
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import date, timedelta
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from score_skill_depth import SIGNALS, score_skill  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
BAR = 10
HEADING = "## Questions to Ask Before Configuring"
OPEN = ("todo", "running")


def load(path: Path) -> tuple[str, dict]:
    text = path.read_text(encoding="utf-8")
    m = re.search(r"^[A-Za-z_]", text, re.M)
    return text[: m.start()] if m else "", yaml.safe_load(text)


def save(path: Path, header: str, data: dict) -> None:
    body = yaml.dump(data, sort_keys=False, default_flow_style=False, width=120, allow_unicode=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(header + body, encoding="utf-8")
    os.replace(tmp, path)


def current_index(data: dict) -> int | None:
    for i, rel in enumerate(data["releases"]):
        if any(it["status"] not in ("done", "dropped") for it in rel["items"]):
            return i
    return None


def to_date(s: str | None) -> date:
    return date.fromisoformat(s) if s else date.today()


def actionable(rel: dict, today: date) -> dict | None:
    for it in rel["items"]:
        if it["status"] != "todo":
            continue
        if today > rel["freeze"] and not (
            it["title"].startswith("Release") or "gate fix" in str(it.get("notes", "")).lower()
        ):
            continue
        return it
    return None


def skill_dirs(skills: Path, domains: list[str] | None) -> list[Path]:
    doms = domains or sorted(p.name for p in skills.iterdir() if p.is_dir())
    return sorted(d for dom in doms for d in (skills / dom).glob("*/") if (d / "SKILL.md").is_file())


def work_list(item: dict, skills: Path) -> list[dict]:
    done = set(item.get("done_skills") or [])
    rows = []
    for d in skill_dirs(skills, item.get("domains")):
        name = f"{d.parent.name}/{d.name}"
        if name in done:
            continue
        s = score_skill(d)
        if item["title"].startswith("Top-up"):
            if s["score"] >= BAR and HEADING not in (d / "SKILL.md").read_text(encoding="utf-8").splitlines():
                rows.append({"skill": name, "score": s["score"], "missing": ["questions_table"]})
        else:
            rows.append({"skill": name, "score": s["score"], "missing": [k for k in SIGNALS if not s.get(k)]})
    return sorted(rows, key=lambda r: (r["score"], r["skill"]))


def cmd_status(args) -> int:
    header, data = load(Path(args.plan))
    i = current_index(data)
    if i is None:
        print("all releases done")
        return 0
    rel = data["releases"][i]
    left = (rel["freeze"] - to_date(args.today)).days
    print(f"release {rel['version']} (mcp {rel['mcp_version']})  ships {rel['ships']}  freeze {rel['freeze']}  {left} days to freeze")
    for it in rel["items"]:
        print(f"{it['id']}  {it['status']:<8} {it['size']}  {it['owner_model']:<6} {it['title'][:80]}")
    return 0


def cmd_next(args) -> int:
    header, data = load(Path(args.plan))
    i = current_index(data)
    item = actionable(data["releases"][i], to_date(args.today)) if i is not None else None
    if item is None:
        print("nothing actionable")
        return 2
    work = work_list(item, Path(args.skills))[: args.batch] if "target" in item else []
    if args.json:
        print(json.dumps({"release": data["releases"][i]["version"], "item": item, "work": work}, default=str, indent=2))
        return 0
    print(f"{item['id']}  {item['size']}  {item['owner_model']}  {item['title']}")
    if item.get("notes"):
        print(f"notes: {item['notes']}")
    if "target" in item:
        print(f"target {item['target']} floor {item.get('floor', '-')}; batch of {len(work)}:")
        for w in work:
            print(f"  {w['score']:>2}  {w['skill']}  missing: {', '.join(w['missing']) or '-'}")
    return 0


def cmd_set_status(args) -> int:
    path = Path(args.plan)
    header, data = load(path)
    item = next((it for r in data["releases"] for it in r["items"] if it["id"] == args.id), None)
    if item is None:
        print(f"no item {args.id}", file=sys.stderr)
        return 1
    if args.status == "done" and not (args.evidence or "").strip():
        print("done requires --evidence", file=sys.stderr)
        return 1
    item["status"] = args.status
    if args.evidence:
        item["evidence"] = args.evidence
    if args.done_skills:
        have = item.setdefault("done_skills", [])
        have.extend(s for s in args.done_skills.split(",") if s and s not in have)
    save(path, header, data)
    print(f"{args.id} -> {args.status}")
    return 0


def cmd_add(args) -> int:
    path = Path(args.plan)
    header, data = load(path)
    today = to_date(args.today)
    cur = current_index(data)
    if cur is None:
        print("no open release to slot into", file=sys.stderr)
        return 1
    rel = data["releases"][cur]
    open_ml = sum(1 for it in rel["items"] if it["size"] in ("M", "L") and it["status"] in OPEN)
    in_current = (
        (args.size == "S" and today < rel["freeze"])
        or (args.size == "M" and (rel["freeze"] - today) >= timedelta(days=5) and open_ml < 3)
    )
    idx = cur if in_current else cur + 1
    if idx >= len(data["releases"]):
        print(f"no release after {rel['version']} to slot a {args.size} ask into", file=sys.stderr)
        return 1
    target = data["releases"][idx]
    prefix = f"R{idx + 1}"
    if target["items"]:
        prefix = target["items"][0]["id"].rsplit("-", 1)[0]
    n = max([int(it["id"].rsplit("-", 1)[1]) for it in target["items"] if it["id"].startswith(prefix + "-")] + [0]) + 1
    title = args.title or args.ask
    if args.size == "L":
        title = "[split before scheduling] " + title
    item = {
        "id": f"{prefix}-{n:02d}",
        "title": title,
        "size": args.size,
        "owner_model": args.owner_model or ("sonnet" if args.size == "S" else "opus"),
        "status": "todo",
    }
    target["items"].append(item)
    data["inbox"] = (data.get("inbox") or []) + [
        {"date": today, "ask": args.ask, "size": args.size, "slotted_into": target["version"]}
    ]
    save(path, header, data)
    print(f"{item['id']} -> release {target['version']}")
    return 0


def cmd_measure(args) -> int:
    path = Path(args.plan)
    header, data = load(path)
    rels = data["releases"]
    if args.release:
        rel = next((r for r in rels if str(r["version"]) == args.release), None)
    else:
        i = current_index(data)
        rel = rels[i] if i is not None else None
    if rel is None:
        print("no such release", file=sys.stderr)
        return 1
    skills = Path(args.skills)
    dirs = skill_dirs(skills, None)
    m = dict(skills=len(dirs), at_bar=0, questions_tables=0, unverified_markers=0, default_version_skills=0)
    for d in dirs:
        text = (d / "SKILL.md").read_text(encoding="utf-8")
        m["at_bar"] += score_skill(d)["score"] >= BAR
        m["questions_tables"] += HEADING in text.splitlines()
        m["default_version_skills"] += bool(re.search(r"""^salesforce-version:\s*["']Spring '25\+["']\s*$""", text, re.M))
        m["unverified_markers"] += text.count("UNVERIFIED") + sum(
            p.read_text(encoding="utf-8", errors="replace").count("UNVERIFIED") for p in (d / "references").glob("*.md")
        )
    m["measured_on"] = to_date(args.today)
    rel["measured"] = m
    save(path, header, data)
    for k, v in m.items():
        print(f"{k}: {v}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="release_plan.py", description="Read and advance RELEASES.yaml.")
    sub = parser.add_subparsers(dest="cmd", required=True)
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--plan", default=str(ROOT / "RELEASES.yaml"), help="path to RELEASES.yaml")
    common.add_argument("--skills", default=str(ROOT / "skills"), help="skills directory")
    common.add_argument("--today", help="YYYY-MM-DD (default: today)")

    p = sub.add_parser("status", parents=[common], help="current release and its items")
    p.set_defaults(func=cmd_status)

    p = sub.add_parser("next", parents=[common], help="next actionable item + skill work list")
    p.add_argument("--batch", type=int, default=10, help="skills to list (default 10)")
    p.add_argument("--json", action="store_true", help="print JSON")
    p.set_defaults(func=cmd_next)

    p = sub.add_parser("set-status", parents=[common], help="move one item")
    p.add_argument("id", metavar="ID")
    p.add_argument("status", choices=["todo", "running", "done", "dropped"])
    p.add_argument("--evidence", help="required for done")
    p.add_argument("--done-skills", help="comma-separated domain/slug to append to done_skills")
    p.set_defaults(func=cmd_set_status)

    p = sub.add_parser("add", parents=[common], help="inbox an ask and slot it by size")
    p.add_argument("ask", metavar="ASK")
    p.add_argument("--size", required=True, choices=["S", "M", "L"])
    p.add_argument("--title")
    p.add_argument("--owner-model", choices=["opus", "sonnet", "fable"])
    p.set_defaults(func=cmd_add)

    p = sub.add_parser("measure", parents=[common], help="write the baseline KPIs into a release's measured map")
    p.add_argument("--release", help="release version (default: current)")
    p.set_defaults(func=cmd_measure)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
