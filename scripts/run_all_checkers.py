#!/usr/bin/env python3
"""Run every skill-local `check_*.py` against a target source tree.

Each skill ships a checker under ``skills/<domain>/<skill>/scripts/check_*.py``
that:

  - Accepts ``--src-root <path>``.
  - Writes ``WARN: ...`` lines (one per finding) to stderr.
  - Exits 0 if no findings, 1 if findings.

This aggregator:

  - Discovers every ``check_*.py`` across the corpus.
  - Runs them in parallel against the target source tree.
  - Parses ``WARN: ...`` lines and groups by skill.
  - Writes a single markdown report (or JSON).
  - Exits 0 if no findings, 1 if any findings — so CI can gate.

Run modes:

  - **Default (markdown report)** — writes
    ``docs/reports/checker-findings.md`` (in the SfSkills repo, not
    the target project). Print a one-line summary to stdout.
  - **--json** — emits a structured JSON payload to stdout (no
    report file).
  - **--include <prefix-or-id>** — restrict to skills matching the
    prefix(es), e.g. ``--include flow/`` for all Flow skills, or
    ``--include flow/flow-error-notification-patterns`` for one.
  - **--severity error** — placeholder for future severity filtering;
    today every checker emits ``WARN``.

Output shape (markdown):

    # Checker findings — <date>

    Ran **N** checkers against `<target>`. **M** had findings.
    Total findings: **K**.

    ## flow/flow-error-notification-patterns (3 findings)

    - WARN: <message>
    - WARN: <message>

    ## admin/picklist-data-integrity (1 finding)

    - WARN: <message>

Usage:

    python3 scripts/run_all_checkers.py --src-root /path/to/sf-project
    python3 scripts/run_all_checkers.py --src-root . --json
    python3 scripts/run_all_checkers.py --src-root . --include flow/
    python3 scripts/run_all_checkers.py --src-root . --workers 16

Designed to be invoked from a consumer's CI:

    - uses: actions/checkout@v4
      with: { repository: 'PranavNagrecha/AwesomeSalesforceSkills', path: 'skills-lib' }
    - run: python3 skills-lib/scripts/run_all_checkers.py --src-root force-app/main/default
"""

from __future__ import annotations

import argparse
import concurrent.futures as cf
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPORT = ROOT / "docs" / "reports" / "checker-findings.md"

# Cap default parallelism — Apex / metadata projects are usually on
# laptop-class machines or modest CI runners. ``min(cpu, 8)`` keeps us
# polite on shared CI runners while saturating local dev.
DEFAULT_WORKERS = min(os.cpu_count() or 4, 8)

# Per-checker timeout. Most checkers finish in < 1s on a small project;
# 60s gives generous headroom for large repos without stalling the pool
# on a runaway one.
PER_CHECKER_TIMEOUT_S = 60.0


@dataclass
class CheckerResult:
    skill_id: str          # e.g. "flow/flow-error-notification-patterns"
    checker_path: Path     # absolute path to the check_*.py
    findings: list[str]    # parsed WARN lines (without the "WARN: " prefix)
    raw_stdout: str
    raw_stderr: str
    exit_code: int
    duration_s: float
    error: str | None = None  # set if invocation itself blew up

    @property
    def had_findings(self) -> bool:
        return bool(self.findings) or (self.exit_code != 0 and self.error is None)


def _discover_checkers(root: Path) -> list[tuple[str, Path]]:
    """Return ``[(skill_id, checker_path), ...]`` for every skill-local
    checker. ``skill_id`` is ``<domain>/<skill-name>``."""
    out: list[tuple[str, Path]] = []
    for checker in sorted((root / "skills").glob("*/*/scripts/check_*.py")):
        # skills/<domain>/<skill>/scripts/check_*.py → skill_id = <domain>/<skill>
        rel = checker.relative_to(root / "skills")
        parts = rel.parts
        if len(parts) < 4:
            continue
        skill_id = f"{parts[0]}/{parts[1]}"
        out.append((skill_id, checker))
    return out


def _filter_by_include(
    checkers: list[tuple[str, Path]], include: list[str] | None
) -> list[tuple[str, Path]]:
    if not include:
        return checkers
    return [
        (sid, p) for sid, p in checkers
        if any(sid == prefix.rstrip("/") or sid.startswith(prefix) for prefix in include)
    ]


