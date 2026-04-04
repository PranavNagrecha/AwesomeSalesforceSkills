# Examples — Scratch Org Management

## Example 1: CI Pipeline Hitting Active Org Limit Mid-Sprint

**Context:** A team of 4 developers shares a Developer Edition Dev Hub. A GitHub Actions workflow creates a scratch org per pull request to run Apex tests. On busy sprint days, 3 orgs are created by CI before any developer has started their own feature work. Developers begin getting `ERROR running force:org:create: You have reached your daily scratch org creation limit` errors.

**Problem:** The Developer Edition Dev Hub has a hard cap of 3 active scratch orgs and 6 daily creates. Without explicit deletion, CI orgs from overnight runs are still active. The `sf org list` command shows 3 active CI orgs none of the developers manually deleted.

**Solution:**

```yaml
# In .github/workflows/ci.yml — add unconditional delete at the end
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - name: Authenticate Dev Hub
        run: sf org login jwt \
             --client-id ${{ secrets.SF_CLIENT_ID }} \
             --jwt-key-file server.key \
             --username ${{ secrets.SF_USERNAME }} \
             --alias DevHub --set-default-dev-hub

      - name: Create scratch org
        run: sf org create scratch \
             --definition-file config/project-scratch-def.json \
             --alias ci-org-${{ github.run_id }} \
             --duration-days 1 \
             --target-dev-hub DevHub

      - name: Deploy and test
        run: |
          sf project deploy start --target-org ci-org-${{ github.run_id }}
          sf apex run test --target-org ci-org-${{ github.run_id }} \
            --result-format tap --code-coverage

      - name: Delete scratch org
        if: always()  # runs even if prior steps fail
        run: sf org delete scratch \
             --target-org ci-org-${{ github.run_id }} \
             --no-prompt
```

**Why it works:** `if: always()` guarantees execution even when deploy or test steps fail. `--duration-days 1` sets a 24-hour safety net if the delete step is somehow skipped (e.g., runner is killed). Using `${{ github.run_id }}` in the alias ensures no alias collision across concurrent runs. Together these two controls prevent active-org accumulation regardless of job outcome.

---

## Example 2: Scratch Org Missing Production Features — Tests Pass Locally, Fail in Production

**Context:** A team builds an Experience Cloud (Communities) component. Their scratch org definition file specifies `"edition": "Developer"` with no `features` array. Local tests pass. After deploying to Enterprise production, several LWC components fail because they reference Experience Cloud guest user behavior that the Developer scratch org never exercised.

**Problem:** The Developer edition scratch org does not include Communities/Experience Cloud features unless explicitly declared. Developers were testing against a stripped-down org that did not reflect production.

**Solution:**

```json
// config/project-scratch-def.json
{
  "edition": "Enterprise",
  "description": "Experience Cloud feature branch",
  "duration": 7,
  "hasSampleData": false,
  "features": [
    "Communities",
    "ExperienceBundle"
  ],
  "settings": {
    "communitiesSettings": {
      "enableNetworksEnabled": true
    },
    "lightningExperienceSettings": {
      "enableS1DesktopEnabled": true
    }
  }
}
```

Then re-create the scratch org:

```bash
sf org delete scratch --target-org old-feature-org --no-prompt

sf org create scratch \
  --definition-file config/project-scratch-def.json \
  --alias feature-communities \
  --duration-days 7 \
  --set-default \
  --target-dev-hub MyDevHub

sf project deploy start
```

**Why it works:** Switching to `Enterprise` edition and declaring `Communities` and `ExperienceBundle` features ensures the scratch org has the same base feature set as production. Settings are declared using Metadata API `settings` objects (not deprecated `orgPreferences`) so they are reliably applied. This closes the "works in scratch, fails in prod" gap caused by edition mismatch.

---

## Example 3: Using ScratchOrgInfo to Build a Deletion Script for Stale CI Orgs

**Context:** A team wants a nightly job to clean up any CI scratch orgs older than 1 day that were not deleted by their pipelines (e.g., due to runner crashes). They want to automate this from the Dev Hub rather than relying on individual developers.

**Problem:** Without a cleanup job, stale CI orgs accumulate and exhaust the active allocation by the time the next business day's CI runs start.

**Solution:**

```bash
# Query ActiveScratchOrg for orgs expiring today or already past expiry
sf data query \
  --target-org MyDevHub \
  --query "SELECT Id, OrgName, ExpirationDate FROM ActiveScratchOrg WHERE ExpirationDate <= TODAY ORDER BY ExpirationDate ASC" \
  --result-format json \
  | jq -r '.result.records[].OrgName'

# For each returned org name, delete via CLI (or Apex DML on ActiveScratchOrg)
# Alternatively, use sf org list and cross-reference aliases
sf org list --all --json | jq -r '.result.scratchOrgs[] | select(.isExpired == true) | .alias'
```

Or in a Scheduled Apex job inside the Dev Hub (note: requires Dev Hub Apex access):

```apex
// Delete expired scratch orgs via DML on ActiveScratchOrg
List<ActiveScratchOrg> expiredOrgs = [
    SELECT Id FROM ActiveScratchOrg
    WHERE ExpirationDate <= TODAY
    LIMIT 200
];
delete expiredOrgs;
```

**Why it works:** `ActiveScratchOrg` is a standard DML-accessible object in the Dev Hub. Deleting a record via DML or the CLI immediately frees the allocation. `ScratchOrgInfo` records are preserved as the audit trail. The SOQL filter on `ExpirationDate <= TODAY` safely targets only already-expired or same-day-expiry orgs.

---

## Anti-Pattern: Committing a Shared Long-Lived Scratch Org Alias to Source Control

**What practitioners do:** A team creates one scratch org, stores its username/alias in a shared `.env` file committed to the repo, and has everyone push/pull against the same org to "save allocations."

**What goes wrong:** Source tracking in a scratch org is per-user-session. Multiple developers pushing to the same org produces conflicting source-tracking state, overwritten metadata, and data corruption in the shared org. When the org expires after 7–30 days, all in-flight work is lost simultaneously. This also defeats the purpose of isolated, reproducible development environments.

**Correct approach:** Each developer and each CI run gets its own scratch org. Orgs are cheap and fast to provision. The definition file is committed to source control; the org username/alias is not. Use `sf project deploy start` and `sf project retrieve start` in isolated orgs, not a shared mutable environment.
