# Examples — Deployment Error Diagnosis

## Example 1 — Field type change fails on populated field

**Error.** `Cannot change type of field "Region__c" because it is
populated on N records`.

**Diagnosis.** Salesforce restricts type changes on fields with
data. The 3 valid options:

1. Clear the data (DML to set every record's `Region__c` to null),
   then change the type.
2. Build a new field `Region_v2__c` of the new type, migrate the
   data, retire the old field.
3. Live with the existing type.

For most non-trivial-data scenarios, option 2 is the right answer
— it preserves data continuity and doesn't require a maintenance
window.

---

## Example 2 — Profile FLS line for a field not in the package

**Error.** `Cannot find field 'Account.Custom_X__c' referenced in
profile 'Sales User'`.

**Two failure modes:**

1. **Field exists in source, not target, not in package.** Add
   the field to the package's `<types>CustomField` list, OR
   pre-deploy the field in a previous package.
2. **Field doesn't exist in source either.** The profile XML has
   a stale FLS reference. Edit the profile XML to remove the
   broken `<fieldPermissions>` block, OR scope the profile
   deploy to only fields in the current package.

The latter is more common with full-profile exports. Using
permission sets + `PermissionSet`-level package scoping avoids
this entirely.

---

## Example 3 — Test coverage failure: 73% across all classes

**Error.** `Average test coverage across all Apex Classes is 73%,
at least 75% is required.`

**Diagnosis SOQL.**

```apex
SELECT ApexClassOrTrigger.Name,
       NumLinesCovered,
       NumLinesUncovered
FROM ApexCodeCoverageAggregate
WHERE NumLinesUncovered > 50
ORDER BY NumLinesUncovered DESC
LIMIT 10
```

The classes with the most uncovered lines are the highest-leverage
targets. Adding a single test class that exercises a 200-line
class (currently 0% covered) lifts the org-wide average more than
adding 10 tests to a 20-line class.

---

## Example 4 — Inactive flow deploy error

**Error.** `Cannot deploy a package containing inactive flow
'My_Flow'`.

**Wrong instinct.** "Just don't deploy the flow."

**Why that's wrong.** The package may include the flow because
something else in the package depends on it.

**Right answer.** Set the flow's `<status>` to `Active` in
source. If the flow is genuinely retired, use `<status>Obsolete</status>`
which permits the deploy and stops new invocations without
deleting history.

```xml
<status>Obsolete</status>
```

---

## Example 5 — Trace `entity is in use` to its references

**Error.** `Cannot delete field 'Account.Old_Field__c' because it
is in use`.

**Search sources.**

```bash
# Search Apex classes / triggers
grep -r "Old_Field__c" force-app/main/default/classes/
grep -r "Old_Field__c" force-app/main/default/triggers/

# Search Flow XML
grep -r "Old_Field__c" force-app/main/default/flows/

# Search formula fields, validation rules
grep -r "Old_Field__c" force-app/main/default/objects/

# Search reports / dashboards
grep -r "Old_Field__c" force-app/main/default/reports/
grep -r "Old_Field__c" force-app/main/default/dashboards/

# Setup → Where Is This Used? (UI) for a final pass
```

For each reference: deactivate, replace, or update. Deploy the
deactivations as a separate package. Then deploy the field
deletion.

---

## Anti-Pattern: Deploying with --ignore-errors / --ignore-warnings

**What it looks like.** CI pipeline configures
`sf project deploy start --ignore-errors --ignore-warnings`.

**What goes wrong.** Errors that should have stopped the deploy
are masked. The target ends up half-deployed; pieces are missing;
behavior at runtime is unpredictable.

**Correct.** Errors should be triaged, not ignored. The whole
point of error messages is to surface real problems. Use
`--ignore-warnings` selectively for known-acceptable warnings
(missing test coverage on managed-package code, etc.) — never
`--ignore-errors`.
