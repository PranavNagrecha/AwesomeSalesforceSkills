#!/usr/bin/env python3
"""
upstream_radar.py — Weekly radar over forcedotcom/sf-skills.

WHAT THIS IS
    The deterministic half of the weekly upstream-sync job. It detects which
    skills in the upstream repo (forcedotcom/sf-skills) are NEW or CHANGED since
    our last run, and classifies each one against our local catalog as
    NET_NEW / ENRICH / COVERED. It emits a machine-readable gap report.

WHAT THIS IS NOT
    It does not copy, fetch, or store any upstream prose. forcedotcom/sf-skills
    currently publishes conflicting license signals (Apache-2.0 in the root
    license file and CC-BY-NC-4.0 in package metadata). Until upstream resolves
    that conflict, this tool treats it as CLEAN-ROOM discovery only: it learns
    *what topics exist* and hands that list to a human/agent who authors our own
    skill FROM OFFICIAL SALESFORCE DOCS. See memory: project-upstream-sf-skills-sync.

    The LLM authoring + draft-PR half lives in commands/sync-upstream-skills.md.

USAGE
    python3 scripts/upstream_radar.py --full            # audit ALL upstream skills + seed manifest
    python3 scripts/upstream_radar.py                   # weekly delta run (new/changed only)
    python3 scripts/upstream_radar.py --dry-run         # don't write the manifest
    python3 scripts/upstream_radar.py --json            # machine-readable output for the agent
    python3 scripts/upstream_radar.py --gate aggressive # widen auto-scaffold cut
    python3 scripts/upstream_radar.py --seed            # snapshot baseline only (no classify)

Requires `gh` (GitHub CLI) authenticated. stdlib-only otherwise.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
UPSTREAM = "forcedotcom/sf-skills"
UPSTREAM_LICENSE = (
    "CONFLICTING: LICENSE.txt declares Apache-2.0 while package metadata declares "
    "CC-BY-NC-4.0 — clean-room only; author from official Salesforce sources"
)
DEFAULT_MANIFEST = REPO_ROOT / "config" / "upstream-sources" / "sf-skills.manifest.json"
SKILL_PATH_RE = re.compile(r"^skills/([^/]+)/SKILL\.md$")

# Classification thresholds, tuned against observed search_knowledge.py skill-level
# scores (covered topics land 5-12; genuine gaps land <3). A radar proposes;
# the human/agent reviewing the draft PR disposes — so rough is fine.
COVERED_MIN = 5.0   # top local score >= this => we already cover it
ENRICH_MIN = 3.0    # in [ENRICH_MIN, COVERED_MIN) => partial coverage worth enriching
                    # below ENRICH_MIN => net-new gap

# Per-gate auto-scaffold cut (Balanced is the chosen default). A gap is
# auto-scaffolded if its top local score is below the cut.
GATE_CUT = {
    "conservative": ENRICH_MIN,  # 3.0 — only clear net-new
    "balanced": 4.5,             # net-new + lower-confidence enrich
    "aggressive": COVERED_MIN + 1.0,  # 6.0 — everything not clearly covered
}

# Verbs that start most upstream skill slugs; dropping them sharpens the
# topic query against our index (we index by Salesforce noun, not by "generating").
LEADING_VERBS = {
    "building", "generating", "creating", "deploying", "configuring",
    "implementing", "developing", "running", "using", "fetching",
    "switching", "handling", "querying", "observing", "testing",
    "analyzing", "modeling", "applying", "searching", "integrating",
    "connecting", "activating", "harmonizing", "orchestrating",
    "preparing", "retrieving", "segmenting", "getting", "uplifting",
}


def gh_json(api_path: str) -> object:
    """Call `gh api <path>` and return parsed JSON, with a clear error on failure."""
    result = subprocess.run(
        ["gh", "api", api_path],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"`gh api {api_path}` failed (is gh installed and authenticated?):\n"
            f"{result.stderr.strip()}"
        )
    return json.loads(result.stdout)


def fetch_upstream_skills(tag: str | None) -> tuple[str, dict[str, str]]:
    """Return (tag, {skill_name: SKILL.md blob sha}) for the upstream repo at a tag."""
    if tag is None:
        tag = gh_json(f"repos/{UPSTREAM}/releases/latest")["tag_name"]
    tree_sha = gh_json(f"repos/{UPSTREAM}/commits/{tag}")["commit"]["tree"]["sha"]
    tree = gh_json(f"repos/{UPSTREAM}/git/trees/{tree_sha}?recursive=1")
    if tree.get("truncated"):
        print(
            "WARNING: upstream tree was truncated by the GitHub API; "
            "skill list may be incomplete.",
            file=sys.stderr,
        )
    skills: dict[str, str] = {}
    for item in tree.get("tree", []):
        match = SKILL_PATH_RE.match(item.get("path", ""))
        if match:
            skills[match.group(1)] = item["sha"]
    return tag, skills


def slug_to_query(slug: str) -> str:
    """'building-ui-bundle-app' -> 'ui bundle app' (drop a leading verb)."""
    words = slug.split("-")
    if words and words[0] in LEADING_VERBS and len(words) > 1:
        words = words[1:]
    return " ".join(words)


def top_local_score(query: str) -> tuple[float | None, str | None, list[dict]]:
    """Run search_knowledge.py --json. Return (top skill score, top skill id, official_sources)."""
    result = subprocess.run(
        [sys.executable, "scripts/search_knowledge.py", "--json", query],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    if result.returncode != 0:
        # Don't let one bad query kill the whole run; treat as unknown coverage.
        print(f"WARNING: search failed for {query!r}: {result.stderr.strip()}", file=sys.stderr)
        return None, None, []
    data = json.loads(result.stdout)
    skills = data.get("skills") or []
    official = data.get("official_sources") or []
    if not skills:
        return None, None, official
    return skills[0].get("score"), skills[0].get("id"), official


def classify(score: float | None) -> str:
    if score is None or score < ENRICH_MIN:
        return "NET_NEW"
    if score < COVERED_MIN:
        return "ENRICH"
    return "COVERED"


def load_manifest(path: Path) -> dict:
    if path.exists():
        return json.loads(path.read_text())
    return {"upstream": UPSTREAM, "tag": None, "skills": {}}


def save_manifest(path: Path, tag: str, skills: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "upstream": UPSTREAM,
        "license": UPSTREAM_LICENSE,
        "tag": tag,
        "skills": dict(sorted(skills.items())),
    }
    path.write_text(json.dumps(payload, indent=2) + "\n")


def build_gap(slug: str, change: str) -> dict:
    query = slug_to_query(slug)
    score, top_id, official = top_local_score(query)
    classification = classify(score)
    return {
        "upstream_skill": slug,
        "change": change,
        "query": query,
        "top_local": top_id,
        "top_score": round(score, 3) if score is not None else None,
        "classification": classification,
        "upstream_url": f"https://github.com/{UPSTREAM}/tree/{{tag}}/skills/{slug}",
        "official_sources": official[:6],
    }


def run(args) -> dict:
    manifest_path = Path(args.manifest)
    manifest = load_manifest(manifest_path)
    prev_skills = manifest.get("skills", {})

    tag, current_skills = fetch_upstream_skills(args.tag)

    new = sorted(set(current_skills) - set(prev_skills))
    changed = sorted(
        s for s in current_skills
        if s in prev_skills and current_skills[s] != prev_skills[s]
    )
    removed = sorted(set(prev_skills) - set(current_skills))

    # --seed: just snapshot the baseline, no classification.
    if args.seed:
        if not args.dry_run:
            save_manifest(manifest_path, tag, current_skills)
        return {
            "mode": "seed",
            "upstream": UPSTREAM,
            "license": UPSTREAM_LICENSE,
            "tag": tag,
            "tracked_skills": len(current_skills),
            "manifest": str(manifest_path),
            "wrote_manifest": not args.dry_run,
        }

    # --full audits every upstream skill; default audits only the delta.
    if args.full:
        to_assess = [(s, "new" if s not in prev_skills else "tracked") for s in sorted(current_skills)]
    else:
        to_assess = [(s, "new") for s in new] + [(s, "changed") for s in changed]

    gaps = []
    for slug, change in to_assess:
        gap = build_gap(slug, change)
        gap["upstream_url"] = gap["upstream_url"].replace("{tag}", tag)
        gap["auto_scaffold"] = (
            gap["classification"] != "COVERED"
            and (gap["top_score"] is None or gap["top_score"] < GATE_CUT[args.gate])
        )
        gaps.append(gap)

    actionable = [g for g in gaps if g["classification"] != "COVERED"]
    report = {
        "mode": "full" if args.full else "delta",
        "upstream": UPSTREAM,
        "license": UPSTREAM_LICENSE,
        "tag": tag,
        "gate": args.gate,
        "counts": {
            "new": len(new),
            "changed": len(changed),
            "removed": len(removed),
            "net_new": sum(1 for g in gaps if g["classification"] == "NET_NEW"),
            "enrich": sum(1 for g in gaps if g["classification"] == "ENRICH"),
            "covered": sum(1 for g in gaps if g["classification"] == "COVERED"),
            "auto_scaffold": sum(1 for g in gaps if g["auto_scaffold"]),
        },
        "gaps": [g for g in gaps if g["classification"] != "COVERED"],
        "covered_skipped": [g["upstream_skill"] for g in gaps if g["classification"] == "COVERED"],
        "removed_upstream": removed,
        "manifest": str(manifest_path),
        "actionable_count": len(actionable),
    }

    if not args.dry_run:
        save_manifest(manifest_path, tag, current_skills)
        report["wrote_manifest"] = True
    else:
        report["wrote_manifest"] = False

    return report


def print_human(report: dict) -> None:
    if report.get("mode") == "seed":
        print(f"Seeded baseline manifest for {report['upstream']} @ {report['tag']}")
        print(f"  tracking {report['tracked_skills']} upstream skills -> {report['manifest']}")
        print(f"  wrote manifest: {report['wrote_manifest']}")
        return

    c = report["counts"]
    print(f"Upstream radar — {report['upstream']} @ {report['tag']}  (mode: {report['mode']}, gate: {report['gate']})")
    print(f"License: {report['license']}")
    print()
    print(f"  new={c['new']}  changed={c['changed']}  removed={c['removed']}")
    print(f"  classified: NET_NEW={c['net_new']}  ENRICH={c['enrich']}  COVERED={c['covered']}")
    print(f"  -> {c['auto_scaffold']} flagged for auto-scaffold under '{report['gate']}' gate")
    if report["removed_upstream"]:
        print(f"  removed upstream (informational): {', '.join(report['removed_upstream'])}")
    print()
    if not report["gaps"]:
        print("No actionable gaps. (Everything new/changed is already covered.)")
    else:
        print(f"Actionable gaps ({len(report['gaps'])}):")
        print(f"  {'SCAFFOLD':9} {'CLASS':8} {'SCORE':>6}  UPSTREAM SKILL  ->  nearest local")
        for g in sorted(report["gaps"], key=lambda x: (x["top_score"] is not None, x["top_score"] or 0)):
            mark = "AUTO" if g["auto_scaffold"] else "backlog"
            score = f"{g['top_score']:.2f}" if g["top_score"] is not None else "  -  "
            print(f"  {mark:9} {g['classification']:8} {score:>6}  {g['upstream_skill']}  ->  {g['top_local'] or '(none)'}")
    print()
    print(f"Manifest written: {report['wrote_manifest']} ({report['manifest']})")
    print("Next: feed --json output to commands/sync-upstream-skills.md (clean-room author + draft PR).")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Weekly radar over forcedotcom/sf-skills (clean-room discovery only).")
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST), help="Path to the state manifest JSON.")
    parser.add_argument("--tag", default=None, help="Pin to a specific upstream tag (default: latest release).")
    parser.add_argument("--gate", choices=list(GATE_CUT), default="balanced", help="Auto-scaffold aggressiveness.")
    parser.add_argument("--full", action="store_true", help="Audit ALL upstream skills, not just the delta.")
    parser.add_argument("--seed", action="store_true", help="Snapshot baseline only; no classification.")
    parser.add_argument("--dry-run", action="store_true", help="Do not write the manifest.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    args = parser.parse_args(argv)

    try:
        report = run(args)
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print_human(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
