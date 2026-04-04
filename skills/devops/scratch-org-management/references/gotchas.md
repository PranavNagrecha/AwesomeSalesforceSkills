# Gotchas — Scratch Org Management

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Daily Limit Is a Rolling 24-Hour Window, Not a Calendar Day Reset

**What happens:** Teams schedule CI jobs at local midnight expecting the previous day's limit to have reset. Jobs still fail with allocation errors because the Salesforce rolling window has not yet elapsed.

**When it occurs:** Any time CI is scheduled around midnight assuming a calendar-day reset. Also occurs when a team burns through the full daily limit late in the afternoon and expects availability first thing the next morning — the 24-hour window may not have fully rolled over.

**How to avoid:** Treat the daily limit as a strict 24-hour window starting from the timestamp of the first creation, not a midnight reset. Monitor `ScratchOrgInfo.CreatedDate` to understand when the oldest creation in the current window will age out. If allocation is critical, implement a pre-flight SOQL check before CI runs:

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
