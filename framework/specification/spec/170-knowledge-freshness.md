# SFAEF-170 — Knowledge freshness and release intelligence

## Source tiers

1. Official Salesforce documentation, release notes, CLI/MCP source, and product references.
2. Standards bodies and official host documentation.
3. Vendor documentation for integration/competitive behavior.
4. High-quality community sources, clearly labelled.
5. Historical or anecdotal sources, never sole support for release-sensitive claims.

## Requirements

SFAEF-170-001. Every release-sensitive skill or product rule MUST record source URL/reference, retrieved date, reviewed date, applicable Salesforce/API/host version, and owner.

SFAEF-170-002. Automated source monitors MAY detect changes but MUST not silently rewrite canonical guidance.

SFAEF-170-003. A source change MUST create a review item linked to affected skills, products, tools, scenarios, and adapters.

SFAEF-170-004. Current official documentation SHOULD be stored as links/digests or permitted snapshots according to licensing; do not copy restricted content wholesale.

SFAEF-170-005. Freshness jobs MUST distinguish source unavailable, changed, reviewed-no-impact, update-required, and superseded.

SFAEF-170-006. Salesforce seasonal release checks SHOULD run against affected flagship scenarios before compatibility is claimed.

## Release radar

The framework should track:

- Salesforce CLI and DX MCP changes;
- metadata/API changes;
- Salesforce seasonal release notes and critical updates;
- Agentforce Builder/Agent Script/testing changes;
- host plugin/skill/subagent/hook format changes;
- MCP, Agent Plugins, Agent Skills, and A2A specification changes;
- security guidance from NIST/OWASP and host vendors.
