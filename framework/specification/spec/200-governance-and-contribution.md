# SFAEF-200 — Governance, ownership, and contribution

## Ownership

Each product, tool, schema, adapter, skill domain, and scenario requires an owner or explicit unowned status. Ownership includes source freshness, tests, security review, and deprecation.

## Requirements

SFAEF-200-001. Material architectural decisions MUST be recorded as ADRs.

SFAEF-200-002. A contribution that changes product behavior MUST identify affected requirements and scenarios.

SFAEF-200-003. New skills require source governance and anti-pattern depth; new products require a user job, evidence path, output contract, and evaluation plan.

SFAEF-200-004. New subagents require proof that isolated context improves quality or control.

SFAEF-200-005. New MCP tools require threat analysis, permission class, bounded output, normalization, and adversarial tests.

SFAEF-200-006. New schemas require an active consumer, validator, and compatibility plan.

SFAEF-200-007. Scenario labels must be reviewed independently of the implementation under test.

## Decision authority

- Product owner: product scope, experience, release claim, market priority.
- Architecture owner: contract consistency, trust boundaries, host portability.
- Salesforce domain owner: platform correctness and source currency.
- Security owner: authority, policy, redaction, threat model.
- QA owner: benchmark truth, thresholds, reproducibility.

One person may hold multiple roles in an early project, but decisions and evidence remain explicit.

## Community model

Contributions should be possible at multiple levels:

- skill/source updates;
- evidence fixtures;
- known-truth scenarios;
- product/context improvements;
- host adapters;
- policy/security tests;
- benchmark analyses.
