---
name: omnistudio-field-mapping-governance
description: "Govern DataRaptor field mappings to prevent runtime errors when source metadata changes: naming, versioning, and dependency tracking. NOT for DataRaptor authoring fundamentals — use data/omnistudio-metadata-management."
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
runtime_orphan: true
version: 1.1.0
author: Pranav Nagrecha
updated: 2026-08-01
---

# OmniStudio Field Mapping Governance

A DataRaptor breaks silently when a source field is renamed or removed. This skill sets up a dependency report (custom metadata + Tooling API) that lists every field each DR/IP references and runs a CI check on every metadata change, plus a naming standard, a monthly orphan-DR cleanup, and a versioning discipline that keeps prior DR versions active while consumers migrate so governance is a living process, not a one-off audit.

## Adoption Signals

Orgs with >20 DataRaptors; required for governance maturity.

## Recommended Workflow

1. Naming standard: prefix DRs by domain, suffix by function (`Account_DR_Read_Contacts`).
2. Build a dependency report via Tooling API: for each DR, extract field references from its JSON.
3. **Data Mapper versioning (Summer '26, opt-in):** On Standard Runtime, enable **Data Mapper Versioning** in Omnistudio Settings *after* Omnistudio Metadata is active. Active Data Mappers lock in place — create a **new version** instead of editing the live mapper, matching OmniScript/FlexCard/IP versioning discipline. Versioning is **off by default**; turning it on activates existing standard mappers as version 1.
4. CI: on every deploy, run a script that cross-references the DR field list against object fields; fail on missing.
5. Track usage: query OmniScript steps referencing each DR; flag orphans.
6. Version DRs — keep old active until consumers migrate; when Data Mapper versioning is on, prefer new versions over in-place edits to active mappers.

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