def _run_one(
    skill_id: str, checker: Path, src_root: Path, timeout: float
) -> CheckerResult:
    """Invoke one checker and return its result. Never raises."""
    started = time.monotonic()
    try:
        proc = subprocess.run(
            [sys.executable, str(checker), "--src-root", str(src_root)],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        elapsed = time.monotonic() - started
        # Parse WARN lines from BOTH stdout and stderr — most checkers write
        # to stderr, but some legacy ones write to stdout. Be permissive.
        findings: list[str] = []
        for stream in (proc.stdout, proc.stderr):
            for line in stream.splitlines():
                stripped = line.strip()
                if stripped.startswith("WARN:"):
                    findings.append(stripped[len("WARN:"):].strip())
                elif stripped.startswith("ERROR:"):
                    findings.append(stripped[len("ERROR:"):].strip())
        return CheckerResult(
            skill_id=skill_id,
            checker_path=checker,
            findings=findings,
            raw_stdout=proc.stdout,
            raw_stderr=proc.stderr,
            exit_code=proc.returncode,
            duration_s=elapsed,
        )
    except subprocess.TimeoutExpired:
        return CheckerResult(
            skill_id=skill_id,
            checker_path=checker,
            findings=[],
            raw_stdout="",
            raw_stderr="",
            exit_code=-1,
            duration_s=time.monotonic() - started,
            error=f"timeout after {timeout}s",
        )
    except Exception as exc:  # noqa: BLE001 — we deliberately catch everything
        return CheckerResult(
            skill_id=skill_id,
            checker_path=checker,
            findings=[],
            raw_stdout="",
            raw_stderr="",
            exit_code=-1,
            duration_s=time.monotonic() - started,
            error=f"{type(exc).__name__}: {exc}",
        )


def _format_markdown(
    results: list[CheckerResult],
    src_root: Path,
    duration_s: float,
    include: list[str] | None,
) -> str:
    """Render results as a markdown report sorted by finding count desc."""
    with_findings = [r for r in results if r.had_findings and r.error is None]
    errored = [r for r in results if r.error is not None]
    total_findings = sum(len(r.findings) for r in with_findings)

    out: list[str] = []
    out.append(f"# Checker findings — {date.today().isoformat()}\n")
    out.append(
        f"Ran **{len(results)}** checker(s) against `{src_root}` in "
        f"{duration_s:.1f}s.  "
        f"**{len(with_findings)}** had findings.  "
        f"Total findings: **{total_findings}**."
    )
    if include:
        out.append(f"\nFiltered by include: `{', '.join(include)}`.")
    if errored:
        out.append(f"\n**{len(errored)}** checker(s) failed to run cleanly (timeout / exception). See bottom.")
    out.append("")

    out.append("## Triage guide")
    out.append("")
    out.append(
        "Each block below is one skill's findings against the target tree. The "
        "skill's `references/llm-anti-patterns.md` and `references/gotchas.md` "
        "explain *why* each pattern is wrong; this report tells you *where* "
        "in your code it occurs."
    )
    out.append("")

    if not with_findings:
        out.append("---\n\n_No findings._\n")
    else:
        out.append("---")
        out.append("")
        # Sort by finding count desc, then skill_id asc.
        with_findings.sort(key=lambda r: (-len(r.findings), r.skill_id))
        for r in with_findings:
            out.append(f"## `{r.skill_id}` — {len(r.findings)} finding(s)")
            out.append("")
            out.append(
                f"_See `skills/{r.skill_id}/references/llm-anti-patterns.md` "
                f"and `references/gotchas.md` for context._"
            )
            out.append("")
            for f in r.findings:
                out.append(f"- {f}")
            out.append("")

    if errored:
        out.append("---")
        out.append("")
        out.append("## Checker invocation errors")
        out.append("")
        out.append(
            "These checkers failed to run (timeout, exception). The aggregator "
            "treats them as 'no findings' but the checker itself may have a bug."
        )
        out.append("")
        for r in errored:
            rel = r.checker_path.relative_to(ROOT)
            out.append(f"- `{rel}` — {r.error}")
        out.append("")

    return "\n".join(out).rstrip() + "\n"


def _format_json(results: list[CheckerResult], src_root: Path, duration_s: float) -> str:
    payload = {
        "src_root": str(src_root),
        "checker_count": len(results),
        "had_findings_count": sum(1 for r in results if r.had_findings and r.error is None),
        "errored_count": sum(1 for r in results if r.error is not None),
        "total_findings": sum(len(r.findings) for r in results if r.error is None),
        "duration_s": round(duration_s, 2),
        "results": [
            {
                "skill_id": r.skill_id,
                "checker_path": str(r.checker_path.relative_to(ROOT)),
                "exit_code": r.exit_code,
                "duration_s": round(r.duration_s, 3),
                "findings": r.findings,
                "error": r.error,
            }
            for r in sorted(results, key=lambda x: x.skill_id)
        ],
    }
    return json.dumps(payload, indent=2, sort_keys=True)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run every skill-local checker against a target source tree.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 scripts/run_all_checkers.py --src-root .
  python3 scripts/run_all_checkers.py --src-root force-app/main/default --include flow/
  python3 scripts/run_all_checkers.py --src-root . --json | jq '.had_findings_count'
  python3 scripts/run_all_checkers.py --src-root . --workers 16
""",
    )
    parser.add_argument(
        "--src-root", type=Path, required=True,
        help="Path to the source tree to scan (Salesforce metadata project, "
             "Apex source, etc.).",
    )
    parser.add_argument(
        "--out", type=Path, default=DEFAULT_REPORT,
        help=f"Where to write the markdown report (default {DEFAULT_REPORT.relative_to(ROOT)}).",
    )
    parser.add_argument(
        "--json", action="store_true",
        help="Emit JSON to stdout instead of writing the markdown report.",
    )
    parser.add_argument(
        "--include", action="append", default=None,
        help="Restrict to skills whose id starts with this prefix. Repeatable. "
             "Example: --include flow/ --include admin/picklist-data-integrity",
    )
    parser.add_argument(
        "--workers", type=int, default=DEFAULT_WORKERS,
        help=f"Parallel subprocess workers (default {DEFAULT_WORKERS}).",
    )
    parser.add_argument(
        "--timeout", type=float, default=PER_CHECKER_TIMEOUT_S,
        help=f"Per-checker timeout in seconds (default {PER_CHECKER_TIMEOUT_S}).",
    )
    parser.add_argument(
        "--list", action="store_true",
        help="List discovered checkers and exit; do not run anything.",
    )
    args = parser.parse_args()

    checkers = _discover_checkers(ROOT)
    checkers = _filter_by_include(checkers, args.include)

    if args.list:
        for sid, p in checkers:
            print(f"{sid}\t{p.relative_to(ROOT)}")
        print(f"\nTotal: {len(checkers)} checker(s).", file=sys.stderr)
        return 0

    if not checkers:
        print("No checkers discovered (after filtering).", file=sys.stderr)
        return 0

    src_root = args.src_root.resolve()
    if not src_root.exists():
        print(f"ERROR: --src-root does not exist: {src_root}", file=sys.stderr)
        return 2

    started = time.monotonic()
    print(
        f"Running {len(checkers)} checker(s) against {src_root} "
        f"with {args.workers} worker(s)...",
        file=sys.stderr,
    )

    results: list[CheckerResult] = []
    with cf.ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {
            pool.submit(_run_one, sid, p, src_root, args.timeout): (sid, p)
            for sid, p in checkers
        }
        for fut in cf.as_completed(futures):
            results.append(fut.result())

    duration = time.monotonic() - started

    if args.json:
        print(_format_json(results, src_root, duration))
    else:
        rendered = _format_markdown(results, src_root, duration, args.include)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered, encoding="utf-8")
        with_findings = sum(1 for r in results if r.had_findings and r.error is None)
        total_findings = sum(len(r.findings) for r in results if r.error is None)
        errored = sum(1 for r in results if r.error is not None)
        print(
            f"Wrote {args.out.relative_to(ROOT)} — "
            f"{len(checkers)} checker(s), {with_findings} with findings, "
            f"{total_findings} total findings"
            + (f", {errored} errored" if errored else "")
            + f" ({duration:.1f}s).",
            file=sys.stderr,
        )

    # Exit non-zero if any checker found anything OR any checker errored.
    has_findings = any(r.had_findings and r.error is None for r in results)
    return 1 if has_findings else 0


if __name__ == "__main__":
    sys.exit(main())
