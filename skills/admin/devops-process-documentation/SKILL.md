---
name: devops-process-documentation
description: "Use when authoring, reviewing, or maintaining Salesforce DevOps operational documents — runbooks, environment matrices, deployment guides, and post-deploy validation checklists. Triggers: 'runbook', 'environment matrix', 'deployment guide', 'pre-deploy checklist', 'post-deploy validation', 'how do I document a deployment', 'rollback procedure template'. NOT for release planning, project scheduling, CI/CD pipeline code, or change advisory board process governance."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Reliability
tags:
  - runbook
  - deployment-guide
  - environment-matrix
  - devops-documentation
  - operational-excellence
inputs:
  - "Org environment inventory: names, types (Developer, Partial, Full), purposes, and branch alignments"
  - "Deployment scope: metadata types, manual steps, Named Credential entries required"
  - "Rollback options: previous metadata version, feature toggle, or hotfix path"
  - "Data policy per environment: refresh cadence, anonymization rules, production data restrictions"
outputs:
  - "Environment matrix: structured table of all environments with type, purpose, branch, refresh cadence, and data policy"
  - "Deployment runbook: numbered execution checklist for a single deployment event covering pre-deploy, deploy, post-deploy, and rollback steps"
  - "Deployment guide: standing reference document covering promotion path, validation strategy, and Named Credential re-entry requirements"
triggers:
  - "how do I write a Salesforce deployment runbook"
  - "need an environment matrix for our sandbox topology"
  - "create a pre-deploy checklist for production deployment"
  - "what goes in a post-deploy validation checklist"
  - "how to document Named Credential re-entry steps after deploy"
  - "deployment guide template for Salesforce release process"
  - "rollback procedure template for Salesforce deployment"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-13
---

# DevOps Process Documentation

Use this skill when you need to author or review Salesforce DevOps operational documents: runbooks that guide a single deployment event, environment matrices that map your sandbox topology, and deployment guides that describe standing process. Activate when a practitioner says they need a runbook, an environment matrix, documentation for a deployment, or a pre/post-deploy checklist.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Environment inventory**: collect org names, org types (Developer Edition, Developer Pro, Partial Copy, Full Copy, Production), their purpose in the promotion path, and which Git branches they align to in DevOps Center or a CLI-based workflow.
- **Most common wrong assumption**: practitioners conflate a runbook with a release plan. A runbook is a single-deployment-event execution checklist. A release plan is a project artifact covering scope, approvals, scheduling, and stakeholder communication. They are different documents with different owners and different lifecycles.
- **Platform constraints to track**: Salesforce has no native runbook or documentation feature. All runbook content is practitioner-authored outside the platform. Named Credentials, External Credentials, and Auth Provider secrets are not deployed through the Metadata API — they must be re-entered manually in the target org after each deploy, which is one of the most common runbook omissions.

---

## Core Concepts

### Runbook vs. Release Plan

A **runbook** is a single-event execution checklist tied to one deployment window. It answers "what exactly does the person doing the deployment click, enter, or verify, in what order, right now?" It is written at the task level: check sandbox refresh date, run validation, approve, deploy, enter Named Credential values, run smoke tests, confirm with stakeholders, close the window.

A **release plan** is a project artifact that answers scope, timeline, dependencies, and stakeholder communication across multiple environments and multiple deployment events. Conflating the two is the most frequent documentation failure in Salesforce DevOps.

### Environment Matrix

An environment matrix is a structured table that captures the complete state of your sandbox topology. For each environment the matrix records: org name, org type (Developer, Partial, Full), purpose (development, regression QA, UAT, staging, hotfix), branch alignment in source control, refresh cadence (monthly, quarterly, ad hoc, never), and data policy (anonymized production data, synthetic data, no production data permitted). Without this document, teams make incorrect assumptions about what is safe to do in a given sandbox.

Salesforce Well-Architected Automated guidance requires maintaining this matrix as a living document and reviewing it before each release cycle. It is referenced directly in the DevOps Center Developer Guide as the environmental context that deployment pipelines depend on.

### Deployment Guide vs. Runbook

