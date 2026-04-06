# Gotchas — Org Cleanup And Technical Debt

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Deleted Fields Stay in Limits for 15 Days

**What happens:** After deleting a custom field through Setup, the admin expects the field slot to be immediately available. Instead, the org still reports the same field count against the limit. New field creation remains blocked.

**When it occurs:** Always — every custom field deletion goes through a 15-day soft-delete queue before the slot is permanently reclaimed. This applies to all custom field types on all objects.

**How to avoid:** After deleting fields, navigate to Setup > Object Manager > [Object] > Fields & Relationships > Deleted Fields. Click "Erase" on each field to permanently remove it and immediately reclaim the slot. Be aware that erasing is irreversible — the field data cannot be recovered after this step.

---

## Gotcha 2: Time-Based Workflow Actions Execute After Rule Deactivation

**What happens:** An admin deactivates a Workflow Rule that had a time-dependent action (e.g., "send email 3 days after creation"). Records that already entered the time queue before deactivation still have their pending actions executed on schedule.

**When it occurs:** Whenever a Workflow Rule with time-dependent actions is deactivated while records are in the time queue. The deactivation only prevents new records from entering the queue — it does not flush existing entries.

**How to avoid:** Before deactivating a time-dependent Workflow Rule, go to Setup > Time-Based Workflow. Search for pending actions associated with that rule. Remove them manually from the queue. Only then deactivate the rule.

---

## Gotcha 3: "Where Is This Used?" Misses Many Reference Types

**What happens:** An admin checks "Where Is This Used?" for a custom field in Setup and sees no references. After deleting the field, a report breaks, a Flow formula fails, or an Apex class throws a runtime exception.

**When it occurs:** The Setup dependency tool does not index: report formula columns, dashboard filter formulas, certain Flow formula expressions, Apex references using dynamic `Schema.describe` calls, and some managed package references.

**How to avoid:** Supplement the Setup lookup with a full-text search of the org's metadata. Retrieve the metadata (SFDX retrieve or Metadata API), then `grep` or search for the field API name across all XML and source files. Also check reports manually by running each report that uses the parent object.

---

## Gotcha 4: Destructive Deploys Do Not Check Runtime Dependencies

**What happens:** A destructive deploy removing a custom field succeeds (the deploy itself completes without error), but Flows that reference the field via dynamic references or formula expressions begin failing at runtime. The deploy API validates metadata compile-time dependencies but not all runtime references.

**When it occurs:** When the deleted metadata is referenced dynamically — through Flow formulas, string-based Apex references, or formula fields that Salesforce does not fully validate at deploy time.

**How to avoid:** Always run a full Apex test suite and manually test critical Flows after a destructive deploy in sandbox before promoting to production. Treat the deploy success as "metadata removed" not "everything still works."

---

## Gotcha 5: Deleting a Custom Object Does Not Delete Its Apex Test Data Setup

**What happens:** An admin deletes a custom object that was part of a retired feature. The deletion succeeds, but Apex test classes that create records of that object now throw compile errors. The next production deployment fails because overall test coverage drops below 75%.

**When it occurs:** When Apex test classes reference the deleted object's API name directly (e.g., `Old_Feature__c obj = new Old_Feature__c(...)`). This creates a hard compile failure in the test class.

**How to avoid:** Before deleting a custom object, search all Apex classes and test classes for references to the object's API name. Coordinate with a developer to update or remove the test classes before (or simultaneously with) the object deletion. Use a destructive deploy that removes both the object and the referencing test class in a single operation.

---

## Gotcha 6: Flow Version Deletion Fails for Versions Referenced as Subflows

**What happens:** An admin tries to delete an old inactive Flow version and receives an error, or the deletion succeeds but a parent Flow that references that specific version as a subflow begins failing at runtime.

**When it occurs:** When a parent Flow's subflow element was configured to reference a specific version of a child Flow (rather than the "latest active version" default). This is uncommon but occurs in orgs where admins pinned subflow versions for stability.

**How to avoid:** Before deleting inactive Flow versions, search Flow metadata for subflow references that specify a version number. Update any pinned references to point to the active version before cleaning up old versions.
