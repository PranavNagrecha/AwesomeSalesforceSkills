# LLM Anti-Patterns — Flow Deployment And Packaging

Common mistakes AI coding assistants make when generating or advising on Flow deployment and packaging. These patterns help the consuming agent self-check its own output.

---

## Anti-Pattern 1: Recommending direct deploy to production without validation

**What the LLM generates:**

```bash
sf project deploy start \
  --source-dir force-app/main/default/flows/Order_Approval.flow-meta.xml \
  --target-org prod \
  --test-level RunLocalTests
```

…as the recommended production deploy command, with no mention of validate-then-quick-deploy.

**Why it happens:** the validate/quick split is two commands, slightly more cognitive load, and not the "first hit" in a casual SF documentation read. LLMs default to the simplest single command that satisfies "deploy to prod".

**Correct pattern:**

```bash
# Step 1 — Validate (hours before cutover, non-blocking).
sf project deploy validate \
  --source-dir force-app/main/default/flows/Order_Approval.flow-meta.xml \
  --target-org prod \
  --test-level RunLocalTests \
  --wait 90

# Step 2 — Quick deploy in the cutover window (within 10 days of validation).
sf project deploy quick \
  --job-id <validationId> \
  --target-org prod \
  --wait 30
```

**Detection hint:** any production deploy guidance that uses `sf project deploy start` directly (without a preceding `validate` step) is suspect. Search for `deploy start.*--target-org prod` and flag.

---

## Anti-Pattern 2: Deploying parent flow without bundling its subflow

**What the LLM generates:**

```bash
sf project deploy start \
  --source-dir force-app/main/default/flows/Lead_Routing.flow-meta.xml \
  --target-org uat
```

…when `Lead_Routing` calls a brand-new subflow `Sub_Score_Lead` not yet in UAT.

**Why it happens:** LLMs treat each file as independent. They don't parse the flow XML to discover `<actionType>flow</actionType>` references to subflows.

**Correct pattern:**

```bash
sf project deploy start \
  --source-dir force-app/main/default/flows/Lead_Routing.flow-meta.xml \
  --source-dir force-app/main/default/flows/Sub_Score_Lead.flow-meta.xml \
  --source-dir force-app/main/default/classes/LeadScorer.cls \
  --source-dir force-app/main/default/classes/LeadScorer.cls-meta.xml \
  --target-org uat
```

…with all dependencies in one bundle.

**Detection hint:** any flow deploy command with a single `--source-dir` flag and no manifest (`--manifest`) — flag for review of dependency completeness. Grep the flow XML for `<actionType>flow</actionType>`, `<actionType>apex</actionType>`, `<object>Custom_*</object>`, and `<field>Custom_*</field>` references.

---

## Anti-Pattern 3: Suggesting in-org Flow Builder edit instead of source-controlled deploy

**What the LLM generates:** "To update the flow in production, open Flow Builder in the prod org, click Edit on the active version, make your change, save as new version, and activate."

**Why it happens:** LLMs surface the user-facing UI workflow because that's what most Salesforce Help pages describe. They under-weight the source-control discipline that real DevOps teams operate under.

**Correct pattern:** "Edit the flow in source control (`force-app/main/default/flows/<FlowName>.flow-meta.xml`), commit to the feature branch, open a PR, get reviewed, merge to main, then run validate-then-quick-deploy. The Flow Builder UI in production is read-only outside emergency hotfixes — and emergency hotfixes must be back-ported to source within 24 hours."

**Detection hint:** any guidance that says "open Flow Builder in production" or "click Edit in the org" — flag immediately. Production flows should not be edited via UI in a source-controlled org.

---

## Anti-Pattern 4: Omitting FlowAccessPermission delivery from the deploy plan

**What the LLM generates:** A complete deploy plan covering the flow XML, dependent subflows, custom fields, and Apex — with no mention of FlowAccessPermission on Profiles / PermissionSets.

**Why it happens:** FlowAccessPermission lives inside Profile / PermissionSet metadata, which feels like a separate concern from "the flow itself". LLMs treat it as out-of-scope.

**Correct pattern:** every deploy plan that introduces a new flow OR changes an existing flow's run-permission requirements must include the relevant Profile / PermissionSet metadata. Smoke-test by impersonating a non-admin user post-deploy.

