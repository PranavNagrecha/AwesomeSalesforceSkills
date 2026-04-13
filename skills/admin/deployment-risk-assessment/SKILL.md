---
name: deployment-risk-assessment
description: "Use when a practitioner needs to classify the risk level of an upcoming Salesforce deployment, define rollback trigger conditions, or assign decision authority before the release window opens. Triggers: 'how risky is this release', 'what needs rollback planning', 'classify deployment risk', 'pre-deployment risk checklist', 'rollback decision authority', 'high risk metadata types'. NOT for executing the deployment itself, writing CI/CD pipeline code, or troubleshooting failures after a deployment has already run — use change-management-and-deployment for execution planning and devops/deployment-error-troubleshooting for post-failure diagnosis."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
  - Security
triggers:
  - "how do I know if this release is high risk before we deploy"
  - "what metadata types need extra scrutiny in a production deployment"
  - "who should have authority to call a rollback during a release window"
  - "what rollback options exist for org-based deployments with no packages"
  - "we need to classify each change as high medium or low risk before the release"
  - "what should we document before opening the deployment window on Friday"
tags:
  - deployment-risk-assessment
  - release-management
  - rollback-planning
  - change-management
  - devops
  - well-architected
inputs:
  - "List of metadata components included in the release (types and names)"
  - "Deployment method in use (Change Sets, DevOps Center, SFDX CLI, unlocked package)"
  - "Promotion path: which sandboxes were validated and in what order"
  - "Rollback assets available: pre-retrieve backup, prior package version, feature flags"
  - "Business impact window and who holds release go/no-go authority"
outputs:
  - "Risk-classified component inventory (HIGH / MEDIUM / LOW per component)"
  - "Rollback plan with explicit trigger conditions and decision authority named"
  - "Pre-deployment checklist covering people, process, and technology failure domains"
  - "Go/no-go criteria document for the release window"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-13
---

# Deployment Risk Assessment

Use this skill to classify deployment risk by component before a release window opens, define rollback trigger conditions in writing, and assign decision authority so that rollback calls are made on pre-agreed criteria rather than improvised under pressure.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Release scope:** What metadata types are included? Permissions, flows, integrations, and sharing rules carry higher inherent risk than layout and list view changes.
- **Deployment method:** Unlocked packages support version-based rollback by redeploying the previous version. Change Sets and CLI-based org deploys have no native undo — rollback requires a pre-retrieve backup or a manually authored destructive change.
- **Validation evidence:** Which sandboxes ran a full deployment validation, and did they match the production metadata state at validation time?
- **Business window:** When does the deployment open, how long is the window, and what is the tolerance for staying in a broken state?
- **Decision authority:** Who has go/no-go authority, who can call rollback, and how are they reachable during off-hours releases?

---

## Core Concepts

### The Three Failure Domains

The Salesforce Well-Architected framework frames deployment risk across three failure domains:

1. **People** — Missing decision authority, unclear escalation paths, or a team unfamiliar with the rollback procedure under time pressure.
2. **Process** — No documented rollback trigger conditions, skipping lower-environment validation, or merging unrelated changes into a single release with no decomposition.
3. **Technology** — Metadata dependencies not resolved before deployment, missing pre-retrieve backup, or relying on the Salesforce UI for a rollback mechanism that does not exist.

Risk classification must address all three domains. A release that looks technically simple can be high-risk on the people dimension if the release manager is unavailable and no alternate decision-maker is named.

### Release Mechanism Risk Ranking

Salesforce release mechanisms differ significantly in their rollback fidelity:

| Mechanism | Rollback Path | Rollback Speed |
|---|---|---|
| Unlocked Package | Redeploy prior package version | Fast — version is pre-built |
| 2GP Managed Package | Install prior version from package store | Medium — package store required |
| SFDX / CLI org deploy | Re-deploy prior metadata from source control | Medium — requires clean pre-retrieve |
| DevOps Center | Re-deploy prior pipeline stage via UI | Medium — depends on pipeline history |
| Change Set | Re-deploy a manually constructed reverse set | Slow — must be built manually |
| In-org config only | Manual undo in Setup | Slowest — no deployment artifact exists |

