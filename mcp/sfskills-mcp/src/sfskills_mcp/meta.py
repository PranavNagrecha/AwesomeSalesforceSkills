"""Meta tools for MCP clients.

These tools don't talk to Salesforce. They surface repo conventions and
handle persistence that every consuming AI would otherwise have to
reimplement.

Three tools:

- ``list_deprecated_redirects`` — dict mapping retired agent ids to the
  canonical router invocation. Saves MCP clients from ever routing to a
  deprecation stub.
- ``get_invocation_modes`` — returns ``docs/agent-invocation-modes.md``
  as a tool resource so clients can pick the right channel for the task.
- ``emit_envelope`` — atomic write of the output envelope + paired
  markdown report to ``docs/reports/<agent>/<run_id>.{json,md}``, per
  ``docs/consumer-responsibilities.md``. Every consumer gets the
  persistence contract for free.
"""

from __future__ import annotations

import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any

from . import paths


# --------------------------------------------------------------------------- #
# list_deprecated_redirects                                                    #
# --------------------------------------------------------------------------- #

# Source of truth: agents/_shared/AGENT_DISAMBIGUATION.md plus docs/MIGRATION.md.
# Kept in code (not parsed from markdown) so the JSON contract is stable and
# typo-free; the markdown is the human-readable counterpart.
_DEPRECATED_REDIRECTS: dict[str, dict[str, str]] = {
    "validation-rule-auditor":        {"router": "audit-router",                "flag": "--domain=validation_rule"},
    "picklist-governor":              {"router": "audit-router",                "flag": "--domain=picklist"},
    "record-type-and-layout-auditor": {"router": "audit-router",                "flag": "--domain=record_type_layout"},
    "report-and-dashboard-auditor":   {"router": "audit-router",                "flag": "--domain=report_dashboard"},
    "reports-and-dashboards-folder-sharing-auditor":
                                      {"router": "audit-router",                "flag": "--domain=reports_dashboards_folder_sharing"},
    "approval-process-auditor":       {"router": "audit-router",                "flag": "--domain=approval_process"},
    "case-escalation-auditor":        {"router": "audit-router",                "flag": "--domain=case_escalation"},
    "lightning-record-page-auditor":  {"router": "audit-router",                "flag": "--domain=lightning_record_page"},
    "list-view-and-search-layout-auditor":
                                      {"router": "audit-router",                "flag": "--domain=list_view_search_layout"},
    "my-domain-and-session-security-auditor":
                                      {"router": "audit-router",                "flag": "--domain=my_domain_session_security"},
    "org-drift-detector":             {"router": "audit-router",                "flag": "--domain=org_drift"},
    "prompt-library-governor":        {"router": "audit-router",                "flag": "--domain=prompt_library"},
    "quick-action-and-global-action-auditor":
                                      {"router": "audit-router",                "flag": "--domain=quick_action"},
    "sharing-audit-agent":            {"router": "audit-router",                "flag": "--domain=sharing"},
    "field-audit-trail-and-history-tracking-governor":
                                      {"router": "audit-router",                "flag": "--domain=field_audit_trail_history_tracking"},
    "workflow-rule-to-flow-migrator": {"router": "automation-migration-router", "flag": "--source-type=wf_rule"},
    "process-builder-to-flow-migrator":
                                      {"router": "automation-migration-router", "flag": "--source-type=process_builder"},
    "approval-to-flow-orchestrator-migrator":
                                      {"router": "automation-migration-router", "flag": "--source-type=approval_process"},
    "workflow-and-pb-migrator":       {"router": "automation-migration-router", "flag": "--source-type=auto"},
}


def list_deprecated_redirects() -> dict[str, Any]:
    """Return the full map of retired agent ids → canonical router + flag.

    MCP clients should call this once per session and use the result to
    redirect any user request matching a deprecated id before calling
    ``get_agent``. A caller that blindly asks for ``get_agent("validation-rule-auditor")``
    will still receive the deprecation stub; the map prevents that.
    """
    return {
        "count": len(_DEPRECATED_REDIRECTS),
        "redirects": _DEPRECATED_REDIRECTS,
        "source": "agents/_shared/AGENT_DISAMBIGUATION.md + docs/MIGRATION.md",
    }


# --------------------------------------------------------------------------- #
# get_invocation_modes                                                         #
# --------------------------------------------------------------------------- #

def get_invocation_modes() -> dict[str, Any]:
    """Return ``docs/agent-invocation-modes.md`` as a tool resource.

    The doc lists the 15 channels this library can be consumed through
    (MCP, slash commands, bundle export, informal chat, subagents, etc.)
    with a Quick Picker table. MCP clients that haven't read the doc
    should call this tool once at session start and use the Quick Picker
    guidance to route the user's request to the right channel.

    The ``canonical_channel`` field names the channel the library
    recommends for production use — currently MCP itself. That steer is
    deliberate; the library is doubling down on MCP adoption.
    """
    doc_path = paths.repo_root() / "docs" / "agent-invocation-modes.md"
    if not doc_path.exists():
        return {
            "error": f"Invocation modes doc not found at {doc_path}",
        }
    body = doc_path.read_text(encoding="utf-8")
    return {
        "path": "docs/agent-invocation-modes.md",
        "canonical_channel": "mcp",
        "num_channels": 15,
        "markdown": body,
    }


