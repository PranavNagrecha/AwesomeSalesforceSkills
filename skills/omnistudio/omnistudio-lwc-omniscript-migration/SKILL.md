---
name: omnistudio-lwc-omniscript-migration
description: "Migrate classic Visualforce-based OmniScripts to LWC-based runtime with feature parity and regression testing. NOT for new OmniScript design."
category: omnistudio
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Performance
triggers:
  - "omniscript lwc migration"
  - "visualforce omniscript deprecated"
  - "switch omniscript to lwc"
  - "omni run lwc mode"
tags:
  - omnistudio
  - omniscript
  - lwc-migration
inputs:
  - "list of OmniScripts and their activation mode"
  - "custom LWCs embedded in scripts"
outputs:
  - "migration plan + parity matrix + rollout runbook"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-17
---

# OmniStudio LWC OmniScript Migration

Salesforce is deprecating the Visualforce OmniScript runtime. Orgs must switch each OmniScript to the LWC runtime via the 'Run OmniScripts in LWC' setting and retest. Third-party templates and embedded custom VFs need replacement LWCs. This skill covers inventory, parity testing, and the rollout sequence.

## When to Use

Any org still using VF-mode OmniScripts; required by the deprecation timeline.

Typical trigger phrases that should route to this skill: `omniscript lwc migration`, `visualforce omniscript deprecated`, `switch omniscript to lwc`, `omni run lwc mode`.

## Recommended Workflow

1. Inventory OmniScripts via OmniScript object query; note Type, Sub-Type, Active version.
2. Enable 'Run OmniScripts in LWC' at org level; each OmniScript can still opt out temporarily.
3. For each script: activate LWC mode; run QA scenarios; fix any parity gaps (custom VF → LWC rewrite).
4. Update embedded scripts: pages that host OmniScripts via `<c-omniscript>` LWC instead of VF include.
5. Deprecation cutover: disable VF mode globally; remove unused assets.

## Key Considerations

- Some template types (signature pad, legacy chart) need custom LWC rewrite.
- Styles differ subtly in LWC mode; QA designers carefully.
- LWC runtime is faster but strict about async patterns — some VF-only tricks won't port.
- Performance improves 30–60% in our benchmarks.

## Worked Examples (see `references/examples.md`)

- *Phased LWC cutover* — 80 OmniScripts
- *Custom VF replacement* — Signature capture inside script

## Common Gotchas (see `references/gotchas.md`)

- **Style drift** — Colors off after migration.
- **Async timing** — Remote action timing different in LWC.
- **No opt-out left** — Business outage when last VF-only script flips.

## Top LLM Anti-Patterns (full list in `references/llm-anti-patterns.md`)

- Big-bang cutover without QA
- Ignoring deprecation timeline
- Custom VF assets left after migration

## Official Sources Used

- OmniStudio Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.omnistudio_developer.meta/omnistudio_developer/
- OmniStudio for Salesforce — https://help.salesforce.com/s/articleView?id=sf.os_omnistudio_for_salesforce_overview.htm
- OmniScript to LWC OSS — https://developer.salesforce.com/docs/atlas.en-us.omnistudio_developer.meta/omnistudio_developer/os_migrate_from_vf_to_lwc.htm
