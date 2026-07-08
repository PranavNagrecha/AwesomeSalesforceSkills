# Gotchas — Scratch Org Management

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Daily Limit Is a Rolling 24-Hour Window, Not a Calendar Day Reset

**What happens:** Teams schedule CI jobs at local midnight expecting the previous day's limit to have reset. Jobs still fail with allocation errors because the Salesforce rolling window has not yet elapsed.

**When it occurs:** Any time CI is scheduled around midnight assuming a calendar-day reset. Also occurs when a team burns through the full daily limit late in the afternoon and expects availability first thing the next morning — the 24-hour window may not have fully rolled over.

**How to avoid:** Treat the daily limit as a strict rolling 24-hour window over *successful creations initiated*, not a midnight reset. Two consequences follow from that definition and both surprise people:

- Deleting active scratch orgs frees the **active** allocation. It does not refund the **daily** allocation — the creation already happened.
- A team that burns the daily allocation at 4 p.m. does not get it back at 9 a.m. the next morning. It comes back creation-by-creation as each one ages out of the window.

The authoritative pre-flight check is the Dev Hub's own limits, not a SOQL count:

```bash
# Reports both ActiveScratchOrgs and DailyScratchOrgs with remaining/max
sf org list limits --target-org MyDevHub
```

(`sf limits api display` is a legacy alias of the same command and still appears in the SFDX Developer Guide. Prefer the canonical `sf org list limits`.)

Use SOQL on `ScratchOrgInfo.CreatedDate` only as a supplement, to understand *when* the oldest creation in the current window will age out:

```bash
sf data query \
  --target-org MyDevHub \
  --query "SELECT COUNT() FROM ScratchOrgInfo WHERE CreatedDate = LAST_N_HOURS:24" \
  --result-format json
```

---

## Gotcha 2: `orgPreferences` Is Deprecated and Silently Drops Settings on Newer API Versions

**What happens:** Scratch orgs provision successfully but the settings declared in `orgPreferences` are not applied. No error is raised. The org appears healthy but behaves differently than expected — for example, record types, sharing rules, or custom org preferences are not activated.

**When it occurs:** Definition files written for older SFDX tooling often used `orgPreferences` (a pre-Spring '20 format). They continue to provision without error on current API versions but settings are silently ignored for preferences that have been migrated to Metadata API settings objects.

**How to avoid:** Replace `orgPreferences` blocks with equivalent Metadata API `settings` objects. The full list of available settings objects is in the Salesforce DX Developer Guide under "Scratch Org Settings." Example migration:

```json
// Old (deprecated) — settings may be ignored
{
  "orgPreferences": {
    "enabled": ["S1DesktopEnabled", "ChatterEnabled"]
  }
}

// New (correct) — reliable on all current API versions
{
  "settings": {
    "lightningExperienceSettings": {
      "enableS1DesktopEnabled": true
    },
    "chatterSettings": {
      "enableChatter": true
    }
  }
}
```

---

## Gotcha 3: Scratch Org Expiration Cannot Be Extended After Creation

**What happens:** A developer is mid-feature when their scratch org expires. They lose all uncommitted changes, any manual configuration applied in the org, and all in-org test data. There is no `sf org extend` or equivalent command.

**When it occurs:** When `--duration-days` was set to a short window (e.g., 1 day for CI) or the default 7 days was not overridden for a longer feature branch. Also occurs when sprint planning does not align with the 30-day maximum.

**How to avoid:** Set `--duration-days` to match the expected feature branch lifespan at creation time. For work that may extend beyond 7 days, always specify `--duration-days 14` or higher (max 30). Establish a team habit of running `sf project retrieve start` before an org expires to snapshot all source changes back to the local repository. Add a reminder by querying for orgs expiring within 2 days:

```bash
sf data query \
  --target-org MyDevHub \
  --query "SELECT OrgName, ExpirationDate, CreatedBy.Name FROM ActiveScratchOrg WHERE ExpirationDate <= NEXT_N_DAYS:2"
```

---

## Gotcha 4: Deleting a Scratch Org Preserves the ScratchOrgInfo Record

**What happens:** After deleting a scratch org via `sf org delete scratch` or by removing the `ActiveScratchOrg` record, the `ScratchOrgInfo` record in the Dev Hub remains permanently. Practitioners who expect a clean deletion are confused to find the record still present and may mistakenly believe the org was not deleted or still counts against their limit.

**When it occurs:** Any time a scratch org is deleted. The `ActiveScratchOrg` record is removed (freeing the allocation); `ScratchOrgInfo` is intentionally retained as an audit trail.

**How to avoid:** Understand this is correct behavior by design. Use `ActiveScratchOrg` to check live allocation; use `ScratchOrgInfo` for historical audit only. Do not attempt to delete `ScratchOrgInfo` records as a cleanup measure — Salesforce does not expose a supported way to purge them, and the records are the source of truth for package version creation history.

---

## Gotcha 5: Feature Flags Cannot Be Added to a Scratch Org After Provisioning

**What happens:** A developer creates a scratch org and later realizes they need an additional feature (e.g., `LightningServiceConsole`, `OrderManagement`). There is no CLI command to add features to an existing scratch org. The developer must delete the org, update the definition file, and create a new one.

**When it occurs:** When a definition file is written without fully enumerating all features required for the work, or when requirements change mid-feature.

**How to avoid:** Before creating the scratch org, audit the full feature set required by reviewing the components being developed and their associated feature dependencies. The Scratch Org Features list in the Salesforce DX Developer Guide provides the exact feature strings. For teams where production feature sets change frequently, use Org Shape so that the feature set is derived from production automatically rather than maintained manually.

---

## Gotcha 6: Scratch Org Storage Is Fixed at 500 MB Data / 50 MB Files Regardless of the Edition You Declare

**What happens:** A team sets `"edition": "Enterprise"` in the definition file, then runs the same data-seeding script they use against a full sandbox. The load fails partway through with storage limit errors, often after the org has already been provisioned and half-populated — so the failure surfaces in the middle of a CI run rather than at org creation.

**When it occurs:** Any time a scratch org is treated as a small sandbox. It is common in CI pipelines that seed reference data (products, price books, territory hierarchies) or in bulkification tests that insert 100k+ records to exercise governor limits.

**How to avoid:** Remember that `edition` controls the *feature set and license model*, not the storage allocation. Scratch orgs are limited to 500 MB for data and 50 MB for files. Entities defined as metadata types are not counted against these allocations, so a large metadata footprint is safe — it is record volume and file/attachment volume that will exhaust the ceiling.

Practical consequences:

- Size bulk-test data sets to the smallest volume that still crosses the governor limit under test (e.g., 201 records to prove a trigger is bulk-safe, not 200,000).
- Load reference data as a trimmed subset rather than a production extract.
- Prefer `Test.loadData()` with a small static resource, or a factory that generates records in-memory, over a bulk file import.
- If a test genuinely requires production-scale data volume, a scratch org is the wrong environment. Use a Partial Copy or Full sandbox.

Before a large load, size the record volume already in the org. From the CLI, run the command with no `--sobject` flag to get every available record count — these are the same counts the Setup UI shows on its Storage Usage page:

```bash
sf org list sobject record-counts --target-org my-scratch-org
```

Counts are approximate: they are calculated asynchronously, so storage usage lags a load that just finished. To read the consumed share of the 500 MB data allocation as a percentage, open the org and navigate to Setup → Storage Usage:

```bash
# Opens the org home page — navigate to Setup → Storage Usage from there
sf org open --target-org my-scratch-org
```
