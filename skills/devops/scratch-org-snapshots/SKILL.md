---
name: scratch-org-snapshots
description: "Use Scratch Org Snapshots to reduce CI bring-up time from 10–20 minutes to under 2. NOT for persistent sandbox provisioning."
category: devops
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Performance
  - Operational Excellence
triggers:
  - "slow scratch org creation"
  - "snapshot scratch org"
  - "speed up ci salesforce"
  - "source push is slow"
tags:
  - scratch-org
  - ci
  - snapshots
inputs:
  - "Dev Hub"
  - "base scratch org definition"
  - "managed package install list"
outputs:
  - "Snapshot + nightly refresh job + CI consumption pattern"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-17
---

# Scratch Org Snapshots

Scratch Org Snapshots (GA) capture a fully configured scratch org so new ones can be created from the snapshot in seconds. For orgs with multiple managed package installs and large metadata pushes, this cuts CI bring-up from 15 minutes to under 2.

## When to Use

CI bring-up >5 minutes, especially with 3+ managed package installs or heavy data seed.

Typical trigger phrases that should route to this skill: `slow scratch org creation`, `snapshot scratch org`, `speed up ci salesforce`, `source push is slow`.

## Recommended Workflow

1. Create a base scratch org with all managed packages installed, baseline metadata pushed, and seed data loaded.
2. `sf org create snapshot --name nightly-base --source-org <aliased-scratch>` — takes 10–15 min, Dev Hub operation.
3. Reference the snapshot in your scratch-def.json: `"snapshot": "nightly-base"`.
4. Add a nightly GitHub Action to recreate the snapshot so it stays fresh against package updates.
5. CI workflows create scratch orgs from the snapshot with `sf org create scratch --definition-file ...` — sub-2-minute bring-up.

## Key Considerations

- Snapshots are Dev Hub scoped; one per Dev Hub.
- Stale snapshots drift from managed-package updates; nightly refresh is mandatory.
- Snapshot includes data; keep seed minimal to avoid bloat.
- Snapshot quota limits: check Setup → Dev Hub → Snapshots.

## Worked Examples (see `references/examples.md`)

- *Multi-package org* — 3 managed packages
- *Nightly refresh workflow* — Snapshot drift

## Common Gotchas (see `references/gotchas.md`)

- **Stale snapshot** — CI builds pass but production deploy fails.
- **Snapshot with seed data** — Tests pass only against seed data; real-world bug missed.
- **Region mismatch** — Snapshot in one Dev Hub region, scratch org created elsewhere.

## Top LLM Anti-Patterns (full list in `references/llm-anti-patterns.md`)

- Weekly-only snapshot refresh
- Huge seed data in snapshot
- Forgetting to update snapshot after package upgrade

## Official Sources Used

- Salesforce DX Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/
- Unlocked Packaging — https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_dev2gp.htm
- SF CLI — https://developer.salesforce.com/docs/atlas.en-us.sfdx_cli_reference.meta/sfdx_cli_reference/
- DevOps Center — https://help.salesforce.com/s/articleView?id=sf.devops_center_overview.htm
- Scratch Org Snapshots — https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_scratch_orgs_snapshots.htm
- sfdx-hardis — https://sfdx-hardis.cloudity.com/
