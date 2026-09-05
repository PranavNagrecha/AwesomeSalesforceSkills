---
name: change-advisory-board-process
description: "Design, implement, or audit a Change Advisory Board (CAB) process for Salesforce deployments: change classification (standard, normal, emergency), required approvals, deployment gate sequencing, and integration with external ITSM tooling. NOT for scoring how risky one release is - use admin/deployment-risk-assessment. NOT for executing or troubleshooting the deployment itself - use admin/change-management-and-deployment. Also covers: the CAB charter (membership, quorum, decision rights), the CAB decision record artefact and its linter, the change classification matrix, the deployOptions a CAB decision pins (checkOnly, testLevel, rollbackOnError, ignoreWarnings, runTests), the 10-day quick-deploy validity window, the deploy-window vs freeze-register check, and the emergency (ECAB) path with its mandatory retrospective."
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
  - "which Salesforce metadata types need CAB approval and which are pre-authorised"
  - "can we quick-deploy a validation the CAB approved three weeks ago"
  - "the deploy window falls inside the Salesforce upgrade weekend"
  - "our CAB approved a change set and a component was added after the vote"
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
version: 1.1.0
author: Pranav Nagrecha
updated: 2026-09-05
---

# Change Advisory Board Process

This skill activates when a team needs to define, implement, or audit a Change Advisory Board (CAB) process for governing Salesforce deployments. It covers ITIL-derived change classification, multi-stakeholder approval design, deployment gating against external ITSM tooling, and coordination with Salesforce's seasonal release upgrade calendar.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm whether the organization already has an enterprise ITSM platform (ServiceNow, Jira Service Management, etc.) — the CAB process must integrate with it, not replace it.
- Identify which Salesforce metadata types are in-scope for high-risk classification: Profile/Permission Set changes, Sharing Rules, Validation Rules affecting critical objects, Flow/Process Builder automation, Named Credentials, Remote Site Settings, and any Connected App OAuth scopes.
- Establish the next Salesforce seasonal release dates (Spring, Summer, Winter). The sandbox preview window opens approximately 4–6 weeks before the production upgrade, and the production upgrade is rolled out in three waves over several weekends. Deployments staged in or near this window may encounter platform-behavior drift between sandbox and production. UNVERIFIED (2026-09-05): the "approximately 4–6 weeks" preview lead time and the three-weekend wave structure are not asserted in any of the extracted guides, and help.salesforce.com cannot be fetched from this environment. What the Metadata API Developer Guide does state is that "Salesforce performs major service upgrades three times per year" and that you should "avoid running deployments during the service upgrade", checking Salesforce Trust for your instance's date (api_meta.txt L2115–2125). Take the instance-specific dates from Trust and the preview rules from `admin/salesforce-release-preparation`; do not hard-code the interval.
- Confirm whether regulated-industry requirements apply (GovCloud for US Federal/HIPAA orgs applies additional Significant Change Notification obligations to the Salesforce trust team).

---

## Questions to Ask Before Configuring

Ask these before writing a charter or approving anything. Each one traces to a gotcha, and a
board that skipped them produces an approval that reads well and enforces nothing.

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "Which single role can say no and not be outvoted, and on what exactly?" | A quorum expressed only as a number lets three admins approve a sharing change. Veto scope is the difference between a board and a headcount | `required_roles` per tier in the charter, plus a named veto scope and its escalation route |
| "Which org was the validation run against, and on what date?" | A validated set qualifies for deployment without re-running tests only for the target environment it ran against, and only for 10 days (Gotcha 6) | `validation_id`, `validation_target_org` and `validation_date` on the decision record, which the checker enforces |
| "What is the rollback in metadata terms, and has anyone actually run it?" | Cancelling a running deploy is not an undo — a deployment in `Finalizing Deploy` cannot be cancelled at all (Gotcha 9) | A pinned previous package, an owner, an RTO, and the manual Setup steps no package can carry |
| "Who in production holds Author Apex, Deploy Change Sets, Modify All Data, or Modify Metadata Through Metadata API Functions?" | That set, not the set with pipeline credentials, is the gate's real perimeter — and `Author Apex` grants metadata deployment as a side effect (Gotcha 10) | A reviewed access list, and an honest statement of which paths the gate does not cover |
| "Which instance is this org on, and when is its next service upgrade?" | Salesforce advises avoiding deployments during a service upgrade; an interrupted deploy is retried from the beginning (`api_meta.txt` L2115–2125) | A freeze register with a citable source and a named exception approver per range, instead of someone's recollection |
| "Does anything in this package delete a component or convert a relationship field?" | Destructive changes are an ordering decision, and `checkOnly` cannot validate a Master-Detail ↔ Lookup conversion at all (Gotcha 7) | The right evidence artefact for the tier — a full sandbox deploy where a validation would always come back red |
| "What evidence closes each approval condition, and who owns it after the deploy?" | Conditions attached to a vote are the thing that silently evaporates between the meeting and the window | `conditions[].owner` and `conditions[].blocks`, and a dated post-implementation review that checks them off |

