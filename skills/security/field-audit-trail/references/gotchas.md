# Gotchas — Field Audit Trail

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Field History Tracking Must Also Be Enabled — FAT Does Not Capture Changes Independently

**What happens:** Administrators enable FAT and set a retention policy, expecting long-term field change capture to begin. Querying `FieldHistoryArchive` weeks later returns zero rows for the configured fields.

**When it occurs:** Any time FAT is enabled without verifying that Field History Tracking is also enabled on the same object and fields in Setup > Object Manager > [Object] > Set History Tracking. FAT governs how long captured history is retained and archived — it does not capture changes by itself.

**How to avoid:** After enabling FAT, immediately verify Field History Tracking is enabled for all the same fields. Use the `check_field_audit_trail.py` script to compare the FAT policy metadata against the Field History Tracking configuration. Treat these as two interdependent configurations, not alternatives.

---

## Gotcha 2: Standard Field History Tracking Is Still Capped at 20 Fields Per Object Even With Shield

**What happens:** Practitioners assume that licensing Shield and enabling FAT removes the 20-field limit on Field History Tracking. They attempt to enable Field History Tracking on a 21st field and receive an error or the 21st field silently does not get tracked.

**When it occurs:** Any time more than 20 fields need standard Field History Tracking on a single object. FAT raises the capture limit to 60 fields per object, but only for the FAT-specific retention path. The standard history sObject (`XxxHistory`) still observes the 20-field limit.

**How to avoid:** When you need to track more than 20 fields on an object, enable FAT for all fields exceeding the standard limit. Be explicit: the first 20 fields flow through both standard Field History Tracking and FAT; fields 21–60 flow only through FAT (and are therefore only queryable via `FieldHistoryArchive`, not via the standard History sObject or Reports). Document this split in your compliance evidence matrix.

---

## Gotcha 3: FieldHistoryArchive Is Not Queryable via Reports or List Views

**What happens:** A compliance officer asks for a Salesforce Report showing 5 years of field change history for a set of records. The report builder has no `FieldHistoryArchive` report type. Practitioners who attempt to create a custom report type against `FieldHistoryArchive` find it is not available.

**When it occurs:** Any time stakeholders plan to use Salesforce Reports as the primary audit delivery mechanism for FAT-archived data. This is a common planning assumption that breaks during implementation.

**How to avoid:** Set expectations early: archived field history is only accessible via SOQL. Plan for a SOQL-based extraction workflow (Apex Batch, Data Loader, Workbench, or an ETL tool) for audit delivery. If a UI-based view is required, build a custom Lightning component that queries `FieldHistoryArchive` via Apex and renders results in a datatable — but note that governor limits apply to the SOQL query size.

---

## Gotcha 4: Archival Is Asynchronous — Data May Not Appear in FieldHistoryArchive Immediately

**What happens:** After enabling FAT and its retention policy, practitioners immediately query `FieldHistoryArchive` and find no rows — or find only recent rows, not the expected historical backfill. They incorrectly conclude FAT is misconfigured.

**When it occurs:** FAT migration is a background async process. When FAT is first enabled on an object, existing history older than the standard retention window migrates to `FieldHistoryArchive` asynchronously. This can take several days for orgs with large history volumes. Additionally, ongoing changes do not appear in `FieldHistoryArchive` immediately — they first enter the standard history path and migrate to the archive over time.

**How to avoid:** Do not schedule compliance audits or validation immediately after enabling FAT. Allow at least 3–5 business days for initial migration to settle. Salesforce does not expose a migration status indicator; verify completeness by comparing record counts between the standard History sObject and `FieldHistoryArchive` over time. Document the activation date for auditors so the migration window is accounted for.

---

## Gotcha 5: Filtering FieldHistoryArchive on Non-Indexed Fields Causes Query Timeouts

**What happens:** A SOQL query against `FieldHistoryArchive` with a `WHERE` clause on `OldValue`, `NewValue`, or `FieldHistoryType` alone (without bounding on `ParentId` or `CreatedDate`) times out or returns a query error. The query may appear to hang and eventually fail with a SOQL exception or governor limit error.

**When it occurs:** `FieldHistoryArchive` can contain billions of rows in production orgs with multi-year FAT retention. Only a subset of fields are selectively indexed. Filtering on `OldValue` or `NewValue` with a `WHERE` clause triggers a full table scan.

**How to avoid:** Always anchor `FieldHistoryArchive` queries with at minimum one of:
- `ParentId = :specificRecordId` (most selective — use whenever querying for a specific record)
- `CreatedDate >= :startDate AND CreatedDate <= :endDate` (bounded date range — keep ranges tight)

For bulk extractions across many records, use Apex Batch with chunked `ParentId` sets rather than a single large SOQL query. If filtering by field name is required, add `FieldHistoryType = 'SomeField__c'` as a secondary filter after anchoring on `ParentId` or `CreatedDate`.
