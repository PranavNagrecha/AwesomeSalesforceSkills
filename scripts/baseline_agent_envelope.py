#!/usr/bin/env python3
"""Create and check structural baselines for agent envelopes.

Closes the drift-detection gap in the agent eval loop:

    fixture YAML  -->  execute_agent_fixture.py  -->  envelope JSON  -->  this tool
                                                                          |
                                                                          +--> create:  write baseline fingerprint
                                                                          +--> check:   compare envelope to baseline,
                                                                                        flag structural drift

A baseline is NOT the full envelope — model prose varies run to run and
would produce noise diffs. The baseline captures the load-bearing
structural fingerprint:

    agent, mode, confidence, refusal.code,
    sorted finding ids, sorted (type,id) citations, sorted follow-up agents,
    multiset of process-observation categories,
    multiset of deliverable kinds, dimensions covered/skipped.

Plus traceability metadata:

    SHA of fixture YAML, SHA of AGENT.md, model id, run timestamp.

The three SHAs let you triangulate why drift happened: did the agent
regress, did the fixture change, or did the model change?

Layout:
    evals/agents/baselines/<agent>/<case>.baseline.json

Usage:

    # Seed (or overwrite) a baseline from a freshly produced envelope.
    python3 scripts/baseline_agent_envelope.py create \\
        --fixture evals/agents/fixtures/apex-refactorer/happy-path.yaml \\
        --envelope docs/validation/agent_executions_2026-04-21/apex-refactorer__happy-path.envelope.json

    # Check the envelope against the existing baseline. Exits 1 on drift.
    python3 scripts/baseline_agent_envelope.py check \\
        --fixture evals/agents/fixtures/apex-refactorer/happy-path.yaml \\
        --envelope docs/validation/agent_executions_2026-04-21/apex-refactorer__happy-path.envelope.json

Stdlib only.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML required (pip install pyyaml)", file=sys.stderr)
    sys.exit(3)

REPO_ROOT = Path(__file__).resolve().parents[1]
AGENTS_DIR = REPO_ROOT / "agents"
BASELINES_DIR = REPO_ROOT / "evals" / "agents" / "baselines"

# Bump when the fingerprint shape changes incompatibly.
FINGERPRINT_SCHEMA_VERSION = 1


def sha_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _counter_pairs(items) -> list[list]:
    """Sorted [[key, count], ...] — JSON-stable (no tuples)."""
    return [list(p) for p in sorted(Counter(items).items())]


def fingerprint(envelope: dict) -> dict:
    """Distill an envelope down to its load-bearing structural shape.

    Anything text-heavy (summary, observation prose, deliverable bodies) is
    excluded — it varies across runs and would generate noise diffs.

    Everything emitted here must round-trip through JSON unchanged (no
    tuples, no sets) so baseline files compare equal to live fingerprints.
    """
    findings = envelope.get("findings") or []
    citations = envelope.get("citations") or []
    followups = envelope.get("followups") or []
    observations = envelope.get("process_observations") or []
    deliverables = envelope.get("deliverables") or []
    refusal = envelope.get("refusal") or {}
    dims_compared = envelope.get("dimensions_compared") or []
    dims_skipped = envelope.get("dimensions_skipped") or []

    citation_pairs = sorted(
        {(c.get("type", ""), c.get("id", "")) for c in citations if isinstance(c, dict)}
    )
    return {
        "schema_version": FINGERPRINT_SCHEMA_VERSION,
        "agent": envelope.get("agent"),
        "mode": envelope.get("mode"),
        "confidence": envelope.get("confidence"),
        "refusal_code": refusal.get("code"),
        "finding_ids": sorted(f.get("id", "") for f in findings if isinstance(f, dict)),
        "finding_severities": _counter_pairs(
            f.get("severity", "") for f in findings if isinstance(f, dict)
        ),
        "citations": [list(p) for p in citation_pairs],
        "followup_agents": sorted(
            f.get("agent", "") for f in followups if isinstance(f, dict)
        ),
        "observation_categories": _counter_pairs(
            o.get("category", "") for o in observations if isinstance(o, dict)
        ),
        "deliverable_kinds": _counter_pairs(
            d.get("kind", "") for d in deliverables if isinstance(d, dict)
        ),
        "dimensions_compared": sorted(d for d in dims_compared if isinstance(d, str)),
        "dimensions_skipped": sorted(
            d.get("dimension", "") for d in dims_skipped if isinstance(d, dict)
        ),
    }


def load_envelope(path: Path) -> dict:
    raw = path.read_text(encoding="utf-8")
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"envelope not valid JSON: {path} ({exc})")


def load_fixture(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or "eval" not in data:
        raise SystemExit(f"fixture missing `eval` block: {path}")
    return data


def baseline_path_for(fixture_path: Path, fixture: dict) -> Path:
    agent_slug = fixture["eval"]["agent"]
    case_stem = fixture_path.stem
    return BASELINES_DIR / agent_slug / f"{case_stem}.baseline.json"


def agent_md_path(agent_slug: str) -> Path:
    return AGENTS_DIR / agent_slug / "AGENT.md"


def build_record(
    *,
    fixture_path: Path,
    fixture: dict,
    envelope: dict,
    envelope_path: Path,
    model: str | None,
) -> dict:
    agent_slug = fixture["eval"]["agent"]
    agent_md = agent_md_path(agent_slug)
    return {
        "schema_version": FINGERPRINT_SCHEMA_VERSION,
        "case_id": fixture["eval"].get("id", fixture_path.stem),
        "agent": agent_slug,
        "fixture_path": str(fixture_path.relative_to(REPO_ROOT)),
        "fixture_sha256": sha_of(fixture_path),
        "agent_md_path": str(agent_md.relative_to(REPO_ROOT)) if agent_md.exists() else None,
        "agent_md_sha256": sha_of(agent_md) if agent_md.exists() else None,
        "envelope_path": str(envelope_path.relative_to(REPO_ROOT))
        if envelope_path.is_relative_to(REPO_ROOT)
        else str(envelope_path),
        "captured_at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "model": model,
        "fingerprint": fingerprint(envelope),
    }


def diff_fingerprints(old: dict, new: dict) -> list[str]:
    """Return human-readable drift lines. Empty list = no drift."""
    drifts: list[str] = []
    keys = sorted(set(old.keys()) | set(new.keys()))
    for k in keys:
        ov, nv = old.get(k), new.get(k)
        if ov == nv:
            continue
        if isinstance(ov, list) and isinstance(nv, list):
            removed = [x for x in ov if x not in nv]
            added = [x for x in nv if x not in ov]
            parts = []
            if removed:
                parts.append(f"removed={removed}")
            if added:
                parts.append(f"added={added}")
            drifts.append(f"  {k}: {' '.join(parts) or 'reordered'}")
        else:
            drifts.append(f"  {k}: {ov!r} -> {nv!r}")
    return drifts


def cmd_create(args) -> int:
    fixture_path = Path(args.fixture).resolve()
    envelope_path = Path(args.envelope).resolve()
    fixture = load_fixture(fixture_path)
    envelope = load_envelope(envelope_path)

    record = build_record(
        fixture_path=fixture_path,
        fixture=fixture,
        envelope=envelope,
        envelope_path=envelope_path,
        model=args.model,
    )

    out = baseline_path_for(fixture_path, fixture)
    if out.exists() and not args.force:
        print(
            f"baseline already exists at {out.relative_to(REPO_ROOT)}; pass --force to overwrite",
            file=sys.stderr,
        )
        return 2
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(record, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    rel = out.relative_to(REPO_ROOT)
    print(f"baseline written: {rel}")
    return 0


def cmd_check(args) -> int:
    fixture_path = Path(args.fixture).resolve()
    envelope_path = Path(args.envelope).resolve()
    fixture = load_fixture(fixture_path)
    envelope = load_envelope(envelope_path)

    baseline_file = baseline_path_for(fixture_path, fixture)
    if not baseline_file.exists():
        if args.allow_missing:
            print(f"no baseline at {baseline_file.relative_to(REPO_ROOT)} — run `create` to seed; allowed")
            return 0
        print(
            f"no baseline at {baseline_file.relative_to(REPO_ROOT)}; run `create` first",
            file=sys.stderr,
        )
        return 2

    baseline = json.loads(baseline_file.read_text(encoding="utf-8"))
    baseline_fp = baseline.get("fingerprint", {})
    current_fp = fingerprint(envelope)
    drifts = diff_fingerprints(baseline_fp, current_fp)

    if not drifts:
        print(f"OK no drift vs {baseline_file.relative_to(REPO_ROOT)}")
        return 0

    print(f"DRIFT vs {baseline_file.relative_to(REPO_ROOT)}:")
    for line in drifts:
        print(line)

    fixture_sha_now = sha_of(fixture_path)
    agent_md = agent_md_path(fixture["eval"]["agent"])
    agent_md_sha_now = sha_of(agent_md) if agent_md.exists() else None
    if baseline.get("fixture_sha256") and baseline["fixture_sha256"] != fixture_sha_now:
        print("  (note: fixture YAML changed since baseline — drift may be expected)")
    if baseline.get("agent_md_sha256") and agent_md_sha_now and baseline["agent_md_sha256"] != agent_md_sha_now:
        print("  (note: AGENT.md changed since baseline — drift may be expected)")
    print(
        "  to accept: rerun with `create --force` after reviewing the diff",
        file=sys.stderr,
    )
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_create = sub.add_parser("create", help="Write a baseline from an envelope.")
    p_create.add_argument("--fixture", required=True)
    p_create.add_argument("--envelope", required=True)
    p_create.add_argument("--model", default=None, help="Model id used to produce envelope (for traceability)")
    p_create.add_argument("--force", action="store_true", help="Overwrite existing baseline")
    p_create.set_defaults(func=cmd_create)

    p_check = sub.add_parser("check", help="Compare envelope to baseline; nonzero exit on drift.")
    p_check.add_argument("--fixture", required=True)
    p_check.add_argument("--envelope", required=True)
    p_check.add_argument(
        "--allow-missing",
        action="store_true",
        help="Treat missing baseline as success (use when seeding a new fixture).",
    )
    p_check.set_defaults(func=cmd_check)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