A **deployment guide** is a standing reference document covering the team's promotion path, validation strategy, approval gates, and known manual steps that recur across every release. It is updated when the process changes. A **runbook** is a release-specific checklist derived from the deployment guide plus the specific scope of the upcoming deployment. The deployment guide is the template; the runbook is the instance.

### Named Credential and Auth Provider Manual Steps

The Metadata API deploys `NamedCredential` and `ExternalCredential` metadata frames but does not carry secret values — passwords, client secrets, tokens, and certificates must be re-entered by an administrator in each target org after deployment. This is one of the most operationally impactful gaps between what "metadata deployed successfully" means and what "the integration actually works" means. Every runbook that includes integration metadata must include explicit steps for credential re-entry with field-level detail, not just a note saying "configure credentials."

---

## Common Patterns

### Pattern 1: Runbook for a Standard Release

**When to use:** Any planned deployment to a production org or a pre-production environment where someone other than the author will execute the steps, or where a post-incident review might need to reconstruct what happened.

**How it works:**

Structure the runbook in four phases:

1. **Pre-deploy gate** — confirm sandbox refresh date is within policy, confirm the validation run passed, confirm the deployment window is approved, confirm backup or rollback path is documented, confirm Named Credential values are on hand for each target environment.
2. **Deploy execution** — record the exact deploy command or Change Set name, the user account executing the deploy, the start timestamp, and any environment-specific flags.
3. **Post-deploy validation** — run named smoke tests (links to test scripts or manual steps), verify Named Credentials are functional by testing the relevant integration endpoint, confirm Flows that were deployed are active in the expected status, confirm profile/permission set assignments are correct.
4. **Rollback decision gate** — define the go/no-go threshold, who owns the rollback call, the rollback procedure (previous metadata version, disable-and-restore, or hotfix), and the estimated rollback time.

**Why not the alternative:** A generic checklist without the four-phase structure fails because practitioners skip post-deploy credential re-entry (the most common gap) and skip the rollback decision gate until a problem has already escalated.

### Pattern 2: Environment Matrix with Data Policy Column

**When to use:** Any org where more than one sandbox exists, or where the team is onboarding new contributors who do not know what each environment is for.

**How it works:**

Build the matrix as a Markdown table with these exact columns: `Org Name | Org Type | Purpose | Branch Alignment | Refresh Cadence | Data Policy | Owner`. The data policy column must state explicitly whether production data is present, anonymized, synthetic, or prohibited — not just "no PII." Refresh cadence drives risk: a Full Copy sandbox refreshed quarterly accumulates configuration drift from production that can cause a pre-deploy validation to pass in the wrong environment context.

**Why not the alternative:** Omitting the data policy column creates a shared assumption among contributors that often turns out to be wrong, leading to test data or integration credentials from one environment being referenced in another.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Single upcoming deployment to production | Author a runbook using the four-phase structure | Runbooks are event-scoped; the release plan already handled scope and approvals |
| Team has no documentation of sandbox topology | Build environment matrix first, then derive runbooks from it | Without the matrix, runbooks reference environments without context |
| Deployment includes Named Credentials or Auth Providers | Add explicit credential re-entry steps to the runbook | Metadata API does not carry secret values; omitting this step breaks integrations silently |
| Standing process is undocumented | Author a deployment guide before the next release | Deployment guide captures the reusable process; runbooks are derived from it |
| Post-incident review requested | Use the runbook as the primary reconstruction artifact | A well-kept runbook records who did what, when, and in what order |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on DevOps process documentation:

