"""Meta tools for MCP clients.

These tools don't talk to Salesforce. They surface repo conventions and
handle persistence that every consuming AI would otherwise have to
reimplement.

Four tools:

- ``list_deprecated_redirects`` — dict mapping retired agent ids to the
  canonical router invocation. Saves MCP clients from ever routing to a
  deprecation stub.
- ``get_invocation_modes`` — returns ``docs/agent-invocation-modes.md``
  as a tool resource so clients can pick the right channel for the task.
- ``emit_envelope`` — atomic write of the output envelope + paired
  markdown report to ``docs/reports/<agent>/<run_id>.{json,md}``, per
  ``docs/consumer-responsibilities.md``. Every consumer gets the
  persistence contract for free.
- ``health`` — server diagnostic dump. Returns version, registry size,
  index freshness, agent counts, sf CLI presence + version, repo root.
  Cheap, never raises — useful for "is this MCP wired up correctly?"
  diagnosis without making a real org call.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import paths
from .__init__ import __version__ as _SERVER_VERSION


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
# health                                                                       #
# --------------------------------------------------------------------------- #


def _file_mtime_iso(path: Path) -> str | None:
    if not path.exists():
        return None
    return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat(timespec="seconds")


def _sf_cli_version_or_none() -> str | None:
    """Return ``sf --version`` output (CLI summary string) or ``None`` if
    the binary isn't on PATH or returns nonzero. Never raises — health
    must stay diagnostic-only."""
    binary = os.environ.get("SFSKILLS_SF_BIN") or shutil.which("sf")
    if not binary:
        return None
    try:
        result = subprocess.run(
            [binary, "--version"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode != 0:
        return None
    out = (result.stdout or result.stderr or "").strip().splitlines()
    return out[0] if out else None


def _sf_cli_block() -> dict[str, Any]:
    """Resolve the sf-CLI metadata for ``health``. ``present`` requires the
    binary path to actually exist on disk — pointing ``SFSKILLS_SF_BIN`` at
    a bogus path should not lie about availability."""
    explicit = os.environ.get("SFSKILLS_SF_BIN")
    binary: str | None
    if explicit:
        binary = explicit
        exists = Path(explicit).exists()
    else:
        binary = shutil.which("sf")
        exists = bool(binary)
    return {
        "binary": binary,
        "version": _sf_cli_version_or_none() if exists else None,
        "present": exists,
    }


def _mcp_sdk_version_or_none() -> str | None:
    """Best-effort import + introspect for the installed MCP SDK version."""
    try:
        import importlib.metadata
        return importlib.metadata.version("mcp")
    except Exception:
        return None


def health() -> dict[str, Any]:
    """Return a server diagnostic snapshot for "is this MCP wired up?" checks.

    Never touches the org. Never raises. Each missing piece comes back as
    ``None`` with the rest of the dict intact, so a partial environment
    (no ``sf`` CLI installed yet, registry not built) still yields useful
    information for the user.
    """
    # Lazy local imports to avoid a load-time circular dep with server.py.
    from . import agents as _agents

    classes = _agents._agent_classes()
    repo = paths.repo_root()

    # Skill count from the registry. Cheap — we just open the file and
    # count list entries. ``len(open(...).read().count("...id...:"))`` is
    # not an option because the registry is real JSON.
    registry_path = paths.registry_skills_json()
    skill_count: int | None = None
    if registry_path.exists():
        try:
            payload = json.loads(registry_path.read_text(encoding="utf-8"))
            skill_count = len(payload.get("skills", []))
        except (OSError, ValueError):
            skill_count = None

    return {
        "server_version": _SERVER_VERSION,
        "mcp_sdk_version": _mcp_sdk_version_or_none(),
        "repo_root": str(repo),
        "registry": {
            "path": str(registry_path.relative_to(repo)) if registry_path.exists() else None,
            "skill_count": skill_count,
            "built_at": _file_mtime_iso(registry_path),
        },
        "lexical_index": {
            "path": "vector_index/lexical.sqlite",
            "built_at": _file_mtime_iso(paths.lexical_index_path()),
            "byte_size": (
                paths.lexical_index_path().stat().st_size
                if paths.lexical_index_path().exists() else None
            ),
        },
        "agents": {
            "runtime": sum(1 for v in classes.values() if v == "runtime"),
            "build": sum(1 for v in classes.values() if v == "build"),
            "deprecated": sum(1 for v in classes.values() if v == "deprecated"),
            "unknown": sum(1 for v in classes.values() if v == "unknown"),
            "total": len(classes),
        },
        "sf_cli": _sf_cli_block(),
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
# ≥8 chars, filename-safe. Excludes ':' explicitly: colons are illegal in
# Windows filenames and historically confused HFS+/POSIX path tools. The
# convention is ISO-8601-ish with dashes throughout
# (``2026-05-11T00-13-41Z``). Pre-v0.4.4 the pattern allowed ':' and
# emit_envelope wrote files like ``2026:05:10.json`` to disk — see P1-L
# in .planning/qa-pre-prod-report-2026-05-10.md.
_RUN_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9\-_T.Z]{7,}$")


_SCHEMA_VALIDATOR_CACHE: dict[str, Any] = {}


def _build_envelope_validator() -> Any:
    """Lazily build a jsonschema validator for the output envelope with all
    referenced schemas (observation, citation) pre-loaded into a Registry.

    Returns a validator object whose ``.iter_errors(envelope)`` yields the
    schema errors. None if jsonschema/referencing isn't available (we
    skip validation rather than crash — same fallback discipline as
    embedding_backends.py).
    """
    if "validator" in _SCHEMA_VALIDATOR_CACHE:
        return _SCHEMA_VALIDATOR_CACHE["validator"]
    try:
        from jsonschema import Draft202012Validator
        from referencing import Registry, Resource
        from referencing.jsonschema import DRAFT202012
    except ImportError:
        _SCHEMA_VALIDATOR_CACHE["validator"] = None
        return None
    schemas_dir = paths.repo_root() / "agents" / "_shared" / "schemas"
    if not schemas_dir.exists():
        _SCHEMA_VALIDATOR_CACHE["validator"] = None
        return None
    # Load every schema, key by its $id so cross-schema $ref resolves.
    resources: list[tuple[str, Resource]] = []
    envelope_schema: dict | None = None
    for schema_path in sorted(schemas_dir.glob("*.schema.json")):
        try:
            schema = json.loads(schema_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        schema_id = schema.get("$id")
        if not schema_id:
            continue
        resources.append((schema_id, Resource.from_contents(schema, default_specification=DRAFT202012)))
        if schema_id == "urn:sfskills:output-envelope":
            envelope_schema = schema
    if envelope_schema is None:
        _SCHEMA_VALIDATOR_CACHE["validator"] = None
        return None
    registry = Registry().with_resources(resources)
    validator = Draft202012Validator(envelope_schema, registry=registry)
    _SCHEMA_VALIDATOR_CACHE["validator"] = validator
    return validator


def validate_envelope_schema(envelope: dict[str, Any]) -> list[str]:
    """Return a list of human-readable schema-violation messages for
    ``envelope``. Empty list = valid.

    Returns [] (treated as valid) when the validator can't be built —
    e.g. jsonschema package missing. Callers that want to enforce
    validation should additionally check ``is_validator_available()``.
    """
    validator = _build_envelope_validator()
    if validator is None:
        return []
    errors: list[str] = []
    for err in validator.iter_errors(envelope):
        path = ".".join(str(p) for p in err.absolute_path) or "<root>"
        errors.append(f"{path}: {err.message}")
    return errors


def is_envelope_validator_available() -> bool:
    """True if jsonschema + referencing are installed AND the schemas
    load cleanly. False means validate_envelope_schema returns [] for
    every envelope (skip validation rather than crash)."""
    return _build_envelope_validator() is not None


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

    # Validate the envelope against output-envelope.schema.json BEFORE
    # any write hits disk. Pre-v0.4.4 emit_envelope happily wrote
    # schema-invalid envelopes (P1-J). Validator returns [] when the
    # jsonschema package isn't installed — in that case we skip
    # validation rather than crash (graceful degradation).
    schema_errors = validate_envelope_schema(envelope)
    if schema_errors:
        return {
            "error": "envelope does not match output-envelope.schema.json",
            "schema_errors": schema_errors[:20],  # cap to keep response sane
            "schema_error_count": len(schema_errors),
        }

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
