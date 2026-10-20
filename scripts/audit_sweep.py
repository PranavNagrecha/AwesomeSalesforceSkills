#!/usr/bin/env python3
"""Mechanical pre-report sweep for a skill writer's worktree — catches the two
defect classes that reviewers kept finding by hand.

1. LEFTOVERS: every distinctive token (number, identifier, quoted phrase, API
   name) that a writer REMOVED or REWROTE in one place must not survive
   unchanged somewhere else in the same package (a heading, a checklist, a
   template, a code comment, a checker docstring). Batches 3-5 of R3-06 had
   18, 16 and 31 such survivals per batch.

3. CITES: every `<guide> 264 L<n>` cite added in the diff is resolved and its corpus line printed;
   blank or table-of-contents lines are flagged BLANK/TOC (11 such cites in one batch).

2. MARKERS: every `UNVERIFIED (YYYY-MM-DD)` marker the writer ADDED must sit on
   a claim the corpus does NOT hold. For each new marker the sweep extracts the
   claim's key terms and greps BOTH corpus directories; a hit is printed for the
   writer to open before reporting. Batches 1-5 had 42, 9, 2, 4, 10 markers on
   corpus-held claims.

Usage (inside the writer's worktree, after editing, before reporting):
  python3 scripts/audit_sweep.py --base <commit-before-edits> \\
      --skills skills/admin/formula-fields skills/apex/soql-fundamentals \\
      --corpus /path/corpus264 --corpus /path/corpus

Exit 0 always (it is an aid, not a gate); prints `SWEEP leftovers=<n> marker-hits=<m> bad-cites=<b>`
as its last line so the reviewer can compare the writer's attached output.
Stdlib only.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

TOKEN_RE = re.compile(
    r"""
    `[^`\n]{3,80}`                       # backtick spans
    | "[^"\n]{6,80}"                     # double-quoted phrases
    | '[^'\n]{6,80}'                     # single-quoted phrases
    | \b\d[\d,]*(?:\.\d+)?\s?(?:MB|KB|GB|ms|s|%|characters|records|rows|fields|levels|per\s\w+)\b
    | \b[A-Z][A-Za-z0-9]+(?:\.[A-Za-z0-9_]+)+\b  # Dotted.API.Names
    | \b[A-Z]{2,}[_A-Z0-9]{3,}\b        # CONSTANT_LIKE_NAMES
    | <[a-zA-Z:]+>                       # XML element names
    | \bAPI\s(?:version\s)?\d{2}\.0\b    # API 55.0
    """,
    re.VERBOSE,
)
STOP = {"UNVERIFIED", "SKILL.md", "TODO", "README", "https://", "http://"}
MARKER_RE = re.compile(r"UNVERIFIED\s*\(\d{4}-\d{2}-\d{2}\)")
WORD_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_.]{3,}|\d[\d,]*(?:\.\d+)?")
COMMON = set(
    "this that with from have been were will which their there about when what where only also "
    "into than then them they your more most some such very each other after before over under "
    "does not can cannot must should would could these those being does field fields record records "
    "object objects value values user users unverified salesforce apex flow skill claim because".split()
)


def run(cmd: list[str], cwd: Path) -> str:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True, check=False).stdout


def diff_lines(base: str, path: Path, cwd: Path) -> tuple[list[str], list[str]]:
    """(removed lines, added lines) for one skill dir between base and the working tree."""
    out = run(["git", "diff", base, "--", str(path)], cwd)
    removed, added = [], []
    for ln in out.splitlines():
        if ln.startswith("---") or ln.startswith("+++"):
            continue
        if ln.startswith("-"):
            removed.append(ln[1:])
        elif ln.startswith("+"):
            added.append(ln[1:])
    return removed, added


def _distinctive(t: str) -> bool:
    """Only tokens a reviewer would call 'the old claim': numbers with units, API versions, dotted/underscored
    identifiers, XML elements, or quoted phrases of three or more words. Bare words like `inputs`, `Output`,
    `null` produced 130 false LEFTOVER lines in one batch."""
    if any(c.isdigit() for c in t):
        return True
    if t.startswith("<") and t.endswith(">"):
        return True
    if "." in t or "_" in t:
        return True
    return len(t.split()) >= 3


def tokens(text: str) -> set[str]:
    out = set()
    for m in TOKEN_RE.finditer(text):
        t = m.group(0).strip("`\"'")
        if len(t) < 4 or any(s in t for s in STOP) or not _distinctive(t):
            continue
        out.add(t)
    return out


