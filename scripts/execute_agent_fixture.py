#!/usr/bin/env python3
"""Execute a runtime agent against a fixture and capture its output envelope.

Wires together the three pieces that previously existed in isolation:

    fixture YAML  -->  this harness  -->  envelope JSON  -->  run_agent_evals.py --grade

Until this script existed, the repo had agent specs (AGENT.md), agent
fixtures (evals/agents/fixtures/<slug>/*.yaml), and an envelope grader
(evals/agents/scripts/run_agent_evals.py), but nothing that actually
invoked a model to produce the envelope the grader expects. Every agent
shipped unverified.

Usage:

    ANTHROPIC_API_KEY=... \\
      python3 scripts/execute_agent_fixture.py \\
        --fixture evals/agents/fixtures/apex-refactorer/happy-path.yaml

Outputs land in:
    docs/validation/agent_executions_<YYYY-MM-DD>/
        <agent>__<case>.envelope.json      the model's envelope
        <agent>__<case>.raw.md             the raw model response
        <agent>__<case>.prompt.txt         the assembled prompt (for debugging)
        <agent>__<case>.grade.txt          the grader's verdict

Stdlib only — no `anthropic` SDK dependency. PyYAML + jsonschema are
already in requirements.txt.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML required (pip install pyyaml)", file=sys.stderr)
    sys.exit(3)

try:
    import jsonschema
except ImportError:
    jsonschema = None  # soft dep — schema validation becomes a WARN

REPO_ROOT = Path(__file__).resolve().parents[1]
AGENTS_DIR = REPO_ROOT / "agents"
SHARED_DIR = AGENTS_DIR / "_shared"
ENVELOPE_SCHEMA_PATH = SHARED_DIR / "schemas" / "output-envelope.schema.json"
REFUSAL_CODES_PATH = SHARED_DIR / "REFUSAL_CODES.md"
DELIVERABLE_CONTRACT_PATH = SHARED_DIR / "DELIVERABLE_CONTRACT.md"

DEFAULT_MODEL = "claude-sonnet-4-5"
DEFAULT_MAX_TOKENS = 8000
DEFAULT_API_BASE = "https://api.anthropic.com"
ANTHROPIC_VERSION = "2023-06-01"


def load_fixture(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise SystemExit(f"fixture root must be a mapping: {path}")
    for req in ("eval", "inputs", "expect"):
        if req not in data:
            raise SystemExit(f"fixture missing required block `{req}`: {path}")
    return data


def load_agent(agent_slug: str) -> tuple[str, dict | None]:
    """Return (AGENT.md body, inputs.schema.json dict or None)."""
    agent_dir = AGENTS_DIR / agent_slug
    md = agent_dir / "AGENT.md"
    if not md.exists():
        raise SystemExit(f"agent not found: {md}")
    agent_body = md.read_text(encoding="utf-8")
    schema_path = agent_dir / "inputs.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8")) if schema_path.exists() else None
    return agent_body, schema


def validate_inputs(inputs: dict, schema: dict | None, path: Path) -> None:
    if schema is None or jsonschema is None:
        return
    try:
        jsonschema.Draft202012Validator(schema).validate(inputs)
    except jsonschema.ValidationError as exc:
        raise SystemExit(f"fixture inputs fail agent inputs.schema.json: {exc.message} (at {path})")


def read_source_references(inputs: dict) -> dict[str, str]:
    """If inputs reference file paths (source_path, related_paths), read them
    so the agent sees the content, not just the path. Inlining the source is
    what makes this harness work without a live filesystem context."""
    files: dict[str, str] = {}
    candidates: list[str] = []
    sp = inputs.get("source_path")
    if isinstance(sp, str):
        candidates.append(sp)
    rp = inputs.get("related_paths")
    if isinstance(rp, list):
        candidates.extend(p for p in rp if isinstance(p, str))
    for rel in candidates:
        p = (REPO_ROOT / rel).resolve()
        if p.exists() and p.is_file() and str(p).startswith(str(REPO_ROOT)):
            try:
                files[rel] = p.read_text(encoding="utf-8")
            except Exception as exc:
                files[rel] = f"[could not read: {exc}]"
        else:
            files[rel] = "[path does not exist on disk — agent should refuse]"
    return files


def assemble_prompt(
    *,
    agent_slug: str,
    agent_body: str,
    inputs: dict,
    org_stub: dict,
    source_files: dict[str, str],
    envelope_schema: dict,
    refusal_codes_md: str,
    deliverable_contract_md: str,
    run_id: str,
) -> tuple[str, str]:
    """Returns (system_prompt, user_message)."""

    system = f"""You are the `{agent_slug}` agent defined in the SfSkills repo. Your AGENT.md, the shared DELIVERABLE_CONTRACT, the list of canonical refusal codes, and the JSON Schema your output envelope must conform to are all provided below. Follow your AGENT.md exactly.

