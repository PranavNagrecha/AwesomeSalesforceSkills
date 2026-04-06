# Gotchas -- Pre-Deployment Checklist

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Validation Deploy Lock Contention

**What happens:** A validation deploy acquires compile locks on Apex classes while running tests. If another validation or deployment is already in progress against the same org, the second operation fails with a lock contention error, even though validation deploys do not write metadata.

**When it occurs:** Teams running parallel CI pipelines that both target the same production org for validation, or a developer running an ad-hoc validation while a scheduled pipeline is already validating.

**How to avoid:** Check the Deployment Status page (Setup > Environments > Deploy > Deployment Status) before starting a validation. Only one validation or deployment can run at a time per org. Coordinate validation windows across teams.

---

## Gotcha 2: RunSpecifiedTests Per-Class Coverage Threshold

**What happens:** A deployment validated with `RunSpecifiedTests` fails because a single Apex class in the package has only 60% coverage, even though the org-wide aggregate is 82%. The deploy error message says "Code coverage for class X is 60%, which is below the 75% threshold."

**When it occurs:** When using `RunSpecifiedTests` instead of `RunLocalTests`. The `RunSpecifiedTests` option enforces 75% coverage per class included in the deployment package, not just 75% aggregate across the org. This is stricter and catches classes that are carried by the org average under `RunLocalTests`.

**How to avoid:** Before choosing `RunSpecifiedTests`, check coverage for every Apex class in the package individually. If any class is below 75%, either add test coverage or switch to `RunLocalTests` (which only enforces aggregate).

---

## Gotcha 3: Quick-Deploy Window Resets on New Validation

**What happens:** A team validates on Monday, earning a quick-deploy ID valid for 10 days. On Wednesday they discover a typo, fix it, and re-validate. The Monday quick-deploy ID is now invalid -- only the Wednesday ID works. If the Wednesday validation fails, they have lost their Monday window entirely.

**When it occurs:** Any time a new validation deploy is run against the same org with the same deployment package. The platform invalidates prior quick-deploy IDs for overlapping component sets.

**How to avoid:** Treat the validation deploy as a locked gate. Do not re-validate unless the previous validation has a known defect. If you must re-validate, plan for the possibility that the new validation fails and you need additional time.

---

## Gotcha 4: Sandbox Test Pass Does Not Guarantee Production Pass

**What happens:** All Apex tests pass in the full-copy staging sandbox. The team deploys directly to production without a validation deploy. Three tests fail in production due to: (a) a managed package trigger that fires in production but was deactivated in the sandbox during the last refresh, (b) SOQL queries hitting the 50,000-row limit against production data volumes, and (c) a sharing rule that restricts visibility in production but not in the sandbox.

**When it occurs:** Every time a team treats sandbox test results as a proxy for production test results. Even full-copy sandboxes diverge from production within hours of a refresh due to configuration changes, data modifications, and managed package updates.

**How to avoid:** Always run a validation deploy (`checkOnly: true`) directly against production. This is the only way to confirm tests pass in the actual production environment. Sandbox testing is a development gate, not a release gate.

---

## Gotcha 5: Destructive Changes and Dependency Ordering

**What happens:** A `destructiveChangesPost.xml` file deletes a custom field that is referenced by a workflow rule not included in the deployment. The deploy succeeds (the field is deleted), but the workflow rule now throws a runtime error because it references a field that no longer exists.

**When it occurs:** When destructive changes are authored based on the deployment package contents without checking what other components in the target org depend on the deleted component. The Metadata API does not prevent deletion of components that have dependents outside the deployment package.

**How to avoid:** Before adding any component to a destructive manifest, query `MetadataComponentDependency` in the target org to find all dependents. Update or remove those dependents as part of the same release. Process constructive changes (adding the replacements) before destructive changes (removing the old components).
