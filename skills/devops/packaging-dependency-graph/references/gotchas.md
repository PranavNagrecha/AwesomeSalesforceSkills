# Gotchas — Packaging Dependency Graph

## Gotcha 1: `LATEST` binds to the newest created version, not the released one

**What happens:** The extension version that gets promoted was built against base build 1.1.0.3, which was never promoted. Subscribers on the released base (1.1.0.2) can't install it, or install it against metadata it was never tested with.

**When it occurs:** The dependency says `"versionNumber": "1.1.0.LATEST"`. `LATEST` maps to the most recently created package version, which might not be the promoted one; it resolves when the extension version is created, so it does not change later — the damage is baked into that 04t.

**How to avoid:** Before creating the extension version you will promote, promote the base, change the dependency to `1.1.0.RELEASED`, then create and test the extension version.

---

## Gotcha 2: Skip-validated base versions are not a safe build target

**What happens:** An extension passes its tests against a base version created with skip validation; the base later fails validation and the pair never ships together.

**When it occurs:** A version created with skip validation is created without validating dependencies, package ancestors, or metadata.

**How to avoid:** Test extensions against a stable, previously promoted base version or a base version created without skip validation.

---

## Gotcha 3: Indirect dependencies must be listed unless transitive calculation is on

**What happens:** `Expense Manager` depends on `Expense Manager - Util`, which depends on `External Apex Library`. The project lists only Util, so the declared dependencies no longer describe everything that must be installed first.

**When it occurs:** By default you list all of a package's dependencies, including indirect ones, in installation order. Only with `calculateTransitiveDependencies: true` do you list direct dependencies alone.

**How to avoid:** Either turn on `calculateTransitiveDependencies` or list the full chain base-first. The checker flags a dependency list whose order contradicts the graph.

---

## Gotcha 4: Install order is a property of the graph, not of the file

**What happens:** A release script installs packages in `packageDirectories` order or alphabetically and fails on the first package whose dependency is not yet in the org.

**When it occurs:** Whenever someone reorders the project file, or adds a package mid-list.

**How to avoid:** Derive the order from the graph: the checker prints it, and for a built version `SELECT Dependencies FROM SubscriberPackageVersion WHERE Id = '04t...'` (Tooling API) returns the dependency 04t IDs in install order.

---

## Gotcha 5: Release status is one-way

**What happens:** A version is promoted "to test promotion" and the team then tries to un-release it.

**When it occurs:** `sf package version update` changes most properties but not the release status. After promoting a MAJOR.MINOR.PATCH, you can't create more versions with that same number. Promotion also needs the "Promote a package version to released" permission in the Dev Hub.

**How to avoid:** Promote only the build you intend to ship, base first, and bump the patch or minor number for the fix.

---

## Gotcha 6: A cycle has no install order

**What happens:** A base package starts referencing a class in its extension. Neither can be versioned against the other, and the failure appears at version-create time, often weeks after the reference was added.

**When it occurs:** Shared code drifts into whichever package a developer had open.

**How to avoid:** Extract the shared piece into a third package that both depend on; the checker reports a cycle as an ERROR as soon as it appears in `sfdx-project.json`.

---

## Gotcha 7: Deleting a version that something still depends on

**What happens:** Old versions are cleaned up, and installs of a dependent version start failing.

**When it occurs:** Unlocked package versions can be deleted whether beta or released (released 2GP managed versions can't). Deletion is permanent, installing a deleted version fails, and the guide says to make sure the version isn't referenced as a dependency first.

**How to avoid:** Before `sf package version delete`, query `SubscriberPackageVersion.Dependencies` for every version you still distribute and keep any 04t that appears there.
