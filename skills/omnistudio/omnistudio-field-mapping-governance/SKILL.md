---
name: omnistudio-field-mapping-governance
description: "Govern DataRaptor field mappings to prevent runtime errors when source metadata changes: naming, versioning, and dependency tracking. NOT for DataRaptor authoring fundamentals."
category: omnistudio
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
triggers:
  - "dataraptor field mapping broken"
  - "omnistudio dependency tracking"
  - "dataraptor field renamed"
  - "omnistudio governance"
tags:
  - dataraptor
  - governance
  - metadata
inputs:
  - "org DataRaptor count + field dependency scope"
outputs:
  - "naming standard + dependency report + CI check"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-17
---

# OmniStudio Field Mapping Governance

A DataRaptor breaks silently when a source field is renamed or removed. This skill sets up a dependency report (custom metadata + Tooling API) that lists every field each DR/IP references and runs a CI check on every metadata change, plus a naming standard, a monthly orphan-DR cleanup, and a versioning discipline that keeps prior DR versions active while consumers migrate so governance is a living process, not a one-off audit.

## When to Use

Orgs with >20 DataRaptors; required for governance maturity.

Typical trigger phrases that should route to this skill: `dataraptor field mapping broken`, `omnistudio dependency tracking`, `dataraptor field renamed`, `omnistudio governance`.

## Recommended Workflow

1. Naming standard: prefix DRs by domain, suffix by function (`Account_DR_Read_Contacts`).
2. Build a dependency report via Tooling API: for each DR, extract field references from its JSON.
3. CI: on every deploy, run a script that cross-references the DR field list against object fields; fail on missing.
4. Track usage: query OmniScript steps referencing each DR; flag orphans.
5. Version DRs — keep old active until consumers migrate.

## Key Considerations

- DataRaptor JSON structure is stable; parse reliably for references.
- Custom metadata may reference DRs by name — watch rename impact.
- Deployment fails on missing fields only if strict validation used.
- Monthly 'DR audit' finds dead DRs.

## Worked Examples (see `references/examples.md`)

- *CI field check* — After a field delete
- *Dead DR cleanup* — 100 DRs, 12 dead

## Common Gotchas (see `references/gotchas.md`)

- **Renamed field** — DR returns empty silently.
- **DR version sprawl** — Many active versions; unclear which runs.
- **Custom metadata refs to DR name** — Break on rename.

## Top LLM Anti-Patterns (full list in `references/llm-anti-patterns.md`)

- No CI DR field check
- Inconsistent naming
- Many active DR versions

## Official Sources Used

- OmniStudio Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.omnistudio_developer.meta/omnistudio_developer/
- OmniStudio for Salesforce — https://help.salesforce.com/s/articleView?id=sf.os_omnistudio_for_salesforce_overview.htm
- OmniScript to LWC OSS — https://developer.salesforce.com/docs/atlas.en-us.omnistudio_developer.meta/omnistudio_developer/os_migrate_from_vf_to_lwc.htm
