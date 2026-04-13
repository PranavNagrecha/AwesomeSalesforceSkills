---
name: change-advisory-board-process
description: "Use when designing, implementing, or auditing a Change Advisory Board (CAB) process for Salesforce deployments — covering change classification (standard, normal, emergency), required approvals, deployment gate sequencing, and integration with external ITSM tooling. NOT for record-level approval workflows (use Salesforce Approval Processes for business-object approvals), NOT for detailed pipeline automation scripting (see devops-process-documentation or pre-deployment-checklist), and NOT for Salesforce DevOps Center pipeline configuration."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Operational Excellence
  - Reliability
triggers:
  - "How do I set up a change advisory board process for Salesforce releases?"
  - "What approvals are required before deploying to production in Salesforce?"
  - "Our organization requires CAB sign-off before any Salesforce deployment — how do we implement this?"
  - "How should we classify Salesforce changes as standard, normal, or emergency for ITIL governance?"
  - "Who needs to approve permission set or sharing rule changes before production deployment?"
  - "How do we coordinate Salesforce deployments with the seasonal release upgrade window?"
  - "We need an emergency change process for urgent Salesforce hotfixes that bypasses the normal CAB cycle"
tags:
  - change-advisory-board
  - cab-process
  - itil
  - governance
  - deployment-governance
  - change-management
  - release-management
  - devops
inputs:
  - "Change classification criteria currently in use (or that need to be defined)"
  - "List of high-risk metadata types relevant to the org (permissions, sharing, flows, integrations)"
  - "Existing ITSM tooling in use (Jira, ServiceNow, Azure DevOps, etc.)"
  - "Deployment pipeline tooling (Salesforce CLI, DevOps Center, Copado, Gearset, etc.)"
  - "Upcoming Salesforce seasonal release dates and sandbox preview window"
  - "Regulatory or compliance context (e.g., HIPAA, FedRAMP/GovCloud, SOX) if applicable"
outputs:
  - "Change classification matrix mapping Salesforce metadata types to CAB tier (standard / normal / emergency)"
  - "Approval workflow definition with named approver roles and required sign-off count per tier"
  - "Deployment freeze calendar accounting for Salesforce seasonal release upgrade windows"
  - "Emergency CAB (ECAB) process documentation with criteria, approvers, and post-incident review requirement"
  - "CAB integration specification for external ITSM tool (e.g., ServiceNow change request gate)"
dependencies:
  - admin/deployment-risk-assessment
  - admin/devops-process-documentation
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-13
---

# Change Advisory Board Process

This skill activates when a team needs to define, implement, or audit a Change Advisory Board (CAB) process for governing Salesforce deployments. It covers ITIL-derived change classification, multi-stakeholder approval design, deployment gating against external ITSM tooling, and coordination with Salesforce's seasonal release upgrade calendar.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm whether the organization already has an enterprise ITSM platform (ServiceNow, Jira Service Management, etc.) — the CAB process must integrate with it, not replace it.
- Identify which Salesforce metadata types are in-scope for high-risk classification: Profile/Permission Set changes, Sharing Rules, Validation Rules affecting critical objects, Flow/Process Builder automation, Named Credentials, Remote Site Settings, and any Connected App OAuth scopes.
- Establish the next Salesforce seasonal release dates (Spring, Summer, Winter). The sandbox preview window opens approximately 4–6 weeks before the production upgrade, and the production upgrade is rolled out in three waves over several weekends. Deployments staged in or near this window may encounter platform-behavior drift between sandbox and production.
- Confirm whether regulated-industry requirements apply (GovCloud for US Federal/HIPAA orgs applies additional Significant Change Notification obligations to the Salesforce trust team).

---

## Core Concepts

### Change Classification Tiers

ITIL defines three change tiers that map cleanly to Salesforce deployment governance:

- **Standard change** — pre-authorized, repeatable, low risk. Examples: adding a custom field to a non-critical object, updating a report or dashboard, activating a cloned email template. No CAB meeting required; implementation follows a pre-approved runbook.
- **Normal change** — requires full CAB review before deployment. Examples: any modification to Profiles or Permission Sets, Sharing Rule changes, Flow deployment to production, new Named Credential or Remote Site Setting, any integration endpoint change. Approval requires sign-off from at least the Salesforce Admin, the relevant Business Owner, and Security/IT where permissions or data access changes are involved.
- **Emergency change** — unplanned fix required to restore service or prevent imminent harm. Routed to an Emergency CAB (ECAB), a smaller rapid-response quorum (typically 2–3 approvers rather than the full board). ECAB approvals require a mandatory post-implementation review within 5 business days.

### CAB Runs Outside Salesforce

Salesforce does not ship a native CAB feature. The CAB meeting, change ticket lifecycle, and deployment gate enforcement all live in the organization's ITSM platform (ServiceNow, Jira Service Management, Freshservice, etc.). The deployment toolchain (Salesforce CLI, Copado, Gearset, DevOps Center) must be configured to require a valid approved change request number before a production deploy can execute. The CAB process governs when a deployment is authorized; the deployment tool executes it.