def package_text(path: Path) -> dict[Path, str]:
    files = {}
    for f in sorted(path.rglob("*")):
        if f.is_file() and f.suffix in {".md", ".py", ".xml", ".cls", ".txt", ".json", ".yaml", ".yml", ".html", ".js"}:
            try:
                files[f] = f.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
    return files


def leftovers(path: Path, base: str, cwd: Path) -> list[tuple[str, Path, int]]:
    removed, added = diff_lines(base, path, cwd)
    gone = tokens("\n".join(removed)) - tokens("\n".join(added))
    if not gone:
        return []
    hits = []
    for f, text in package_text(path).items():
        for i, line in enumerate(text.splitlines(), 1):
            for t in gone:
                if t in line and "UNVERIFIED" not in line and "Summer '26" not in line and "262" not in line:
                    hits.append((t, f.relative_to(cwd), i))
    return hits


def key_terms(line: str) -> list[str]:
    """Identifier-like terms only: API names, element names, constants, numbers with 3+ digits, Capitalised words >= 6."""
    words = [w.strip(",.;:()`'\"") for w in WORD_RE.findall(line)]
    terms = []
    for w in words:
        if not w or w.lower() in COMMON or w.upper() == "UNVERIFIED":
            continue
        ident = ("_" in w) or ("." in w and not w.endswith(".")) or any(c.isdigit() for c in w) or (w[:1].isupper() and len(w) >= 6)
        if ident and len(w) >= 3:
            terms.append(w)
    # dedupe, keep order; prefer longer identifiers
    seen, out = set(), []
    for w in sorted(terms, key=lambda x: (-("_" in x or "." in x), -len(x))):
        if w.lower() not in seen:
            seen.add(w.lower()); out.append(w)
    return out[:3]


def marker_hits(path: Path, base: str, cwd: Path, corpora: list[Path]) -> list[tuple[Path, int, str, str]]:
    """New UNVERIFIED markers whose top-2 identifier terms co-occur on ONE corpus line somewhere."""
    _, added = diff_lines(base, path, cwd)
    added_set = set(added)
    corpus_files = []
    seen_names = set()
    for c in corpora:
        for cf in sorted(c.glob("*.txt")):
            if cf.name in seen_names:  # the 262 copy of a guide also present at 264 adds only noise
                continue
            seen_names.add(cf.name)
            try:
                corpus_files.append((cf.name, cf.read_text(encoding="utf-8", errors="ignore").splitlines()))
            except OSError:
                continue
    results = []
    for f, text in package_text(path).items():
        for i, line in enumerate(text.splitlines(), 1):
            if not MARKER_RE.search(line) or line not in added_set:
                continue
            terms = key_terms(MARKER_RE.sub("", line))
            if len(terms) < 2:
                continue
            a, b = terms[0], terms[1]
            hit = None
            for name, lines in corpus_files:
                for ln in lines:
                    if a in ln and b in ln:
                        hit = (name, ln.strip()[:110]); break
                if hit:
                    break
            if hit:
                results.append((f.relative_to(cwd), i, f"{a} + {b}", f"{hit[0]}: {hit[1]}"))
    return results


