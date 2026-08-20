# Current repository assessment

## Verified baseline

The uploaded repository snapshot contains:

- 1,034 skill packages across 11 domains;
- 76 canonical agent definitions, including 48 active stable runtime agents;
- 67 slash commands;
- 38 MCP tools;
- 272 passing unit tests;
- 76 agent definitions validating with zero errors and 12 warnings;
- deterministic plugin and export drift checks passing.

Detailed generated inventory is under `migration/catalogs/` and exact baseline logs are under `baseline/logs/`.

## Strengths to preserve

1. **Tiered discovery.** The repository already avoids placing the full catalog into startup context.
2. **Operational depth.** Skills contain examples, anti-patterns, references, and concrete Salesforce guidance.
3. **Agent contracts.** Runtime/build classes, modes, input schemas, org requirements, output envelopes, citations, and templates already exist.
4. **Read-only bias.** The MCP surface is predominantly observational.
5. **Deterministic build discipline.** Validators, fixtures, exports, and generated plugin checks provide a strong foundation.

## Product gaps

1. Host-native Cursor distribution is weaker than the repository’s knowledge model.
2. Current agents often declare broad execution-time dependency sets; the stable runtime average is about 20.5 distinct skill references, with a maximum of 45.
3. Commands are mostly prose contracts rather than typed, portable product APIs.
4. Structural and factuality QA do not yet prove actual host behavior against planted Salesforce ground truth.
5. Tool outputs are not uniformly normalized into a common evidence graph.
6. Independent evidence review is a convention rather than a hard product gate.
7. Context compaction, task switching, and cross-run contamination are not comprehensively tested.
8. The repository measures inventory more readily than user outcomes.

## Migration principle

Do not rewrite the repository merely to make it look architecturally pure. Preserve working knowledge and compatibility surfaces. Introduce V2 contracts when a shipped product uses them, then migrate existing agents on touch or when quality data justifies it.