# --------------------------------------------------------------------------- #
# emit_envelope                                                                #
# --------------------------------------------------------------------------- #

_AGENT_ID_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_RUN_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9:\-_T.Z]{7,}$")  # ≥8 chars, safe


def emit_envelope(
    agent: str,
    run_id: str,
    envelope: dict[str, Any],
    markdown_report: str,
    overwrite: bool = False,
) -> dict[str, Any]:
    """Atomically write the envelope JSON + paired markdown report for a
    runtime agent run, following ``docs/consumer-responsibilities.md``.

    Convention:
      - ``docs/reports/<agent>/<run_id>.json`` — the envelope
      - ``docs/reports/<agent>/<run_id>.md``   — the human-readable report

    Atomicity is per-file (write to temp + os.replace). If either write
    fails the caller MUST clean up — the tool returns an error dict with
    ``partial_write: true`` so the consumer can take action.

    Overwrite protection is ON by default. Runtime agents are supposed to
    produce one envelope per run; overwriting is usually a bug.
    """
    if not _AGENT_ID_PATTERN.match(agent):
        return {"error": f"agent must match /^[a-z0-9]+(?:-[a-z0-9]+)*$/ (got: {agent!r})"}
    if not _RUN_ID_PATTERN.match(run_id):
        return {"error": f"run_id must be ≥8 chars and safe for a filename (got: {run_id!r})"}
    if not isinstance(envelope, dict):
        return {"error": "envelope must be a JSON object"}
    if not isinstance(markdown_report, str):
        return {"error": "markdown_report must be a string"}

    # Light shape check: ensure the envelope's own report_path / envelope_path
    # agree with where we're writing, so downstream tooling doesn't end up
    # with a mismatch.
    expected_md = f"docs/reports/{agent}/{run_id}.md"
    expected_js = f"docs/reports/{agent}/{run_id}.json"
    if envelope.get("report_path") and envelope["report_path"] != expected_md:
        return {
            "error": (
                f"envelope.report_path ({envelope['report_path']}) does not match "
                f"convention ({expected_md}). Fix the envelope before emitting."
            )
        }
    if envelope.get("envelope_path") and envelope["envelope_path"] != expected_js:
        return {
            "error": (
                f"envelope.envelope_path ({envelope['envelope_path']}) does not match "
                f"convention ({expected_js}). Fix the envelope before emitting."
            )
        }

    # Fill in the canonical paths if the caller omitted them — cheap help.
    envelope.setdefault("agent", agent)
    envelope.setdefault("run_id", run_id)
    envelope.setdefault("report_path", expected_md)
    envelope.setdefault("envelope_path", expected_js)

    repo = paths.repo_root()
    target_dir = repo / "docs" / "reports" / agent
    target_dir.mkdir(parents=True, exist_ok=True)
    md_path = target_dir / f"{run_id}.md"
    js_path = target_dir / f"{run_id}.json"

    if not overwrite and (md_path.exists() or js_path.exists()):
        return {
            "error": (
                f"run_id {run_id!r} already written under {target_dir}. "
                f"Set overwrite=true to replace, or pick a new run_id."
            )
        }

    written: list[str] = []
    try:
        # Write JSON via temp + rename.
        _atomic_write_text(js_path, json.dumps(envelope, indent=2, sort_keys=True))
        written.append(str(js_path))
        # Write markdown.
        _atomic_write_text(md_path, markdown_report)
        written.append(str(md_path))
    except Exception as e:  # noqa: BLE001 — surface anything as a dict
        # If we wrote the JSON but failed the markdown, flag a partial write
        # so the caller can clean up.
        return {
            "error": f"emit_envelope failed: {type(e).__name__}: {e}",
            "partial_write": len(written) == 1,
            "written_before_failure": written,
        }

    return {
        "wrote": [
            {"kind": "envelope_json", "path": str(js_path.relative_to(repo))},
            {"kind": "markdown_report", "path": str(md_path.relative_to(repo))},
        ],
        "agent": agent,
        "run_id": run_id,
        "report_path": expected_md,
        "envelope_path": expected_js,
    }


def _atomic_write_text(path: Path, content: str) -> None:
    """Write ``content`` to ``path`` atomically on POSIX.

    Writes to a sibling temp file in the same directory (same filesystem),
    fsyncs, then ``os.replace``. On Windows ``os.replace`` is also atomic
    when source and dest are on the same volume.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=str(path.parent),
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(content)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)
    except Exception:
        # Clean up temp on failure.
        try:
            os.unlink(tmp)
        except FileNotFoundError:
            pass
        raise
