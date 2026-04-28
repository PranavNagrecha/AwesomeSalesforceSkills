---
name: sfdx-hardis-integration
description: "Adopt sfdx-hardis for org monitoring, CI pipelines, and release automation. NOT for writing plugins to sfdx-hardis itself."
category: devops
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
triggers:
  - "sfdx hardis setup"
  - "salesforce monitoring open source"
  - "cicd for salesforce free"
  - "hardis commands"
tags:
  - sfdx-hardis
  - cicd
  - monitoring
inputs:
  - "CI provider"
  - "monitoring SLAs"
  - "release cadence"
outputs:
  - "hardis configuration + CI pipeline + monitoring job"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-28
---

# sfdx-hardis Integration

sfdx-hardis is an open-source sfdx plugin that wraps org monitoring, deploy validation, and simpler CLI ergonomics. It includes prebuilt GitHub Actions / GitLab CI templates, a daily monitoring job that diffs metadata, and a 'smart deploy' flow.

## Adoption Signals

Teams without Copado / Gearset budget who want a battle-tested open-source stack. Not for teams already deeply invested in DevOps Center.

- Required when org monitoring (license drift, security baselines, metadata diffs) must run on a self-hosted CI runner.
- Required when the team needs scriptable hooks (pre-deploy data backup, post-deploy smoke tests) that hosted vendors don't expose.

## Recommended Workflow

1. `sf plugins install sfdx-hardis` on CI agents and developer machines.
2. Run `sf hardis:project:configure:auth` to wire JWT credentials per environment.
3. Adopt the provided CI template (GitHub / GitLab / Azure) — it handles validation, deploy, and rollback hints.
4. Enable `sf hardis:org:monitor:all` as a daily scheduled job to diff metadata and flag drift.
5. Use `sf hardis:work:new` instead of `sf org create scratch` for guided dev workflow.

## Key Considerations

- OSS — no vendor support SLA; community Discord is active.
- Opinionated; layering heavy customization fights the tool.
- Monitoring output is JSON + HTML; wire HTML to GitHub Pages for discoverability.
- Upgrades can be breaking; pin plugin version in CI.

## Worked Examples (see `references/examples.md`)

- *Daily drift monitor* — Detect manual prod changes
- *Smart deploy* — Reduce deploy failures

## Common Gotchas (see `references/gotchas.md`)

- **Plugin version drift** — CI and local produce different output.
- **Long monitor run** — Daily job exceeds 2h.
- **False-positive drift** — Noise alerts.

## Top LLM Anti-Patterns (full list in `references/llm-anti-patterns.md`)

- Running hardis without pinning version
- Ignoring monitor alerts
- Forking hardis to add custom logic (contribute upstream instead)

## Official Sources Used

- Salesforce DX Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/
- Unlocked Packaging — https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_dev2gp.htm
- SF CLI — https://developer.salesforce.com/docs/atlas.en-us.sfdx_cli_reference.meta/sfdx_cli_reference/
- DevOps Center — https://help.salesforce.com/s/articleView?id=sf.devops_center_overview.htm
- Scratch Org Snapshots — https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_scratch_orgs_snapshots.htm
- sfdx-hardis — https://sfdx-hardis.cloudity.com/
