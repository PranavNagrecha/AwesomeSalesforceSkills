# LLM Anti-Patterns — Packaging Dependency Graph

Scope: the `dependencies` graph between second-generation packages and the promotion order
it implies. Repository layout for multiple packages belongs to
`devops/sfdx-monorepo-patterns`; the package lifecycle as a whole belongs to
`devops/unlocked-package-development`. This file is about what goes in the `dependencies`
block and what breaks when it is wrong.

## Anti-Pattern 1: Inventing a dependency syntax

The `dependencies` block sits inside a `packageDirectories` entry, and each dependency is an
object with `package` plus either a `versionNumber` or nothing at all (when the alias itself
pins a version). Assistants produce npm-shaped or Maven-shaped variants because those are
what "dependencies" looks like everywhere else, and the CLI rejects them with an error that
does not explain the shape.

**Wrong** — plausible, not the schema:

```json
{
  "packageDirectories": [
    {
      "path": "exp-core",
      "package": "Expense Manager",
      "dependencies": {
        "Expense Manager - Util": "^4.7.0"
      }
    }
  ]
}
```

**Right** — an array of objects, and every name resolved through `packageAliases`:

```json
{
  "packageDirectories": [
    {
      "path": "util",
      "default": true,
      "package": "Expense Manager - Util",
      "versionName": "Summer '24",
      "versionNumber": "4.7.0.NEXT"
    },
    {
      "path": "exp-core",
      "default": false,
      "package": "Expense Manager",
      "versionNumber": "3.2.0.NEXT",
      "dependencies": [
        { "package": "Expense Manager - Util", "versionNumber": "4.7.0.LATEST" },
        { "package": "External Apex Library - 1.0.0.4" }
      ]
    }
  ],
  "packageAliases": {
    "Expense Manager - Util": "0Ho...",
    "Expense Manager": "0Ho...",
    "External Apex Library@1.0.0.4": "04t..."
  }
}
```

Note the two forms in that array. A dependency with a `versionNumber` names the package and
pins the version separately; a dependency without one carries the version inside the alias,
which resolves to a specific `04t` subscriber package version id. Both are valid; mixing
them in one file is normal.

Source: Project Configuration File for Unlocked Packages — https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_unlocked_pkg_config_file.htm

## Anti-Pattern 2: Reading `LATEST` and `NEXT` as interchangeable

They occupy the same build-number position and mean opposite things, so assistants swap
them freely. `NEXT` belongs in **your** package's `versionNumber` and increments the build to
the next available one when you create a version. `LATEST` belongs in a **dependency's**
`versionNumber` and resolves to the newest existing build of that package version.

❌ `"versionNumber": "3.2.0.LATEST"` on the package you are building — you are not building
a version that already exists.
✅ `NEXT` on your own package, `LATEST` (or a literal build number) on a dependency. And
know what `LATEST` costs: it re-resolves each time a version is created, so two builds of the
same commit can bind to different dependency builds. For anything you intend to promote,
pin the literal build number so the artefact is reproducible.

## Anti-Pattern 3: Adding `ancestorId` to an unlocked package

Ancestry is a **second-generation managed package** feature — it exists so a managed package
can be upgraded in place along a version lineage. Assistants add `ancestorId` or
`ancestorVersion` to unlocked package directories because both live in `sfdx-project.json`
and the guides sit next to each other. It does not belong there, and the resulting error
sends teams looking for a versioning problem that does not exist.

❌ `"ancestorVersion": "HIGHEST"` in an unlocked package's directory entry.
✅ Keep ancestry to managed 2GP. Where it does apply, the binding rule is that **only
package versions promoted to managed-released state can be listed as an ancestor** — so an
ancestry chain pointing at a version you never promoted blocks the next release until you
either promote that version or repoint the ancestor. `HIGHEST` is the maintenance-free form
because it tracks the highest promoted version without an edit per release.

Source: Specify a Package Ancestor in the Project File for a Second-Generation Managed Package — https://developer.salesforce.com/docs/atlas.en-us.pkg2_dev.meta/pkg2_dev/sfdx_dev_dev2gp_config_ancestors.htm

## Anti-Pattern 4: Promoting in the order the packages appear in the file

Promotion has to follow the dependency graph bottom-up: a package cannot be promoted while
it depends on a version that is still beta. Assistants generate a release script that
promotes in file order or alphabetically, which works by accident until someone reorders the
file.

❌ `for p in $(jq -r '.packageDirectories[].package' sfdx-project.json); do sf package version promote ...; done`
✅ Derive the order from the graph, then promote leaves first:

```bash
#!/usr/bin/env bash
# Promote bottom-up. Base packages have no dependencies; promote them, then dependents.
set -euo pipefail

for PKG in "Expense Manager - Util" "External Apex Library" "Expense Manager"; do
  VERSION_ID=$(sf package version list --packages "$PKG" --released false --json \
    | python3 -c "import json,sys; print(json.load(sys.stdin)['result'][-1]['SubscriberPackageVersionId'])")
  echo "promoting $PKG -> $VERSION_ID"
  sf package version promote --package "$VERSION_ID" --no-prompt
done
```

The order in the docs' own example is instructive: where a package depends on a util package
which in turn depends on an external library, the dependency list is written in install
order. Keep the promotion script and the `dependencies` arrays consistent with each other,
and derive both from one place rather than maintaining two orderings.

## Anti-Pattern 5: Believing a scratch org proved the install

The most expensive false confidence in packaging. A scratch org used for development
already has the dependency source pushed into it, so installing the dependent package
succeeds whether or not the dependency is declared. The same install into a clean org fails.

❌ "It installs in my scratch org" as the release gate.
✅ Install into an org that has never seen the source, in the order a subscriber would, and
smoke-test after:

```bash
sf org create scratch --definition-file config/project-scratch-def.json \
  --alias install-check --duration-days 1 --wait 10

for VERSION_ID in "$UTIL_VERSION_ID" "$CORE_VERSION_ID"; do
  sf package install --package "$VERSION_ID" --target-org install-check \
    --wait 20 --publish-wait 20 --no-prompt
done

sf apex run test --target-org install-check --test-level RunLocalTests --wait 30
```

A missing dependency declaration is invisible everywhere except a clean install, which is
precisely why it survives to production.

## Anti-Pattern 6: Letting a cycle form and planning to fix it later

Two packages that reference each other cannot both be versioned, and the failure arrives at
version-create time rather than at the moment the reference was added — often weeks later,
usually during a release. Assistants suggest "temporarily" adding a back-reference because
it makes the immediate compile problem go away.

❌ Add a reference from the base package back to the dependent to unblock one class.
✅ Extract the shared piece into a third package that both depend on. The refactor is
cheaper the day the cycle is created than on the day the release is blocked, and the
signal — a base package that suddenly needs to know about a consumer — is usually a sign the
code is in the wrong package rather than that the graph is wrong.

## Anti-Pattern 7: Treating a promoted version as something you can take back

Promotion is not reversible in the way a git tag is. Subscribers install specific `04t`
version ids, so a version that has been promoted and installed anywhere has to keep working;
the remedy for a bad release is a new version, not the removal of the old one.

❌ Promote early "to test the promotion step", or promote from a feature branch.
✅ Promote only what you intend to ship, from the commit you intend to ship, after the clean
install check above has passed. Keep the version id, the git commit and the release notes
recorded together — when a subscriber reports a defect against a version, the id is the only
thing that identifies which source built it.
