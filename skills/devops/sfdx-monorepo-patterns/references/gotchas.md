# Gotchas — SFDX Monorepo Patterns

## Gotcha 1: Cross-package ownership of a custom object

**What happens:** A field on `Customer_Profile__c` lives in `sales-core`, the object definition lives in `base-utils`, and `sales-core` doesn't depend on `base-utils`. Installs and clean-org deploys of `sales-core` fail because the object isn't there.

**When it occurs:** Teams extend a shared custom object from their own directory. The DX guide explicitly allows a field to live in a different directory from its object; what it requires is that the object exists first.

**How to avoid:** One directory owns each custom object's definition; every directory holding its fields declares a dependency on the owner. The checker warns when a field's object is owned by a directory the package doesn't depend on.

---

## Gotcha 2: New components from a retrieve land in the default directory

**What happens:** After a Setup change, `sf project retrieve start` puts a new Flow in `base-utils`, and the next package version ships it in the wrong package.

**When it occurs:** Retrieve updates components that already exist locally in their own directory but copies components it can't match into the default directory. Only one directory can be the default.

**How to avoid:** Make the default the directory reviewers watch most closely, retrieve with `--source-dir` or `--metadata` for targeted work, and move new files to their owning directory before committing.

---

## Gotcha 3: Package directories are not packages

**What happens:** The team assumes code under `packages/sales-core` "belongs to" the `sales-core` package in the org because it was deployed from there.

**When it occurs:** The multiple-directory structure is client-side only. `sf project deploy start` has no association between a local directory and a package in the org; metadata belongs to an unlocked or 2GP package only when that package is installed.

**How to avoid:** Decide per environment whether it receives source deploys or package installs, and don't mix them for the same components.

---

## Gotcha 4: Tooling inside a package path ships

**What happens:** Seed scripts and demo-data Apex in a package directory end up in every org that installs the package.

**When it occurs:** Anything under a `packageDirectories` path is package content.

**How to avoid:** Keep tooling in `tools/` outside every package path (test classes stay inside, because they supply coverage). The checker warns on classes whose names suggest seeding or demo data inside package paths.

---

## Gotcha 5: A per-package `.forceignore` replaces the root one

**What happens:** The root `.forceignore` excludes `**/jsconfig.json` and LWC test folders, but files in one package still deploy.

**When it occurs:** Project commands walk up from a source file to the first `.forceignore`, use it, and stop — they don't continue to the root file. A package directory with its own `.forceignore` ignores the root rules.

**How to avoid:** Keep one root `.forceignore`, or copy every root rule a package still needs into its own file. The checker lists per-package `.forceignore` files and the root patterns they omit.

---

## Gotcha 6: Changed-files CI misses broken dependents

**What happens:** A signature change in `base-utils` passes CI because only `base-utils` was validated; `sales-core` breaks in the release build.

**When it occurs:** Change detection maps changed paths to packages and stops there.

**How to avoid:** Expand the changed set through the declared `dependencies` to every dependent, and validate in dependency order (see `examples.md`).

---

## Gotcha 7: `sourceApiVersion` is one value for the whole project

**What happens:** Bumping `sourceApiVersion` for one team's feature changes the fields retrieved for every metadata type in every package, and unrelated diffs appear across the repo.

**When it occurs:** `sourceApiVersion` is a project-level setting that determines the fields retrieved for each metadata type during deploy, retrieve, and convert.

**How to avoid:** Upgrade it in a dedicated change, retrieve and validate every package, and review the resulting diffs together.
