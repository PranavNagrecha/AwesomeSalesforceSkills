# Gotchas — Apex Custom Settings Hierarchy

Non-obvious Salesforce platform behaviors that cause real production problems.

## Gotcha 1: `getInstance()` Returns An Empty Record, Not `null`

**What happens:** A developer assumes `getInstance()` returns `null` when no setting is configured and writes `if (s == null) return defaultValue;`. The branch never fires — `s` is a non-null record with null field values.

**When it occurs:** Any time no tier (User, Profile, Org) has been populated.

**How to avoid:** Null-check the specific field(s) you need. The record itself is always non-null for Hierarchy Custom Settings.

---

## Gotcha 2: `getOrgDefaults()` *Can* Return `null`

**What happens:** Unlike `getInstance()`, `getOrgDefaults()` returns `null` when no org-default row exists. Code that treats `getInstance()` and `getOrgDefaults()` as interchangeable gets a surprise NPE.

**When it occurs:** Refactoring from `getInstance()` to `getOrgDefaults()` to avoid user-tier lookups in batch context.

**How to avoid:** Always null-check the record when you use `getOrgDefaults()`; accept that the record is always non-null when using `getInstance()`.

---

## Gotcha 3: Custom Setting Data Does Not Travel With Metadata Deploys

**What happens:** A deployment succeeds but the feature is broken. Investigation reveals that the target org has no rows in the setting — the deploy shipped the object but not the data.

**When it occurs:** Every sandbox refresh and every production deploy of a new Custom Setting.

**How to avoid:** Document the seeding procedure in a README checked into the repo, or automate it with a post-install `@InvocableMethod` / post-deploy script. For deploy-time configuration, use Custom Metadata Types instead — CMDT records deploy with source.

---

## Gotcha 4: `Privileged` Determines Who Can Write

**What happens:** A trigger that `insert`s a Custom Setting record fails for standard users with `INSUFFICIENT_ACCESS_OR_READONLY`, but works for admins. The developer thinks the trigger has a profile-specific bug.

**When it occurs:** When the setting is created without `Privileged = true` (a property in the object definition) and the calling code runs `without sharing` only for access — but the DML still checks object permissions.

**How to avoid:** Decide up front whether end users should write. If not, set `Privileged = true` in the object definition (or require an admin-only code path).

---

## Gotcha 5: `SetupOwnerId` Accepts User Or Profile Silently

**What happens:** An integration tries to write a per-profile override but passes a User Id; the row inserts as a per-user override and only affects one person.

**When it occurs:** Any time `SetupOwnerId` is set dynamically from a variable whose type (User vs Profile) is not asserted.

**How to avoid:** Validate the prefix (`005` for User, `00e` for Profile, org Id for default) or use `Id.getSobjectType()` before inserting.

---

## Gotcha 6: `@IsTest(SeeAllData=true)` Is Required For Reading From Some Legacy Settings

**What happens:** A unit test reads `MySetting__c.getInstance()` and finds it empty, even though production has values. Apex test context isolates data from the org.

**When it occurs:** Test classes without `@IsTest(SeeAllData=true)` (which is discouraged) or without explicit setup data.

**How to avoid:** Always seed the setting in `@TestSetup` or the test method itself. Do NOT enable `SeeAllData` just to read settings — insert them in the test.

---

## Gotcha 7: Hierarchy Setting Values Are Not Audit-Logged By Default

**What happens:** An admin changes the org-default value of a feature flag, a bug appears in production, and no one can tell when or who changed the setting. Salesforce does not audit-log Custom Setting writes by default.

**When it occurs:** Any change to a setting record via Setup UI, Data Loader, or Apex.

**How to avoid:** For auditable config, use Custom Metadata Types (which deploy via changesets/source) or Field History Tracking on the setting's fields (enable per-field in the object definition).

---

## Gotcha 8: Cache Is Per-Transaction, Not Cross-Transaction

**What happens:** A team assumes Custom Setting reads are "cached" and is surprised that a 6-hour batch reads the setting anew in each `execute()` call, causing 40 SOQL queries for 40 batches.

**When it occurs:** Long-running async jobs.

**How to avoid:** Cache the value once in a member variable of the batch class or Queueable; use `Database.Stateful` if you need it across `execute()` invocations.
