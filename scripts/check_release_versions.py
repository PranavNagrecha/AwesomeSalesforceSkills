#!/usr/bin/env python3
"""Fail when plugin/MCP versions disagree across canonical sources.

stdlib only. Importable from tests and runnable as
``python3 scripts/check_release_versions.py``.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGIN_RE = re.compile(r'^PLUGIN_VERSION\s*=\s*["\']([^"\']+)["\']', re.M)
PYPROJECT_RE = re.compile(r'^version\s*=\s*["\']([^"\']+)["\']', re.M)
DUNDER_RE = re.compile(r'^__version__\s*=\s*["\']([^"\']+)["\']', re.M)


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def collect_versions() -> dict[str, str]:
    plugin = PLUGIN_RE.search(_read("scripts/build_plugin.py"))
    pyproject = PYPROJECT_RE.search(_read("mcp/sfskills-mcp/pyproject.toml"))
    dunder = DUNDER_RE.search(_read("mcp/sfskills-mcp/src/sfskills_mcp/__init__.py"))
    plugin_json = json.loads(_read(".claude-plugin/plugin.json"))
    marketplace = json.loads(_read(".claude-plugin/marketplace.json"))
    market_plugin = None
    plugins = marketplace.get("plugins") or marketplace.get("marketplace", {}).get("plugins")
    if isinstance(plugins, list) and plugins:
        market_plugin = plugins[0].get("version")
    elif isinstance(marketplace.get("plugins"), dict):
        market_plugin = next(iter(marketplace["plugins"].values()), {}).get("version")
    # marketplace.json in this repo is a Claude marketplace file
    if market_plugin is None:
        for key in ("version",):
            if key in marketplace:
                market_plugin = marketplace[key]
                break
        # nested plugin entries
        for item in marketplace.get("plugins", []) if isinstance(marketplace.get("plugins"), list) else []:
            if isinstance(item, dict) and item.get("version"):
                market_plugin = item["version"]
                break
    return {
        "plugin_source": plugin.group(1) if plugin else "",
        "plugin_manifest": str(plugin_json.get("version") or ""),
        "plugin_marketplace": str(market_plugin or ""),
        "mcp_pyproject": pyproject.group(1) if pyproject else "",
        "mcp_dunder": dunder.group(1) if dunder else "",
    }


def collect_issues() -> list[str]:
    versions = collect_versions()
    issues: list[str] = []
    if not versions["plugin_source"]:
        issues.append("scripts/build_plugin.py has no PLUGIN_VERSION")
    if versions["plugin_source"] != versions["plugin_manifest"]:
        issues.append(
            f"plugin source {versions['plugin_source']!r} != "
            f".claude-plugin/plugin.json {versions['plugin_manifest']!r}"
        )
    if versions["plugin_marketplace"] and versions["plugin_marketplace"] != versions["plugin_source"]:
        issues.append(
            f"plugin source {versions['plugin_source']!r} != "
            f"marketplace.json {versions['plugin_marketplace']!r}"
        )
    if versions["mcp_pyproject"] != versions["mcp_dunder"]:
        issues.append(
            f"MCP pyproject {versions['mcp_pyproject']!r} != "
            f"sfskills_mcp.__version__ {versions['mcp_dunder']!r}"
        )
    changelog = _read("CHANGELOG.md")
    plugin_ver = versions["plugin_source"]
    mcp_ver = versions["mcp_pyproject"]
    if plugin_ver and f"Plugin {plugin_ver}" not in changelog and f"[Plugin {plugin_ver}]" not in changelog:
        issues.append(f"CHANGELOG.md has no heading for Plugin {plugin_ver}")
    if mcp_ver and f"[{mcp_ver}]" not in changelog:
        issues.append(f"CHANGELOG.md has no heading for [{mcp_ver}]")
    readme = _read("README.md")
    # Current-facing README must not still advertise the previous MCP patch
    # as the live server version once the dunder has moved on.
    if mcp_ver:
        m = re.search(r"The server reports version \*\*([0-9.]+)\*\*", readme)
        if m and m.group(1) != mcp_ver:
            issues.append(
                f"README.md advertises MCP {m.group(1)} but __version__ is {mcp_ver}"
            )
    return issues


def main(argv: list[str] | None = None) -> int:
    argparse.ArgumentParser(description="Version-consistency gate").parse_args(argv)
    issues = collect_issues()
    versions = collect_versions()
    print(
        "plugin={plugin_source} mcp={mcp_pyproject} "
        "plugin.json={plugin_manifest} marketplace={plugin_marketplace} "
        "__version__={mcp_dunder}".format(**versions)
    )
    for issue in issues:
        print(f"ERROR {issue}")
    if issues:
        print(f"{len(issues)} version-consistency error(s).")
        return 1
    print("Version sources agree.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
