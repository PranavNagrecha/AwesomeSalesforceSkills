# Research method and evidence discipline

## Scope

The product thesis was researched against the existing SfSkills repository, current official Salesforce developer/tooling material, current agent-host capabilities, open agent standards, security guidance, and public competitor product material as of 2026-08-19.

## Source priority

1. Official Salesforce, host, standards-body, or protocol documentation.
2. Official vendor product/help material for competitive feature statements.
3. Public repositories and release notes for implementation behavior.
4. Community reports only for risks or host defects, never as the sole basis of a product guarantee.

## Confidence rules

- “Current platform behavior” requires a dated source record and must be rechecked during implementation/release.
- Vendor capability statements are treated as vendor claims unless independently tested.
- Market/adoption outcomes are hypotheses until measured with a defined cohort.
- No broad market-share or accuracy claim is part of the specification.
- Host file shape never substitutes for actual host execution.

## Repository method

The uploaded repository snapshot was structurally scanned across skills, agents, commands, MCP registrations, schemas, validators, generated packages, tests, docs, and routing. Current inventories are recorded under `migration/catalogs/`. The framework preserves those assets and assigns V2 dispositions rather than assuming a greenfield rewrite.

## Research refresh

Before each release candidate, recheck all source records with `status=current` that affect shipped adapters, Salesforce APIs/CLI, safety controls, or public claims. Mark changed/superseded sources and update affected requirements/tests/ADRs.