Attempting to implement CAB governance using Salesforce-native Approval Processes is an anti-pattern (see llm-anti-patterns.md). Approval Processes govern record-level business workflows with no pipeline awareness.

### Seasonal Release Upgrade Windows

Salesforce upgrades sandbox environments approximately 4–6 weeks before the corresponding production upgrade. The production upgrade rolls out in three weekend waves. Teams must:

1. Block deployments during the sandbox preview window unless they have been explicitly tested against the preview release.
2. Treat the 7-day period immediately before each production upgrade wave as a soft freeze for anything other than emergency changes.
3. Account for sandbox-to-production behavior drift: a deployment that passes in a pre-upgrade sandbox may fail or behave differently in a post-upgrade production org.

The Salesforce Trust calendar (trust.salesforce.com) publishes upgrade dates. The CAB change calendar must incorporate these dates.

### High-Risk Metadata Types

Certain metadata types carry inherently higher risk and must always route through a normal (or emergency) CAB, never be pre-authorized as standard changes:

| Metadata Type | Risk Reason |
|---|---|
| Profile / PermissionSet | Can grant or revoke access at scale instantly |
| SharingRules / OWD | Changes visibility of records org-wide |
| Flow / ProcessBuilder | Can trigger automation loops or mass DML |
| NamedCredential / RemoteSiteSetting | Opens or closes external network access |
| Connected App OAuth scopes | Changes what external systems can access |
| ValidationRule (on critical objects) | Can silently block data entry for users |
| CustomMetadata / CustomSetting | Can alter behavior of Apex and automations globally |

---

## Common Patterns

### Pattern 1: ITSM-Gated Pipeline Deploy

**When to use:** When the organization uses a CI/CD pipeline (GitHub Actions, Copado, Gearset) and wants CAB approval to be a hard gate before production deploys are allowed.

**How it works:**
1. Developer or admin raises a change request in the ITSM tool (e.g., ServiceNow), providing metadata scope, risk classification, rollback plan, and test evidence.
2. The ITSM tool routes the ticket to the appropriate CAB queue based on the change tier.
3. CAB approvers review asynchronously or in a scheduled meeting and set the change request status to Approved.
4. The deployment pipeline checks the ITSM API for the approved change request number before allowing the production deploy step. If the ticket is not in Approved state, the pipeline fails-fast with a descriptive error.
5. Post-deployment, the pipeline updates the change request status to Implemented and attaches a deployment log.

**Why not the alternative:** Relying on informal email or Slack approvals creates no audit trail, fails compliance audits, and has no enforcement mechanism to prevent unauthorized deployments.

### Pattern 2: Change Classification Matrix Gating in Pull Requests

**When to use:** When the organization wants to shift change classification left — identifying the CAB tier at the point of code review, not at deployment time.

**How it works:**
1. A pull request template includes a mandatory "Change Classification" field (Standard / Normal / Emergency).
2. A lightweight PR check script inspects which metadata types appear in the diff and flags if the declared classification is inconsistent (e.g., a Profile change declared as Standard).
3. For Normal changes, PR approval requires a named security or platform architect reviewer in addition to the peer reviewer.
4. The merged PR creates a linked ITSM change request automatically via webhook.

