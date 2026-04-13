# LLM Anti-Patterns — Deployment Risk Assessment

Common mistakes AI coding assistants make when generating or advising on Deployment Risk Assessment.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Suggesting a Native Rollback or Undo Deployment Button in Setup

**What the LLM generates:** Instructions to navigate to Setup > Deployment Status, find the completed deployment, and click "Undo" or "Rollback" to revert it. Some LLMs describe a rollback option in the Deployment Status page or suggest that Salesforce provides a one-click revert similar to database rollback semantics.

**Why it happens:** LLMs trained on general DevOps content learn that deployment platforms often provide rollback buttons (Heroku, AWS CodeDeploy, Azure DevOps). The model transfers this pattern to Salesforce without grounding in Salesforce-specific platform behavior. The term "rollback" is used frequently in Salesforce contexts but always refers to re-deploying prior state, never a platform-native undo.

**Correct pattern:**

```
No native rollback or undo mechanism exists in Salesforce Setup or in the Deployment Status page.

Rollback is always one of:
1. Re-deploy the prior metadata from a pre-retrieve backup (org-based deployments)
2. Install the prior package version (unlocked or managed package deployments)
3. Manually reconstruct and deploy a reverse change set (Change Set deployments)
4. Run a destructive change deployment to remove added components

The rollback artifact (backup, prior version number, or destructive change XML) must exist
before the deployment window opens. It cannot be generated from the platform after deployment.
```

**Detection hint:** Look for phrases like "click Rollback in Deployment Status", "use the undo option", "Salesforce provides a rollback button", or any instruction that implies a single platform UI action reverses a completed deployment.

---

## Anti-Pattern 2: Classifying All Changes as the Same Risk Level

**What the LLM generates:** A risk assessment that assigns the same risk level (often "medium") to all components in a release, or a generic statement like "all deployments carry some risk" without differentiating metadata types.

**Why it happens:** Without domain grounding, LLMs default to balanced, hedged risk language to avoid appearing reckless. The model lacks the Salesforce-specific knowledge that PermissionSets and Flows carry categorically different risk profiles than page layouts and list views.

**Correct pattern:**

```
Risk classification must be component-specific. The following metadata types are always
classified HIGH by default in the absence of specific mitigating evidence:

HIGH by default: PermissionSet, Profile, SharingRule, ConnectedApp, AuthProvider,
ExternalCredential, Flow (on high-volume objects), ApexTrigger (on high-volume objects)

MEDIUM by default: Flow (low-volume objects), ApprovalProcess, CustomMetadata (runtime-affecting),
NamedCredential, ExternalDataSource

LOW by default: Layout, ListView, Report, Dashboard, EmailTemplate, CustomField
(with no automation dependency)

A release that mixes HIGH and LOW components should be classified HIGH overall unless
the HIGH components are gated behind a feature flag or deployed separately.
```

**Detection hint:** Look for a single risk level applied to all components in a diverse release, or language like "this is a medium-risk deployment" applied to a release that includes PermissionSets or Flows without component-level justification.

---

## Anti-Pattern 3: Writing Vague, Subjective Rollback Trigger Conditions

**What the LLM generates:** Rollback trigger conditions like "if users report issues", "if something seems broken", "if the deployment causes problems", or "if the error rate is unacceptable". These conditions require subjective judgment to apply during an incident.

**Why it happens:** LLMs generating release documentation default to natural language descriptions of failure without translating them into observable, measurable thresholds. The model has not learned that subjective trigger conditions fail in practice because teams under pressure interpret them differently.

**Correct pattern:**

```
Rollback trigger conditions must be observable and measurable. Examples:

GOOD:
- Apex exception count on OpportunityTrigger exceeds 50 in any 5-minute window
  (check: Setup > Apex Exception Email or Event Monitoring)
- Integration API response time for the billing endpoint exceeds 10 seconds
  for more than 3 consecutive calls in the monitoring dashboard
- Case creation success rate drops below 95% in the 30 minutes post-deployment
  (baseline: current 7-day average from reports)

BAD:
- Roll back if users report issues
- Roll back if error rate is unacceptable
- Roll back if the release causes problems
```