=== AGENT.md (agents/{agent_slug}/AGENT.md) ===
{agent_body}

=== DELIVERABLE_CONTRACT.md (agents/_shared/DELIVERABLE_CONTRACT.md) ===
{deliverable_contract_md}

=== REFUSAL_CODES.md (agents/_shared/REFUSAL_CODES.md) ===
{refusal_codes_md}

=== output-envelope.schema.json (agents/_shared/schemas/output-envelope.schema.json) ===
{json.dumps(envelope_schema, indent=2)}

=== HARNESS CONSTRAINTS ===
You are being executed inside a batch grading harness, not a live session. You have no tool access. The caller has pre-fetched every file and org probe you would otherwise call — they appear inline in the user message. Do NOT ask follow-up questions. Do NOT claim you need to fetch a file — if a file is relevant and not shown, treat it as unavailable and lower confidence. You MUST return exactly one fenced JSON block matching the envelope schema. No prose outside the fence. The `run_id` MUST be `{run_id}`. The `report_path` MUST be `docs/reports/{agent_slug}/{run_id}.md`. The `envelope_path` MUST be `docs/reports/{agent_slug}/{run_id}.json`. Include the full refactored Apex + test class in `deliverables[]` — do NOT truncate."""

    files_block = ""
    if source_files:
        parts = []
        for rel, content in source_files.items():
            parts.append(f"--- file: {rel} ---\n{content}")
        files_block = "\n\n=== SOURCE FILES (inlined by harness) ===\n" + "\n\n".join(parts)

    org_block = ""
    if org_stub:
        org_block = "\n\n=== ORG STUB (inlined by harness — pretend these came from MCP probes) ===\n" + json.dumps(org_stub, indent=2)

    user = f"""Execute your Plan against the following input packet and return the output envelope.

=== INPUTS (conforms to agents/{agent_slug}/inputs.schema.json) ===
{json.dumps(inputs, indent=2)}{files_block}{org_block}

