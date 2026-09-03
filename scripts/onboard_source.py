#!/usr/bin/env python3
"""Deterministic intake + triage for onboarding external knowledge sources.

This is step 1 of the `/onboard-source` pipeline (see commands/onboard-source.md).
It accepts ONE of three input shapes and produces a machine-readable intake
report that the `source-onboarding` workflow (Sonnet/Opus agents) consumes:

    # A GitHub repository — license-gated candidate discovery
    python3 scripts/onboard_source.py repo https://github.com/owner/name

    # A subdirectory of a repo at a pinned ref (tree URLs are parsed for you;
    # --ref / --subpath override whatever the URL carries)
    python3 scripts/onboard_source.py repo https://github.com/owner/name/tree/<sha>/plugins/x/skills
    python3 scripts/onboard_source.py repo https://github.com/owner/name --ref <sha> --subpath plugins/x/skills

    # A local attachment (markdown / plain text) — heading-based candidates
    python3 scripts/onboard_source.py file /path/to/notes.md

    # A web article — fetch is out of scope for this stdlib script; distill the
    # article into a headings file yourself, then record the true origin:
    python3 scripts/onboard_source.py url /path/to/headings.md --source-url https://example.com/article

    # A bare topic
    python3 scripts/onboard_source.py topic "Data Cloud Python code extensions"

Every candidate is triaged against the local catalog via search_knowledge.py
(the same lexical evidence the repo's duplicate gates use) and the VERBATIM
top hits are embedded in the report, so downstream agents interpret
deterministic evidence instead of re-deriving (or fabricating) coverage claims.

License gate
------------
    permissive   MIT / Apache-2.0 / BSD / ISC / CC0 / Unlicense / 0BSD / Zlib
                 -> agents MAY read source content; adapted expression needs
                    attribution; claims still require official-doc confirmation.
    clean-room   everything else (GPL/AGPL, CC-BY-NC, MPL/LGPL/EPL, missing,
                 NOASSERTION) -> topic radar ONLY. This script fetches file
                 PATHS + blob SHAs, never file contents, and downstream agents
                 are forbidden from fetching the source at all.

    repo mode detects the SPDX id from GitHub. file/url modes default to
    CLEAN-ROOM (unlicensed material is the common case; "when in doubt,
    clean-room"). `--license permissive` lets the caller attest otherwise;
    `--license clean-room` tightens any mode. Weakening repo mode's detected
    non-permissive license is refused.

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

# Some repositories publish conflicting license signals across tracked files.
# GitHub's repository metadata exposes only one of those signals, so an
# apparently permissive SPDX result is not sufficient for these known cases.
# Keep them clean-room until the upstream project resolves the conflict.
REPO_LICENSE_OVERRIDES = {
    "forcedotcom/sf-skills": {
        "license": (
            "CONFLICTING: repository LICENSE.txt declares Apache-2.0 while "
            "package metadata declares CC-BY-NC-4.0"
        ),
        "license_class": "clean-room",
        "reason": (
            "Known public license conflict; use topic discovery only and author "
            "all shipped SfSkills content independently from official Salesforce sources."
        ),
    },
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

def _parse_repo_url(url: str) -> tuple[str, str | None, str | None]:
    """owner/name plus any ref/subpath a GitHub tree URL carries.

    https://github.com/o/n                      -> ("o/n", None, None)
    https://github.com/o/n/tree/<ref>          -> ("o/n", "<ref>", None)
    https://github.com/o/n/tree/<ref>/a/b      -> ("o/n", "<ref>", "a/b")
    """
    m = re.search(r"github\.com/([^/]+)/([^/#?]+)(?:/tree/([^/#?]+)(?:/([^#?]+))?)?", url)
    if not m:
        raise SystemExit(f"Not a GitHub repo URL: {url}")
    full = f"{m.group(1)}/{m.group(2).removesuffix('.git')}"
    return full, m.group(3), (m.group(4) or "").strip("/") or None


def discover_repo(url: str, ref: str | None = None, subpath: str | None = None) -> dict:
    full, url_ref, url_subpath = _parse_repo_url(url)
    ref = ref or url_ref
    subpath = (subpath or url_subpath or "").strip("/")

    meta = gh_json(f"repos/{full}")
    detected_spdx = ((meta.get("license") or {}).get("spdx_id")) or "NONE"
    spdx = detected_spdx
    license_class = "permissive" if spdx in PERMISSIVE_SPDX else "clean-room"
    license_reason = None
    override = REPO_LICENSE_OVERRIDES.get(full.lower())
    if override:
        spdx = override["license"]
        license_class = override["license_class"]
        license_reason = override["reason"]
    ref = ref or meta.get("default_branch") or "main"

    tree = gh_json(f"repos/{full}/git/trees/{ref}?recursive=1")
    if tree.get("truncated"):
        print("WARNING: GitHub tree truncated; candidate list may be partial.", file=sys.stderr)

    blobs = {e["path"]: e["sha"] for e in tree.get("tree", []) if e.get("type") == "blob"}
    if subpath:
        # Scope discovery to the subtree; paths below are subpath-relative so
        # the SKILL_DIR_PATTERNS keep working regardless of where the skills
        # directory sits inside a monorepo.
        prefix = subpath + "/"
        blobs = {p[len(prefix):]: sha for p, sha in blobs.items() if p.startswith(prefix)}
        if not blobs:
            raise SystemExit(f"--subpath {subpath!r} matches no files at ref {ref!r}")

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
    if not candidates and subpath:
        # The subpath often IS the skills directory — one topic per child dir.
        for path in blobs:
            if "/" in path:
                slug = path.split("/")[0]
                candidates.setdefault(slug, {
                    "topic": slug.replace("-", " ").replace("_", " "),
                    "origin": f"{subpath}/{slug}",
                })
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
        "source_url": f"https://github.com/{full}" + (f"/tree/{ref}/{subpath}" if subpath else ""),
        "ref": ref,
        **({"subpath": subpath} if subpath else {}),
        "report_slug": f"{full}-{subpath}" if subpath else full,
        "license": spdx,
        "detected_license": detected_spdx,
        "license_class": license_class,
        **({"license_reason": license_reason} if license_reason else {}),
        "manifest_blobs": {
            slug: blobs.get(f"skills/{slug}/SKILL.md") or blobs.get(f"{slug}/SKILL.md", "")
            for slug in candidates
        },
        "candidates": [
            {"id": slug, **info} for slug, info in sorted(candidates.items())
        ],
    }


HEADING_RE = re.compile(r"^(#{1,3})\s+(.+?)\s*#*\s*$")


def discover_file(path_str: str) -> dict:
    path = Path(path_str).expanduser()
    if not path.is_file():
        raise SystemExit(f"Attachment not found: {path}")
    if path.suffix.lower() not in {".md", ".markdown", ".txt"}:
        raise SystemExit(
            f"Unsupported attachment type {path.suffix!r} — convert to markdown/text first."
        )
    seen: dict[str, dict] = {}
    doc_slug = _slugify(path.stem)
    skipped_title = False
    for line in path.read_text(errors="replace").splitlines():
        m = HEADING_RE.match(line.strip())
        if not m:
            continue
        level = len(m.group(1))
        heading = re.sub(r"[`*_\[\]()]", "", m.group(2)).strip()
        slug = _slugify(heading)
        if len(slug) < 4 or slug in seen:
            continue
        # The document's own title is not a topic: skip the first H1, and any
        # heading that restates the source slug. (Every file-mode production
        # run otherwise produced a junk NET_NEW from the title heading.)
        if level == 1 and not skipped_title:
            skipped_title = True
            continue
        if slug == doc_slug:
            continue
        seen[slug] = {"topic": heading, "origin": path.name}
    if not seen:
        # No usable headings — treat the document title (filename) as one topic.
        slug = _slugify(path.stem)
        seen[slug] = {"topic": path.stem.replace("-", " "), "origin": path.name}
    return {
        "mode": "file",
        # Unlicensed attachments are the common case; "when in doubt,
        # clean-room" (commands/onboard-source.md). --license overrides.
        "source": str(path),
        "license": "NONE (not stated)",
        "license_class": "clean-room",
        "candidates": [{"id": s, **info} for s, info in seen.items()],
    }


def discover_url(path_str: str, source_url: str) -> dict:
    """Web-article intake: heading extraction from a caller-distilled headings
    file (fetching is out of scope for this stdlib script), with the report
    recording the true origin URL rather than the scratchpad path."""
    report = discover_file(path_str)
    report["mode"] = "url"
    report["source"] = source_url
    report["source_url"] = source_url
    report["headings_file"] = str(Path(path_str).expanduser())
    report["license"] = "NONE (web content, no license stated)"
    report["report_slug"] = re.sub(r"^https?-+", "", _slugify(source_url))
    return report


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
    slug = _slugify(report.get("report_slug") or report["source"])
    path = MANIFEST_DIR / f"{slug}.manifest.json"
    MANIFEST_DIR.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({
        "upstream": report["source"],
        "license": report["license"],
        "license_class": report["license_class"],
        **({"detected_license": report["detected_license"]} if report.get("detected_license") else {}),
        **({"license_reason": report["license_reason"]} if report.get("license_reason") else {}),
        "ref": report.get("ref", ""),
        **({"subpath": report["subpath"]} if report.get("subpath") else {}),
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
    ap.add_argument("mode", choices=["repo", "file", "url", "topic"])
    ap.add_argument("value", help="repo URL, file path, headings-file path (url mode), or topic text")
    ap.add_argument("--write-manifest", action="store_true",
                    help="repo mode: commit-ready lockfile under config/upstream-sources/")
    ap.add_argument("--update-backlog", action="store_true",
                    help="append RESEARCH/DUPLICATE entries to BACKLOG.yaml")
    ap.add_argument("--license", choices=["permissive", "clean-room"], default=None,
                    help="override the license class. file/url modes default to clean-room; "
                         "repo mode's detected license can only be tightened, never weakened.")
    ap.add_argument("--source-url", default=None,
                    help="true origin URL (required for url mode; optional provenance for file mode)")
    ap.add_argument("--ref", default=None,
                    help="repo mode: git ref (branch/tag/SHA) to read instead of the default branch")
    ap.add_argument("--subpath", default=None,
                    help="repo mode: only triage files under this directory (monorepo scoping)")
    ap.add_argument("--max-candidates", type=int, default=MAX_CANDIDATES)
    ap.add_argument("--out", type=Path, default=None,
                    help="report path (default .intake-reports/<slug>-report.json)")
    args = ap.parse_args(argv)

    if args.mode == "repo":
        report = discover_repo(args.value, ref=args.ref, subpath=args.subpath)
    elif args.mode == "url":
        if not args.source_url:
            ap.error("url mode requires --source-url https://…")
        report = discover_url(args.value, args.source_url)
    elif args.mode == "file":
        report = discover_file(args.value)
        if args.source_url:
            report["source_url"] = args.source_url
    else:
        report = discover_topic(args.value)

    if args.license and args.license != report["license_class"]:
        if report["mode"] == "repo" and args.license == "permissive":
            raise SystemExit(
                f"Refusing --license permissive: {report['source']} has detected license "
                f"{report['license']!r} (clean-room). The gate can only be tightened."
            )
        note = ("forced clean-room via --license" if args.license == "clean-room"
                else "user-attested permissive via --license")
        report["license"] = f"{report['license']} — {note}"
        report["license_class"] = args.license

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

    report_stem = report.get("report_slug") or (
        Path(report["source"]).stem if report["mode"] == "file" else report["source"])
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
