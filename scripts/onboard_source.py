#!/usr/bin/env python3
"""Deterministic intake + triage for onboarding external knowledge sources.

This is step 1 of the `/onboard-source` pipeline (see commands/onboard-source.md).
It accepts ONE of three input shapes and produces a machine-readable intake
report that the `source-onboarding` workflow (Sonnet/Opus agents) consumes:

    # A GitHub repository — license-gated candidate discovery
    python3 scripts/onboard_source.py repo https://github.com/owner/name

    # A local attachment (markdown / plain text) — heading-based candidates
    python3 scripts/onboard_source.py file /path/to/notes.md

    # A bare topic
    python3 scripts/onboard_source.py topic "Data Cloud Python code extensions"

Every candidate is triaged against the local catalog via search_knowledge.py
(the same lexical evidence the repo's duplicate gates use) and the VERBATIM
top hits are embedded in the report, so downstream agents interpret
deterministic evidence instead of re-deriving (or fabricating) coverage claims.

License gate (repo mode)
------------------------
    permissive   MIT / Apache-2.0 / BSD / ISC / CC0 / Unlicense / 0BSD / Zlib
                 -> agents MAY read source content; adapted expression needs
                    attribution; claims still require official-doc confirmation.
    clean-room   everything else (GPL/AGPL, CC-BY-NC, MPL/LGPL/EPL, missing,
                 NOASSERTION) -> topic radar ONLY. This script fetches file
                 PATHS + blob SHAs, never file contents, and downstream agents
                 are forbidden from fetching the source at all.

Outputs
-------
    .intake-reports/<slug>-report.json      (gitignored; session artifact)
    config/upstream-sources/<slug>.manifest.json   (only with --write-manifest)
    BACKLOG.yaml entries                     (only with --update-backlog)

stdlib-only, plus the `gh` CLI for GitHub API access (authenticated).
"""

from __future__ import annotations

import argparse
import concurrent.futures
import datetime as _dt
import json
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from upstream_radar import classify, gh_json, slug_to_query  # noqa: E402

REPORT_DIR = REPO_ROOT / ".intake-reports"
MANIFEST_DIR = REPO_ROOT / "config" / "upstream-sources"

PERMISSIVE_SPDX = {
    "MIT", "Apache-2.0", "BSD-2-Clause", "BSD-3-Clause", "ISC",
    "CC0-1.0", "Unlicense", "0BSD", "Zlib",
}

# Directory shapes that usually hold one topic per child directory.
SKILL_DIR_PATTERNS = (
    re.compile(r"^(?:\.claude/|\.agents/)?skills/([^/]+)/"),
    re.compile(r"^(?:prompts|recipes|patterns|playbooks|guides)/([^/]+)/"),
)

MAX_CANDIDATES = 200
SEARCH_WORKERS = 4
TOP_HITS_KEPT = 3


def _now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return re.sub(r"-{2,}", "-", slug)[:80]


# ---------------------------------------------------------------------------
# Candidate discovery — one function per input mode
# ---------------------------------------------------------------------------

