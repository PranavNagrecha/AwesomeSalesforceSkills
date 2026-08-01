# Examples — Scratch Org Snapshots

## Example 1: Consuming a snapshot, and putting back what it cannot carry

**Context:** A CI pipeline whose bring-up was dominated by installing three managed packages
into every PR's scratch org.

**Problem:** Switching to a snapshot cut the create time as expected, and then every callout
test started failing. The cause was not flakiness: a snapshot includes installed packages,
features, limits, licenses, metadata and data, but it cannot include connected apps,
external credentials or named credentials. The org came back complete apart from every
integration.

**Solution:** Consume the snapshot for the expensive parts and treat credentials as a
post-create step that runs on every org.

```json
// config/ci-scratch-def.json — the snapshot replaces edition/features, it does not add to them
{
  "orgName": "CI PR check",
  "snapshot": "ci-base"
}
```

```yaml
name: PR validation
on: pull_request

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Create the org from the snapshot, with a fallback
        run: |
          set -euo pipefail
          sf org create scratch \
            --definition-file config/ci-scratch-def.json \
            --alias pr-check --duration-days 1 --wait 10 \
          || {
            echo "snapshot unavailable — falling back to a full build"
            sf org create scratch \
              --definition-file config/project-scratch-def.json \
              --alias pr-check --duration-days 1 --wait 20
            bash scripts/install-packages.sh pr-check
          }

      - name: Restore what the snapshot cannot carry
        run: |
          # Connected apps, external credentials and named credentials are NOT in a snapshot.
          sf project deploy start \
            --metadata ExternalCredential,NamedCredential \
            --source-dir config/credentials \
            --target-org pr-check

      - name: Push the PR's source and test
        run: |
          sf project deploy start --source-dir force-app --target-org pr-check
          sf apex run test --target-org pr-check --test-level RunLocalTests --wait 30

      - name: Always clean up
        if: always()
        run: sf org delete scratch --target-org pr-check --no-prompt
```

**Why it works:** the snapshot carries the slow, stable part — package installs and baseline
metadata — while the fast, volatile part is applied per org. The credential step is not a
workaround for a limitation; it is the reason a snapshot cannot leak a credential, which is
worth keeping rather than engineering around.

**Why the fallback exists:** a snapshot is another dependency between a developer and a
working org. It expires after 90 days, the Dev Hub's allocation can be exhausted, and an
overnight rebuild can fail. A pipeline that can only create from a snapshot stops entirely
when any of those happen, and the outage reads as a platform incident. Exercise the fallback
on a schedule so it has not rotted by the time it is needed.

---

## Example 2: A nightly rebuild that does not eat the Dev Hub's allocation

**Context:** Managed packages and baseline metadata that changed roughly weekly, against a
Dev Hub whose snapshot allocation is small.

**Problem:** The first version created a snapshot per merge, named with the commit SHA. The
allocation was exhausted within a day — both the active count and the daily creation count
are per Dev Hub and depend on edition, and a Developer Edition Dev Hub gets 3 where an
Enterprise Dev Hub gets 40. The second version tried to refresh in place by spinning an org
up *from* `ci-base`, pushing changes, and snapshotting it back, which is not allowed: you
cannot snapshot a scratch org that was itself created from a snapshot.

**Solution:** Rebuild the source org from the definition file each night, snapshot that, and
swap consumers over only once the new snapshot reports `Active`.

```yaml
name: Rebuild CI snapshot
on:
  schedule:
    - cron: '0 2 * * *'
  workflow_dispatch:

jobs:
  rebuild:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Build the source org from scratch, never from a snapshot
        run: |
          set -euo pipefail
          sf org create scratch \
            --definition-file config/project-scratch-def.json \
            --alias snapshot-source --duration-days 1 --wait 30
          bash scripts/install-packages.sh snapshot-source
          sf project deploy start --source-dir force-app --target-org snapshot-source
          # Minimal reference data only — see the note below on demo data.
          sf data import tree --plan data/reference-plan.json --target-org snapshot-source

      - name: Create the snapshot (name is capped at 15 characters)
        run: |
          sf org create snapshot \
            --name ci-base-new \
            --source-org snapshot-source \
            --target-dev-hub my-dev-hub \
            --description 'CI base: 3 managed packages + baseline metadata, rebuilt nightly'

      - name: Wait for Active before anything consumes it
        run: |
          set -euo pipefail
          for _ in $(seq 1 60); do
            STATUS=$(sf data query --target-org my-dev-hub --json \
              --query "SELECT Status FROM ScratchOrgSnapshot WHERE SnapshotName='ci-base-new'" \
              | python3 -c "import json,sys; r=json.load(sys.stdin)['result']['records']; \
                            print(r[0]['Status'] if r else 'Missing')")
            echo "status: $STATUS"
            [ "$STATUS" = "Active" ] && exit 0
            [ "$STATUS" = "Error" ] && exit 1
          done
          echo "snapshot did not become Active in time"; exit 1

      - name: Promote the new snapshot and retire the old one
        run: |
          # Only after Active: delete the previous snapshot, then rename or repoint consumers.
          # Keeping the old one until this point means a failed rebuild is not an outage.
          sf org delete snapshot --snapshot ci-base --target-dev-hub my-dev-hub --no-prompt || true

      - name: Always release the source org
        if: always()
        run: sf org delete scratch --target-org snapshot-source --no-prompt
```

**Why it works:** the nightly rebuild pays the slow path once instead of once per pull
request, which is the entire economic argument for snapshots. Rebuilding the source org from
the definition file each time avoids the snapshot-of-a-snapshot restriction and, more
usefully, means the definition file stays exercised — a snapshot lineage that is never
rebuilt from source hides the moment the definition stops working.

**Why the status poll is not optional:** snapshot creation is asynchronous. The status moves
to `InProgress` and only later to `Active`, and creating an org against a non-active snapshot
fails. Create-then-consume in consecutive steps is an intermittent failure that reproduces
only when the source org is large enough for the timing to matter.

**Why the reference data is minimal:** a snapshot includes data, which makes it tempting to
bake in everything a demo needs. That data then exists only inside an artefact that expires
after 90 days and is in no diff, so "why did this test start failing" becomes unanswerable.
Keep genuinely static reference data in the snapshot and build test-specific records per test
with a factory — see `templates/apex/tests/`.

**On naming:** `ci-base` fits the 15-character maximum; a descriptive name like
`nightly-base-with-packages` does not, and the rejection reads like a Dev Hub permissions
problem to anyone who has not hit it before. Put the detail in `--description`.