What a proper CAB process adds over just approving deployments: the board's decision is a
linted, version-controlled record pinned to one package, one set of deploy options and one
window — so an auditor, and the next release, can reconstruct what was approved and on what
evidence rather than reading a thread.

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

### What the Board Is Actually Approving: a Package Plus Its Deploy Options

A CAB that approves "the change" has approved a range of behaviours. The same package deployed
with different `DeployOptions` is a different deployment, so the decision record pins them. What
the Metadata API Developer Guide states about each:

| Option | What the guide says | Consequence for the decision |
|---|---|---|
| `checkOnly` | `true` performs "a test deployment (validation) of components without saving the components in the target org" (L3095–3099) | The validation is the evidence, not the change. Record its id, its target org and its date |
| `testLevel` | Enum: `NoTestRun`, `RunSpecifiedTests`, `RunRelevantTests` (beta), `RunLocalTests`, `RunAllTestsInOrg`. `NoTestRun` "applies only to deployments to development environments". `RunLocalTests` "is the default for production deployments that include Apex classes or triggers" (L4280–4329) | `NoTestRun` on a production window is an error, not a shortcut |
| `rollbackOnError` | "This parameter must be set to `true` if you're deploying to a production org" (L4255–4260) | With it false the deploy can land as `SucceededPartial` (L7451) — a half-applied package nobody reviewed |
| `ignoreWarnings` | Defaults to `false`; "Don't set this argument to `true` for deployments to production organizations" (L7390–7392) | With it true, warnings are reported as successes and the deploy log stops being evidence |
| `runTests` | "A list of Apex tests to run… To use this option, set `testLevel` to `RunSpecifiedTests`" (L3132–3135) | A `runTests` list under any other test level is silently inert |

**The quick-deploy window is 10 days and is bound to one org.** A validated component set can be
deployed without re-running Apex tests only when "the components have been validated successfully
**for the target environment** within the last **10 days**", the target org's Apex tests passed,
and coverage requirements are met (`api_meta.txt` L4863–4869). A validation against UAT is not an
approval input for a production deploy, and an approval that predates the window by more than ten
days has expired. See `references/gotchas.md` Gotcha 6.

**Deployment windows and service upgrades.** The guide's own guidance is to "avoid running
deployments during the service upgrade", because a file-based deployment interrupted by downtime
has "both component deployment and validation… retried from the beginning after the service is
restored" — and it names Salesforce Trust as where to check whether your instance is due
(`api_meta.txt` L2115–2125). That is the platform basis for the freeze register; the
instance-specific dates and the Release Updates posture come from
`admin/salesforce-release-preparation`.

### The CAB Decision Record

The board's output is one YAML file per decision, committed beside the release manifest so the
approval and the package it approved are versioned together. Its shape, filled in for a real
release, is `references/worked-examples.md` §3; `scripts/check_change_advisory_board_process.py`
lints it. The blocks it must carry:

| Block | Holds | Checked by the linter |
|---|---|---|
| `classification` / `decision` | The tier and the outcome, from fixed enums | Value is in the enum |
| `board[]` | One row per member with a `vote`, not attendance | Quorum met for the tier; charter's `required_roles` among the voters; no unresolved veto under an approval |
| `risk` + `blast_radius` | Level, rationale, and an *imported* blast radius citing the analysis that produced it | Level in enum; rationale non-empty; blast radius names a source and at least one metadata type |
| `test_evidence[]` | UAT pack, validation result, RACI, run sheet — each by path | Every path resolves to a real file under `--manifest-dir` |
| `rollback` | Pinned previous package, owner, RTO, manual steps | Method and owner present; `rehearsed: true` required at `risk.level: high` |
| `deploy_window` + `freezes[]` | Target org, window, deploy options, quick-deploy fields, freeze ranges | Window does not overlap a freeze; options and quick-deploy validity as above |
| `post_implementation_review` | Date and owner | Mandatory for `emergency`; warned for `normal` |

The record lives outside the org. Salesforce ships no CAB feature, no change-record standard
object and no way for the org to gate its own deployment pipeline — which is why the enforcement
point is the pipeline and the evidence point is this file.

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

1. **Write or re-read the charter first.** `references/worked-examples.md` §1 is a filled-in
   `cab-charter.yaml`. Fix `quorum` per tier, `required_roles` per tier, veto scope, and the
   `exception_approver` for a freeze. Everything downstream reads these; a decision record cannot
   be linted against a charter that does not exist.
2. **Build the classification matrix from the package's metadata types, not from intent.**
   Enumerate the types with `sf project generate manifest` or from the PR diff, then apply
   `references/worked-examples.md` §2. Highest tier wins for the whole package. Record why
   `ValidationRule` and `SharingRules` outrank `ListView` — the risk signal, not the folder name.
