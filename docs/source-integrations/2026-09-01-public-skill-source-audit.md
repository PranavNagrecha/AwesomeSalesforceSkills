# Public Salesforce Skill Source Audit — 2026-09-01

## Scope and evidence boundary

The user designated `AwesomeSalesforceSkills-main (3).zip` as the latest canonical repository and supplied five public-source archives. In the active container, only `AwesomeSalesforceSkills-main (1).zip` was available. That fallback archive was inspected and initialized at baseline commit `8107787e378a1c3b5cfcdb2c948318359674f882`; none of the five public archives nor the designated `(3)` archive was available for byte-level inspection.

This integration therefore uses:

1. the inspectable fallback baseline for canonical gap analysis;
2. current public repository pages for source inventory and reported license;
3. committed historical upstream manifests where present;
4. official Salesforce documentation for every accepted Salesforce product claim;
5. original writing only—no upstream prose, scripts, templates, examples, images, or evaluation results were copied.

The machine-readable chain of title is under `registry/source-integrations/` and is validated by `scripts/check_source_integrations.py`.

## Source decisions

| Source | Observed license/status | Decision | Result |
|---|---|---|---|
| `deejay-hub/salesforce-ada-agent-skills` | MIT; active | ADD | Original decision-analysis and citation-first learning products, each with canonical skills, runtime agent, slash command, checkers, and MCP exposure |
| `SalesforceDiariesBySanket/Copilot-Skills-Salesforce` | MIT; active | STOP broad import; DEEPEN focused migration quality | Existing narrow SfSkills owners win; TypeScript migration follows repository-native progressive references, anti-patterns, and deterministic checks |
| `Clientell-Ai/salesforce-skills` | Apache-2.0; active | STOP broad import; REJECT benchmark reuse | Eighteen broad categories already map to the canonical corpus; the upstream +108% benchmark is not an SfSkills result |
| `forcedotcom/sf-skills` | Conflicting Apache-2.0 repository/root declaration and CC-BY-NC-4.0 package metadata; active | ADD/DEEPEN/STOP | Add LWC TypeScript migration and ApexGuru analysis; deepen Code Analyzer; reject a duplicate generic validation loop |
| `Jaganpro/sf-skills` | MIT; archived | STOP/DEFER | Prior per-skill integration manifest already exists; review future successor deltas only from a pinned official snapshot |

## License conflict preserved

`config/upstream-sources/sf-skills.manifest.json` preserves the conflict: repository metadata and the root license indicate Apache-2.0, while package metadata declares CC-BY-NC-4.0 and upstream has an open clarification issue. These surfaces are not silently reconciled. The accepted content uses the conservative clean-room path until a pinned upstream release carries one unambiguous grant.

## Accepted canonical changes

### New skills

- `architect/salesforce-decision-analysis`
- `architect/salesforce-learning-research`
- `admin/salesforce-learning-brief`
- `lwc/lwc-typescript-migration`
- `apex/apexguru-performance-analysis`

### Deepened skill

- `devops/salesforce-code-analyzer` — ApexGuru engine selection, target-org requirements, source-analysis boundary, and MCP lifecycle caveat

### Runtime product surfaces

- `salesforce-decision-facilitator` via `/decide-salesforce`
- `salesforce-learning-guide` via `/learn-salesforce`

Every command is automatically discoverable as an MCP Prompt; every canonical skill is available through `search_skill`, `get_skill`, and `sfskills://skill/{domain__name}`; both agents are available through `get_agent`.

## Rejected duplicate

A generic “agentic validation feedback loop” was not added. Existing canonical deployment, preflight, CI, validation, and rollback packages already own the lifecycle. Adding another umbrella skill would weaken routing and could blur the repository's read-only-versus-mutation authority boundary.

## Unverified lanes

- No current public archive was hashed or diffed.
- No authenticated Salesforce org was available for ApexGuru or live-agent smoke tests.
- No scratch-org deployment was run for LWC TypeScript because the target CLI, extension, API version, and deployment strategy are project-specific prerequisites.
- The Clientell benchmark was not reproduced.
