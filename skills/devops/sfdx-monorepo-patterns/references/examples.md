# Examples — SFDX Monorepo Patterns

## Example 1: Splitting one force-app into three packages without splitting the shared object

**Context:** A single `force-app` directory with roughly 800 metadata files, three teams,
and one Account object that all three had extended.

**Problem:** Every deploy was all-or-nothing and every PR touched files three teams cared
about. The first split attempt made it worse: each team's package got its own partial
`objects/Account/` folder, the object definition ended up in whichever package happened to
be created first, and installs into a clean org started failing depending on order — a
failure invisible in development, because every scratch org had all three sets of source
pushed into it.

**Solution:** A base package that owns anything shared, feature packages that depend on it,
and tooling kept outside every package path.

```text
repo/
├── packages/
│   ├── base-utils/                       <- owns shared objects and cross-cutting Apex
│   │   └── main/default/
│   │       ├── objects/Account/          <- the object definition lives HERE, once
│   │       └── classes/                  <- TriggerHandler, logging, security utils
│   ├── sales-core/
│   │   └── main/default/objects/Account/fields/   <- extension fields only
│   └── service-core/
│       └── main/default/objects/Account/fields/
├── tools/                                <- NOT a packageDirectory: seeders, one-offs
├── config/
│   └── project-scratch-def.json
└── sfdx-project.json
```

```json
{
  "namespace": "",
  "sfdcLoginUrl": "https://login.salesforce.com",
  "sourceApiVersion": "61.0",
  "packageDirectories": [
    {
      "path": "packages/base-utils",
      "default": true,
      "package": "base-utils",
      "versionName": "Base Utils 1.4",
      "versionNumber": "1.4.0.NEXT",
      "definitionFile": "config/project-scratch-def.json"
    },
    {
      "path": "packages/sales-core",
      "default": false,
      "package": "sales-core",
      "versionNumber": "2.1.0.NEXT",
      "definitionFile": "config/project-scratch-def.json",
      "dependencies": [
        { "package": "base-utils", "versionNumber": "1.4.0.LATEST" }
      ]
    },
    {
      "path": "packages/service-core",
      "default": false,
      "package": "service-core",
      "versionNumber": "3.0.0.NEXT",
      "definitionFile": "config/project-scratch-def.json",
      "dependencies": [
        { "package": "base-utils", "versionNumber": "1.4.0.LATEST" }
      ]
    }
  ],
  "packageAliases": {
    "base-utils": "0HoB00000004AAAKA2",
    "sales-core": "0HoB00000004BBBKA2",
    "service-core": "0HoB00000004CCCKA2"
  }
}
```

**Why it works:** exactly one directory carries `default: true`, which is the documented
rule — with several paths you have to nominate one, and more than one is rejected. The
shared object has a single owner, so install order stops being luck: both feature packages
declare a dependency on `base-utils`, and the platform enforces the order rather than a
runbook.

**Why the default is `base-utils` specifically:** the default directory is where retrieved
metadata lands when no destination is given. Pointing it at the base package means an
accidental `sf project retrieve start` files the component somewhere every reviewer is
watching, rather than quietly into a feature team's package. It does not remove the need to
retrieve with `--output-dir`; it makes the mistake visible.

**Why `tools/` is outside `packages/`:** everything under a `packageDirectories` path is
package content and ships to every org that installs it. Seed data scripts and migration
one-offs left inside a package become permanent metadata in a subscriber org. Test classes
are the deliberate exception — they belong inside the package, because deploying Apex to
production requires at least 75% coverage and they are what supplies it.

---

## Example 2: Building only what changed, without missing what a base change broke

**Context:** CI validated all three packages on every push, taking long enough that
developers stopped reading the results.

**Problem:** The first attempt at change detection mapped changed file paths to package
names and built only those. It cut the time and introduced a worse failure: a change to
`base-utils` alone built only `base-utils`, so a signature change that broke `sales-core`
merged green and failed in the release build a week later.

**Solution:** Compute the changed set, then expand it through the declared dependency graph
before choosing the matrix.

```yaml
name: Validate affected packages
on:
  pull_request:
    branches: [main]

jobs:
  detect:
    runs-on: ubuntu-latest
    outputs:
      packages: ${{ steps.affected.outputs.packages }}
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0          # needed for a real diff against the base branch

      - id: affected
        run: |
          set -euo pipefail
          CHANGED=$(git diff --name-only "origin/${GITHUB_BASE_REF}...HEAD" \
                    | awk -F/ '$1=="packages" {print $2}' | sort -u | tr '\n' ' ')
          python3 - "$CHANGED" <<'PY' >> "$GITHUB_OUTPUT"
          import json, os, sys
          changed = set(sys.argv[1].split())
          proj = json.load(open('sfdx-project.json'))
          dirs = proj['packageDirectories']
          by_leaf = {d['path'].split('/')[-1]: d['package'] for d in dirs}
          deps = {d['package']: [x['package'] for x in d.get('dependencies', [])]
                  for d in dirs}

          affected, frontier = set(), {by_leaf[c] for c in changed if c in by_leaf}
          while frontier:                       # walk consumers, not just the changed set
              pkg = frontier.pop()
              if pkg in affected:
                  continue
              affected.add(pkg)
              frontier |= {p for p, ds in deps.items() if pkg in ds}

          # Emit in declaration order so dependencies are validated before dependents.
          ordered = [d['package'] for d in dirs if d['package'] in affected]
          print('packages=' + json.dumps(ordered))
          PY

  validate:
    needs: detect
    if: needs.detect.outputs.packages != '[]'
    runs-on: ubuntu-latest
    strategy:
      max-parallel: 1                    # dependency order matters; do not fan out blindly
      matrix:
        package: ${{ fromJSON(needs.detect.outputs.packages) }}
    steps:
      - uses: actions/checkout@v4
      - name: Validate ${{ matrix.package }}
        run: |
          sf project deploy validate \
            --target-org uat \
            --source-dir "packages/${{ matrix.package }}" \
            --test-level RunSpecifiedTests \
            --tests $(cat "packages/${{ matrix.package }}/tests.txt" | tr '\n' ' ') \
            --wait 60
```

**Why it works:** the graph expansion is the part a path-based rule cannot do. Changing
`base-utils` puts `sales-core` and `service-core` into the affected set even though no file
under them changed, which is exactly the case the naive version missed. Emitting in
declaration order — and not fanning the matrix out in parallel — keeps dependencies
validated before their dependents.

**Why `RunSpecifiedTests` here and not `RunLocalTests`:** `RunLocalTests` runs every test in
the org except those from installed managed and unlocked packages. That is the right level
for a pre-production validation and the wrong level for PR feedback, where it makes the gate
slow enough to be ignored. Scope the test level to the risk: specified tests on a PR, local
tests before production. `RunAllTestsInOrg` is rarely correct in either place — it adds
managed-package tests you neither own nor can fix.

**What still needs a full build:** a `sourceApiVersion` bump. It is a project-level key
rather than a per-directory one, so changing it affects every package at once and deserves
its own PR that rebuilds all of them.
