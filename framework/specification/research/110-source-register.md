# Source register — research freeze 2026-08-19

The canonical external source records are JSON files under `research/sources/` and the generated human index is `catalogs/SOURCE_CATALOG.md`.

## Rules

- Release-sensitive implementation and public claims must recheck affected sources.
- Official publisher documentation is preferred for platform/host behavior.
- Vendor pages support descriptions of vendor capabilities, not independent effectiveness claims.
- Community reports can identify host risks but cannot establish a guaranteed behavior.
- Changed or unavailable sources are marked `review-due`, `stale`, `superseded`, or `unavailable`; they are not silently deleted.
- Source changes affecting authority, host enforcement, schemas, or product behavior require updated tests and potentially an ADR.

## Primary source groups

### Salesforce

`SRC-SF-DX-MCP`, `SRC-SF-HEADLESS-360`, `SRC-SF-HEADLESS-360-BLOG`, `SRC-SF-CODE-ANALYZER-SKILLS`, `SRC-SF-CODE-ANALYZER-MCP-TRANSITION`, `SRC-SF-AGENTFORCE-BUILDER-2026`, `SRC-SF-AGENT-TESTING-CLI`, `SRC-SF-AGENT-TEST-RUN-EVAL`, `SRC-SF-AGENTLENS`, `SRC-SF-VIBES-2026`, `SRC-SF-WAF`, `SRC-SF-DEVOPS-CENTER`.

### Hosts and standards

`SRC-CURSOR-PLUGINS`, `SRC-CURSOR-CUSTOMIZE`, `SRC-CURSOR-SKILLS`, `SRC-CURSOR-SUBAGENTS`, `SRC-CURSOR-HOOKS`, `SRC-CURSOR-CLOUD-AGENTS`, `SRC-CLAUDE-PLUGINS`, `SRC-VSCODE-SKILLS`, `SRC-AGENT-PLUGINS`, `SRC-A2A-1`, `SRC-MCP-ANNOTATIONS`, `SRC-NIST-AGENTS`, `SRC-OWASP-AGENTIC`.

### Competitive positioning

`SRC-GEARSET-AI`, `SRC-GEARSET-ORG-INTELLIGENCE`, `SRC-COPADO-AGENTIA`, `SRC-ELEMENTS-ORG-INTELLIGENCE`, `SRC-SALTO-SALESFORCE`.

Run `python3 scripts/build_catalogs.py` after adding or changing source records.