Unlocked packages offer the most rollback-friendly path through versioning. Change Sets and direct org config changes have no native undo — rollback is always a re-deploy of the prior state, not a platform-provided undo button.

### Risk Classification Criteria

Classify each component HIGH, MEDIUM, or LOW before the release window opens:

**HIGH risk indicators (any one sufficient):**
- Metadata type affects security, sharing, or access: PermissionSet, Profile, SharingRule, ConnectedApp, AuthProvider, ExternalCredential
- Metadata has org-wide behavioral impact: Flow on high-volume objects, ApexTrigger on high-volume objects, CustomSetting used by integrations
- No lower-environment validation evidence exists at current production metadata state
- Component cannot be disabled without redeploying — no feature flag or custom permission gate
- Rollback requires destructive change metadata that has not been authored and tested in advance

**MEDIUM risk indicators:**
- Flow, Process Builder, or approval process with moderate transaction volume
- Integration endpoint URL or named credential change
- Custom metadata type value changes that affect runtime behavior
- New Apex class or trigger with no prior production surface

**LOW risk indicators:**
- UI-only changes: page layouts, list views, compact layouts, reports, dashboards
- New custom field with no automation or trigger dependency
- Email template or letterhead changes

### Rollback as a Pre-Agreed Procedure

Rollback conditions must be defined before the release window, not decided during one. A rollback plan that says "roll back if something breaks" is not actionable. A valid rollback plan specifies:

- Exact observable trigger conditions (error rate exceeds a defined threshold, a specific Apex exception fires in production, integration response latency exceeds a defined limit)
- Who has authority to call rollback (named individual plus named alternate)
- How long the team will monitor before declaring the release stable
- The exact rollback procedure steps and estimated execution time

---

## Common Patterns

### Pre-Release Risk Classification Table

**When to use:** Any release containing more than one metadata component or any HIGH-risk component type.

**How it works:** Before the release window, build a table with one row per component group. Score each row across five dimensions: metadata type risk, validation coverage, rollback complexity, business impact, and people readiness. Sum the dimension scores to produce an overall release risk level.

**Why not the alternative:** Informal team review without a structured table produces inconsistent results — experienced engineers classify intuitively while newer contributors underestimate risk. A table forces explicit scoring and surfaces gaps before the window opens.

### Rollback Runbook

**When to use:** Any HIGH or MEDIUM release that deploys to production.

**How it works:** Author the rollback runbook as part of release preparation, not as an afterthought. The runbook includes: the pre-retrieve backup path for org-based deploys, the package version to reinstall for packaged releases, the exact CLI command or UI steps, the expected execution time, and the post-rollback smoke test.

**Why not the alternative:** Improvising rollback steps during a production incident is the primary cause of rollback failures. The team is under time pressure, may be missing key personnel, and the environment state may differ from what was expected.

### Feature Flag Gate for HIGH-Risk Components

**When to use:** A HIGH-risk behavioral change (new Flow logic, Apex trigger change, integration routing) needs to be deployed but activation timing is uncertain.

**How it works:** Deploy the change behind a Custom Permission or Custom Metadata Type flag. The component is present in the org but inactive. Activation happens through a separate, lower-risk metadata update (changing a Custom Metadata record) that can be reverted without a full re-deploy.

**Why not the alternative:** Deploying and activating simultaneously collapses the deployment risk and the activation risk into a single event. Separating deployment from activation allows rollback of activation without touching the deployment artifact.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Release contains PermissionSet or Profile changes | Classify HIGH; require full sandbox validation at current prod metadata state | Security metadata errors may silently over-share or under-share access |
| No pre-retrieve backup exists before the window | Require backup before proceeding or reclassify deployment method risk as HIGH | Org-based rollback requires prior state capture — no platform undo exists |
| Rollback authority is unclear or person is unavailable | Block release until named alternate is confirmed and reachable | Rollback without authority wastes time; no authorized caller means longer outage |
| Release uses unlocked package | Record the prior package version number; confirm subscriber org can receive an older version | Version-based rollback is the fastest path but still requires a deliberate install action |
| Multiple unrelated features are bundled | Recommend decomposing into separate deployments or documenting per-feature rollback steps | Bundled releases cannot be partially rolled back; a defect in one feature forces rollback of all |
| Component has no feature flag or disable path | Require destructive change metadata to be authored and tested before the window opens | HIGH-risk components with no disable path make rollback expensive and slow |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Gather release scope and method** — Collect the complete component list, the deployment method, and the environments in the promotion path. Confirm which sandboxes ran full deployment validation and whether each sandbox matched production metadata at validation time.

