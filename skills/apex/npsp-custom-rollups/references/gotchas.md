# Gotchas — NPSP Custom Rollups (CRLP)

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Enabling CRLP Is a One-Way Migration With No Rollback

**What happens:** When CRLP is enabled for the first time via NPSP Settings > Customizable Rollups, NPSP permanently removes all user-defined legacy rollup configurations. The legacy rollup summary fields (e.g., `npo02__TotalOppAmount__c`, `npo02__LastCloseDate__c`) continue to exist as fields on Contact and Account, but they will only be populated if equivalent CRLP Rollup Definitions are created. There is no "undo CRLP" button.

**When it occurs:** Any time a user clicks "Enable Customizable Rollups" in NPSP Settings — whether in sandbox or production. The migration prompt does not list which formula fields, flows, or Apex classes currently reference the legacy rollup fields.

**How to avoid:** Before enabling CRLP:
1. Export the full list of active NPSP rollup fields from the NPSP Rollups tab.
2. Search formula fields, flow conditions, report filters, and Apex for references to `npo02__` rollup fields.
3. Create CRLP Rollup Definitions that replicate each actively-used rollup before clicking Enable.
4. Run the Full recalculation batch immediately after enabling and verify values.

---

## Gotcha 2: CRLP Rollup Values Are Not Real-Time — Batch Is Always Required

**What happens:** Creating or updating an Opportunity does not immediately update the related Contact's or Account's CRLP rollup fields. The value change only propagates when the NPSP batch job runs and processes that record. If no batch is scheduled or has run recently, rollup fields can be days or weeks stale.

**When it occurs:** In any org where CRLP is enabled but the Incremental or Scheduled batch has not been configured. Also occurs immediately after bulk data loads via Data Loader or Bulk API, where the dirty-flag mechanism may not be triggered for all records, leaving a Full recalculation as the only reliable path to accurate values.

**How to avoid:** Always configure a scheduled recalculation after enabling CRLP:
- Set up an Incremental recalculation to run at least nightly.
- Run a Full recalculation manually after any bulk data operation or rollup definition change.
- Educate stakeholders that rollup fields reflect values as of the last batch run, not real-time.

---

## Gotcha 3: Filter Group Names Have a Silent 40-Character Hard Limit

**What happens:** The NPSP Settings UI for creating or editing Filter Groups does not visually enforce the 40-character name limit before submission. When a user saves a filter group with a name exceeding 40 characters, the save either fails with a generic error message or silently truncates the name, causing confusion about which filter group is which.

**When it occurs:** Most commonly when practitioners use descriptive names like "Current Fiscal Year Major Donor Gifts" (42 characters) or "Membership Year Renewal Eligible Donations" (41 characters). The error is easy to miss because the NPSP Settings page does not highlight the name field on failure.

**How to avoid:** Count characters before naming a filter group. Use abbreviations for common qualifiers: "FY" for fiscal year, "CY" for calendar year, "MG" for major gifts. Keep all filter group names to 40 characters or fewer. If deploying via Metadata API, the character limit is still enforced at the metadata level — validate name lengths before deploying.

---

## Gotcha 4: Large Filter Groups Time Out on Save in the NPSP Settings UI

**What happens:** Saving a Filter Group with many filter rows through the NPSP Settings UI can exceed the browser request timeout, causing a timeout error and leaving the filter group in an inconsistent state. This is a UI limitation, not a platform limit on filter group complexity.

**When it occurs:** Filter groups with approximately 10 or more rows, or any group saved during high-org-activity periods (scheduled jobs, large batch operations), are most prone to timeout. The exact threshold varies by org performance.

**How to avoid:** Deploy complex filter groups directly via the Metadata API rather than the NPSP Settings UI. Build the `Customizable_Rollup_Filter_Rules__mdt` records in XML and deploy with SFDX or a change set. This bypasses the browser timeout entirely and makes the configuration version-controllable.

---

## Gotcha 5: Full Recalculation Required After Any Rollup Definition Modification

**What happens:** Modifying an existing Rollup Definition — changing the filter group, changing the aggregate operation, updating the date range type, or changing the store field — does not automatically mark related records as dirty. Existing Contact and Account records retain their stale values until a Full recalculation batch is explicitly run.

**When it occurs:** Any time a Rollup Definition is edited in production and only the Incremental batch is scheduled. The Incremental batch only processes records flagged as dirty by recent Opportunity changes, not records affected by a configuration change.

**How to avoid:** After every Rollup Definition change in production:
1. Run a Full recalculation batch immediately.
2. Wait for the batch to complete before validating or reporting on rollup values.
3. Document configuration changes so downstream users know a recalculation was triggered.
