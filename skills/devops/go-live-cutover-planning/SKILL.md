---
name: go-live-cutover-planning
description: "Use when planning, sequencing, or executing the final cutover to production for a Salesforce implementation or major release. Covers cutover runbooks, code freeze enforcement, mock deployments, go/no-go decision gates, validation deploy timing, quick deploy windows, hypercare scheduling, and rollback trigger definitions. NOT for deployment mechanics (use devops/post-deployment-validation). NOT for release calendar or versioning strategy (use devops/release-management). NOT for writing smoke tests (use devops/post-deployment-validation)."
category: devops
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Reliability
triggers:
  - "how do I plan a Salesforce go-live cutover weekend"
  - "what should be in a go-live cutover runbook for Salesforce"
  - "when should we do the validation deploy before go-live"
  - "how to define go/no-go criteria for Salesforce production deployment"
  - "what is a code freeze and when should it start before go-live"
  - "how to plan hypercare support after Salesforce go-live"
tags:
  - go-live-cutover-planning
  - cutover-runbook
  - code-freeze
  - go-no-go
  - validation-deploy
  - hypercare
  - mock-deployment
inputs:
  - "Go-live target date and approved deployment window (start/end times)"
  - "List of metadata components, data migrations, and configuration changes in scope"
  - "Stakeholder list with roles (deployment lead, business sponsor, QA lead, support lead)"
  - "Environment inventory (production org, staging sandbox, UAT sandbox)"
  - "Rollback constraints (data-only changes that cannot be undone, destructive changes)"
outputs:
  - "Cutover runbook with sequenced steps, owners, estimated durations, and rollback triggers"
  - "Go/no-go decision checklist with criteria and sign-off slots"
  - "Hypercare plan with escalation paths and monitoring schedule"
  - "Code freeze timeline and enforcement rules"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-06
---

# Go Live Cutover Planning

This skill activates when a practitioner or agent needs to plan and execute the final cutover sequence for moving a Salesforce implementation or major release into production. It covers the end-to-end process from code freeze through validation deploy, go/no-go decision, cutover execution, smoke testing, and hypercare — producing a runbook that teams can follow step-by-step during the deployment window.

---

## Before Starting

Gather this context before working on anything in this domain:

- Identify whether this is a greenfield go-live (new org, first production use) or a brownfield release (existing production org with active users). Greenfield cutovers have simpler rollback options because there is no live user data at risk, while brownfield cutovers must account for in-flight transactions and user disruption.
- Confirm whether the deployment uses change sets, Salesforce CLI (sf project deploy), or unlocked packages. Each has different validation deploy and quick deploy mechanics that directly affect cutover timing.
- Know the Salesforce maintenance windows. Salesforce performs platform maintenance and seasonal releases on specific weekends. Never schedule a cutover during or immediately adjacent to a Salesforce platform release weekend — sandbox preview timing can shift metadata behavior unexpectedly.

---

## Core Concepts

### Code Freeze

A code freeze is the point at which all metadata changes are locked in source control and no further commits are permitted until after go-live. The freeze ensures that the validation deploy tests exactly the same metadata that will be quick-deployed to production. Any commit after the validation deploy invalidates the validated deploy ID, requiring a full re-validation. A typical code freeze starts 3-7 days before the go-live date, depending on org complexity and the number of contributing developers.

### Validation Deploy and Quick Deploy Window

A validation deploy (checkOnly:true) runs the full deployment pipeline — metadata parsing, Apex compilation, and test execution — without committing changes to the org. Once a validation deploy succeeds, Salesforce caches the validated deploy ID for exactly 10 days. During this window, you can execute a quick deploy that skips test re-execution and commits the metadata in minutes rather than hours. The cutover runbook must account for both the validation deploy duration (which can take 1-6 hours depending on test volume) and the quick deploy execution time (typically 5-30 minutes).

### Go/No-Go Decision Gate

