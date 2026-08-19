"""Focused /sfskills-doctor checks. Not a general runtime CLI."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]


def _status(ok: bool, *, detail: str, extra: dict[str, Any] | None = None) -> dict[str, Any]:
    row = {"status": "ok" if ok else "error", "detail": detail}
    if extra:
        row.update(extra)
    return row


def _plugin_version(root: Path) -> str:
    manifest = root / "dist" / "cursor" / "awesome-salesforce-skills" / ".cursor-plugin" / "plugin.json"
    source = root / "integrations" / "cursor" / "plugin.json"
    for path in (manifest, source):
        if path.is_file():
            try:
                return str(json.loads(path.read_text(encoding="utf-8")).get("version") or "unknown")
            except json.JSONDecodeError:
                return "invalid"
    return "missing"


def _index_state(root: Path) -> dict[str, Any]:
    path = root / "vector_index" / "lexical.sqlite"
    if not path.is_file():
        return {
            "status": "index_missing",
            "detail": "vector_index/lexical.sqlite is absent. Run python3 scripts/bootstrap.py",
            "path": str(path),
        }
    age = path.stat().st_mtime
    return {"status": "ok", "detail": "lexical index present", "path": str(path), "mtime": age}


def _sf_cli() -> dict[str, Any]:
    binary = os.environ.get("SFSKILLS_SF_BIN") or shutil.which("sf")
    if not binary:
        return _status(False, detail="Salesforce CLI (sf) not found on PATH")
    try:
        completed = subprocess.run(  # noqa: S603
            [binary, "--version"],
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return _status(False, detail=f"sf --version failed: {exc}")
    version = (completed.stdout or completed.stderr or "").strip().splitlines()[:1]
    return _status(True, detail=version[0] if version else "sf present", extra={"binary": binary})


def _org_aliases() -> dict[str, Any]:
    binary = os.environ.get("SFSKILLS_SF_BIN") or shutil.which("sf")
    if not binary:
        return {"status": "error", "detail": "sf CLI missing; cannot list aliases", "aliases": []}
    try:
        completed = subprocess.run(  # noqa: S603
            [binary, "org", "list", "--json"],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"status": "error", "detail": str(exc), "aliases": []}
    try:
        payload = json.loads(completed.stdout or "{}")
    except json.JSONDecodeError:
        return {"status": "error", "detail": "sf org list did not return JSON", "aliases": []}
    result = payload.get("result") if isinstance(payload, dict) else {}
    aliases: list[dict[str, Any]] = []
    for bucket in ("nonScratchOrgs", "scratchOrgs", "sandboxes", "devHubs", "other"):
        for row in result.get(bucket) or []:
            if not isinstance(row, dict):
                continue
            aliases.append(
                {
                    "alias": row.get("alias") or row.get("username"),
                    "is_default": bool(row.get("isDefaultUsername") or row.get("isDefaultDevHubUsername")),
                    "connected": bool(row.get("connectedStatus") == "Connected" or row.get("connectedStatus") is None),
                    "kind": bucket,
                }
            )
    default = next((a["alias"] for a in aliases if a.get("is_default")), None)
    return {
        "status": "ok" if aliases else "warn",
        "detail": f"{len(aliases)} aliases (no secrets)",
        "aliases": aliases,
        "default_target_org": default,
    }


def _mcp_entrypoint(root: Path) -> dict[str, Any]:
    server = root / "mcp" / "sfskills-mcp" / "src" / "sfskills_mcp" / "server.py"
    if server.is_file():
        return _status(True, detail=str(server.relative_to(root)))
    return _status(False, detail="mcp/sfskills-mcp/src/sfskills_mcp/server.py missing")


def _python_deps() -> dict[str, Any]:
    missing: list[str] = []
    try:
        import yaml  # noqa: F401
    except ImportError:
        missing.append("pyyaml")
    # mcp is optional for doctor itself
    return {
        "status": "ok" if not missing else "warn",
        "detail": "required doctor deps present" if not missing else f"optional missing: {missing}",
        "executable": sys.executable,
        "version": sys.version.split()[0],
        "missing": missing,
    }


def _plugin_install(root: Path) -> dict[str, Any]:
    built = (root / "dist" / "cursor" / "awesome-salesforce-skills" / ".cursor-plugin" / "plugin.json").is_file()
    home = Path.home() / ".cursor" / "plugins" / "awesome-salesforce-skills"
    linked = home.is_symlink() or home.is_dir()
    return {
        "status": "ok" if built else "warn",
        "detail": "plugin built" if built else "plugin not built — run python3 scripts/build_cursor_plugin.py",
        "built": built,
        "user_install_present": linked,
        "user_install_path": str(home),
    }


def run_doctor(root: Path | None = None) -> dict[str, Any]:
    repo = root or REPO_ROOT
    checks = {
        "repo": _status((repo / "AGENT_RULES.md").is_file(), detail=str(repo)),
        "plugin_version": {"status": "ok", "detail": _plugin_version(repo)},
        "plugin_install": _plugin_install(repo),
        "python": _python_deps(),
        "mcp_entrypoint": _mcp_entrypoint(repo),
        "salesforce_cli": _sf_cli(),
        "org_aliases": _org_aliases(),
        "search_index": _index_state(repo),
    }
    worst = "ok"
    for row in checks.values():
        st = row.get("status")
        if st == "error" or st == "index_missing":
            worst = "error"
            break
        if st == "warn" and worst == "ok":
            worst = "warn"
    return {
        "ok": worst == "ok",
        "overall": worst,
        "checks": checks,
    }
