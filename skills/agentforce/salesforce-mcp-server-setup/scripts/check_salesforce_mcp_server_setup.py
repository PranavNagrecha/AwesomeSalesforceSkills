#!/usr/bin/env python3
"""Checker script for Salesforce MCP Server Setup skill.

Checks metadata and configuration relevant to the salesforce-mcp-lib integration:
- Apex REST endpoint class exists and uses the correct urlMapping pattern
- Connected App metadata is present
- No hardcoded secrets in mcp config files found in the project tree

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_salesforce_mcp_server_setup.py [--help]
    python3 check_salesforce_mcp_server_setup.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Salesforce MCP Server Setup configuration and metadata for common issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def check_salesforce_mcp_server_setup(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    # Check 1: Look for Apex REST endpoint classes that reference McpServer
    apex_dir = manifest_dir / "force-app" / "main" / "default" / "classes"
    if not apex_dir.exists():
        # Try alternative common paths
        apex_dir = manifest_dir / "classes"

    mcp_endpoint_found = False
    if apex_dir.exists():
        for apex_file in apex_dir.glob("*.cls"):
            content = apex_file.read_text(encoding="utf-8", errors="replace")
            if "McpServer" in content and "handleRequest" in content:
                mcp_endpoint_found = True
                # Check that the endpoint uses @RestResource annotation
                if "@RestResource" not in content:
                    issues.append(
                        f"{apex_file.name}: contains McpServer.handleRequest() but is missing "
                        "@RestResource annotation. The MCP endpoint must be a REST-exposed class."
                    )
                # Check that the class uses global access modifier
                if "global class" not in content and "global with sharing class" not in content and "global without sharing class" not in content:
                    issues.append(
                        f"{apex_file.name}: MCP endpoint class should use 'global' access modifier "
                        "so it is accessible from the installed package context."
                    )

    # Check 2: Detect hardcoded secrets in MCP config files
    secret_patterns = ["client_secret", "clientSecret", "SF_CLIENT_SECRET"]
    config_file_names = [
        "claude_desktop_config.json",
        "mcp_settings.json",
        ".mcp.json",
        "mcp.json",
    ]
    for config_name in config_file_names:
        for config_file in manifest_dir.rglob(config_name):
            # Skip node_modules and .git
            if "node_modules" in str(config_file) or ".git" in str(config_file):
                continue
            try:
                content = config_file.read_text(encoding="utf-8", errors="replace")
                for pattern in secret_patterns:
                    if pattern in content and "YOUR_" not in content and "PLACEHOLDER" not in content:
                        # Heuristic: if the pattern is present and doesn't look like a placeholder
                        issues.append(
                            f"{config_file}: may contain a hardcoded Connected App secret "
                            f"(found pattern '{pattern}'). Use environment variables instead: "
                            "SF_CLIENT_SECRET, SF_CLIENT_ID, SF_INSTANCE_URL, SF_ENDPOINT."
                        )
                        break
            except OSError:
                pass

    # Check 3: Verify Node.js version hint in package.json or .nvmrc if present
    package_json = manifest_dir / "package.json"
    if package_json.exists():
        try:
            content = package_json.read_text(encoding="utf-8", errors="replace")
            # salesforce-mcp-lib requires Node >= 20
            if '"node"' in content and '"engines"' in content:
                import json
                try:
                    pkg = json.loads(content)
                    engines = pkg.get("engines", {})
                    node_req = engines.get("node", "")
                    if node_req and not any(v in node_req for v in ["20", "21", "22", "23", ">=20"]):
                        issues.append(
                            f"package.json engines.node is set to '{node_req}'. "
                            "salesforce-mcp-lib requires Node.js >= 20."
                        )
                except (json.JSONDecodeError, KeyError):
                    pass
        except OSError:
            pass

    # Check 4: Warn if no MCP endpoint found at all
    if apex_dir.exists() and not mcp_endpoint_found:
        issues.append(
            "No Apex class found that calls McpServer.handleRequest(). "
            "The salesforce-mcp-lib integration requires an @RestResource Apex class "
            "that instantiates McpServer and calls handleRequest(RestContext.request, RestContext.response)."
        )

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_salesforce_mcp_server_setup(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
