# Gotchas — Mixed DML and Setup Objects

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: PermissionSetAssignment Triggers the Restriction

**What happens:** A developer inserts a `PermissionSetAssignment` in the same transaction as a custom object record and gets `MIXED_DML_OPERATION`. They expected only `User` to be restricted.

**When it occurs:** Any time code creates or modifies `PermissionSetAssignment`, `PermissionSetGroup`, `GroupMember`, or `QueueSObject` alongside non-setup objects.

**How to avoid:** Treat every object on the setup object list as restricted. The list is longer than most developers assume: User, UserRole, Group, GroupMember, PermissionSet, PermissionSetAssignment, PermissionSetGroup, QueueSObject, ObjectTerritory2Association, Territory2, UserTerritory2Association, and UserPackageLicense.

---

## Gotcha 2: System.runAs() Does Not Fix Production Code

**What happens:** A developer wraps setup DML in `System.runAs()` in production Apex, expecting it to create a separate DML context. The code still throws `MIXED_DML_OPERATION`.

**When it occurs:** `System.runAs()` only creates a separate DML transaction context during test execution. In production, it changes the running user context for permission evaluation but does not create a new DML boundary.

**How to avoid:** In production code, the only workaround is `@future` or a Queueable that runs in a genuinely separate transaction.

---

## Gotcha 3: @testSetup Is Still One Transaction

**What happens:** A `@testSetup` method inserts a User and a custom object record without `System.runAs()` isolation. The setup method fails with `MIXED_DML_OPERATION` before any test method runs.

**When it occurs:** Developers assume `@testSetup` runs in a special context. It does not — it is subject to the same mixed DML restriction as any other Apex method.

**How to avoid:** Use `System.runAs()` inside `@testSetup` just as you would in a `@IsTest` method.

---

## Gotcha 4: The Restriction Applies to Update and Delete, Not Just Insert

**What happens:** A batch job updates a User's `IsActive` field and also updates an Account in the same `execute()` method. The batch fails with `MIXED_DML_OPERATION`.

**When it occurs:** Developers remember the insert restriction but forget that update, delete, and undelete of setup objects also trigger it.

**How to avoid:** Any DML operation (insert, update, upsert, delete, undelete) on a setup object in the same transaction as any DML operation on a non-setup object triggers the restriction.

---

## Gotcha 5: Enqueuing a Queueable Does Not Escape the Current Transaction

**What happens:** A developer performs User DML, then enqueues a Queueable for Account DML. The error fires before the Queueable even runs.

**When it occurs:** The `System.enqueueJob()` call itself is just a system method invocation in the current transaction. If setup DML already happened in this transaction, any subsequent non-setup DML is still in the same transaction.

**How to avoid:** Move the setup DML into the Queueable (or @future), not the non-setup DML. The async boundary must wrap the setup objects, not the other way around.

---

## Gotcha 6: Order Matters — Non-Setup First, Then Setup

**What happens:** A test creates a User first (setup DML), then tries to create an Account (non-setup DML) outside `System.runAs()`. The Account insert throws the error even though the User insert succeeded.

**When it occurs:** The restriction is bidirectional within a single transaction context. Once any setup DML occurs, no non-setup DML is allowed, and vice versa.

**How to avoid:** In test classes, create non-setup records first (outside `System.runAs()`), then create setup records inside `System.runAs()`. This ordering ensures the non-setup DML context is clean before the setup DML context begins.
