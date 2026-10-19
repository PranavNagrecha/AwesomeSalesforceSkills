---
name: packaging-dependency-graph
description: "Model and verify unlocked package dependencies, version pinning, and promotion. NOT for 1GP managed packages — use devops/multi-package-development."
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
  - "work out the install order for our unlocked packages"
  - "decide between LATEST and RELEASED for a package dependency"
  - "find which package versions a 04t depends on before installing it"
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
version: 1.2.0
author: Pranav Nagrecha
updated: 2026-10-19
---

# Packaging Dependency Graph

Unlocked package dependencies bind a package version to versions of other packages. Without an explicit graph you can ship an extension version built against a base version that was never released, or install packages in an order the platform rejects. This skill covers declaring dependencies in `sfdx-project.json`, choosing between the `LATEST` and `RELEASED` keywords, deriving install and promotion order from the graph, and proving the order in an org that has never seen the source.

---

## Before Starting

- List every package directory, its `package` alias, and its `versionNumber` (with `NEXT` or a literal build).
- Find out which packages are developed in parallel (base and extension changing in the same sprint) and whether anyone creates versions with `--skip-validation`.
- Confirm who in the Dev Hub holds the "Promote a package version to released" user permission.

---

## Questions to Ask Before Configuring

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| Are any base and extension packages developed in parallel? | `LATEST` binds the extension to the newest *created* base version, which may never be promoted (gotcha 1). | A rule to switch the dependency to `RELEASED` before the extension version you will promote is created. |
| Does anyone create versions with skip validation? | Skip-validated versions aren't checked for dependencies, ancestors, or metadata; extensions must be tested against a promoted or validated base (gotcha 2). | A list of which versions are safe to build against. |
| Is `calculateTransitiveDependencies` on? | Without it you must list indirect dependencies yourself, in install order (gotcha 3). | One unambiguous dependency list per package. |
| What order would a subscriber install these packages in? | Dependencies are listed in installation order, and `SubscriberPackageVersion.Dependencies` returns the 04t IDs in that order (gotcha 4). | A generated install order rather than a remembered one. |
| Who promotes, and in what order? | Promotion is permission-gated and cannot be reverted with `package version update` (gotcha 5). | A named promoter and a base-first promotion runbook. |
| Will any package reference a package that references it back? | A cycle makes the graph impossible to order; the fix is a third package (gotcha 6). | A dependency direction rule per package layer. |
| Do you ever expect to delete a version? | Released unlocked versions can be deleted, released 2GP managed versions can't, and deleting a version that is still a dependency breaks installs (gotcha 7). | A retention rule that checks dependents before any delete. |

A properly configured graph adds a single source for install and promotion order and a `RELEASED`-based dependency at promotion time, where "just adding the dependency" ships an extension pinned to a base build nobody released.

---

## Core Concepts

### Dependency declaration

Each `packageDirectories` entry may carry a `dependencies` array. A dependency is either `{"package": "<alias>@<version>"}` (the alias resolves to a version) or `{"package": "<name>", "versionNumber": "<M.m.p.build>"}`; packages outside the Dev Hub use the alias form. IDs work too: the `0Ho` package ID with a version number, or the `04t` subscriber package version ID alone. With more than one dependency, list them in installation order, including indirect ones, unless `calculateTransitiveDependencies` is true — then list direct dependencies only and the CLI computes the rest.

```json
{
  "packageDirectories": [
    { "path": "util", "package": "Expense Manager - Util", "versionNumber": "4.7.0.NEXT", "default": true },
    {
      "path": "exp-core",
      "package": "Expense Manager",
      "versionNumber": "3.2.0.NEXT",
      "default": false,
      "calculateTransitiveDependencies": true,
      "dependencies": [
        { "package": "Expense Manager - Util", "versionNumber": "4.7.0.RELEASED" }
      ]
    }
  ],
  "packageAliases": {
    "Expense Manager - Util": "0Ho000000000001AAA",
    "Expense Manager": "0Ho000000000002AAA"
  }
}
```

### Version keywords