2. **Classify each component** — Apply the HIGH / MEDIUM / LOW criteria to every component in the release. Document the classification and the specific risk indicator that drove the rating. Flag any component whose classification cannot be confirmed due to missing information.

3. **Identify rollback assets** — For org-based deployments, confirm a pre-retrieve backup was taken before the window. For packaged releases, note the prior version number. For any HIGH-risk component, confirm whether a destructive change file or feature flag disable path exists.

4. **Author the rollback plan** — Write explicit trigger conditions (observable and measurable), name the decision authority and alternate, and document the exact rollback procedure with estimated time. Do not accept "roll back if something is broken" as a trigger condition.

5. **Confirm people readiness** — Verify that the release manager, rollback authority, and technical executor are available for the full release window and the monitoring period afterward. Document alternates for each role.

6. **Produce the go/no-go checklist** — Summarize the risk level, outstanding gaps, rollback plan status, and people readiness. Require explicit sign-off before the window opens.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Every component in the release scope has a HIGH / MEDIUM / LOW classification with documented rationale
- [ ] Rollback trigger conditions are observable and measurable, not subjective
- [ ] Rollback decision authority is named as an individual plus alternate, not a role or team
- [ ] Rollback procedure is documented with estimated execution time and post-rollback smoke test
- [ ] For org-based deployments: pre-retrieve backup confirmed before the window opens
- [ ] For packaged deployments: prior package version number is recorded and accessible
- [ ] Any HIGH-risk component without a feature flag has a tested destructive change file prepared
- [ ] All required personnel are confirmed reachable for the release window and monitoring period

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **No native rollback or undo button exists in Salesforce Setup** — There is no "undo deployment" feature in the platform. When a component is deployed it overwrites the prior state. Rollback is always a deliberate re-deployment of the prior version, destructive change, or package install. This is one of the most common false assumptions practitioners and LLMs make about the platform.

2. **Change Set rollback requires manually building the reverse set** — Unlike source-controlled CLI deployments, Change Sets do not retain the prior metadata state. If a Change Set deployment must be rolled back, a practitioner must manually construct a new Change Set containing the prior version of each affected component — which requires the prior version to have been captured before deployment.

3. **Unlocked package rollback restores metadata but not data side effects** — Redeploying a prior unlocked package version restores code and configuration but does not revert data changes made by the newer version such as field population or records created by new automation. Rollback of packaged releases must account for data side effects separately.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Risk-classified component inventory | Table of all release components with HIGH / MEDIUM / LOW rating and the specific risk indicator driving each rating |
| Rollback plan | Observable trigger conditions, named decision authority and alternate, exact rollback steps, estimated execution time, and post-rollback smoke test |
| Pre-deployment checklist | People, process, and technology readiness gates to pass before the window opens |
| Go/no-go summary | One-page release readiness summary for release manager sign-off |

---

## Related Skills

- change-management-and-deployment — Use for selecting the deployment method, building the release plan, and executing the deployment; this skill focuses on pre-deployment risk classification
- devops/deployment-monitoring — Use to monitor deployment execution and detect failure signals in real time after the window opens
- devops/deployment-error-troubleshooting — Use when a deployment has already failed and root cause diagnosis is needed
- devops/environment-strategy — Use to evaluate whether the promotion path provides sufficient risk isolation before classification begins
- admin/devops-process-documentation — Use to document the full release process including the risk assessment procedure for repeatable team execution
