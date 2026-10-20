# Gotchas -- Pre-Deployment Checklist

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Deployments Queue, One at a Time

**What happens:** "only one deployment can run at a time", the others "remain in the queue", and queued deployments "are not necessarily executed in the order in which they were submitted" (api_meta 264 L4246-4248). A running deploy also locks write-access to the resources it deploys, and changes to those resources meanwhile "can result in errors" (L4214-4216). UNVERIFIED (2026-10-20): that a validation takes compile locks on Apex classes and that a second operation fails with a lock-contention error; the guide describes queuing, not failure, so the earlier text of this gotcha was replaced.

**When it occurs:** Teams running parallel CI pipelines that both target the same production org, or a developer starting an ad-hoc validation while a scheduled pipeline is deploying; the later job waits and may run out of order.

**How to avoid:** Check the Deployment Status page (enter Deployment Status in the Setup Quick Find box, api_meta 264 L4223) before starting. To control order, submit deployments one at a time after the previous one has completed successfully (L4248-4249). Coordinate windows across teams.

---

## Gotcha 2: RunSpecifiedTests Per-Class Coverage Threshold

**What happens:** A deployment validated with `RunSpecifiedTests` fails because a single Apex class in the package has only 60% coverage, even though the org-wide aggregate is 82%. UNVERIFIED (2026-10-20): the exact error message text is not in either corpus.

**When it occurs:** When using `RunSpecifiedTests` instead of `RunLocalTests`. The `RunSpecifiedTests` level requires each class and trigger in the package to be covered at 75% individually, "different than the overall coverage percentage" (api_meta 264 L4433-4434); an all-tests or local-tests run needs overall coverage of at least 75% with some coverage on triggers (L3582). This is stricter and catches classes that are carried by the org average under `RunLocalTests`.

**How to avoid:** Before choosing `RunSpecifiedTests`, check coverage for every Apex class in the package individually. If any class is below 75%, either add test coverage or switch to `RunLocalTests` (overall coverage, L3582).

---

## Gotcha 3: Re-Validating Mid-Window

**What happens:** A team validates on Monday, earning a quick-deploy ID usable within 10 days (api_meta 264 L3579). On Wednesday they discover a typo, fix it, and re-validate. The Monday ID no longer matches the corrected package, so Wednesday's validation is the one to redeem. UNVERIFIED (2026-10-20): that the platform invalidates prior quick-deploy IDs, and that the window "resets"; the guide says only that the components must have been validated within the last 10 days (L4969). If the Wednesday validation fails, the team has no passing validation for the corrected package.

**When it occurs:** Any time a package changes after validation and is validated again.

**How to avoid:** Treat the validation deploy as a locked gate. Do not re-validate unless the previous validation has a known defect. If you must re-validate, plan for the possibility that the new validation fails and you need additional time.

---

## Gotcha 4: Sandbox Test Pass Does Not Guarantee Production Pass

**What happens:** All Apex tests pass in the full-copy staging sandbox. The team deploys directly to production without a validation deploy. Three tests fail in production due to: (a) a managed package trigger that fires in production but was deactivated in the sandbox during the last refresh, (b) SOQL queries hitting a row limit against production data volumes, and (c) a sharing rule that restricts visibility in production but not in the sandbox. The three causes are illustrative and UNVERIFIED (2026-10-20): none is stated in the corpus.

**When it occurs:** Every time a team treats sandbox test results as a proxy for production test results. UNVERIFIED (2026-10-20): that even full-copy sandboxes diverge from production within hours of a refresh.

**How to avoid:** Always run a validation deploy (`checkOnly: true`) directly against production. This is the only way to confirm tests pass in the actual production environment. Sandbox testing is a development gate, not a release gate.

---

## Gotcha 5: Destructive Changes and Dependency Ordering

**What happens:** By default deletions are processed before additions; `destructiveChangesPre.xml` and `destructiveChangesPost.xml` (API 33.0+) set the timing, and the guide's example uses Post to delete a custom object after the Apex class that referenced it is updated, since the object cannot be deleted while the class still depends on it (api_meta 264 L4749-4758). UNVERIFIED (2026-10-20): the earlier scenario here, a Post deletion of a field that succeeds while a workflow rule outside the package then throws at runtime; and the claim that the Metadata API "does not prevent deletion of components that have dependents outside the deployment package". The guide's example points the other way for dependents it can see.

**When it occurs:** When destructive changes are authored from the package contents without checking what else in the target org depends on the deleted component.

**How to avoid:** Find all dependents of a component before adding it to a destructive manifest (a `MetadataComponentDependency` query is UNVERIFIED, 2026-10-20: not in either corpus). Update or remove those dependents in the same release, and choose Pre or Post so the dependent is updated first.
