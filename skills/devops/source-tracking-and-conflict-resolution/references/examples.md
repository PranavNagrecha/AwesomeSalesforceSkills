# Examples — Source Tracking and Conflict Resolution

---

## Example 1: Resolving a Pull Conflict After Admin Makes Declarative Changes in Sandbox

**Context:** A developer has a local branch with edits to `AccountLayout.layout-meta.xml`. Meanwhile, an admin logged into the same Developer sandbox and modified the same page layout directly in Setup. When the developer tries to pull the latest org state, the CLI aborts.

**Problem:**

```
Error (CONFLICT): The following files conflict with changes in the org:
  force-app/main/default/layouts/Account-Account Layout.layout-meta.xml
To overwrite your local changes, run again with --ignore-conflicts.
```

The developer cannot retrieve the org's version without deciding what happens to their local edits.

**Solution:**

```bash
# Step 1: Stash or commit the local version to Git so it is not lost
git add force-app/main/default/layouts/Account-Account\ Layout.layout-meta.xml
git stash

# Step 2: Retrieve the org version, overwriting the local file
sf project retrieve start --ignore-conflicts --target-org devSandbox

# Step 3: Compare the stashed version to see if any local changes need to be re-applied
git stash show -p

# Step 4: If local edits need to be merged back in, apply them manually, then deploy
sf project deploy start --target-org devSandbox
```

**Why it works:** `--ignore-conflicts` on retrieve tells the CLI to accept the org's revision counter as the new baseline and overwrite the conflicting local file. The tracking database in `.sf/orgs/<orgId>/maxRevision.json` is updated to reflect the org's current state. Because the developer stashed first, no work is permanently lost.

---

## Example 2: Recovering Source Tracking After Sandbox Refresh

**Context:** A QA sandbox was refreshed on Friday. On Monday, a developer runs `sf project retrieve start --target-org qaSandbox` and sees every metadata component in the project listed as a conflict — hundreds of files. Nothing was changed over the weekend.

**Problem:**

The sandbox refresh assigned a new org ID to the sandbox. The developer's alias `qaSandbox` now resolves to the new org ID, but `.sf/orgs/` still contains only the old org ID directory. The CLI finds no matching tracking state for the new org ID and treats all local files as conflicting with the empty tracking baseline.

**Solution:**

```bash
# Step 1: Check what org IDs are in the local tracking directory
ls .sf/orgs/
# Output: 00D000000000001AAA/   (old org ID)

# Step 2: Confirm the new org ID from the refreshed sandbox
sf org display --target-org qaSandbox
# Output shows OrgId: 00D000000000002BBB

# Step 3: Delete the stale tracking directory
rm -rf .sf/orgs/00D000000000001AAA/

# Step 4: Retrieve from the refreshed sandbox to rebuild tracking state
sf project retrieve start --target-org qaSandbox

# Step 5: Confirm status is clean
sf project deploy start --dry-run --target-org qaSandbox
```

**Why it works:** Deleting the stale directory removes the outdated revision counter entries. When the CLI retrieves from the refreshed org, it creates a new `.sf/orgs/00D000000000002BBB/` directory and rebuilds `maxRevision.json` from the org's current `SourceMember` records. After the initial retrieve, local and org are in sync with no conflicts.

---

## Example 3: Previewing What Will Be Deployed Before Pushing to a Shared Sandbox

**Context:** A developer wants to confirm exactly which components will be deployed to a shared integration sandbox before running the actual deploy. The sandbox is used by multiple developers and a mistaken deploy could disrupt others.

**Problem:** Running `sf project deploy start` without confirmation could push unexpected components if the tracking state is unclear.

**Solution:**

```bash
# Dry-run deploy — validates full deployment including Apex tests, shows component list, does not write to org
sf project deploy start --dry-run --target-org integrationSandbox

# Sample output excerpt:
# Component Summary
# ─────────────────────────────────────────────────────────────
# No conflicts detected.
# Deploying 3 metadata components:
#   ApexClass            AccountService
#   ApexClass            AccountServiceTest
#   CustomField          Account.AnnualRevenue__c
# ─────────────────────────────────────────────────────────────
# Validation Successful.
```

**Why it works:** `--dry-run` runs the full Metadata API validation endpoint (equivalent to deploying with `checkOnly=true`). It evaluates Apex test coverage, shows the exact component list that would be deployed, surfaces any conflicts, and returns a non-zero exit code on failure. No metadata is written to the org. This output can be reviewed — or sent to a team lead for approval — before the real deploy is run.

---

## Anti-Pattern: Editing `.sf/orgs/<orgId>/maxRevision.json` Manually to "Fix" Conflicts

**What practitioners do:** When faced with persistent conflicts, some developers open `.sf/orgs/<orgId>/maxRevision.json`, find the component entries, and manually change the `RevisionCounter` values to match what they see in the org — or delete the entries entirely — hoping to "reset" the conflict state for specific components.

**What goes wrong:** The tracking database schema is version-specific and the CLI uses a combination of `RevisionCounter`, `lastRetrievedFromServer`, and component identity hash values to determine conflict state. Editing one field without updating all related fields causes the CLI to behave unpredictably: components may stop appearing as modified even when they have changed, or the CLI may throw internal JSON parse errors. In some CLI versions, a partially corrupted `maxRevision.json` causes the entire tracking system to fall back to full-retrieve mode for every subsequent operation.

**Correct approach:** Never edit tracking files manually. If the tracking state is wrong, delete the entire `.sf/orgs/<orgId>/` directory and run a full `sf project retrieve start` to let the CLI rebuild tracking state from the org's live `SourceMember` data.