def discover_repo(url: str) -> dict:
    m = re.search(r"github\.com/([^/]+)/([^/#?]+)", url)
    if not m:
        raise SystemExit(f"Not a GitHub repo URL: {url}")
    owner, name = m.group(1), m.group(2).removesuffix(".git")
    full = f"{owner}/{name}"

    meta = gh_json(f"repos/{full}")
    spdx = ((meta.get("license") or {}).get("spdx_id")) or "NONE"
    license_class = "permissive" if spdx in PERMISSIVE_SPDX else "clean-room"
    ref = meta.get("default_branch") or "main"

    tree = gh_json(f"repos/{full}/git/trees/{ref}?recursive=1")
    if tree.get("truncated"):
        print("WARNING: GitHub tree truncated; candidate list may be partial.", file=sys.stderr)

    blobs = {e["path"]: e["sha"] for e in tree.get("tree", []) if e.get("type") == "blob"}

    candidates: dict[str, dict] = {}
    for path in blobs:
        for pat in SKILL_DIR_PATTERNS:
            m2 = pat.match(path)
            if m2:
                slug = m2.group(1)
                candidates.setdefault(slug, {
                    "topic": slug.replace("-", " ").replace("_", " "),
                    "origin": path.split("/")[0] if not path.startswith(".") else "/".join(path.split("/")[:2]),
                })
                break
    if not candidates:
        # Fallback: top-level and docs/ markdown files, one candidate per file.
        for path in blobs:
            if path.lower().endswith(".md") and path.count("/") <= 1:
                stem = _slugify(Path(path).stem)
                if stem and stem not in {"readme", "license", "contributing",
                                         "changelog", "code-of-conduct", "security"}:
                    candidates.setdefault(stem, {
                        "topic": stem.replace("-", " "),
                        "origin": path,
                    })

    return {
        "mode": "repo",
        "source": full,
        "source_url": f"https://github.com/{full}",
        "ref": ref,
        "license": spdx,
        "license_class": license_class,
        "manifest_blobs": {
            slug: blobs.get(f"skills/{slug}/SKILL.md", "") for slug in candidates
        },
        "candidates": [
            {"id": slug, **info} for slug, info in sorted(candidates.items())
        ],
    }


HEADING_RE = re.compile(r"^#{1,3}\s+(.+?)\s*#*\s*$")


def discover_file(path_str: str) -> dict:
    path = Path(path_str).expanduser()
    if not path.is_file():
        raise SystemExit(f"Attachment not found: {path}")
    if path.suffix.lower() not in {".md", ".markdown", ".txt"}:
        raise SystemExit(
            f"Unsupported attachment type {path.suffix!r} — convert to markdown/text first."
        )
    seen: dict[str, dict] = {}
    for line in path.read_text(errors="replace").splitlines():
        m = HEADING_RE.match(line.strip())
        if not m:
            continue
        heading = re.sub(r"[`*_\[\]()]", "", m.group(1)).strip()
        slug = _slugify(heading)
        if len(slug) >= 4 and slug not in seen:
            seen[slug] = {"topic": heading, "origin": path.name}
    if not seen:
        # No headings — treat the whole document title (filename) as one topic.
        slug = _slugify(path.stem)
        seen[slug] = {"topic": path.stem.replace("-", " "), "origin": path.name}
    return {
        "mode": "file",
        "source": str(path),
        "license": "user-supplied",
        "license_class": "permissive",
        "candidates": [{"id": s, **info} for s, info in seen.items()],
    }


def discover_topic(topic: str) -> dict:
    return {
        "mode": "topic",
        "source": f"topic-{_slugify(topic)}",
        "license": "user-supplied",
        "license_class": "permissive",
        "candidates": [{"id": _slugify(topic), "topic": topic, "origin": "user"}],
    }


# ---------------------------------------------------------------------------
# Triage — deterministic local-coverage evidence per candidate
# ---------------------------------------------------------------------------

def _search(query: str) -> list[dict]:
    result = subprocess.run(
        [sys.executable, "scripts/search_knowledge.py", "--json", query],
        capture_output=True, text=True, cwd=REPO_ROOT,
    )
    if result.returncode != 0:
        print(f"WARNING: search failed for {query!r}", file=sys.stderr)
        return []
    return (json.loads(result.stdout).get("skills") or [])[:TOP_HITS_KEPT]


def triage(candidates: list[dict]) -> None:
    """Mutates each candidate in place with query, verbatim hits, classification."""
    queries = {c["id"]: slug_to_query(_slugify(c["topic"])) for c in candidates}
    with concurrent.futures.ThreadPoolExecutor(max_workers=SEARCH_WORKERS) as pool:
        hits_by_id = dict(zip(
            queries.keys(),
            pool.map(_search, queries.values()),
        ))
    for c in candidates:
        hits = hits_by_id[c["id"]]
        top = hits[0] if hits else None
        c["query"] = queries[c["id"]]
        c["local_hits"] = [
            {"skill": h.get("id"), "score": h.get("score")} for h in hits
        ]
        c["classification"] = classify(top.get("score") if top else None)


