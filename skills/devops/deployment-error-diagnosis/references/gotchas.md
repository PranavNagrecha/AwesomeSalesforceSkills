# Gotchas — Deployment Error Diagnosis

Non-obvious behaviors of Salesforce metadata deploys.

---

## Gotcha 1: `Cannot change type` requires data clearance

**What happens.** Field type change rejected with `Cannot change
type ... because it is populated`.

**How to avoid.** Either clear the data (DML to null) or use the
v2-field migration pattern (new field + migrate + delete old).
Type changes on populated fields are restricted by design.

---

## Gotcha 2: Full-profile exports cause cross-reference failures

**What happens.** SFDX exports a profile with FLS lines for every
field in the source. Deploying it against a target with different
fields produces "field not found" errors per missing field.

**How to avoid.** Use Permission Sets + Permission Set Groups
where possible (smaller, scoped). For profiles, scope the package
explicitly:

```xml
<types>
    <members>Sales_User</members>
    <name>Profile</name>
</types>
```

Plus the fields the profile references. Or use `profileFieldLevelSecurities`
+ `profileObjectAccesses` to scope to the package contents.

---

## Gotcha 3: Test coverage is org-wide AND per-class

**What happens.** Deploy passes "average across all classes" but
fails "individual class below 75%" for a specific new class.

**How to avoid.** Both thresholds apply. New classes need 75%
individually AND the org-wide average needs 75%. Both can fail
independently.

---

## Gotcha 4: Wildcard + explicit `<members>` for the same type confuses the platform

**What happens.** package.xml has `<members>*</members>` AND
`<members>Custom_Field_X__c</members>` for `CustomField`. The
platform's behavior is implementation-defined; some deploys
include the explicit member, some don't.

**How to avoid.** Pick one. Wildcard for "everything"; explicit
for "just these". Don't mix.

---

## Gotcha 5: Flow retirement: `<status>Obsolete</status>` not delete

**What happens.** Admin tries to delete a flow that has historical
runs. Delete fails. Or succeeds and loses history.

**How to avoid.** Use `<status>Obsolete</status>` to retire flows.
Existing interview history is preserved; new invocations are
prevented; the flow remains in the org for audit.

---

## Gotcha 6: `entity is in use` doesn't list every reference

**What happens.** "Where Is This Used?" Setup feature shows some
references but misses others (formula fields, dynamic Apex). Admin
removes the listed references; deploy still fails.

**How to avoid.** Source-side comprehensive search (grep across
metadata + Apex). Setup's reference report is a starting point,
not the source of truth.

---

## Gotcha 7: PermissionSetGroup must deploy after its component PermissionSets

**What happens.** Package contains PermissionSetGroup `Custom_PSG`
referencing PermissionSet `New_Permset`. Both in the package; deploy
fails because the platform tries to deploy the PSG before the
PermissionSet exists.

**How to avoid.** Deploy in two passes: PermissionSets first,
PermissionSetGroups second. Or rely on the platform's dependency
resolution (works for most cases, but not all combinations).

---

## Gotcha 8: `--ignore-errors` / `--ignore-warnings` masks real failures

**What happens.** CI pipeline uses `--ignore-errors`; deploys
"succeed" but the target is half-deployed; runtime breaks
mysteriously.

**How to avoid.** Never use `--ignore-errors`. `--ignore-warnings`
only for documented-acceptable warnings (managed-package coverage
limitations, etc.).

---

## Gotcha 9: Validation rule's `errorConditionFormula` evaluation differs by version

**What happens.** Validation rule deploys; behavior in target is
slightly different from source because the formula evaluation
engine version differs.

**How to avoid.** Match Apex / metadata API versions across
source and target. Test validation rules in target with realistic
data after deploy.

---

## Gotcha 10: Inactive Apex classes are deployed as inactive

**What happens.** Source has an inactive Apex class
(`<status>Inactive</status>` in `*.cls-meta.xml`). Deploys to
target as inactive. Code that depended on it now fails at runtime.

**How to avoid.** Verify class status (`Active` vs `Inactive`)
matches the intent before deploy. The metadata version-controls
the activation state.

---

## Gotcha 11: "Operation failed due to fields being inaccessible" at deploy-time test execution names no field

**What happens.** A validation deploy (`--test-level RunSpecifiedTests`
or `RunLocalTests`) compiles every component clean, then every test
method fails at its own seed `insert`:

```
System.DmlException: Operation failed due to fields being inaccessible
on Sobject Case, check errors on Exception or Result!
```

The message says a field is inaccessible and does not say which one.
At API 67.0+ this is FLS, not a syntax problem: Apex runs in user
context by default, so `insert` inside `System.runAs(user)` — or any
DML at `AccessLevel.USER_MODE` — checks create access on every
populated field, including one a factory method assigned from a null
argument (the field still counts as "populated"; see
`apex/test-class-standards` Gotcha 14 for that half of the bug).

**How to avoid.** Don't guess the field from the object's shape —
print it. Wrap the failing insert in try/catch inside the test and
rethrow with the diagnostic attached:

```apex
try {
    insert seedRecords;
} catch (DmlException e) {
    List<String> failedFields = e.getDmlFieldNames(0);
    Map<String, Schema.SObjectField> fieldMap =
        seedRecords[0].getSObjectType().getDescribe().fields.getMap();
    for (String f : failedFields) {
        System.debug(f + ' createable=' + fieldMap.get(f).getDescribe().isCreateable());
    }
    System.debug('profile=' + [SELECT Profile.Name FROM User WHERE Id = :UserInfo.getUserId()].Profile.Name);
    System.debug('psa=' + [SELECT COUNT() FROM PermissionSetAssignment WHERE AssigneeId = :UserInfo.getUserId()]);
    throw e;
}
```

`e.getDmlFieldNames(0)` turns the generic message into an explicit
field list; the describe loop shows which of those the running user
actually can't create; the profile and `PermissionSetAssignment`
count rule out "wrong user" versus "permission set never assigned."
Re-run the same deploy — the fix is either the permission set the
build ships, or the test's own factory populating a field it didn't
need to. Evidence: `.sfskills/builds/tier2-webhook/reports/MOCK-DEPLOY-M1.md`
run 7, where the probe isolated the field to `AccountId` on a
Standard User holding the build's permission set.
