---
name: deployment-error-diagnosis
description: "Pattern catalog of common Salesforce metadata-deploy errors and their fixes — `Cannot change type` (field type already in use), dependent-metadata ordering (deploy field before profile that references it), profile / permission set delta issues (deactivated permissions blocking deploy), missing-reference errors, test class coverage failures, and the package.xml-shape mistakes that produce confusing first-line errors. Covers the SFDX / Metadata API error message shapes and how to translate them into the actual fix. NOT for designing the deployment pipeline (use devops/sfdx-cicd-pipeline), NOT for change set orchestration (use admin/changeset-builder)."
category: devops
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
triggers:
  - "salesforce deployment cannot change type field error"
  - "metadata deploy missing reference dependency order"
  - "profile field-level security deploy permset delta"
  - "package.xml wildcard cannot be deployed"
  - "deployment test coverage failure 75 percent"
  - "metadata api INVALID_CROSS_REFERENCE_KEY"
tags:
  - deployment
  - metadata-api
  - sfdx
  - error-diagnosis
  - dependency-order
  - test-coverage
inputs:
  - "The deployment error message verbatim"
  - "Source: change set / SFDX deploy / Metadata API / Copado / Gearset / Flosum"
  - "Source and target environments"
  - "Whether the deploy is being run as a fresh sandbox (different rules)"
outputs:
  - "Translation of the error message into the actual fix"
  - "Ordering correction (which metadata to add to the package; which to deploy first)"
  - "Test-coverage fix if applicable (which class / method needs coverage)"
  - "Workaround (if the underlying schema change isn't directly deployable)"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-05-05
---

# Deployment Error Diagnosis

Salesforce deploy errors are notorious for being technically
correct but actionably opaque. "INVALID_CROSS_REFERENCE_KEY" tells
you a reference is broken, not which one. "Field type cannot be
changed" doesn't tell you which records are using the field.
"Dependent class is invalid and needs recompilation" implicates
some class but not yours.

This skill is a translation layer: error message → actual cause →
actual fix. It assumes you have the deploy log; the input is the
error string, the output is the next action.

What this skill is NOT. Pipeline design (CI/CD shape, environment
strategy) is `devops/sfdx-cicd-pipeline`. Change-set construction
mechanics — `admin/changeset-builder`. This skill is for the
"my deploy failed; what does this mean" moment.

---

## Before Starting

- **Capture the FULL error message.** Not just the first line —
  the dependent-metadata error often appears 30 lines down.
- **Capture the package contents.** Knowing what's IN the package
  is half the diagnosis.
- **Note source / target environments.** A deploy that works prod
  → sandbox may fail dev → prod for permission reasons.
- **Note whether tests ran.** "Tests didn't run" vs "tests ran and
  failed" are different problems.

---

## Core Concepts

### The most-common error patterns

| Error message (paraphrased) | Actual cause | Fix |
|---|---|---|
| `Cannot change type of field` | Field already populated; type changes restricted | Either: data-clear + change, or new field + migration + delete old |
| `Dependent class is invalid and needs recompilation` | A class that depends on the changed metadata didn't rebuild | Add the dependent class to the package; deploy together |
| `INVALID_CROSS_REFERENCE_KEY: invalid cross-reference id` | A profile / permset references metadata not in the target | Add the referenced metadata; or scrub the profile's reference |
| `Field-level security cannot be set on a non-existent field` | Profile delta references a field the package doesn't deploy and target doesn't have | Add the field to the package; or remove the FLS line |
| `INVALID_FIELD: No such column` (in test class) | Schema referenced in test doesn't exist in target | Add the schema to package, or fix the test |
| `Average test coverage across all Apex Classes is below 75%` | Org-wide or per-class coverage threshold | Add tests for the class with low coverage |
| `Cannot deploy a package containing inactive flow` | Flow with `<status>Draft</status>` | Set `<status>Active</status>` or `Obsolete` before deploy |
| `Required field is missing: name` (on a record) | Standard validation rule on target rejecting Apex test data | Use `Test.startTest()` + bypass or fix the test data |
| `Component error: 'X' is not a valid value for type 'Y'` | Picklist value missing in target | Add picklist value to package; or update package XML to omit |
| `Ambiguous reference to a method` | Two classes have same method signature; deploy order resolves wrong one | Fully-qualify the method call or rename |
| `entity is in use` (when retiring fields) | Active references in flows / formulas / validation rules | Find references; deactivate or delete them; redeploy |

