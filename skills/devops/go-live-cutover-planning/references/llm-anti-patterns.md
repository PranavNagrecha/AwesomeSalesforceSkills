# LLM Anti-Patterns — Go Live Cutover Planning

Common mistakes AI coding assistants make when generating or advising on Salesforce go-live cutover planning.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Suggesting a Full Deploy During the Cutover Window Instead of Quick Deploy

**What the LLM generates:** A cutover runbook that schedules `sf project deploy start --test-level RunLocalTests` during the Saturday deployment window, treating test execution time as part of the cutover.

**Why it happens:** LLMs default to the most common deploy command they have seen in training data. The validation deploy + quick deploy two-step pattern is less represented in tutorials and blog posts than the single-command full deploy.

**Correct pattern:**

```bash
# Step 1: Validation deploy (days before cutover)
sf project deploy start --target-org prod --dry-run --test-level RunLocalTests
# Record the job ID from output

# Step 2: Quick deploy (during cutover window)
sf project deploy quick --job-id 0Af1234567890ABCDE --target-org prod
```

**Detection hint:** Look for `--test-level` flags in commands scheduled during the cutover window. If tests are running during the cutover, the plan is missing the validation deploy pre-stage.

---

## Anti-Pattern 2: Omitting Rollback Triggers and Defining Only the Happy Path

**What the LLM generates:** A cutover runbook with sequential deployment steps but no rollback triggers, rollback actions, or failure criteria for each phase. The plan assumes every step succeeds.

**Why it happens:** LLMs optimize for the positive case when generating procedural documentation. Rollback planning requires reasoning about failure modes for each step, which is a separate cognitive task that LLMs tend to skip unless explicitly prompted.

**Correct pattern:**

```text
Step 5: Activate record-triggered Flows
  Owner: Automation Lead
  Duration: 15 minutes
  Verify: Create test Account, confirm Flow populates Region field
  Rollback trigger: Flow throws unhandled fault on test record
  Rollback action: Deactivate Flow, revert to previous version, continue with degraded functionality
```

**Detection hint:** Check whether every step in the runbook has a "rollback trigger" and "rollback action" field. If any step lacks both, the plan is incomplete.

---

## Anti-Pattern 3: Using Sandbox Test Results as the Go/No-Go Criterion

**What the LLM generates:** A go/no-go checklist that references "all tests passing in UAT sandbox" as the deployment readiness criterion, without requiring a validation deploy against production.

**Why it happens:** LLMs conflate sandbox testing (which validates functional behavior) with production validation deploys (which validate that metadata can be deployed to production with passing tests). They are different things — sandbox test results do not predict production deployment success.

**Correct pattern:**

```text
Go/No-Go Criteria:
  [x] Validation deploy (checkOnly:true) passed against PRODUCTION org
  [x] Apex test coverage: 92% (above 75% threshold)
  [x] Zero test failures in production validation
  [x] UAT sign-off from business sponsor (separate from validation deploy)
```

**Detection hint:** If the go/no-go checklist references sandbox test results but not a production validation deploy, the criterion is insufficient.

---

## Anti-Pattern 4: Treating Code Freeze as a Social Agreement Rather Than a Technical Control

**What the LLM generates:** "Notify all developers that the code freeze begins on Monday. No further changes should be committed." No mention of branch protection, merge restrictions, or automated enforcement.

**Why it happens:** LLMs generate process-oriented advice that mimics project management documents. They do not default to technical enforcement mechanisms because training data contains more process documents than Git configuration examples.

**Correct pattern:**

```text
Code Freeze Enforcement:
  1. Enable branch protection on main: require PR approval, disable direct push
  2. Set CODEOWNERS to require release manager approval for any merge
  3. CI pipeline rejects PRs targeting main after freeze date (label-based gate)
  4. Emergency hotfix process: separate branch with expedited review, requires new validation deploy
```

**Detection hint:** If the code freeze section contains only communication steps (email, Slack message, meeting) without any source control enforcement (branch protection, merge restrictions), the freeze is unenforceable.

---

## Anti-Pattern 5: Generating a Generic Hypercare Plan Without Salesforce-Specific Monitoring

**What the LLM generates:** A hypercare section that says "monitor the system for 2 weeks and address issues as they arise" without specifying what to monitor or how.

**Why it happens:** LLMs produce generic IT operations advice when they lack domain-specific monitoring details. Salesforce-specific monitoring tools (Event Monitoring, debug logs, Apex exception emails, Login History, Setup Audit Trail) are underrepresented in general DevOps training data.

**Correct pattern:**

```text
Hypercare Monitoring Plan (Weeks 1-2):
  Daily checks:
    - Setup Audit Trail: review all changes since go-live for unauthorized modifications
    - Apex Exception Emails: check for unhandled exceptions in new code
    - Login History: confirm user adoption rates match expectations
    - Email Logs: verify automated email delivery (alerts, workflow emails)

  Dashboard monitors:
    - Batch job completion rates (Apex Jobs page)
    - Integration callout success/failure rates (Named Credential logs)
    - Flow error report (Setup > Flow > filter by errors since go-live date)

  Escalation:
    - P1 (system down/data loss): 30-minute response, war room in #go-live-support
    - P2 (feature broken): 4-hour response, assigned to on-call engineer
    - P3 (cosmetic/minor): next business day, logged in backlog
```

**Detection hint:** If the hypercare section does not mention at least three Salesforce-specific monitoring mechanisms (Setup Audit Trail, Apex Exception Emails, Event Monitoring, Flow error reports, Login History), it is too generic.

---

## Anti-Pattern 6: Ignoring Deployment Sequence Dependencies for Destructive Changes

**What the LLM generates:** A single deployment package that includes both constructive changes (new fields, new classes) and destructive changes (field deletions, class removals) in the same manifest, or suggests running destructive changes before constructive changes.

**Why it happens:** LLMs treat deployment as a single atomic operation and do not account for Salesforce's requirement that destructive changes use a separate destructiveChanges.xml manifest. They also do not reason about reference dependencies — deleting a field that is referenced by a Flow or formula causes deployment failure.

**Correct pattern:**

```text
Deployment Sequence:
  1. Deploy constructive changes (package.xml): new fields, updated classes, new Flows
  2. Verify constructive changes landed correctly
  3. Deploy destructive changes (destructiveChanges.xml): removed fields, deleted classes
  4. Verify no broken references remain
```

**Detection hint:** If a deployment plan mentions field or class deletions in the same step as additions, or if destructiveChanges.xml is not mentioned when deletions are in scope, the sequence is wrong.
