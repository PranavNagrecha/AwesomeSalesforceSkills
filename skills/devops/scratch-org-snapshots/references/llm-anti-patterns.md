# LLM Anti-Patterns — Scratch Org Snapshots

Scope: creating a snapshot and consuming it from a scratch org definition. Scratch org
lifecycle in general belongs to `devops/scratch-org-management`, pre-warmed org pools to
`devops/scratch-org-pools`, and the definition file's edition/features/settings keys to
`devops/org-shape-and-scratch-definition`. This file is about the snapshot itself.

## Anti-Pattern 1: Assuming a snapshot captures everything

The assumption that produces the hardest failures to diagnose, because the org looks
complete. A snapshot is a point-in-time copy that includes installed packages, features,
limits, licenses, metadata and data — and explicitly **cannot include connected apps,
external credentials or named credentials**. Every integration in the org comes back
unconfigured, and the tests that fail are callout tests, which everyone assumes are flaky.

❌ Snapshot the fully configured org and expect CI to be able to call out.
✅ Treat credentials as a post-create step that runs every time, on top of the snapshot:

```bash
sf org create scratch --snapshot ci-base --alias pr-check --duration-days 1 --wait 10

# Snapshots do not carry these. Recreate them on every org, from CI secrets.
sf project deploy start --metadata ExternalCredential,NamedCredential \
  --target-org pr-check --source-dir config/credentials
```

The corollary is a security property worth stating: because credential metadata does not
travel, a snapshot cannot leak one. That is a reason to keep the split rather than to look
for a way around it.

Source: Scratch Org Snapshots — what a snapshot includes, and the exclusion of connected apps, external credentials and named credentials — https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_snapshots_intro.htm

## Anti-Pattern 2: Treating the snapshot as unlimited and permanent

Generated pipelines create a snapshot per branch, per build, or on every merge, because the
command is cheap to write. Both the active count and the daily creation count are allocated
per Dev Hub **by edition** — a Developer Edition Dev Hub gets 3, an Enterprise Dev Hub 40,
Unlimited and Performance 100. And they are not permanent: **snapshots expire after 90 days**,
with the associated data deleted afterwards.

❌ `sf org create snapshot --name "snap-${GITHUB_SHA}"` on every push, against a Developer
Edition Dev Hub with an allocation of 3.
✅ A small number of long-lived, named snapshots refreshed on a schedule, with the name
reused rather than accumulated. Check the allocation for your Dev Hub's edition before
designing the refresh cadence — a design that works against an Enterprise Dev Hub can be
impossible on a Developer Edition one, and that is the difference between a working pipeline
and a broken pilot.

## Anti-Pattern 3: Trying to snapshot an org that cannot be snapshotted

Two restrictions catch teams building the "refresh the snapshot from the snapshot" loop that
seems obvious: you cannot create a snapshot from a scratch org that was **itself created
from a snapshot**, and you cannot create one from a **namespaced** scratch org. Namespaced
orgs can be created *from* a snapshot — the restriction is on the source, not the target.

❌ A nightly job that spins up an org from `ci-base`, pushes the day's changes, and snapshots
that org back over `ci-base`.
✅ Rebuild the source org from scratch each time, from the definition file and the install
list, then snapshot that. The rebuild is the slow path you were trying to avoid — but it runs
once nightly rather than once per PR, which is the whole point of the pattern.

## Anti-Pattern 4: A snapshot name the command will reject

Small and specific: the snapshot name has a maximum length of 15 characters. Assistants
generate descriptive names — `nightly-base-with-packages` — and the failure looks like a
permissions or Dev Hub problem to anyone who has not hit it.

❌ `--name nightly-base-with-packages`
✅ `--name ci-base` and put the description where the length is not constrained:

```bash
sf org create snapshot \
  --name ci-base \
  --source-org snapshot-source \
  --target-dev-hub my-dev-hub \
  --description 'CI base: 3 managed packages + baseline metadata, rebuilt nightly'
```

## Anti-Pattern 5: Treating creation as synchronous

`sf org create snapshot` starts an asynchronous process. The snapshot's status goes to
`InProgress` and only later becomes `Active`, and a scratch org created against a snapshot
that is not yet active fails. Generated pipelines run create-then-consume in consecutive
steps and produce an intermittent failure that reproduces only when the org is large.

❌ Create the snapshot and immediately create an org from it in the next step.
✅ Poll for `Active` before anything depends on it, and keep the previous snapshot usable
until the new one is confirmed:

```bash
sf org create snapshot --name ci-base-new --source-org snapshot-source \
  --target-dev-hub my-dev-hub --description 'nightly rebuild'

# Wait for Active. Do not swap consumers over until this returns.
until sf data query --target-org my-dev-hub \
        --query "SELECT Status FROM ScratchOrgSnapshot WHERE SnapshotName='ci-base-new'" \
        --json | grep -q '"Status":"Active"'; do
  echo "snapshot still building"
done
```

## Anti-Pattern 6: Baking a demo data set into the snapshot

Because a snapshot includes data, it is tempting to load everything a demo needs. Two costs
follow. Every org created from it carries that data, so tests pass against a shape that only
exists in the snapshot and real-world defects are masked. And the data is now version-
controlled nowhere — it lives only inside a snapshot that expires in 90 days, which makes
"why did this test start failing" unanswerable.

❌ Seed thousands of records into the source org before snapshotting.
✅ Put the minimum in the snapshot — the reference data that genuinely never changes — and
load test-specific data per test with a factory, where it is in source control and visible in
the diff. See `templates/apex/tests/` for the factory patterns.

## Anti-Pattern 7: No fallback when the snapshot is unusable

A snapshot is one more dependency between a developer and a working org, and the failure
modes are real — expiry, a Dev Hub allocation exhausted, a rebuild that failed overnight.
Pipelines that can only create from a snapshot stop entirely, and the outage looks like a
platform incident rather than a configuration one.

❌ `sf org create scratch --snapshot ci-base` as the only path, with no alternative.
✅ Keep the definition-file path working and fall back to it, accepting the slower bring-up:

```bash
sf org create scratch --snapshot ci-base --alias pr-check --duration-days 1 --wait 10 \
  || {
    echo "snapshot unavailable, falling back to a full build"
    sf org create scratch --definition-file config/project-scratch-def.json \
      --alias pr-check --duration-days 1 --wait 20
    bash scripts/install-packages.sh pr-check
  }
```

Keeping that path exercised — on a schedule, not only in an emergency — is what stops it
from having rotted by the time it is needed.
