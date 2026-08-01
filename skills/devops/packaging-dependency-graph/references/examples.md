# Examples — Packaging Dependency Graph

## Example 1: A three-package graph with the dependency actually declared

**Context:** Three second-generation packages — a util package, a core package that uses it,
and an external Apex library the core package also needs.

**Problem:** `service-core` broke in a customer org every time `sales-core` shipped. In
development nothing was wrong, because the developers' scratch orgs had both sets of source
pushed into them, so the dependency was satisfied by accident. The `dependencies` block was
empty, and the only thing holding the two packages together was that they happened to be
installed in the right order by hand.

**Solution:** Declare the graph, pin what must be reproducible, and let the aliases carry
the version ids.

```json
{
  "namespace": "",
  "sfdcLoginUrl": "https://login.salesforce.com",
  "sourceApiVersion": "61.0",
  "packageDirectories": [
    {
      "path": "util",
      "default": true,
      "package": "Expense Manager - Util",
      "versionName": "Summer '24",
      "versionNumber": "4.7.0.NEXT",
      "definitionFile": "config/scratch-org-def.json"
    },
    {
      "path": "exp-core",
      "default": false,
      "package": "Expense Manager",
      "versionName": "v 3.2",
      "versionNumber": "3.2.0.NEXT",
      "definitionFile": "config/scratch-org-def.json",
      "dependencies": [
        { "package": "Expense Manager - Util", "versionNumber": "4.7.0.LATEST" },
        { "package": "External Apex Library - 1.0.0.4" }
      ]
    }
  ],
  "packageAliases": {
    "Expense Manager - Util": "0HoB00000004CFpKAM",
    "External Apex Library@1.0.0.4": "04tB0000000IB1EIAW",
    "Expense Manager": "0HoB00000004CFuKAM"
  }
}
```

**Why it works:** the dependency is now a property of the artefact rather than of whoever
ran the install. `sf package version create` on `Expense Manager` resolves and records the
dependency into the version, so a subscriber installing that `04t` gets told what else it
needs instead of getting a runtime failure.

**The two dependency forms, and why both appear:** the first entry names a package and pins
its version separately, so it can float to the latest build of `4.7.0`. The second carries
the version inside the alias — `External Apex Library@1.0.0.4` resolves to a specific `04t`
subscriber package version id, which is how you depend on something you do not build.

**`NEXT` versus `LATEST`, which is the reversal that costs a day:** `NEXT` sits on *your*
package's `versionNumber` and takes the next build number when you create a version.
`LATEST` sits on a *dependency* and resolves to the newest existing build of that version.
They are not interchangeable, and `3.2.0.LATEST` on the package you are building is asking
to build a version that already exists.

**When to stop using `LATEST`:** it re-resolves on every version create, so two builds of
the same commit can bind to different dependency builds. That is convenient during
development and unacceptable for anything you promote — pin the literal build number for
release candidates so the artefact is reproducible from the commit.

---

## Example 2: Proving the install order against an org that has never seen the source

**Context:** A release that had passed every test, in scratch orgs that the team had been
developing in all sprint.

**Problem:** The first production install failed on a missing dependency. Nobody had
installed the packages into a clean org in the subscriber's order — every development
scratch org already contained the source, so the dependent package installed fine whether or
not the dependency was declared. The gate everyone trusted could not detect the defect it
was supposed to catch.

**Solution:** A CI job that builds a genuinely empty org, installs in dependency order, and
runs tests against the installed metadata rather than against pushed source.

```yaml
name: Clean-org install check
on:
  pull_request:
    branches: [main]

jobs:
  install-order:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Create an org that has never seen this source
        run: |
          sf org create scratch \
            --definition-file config/project-scratch-def.json \
            --alias install-check --duration-days 1 --wait 10

      - name: Install bottom-up, in the order a subscriber would
        run: |
          set -euo pipefail
          # Order comes from the dependency graph, never from file order or alphabetical.
          for VERSION_ID in "$EXTERNAL_LIB_04T" "$UTIL_04T" "$CORE_04T"; do
            echo "installing $VERSION_ID"
            sf package install --package "$VERSION_ID" \
              --target-org install-check \
              --wait 20 --publish-wait 20 --no-prompt
          done

      - name: Smoke-test the installed metadata
        run: |
          sf apex run test --target-org install-check \
            --test-level RunLocalTests --wait 30 --result-format human

      - name: Always clean up
        if: always()
        run: sf org delete scratch --target-org install-check --no-prompt
```

**Why it works:** the org is the control. Because nothing was ever pushed into it, the only
way the core package can install is if its dependencies are declared and available — which
is exactly the condition production will impose. A missing declaration fails here instead of
in a customer org.

**Promotion order follows the same graph:** a package cannot be promoted while it depends
on a version that is still beta, so promotion runs leaves-first for the same reason install
does.

```bash
#!/usr/bin/env bash
set -euo pipefail

# Bottom-up: nothing is promoted before the things it depends on.
for PKG in "External Apex Library" "Expense Manager - Util" "Expense Manager"; do
  VERSION_ID=$(sf package version list --packages "$PKG" --released false --json \
    | python3 -c "import json,sys; print(json.load(sys.stdin)['result'][-1]['SubscriberPackageVersionId'])")
  echo "promoting $PKG -> $VERSION_ID"
  sf package version promote --package "$VERSION_ID" --no-prompt
done
```

**Keep one ordering, not two:** the `dependencies` arrays and the promotion script encode
the same graph. Maintaining them independently means they drift, and the drift is only
detectable at release time. Derive the promotion order from the project file, or at minimum
review them together.

**On promoting early:** promotion is not a git tag you can move. Subscribers install a
specific `04t`, so a promoted version that reached anyone has to keep working — the remedy
for a bad release is a new version. Promote only the commit you intend to ship, after this
clean-install job is green, and record the version id alongside the commit so a defect
report against a version can be traced to source.
