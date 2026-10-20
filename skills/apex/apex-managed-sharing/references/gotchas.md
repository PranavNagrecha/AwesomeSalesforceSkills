# Gotchas — Apex Managed Sharing

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: An OWD Change Triggers Recalculation

**What happens:** When an administrator changes the Org-Wide Default for an object, "Salesforce automatically recalculates sharing for all records", adds managed sharing where appropriate, and removes any sharing "if the access they grant is considered redundant" (apex dev guide 264 L13049-13052). Apex recalculation classes defined for a custom object also run on an OWD change (L13071-13072). UNVERIFIED (2026-10-20): that the platform deletes **all** Apex-managed rows including custom row causes, that no error or notification appears when no class is registered, and that sharing rule edits or sandbox refreshes trigger the same behaviour.

**When it occurs:** Any OWD change on the object.

**How to avoid:** Register a `Database.Batchable` recalculation class for the object (the Apex Sharing Recalculation related list on the custom object's detail page, L13053-13055; the earlier "Edit > Recalculation Apex Class on the sharing reason" path is CONTRADICTED). Test the rebuild by changing the OWD in a sandbox and checking the Share table by `RowCause`.

---

## Gotcha 2: The Recalculation Sample Is `without sharing`

**What happens:** The guide's recalculation class is `public without sharing class JobSharingRecalc` and its `start` query uses `AccessLevel.SYSTEM_MODE` (apex dev guide 264 L13095, L13105-13106). UNVERIFIED (2026-10-20): that a `with sharing` batch silently under-queries and completes without error. The earlier remark that a class with no keyword "defaults to `without sharing` only at the top level in some contexts" is superseded: at API 67.0 and later classes without an explicit sharing declaration run `with sharing` (L11930-11931); below 67.0 the mode depends on the inheritance chain and calling context (L11931-11937).

**When it occurs:** A batch submitted by a non-admin user or an integration user with limited visibility.

**How to avoid:** Declare the recalculation class `without sharing` (or `public without sharing`) and add a code comment explaining the intentional bypass. UNVERIFIED (2026-10-20): that `global` is required.

---

## Gotcha 3: Custom Row Cause Must Exist in the Target Org Before Deployment

**What happens:** Code that references a custom Apex sharing reason (for example `Project__Share.rowCause.TerritoryAccess__c`) fails at DML time if the reason is missing; `RowCause` is a restricted picklist (object_reference 264 L17456-17459). UNVERIFIED (2026-10-20): that the code still compiles and the exact `System.DmlException: FIELD_INTEGRITY_EXCEPTION, value not in set for restricted picklist field: RowCause` text.

**When it occurs:** Deploying to a new sandbox, production org, or CI environment where the sharing reason has not been created.

**How to avoid:** Sharing reasons are a Metadata API type (`SharingReason`, api_meta 264 L47631-47637; the earlier "not part of standard metadata deployments" wording is CONTRADICTED), so include it with the object in the deployment package. For a custom object you can also create it in Salesforce Classic: "Apex sharing reasons aren't available in Lightning Experience" (apex dev guide 264 L12879-12880). Add a smoke test that attempts a test insert with the reason.

---

## Gotcha 4: `All` Cannot Be Granted, and the Level Must Exceed the OWD

**What happens:** "The All access level is an internal value and can't be granted" (apex dev guide 264 L12730), and on AccountShare `All` "isn't valid for create or update calls" (object_reference 264 L17379). The field "must be set to an access level that's higher than the organization's default access level" (L12731-12732). UNVERIFIED (2026-10-20): the exact `INVALID_ACCESS_LEVEL, Invalid access level: All` text; an access level at or below the default instead raises `FIELD_FILTER_VALIDATION_EXCEPTION` containing `AccessLevel` (L12803-12804).

**When it occurs:** When a developer assumes `All` gives "full control", or grants `Read` on an object whose OWD is already Public Read Only.

**How to avoid:** Use `Edit` as the maximum, and treat the access-level error as benign when the grant is redundant, as the guide's sample does (L12990-12999). If ownership transfer is needed, update `OwnerId`.

---

## Gotcha 5: Re-Granting Can Update the Existing Row

**What happens:** The guide says that when "a manual share access level is set to Read and you insert a new one set to Write. The original share rows are updated to Write" (apex dev guide 264 L13024-13025). The AccountShare reference lists `update()` and `upsert()` among its supported calls (object_reference 264 L17349-17350), so the earlier claim that Share objects have no update path and do not support upsert is CONTRADICTED for AccountShare. UNVERIFIED (2026-10-20): the `(ParentId, UserOrGroupId, RowCause)` unique constraint and the `DUPLICATE_VALUE` error on an exact repeat.

**When it occurs:** Recalculation when access levels have changed, and retry logic that re-runs share inserts without cleaning up first.

**How to avoid:** In recalculation, delete the existing rows for the relevant `RowCause` and `ParentId` set before inserting fresh rows. In trigger logic, query existing rows and compare — insert only new grants and delete revoked ones.