```bash
# Add to the deploy bundle.
--source-dir force-app/main/default/permissionsets/Sales_Ops_User.permissionset-meta.xml
```

**Detection hint:** if a deploy plan introduces a flow but doesn't touch any Profile or PermissionSet file, ask: "who is allowed to run this flow, and is that permission set already in the target org?" If unclear, flag.

---

## Anti-Pattern 5: Suggesting Change Sets when Unlocked Package is the right long-term answer

**What the LLM generates:** "To migrate this flow library across your 8 internal orgs, build a Change Set in the source sandbox and upload it to each target org."

**Why it happens:** Change Sets are the most familiar Salesforce migration concept; LLMs default to them. Unlocked Packages have a steeper setup curve and don't surface as readily in casual queries.

**Correct pattern:** "For a flow library shipped to 3+ orgs, the right shape is an Unlocked Package (2GP). One-time setup: define the package in `sfdx-project.json`, build versions with `sf package version create`, install in each target with `sf package install`. Versioned, upgradable in place, single source of truth. Change Sets are appropriate only for one-off single-org migrations."

**Detection hint:** any guidance recommending Change Sets for a multi-org distribution scenario — flag and propose Unlocked Package alternative.

---

## Anti-Pattern 6: Recommending `<status>Active</status>` for a high-risk cutover

**What the LLM generates:** "Set `<status>Active</status>` in the flow XML and run `sf project deploy start`. The new version will be live immediately."

**Why it happens:** "Active" sounds like the natural end state, and LLMs don't always distinguish between "ready to run" and "running right now in front of users".

**Correct pattern:** for low-risk changes (label tweaks, internal admin flows), Active is fine. For high-risk (revenue-critical, customer-facing, complex), deploy as `Draft` and activate manually in the maintenance window via Tooling API PATCH on `FlowDefinition.ActiveVersionNumber`. This gives a smoke-test window between deploy and live traffic.

**Detection hint:** check the change description. If it mentions "high-risk", "revenue-critical", "customer-facing", "complex", "first version of new automation" — recommend Draft + manual activate, not direct Active.

---

## Anti-Pattern 7: Using `--ignore-errors` to "make the deploy go through"

**What the LLM generates:** "If the deploy fails on a non-critical component, add `--ignore-errors` to skip it and proceed."

**Why it happens:** LLMs learn from forum posts where exhausted developers worked around errors instead of fixing them. The flag exists, so LLMs assume it's appropriate.

**Correct pattern:** never use `--ignore-errors` against production. Partial deploys leave the org in a half-migrated state — parent flow active while dependent subflow failed. Hard to diagnose, harder to roll back. Fix the error or surgically exclude the failing component from the deploy bundle.

**Detection hint:** any command with `--ignore-errors` against a non-scratch org — flag immediately as a deploy-safety violation.

---

## Anti-Pattern 8: Re-running `validate` instead of using cached `quick`

**What the LLM generates:** "If the first deploy attempt fails or times out, run `sf project deploy validate` again."

**Why it happens:** LLMs treat each invocation as fresh. They don't track that a successful validation has already been cached server-side and is reusable for 10 days.

**Correct pattern:** if validation succeeded but quick-deploy timed out, re-run `sf project deploy quick --job-id <originalValidationId>` against the same validation. Don't re-validate (slow, wastes test cycles, restarts the 10-day clock from the wrong point).

**Detection hint:** in deploy retry guidance, look for repeated `validate` calls. If the previous validate succeeded, the right retry is `quick`, not another `validate`.

---

## Anti-Pattern 9: Treating `<status>Obsolete</status>` as a no-op cleanup

**What the LLM generates:** "Deploy the old flow with `<status>Obsolete</status>` to mark it as deprecated."

**Why it happens:** "Obsolete" sounds like a passive label, not an active state-change.

**Correct pattern:** `<status>Obsolete</status>` actively *deactivates* the currently active version. After this deploy, the flow stops running entirely (no active version). Use only when you genuinely want the flow off. To replace with a new version, deploy the new one as `Active` (which auto-deactivates the old).

**Detection hint:** any guidance to deploy `<status>Obsolete</status>` — confirm intent. Is this a "turn it off" operation, or accidental?

---

## Anti-Pattern 10: Forgetting to query / document the prior active version before cutover

**What the LLM generates:** A complete deploy plan ending with "deploy and verify the new version is active." No mention of capturing the prior `VersionNumber`.

