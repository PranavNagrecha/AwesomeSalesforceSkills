"""SfSkills MCP server — exposes the SfSkills library and live org metadata over MCP."""

# Bumped at the end of each Tier:
#   0.1.0 — Wave-2 baseline (23 tools, hand-coded agent roster)
#   0.1.1 — Tier A: drift fix (frontmatter-driven counts, freshness tests)
#   0.2.0 — Tier B: tool annotations + 68 prompts + 5 resource shapes + probe progress
#   0.3.0 — Tier C: 14 new tools (8 dev-org + 5 search + suggest_agent)
#   0.4.0 — Tier D: health tool + per-tool timeouts + PyPI publish prep
__version__ = "0.4.0"
