# LLM Anti-Patterns — Copado Essentials

Common mistakes AI coding assistants make when generating or advising on Copado Essentials.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Recommending SFDX CLI Commands for Copado Promotions

**What the LLM generates:** Instructions like "run `sf project deploy start --source-dir force-app` to push your user story changes to UAT" when the user is operating inside a Copado Essentials pipeline.

**Why it happens:** LLMs are heavily trained on Salesforce CLI documentation and SFDX patterns, which represent the most common developer workflow in public training data. When a user asks "how do I deploy my changes to UAT," LLMs default to CLI commands unless explicitly grounded in the Copado context. Copado Essentials uses the Metadata API indirectly through its own managed package deployment engine — direct CLI deployments to a Copado-managed org create pipeline state inconsistencies that are not visible in the Copado UI.

**Correct pattern:**

```text
To promote a user story to UAT in Copado Essentials:
1. Open the User Story record in Salesforce
2. Verify User Story Task records list all changed components
3. Click "Promote" on the user story (Work Items mode)
   OR wait for Copado to create a PR and merge it (Pull Requests mode)
4. Monitor the Deployment record for status
Do NOT use sf/sfdx CLI deploy commands against Copado-managed orgs.
```

**Detection hint:** Look for `sf project deploy`, `sfdx force:source:deploy`, `sf deploy metadata`, or `sfdx force:mdapi:deploy` in any response about Copado pipeline promotions.

---

## Anti-Pattern 2: Advising Manual Git Branch Merges to Bypass Copado Pipeline

**What the LLM generates:** "You can speed things up by running `git merge feature/US-1042 develop` locally and pushing to origin. That will get your changes into the dev sandbox without waiting for Copado."

**Why it happens:** LLMs treat Copado as a thin wrapper over standard Git operations and assume that because Copado uses Git underneath, any valid Git operation is equivalent to a Copado pipeline action. This is incorrect: Copado maintains pipeline state in Salesforce custom objects (Deployment records, User Story status fields) that are updated only when promotions occur through Copado's own processes.

**Correct pattern:**

```text
Do not merge feature branches to environment branches outside Copado.
If an emergency bypass is necessary:
1. Complete the manual merge/deploy as required
2. Open the User Story record in Copado
3. Mark the user story status as "Cancelled" to reflect it was deployed
   outside the pipeline
4. Document the bypass in the user story record comments
5. Verify no subsequent Copado promotions depend on this story's pipeline
   state before resuming normal operations
```

**Detection hint:** Look for `git merge`, `git push origin develop`, `git push origin main`, or `git rebase` commands in responses about Copado promotion workflows. Any suggestion to merge to environment branches without going through Copado is this anti-pattern.

---

## Anti-Pattern 3: Treating Copado Essentials and Copado Enterprise as Interchangeable

**What the LLM generates:** Instructions referencing Copado features that exist only in the paid Enterprise tier — such as automated test execution, compliance hub, quality gates, sprint management, or Selenium testing integration — when the user is running Copado Essentials (the free tier).

**Why it happens:** Public documentation and blog content frequently discuss Copado's full product suite without clearly distinguishing Essentials from Enterprise. LLMs blend these sources and generate advice referencing Enterprise features as if they were universally available.

**Correct pattern:**

```text
Copado Essentials (free tier) includes:
- User Stories and User Story Tasks
- Pipeline with stages and branch management
- Work Items deployment mode
- Deployments with Pull Requests mode
- Conflict detection and resolution (in Work Items mode)
- Basic deployment record history

Not available in Essentials (Enterprise only):
- Quality gates and automated test execution
- Compliance Hub and audit reporting
- Sprint/backlog management
- Selenium and automated testing integration
- Advanced AI features

Verify the user's Copado tier before advising on any feature beyond the
Essentials list above.
```

**Detection hint:** Look for terms like "quality gate," "compliance hub," "automated regression," "sprint board," "Copado Testing," or "Selenium" in responses about Copado Essentials.

---

## Anti-Pattern 4: Citing the Wrong Field as the Source of the Feature Branch Name

**What the LLM generates:** "Copado names the feature branch after the User Story record name (the Name field)" or "The branch is created using the user story's Salesforce record Id."

**Why it happens:** Salesforce custom objects conventionally use the `Name` field as the primary identifier, and Salesforce record Ids are the unique system identifiers. LLMs default to these fields when asked how Copado derives the branch name because the concept of a secondary "reference" field acting as the branch naming key is not a standard Salesforce pattern.

**Correct pattern:**

```text
Copado Essentials derives the feature branch name from the User Story Reference
field (a separate field from the record Name, often an autonumber field).
Branch naming pattern: feature/{user-story-reference-value}

Example:
  User Story Name: "Account Page Layout Updates"
  User Story Reference: "US-2024-089"
  Branch created: feature/US-2024-089

The reference field must:
- Be populated before clicking "Create Feature Branch"
- Contain only Git-safe characters (alphanumeric, hyphens, underscores)
- Not contain spaces, slashes, or special characters
```

**Detection hint:** Look for responses that say the branch is named after the "Name field," "record name," "record title," or "Salesforce Id."

---

## Anti-Pattern 5: Advising Deployment Mode Changes Without Warning About In-Flight Stories

**What the LLM generates:** "To switch from Work Items to Pull Requests mode, just go to the pipeline settings and change the deployment mode field. Your existing promotions will adapt automatically."

**Why it happens:** UI-driven configuration changes in Salesforce typically take effect immediately and apply to all subsequent operations, leading LLMs to assume the same applies to Copado's deployment mode toggle. The LLM does not model the state machine that Copado maintains per user story promotion.

**Correct pattern:**

```text
Before changing the Copado Essentials pipeline deployment mode:
1. Audit the pipeline stage view for any user story in "Promoting,"
   "Pending Approval," or "Pending PR" status
2. For each in-flight story, either:
   a. Complete the promotion under the current mode, OR
   b. Cancel the promotion and reset the user story to "In Progress"
3. Confirm zero in-flight promotions remain
4. Change the deployment mode on the pipeline record
5. Validate the mode change with a new test user story before
   reopening promotions to the team
6. Communicate the mode change — the UI and approval workflow change completely
```

**Detection hint:** Look for responses that say mode changes are "automatic," "backward-compatible," or "apply to existing promotions." Any suggestion that in-flight stories will "adapt" or "migrate automatically" is this anti-pattern.