3. **Import the blast radius; do not estimate it in the meeting.** Run `/analyze-field-impact`
   (`agents/field-impact-analyzer/AGENT.md`) or the equivalent and cite its report path in
   `blast_radius.source`. Pull the rollback shape from `devops/rollback-and-hotfix-strategy` and
   the pre-deploy evidence set from `devops/pre-deployment-checklist`.
4. **Fill in the decision record.** Copy `references/worked-examples.md` §3. Pin the deploy
   options and, if quick-deploying, all three quick-deploy fields. Attach the four practice
   artefacts as `test_evidence`: the UAT pack (`admin/uat-and-acceptance-criteria`), the
   validation result, the RACI (`admin/stakeholder-raci-for-sf-projects`) and the release run
   sheet (`admin/salesforce-release-preparation`).
5. **Lint it before the meeting, not after.** Run
   `python3 scripts/check_change_advisory_board_process.py --manifest-dir <artefacts>`. It exits
   1 on: an enum violation, quorum or a required role missing, an empty risk or blast-radius
   block, a rollback with no owner (or unrehearsed at high risk), an evidence path that does not
   resolve, a window overlapping a freeze, an invalid `testLevel` or `rollbackOnError: false` on
   production, an expired or wrong-org quick deploy, and an emergency record with no
   retrospective date. Every failure is something the board would otherwise discover afterwards.
6. **Deploy inside the window and capture platform-side evidence.** `sf project deploy report`
   gives `createdByName` and whether tests ran; a `SetupAuditTrail` query over the window
   (`references/worked-examples.md` §5) surfaces Setup activity that was *not* in the approved
   package. Both belong on the CR.
7. **Hold the post-implementation review and feed it back into the charter.** Use
   `references/worked-examples.md` §7. Close each condition by id, record what the blast-radius
   estimate got wrong, and report the emergency:normal ratio. A charter that never changes after
   a PIR is a charter nobody is reading.

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

## Reference Files

| File | Read it when |
|---|---|
| `references/worked-examples.md` | Writing anything. Holds the Acme case-intake release end to end — the charter, the classification matrix, the filled-in decision record, the package and destructive manifests, the deploy-options table with its grounding, the emergency record, and the post-implementation review |
| `references/gotchas.md` | Before approving, and when a board decision is challenged afterwards. Eleven platform behaviours that turn a well-run meeting into an unenforced approval |
| `references/examples.md` | Choosing an enforcement mechanism. Three scenarios — PR-time classification, an ECAB flow deployment, and a freeze-register collision — with the gate scripts and the register file |
| `references/llm-anti-patterns.md` | Reviewing AI-generated CAB guidance, especially anything that proposes a Salesforce Approval Process or a `Deployment_Request__c` object as the gate |
| `references/well-architected.md` | Justifying the process weight to a sponsor: pillar mapping, the three tradeoffs, and the full source list with the claim each one supports |
| `scripts/check_change_advisory_board_process.py` | Every time a decision record changes. `--manifest-dir <dir>`, or `--file <record>`; `--charter` to point at a charter outside the scanned tree |
| `templates/change-advisory-board-process-template.md` | Starting from blank: the section skeleton for the charter, matrix, approval workflow, freeze calendar and ITSM gate spec |

---

## Related Skills

- admin/deployment-risk-assessment — Use before classifying a change to assess blast radius, rollback complexity, and data impact of the planned deployment
- admin/devops-process-documentation — Use to document the end-to-end deployment and release process that the CAB process governs
- admin/change-management-and-training — Use when the CAB process change itself requires stakeholder communication and adoption planning
- devops/pre-deployment-checklist — Use to execute the technical pre-flight checks that feed evidence into the CAB change ticket
- devops/release-management — Use for the broader release planning context within which individual CAB-approved changes are scheduled
- devops/deployment-monitoring — Use post-deployment to generate the evidence artifacts required by the CAB post-implementation review
- admin/change-management-and-deployment — Use to execute the deployment the CAB approved: manifests, deploy order, and the CLI mechanics this skill only gates
- admin/salesforce-release-preparation — Use to build the freeze register's inputs: instance upgrade dates, Release Updates posture for the cycle, and the Sandbox Preview opt-in decision
- admin/stakeholder-raci-for-sf-projects — Use to produce the RACI cited as `test_evidence` on the decision record; it names the accountable party the board otherwise assumes
- admin/uat-and-acceptance-criteria — Use to produce the UAT pack cited as `test_evidence`; the board reviews its sign-off rather than re-testing
- admin/sandbox-strategy — Use to check that the rollback rehearsal has an environment to run in and that its refresh floor fits inside the release cadence
- devops/rollback-and-hotfix-strategy — Use to design the rollback the decision record pins, including the manual Setup steps no package can carry
- devops/post-deployment-validation — Use to define the checks whose results close the post-implementation review
