# LLM Anti-Patterns — SFDX Monorepo Patterns

Scope: one repository holding several package directories, and the CI that has to work out
what changed. The dependency graph between those packages belongs to
`devops/packaging-dependency-graph`; the package lifecycle belongs to
`devops/unlocked-package-development` and `devops/package-development-strategy`. This file
covers the layout and the failures the layout causes.

## Anti-Pattern 1: More than one `default: true`

The rule is exact and the failure is immediate: **you can have only one default path**. With
a single path the default is assumed and the key can be omitted entirely; with multiple
paths you must nominate one. Assistants generating a multi-package file copy the
single-package example once per package, `default: true` included, and produce a project the
CLI refuses to read.

**Wrong** — every directory claiming to be the default:

```json
{
  "packageDirectories": [
    { "path": "packages/sales-core",   "default": true, "package": "sales-core" },
    { "path": "packages/service-core", "default": true, "package": "service-core" },
    { "path": "packages/ai-actions",   "default": true, "package": "ai-actions" }
  ]
}
```

**Right** — exactly one default, and it is a decision rather than a formality:

```json
{
  "namespace": "",
  "sfdcLoginUrl": "https://login.salesforce.com",
  "sourceApiVersion": "61.0",
  "packageDirectories": [
    { "path": "packages/base-utils",   "default": true,  "package": "base-utils",
      "versionNumber": "1.4.0.NEXT" },
    { "path": "packages/sales-core",   "default": false, "package": "sales-core",
      "versionNumber": "2.1.0.NEXT",
      "dependencies": [ { "package": "base-utils", "versionNumber": "1.4.0.LATEST" } ] },
    { "path": "packages/service-core", "default": false, "package": "service-core",
      "versionNumber": "3.0.0.NEXT",
      "dependencies": [ { "package": "base-utils", "versionNumber": "1.4.0.LATEST" } ] }
  ],
  "packageAliases": {
    "base-utils": "0Ho...",
    "sales-core": "0Ho...",
    "service-core": "0Ho..."
  }
}
```

Source: Salesforce DX Project Configuration — "You can have only one default path (package directory)" — https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_ws_config.htm

## Anti-Pattern 2: Not knowing what the default directory actually decides

Because the key looks decorative, its consequence gets missed: metadata retrieved from an
org without an explicit destination lands in the default directory. In a monorepo that means
a `sf project retrieve start` after a Setup change silently files a Flow into `base-utils`,
and the next version create ships it in the wrong package — where it is now the wrong team's
problem, and removing it from a package is considerably harder than adding it.

❌ Retrieve first, sort out the directory later.
✅ Retrieve with an explicit target, and make the default the least surprising package —
typically the base or utility package, where an accidental arrival is most visible in review:

```bash
sf project retrieve start \
  --metadata Flow:Case_Escalation \
  --target-org uat \
  --output-dir packages/service-core        # never rely on the default for a retrieve
```

Then check the diff before committing. A file appearing under a package that nobody in the
PR owns is the signal, and it only shows up if someone is looking.

## Anti-Pattern 3: Splitting one object's fields across packages by accident

The defect unique to a Salesforce monorepo. Two packages both add fields to `Account`, which
is legal, but the object's own definition can only live in one of them — and each package's
directory ends up with a partial `Account/` folder. Assistants generate the layout by
feature and never notice, because in a development scratch org with everything pushed it
works perfectly.

❌ `packages/sales-core/.../objects/Account/fields/Sales_Region__c.field-meta.xml` and
`packages/service-core/.../objects/Account/fields/Support_Tier__c.field-meta.xml` with no
declared relationship between the two packages.
✅ Decide an owner for every shared object and make the extension packages depend on it:

```text
packages/base-utils/main/default/objects/Account/        <- owns the object, shared fields
packages/sales-core/main/default/objects/Account/fields/ <- extension fields only, depends on base-utils
packages/service-core/main/default/objects/Account/fields/
```

The dependency is what makes install order deterministic. Without it the packages install in
whatever order someone chose, and the one that arrives first defines what the others get.