**Detection hint:** Look for rollback conditions containing words like "issues", "problems", "errors", "seems", "appears", or "unacceptable" without a specific measurable threshold and a named data source to observe it.

---

## Anti-Pattern 4: Recommending Sandbox as the Rollback Source

**What the LLM generates:** A rollback plan that instructs the team to retrieve the affected components from a Full sandbox or developer sandbox and re-deploy them to production if rollback is needed.

**Why it happens:** LLMs associate sandboxes with "safe copies of production" based on how they are marketed and described. The model does not account for the fact that sandbox state diverges from production every time a production change is made outside the sandbox track.

**Correct pattern:**

```
The rollback artifact for org-based deployments must be a production retrieve
taken immediately before the deployment window opens — not a sandbox retrieve.

Sandbox state diverges from production:
- Every time Setup changes are made directly in production
- When sandbox refresh cycles are not aligned with the deployment track
- When multiple feature teams use separate sandbox environments

A rollback plan that reads "retrieve from Full sandbox if needed" is unreliable.

Correct rollback source for org-based deploys:
sf project retrieve start \
  --metadata "PermissionSet:MyPS,Flow:MyFlow" \
  --target-org production \
  --output-dir .rollback-backup/$(date +%Y-%m-%d-%H%M)

This command must run BEFORE the deployment, not during rollback execution.
```

**Detection hint:** Look for rollback instructions that reference a sandbox as the source of the prior metadata state, or any plan that does not include a production retrieve step with a timestamp before the deployment window.

---

## Anti-Pattern 5: Assigning Rollback Authority to a Role or Team Rather Than a Named Individual

**What the LLM generates:** A rollback plan that assigns decision authority to "the release team", "the project manager", "the DevOps team", or "the release manager role" without naming a specific person and a named alternate.

**Why it happens:** LLMs default to organizational role language because it appears in most ITSM and change management templates. The model does not recognize that role-based authority fails during incidents when the role-holder is unavailable and no alternate is pre-named.

**Correct pattern:**

```
Rollback decision authority must be named as a specific individual, not a role.

GOOD:
- Rollback authority: Jane Smith (jane.smith@example.com, mobile: +1-555-0101)
- Alternate: Carlos Rivera (carlos.rivera@example.com, mobile: +1-555-0102)
- If neither is reachable: escalate to VP Engineering per on-call page

BAD:
- Rollback authority: Release Manager
- Rollback authority: The DevOps team
- Rollback authority: Project lead

The alternate must be confirmed available for the release window before
the window opens — not identified for the first time during an incident.
```

**Detection hint:** Look for rollback authority described using role titles, team names, or department references without a specific person's name and contact information. Also flag any plan that names an authority without also naming an alternate.

---

## Anti-Pattern 6: Omitting Data Side Effects from the Rollback Plan for Packaged Releases

**What the LLM generates:** A rollback plan for an unlocked package release that says "rollback is simply reinstalling the prior package version" without addressing data changes made by automation in the new version while it was active in production.

**Why it happens:** LLMs understand package version rollback as a code and configuration operation and correctly identify it as the fastest rollback path. The model does not reason about the data side effects created by flows, triggers, or automation that ran on the new version before rollback.

**Correct pattern:**

```
Unlocked package rollback restores metadata and configuration to the prior version.
It does NOT revert:
- Records created or modified by automation in the new package version
- Field values populated by new formula logic or default values
- Related records created by new process automation

For any release where new automation runs on record creation or modification,
the rollback plan must include:

1. Identify which records were affected while the new version was active
   (use Created Date or LastModifiedDate relative to deployment timestamp)
2. Determine whether data cleanup is required (manual or via data loader)
3. Document the data cleanup procedure alongside the package reinstall steps
4. Estimate data cleanup time separately from package reinstall time

The rollback window is: package reinstall time + data cleanup time, not just package reinstall time.
```

**Detection hint:** Look for packaged rollback plans that describe only the `sf package install` command without any mention of data side effects, data cleanup, or record state assessment.
