#!/usr/bin/env python3
"""Golden eval runner.

Modes:
    --structure                Lint every eval file under evals/golden/
    --file <path>              Operate on a single eval file
    --dry-run                  Parse + lint only; no grader invocation
    --grader <model-id>        Invoke the named grader (not bundled — wire up in --grader-cmd)
    --grader-cmd <cmd>         External command taking the eval case on stdin, returning JSON on stdout
    --output <path>            Write a run report (JSON) to this path

Exit codes:
    0  all pass
    1  structural errors
    2  P0 rubric failures
    3  invalid CLI usage

The script intentionally performs NO network calls of its own. Grader
models are invoked through `--grader-cmd` so teams can plug in the model
provider they already use (Bedrock, OpenAI, internal gateway, etc.).
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

REPO_ROOT = Path(__file__).resolve().parents[2]
GOLDEN_DIR = REPO_ROOT / "evals" / "golden"

REQUIRED_METADATA_KEYS = {
    "Skill under test",
    "Priority",
    "Cases",
    "Last verified",
    "Related templates",
    "Related decision trees",
}

REQUIRED_CASE_HEADERS = [
    "**Priority:**",
    "**User prompt:**",
    "**Expected output MUST include:**",
    "**Expected output MUST NOT include:**",
    "**Rubric",
    "**Reference answer",
]


@dataclass
class Case:
    name: str
    priority: str
    text: str  # raw markdown block
    line_start: int


@dataclass
class EvalFile:
    path: Path
    metadata: dict
    cases: list[Case] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


METADATA_LINE = re.compile(r"^-\s+\*\*(?P<key>[^:]+):\*\*\s+(?P<value>.+)\s*$")


def parse_eval_file(path: Path) -> EvalFile:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()

    metadata: dict = {}
    cases: list[Case] = []
    errors: list[str] = []

    if not lines or not lines[0].startswith("# Eval:"):
        errors.append("first line must start with '# Eval:'")

    for line in lines[:25]:
        match = METADATA_LINE.match(line)
        if match:
            metadata[match.group("key").strip()] = match.group("value").strip()

    missing = REQUIRED_METADATA_KEYS - set(metadata.keys())
    if missing:
        errors.append(f"missing metadata keys: {sorted(missing)}")

    current_start = None
    current_name = None
    for i, line in enumerate(lines):
        if line.startswith("## Case "):
            if current_start is not None:
                case_text = "\n".join(lines[current_start:i])
                cases.append(_build_case(current_name, case_text, current_start, errors))
            current_start = i
            current_name = line.lstrip("# ").strip()

    if current_start is not None:
        case_text = "\n".join(lines[current_start:])
        cases.append(_build_case(current_name, case_text, current_start, errors))

    if not cases:
        errors.append("no '## Case ' sections found")

    return EvalFile(path=path, metadata=metadata, cases=cases, errors=errors)


def _build_case(name: str, body: str, line_start: int, errors: list[str]) -> Case:
    missing = [h for h in REQUIRED_CASE_HEADERS if h not in body]
    if missing:
        errors.append(f"case '{name}' missing: {missing}")
    priority_match = re.search(r"\*\*Priority:\*\*\s+(\w+)", body)
    priority = priority_match.group(1) if priority_match else "UNKNOWN"
    return Case(name=name, priority=priority, text=body, line_start=line_start)


def iter_eval_files(single: Path | None) -> Iterable[Path]:
    if single:
        yield single
        return
    if not GOLDEN_DIR.exists():
        return
    for path in sorted(GOLDEN_DIR.glob("*.md")):
        if path.name.startswith("_"):
            continue
        yield path


def lint(files: list[EvalFile]) -> int:
    any_errors = False
    for f in files:
        if f.errors:
            any_errors = True
            print(f"[FAIL] {f.path.relative_to(REPO_ROOT)}")
            for err in f.errors:
                print(f"       - {err}")
        else:
            print(f"[OK]   {f.path.relative_to(REPO_ROOT)} ({len(f.cases)} cases)")
    return 1 if any_errors else 0


def grade(files: list[EvalFile], grader_cmd: str, output_path: Path | None) -> int:
    results = []
    p0_failures = 0
    for f in files:
        for case in f.cases:
            payload = {
                "skill": f.metadata.get("Skill under test"),
                "case_name": case.name,
                "priority": case.priority,
                "case_markdown": case.text,
            }
            proc = subprocess.run(
                grader_cmd,
                shell=True,
                input=json.dumps(payload),
                capture_output=True,
                text=True,
                check=False,
            )
            if proc.returncode != 0:
                print(f"[ERROR] grader failed for {case.name}: {proc.stderr.strip()}")
                continue
            try:
                result = json.loads(proc.stdout)
            except json.JSONDecodeError:
                print(f"[ERROR] grader returned non-JSON for {case.name}")
                continue
            result.update({
                "file": str(f.path.relative_to(REPO_ROOT)),
                "case": case.name,
                "priority": case.priority,
            })
            results.append(result)
            if case.priority == "P0":
                rubric = result.get("rubric", {})
                if any(score < 4 for score in rubric.values()):
                    p0_failures += 1
    if output_path:
        output_path.write_text(json.dumps(results, indent=2))
        print(f"Report written to {output_path}")
    if p0_failures:
        print(f"[FAIL] {p0_failures} P0 cases scored below 4/5 on at least one rubric item.")
        return 2
    print("[PASS] All P0 gates met.")
    return 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Run or lint golden evals.")
    parser.add_argument("--structure", action="store_true", help="Lint every eval file.")
    parser.add_argument("--file", type=Path, help="Operate on a single eval file.")
    parser.add_argument("--dry-run", action="store_true", help="Parse + lint only.")
    parser.add_argument("--grader", help="Grader model identifier (informational).")
    parser.add_argument("--grader-cmd", help="Shell command that grades one case via stdin/stdout.")
    parser.add_argument("--output", type=Path, help="Write run report JSON here.")
    args = parser.parse_args(argv)

    if args.structure and args.file:
        parser.error("use either --structure or --file, not both.")

    single = args.file.resolve() if args.file else None
    files = [parse_eval_file(p) for p in iter_eval_files(single)]

    if not files:
        print("No eval files found.")
        return 0

    if args.structure or args.dry_run or not args.grader_cmd:
        return lint(files)

    return grade(files, args.grader_cmd, args.output)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
