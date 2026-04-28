---
name: devops-center-advanced
description: "Use DevOps Center for work item tracking, org-based release pipelines, and merging into existing SFDX workflows. NOT for first-time setup."
category: devops
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
triggers:
  - "devops center pipeline"
  - "work item salesforce"
  - "devops center merge conflict"
  - "bypass devops center"
tags:
  - devops-center
  - work-item
  - pipeline
inputs:
  - "existing pipeline"
  - "team size"
outputs:
  - "work-item model + bypass rules + hybrid SFDX + DOC workflow"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-28
---

# DevOps Center Advanced Workflows

DevOps Center provides a point-and-click UI over source-tracked pipelines. For teams already on SFDX it can coexist if you treat DOC work items as promotion units and keep local dev via `sf org create scratch`. This skill documents the hybrid pattern, escalation paths, and the bypass rules for emergency hot-fixes.

## Recommended Workflow

1. Connect dev + UAT + prod orgs; configure pipeline stages in DevOps Center.
2. Every change is a Work Item tied to a pipeline; admins use Builder UI, devs use branches + `sf project retrieve`.
3. Developer workflow: create branch for WI → commit via sfdx → DOC auto-syncs the branch to the WI.
4. Promotion: DOC merges WI branch to pipeline branch; deploys to next stage.
5. Emergency hotfix: bypass pipeline by deploying directly with a flag + post-deploy WI reconciliation.

## Key Considerations

- DOC uses GitHub as source of truth; conflicts show up in GitHub PR UI.
- WI-based model fights with ad-hoc git branching — pick one pattern per WI.
- DOC test deployments run in target org — quota impact.
- Historical WIs are not easy to delete; plan retention.

## Worked Examples (see `references/examples.md`)

- *Hybrid dev flow* — Team with admins + devs
- *Bypass for P0* — Prod outage

## Common Gotchas (see `references/gotchas.md`)

- **WI merge conflict** — Two admins edit same flow.
- **Branch ≠ WI state** — Branch pushed manually while WI is in progress.
- **Bypass becomes normal** — Every deploy is 'emergency'.

## Top LLM Anti-Patterns (full list in `references/llm-anti-patterns.md`)

- Using DOC and SFDX branches for the same change simultaneously
- No bypass runbook (invents one at 3am)
- Keeping every WI forever (UI bloat)

## Official Sources Used

- Salesforce DX Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/
- Unlocked Packaging — https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_dev2gp.htm
- SF CLI — https://developer.salesforce.com/docs/atlas.en-us.sfdx_cli_reference.meta/sfdx_cli_reference/
- DevOps Center — https://help.salesforce.com/s/articleView?id=sf.devops_center_overview.htm
- Scratch Org Snapshots — https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_scratch_orgs_snapshots.htm
- sfdx-hardis — https://sfdx-hardis.cloudity.com/
