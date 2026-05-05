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