Return exactly one fenced ```json code block containing the envelope. Nothing else."""

    return system, user


def call_claude(*, api_key: str, model: str, system: str, user: str, max_tokens: int) -> dict:
    body = {
        "model": model,
        "max_tokens": max_tokens,
        "system": system,
        "messages": [{"role": "user", "content": user}],
    }
    base = os.environ.get("ANTHROPIC_API_BASE") or DEFAULT_API_BASE
    req = urllib.request.Request(
        base.rstrip("/") + "/v1/messages",
        data=json.dumps(body).encode("utf-8"),
        headers={
            "content-type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": ANTHROPIC_VERSION,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"Claude API HTTP {exc.code}: {detail}")


_FENCE_RE = re.compile(r"```(?:json)?\s*\n(.*?)\n```", re.DOTALL)


def extract_envelope(raw_text: str) -> dict:
    """Find the first ```json fenced block; fall back to the first { ... } run."""
    m = _FENCE_RE.search(raw_text)
    candidate = m.group(1) if m else None
    if candidate is None:
        start = raw_text.find("{")
        end = raw_text.rfind("}")
        if start == -1 or end == -1 or end < start:
            raise SystemExit("Model response contained no JSON object")
        candidate = raw_text[start : end + 1]
    try:
        return json.loads(candidate)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Envelope JSON did not parse: {exc}\n\nRaw candidate:\n{candidate[:800]}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", required=True, help="Path to a fixture YAML under evals/agents/fixtures/")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"Claude model id (default: {DEFAULT_MODEL})")
    parser.add_argument("--max-tokens", type=int, default=DEFAULT_MAX_TOKENS)
    parser.add_argument("--out-dir", default=None, help="Override output directory")
    parser.add_argument("--no-grade", action="store_true", help="Skip running the grader after execution")
    parser.add_argument(
        "--baseline",
        choices=["off", "auto", "check", "create", "create-force"],
        default="auto",
        help=(
            "Drift detection vs evals/agents/baselines/<agent>/<case>.baseline.json. "
            "'auto' (default) checks if a baseline exists and silently skips otherwise. "
            "'check' fails if no baseline exists. 'create' seeds a missing baseline. "
            "'create-force' overwrites. 'off' disables baselines entirely."
        ),
    )
    parser.add_argument("--dry-run", action="store_true", help="Assemble the prompt and stop — no API call")
    parser.add_argument(
        "--envelope-from",
        default=None,
        help="Skip the API call and grade this pre-produced envelope JSON (or markdown "
        "containing a fenced ```json block) instead. Useful when the API key is not "
        "reachable from this process but a model response is available out-of-band.",
    )
    args = parser.parse_args()

    fixture_path = Path(args.fixture).resolve()
    fixture = load_fixture(fixture_path)
    ev = fixture["eval"]
    agent_slug = ev["agent"]
    case_id = ev.get("id", fixture_path.stem).replace("/", "__")

    agent_body, inputs_schema = load_agent(agent_slug)
    inputs = fixture.get("inputs") or {}
    org_stub = fixture.get("org_stub") or {}

    validate_inputs(inputs, inputs_schema, fixture_path)
    source_files = read_source_references(inputs)

    envelope_schema = json.loads(ENVELOPE_SCHEMA_PATH.read_text(encoding="utf-8"))
    refusal_md = REFUSAL_CODES_PATH.read_text(encoding="utf-8") if REFUSAL_CODES_PATH.exists() else ""
    deliverable_md = DELIVERABLE_CONTRACT_PATH.read_text(encoding="utf-8") if DELIVERABLE_CONTRACT_PATH.exists() else ""

    today = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d")
    run_id = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = Path(args.out_dir) if args.out_dir else REPO_ROOT / "docs" / "validation" / f"agent_executions_{today}"
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = f"{agent_slug}__{case_id.replace(agent_slug + '__', '')}"

    system_prompt, user_msg = assemble_prompt(
        agent_slug=agent_slug,
        agent_body=agent_body,
        inputs=inputs,
        org_stub=org_stub,
        source_files=source_files,
        envelope_schema=envelope_schema,
        refusal_codes_md=refusal_md,
        deliverable_contract_md=deliverable_md,
        run_id=run_id,
    )

    prompt_path = out_dir / f"{stem}.prompt.txt"
    # Only write prompt.txt when we'll actually call the model — in --envelope-from
    # mode we're grading a prior run and overwriting prompt.txt would decouple the
    # pinned run_id from the one inside the envelope.
    if not args.envelope_from:
        prompt_path.write_text(f"=== SYSTEM ===\n{system_prompt}\n\n=== USER ===\n{user_msg}\n", encoding="utf-8")

    if args.dry_run:
        print(f"Dry run — prompt assembled at {prompt_path.relative_to(REPO_ROOT)}")
        print(f"System length: {len(system_prompt)} chars")
        print(f"User length:   {len(user_msg)} chars")
        return 0

    if args.envelope_from:
        raw_text = Path(args.envelope_from).read_text(encoding="utf-8")
        print(f"[{agent_slug}] grading pre-produced envelope from {args.envelope_from}")
    else:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise SystemExit(
                "ANTHROPIC_API_KEY env var is required (or use --dry-run / --envelope-from <path>)."
            )
        print(f"[{agent_slug}] invoking {args.model} (max_tokens={args.max_tokens})...", flush=True)
        resp = call_claude(
            api_key=api_key,
            model=args.model,
            system=system_prompt,
            user=user_msg,
            max_tokens=args.max_tokens,
        )
        raw_text = "".join(
            block.get("text", "") for block in resp.get("content", []) if block.get("type") == "text"
        )
        usage = resp.get("usage", {})
        stop_reason = resp.get("stop_reason")
        print(f"[{agent_slug}] stop_reason={stop_reason} usage={usage}")

    raw_path = out_dir / f"{stem}.raw.md"
    if not args.envelope_from:
        raw_path.write_text(raw_text, encoding="utf-8")

    envelope = extract_envelope(raw_text)
    envelope_path = out_dir / f"{stem}.envelope.json"
    envelope_path.write_text(json.dumps(envelope, indent=2), encoding="utf-8")
    print(f"[{agent_slug}] envelope -> {envelope_path.relative_to(REPO_ROOT)}")

    if args.no_grade:
        return 0

    grader = REPO_ROOT / "evals" / "agents" / "scripts" / "run_agent_evals.py"
    result = subprocess.run(
        [
            sys.executable,
            str(grader),
            "--grade",
            "--file",
            str(fixture_path),
            "--envelope",
            str(envelope_path),
        ],
        capture_output=True,
        text=True,
    )
    grade_path = out_dir / f"{stem}.grade.txt"
    grade_path.write_text(
        f"exit_code: {result.returncode}\n--- stdout ---\n{result.stdout}\n--- stderr ---\n{result.stderr}\n",
        encoding="utf-8",
    )
    print(f"[{agent_slug}] grader exit={result.returncode} -> {grade_path.relative_to(REPO_ROOT)}")
    print(result.stdout)
    if result.stderr.strip():
        print(result.stderr, file=sys.stderr)

    baseline_exit = run_baseline_step(
        mode=args.baseline,
        fixture_path=fixture_path,
        envelope_path=envelope_path,
        agent_slug=agent_slug,
        model=args.model,
    )
    return result.returncode or baseline_exit


def run_baseline_step(
    *,
    mode: str,
    fixture_path: Path,
    envelope_path: Path,
    agent_slug: str,
    model: str,
) -> int:
    if mode == "off":
        return 0

    baseline_tool = REPO_ROOT / "scripts" / "baseline_agent_envelope.py"
    if not baseline_tool.exists():
        print(f"[{agent_slug}] baseline tool missing — skipping baseline step", file=sys.stderr)
        return 0

    baselines_dir = REPO_ROOT / "evals" / "agents" / "baselines"
    baseline_file = baselines_dir / agent_slug / f"{fixture_path.stem}.baseline.json"

    if mode == "auto":
        if not baseline_file.exists():
            print(f"[{agent_slug}] no baseline yet at {baseline_file.relative_to(REPO_ROOT)} — skipping (use --baseline=create to seed)")
            return 0
        sub_args = ["check", "--fixture", str(fixture_path), "--envelope", str(envelope_path)]
    elif mode == "check":
        sub_args = ["check", "--fixture", str(fixture_path), "--envelope", str(envelope_path)]
    elif mode == "create":
        sub_args = ["create", "--fixture", str(fixture_path), "--envelope", str(envelope_path), "--model", model]
    elif mode == "create-force":
        sub_args = ["create", "--fixture", str(fixture_path), "--envelope", str(envelope_path), "--model", model, "--force"]
    else:
        return 0

    res = subprocess.run([sys.executable, str(baseline_tool), *sub_args], capture_output=True, text=True)
    if res.stdout:
        print(res.stdout, end="")
    if res.stderr.strip():
        print(res.stderr, file=sys.stderr, end="")
    return res.returncode


if __name__ == "__main__":
    sys.exit(main())