### `package.xml` ordering smells

`package.xml` doesn't have explicit ordering — the platform
resolves dependencies. But:

- **Wildcards (`<members>*</members>`)** with explicit
  `<members>` for the same type confuse the platform; pick one.
- **Profile / Permission Set delta** must include the metadata
  it references. A profile delta saying `<field>Account.Custom__c</field>`
  with `<editable>true</editable>` requires `Account.Custom__c`
  in the package OR pre-existing in target.
- **`PermissionSetGroup`** must be deployed AFTER its component
  PermissionSets.
- **`Flow`** with subflow references requires the subflow active in
  target (or in the package as Active).

### Profile / Permission Set deltas

Profiles and permission sets are notoriously verbose; SFDX often
exports them in full (every FLS line for every field). Deploying
a full profile against a target with different fields produces
errors per missing field.

The cleanest patterns:

- **Permission Set Groups** instead of profiles where possible.
- **Profile delta scoping** — only the fields / objects in the
  package, not the full profile.
- **`profileObjectAccesses` + `profileFieldLevelSecurities`** in
  package.xml so SFDX exports just those entries.

### Test coverage failures

Salesforce requires 75% test coverage org-wide for production
deploy. Per-class coverage is also tracked. Failures present as:

```
Average test coverage across all Apex Classes is 73%, at least 75% is required.
```

Or:

```
Failed: classes/MyHandler — only 60% covered
```

Diagnosis: query `ApexCodeCoverageAggregate` to find low-coverage
classes; add tests; redeploy.

---

## Common Patterns

### Pattern A — `Cannot change type` field migration

**When to use.** Need to change `Region__c` from Text to Picklist.

**Sequence.**

1. Create new field `Region_v2__c` of the new type.
2. Migrate data: SOQL update setting v2 from v1 mapping rule.
3. Update all references (Apex, formulas, validation rules,
   reports, dashboards, page layouts) to use v2.
4. Delete v1 in a separate deploy.

The "delete v1" step requires v1 to have no remaining references —
the deploy fails if it does, with a more useful error listing the
references.

### Pattern B — Profile / permset cross-reference fix

**When to use.** Error: `Cannot find field Account.Custom_X__c
referenced in profile`.

**Diagnosis.**

1. Confirm the field exists in source.
2. Confirm the package.xml includes the field (either explicitly
   or via `<members>*</members>` for `CustomField`).
3. If yes: target may have a stale profile referencing the field.
   Add the field to the package.
4. If no: the field needs to be added to the package, OR the
   profile delta needs to omit the FLS line for the missing field.

### Pattern C — Test coverage failure on a deploy

**When to use.** Production deploy fails on coverage threshold.

**Diagnosis.**

1. SOQL: `[SELECT ApexClassOrTrigger.Name, NumLinesCovered, NumLinesUncovered FROM ApexCodeCoverageAggregate WHERE NumLinesUncovered > 0 ORDER BY NumLinesUncovered DESC LIMIT 20]`.
2. The classes with the most uncovered lines are the targets.
3. Write tests for them in the same package as the deploy.
4. Re-run.

For "average across all classes" failures, the calculation is
total-lines-covered / total-lines. One fully-covered new class
can lift the average enough; check a representative
high-line-count class first.

### Pattern D — Flow active / inactive deploy errors

**When to use.** "Cannot deploy a package containing inactive flow"
or "Active flow refers to inactive subflow".

**Approach.**

- Set `<status>Active</status>` on the top-level flow.
- For subflows referenced by an active flow, also set Active.
- For flows being retired, set `<status>Obsolete</status>` —
  doesn't fail the deploy, doesn't run new invocations, preserves
  history.