The go/no-go checkpoint is a formal meeting held after the validation deploy succeeds but before the cutover execution begins. The decision requires sign-off from the deployment lead, business sponsor, and QA lead. Criteria include: validation deploy passed with 75%+ Apex test coverage, UAT sign-off is complete, data migration dry-run succeeded, rollback plan is documented, and support team is staffed for hypercare. If any criterion fails, the go-live is postponed to the next approved window.

### Hypercare Period

Hypercare is the defined support period immediately following go-live, typically lasting 1-2 weeks. During hypercare, the deployment team maintains heightened monitoring, accelerated response times, and direct escalation paths. The hypercare plan defines who is on-call, what monitoring dashboards to watch, how to triage user-reported issues, and when the org transitions from hypercare to steady-state support.

---

## Common Patterns

### Pattern 1: Weekend Cutover with Validation Deploy Pre-staged

**When to use:** Most production deployments where the org has active weekday users and the deployment window must minimize disruption.

**How it works:**
1. Code freeze begins Monday of cutover week (T-5 days).
2. Validation deploy runs Tuesday-Wednesday against production (checkOnly:true, RunLocalTests).
3. Go/no-go meeting held Thursday with all stakeholders.
4. Quick deploy executes Saturday morning during the approved maintenance window.
5. Smoke tests and business validation run Saturday afternoon.
6. Hypercare begins Monday with the deployment team on standby.

**Why not the alternative:** Running the full deploy (not quick deploy) during the cutover window adds hours of test execution time, increasing the risk of running past the maintenance window and requiring a rollback under pressure.

### Pattern 2: Mock Deployment Rehearsal

**When to use:** Large or high-risk deployments where the team has not deployed to production before, or the deployment includes destructive changes, data migrations, or complex post-deployment configuration steps.

**How it works:**
1. Create a Full sandbox that mirrors production (or use the most recent Full sandbox refresh).
2. Execute the entire cutover runbook against the sandbox exactly as planned for production — same sequence, same people, same timing.
3. Record actual durations for each step and compare against estimates.
4. Identify steps that took longer than expected, failed, or required improvisation.
5. Update the runbook with corrected durations and additional contingency steps.
6. Repeat if the mock deployment revealed blocking issues.

**Why not the alternative:** Skipping the mock deployment means the first time the team executes the runbook is in production, where surprises cause delays, missed windows, and emergency rollbacks.

### Pattern 3: Phased Cutover for Large Implementations

**When to use:** Greenfield implementations with multiple workstreams (Sales Cloud, Service Cloud, data migration, integrations) where deploying everything in one window is too risky.

**How it works:**
1. Sequence workstreams by dependency: data model and security first, then automation, then UI, then integrations.
2. Each phase has its own validation deploy, go/no-go, and smoke test checklist.
3. Phases deploy in order within the same cutover window, with explicit hold points between phases.
4. If a phase fails, subsequent phases are aborted and the rollback plan for that phase executes.

**Why not the alternative:** A single monolithic deployment for a large implementation creates a binary pass/fail outcome where one failing component forces a complete rollback of all work.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Standard release with <50 components | Weekend cutover with pre-staged validation deploy | Quick deploy minimizes window duration; low risk does not justify mock deployment cost |
| First-ever production deployment or >200 components | Mock deployment rehearsal + weekend cutover | Rehearsal catches timing and sequencing issues before they affect production |
| Multiple independent workstreams going live together | Phased cutover with hold points | Isolates blast radius so one failure does not force rollback of unrelated work |
| Deployment includes destructive changes (field deletions, object removals) | Mock deployment mandatory; extended rollback plan | Destructive changes cannot be undone via metadata rollback — data loss is permanent |
| Go-live date falls within 2 weeks of Salesforce seasonal release | Reschedule or add extra validation after platform upgrade | Salesforce platform changes can alter metadata behavior, invalidating pre-go-live testing |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner building a cutover plan:

