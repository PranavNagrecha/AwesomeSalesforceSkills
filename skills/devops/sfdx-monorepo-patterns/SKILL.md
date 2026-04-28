---
name: sfdx-monorepo-patterns
description: "Structure a single repo with multiple unlocked packages, shared templates, and cross-package test strategies. NOT for multi-repo org strategies."
category: devops
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Scalability
triggers:
  - "monorepo salesforce"
  - "multiple unlocked packages one repo"
  - "sfdx project multiple packages"
  - "package dependency order"
tags:
  - monorepo
  - packaging
  - sfdx
inputs:
  - "current repo layout"
  - "list of logical packages"
outputs:
  - "sfdx-project.json package directive list, Turborepo/Nx analog, CI matrix"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-28
---

# SFDX Monorepo Patterns

A monorepo lets multiple unlocked packages share a single git history, shared templates (test factory, TriggerHandler), and a coordinated CI pipeline. This skill formalizes the sfdx-project.json layout, the dependency graph (`"dependencies"` per package), and a change-detection strategy so CI only validates what changed.

## Adoption Signals

Orgs with 3+ logical domains (sales, service, custom agentforce actions). Not for single-package projects.

- Required when one repo holds multiple unlocked packages with shared dependencies and ordered install requirements.
- Required when CI must build only the packages whose source changed — full-repo rebuilds become uneconomic.

## Recommended Workflow

1. Define package directories in sfdx-project.json with `"default": true` on the top-level, `"package": "<pkg>"` on each.
2. Declare cross-package dependencies in `"dependencies"`; package version bumps cascade.
3. Move shared templates to packaged 'utils' with narrow public API; dependent packages depend on utils.
4. CI: compute changed files per push; run `sf project deploy validate` only on affected packages using `--manifest`.
5. Weekly: bump package version + create a new version ID for changed packages; promote to `released` after validation.

## Key Considerations

- Declarative metadata that spans packages (Custom Object with fields in two packages) requires careful ownership.
- CI must know the dependency graph to build in order.
- Shared templates should not ship to prod — keep them in a `tools` directory outside package dirs.
- Use package aliases in sfdx-project.json for readability.

## Worked Examples (see `references/examples.md`)

- *Three-package layout* — Sales + Service + Agentforce
- *Change-detection CI* — Push touches only sales package

## Common Gotchas (see `references/gotchas.md`)

- **Cross-package field ownership** — Two packages define fields on Account; deploy order breaks.
- **Missing dependency declaration** — Deploy fails in prod; works in scratch.
- **Templates shipped to prod** — Tooling files leak into org.

## Top LLM Anti-Patterns (full list in `references/llm-anti-patterns.md`)

- One giant force-app directory
- No package dependency declaration
- Deploying everything on every push

## Official Sources Used

- Salesforce DX Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/
- Unlocked Packaging — https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_dev2gp.htm
- SF CLI — https://developer.salesforce.com/docs/atlas.en-us.sfdx_cli_reference.meta/sfdx_cli_reference/
- DevOps Center — https://help.salesforce.com/s/articleView?id=sf.devops_center_overview.htm
- Scratch Org Snapshots — https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_scratch_orgs_snapshots.htm
- sfdx-hardis — https://sfdx-hardis.cloudity.com/
