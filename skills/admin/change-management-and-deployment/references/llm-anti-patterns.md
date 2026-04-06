# LLM Anti-Patterns — Change Management and Deployment

Common mistakes AI coding assistants make when generating or advising on Salesforce metadata deployment and release management.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Treating change set deployment as atomic and rollback-safe

**What the LLM generates:** "Deploy the change set to production. If something goes wrong, roll back the change set."

**Why it happens:** LLMs equate Salesforce change sets with version-controlled deployments that support rollback. Change sets are additive and destructive changes (field deletions, flow deactivations) are not automatically reversible. There is no native "undo" for a deployed change set.

**Correct pattern:**

```
Change sets are NOT rollback-safe. Plan for this:
1. Before deploying, document the current state of every component
   being overwritten (screenshot, metadata export, or sandbox snapshot).
2. Prepare a "rollback change set" containing the original component
   versions from production, ready to deploy if needed.
3. For destructive changes (deleting fields, retiring flows),
   there is no change-set rollback — manual re-creation is required.
4. Consider using SFDX source-tracked deployments with version control
   for true rollback capability.
```

**Detection hint:** If the output says "roll back the change set" as if it is a single-click operation, rollback is being oversimplified. Search for `roll back` without a corresponding manual rollback plan.

---

## Anti-Pattern 2: Omitting dependent metadata from the deployment package

**What the LLM generates:** "Add the Flow to the change set and deploy it."

**Why it happens:** LLMs list the primary component but not its dependencies. Flows may reference custom fields, custom metadata types, Apex classes, or custom labels that must also be in the change set. Missing dependencies cause validation failures in the target org.

**Correct pattern:**

```
Always include dependent metadata:
1. For Flows: custom fields, custom objects, custom labels, Apex actions,
   email templates, and custom metadata types referenced by the Flow.
2. For Apex classes: referenced custom objects, fields, and any
   classes or interfaces they depend on.
3. Use "View/Add Dependencies" button in the change set editor
   to auto-detect some dependencies (not all are caught).
4. For SFDX: run `sf project deploy validate` in the target org
   before the actual deployment to catch missing dependencies.
```

**Detection hint:** If the output adds a single component to a change set without mentioning dependency analysis, dependencies are likely missing. Search for `dependencies` or `View/Add Dependencies`.

---

## Anti-Pattern 3: Suggesting direct production edits for "small changes"

**What the LLM generates:** "For simple changes like adding a field, just make the change directly in production."

**Why it happens:** LLMs optimize for speed and suggest skipping the sandbox-to-production promotion path for seemingly low-risk changes. Direct production changes bypass testing, create configuration drift between environments, and violate change management governance.

**Correct pattern:**

```
All changes should follow the promotion path:
1. Make the change in a sandbox (Developer or Developer Pro).
2. Test in the sandbox.
3. Deploy to a staging/UAT sandbox if available.
4. Deploy to production via change set, SFDX, or DevOps Center.

The only exceptions are:
- Emergency data fixes (with documented approval).
- User management tasks (creating users, resetting passwords).
- Report and dashboard creation by end users.
Even "simple" field additions can break validation rules, flows,
or integrations if not tested first.
```

**Detection hint:** If the output recommends making changes "directly in production" or "just in prod," it is bypassing change management. Search for `directly in production` or `just in prod`.

---

## Anti-Pattern 4: Ignoring deployment order for interdependent components

**What the LLM generates:** "Deploy all your metadata in one change set — custom objects, fields, flows, permission sets, and sharing rules."

**Why it happens:** LLMs treat deployment as a single atomic operation. While change sets do deploy as a unit, SFDX deployments and multi-step releases often require specific deployment order. Sharing rules cannot deploy before the OWD they depend on, permission sets referencing new fields fail if fields are not yet in the target, and flows referencing new Apex classes need the classes deployed first.

**Correct pattern:**

```
Follow dependency-driven deployment order:
1. Custom objects and fields (the data model).
2. Apex classes and triggers (code that references the model).
3. Flows (which may reference both fields and Apex actions).
4. Page layouts, record types, compact layouts.
5. Permission sets and profiles (which reference all of the above).
6. Sharing rules (which depend on OWD and object existence).
7. Reports and dashboards (which reference fields and objects).

For large releases, split into sequenced deployment packages.
```

**Detection hint:** If the output recommends deploying "everything in one package" without mentioning deployment order or dependency sequencing, the deployment may fail. Search for `deployment order` or `sequence`.

---

## Anti-Pattern 5: Confusing change set validation with deployment

**What the LLM generates:** "Validate the change set in production — once validation passes, the changes are live."

**Why it happens:** LLMs conflate validation and deployment. Validating a change set checks whether the components can be deployed (metadata compatibility, test coverage) but does NOT actually deploy them. The admin must click "Deploy" separately after successful validation.

**Correct pattern:**

```
Change set workflow:
1. Upload: sends the change set from source to target org.
2. Validate: runs a test deployment without making changes live.
   - Checks metadata compatibility.
   - Runs Apex tests if required (75% org-wide coverage for production).
   - Does NOT activate any changes.
3. Deploy: actually applies the changes to the target org.
   - This is a separate step after validation.
   - Validation results expire after 10 days (for Quick Deploy eligibility).
```

**Detection hint:** If the output says validation makes changes "live" or "active," it is confusing validation with deployment. Search for `validate` being described as the final step.

---

## Anti-Pattern 6: Failing to mention post-deployment verification steps

**What the LLM generates:** "Deploy the change set to production. The release is complete."

**Why it happens:** LLMs end at the deployment step and omit post-deployment verification. Production deployment requires confirming that flows are active, permission sets are assigned, page layouts render correctly, integrations still function, and Apex tests pass in the production context.

**Correct pattern:**

```
Post-deployment verification checklist:
1. Confirm all deployed Flows are in Active status.
2. Verify new fields appear on page layouts for affected profiles.
3. Run smoke tests on affected business processes.
4. Check integration endpoints are still connecting.
5. Verify Apex test results in production (Setup → Apex Test Execution).
6. Confirm reports and dashboards referencing new fields load correctly.
7. Notify stakeholders that the release is complete and verified.
```

**Detection hint:** If the output ends at "deploy" without any post-deployment verification steps, the release process is incomplete. Search for `verify`, `smoke test`, or `post-deployment`.