**Why not the alternative:** Leaving classification to deployment time means the CAB review happens after development is complete, creating pressure to approve without adequate review time.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Org change involves Profile or PermissionSet edits | Normal change — full CAB required | Access control changes are irreversible at scale and have immediate security impact |
| Routine report/dashboard update, no data access change | Standard change — use pre-approved runbook | Low risk, high frequency; CAB overhead is disproportionate |
| Production system down, Flow causing data corruption | Emergency change — ECAB with 2–3 approvers | Speed required; document and post-review within 5 business days |
| Deployment lands in Salesforce seasonal upgrade preview window | Flag for extended testing; treat as Normal minimum | Sandbox-to-production platform drift risk is elevated |
| Regulated industry org (GovCloud / HIPAA) | Add Significant Change Notification to Salesforce Trust as additional step | Regulatory obligation; failure to notify can trigger compliance findings |
| Integration endpoint or Named Credential change | Normal change — require security team approval | External network access changes need security sign-off |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Inventory the current metadata scope.** Enumerate all metadata types in the planned deployment. Use `sf project generate manifest` or review the PR diff. Cross-reference each type against the high-risk metadata list to determine the minimum CAB tier.
2. **Classify the change.** Apply the change classification matrix. If any single metadata type in the deployment maps to Normal, the entire deployment is Normal (no mixing tiers in a single change). Document the classification rationale in the change ticket.
3. **Raise the change request in the ITSM tool.** Populate all required fields: classification tier, description of change, impacted business processes, rollback plan, test evidence (sandbox deployment log, test class results), planned deployment window, and approver assignments.
4. **Obtain required approvals.** Normal changes require sign-off from: Salesforce Admin or Release Manager, affected Business Process Owner(s), and Security/IT for any access or integration changes. Emergency changes require the ECAB quorum (minimum 2 named approvers). Do not proceed until the change request reaches Approved status.
5. **Verify deployment window is clear.** Check the Salesforce Trust calendar (trust.salesforce.com) for upcoming upgrade windows. Confirm the planned deploy window is not within 7 days of a production upgrade wave. If it is, either reschedule or escalate to confirm explicit CAB acceptance of the elevated risk.
6. **Execute deployment and capture evidence.** Run the deployment through the approved pipeline. Attach the deployment log and any post-deployment validation results to the change ticket. Mark the ticket Implemented.
7. **Conduct post-implementation review.** For Normal changes, confirm no unintended impacts within 24 hours. For Emergency changes, schedule the mandatory post-implementation review within 5 business days and capture lessons learned.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Every metadata type in the deployment has been classified against the risk matrix
- [ ] Change request exists in the ITSM tool with all required fields completed (scope, rollback plan, test evidence)
- [ ] Required approvals have been obtained and are documented in the change ticket
- [ ] Deployment window is clear of Salesforce seasonal upgrade waves (check trust.salesforce.com)
- [ ] Rollback procedure is documented and has been tested (or the rollback steps are explicitly understood)
- [ ] Post-deployment validation plan is defined (smoke tests, data integrity check, user acceptance)
- [ ] For Emergency changes: post-implementation review is scheduled within 5 business days

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Sandbox Preview Behavior Drift** — When Salesforce rolls out the seasonal preview to sandboxes (approximately 4–6 weeks before production), the sandbox may exhibit new platform behaviors (API changes, validation differences, Flow engine updates) that do not yet exist in production. A deployment passing in the preview sandbox can fail or behave differently in the still-on-old-release production org. The CAB change calendar must treat this window as elevated-risk and require explicit sign-off acknowledging the drift.

2. **Permission Set Deployment Does Not Revoke** — Deploying a Permission Set via the Metadata API or Salesforce CLI adds or updates permission entries but does not remove permissions that were manually added in the target org after the last source-tracked state. An LLM or practitioner assuming "deploy from source" produces an exact replica is wrong. The CAB process for access control changes must include a post-deployment audit step comparing expected vs. actual effective permissions.

3. **Profile Metadata Is Full-Replace on Some Attributes** — When a Profile is deployed, certain sections (e.g., field-level security, object permissions) behave as full replacements for the attributes present in the deployed XML — but the XML itself may not capture all attributes if the project was not retrieved with the full Profile. This can silently revoke permissions that were not included in the retrieved file. Any CAB involving Profile changes must require a full Profile retrieval before classification and a post-deploy permission audit.

4. **Approval Processes Are Not CAB Enforcement** — Salesforce Approval Processes govern individual record state transitions (e.g., Opportunity discount approval). They have no awareness of the deployment pipeline, no concept of a change ticket, and cannot gate metadata deployments. Configuring an Approval Process as the CAB mechanism is an anti-pattern that creates a false sense of governance while leaving the deployment pipeline completely ungated.

5. **Regulatory Significant Change Notification (GovCloud / HIPAA)** — Orgs operating under GovCloud or HIPAA arrangements with Salesforce have a contractual obligation to notify the Salesforce Trust team of Significant Changes (e.g., major integration changes, architectural shifts) with advance notice defined in the agreement. This is a step the internal CAB process must trigger — missing it is a compliance violation, not just an operational oversight.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Change Classification Matrix | Table mapping Salesforce metadata types to CAB tier (Standard / Normal / Emergency) with rationale |
| Approval Workflow Definition | Named approver roles, minimum sign-off count per tier, escalation path |
| Deployment Freeze Calendar | Rolling calendar with Salesforce upgrade windows, internal freeze periods, and available deployment slots |
| ECAB Process Document | Emergency change criteria, ECAB quorum membership, expedited approval steps, post-review requirement |
| ITSM Integration Specification | API gate configuration connecting the deployment pipeline to the ITSM change request status |

---

## Related Skills

- admin/deployment-risk-assessment — Use before classifying a change to assess blast radius, rollback complexity, and data impact of the planned deployment
- admin/devops-process-documentation — Use to document the end-to-end deployment and release process that the CAB process governs
- admin/change-management-and-training — Use when the CAB process change itself requires stakeholder communication and adoption planning
- devops/pre-deployment-checklist — Use to execute the technical pre-flight checks that feed evidence into the CAB change ticket
- devops/release-management — Use for the broader release planning context within which individual CAB-approved changes are scheduled
- devops/deployment-monitoring — Use post-deployment to generate the evidence artifacts required by the CAB post-implementation review