1. **Identify the document type needed** — determine whether the request is for a runbook (single deployment event), an environment matrix (sandbox topology reference), or a deployment guide (standing process reference). Do not conflate them.
2. **Gather environment inventory** — collect org names, types, purposes, branch alignments, refresh cadence, and data policies. Cross-reference with `skills/devops/environment-strategy` if an environment strategy is already documented.
3. **Identify all manual steps in scope** — audit the deployment scope for metadata types that require manual post-deploy action: Named Credentials, External Credentials, Auth Providers, Connected App secrets, IP allowlists, and any metadata type not covered by the Metadata API. List each as an explicit runbook step with field-level detail.
4. **Draft the document using the appropriate template** — use the runbook template for event-specific checklists, the environment matrix table for topology documentation, and the deployment guide structure for standing process.
5. **Add pre-deploy gate and rollback decision gate** — every runbook must include a documented rollback path with an owner, a go/no-go threshold, and a time estimate before the deployment window opens.
6. **Review against the Well-Architected Automated and Resilient pillars** — confirm the document covers observability (how will the team know the deployment succeeded), recovery (what is the rollback path), and change control (who approved this deployment).
7. **Socialize and store** — place the document in a location accessible to all deployment participants before the deployment window. A runbook stored only in the author's notes is not a runbook.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Document type is clearly identified: runbook, environment matrix, or deployment guide (not a blend)
- [ ] All environments in scope are listed with type, purpose, branch alignment, refresh cadence, and data policy
- [ ] Every metadata type that requires manual post-deploy action is captured as an explicit numbered step
- [ ] Named Credential and Auth Provider re-entry steps include field-level detail, not a generic note
- [ ] Rollback path is named, owned, and time-estimated before the deployment window opens
- [ ] Pre-deploy gate includes: sandbox refresh date confirmation, validation run status, deployment window approval
- [ ] Post-deploy smoke tests are listed by name or link, not just as "run smoke tests"
- [ ] Document is stored and accessible to all participants before the deployment window

---

## Salesforce-Specific Gotchas

1. **Named Credentials are deployed as empty shells** — Deploying `NamedCredential` metadata creates the record in the target org but does not transfer the password, token, or certificate. The integration will appear to deploy successfully and then fail at runtime. Every runbook for a deployment that includes integration metadata must contain explicit post-deploy steps to re-enter credentials.

2. **Sandbox refresh invalidates prior runbook assumptions** — After a Full Copy sandbox refresh, the org configuration reverts to the production state at the time of the refresh snapshot. Runbooks authored before a refresh may reference settings, users, permission sets, or connected apps that no longer exist or have different IDs in the refreshed org. Always confirm sandbox refresh date as a pre-deploy gate item.

3. **Flow activation state is separate from Flow deployment** — Deploying a Flow through the Metadata API creates the Flow version in the target org, but whether it is active or inactive depends on the `status` field in the metadata. Teams frequently deploy Flows and then discover in production that the Flow is inactive (or worse, that an old active version is still running). Every runbook that includes Flow deployment must include a post-deploy step to verify active Flow version and version number.

4. **Environment matrices go stale silently** — Salesforce does not notify teams when a sandbox is refreshed, when org type changes, or when a new environment is added. A matrix that was accurate six months ago may now describe environments that no longer exist or misrepresent environments that were refreshed. The matrix must have an explicit review step at the start of each release cycle, not just when someone notices it is wrong.

5. **Conflating runbook with release plan creates accountability gaps** — If the runbook is written at release plan granularity (scope, timeline, stakeholder communication), it becomes too long to use during a deployment window and does not identify who is responsible for each action step. Runbooks must be written at execution granularity: numbered steps, single responsible person per step, expected duration, and a pass/fail outcome.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Environment matrix | Markdown table: org name, type, purpose, branch alignment, refresh cadence, data policy, owner |
| Deployment runbook | Numbered execution checklist covering pre-deploy gate, deploy execution, post-deploy validation, and rollback decision gate |
| Deployment guide | Standing reference: promotion path, validation strategy, approval gates, recurring manual steps |
| Named Credential re-entry checklist | Field-level steps for re-entering credentials in each target environment after deploy |

---

## Related Skills

- **devops/environment-strategy** — Use when the environment topology itself needs to be designed or restructured, not just documented. This skill documents an existing topology; environment-strategy establishes it.
- **admin/change-management-and-deployment** — Use when the deployment method selection, release governance, or rollback strategy is the primary question. This skill documents the process; change-management-and-deployment governs it.
- **admin/deployment-risk-assessment** — Use when the primary need is risk scoring and pre-release risk identification before a deployment. This skill documents execution steps; deployment-risk-assessment evaluates risk.
- **devops/deployment-monitoring** — Use when the question is how to observe and alert on deployments in flight, not how to document the process.