CITE_RE = re.compile(r"\b(apexdev|api_meta|apexref|secguide|obj|object_reference|lim|ldv|pe|platform_events|sfdx|sfdx_dev|pkg2|pkg2_dev|rest|api_rest|asy|api_asynch|stream|api_streaming|dl|data_loader|salesforce_apex_developer_guide|salesforce_app_limits_cheatsheet|salesforce_large_data_volumes_bp|salesforce_data_loader)(?:\.txt)?\s+(264|262)\s+L(\d+)")
GUIDE_FILES = {
    "apexdev": "salesforce_apex_developer_guide.txt", "salesforce_apex_developer_guide": "salesforce_apex_developer_guide.txt",
    "api_meta": "api_meta.txt", "apexref": "salesforce_apex_reference_guide.txt", "secguide": "salesforce_security_impl_guide.txt",
    "obj": "object_reference.txt", "object_reference": "object_reference.txt", "lim": "salesforce_app_limits_cheatsheet.txt",
    "salesforce_app_limits_cheatsheet": "salesforce_app_limits_cheatsheet.txt", "ldv": "salesforce_large_data_volumes_bp.txt",
    "salesforce_large_data_volumes_bp": "salesforce_large_data_volumes_bp.txt", "pe": "platform_events.txt", "platform_events": "platform_events.txt",
    "sfdx": "sfdx_dev.txt", "sfdx_dev": "sfdx_dev.txt", "pkg2": "pkg2_dev.txt", "pkg2_dev": "pkg2_dev.txt", "rest": "api_rest.txt",
    "api_rest": "api_rest.txt", "asy": "api_asynch.txt", "api_asynch": "api_asynch.txt", "stream": "api_streaming.txt",
    "api_streaming": "api_streaming.txt", "dl": "salesforce_data_loader.txt", "data_loader": "salesforce_data_loader.txt",
    "salesforce_data_loader": "salesforce_data_loader.txt",
}
TOC_RE = re.compile(r"(\. ){4,}|^\s*$")


def cite_check(path: Path, base: str, cwd: Path, corpora: list[Path]) -> list[tuple[str, str]]:
    """Every cite ADDED in the diff, resolved to its corpus line. Flags blank and table-of-contents lines."""
    _, added = diff_lines(base, path, cwd)
    by_release = {}
    for c in corpora:
        rel = "264" if "264" in c.name else "262"
        by_release.setdefault(rel, c)
    out, seen = [], set()
    for line in added:
        for m in CITE_RE.finditer(line):
            guide, rel, n = m.group(1), m.group(2), int(m.group(3))
            key = (guide, rel, n)
            if key in seen:
                continue
            seen.add(key)
            cdir = by_release.get(rel)
            fname = GUIDE_FILES.get(guide)
            if not cdir or not fname or not (cdir / fname).exists():
                out.append((f"{guide} {rel} L{n}", "UNRESOLVED: corpus file not available"))
                continue
            try:
                text = (cdir / fname).read_text(encoding="utf-8", errors="ignore").splitlines()
            except OSError:
                continue
            if n < 1 or n > len(text):
                out.append((f"{guide} {rel} L{n}", "OUT OF RANGE"))
                continue
            ln = text[n - 1].strip()
            flag = "BLANK/TOC " if TOC_RE.search(ln) else ""
            out.append((f"{guide} {rel} L{n}", f"{flag}{ln[:120]}"))
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base", required=True, help="commit before the writer's edits (e.g. the merge-base or HEAD)")
    ap.add_argument("--skills", nargs="+", required=True, help="skill directories to sweep")
    ap.add_argument("--corpus", action="append", default=[], help="corpus directory of .txt guides (repeatable)")
    ap.add_argument("--cwd", default=".", help="repo/worktree root")
    args = ap.parse_args(argv)
    cwd = Path(args.cwd).resolve()
    corpora = [Path(c) for c in args.corpus if Path(c).is_dir()]
    total_left = total_mark = total_bad = 0
    for s in args.skills:
        p = (cwd / s).resolve()
        if not p.is_dir():
            print(f"ERROR: not a directory: {s}")
            continue
        left = leftovers(p, args.base, cwd)
        marks = marker_hits(p, args.base, cwd, corpora) if corpora else []
        cites = cite_check(p, args.base, cwd, corpora) if corpora else []
        bad_cites = [c for c in cites if c[1].startswith(("BLANK/TOC", "OUT OF RANGE", "UNRESOLVED"))]
        print(f"== {s}: leftovers={len(left)} marker-hits={len(marks)} cites={len(cites)} bad-cites={len(bad_cites)}")
        for c, ln in cites:
            print(f"  CITE     {c}: {ln}")
        for t, f, i in left[:60]:
            print(f"  LEFTOVER {f}:{i}: old token still present: {t!r}")
        for f, i, terms, cf in marks[:60]:
            print(f"  MARKER   {f}:{i}: corpus file {cf} contains {terms} — open it before keeping this UNVERIFIED")
        total_left += len(left)
        total_mark += len(marks)
        total_bad += len(bad_cites)
    print(f"SWEEP leftovers={total_left} marker-hits={total_mark} bad-cites={total_bad}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
