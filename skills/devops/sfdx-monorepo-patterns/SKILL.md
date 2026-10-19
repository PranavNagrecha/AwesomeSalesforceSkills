---
name: sfdx-monorepo-patterns
description: "Structure a single repo with multiple unlocked packages, shared templates, and cross-package test strategies. NOT for multi-repo org strategies — use apex/sf-cli-and-sfdx-essentials."
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
  - "split one force-app folder into several package directories"
  - "build only the packages that changed in CI"
  - "keep seed scripts and tooling out of our unlocked packages"
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
version: 1.2.0
author: Pranav Nagrecha
updated: 2026-10-19
---

# SFDX Monorepo Patterns

A monorepo lets multiple package directories — usually unlocked packages — share one git history, shared building blocks (test factory, trigger framework), and one coordinated CI pipeline. This skill formalizes the `sfdx-project.json` layout, ownership of shared objects across directories, `.forceignore` scoping, and change detection that builds what changed plus everything that depends on it.

---

## Before Starting

- Inventory the logical domains (sales, service, integration, shared utilities) and who owns each.
- Decide whether the directories will become unlocked packages now, later, or never — the layout differs only in the `package`, `versionNumber`, and `dependencies` keys.
- List shared custom objects and which domain should own each object definition.
- Find every non-deployable asset (seed scripts, sample data, local tooling) currently inside `force-app`.

---

## Questions to Ask Before Configuring

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| Which directory is the default, and why that one? | Only one package directory can be the default, and retrieves put new components there (gotcha 2). | A default chosen so stray retrieves land where reviewers look. |
| Which package owns each shared custom object's definition? | A field can live in a different directory from its object, but the object must be installed first (gotcha 1). | One owner per object and a declared dependency from every extension package. |
| Will directories become packages, or is this source organization only? | The directory structure is client-side only; `sf project deploy start` doesn't put metadata into any package (gotcha 3). | A clear line between "organized source" and "installable packages". |
| Where do tooling, seed data, and scripts live? | Everything under a package directory deploys with it (gotcha 4). | A `tools/` area outside every `packageDirectories` path. |
| Does any package directory need its own `.forceignore`? | The CLI uses the first `.forceignore` it finds walking up from a file and stops there (gotcha 5). | A deliberate choice between one root file and per-package files. |
| How does CI decide what to validate? | A change in a base package can break dependents that have no changed files (gotcha 6). | Change detection expanded through the dependency graph. |
| Is `sourceApiVersion` bumped repo-wide in its own change? | It is one project-level value that sets the fields retrieved for every type (gotcha 7). | API-version upgrades reviewed and validated across all packages. |

A properly configured monorepo adds single ownership for shared objects, an explicit dependency graph, and graph-aware CI, where "just making folders" produces packages that install only in the order someone remembers.

---

## Core Concepts

### Package directories are a client-side structure

List each directory under `packageDirectories`; each follows the standard DX structure. The structure is local only: deploying with `sf project deploy start` has no association between a local directory and a package in the org — metadata belongs to an unlocked or 2GP package only when that package is installed. For a new org, `sf project deploy start` with no target deploys every package directory in one transaction; `--source-dir` (repeatable) narrows it.

```json
{
  "packageDirectories": [
    { "path": "packages/base-utils", "default": true, "package": "base-utils", "versionNumber": "1.4.0.NEXT" },
    {
      "path": "packages/sales-core",
      "package": "sales-core",
      "versionNumber": "2.1.0.NEXT",
      "dependencies": [{ "package": "base-utils", "versionNumber": "1.4.0.RELEASED" }]
    }
  ],
  "packageAliases": { "base-utils": "0Ho000000000001AAA", "sales-core": "0Ho000000000002AAA" },
  "sourceApiVersion": "67.0"
}
```

### Ownership of shared objects

The DX guide's own example puts a custom object `MyObject` in the default directory and a new field `MyField` on it in an "extension" directory without the object files. That is the pattern: one directory owns each custom object's definition; other directories hold only their fields and depend on the owner.

### What the default directory decides

There can be only one package directory with `"default": true`. `sf project retrieve start` updates components that already exist locally in their own directory and copies components it can't match into the default directory.

### `.forceignore` resolution

Project commands walk up from a source file to the first `.forceignore` they find, use it, and stop. A per-package `.forceignore` therefore replaces the root file's rules for that package rather than adding to them.

---

## Recommended Workflow

1. Map domains to directories under `packages/`, pick the default (usually the base package), and keep `tools/` and `config/` outside every package path.
2. Give each shared custom object one owning directory; move other teams' fields into their own directories and declare `dependencies` on the owner.
3. Run `python3 skills/devops/sfdx-monorepo-patterns/scripts/check_sfdx_monorepo_patterns.py --manifest-dir .` — it ERRORs on more than one default, missing package paths, overlapping paths, and an object definition owned by two directories; it WARNs on field files whose object lives in a directory the package doesn't depend on, and on per-package `.forceignore` files.
4. Wire CI change detection from `references/examples.md` (changed directories expanded to their dependents, validated in dependency order).
5. For packaged directories, follow `devops/packaging-dependency-graph` for `LATEST` vs `RELEASED` and promotion order.

---

## Decision Guidance

| Situation | Approach | Why |
|---|---|---|
| Two teams extend the same custom object | Object in the base directory; fields in each team's directory; dependency on base | A field can live apart from its object, but the object must exist first |
| Seed data and scripts | `tools/` outside `packageDirectories` | Everything in a package directory deploys |
| Different ignore rules per package | Per-package `.forceignore` that repeats the root rules it still needs | The nearest file wins; rules don't merge |
| CI time | Validate changed packages plus their dependents | A base change can break untouched dependents |
| One package needs a different API version | Treat as a repo-wide decision or a separate repo | `sourceApiVersion` is project-level |

---

## Review Checklist

- [ ] Exactly one `"default": true`, and every `path` exists
- [ ] No two package paths overlap
- [ ] Each shared custom object's definition lives in one directory; extension directories declare a dependency on it
- [ ] No tooling, seed data, or scripts inside any package path
- [ ] `.forceignore` placement is deliberate and per-package files repeat needed root rules
- [ ] CI validates changed packages plus dependents, in dependency order
- [ ] The checker exits 0

---

## Salesforce-Specific Gotchas

Full list in `references/gotchas.md`. The two that cost the most:

1. **Directories are not packages** — deploying source never makes anything packaged.
2. **The nearest `.forceignore` wins** — a per-package file silently drops the root file's rules.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| `sfdx-project.json` | Package directories, single default, aliases, dependencies |
| Ownership table | Shared object → owning directory → dependents |
| CI matrix | Changed + dependent packages, in dependency order |
| Checker gate | `check_sfdx_monorepo_patterns.py` on every PR |

---

## Reference Files

| File | Use it for |
|---|---|
| `references/examples.md` | Splitting one `force-app` into three packages; graph-aware change detection |
| `references/gotchas.md` | Seven monorepo behaviours with avoidance steps |
| `references/llm-anti-patterns.md` | Layout and CI mistakes AI assistants make |
| `references/well-architected.md` | Pillar framing and the guide lines behind each claim |
| `references/layout-reference.md` | Directory tree, `.forceignore` placement, and ownership table template |

---

## Related Skills

- `devops/packaging-dependency-graph` — dependency keywords, install and promotion order for the packages in this repo
- `devops/unlocked-package-development` — package lifecycle
- `devops/github-actions-for-salesforce` — workflow structure for the CI matrix
- `apex/sf-cli-and-sfdx-essentials` — multi-repo and general CLI practice