**Why it happens:** rollback is implicit / future-tense, and LLMs optimize for the happy path.

**Correct pattern:** before any production flow deploy, query the current active version:

```bash
sf data query \
  --query "SELECT Id, ActiveVersion.VersionNumber FROM FlowDefinition WHERE DeveloperName = '<FlowName>'" \
  --use-tooling-api \
  --target-org prod
```

Document the result in the deploy ticket. Include the rollback Tooling API command alongside.

**Detection hint:** any deploy plan that doesn't include a "current state captured" step or a "rollback steps" section — flag and add.

---

## Anti-Pattern 11: Assuming Flow Tests gate the deploy

**What the LLM generates:** "Add Flow Tests in Flow Builder for `Lead_Routing`, then deploy with `--test-level RunLocalTests` — the Flow Tests will gate the deploy."

**Why it happens:** "Flow Tests" sounds analogous to Apex tests, and `RunLocalTests` sounds inclusive.

**Correct pattern:** Flow Tests are a Flow Builder–internal authoring aid. They do NOT run during deploy and do NOT gate the deploy. To gate a deploy on flow logic, write Apex tests that instantiate `Flow.Interview.<FlowName>`. Apex tests run during `RunLocalTests`.

**Detection hint:** any guidance suggesting Flow Tests will gate a deploy — flag and replace with Apex test guidance.

---

## Anti-Pattern 12: Suggesting "delete and re-create" for rollback

**What the LLM generates:** "To roll back the bad flow version, delete it via Flow Builder and re-deploy the prior XML."

**Why it happens:** LLMs default to "fix forward" workflows from non-Salesforce contexts (Git revert, container redeploy).

**Correct pattern:** rollback is a one-step metadata operation — re-activate the prior version via Tooling API PATCH on `FlowDefinition.ActiveVersionNumber`. The prior version still exists in the org as Obsolete; you don't need to redeploy XML. This is the fastest possible recovery path (sub-minute).

```bash
sf data update record \
  --sobject FlowDefinition \
  --record-id <flowDefId> \
  --values "ActiveVersionNumber=<priorVersion>" \
  --use-tooling-api \
  --target-org prod
```

**Detection hint:** any rollback guidance that involves redeploying XML — replace with the Tooling API re-activation pattern.

---

## Anti-Pattern 13: Hard-coding API version in `sfdx-project.json` to a future release

**What the LLM generates:** `"sourceApiVersion": "65.0"` when the target prod org is on Spring '25 (API 63.0).

**Why it happens:** LLMs default to the highest-known API version, assuming "newest is best".

**Correct pattern:** `sourceApiVersion` should match the *lowest* API version of any target org you deploy to. For most teams, that's the production org. Bump the source only after the org has been upgraded.

**Detection hint:** check that `sourceApiVersion` is ≤ the prod org's current release API. If higher, flag.

---

## Anti-Pattern 14: Conflating "deploy" with "activate" in narrative answers

**What the LLM generates:** "After you deploy the flow, it will start running automatically." (with no qualification).

**Why it happens:** in casual usage "deployed" implies "live". LLMs don't always distinguish the two.

**Correct pattern:** "After you deploy with `<status>Active</status>`, the flow starts running. After you deploy with `<status>Draft</status>`, the flow exists in the org but doesn't run until you activate it (via Flow Builder UI or Tooling API PATCH)." Always qualify the activation state.

**Detection hint:** any narrative that says "deploys and runs" without specifying the `<status>` value — flag and clarify.

---

## Anti-Pattern 15: Ignoring obsolete-version cleanup until the 50-version limit hits

**What the LLM generates:** No mention of obsolete-version hygiene anywhere in deployment guidance.

**Why it happens:** version cleanup is a maintenance task, not a deploy task; LLMs scope their answers narrowly to the immediate request.

**Correct pattern:** include a "version hygiene" check in the standard deploy runbook. Quarterly: query `Flow WHERE DeveloperName = '<X>' AND Status = 'Obsolete'`, count, delete versions older than N (keep last 5 for rollback safety). Salesforce hard-limits each FlowDefinition to 50 versions — without cleanup, high-iteration flows hit this limit and start failing deploys.

**Detection hint:** any deploy plan for a flow that has been iterated > 30 times — recommend a cleanup pass before further deploys.