| Keyword | Where | Resolves to |
|---|---|---|
| `NEXT` | your own `versionNumber` | the next available build number |
| `LATEST` | a dependency's `versionNumber` | the most recently created version, promoted or not |
| `RELEASED` | a dependency's `versionNumber` | the promoted and released version |
| `HIGHEST` / `NONE` | `ancestorVersion` / `ancestorId` | highest promoted version / no ancestor (existing customers can't upgrade) |

Example from the guide: with versions 1.0.0.1, 1.0.0.2, 1.0.0.3 created and 1.0.0.2 promoted, `1.0.0.RELEASED` = 1.0.0.2 but `1.0.0.LATEST` = 1.0.0.3.

### Reading the graph back

For an installed (or installable) version, query the Tooling API: `SELECT Dependencies FROM SubscriberPackageVersion WHERE Id = '04t...'` returns the dependency 04t IDs in install order. `sf package version displaydependencies` draws the hierarchy when `calculateTransitiveDependencies` is enabled.

Metadata XML: not applicable — the graph lives entirely in `sfdx-project.json` and the package version records.

---

## Recommended Workflow

1. Inventory `sfdx-project.json`: every package directory, alias, `versionNumber`, and `dependencies` entry; answer the Questions table.
2. Run `python3 skills/devops/packaging-dependency-graph/scripts/check_packaging_dependency_graph.py --manifest-dir .` — it ERRORs on unresolved aliases, cycles, `NEXT` on a dependency, and `LATEST`/`RELEASED` on your own `versionNumber`, and prints the base-first order.
3. During parallel development use `LATEST`; before creating the extension version you intend to promote, promote the base, switch the dependency to `RELEASED`, then create and test the extension version.
4. Install the 04t versions into a fresh org in the printed order (`references/worked-example.md` has the CI job) and run tests against the installed metadata.
5. Promote base-first with `sf package version promote`, recording each 04t with its commit.
6. Before any `sf package version delete`, query dependents and confirm nothing installs against that version.

---

## Decision Guidance

| Situation | Use | Why |
|---|---|---|
| Base and extension change in the same sprint | `LATEST` while developing, `RELEASED` for the promoted build | `LATEST` can bind to an unpromoted base |
| Extension depends on a third-party or other-Dev Hub package | Alias form `"Name@1.2.0"` / the 04t ID | Packages outside the Dev Hub use the alias form |
| Deep chains (C → B → A) | `calculateTransitiveDependencies: true` | List direct dependencies only; the CLI computes the rest |
| Two packages need each other's code | Extract a third package both depend on | A cycle has no install order |
| A released version is bad | Ship a new version | Release status can't be changed with `package version update` |

---

## Review Checklist

- [ ] Every dependency `package` value resolves to a `packageAliases` key or is a `0Ho`/`04t` ID
- [ ] No dependency uses `NEXT`; no package's own `versionNumber` uses `LATEST` or `RELEASED`
- [ ] The extension version being promoted was built against a `RELEASED` (or literal, promoted) base version
- [ ] The graph has no cycle; the checker's printed order matches the install and promotion scripts
- [ ] A fresh-org install in that order passed tests
- [ ] The promoter holds the Dev Hub permission to promote
- [ ] No version slated for deletion is a dependency of another version

---

## Salesforce-Specific Gotchas

Full list in `references/gotchas.md`. The two that block releases most often:

1. **`LATEST` is not "latest released"** — it maps to the newest created version.
2. **List order is install order** — dependencies are listed in installation order unless transitive calculation is on.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Dependency diagram | Packages, edges, and the keyword on each edge |
| Install / promotion order | The checker's base-first order, used by CI and the release runbook |
| Pinning strategy | When each edge moves from `LATEST` to `RELEASED` |
| Promotion runbook | Base-first promotion with recorded 04t IDs |

---

## Reference Files

| File | Use it for |
|---|---|
| `references/examples.md` | A three-package graph declared correctly, and a clean-org install proof |
| `references/gotchas.md` | Seven dependency and promotion behaviours with avoidance steps |
| `references/llm-anti-patterns.md` | Dependency syntax and promotion mistakes AI assistants make |
| `references/well-architected.md` | Pillar framing and the guide lines behind each claim |
| `references/worked-example.md` | Parallel base/extension release from `LATEST` to `RELEASED`, with the CI install job |

---

## Related Skills

- `devops/unlocked-package-development` — the package lifecycle as a whole
- `devops/sfdx-monorepo-patterns` — repository layout for multiple package directories
- `devops/multi-package-development` — 1GP managed packages and cross-package development
