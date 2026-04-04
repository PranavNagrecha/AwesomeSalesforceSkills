# Gotchas — Apex Managed Sharing

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Apex Managed Share Rows Are Silently Cleared on OWD Change or Full Recalculation

**What happens:** When an administrator changes the Org-Wide Default for an object, or triggers a full sharing recalculation from Setup (Sharing Settings > Recalculate), the platform deletes **all** Apex-managed share rows for the affected object — including rows with custom row causes. If a recalculation class is registered on the Apex sharing reason, the platform invokes it automatically to rebuild the grants. If no class is registered, the grants are gone with no error or notification.

**When it occurs:** Any time an admin modifies OWD, adds or removes a sharing rule, or manually recalculates sharing via Setup. This also happens when object-level sharing recalculation is triggered by certain org migrations or sandbox refreshes.

**How to avoid:** Always register a `Database.Batchable` recalculation class on every Apex sharing reason (Setup > Object Manager > [Object] > Apex Sharing Reasons > Edit > Recalculation Apex Class). Test the recalculation path in UAT by simulating an OWD change in a sandbox, then verifying shares are rebuilt. Monitor with periodic SOQL audits on the Share table.

---

## Gotcha 2: `without sharing` Is Mandatory in Recalculation Classes

**What happens:** A recalculation batch class declared `with sharing` (or with no keyword, which defaults to `without sharing` only at the top level in some contexts, but is unreliable) silently under-queries the parent object. Records the running user cannot see are excluded from the `Database.QueryLocator` result. The batch completes without error, but the share table is partially rebuilt — only records the submitting admin happens to own or have access to are covered.

**When it occurs:** Whenever the batch is submitted by a non-admin user, or by an admin who does not have access to all records due to a misconfigured role hierarchy or sharing rule. Also occurs in automated processes (scheduled jobs, platform events) where the running user is an integration user with limited visibility.

**How to avoid:** Declare the recalculation class `global without sharing` (or `public without sharing`). The `without sharing` keyword on the class ensures all records are visible for the query regardless of who invokes the batch. Document this intentional bypass in a code comment citing this gotcha.

---

## Gotcha 3: Custom Row Cause Must Exist in the Target Org Before Deployment

**What happens:** Code that references a custom Apex sharing reason (e.g., `Project__Share.rowCause.TerritoryAccess__c`) compiles successfully even if the reason does not exist in the org. At DML runtime, inserting a share row with the non-existent row cause throws `System.DmlException: FIELD_INTEGRITY_EXCEPTION, value not in set for restricted picklist field: RowCause`. The exception rolls back the transaction.

**When it occurs:** When deploying to a new sandbox, production org, or CI environment where the Apex sharing reason metadata record has not been created. Apex sharing reasons are created through Setup UI (Object Manager), not through standard metadata deployments in a typical `force-app` directory. They are part of the `CustomObject` metadata type and must be included explicitly in the deployment package's `CustomObject` XML, or created manually before deployment.

**How to avoid:** Include the sharing reason in the object's `CustomObject` metadata XML under `<sharingReasons>` in your deployment package. Alternatively, add a pre-deployment Setup step in the runbook. Add a smoke test that queries `EntityDefinition` or attempts a test insert in the target org's Apex test to confirm the reason exists before DML.

---

## Gotcha 4: AccessLevel `All` Cannot Be Granted Via Apex — Use `Edit` for Maximum Programmatic Access

**What happens:** Attempting to insert a share row with `AccessLevel = 'All'` throws `System.DmlException: INVALID_ACCESS_LEVEL, Invalid access level: All`. `All` is the owner-level access reserved for the record owner and is not grantable through Share object DML.

**When it occurs:** When a developer assumes that to give a user "full control" of a record they should use `All`. The valid Apex-grantable levels are `Read` and `Edit` only.

**How to avoid:** Use `Edit` as the maximum Access Level in Apex managed sharing. If ownership transfer is needed, update the `OwnerId` field directly. Document the valid values in code comments: `Read`, `Edit`.

---

## Gotcha 5: Stale Share Rows Must Be Deleted Before Re-Granting — Upsert Is Not Supported

**What happens:** The Share object does not support `upsert`. Attempting to upsert or re-insert a share row for an existing `(ParentId, UserOrGroupId, RowCause)` combination throws `DUPLICATE_VALUE`. Changing the `AccessLevel` of an existing grant requires deleting the old row and inserting a new one — there is no update path via the Share object.

**When it occurs:** During recalculation when access levels may have changed (e.g., a user was previously given Read and now needs Edit), and during retry logic that re-runs share inserts without cleaning up first.

**How to avoid:** In recalculation logic, always delete all existing rows for the relevant `RowCause` and `ParentId` set before inserting fresh rows. In trigger logic, query existing rows and compare — only insert rows for new grants, delete rows for revoked grants, and delete-then-insert when the access level has changed.