1. **Inventory the deployment scope** — List every metadata component, data migration job, manual configuration step, and integration activation. Group items by dependency order. Flag destructive changes and data-only changes that cannot be rolled back via metadata redeployment.
2. **Define the code freeze date** — Set the freeze 3-7 days before go-live. Communicate the freeze to all developers and enforce it via branch protection rules in source control. No commits after this date unless approved as a hotfix through the emergency change process.
3. **Schedule the validation deploy** — Run the validation deploy (checkOnly:true) against production 2-5 days before the cutover window. Use RunLocalTests to match production test execution. Record the validated deploy ID and its 10-day expiration date.
4. **Prepare the go/no-go checklist** — Document every criterion that must be true before the cutover proceeds: validation deploy passed, UAT signed off, data migration dry-run complete, rollback plan reviewed, hypercare team confirmed, communication sent to end users.
5. **Build the cutover runbook** — Sequence every step with owner, estimated duration, verification criteria, and rollback action. Include pre-cutover steps (disable integrations, notify users), deployment steps (quick deploy, activate flows, run post-deploy scripts), and post-cutover steps (smoke tests, re-enable integrations, confirm with business).
6. **Execute mock deployment** — For high-risk or first-time deployments, run the complete runbook against a Full sandbox. Update durations and add contingency steps based on results.
7. **Execute cutover and enter hypercare** — Run the runbook during the approved window. After smoke tests pass and business confirms, declare go-live complete and begin the hypercare monitoring period.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Cutover runbook exists with sequenced steps, owners, durations, and rollback triggers for each step
- [ ] Code freeze date is defined and communicated to all contributors
- [ ] Validation deploy has been run (or is scheduled) with the validated deploy ID recorded
- [ ] Go/no-go checklist documents every required criterion with assigned approvers
- [ ] Rollback plan covers both metadata rollback (redeploy previous version) and data rollback (restore from backup or manual correction)
- [ ] Hypercare plan defines on-call schedule, escalation paths, and monitoring dashboards for the first 2 weeks
- [ ] Mock deployment was completed (for high-risk or first-time deployments) and runbook updated with actual timings
- [ ] Cutover window does not conflict with Salesforce seasonal release or scheduled maintenance

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Validation deploy ID expires silently after 10 days** — There is no notification when the validated deploy ID expires. If the cutover window shifts past the 10-day mark, the quick deploy will fail with a cryptic error and you must re-run the full validation deploy, adding hours to the cutover.
2. **Flow version activation is not atomic with metadata deploy** — Deploying a Flow deploys the latest version but does not automatically activate it if a previous version was active. The cutover runbook must include explicit Flow activation steps and verification that the correct version is running.
3. **Destructive changes require a separate deployment manifest** — Deleting metadata (fields, classes, objects) requires a destructiveChanges.xml file deployed separately from the constructive changes. If the destructive deploy runs before dependent metadata is updated, the deployment fails with missing reference errors. Always sequence constructive changes first, destructive changes last.
4. **Data migration records created before Flow activation may not trigger automation** — If you load data before activating record-triggered Flows, those records will not fire the Flows. Sequence matters: activate automation first, then load data (or plan for a backfill process).

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Cutover runbook | Step-by-step execution plan with owners, durations, verification gates, and rollback instructions for each step |
| Go/no-go checklist | Decision document listing every criterion required to proceed, with sign-off fields for each approver |
| Hypercare plan | Post-go-live support schedule defining on-call rotation, monitoring dashboards, escalation matrix, and transition-to-steady-state criteria |
| Code freeze communication | Notification to all contributors with freeze start date, exception process, and expected thaw date |

---

## Related Skills

- devops/post-deployment-validation — Use after the cutover quick deploy executes to verify metadata landed correctly and run smoke tests
- devops/release-management — Use for the broader release planning lifecycle including version numbering and release notes; go-live cutover is the execution phase of the release plan
- devops/rollback-and-hotfix-strategy — Use to design the detailed rollback procedures referenced in the cutover runbook
- devops/pre-deployment-checklist — Use to validate readiness before the cutover window opens
- admin/change-management-and-training — Use for end-user communication, training, and adoption planning that surrounds the go-live event