# ---------------------------------------------------------------------------
# Optional side effects — manifest lockfile and BACKLOG.yaml entries
# ---------------------------------------------------------------------------

def write_manifest(report: dict) -> Path:
    slug = _slugify(report["source"])
    path = MANIFEST_DIR / f"{slug}.manifest.json"
    MANIFEST_DIR.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({
        "upstream": report["source"],
        "license": report["license"],
        "license_class": report["license_class"],
        "ref": report.get("ref", ""),
        "retrieved": report["generated"],
        "skills": report.get("manifest_blobs", {}),
    }, indent=1) + "\n")
    return path


def update_backlog(report: dict) -> int:
    from queue_reader import BacklogEntry, load_backlog, render_backlog, BACKLOG

    entries = load_backlog()
    known = {e.id for e in entries}
    added = 0
    for c in report["candidates"]:
        if c["id"] in known:
            continue
        cls = c["classification"]
        status = "DUPLICATE" if cls == "COVERED" else "RESEARCH"
        hits = ", ".join(f"{h['skill']} ({h['score']})" for h in c["local_hits"]) or "no hits"
        entries.append(BacklogEntry(
            id=c["id"],
            status=status,
            skill=c["id"],
            summary=f"{c['topic']} — intake from {report['source']} ({report['mode']} mode).",
            notes=(
                f"Intake triage {report['generated']}: {cls}; "
                f"search_knowledge top hits: {hits}. "
                f"License class: {report['license_class']}."
            ),
            history=[{"at": report["generated"], "status": status, "actor": "onboard_source"}],
        ))
        added += 1
    if added:
        BACKLOG.write_text(render_backlog(entries))
        print(f"BACKLOG.yaml: +{added} entries — regenerate the dashboard with:")
        print("  python3 scripts/generate_queue_dashboard.py")
    return added


# ---------------------------------------------------------------------------


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("mode", choices=["repo", "file", "topic"])
    ap.add_argument("value", help="repo URL, file path, or topic text")
    ap.add_argument("--write-manifest", action="store_true",
                    help="repo mode: commit-ready lockfile under config/upstream-sources/")
    ap.add_argument("--update-backlog", action="store_true",
                    help="append RESEARCH/DUPLICATE entries to BACKLOG.yaml")
    ap.add_argument("--max-candidates", type=int, default=MAX_CANDIDATES)
    ap.add_argument("--out", type=Path, default=None,
                    help="report path (default .intake-reports/<slug>-report.json)")
    args = ap.parse_args(argv)

    report = {"repo": discover_repo, "file": discover_file, "topic": discover_topic}[args.mode](args.value)
    report["generated"] = _now()

    if len(report["candidates"]) > args.max_candidates:
        print(f"NOTE: truncating {len(report['candidates'])} candidates to {args.max_candidates}.",
              file=sys.stderr)
        report["candidates"] = report["candidates"][:args.max_candidates]

    print(f"Triaging {len(report['candidates'])} candidate(s) against the local catalog…")
    triage(report["candidates"])

    counts: dict[str, int] = {}
    for c in report["candidates"]:
        counts[c["classification"]] = counts.get(c["classification"], 0) + 1
    report["counts"] = counts

    report_stem = Path(report["source"]).stem if report["mode"] == "file" else report["source"]
    out = args.out or (REPORT_DIR / f"{_slugify(report_stem)}-report.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=1) + "\n")

    if args.write_manifest and report["mode"] == "repo":
        print(f"Manifest: {write_manifest(report).relative_to(REPO_ROOT)}")
    if args.update_backlog:
        update_backlog(report)

    print(f"\nSource: {report['source']}  license={report['license']} ({report['license_class']})")
    print(f"Counts: {counts}")
    print(f"Report: {out}")
    print("\nNext: launch the source-onboarding workflow with this report path "
          "(see commands/onboard-source.md).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