### Pattern E — Cleaning up `entity is in use` for field deletion

**When to use.** Field deletion blocked by "entity is in use".

**Diagnosis.**

- The field is referenced somewhere active. Search Apex / formulas
  / validation rules / reports / dashboards / Flow / layouts.
- The "Where Is This Used?" Setup feature shows references but
  isn't always exhaustive.
- For comprehensive search: SFDX `sf data query` + grep across
  source.

**Approach.**

1. Inventory references; deactivate / replace each.
2. Deploy the deactivations / replacements as a separate package.
3. Then deploy the field deletion.

---

## Decision Guidance

| Error pattern | Approach |
|---|---|
| `Cannot change type` | Pattern A (new field + migrate + delete old) |
| `Dependent class is invalid` | Add the dependent class to the package; deploy together |
| `INVALID_CROSS_REFERENCE_KEY` | Trace the broken reference; usually missing metadata in package |
| `Field-level security on non-existent field` | Add field to package OR scrub profile delta |
| `Average test coverage below 75%` | Pattern C (find low-coverage class, add tests) |
| `Cannot deploy inactive flow` | Set `<status>Active</status>` or `<status>Obsolete</status>` |
| `entity is in use` | Pattern E (find references, deactivate, redeploy) |
| `Component error: not a valid picklist value` | Add picklist value to package; or align values across orgs |
| Wildcard + explicit members confusion | Pick one (wildcard OR explicit, not both) |
| `Ambiguous reference to method` | Fully-qualify or rename |

---

## Recommended Workflow

1. **Capture the full error message** + the deploy package contents.
2. **Match against the error patterns above.** Most production deploy errors fit a known shape.
3. **For unmatched errors:** search the salesforce.stackexchange.com Q&A for the exact error string.
4. **Apply the fix** in source control. Don't hotfix the target org directly; the source-target gap creates more errors.
5. **Re-run the deploy.**
6. **For deploys that keep failing:** capture the sequence of errors. The order tells you the dependency graph.

---

## Review Checklist

- [ ] Full deploy error message captured (not just first line).
- [ ] Package contents reviewed.
- [ ] Source / target environments noted.
- [ ] Test-coverage status (ran / didn't run / failed) noted.
- [ ] Fix applied in source control, not the target org.
- [ ] Dependent metadata included in the package.
- [ ] Profile / permset delta scoped to the package's metadata.

---

## Salesforce-Specific Gotchas

1. **`Cannot change type` requires data clearance.** Type changes are restricted on populated fields. (See `references/gotchas.md` § 1.)
2. **Profile / permset full-export deploys verbose deltas** that fail per missing field. (See `references/gotchas.md` § 2.)
3. **Test coverage org-wide vs per-class** — failures can be either; diagnose appropriately. (See `references/gotchas.md` § 3.)
4. **`<members>*</members>` + explicit `<members>` for the same type** confuses the platform. (See `references/gotchas.md` § 4.)
5. **Flow retirement should be `Obsolete`, not delete.** Preserves history; doesn't run new invocations. (See `references/gotchas.md` § 5.)
6. **`entity is in use` rarely surfaces every reference.** Search source comprehensively, not just Setup → Where Is This Used. (See `references/gotchas.md` § 6.)
7. **PermissionSetGroup deploys after component PermissionSets.** Order matters for groups. (See `references/gotchas.md` § 7.)

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Error → Cause → Fix mapping | Translated explanation for the specific error |
| Updated package.xml | If the fix is a packaging-level change |
| Test class additions | If coverage was the failure |
| Reference cleanup commits | If `entity is in use` was the failure |

---

## Related Skills

- `devops/sfdx-cicd-pipeline` — pipeline design where these errors show up.
- `admin/changeset-builder` — change-set-specific deployment.
- `apex/test-class-standards` — test coverage that prevents Pattern C failures.
- `admin/order-of-execution` — when "deploy succeeds but behavior is wrong" comes from save-time ordering.