## Anti-Pattern 4: Shipping tooling to production because it sat inside a package directory

Anything under a `packageDirectories` path is package content. Test data factories used only
by CI, scratch org setup scripts, sample data, migration one-offs — put any of them inside a
package folder and they are deployed to every org that installs it, where they linger as
metadata nobody can explain years later.

❌ `packages/sales-core/main/default/classes/DemoDataSeeder.cls`
✅ Keep tooling outside every package path, so it is in the repo but not in the artefact:

```text
repo/
├── packages/          <- every entry in packageDirectories lives here
│   ├── base-utils/
│   ├── sales-core/
│   └── service-core/
├── tools/             <- NOT a packageDirectory: seeders, one-offs, local scripts
├── config/            <- scratch org definition files
└── sfdx-project.json
```

Test classes are the exception worth being precise about: they belong inside the package,
because deploying Apex to production requires at least 75% coverage and those tests are what
provide it. Seed *data* and developer convenience scripts do not.

## Anti-Pattern 5: Change detection by directory name only

The obvious implementation — map changed paths to package names and build those — is right
until a base package changes. A change to `base-utils` can break `sales-core` without
touching a single file in it, and a diff-only rule will not build `sales-core` at all.

❌ `git diff --name-only origin/main... | cut -d/ -f2 | sort -u` as the whole rule.
✅ Expand the changed set through the dependency graph before deciding what to build:

```bash
#!/usr/bin/env bash
set -euo pipefail

CHANGED=$(git diff --name-only "origin/${GITHUB_BASE_REF}...HEAD" \
          | awk -F/ '$1=="packages" {print $2}' | sort -u)

# Anything that depends, transitively, on something changed must also be built.
AFFECTED=$(python3 - "$CHANGED" <<'PY'
import json, sys
changed = set(sys.argv[1].split())
proj = json.load(open('sfdx-project.json'))
# path segment -> package name, and package name -> declared dependencies
by_path = {d['path'].split('/')[-1]: d for d in proj['packageDirectories']}
deps = {d.get('package'): [x['package'] for x in d.get('dependencies', [])]
        for d in proj['packageDirectories']}

affected, frontier = set(), {by_path[c]['package'] for c in changed if c in by_path}
while frontier:
    pkg = frontier.pop()
    if pkg in affected:
        continue
    affected.add(pkg)
    frontier |= {p for p, ds in deps.items() if pkg in ds}
print(' '.join(sorted(affected)))
PY
)
echo "affected=$AFFECTED" >> "$GITHUB_OUTPUT"
```

The build order within that set is the dependency order, not the order the script emitted
them. Getting the set right and the order wrong fails just as loudly.

## Anti-Pattern 6: One `sourceApiVersion` treated as a per-package setting

`sourceApiVersion` is a project-level key, not a per-directory one. Assistants add it inside
each `packageDirectories` entry expecting per-package pinning, and are then surprised when
changing it in one place moves all of them.

❌ `"sourceApiVersion"` repeated inside each package directory entry.
✅ Set it once at the top level and treat an API version bump as a repo-wide change with its
own PR — one that rebuilds every package, because it can change behaviour in all of them.
A package that needs a genuinely different API version is a signal it should be its own
repository, not a signal to fight the schema.

## Anti-Pattern 7: Validating the whole repository on every push

The reflex fix when change detection is hard. It is correct and unaffordable: a full
validation with `RunLocalTests` runs every test in the org for every package on every push,
so PR feedback degrades until people stop waiting for it — which removes the gate more
effectively than deleting it would.

❌ One job that validates every package with `--test-level RunLocalTests` on every push.
✅ Scope the validation to the affected set, and scope the test level to the risk. Use
`RunSpecifiedTests` with the affected packages' test classes for PR feedback, and keep the
full `RunLocalTests` run for the pre-production validation where the cost is justified. Note
that `RunLocalTests` excludes tests from installed managed and unlocked packages, which is
usually what you want — `RunAllTestsInOrg` adds tests you neither own nor can fix.

Source: Metadata API `deploy()` — `testLevel` values and their scope — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_deploy.htm
