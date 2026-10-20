# Gotchas — System Field Behavior and Audit

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: SystemModstamp Does Not Capture Every Change

**What happens:** A delta sync on object A misses a change because A only retrieves the value from object B. The Object Reference says B's field change is reflected in B's SystemModstamp "but not on object A" (object_reference 264 L2581-2583). The earlier text of this gotcha claimed the opposite (a parent change advances the child's SystemModstamp through a cross-object formula); that was CONTRADICTED by those lines and is withdrawn.

**When it occurs:** Any object whose displayed value comes from another object (cross-object formula, lookup-derived value). UNVERIFIED (2026-10-20): whether a particular formula type is the "retrieves values" case the guide describes.

**How to avoid:** Sync each object from its own SystemModstamp and re-read dependents that mirror another object's value. Do not treat a SystemModstamp change as proof that a user edited the record; LastModifiedDate is the user-modification field (L2563).

---

## Gotcha 2: Create Audit Fields Requires Both Org Permission and User Permission

**What happens:** A developer enables the org-level "Set Audit Fields upon Record Creation" setting but the insert still overwrites CreatedDate with the current timestamp. The migration appears to work but all dates are wrong.

**When it occurs:** The Setup setting and the permission on the user's permission set or profile are two separate steps (object_reference 264 L2600-2602). UNVERIFIED (2026-10-20): that without both the platform silently ignores the values — the guide lists the steps, not the failure behaviour.

**How to avoid:** After enabling the org setting, create a dedicated permission set with the "Set Audit Fields upon Record Creation" permission and assign it to the migration user. Test with a single record before running the full migration batch. For custom objects the org must also be API enabled and the user must have "Modify All Data" (object_reference 264 L3125).

---

## Gotcha 3: ALL ROWS Returns Archived Records Too

**What happens:** A query intended to find only soft-deleted (Recycle Bin) records returns unexpected results that include archived activities (`ALL ROWS` covers "deleted records and archived activities", apex dev guide 264 L10124).

**When it occurs:** On Task and Event, whose archived records Bulk API queryAll also returns (api_asynch 264 L6670-6671). The earlier "custom objects with Big Object archival" example is dropped — UNVERIFIED (2026-10-20): no corpus line ties ALL ROWS to Big Object archives.

**How to avoid:** Always include an explicit `IsDeleted = true` filter when you only want Recycle Bin records. Do not rely on `ALL ROWS` alone as a proxy for "deleted records."

---

## Gotcha 4: The Recycle Bin Window Is 15 Days, Then Hard Deletion

**What happens:** A team attempts to recover records deleted more than 15 days ago using `ALL ROWS` and finds nothing. Once the Recycle Bin retention period expires, items are scheduled for hard deletion (large_data_volumes_bp 264 L739). "After these records are permanently removed from the recycle bin, you can no longer query them" (api_rest 264 L17232-17233, the QueryAll resource).

**When it occurs:** After the 15-day Recycle Bin window, when items are "scheduled for hard deletion" at a time Salesforce does not guarantee; or sooner if the bin is emptied by UI, API or Apex, or if Bulk API / Bulk API 2.0 hard delete was used (large_data_volumes_bp 264 L738-742).

**How to avoid:** Implement a scheduled job or integration that queries soft-deleted records on a regular cadence (e.g., daily) and backs them up to an external system before the 15-day window closes. Alert on unexpected bulk deletes.

---

## Gotcha 5: Filter Delta Syncs on SystemModstamp, Which Is on the Default Index List

**What happens:** UNVERIFIED (2026-10-20): the claim that a `LastModifiedDate >` filter runs slowly where the same filter on `SystemModstamp` returns instantly. The corpus gives only the index list.

**When it occurs:** The platform maintains default indexes on CreatedDate, Name, Id and "Systemmodstamp (LastModifiedDate)" (large_data_volumes_bp 264 L309, L404-411). The `> 100,000 rows` threshold is UNVERIFIED (2026-10-20); the guide's own selectivity thresholds are in that guide.

**How to avoid:** Use `SystemModstamp` in SOQL WHERE clauses for sync filtering. Custom indexes are requested through Customer Support for custom fields (large_data_volumes_bp 264 L310-311); whether LastModifiedDate qualifies is UNVERIFIED (2026-10-20).

---

## Gotcha 6: Create Audit Fields Only Works on Insert, Not Update

**What happens:** A developer attempts to correct a wrong CreatedDate on existing records by running a DML update with the Create Audit Fields permission. UNVERIFIED (2026-10-20): the outcome (silent ignore vs a FIELD_NOT_UPDATEABLE error) — the guide documents the create path only (object_reference 264 L2603).

**When it occurs:** An update DML on CreatedDate, CreatedById, LastModifiedDate, or LastModifiedById. UNVERIFIED (2026-10-20): that it fails "regardless of permissions" — the corpus describes only setting the values at creation (object_reference 264 L2603).

**How to avoid:** Plan audit field values before the initial insert. If historical dates were not set correctly during migration, the remediation options are to delete and re-insert the records (which resets relationships and may cascade deletes on child records) or to store the correct historical date in a separate custom field.
