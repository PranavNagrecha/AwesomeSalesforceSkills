# Gotchas — Gift Entry and Processing

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Advanced Mapping Must Be Enabled Before Activating Gift Entry

**What happens:** Attempting to activate the Gift Entry feature in NPSP Settings fails or produces a generic configuration error if Advanced Mapping has not been enabled first. The error message does not always clearly identify Advanced Mapping as the cause, so admins waste time troubleshooting other settings.

**When it occurs:** Every fresh NPSP installation. Advanced Mapping is not enabled by default — it must be explicitly turned on in NPSP Settings > Advanced Mapping before Gift Entry can be activated. It also occurs after org refreshes or sandbox copies where NPSP settings are reset.

**How to avoid:** Before any Gift Entry work, navigate to NPSP Settings > Advanced Mapping and confirm it is enabled. This is step one of the recommended workflow. Add it to any pre-work checklist for Gift Entry setup tasks.

---

## Gotcha 2: Default Gift Entry Template Is the Only Single-Entry Template

**What happens:** Custom Gift Entry templates are batch-only. They do not appear in the standard single-gift entry UI flow. If an admin creates a custom template and expects fundraisers to use it for individual gift entry, those staff will see no template option and will be routed to the Default Gift Entry Template regardless.

**When it occurs:** When admins design a custom template for both single and batch use, or when they expect a custom template to replace the Default Gift Entry Template for individual gift entry.

**How to avoid:** Treat template type as a hard platform constraint, not a configuration choice. Single-gift entry = Default Gift Entry Template. Batch entry = custom template. Design the Default Gift Entry Template carefully, since it cannot be swapped out for single-entry workflows. Document this constraint in any Gift Entry admin guide delivered to the org.

---

## Gotcha 3: Skipping processGiftEntries Leaves Gifts Permanently in Staging

**What happens:** `GiftEntry` staging records are not automatically promoted. If a custom integration or flow creates `GiftEntry` records but never calls `processGiftEntries`, those records accumulate in the staging object indefinitely. They will never become `GiftTransaction`, `GiftDesignation`, or `GiftSoftCredit` records. They will not appear in fundraising reports or gift dashboards. The org will have phantom "gifts" that are invisible to finance.

**When it occurs:** Any time `processGiftEntries` is skipped — for example, a developer writes a bulk staging load but forgets the promotion step, or a Flow creates staging records but has no action step calling the invocable action, or a batch process errors out after creating staging records but before processing them.

**How to avoid:** Always pair staging record creation with a `processGiftEntries` invocation. For bulk loads, include error logging that flags any staging record remaining in `Imported` status after the processing window. Add a scheduled cleanup report that queries `GiftEntry` records older than 24 hours in `Imported` status and alerts the admin team.

---

## Gotcha 4: isDryRun=true Does Not Need Rollback Logic

**What happens:** Some developers wrap `processGiftEntries` dry-run calls in Savepoint/Rollback patterns, assuming the dry run might partially commit records that need to be rolled back. This adds unnecessary complexity and can introduce lock contention in high-volume scenarios.

**When it occurs:** When developers unfamiliar with the Gift Entry staging model apply defensive database patterns around what they assume is a write operation.

**How to avoid:** `isDryRun=true` is a pure validation pass — it performs no DML and creates no records. There is nothing to roll back. Remove any Savepoint/Rollback logic around dry-run calls. Reserve Savepoint patterns for the actual commit pass (`isDryRun=false`) if you need transactional rollback on failure.

---

## Gotcha 5: TaxReceiptStatus Is Only Available at API v62.0+

**What happens:** Querying `TaxReceiptStatus` on `GiftTransaction` in orgs below API v62.0 throws an "invalid field" error in SOQL, Apex, and Flow. This is not a permissions issue — the field does not exist in the schema at earlier API versions. Deployments that reference this field will fail validation if the org's metadata API version is below v62.0.

**When it occurs:** When documentation referencing newer API features is applied to orgs that have not yet upgraded, or when metadata is deployed from a newer API version scratch org to a production org on an older API version.

**How to avoid:** Check the org's current API version before referencing `TaxReceiptStatus`. For orgs on API v59.0–v61.0, use a custom field on `GiftTransaction` (e.g., `Receipt_Status__c`) as a workaround and document the migration path to the platform-native field once the org upgrades to v62.0+. Always include API version in the Before Starting checklist for any Gift Entry receipting work.
