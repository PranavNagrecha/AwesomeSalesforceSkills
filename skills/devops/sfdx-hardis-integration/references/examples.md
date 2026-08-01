# Examples — sfdx-hardis Integration

Both examples deliberately keep the plugin's own command surface to a minimum and put the
platform operations in plain `sf` commands. That is not stylistic: the plugin is third-party
open source whose commands and flags change on its own schedule, while the `sf` commands
below are covered by Salesforce documentation. Verify every plugin invocation against
`sf hardis --help` for the version you have installed before it goes into a pipeline.

## Example 1: A pinned toolchain, and drift detection whose scope is stated

**Context:** Admins were making changes directly in production. The team wanted a daily
report of anything in the org that did not match the repository.

**Problem:** The first pipeline installed the plugin unpinned and reported "no drift"
convincingly for three weeks — during which a Flow and two permission sets had in fact
changed. Two causes. A plugin release mid-period changed the default scope of what was
retrieved, with no change on the team's side. And the report presented an absence of diffs
as an absence of drift, when some of what mattered was not being retrieved at all.

**Solution:** Pin both layers, record the versions, and publish the scope alongside the
result.

```yaml
name: Daily org drift
on:
  schedule:
    - cron: '0 4 * * *'
  workflow_dispatch:

jobs:
  monitor:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install a known toolchain and record it
        run: |
          set -euo pipefail
          npm install --global @salesforce/cli@2.x.y      # pin the CLI
          sf plugins install sfdx-hardis@<exact-version>  # pin the plugin
          sf version --verbose
          sf plugins inspect sfdx-hardis                  # in the log, for a later bisect

      - name: Authenticate — the pipeline owns the credential, not the plugin
        env:
          SF_JWT_KEY:   ${{ secrets.SF_JWT_KEY_PROD }}    # [REDACTED]
          SF_CLIENT_ID: ${{ secrets.SF_CLIENT_ID_PROD }}  # [REDACTED]
          SF_USERNAME:  ${{ vars.SF_USERNAME_PROD }}
        run: |
          set -euo pipefail
          umask 077
          KEYFILE="$(mktemp)"; trap 'rm -f "$KEYFILE"' EXIT
          printf '%s' "$SF_JWT_KEY" | base64 -d > "$KEYFILE"
          sf org login jwt --client-id "$SF_CLIENT_ID" --jwt-key-file "$KEYFILE" \
            --username "$SF_USERNAME" --alias prod

      - name: Retrieve the declared scope with plain CLI, so the scope is auditable
        run: |
          # manifest/monitor-package.xml states exactly what is compared. An absence of
          # diffs is only meaningful for the types named in it.
          sf project retrieve start \
            --manifest manifest/monitor-package.xml \
            --target-org prod \
            --output-dir .monitor/retrieved

      - name: Report drift with the scope attached
        run: |
          {
            echo "## Drift report"
            echo "Scope: $(grep -c '<name>' manifest/monitor-package.xml) metadata types"
            echo "Types NOT compared are listed in manifest/monitor-exclusions.md"
            git --no-pager diff --stat --no-index force-app .monitor/retrieved || true
          } >> "$GITHUB_STEP_SUMMARY"
```

**Why it works:** the comparison scope is a file in the repository rather than a plugin
default, so it appears in diffs and can be reviewed. That matters more than it sounds:
a drift monitor concludes things by retrieving and diffing, so anything not retrievable at
your API version silently reports as unchanged. Check Metadata Coverage before treating an
absence as evidence.

**Why the pipeline authenticates, not the plugin:** CI has no human to complete a browser
login, which is why the JWT bearer flow is the documented approach. Keeping that step in your
own YAML means the credential arrangement survives the plugin being upgraded, reconfigured or
replaced.

**Managed-package noise:** vendor components change on the vendor's schedule and generate
real but unactionable diffs. Maintain the ignore list as a reviewed file rather than a
growing set of muted alerts — the failure mode is that noise suppression quietly becomes
blindness, and the monitor is still cited as evidence afterwards.

---

## Example 2: A pre-merge validation where the test level is explicit

**Context:** The team wanted the plugin's deployment ergonomics on pull requests.

**Problem:** Adopting the wrapper's defaults made validations noticeably faster, which was
taken as a win until a production deploy failed on tests that the PR gate had not run. The
wrapper had selected a narrower test level than the team assumed. Nobody had checked, because
the wrapper's output did not say which level it used.

**Solution:** Set the level explicitly, and state the platform requirement the wrapper cannot
change.

```yaml
      - name: Validate — check-only, explicit test level
        run: |
          # checkOnly: performs the deployment against the target without saving components.
          sf project deploy validate \
            --target-org staging \
            --source-dir force-app \
            --test-level RunSpecifiedTests \
            --tests $(cat manifest/pr-tests.txt | tr '\n' ' ') \
            --wait 60

      - name: Pre-production gate — the level the platform defaults to for prod
        if: github.base_ref == 'main'
        run: |
          sf project deploy validate \
            --target-org preprod \
            --source-dir force-app \
            --test-level RunLocalTests \
            --wait 90
```

**Why it works:** whatever tool issues the call, the underlying operation is a Metadata API
deployment and `testLevel` decides what runs. `RunLocalTests` executes every test in the org
except those from installed managed and unlocked packages, and is the documented default for
production deployments containing Apex classes or triggers. `RunSpecifiedTests` runs only
what you name — appropriate for fast PR feedback and not a substitute for the pre-production
run. `NoTestRun` applies only to development environments and is unavailable for production.

**What no wrapper changes:** deploying Apex to production requires unit tests covering at
least 75% of the org's Apex, and those tests must pass. A tool that makes validation faster
by running fewer tests has moved the failure later, not removed it.

**Before adopting any plugin command in a pipeline:**

```bash
sf plugins inspect sfdx-hardis    # which version is this
sf hardis --help                  # what commands exist in it
sf hardis <topic> --help          # what flags, and what the defaults are
```

If a suggested command — from a blog, a model, or this file — disagrees with `--help`, the
installed version wins. Treat the plugin's own documentation as authoritative for its
behaviour and Salesforce documentation as authoritative for the platform's, and do not let a
convenient wrapper become the reason nobody on the team can say what the deployment actually
did.
