---
name: packaging-dependency-graph
description: "Model and verify unlocked package dependencies, version pinning, and promotion. NOT for 1GP managed packages."
category: devops
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
triggers:
  - "unlocked package dependency"
  - "package version pinning"
  - "promote package released"
  - "dependency graph salesforce"
tags:
  - packaging
  - 2gp
  - dependencies
inputs:
  - "list of packages + current version"
  - "intended promotion plan"
outputs:
  - "dependency diagram, pinning strategy, promotion runbook"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-28
---

# Packaging Dependency Graph

Unlocked package dependencies pin a package to a specific version of another. Without a graph, you can accidentally ship a service-core change that depends on an unreleased sales-core version, breaking prod deploy. This skill walks through extracting the dependency graph with the SF CLI, pinning versions explicitly in sfdx-project.json, and enforcing promotion order with a RELEASE.md checklist plus a fresh-scratch install validation step in CI. Correctly modeled dependencies prevent the most common 'works in staging, fails in prod' failure mode for multi-package monorepos.

## Recommended Workflow

1. Run `sf package dependencies list --package <id>` for each package; assemble the graph.
2. In sfdx-project.json, pin deps to `@version` (e.g., `sales-core@1.4.0-2`).
3. Promote packages bottom-up: base utils first, then dependents.
4. Validate install order on a fresh scratch org before promoting to prod.
5. Document the promotion order in a RELEASE.md checklist.

## Key Considerations

- Unlocked packages support LATEST, but pinning to a specific version is safer.
- Circular dependencies are disallowed; refactor to extract a third package.
- Promotion is one-way in the same org; keep old versions available via install links.
- Deletion of a package version is not supported in some flavors.

## Worked Examples (see `references/examples.md`)

- *Pinned deps* — 3 packages
- *Fresh-scratch validation* — Before prod release

## Common Gotchas (see `references/gotchas.md`)

- **LATEST rot** — Dev bumped base package; dependent silently breaks in prod.
- **Circular dep** — `sf package version create` fails with SSA_CYCLIC_DEP.
- **Promotion skip** — Promoted service-core before sales-core; installer fails.

## Top LLM Anti-Patterns (full list in `references/llm-anti-patterns.md`)

- Depending on @LATEST in prod
- No fresh-scratch install test
- Manual promotion order

## Official Sources Used

- Salesforce DX Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/
- Unlocked Packaging — https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_dev2gp.htm
- SF CLI — https://developer.salesforce.com/docs/atlas.en-us.sfdx_cli_reference.meta/sfdx_cli_reference/
- DevOps Center — https://help.salesforce.com/s/articleView?id=sf.devops_center_overview.htm
- Scratch Org Snapshots — https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_scratch_orgs_snapshots.htm
- sfdx-hardis — https://sfdx-hardis.cloudity.com/
