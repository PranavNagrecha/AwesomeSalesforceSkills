---
name: salesforce-release-preparation
description: "Use when preparing for a Salesforce seasonal release — triaging release notes, reviewing Release Updates, opting into Sandbox Preview, and communicating change impact to stakeholders. Triggers: 'upcoming Salesforce release', 'release notes triage', 'Release Updates', 'sandbox preview opt-in', 'release readiness checklist', 'production upgrade date', 'feature impact', 'critical update'. NOT for deploying org-specific changes between sandboxes (use change-management-and-deployment), nor for long-term sandbox environment design (use sandbox-strategy)."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Reliability
tags:
  - release-preparation
  - release-readiness
  - release-updates
  - sandbox-preview
  - stakeholder-communication
  - seasonal-release
inputs:
  - "Target release name (e.g. Summer '25, Winter '26)"
  - "Org edition and enabled feature areas (Sales Cloud, Service Cloud, Flow, Apex, etc.)"
  - "List of active automations, Apex code, integrations, and critical business processes"
  - "Sandbox inventory and which sandboxes are candidates for preview opt-in"
  - "Stakeholder communication responsibilities and cadence"
outputs:
  - "Prioritized release notes triage list filtered by Feature Impact and relevant feature areas"
  - "Release Updates action plan: auto-activated vs. toggle-on items, enforcement deadlines"
  - "Sandbox Preview opt-in plan per sandbox with rationale"
  - "Stakeholder communication brief summarizing material changes and recommended admin actions"
  - "Release readiness checklist ready for sign-off"
triggers:
  - upcoming Salesforce release preparation checklist
  - how do I triage release notes for my org
  - sandbox preview opt-in before production upgrade
  - which Release Updates need action before enforcement
  - communicating Salesforce upgrade impact to stakeholders
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-06
---

# Salesforce Release Preparation

This skill activates when a Salesforce admin needs to systematically prepare the org and stakeholders for an upcoming Salesforce seasonal release — covering release notes triage, Release Updates review, Sandbox Preview enrollment, and stakeholder communication. It produces a structured action plan rather than relying on ad hoc last-minute review.

---

## Before Starting

Check for `salesforce-context.md` in the project root. If present, read it first. Only ask for information not already covered there.

Gather if not available:
- Which release is approaching and what is the production upgrade date for this org's instance? (Check trust.salesforce.com or Setup > Release Updates for the instance-specific schedule.)
- Which Salesforce feature areas are actively in use? (Apex, Flow, Lightning Experience, OmniStudio, Commerce, etc. — Release Updates vary by feature area.)
- Are there any Release Updates currently showing as "Activated" or "Scheduled for Auto-Activation" that the team has not reviewed?
- Is there at least one sandbox with no dependency on auto-refresh timing that can be opted into Sandbox Preview?
- Who are the stakeholders who need communication — end users, managers, IT, integrations owners?

---

## Core Concepts

### Salesforce Seasonal Release Schedule

Salesforce delivers three major releases per year: Spring (February), Summer (June), and Winter (October). The exact upgrade date for each org instance is published on trust.salesforce.com under the planned maintenance calendar. Production orgs in different NA, EU, or APAC instances upgrade on different weekends within the same release window. Sandboxes in the preview window upgrade first — typically four to six weeks before production.

### Sandbox Preview Opt-In

Sandbox Preview is a per-sandbox, per-release opt-in that upgrades that sandbox to the upcoming release before production receives it. Enrollment is done in Setup > Sandboxes during the published preview enrollment window. Not all sandbox types qualify every release; Salesforce publishes which types are eligible each cycle. Opting in is irreversible for that sandbox during the release cycle — the sandbox cannot be rolled back to the previous release after the preview upgrade runs. Salesforce Knowledge Article 000391927 documents the step-by-step enrollment process and eligibility criteria. The preview window closes on a published date; after that, the sandbox upgrades with production.

### Release Updates

Release Updates (formerly Critical Updates) are targeted behavior changes that Salesforce intends to eventually enforce on all orgs. Each update has an activation status:
- **Opt-In Available**: the admin can voluntarily activate it now to test early.
- **Auto-Activation Scheduled**: Salesforce will activate it automatically on a published date unless the admin acts.
- **Enforced**: the behavior change is permanent and cannot be toggled off.

Release Updates are managed in Setup > Release Updates. Each update includes a description, an enforcement date, and a test-activation toggle. Admins should activate and test every non-enforced update in a sandbox before the auto-activation date. Allowing auto-activation without prior testing means any breakage surfaces first in production.

### Release Notes Feature Impact Triage

Salesforce publishes release notes for every release at help.salesforce.com. Release notes include a "Feature Impact" filter that classifies changes as Admin (configuration required), Developer (code changes may be needed), End User (visible behavior change), or Requires Setup (must be enabled). Using the Feature Impact filter with your feature areas as a secondary filter reduces a 300+ item document to an actionable 20–40 item triage list. The admin.salesforce.com "Be Release Ready" program mirrors Salesforce releases and provides curated admin-focused summaries alongside the full notes.

---

## Common Patterns

### Pattern: Structured Pre-Release Triage

**When to use:** 6–8 weeks before the production upgrade date, when the release notes are published and the preview window opens.

**How it works:**
1. Download or open the release notes for the upcoming release from help.salesforce.com.
2. Apply the Feature Impact filter to show only Admin, Developer, and End User items.
3. Cross-reference with the org's active feature areas to eliminate irrelevant sections.
4. For each remaining item: classify as (a) auto-activated change requiring no action, (b) toggle-on feature with a decision to make, or (c) Release Update requiring sandbox testing.
5. Assign an owner and target sandbox test date for every Release Update and every critical behavior change.
6. Update the stakeholder communication brief with a plain-language summary of end-user-visible changes.

**Why not the alternative:** Reviewing notes without a filter produces review fatigue and causes teams to miss high-impact items buried in product-specific sections they do not use.

### Pattern: Release Update Activation Cadence

**When to use:** As soon as preview notes are published, for every release cycle.

**How it works:**
1. Open Setup > Release Updates in the preview sandbox.
2. For each update not yet Enforced: read the description and enforcement date.
3. Activate the update in the preview sandbox using the "Activate" toggle.
4. Run regression tests — Apex tests, Flow tests, UAT scripts — against affected processes.
5. Fix any breakage in the sandbox before the production auto-activation date.
6. After validating all updates, activate them in production ahead of schedule to avoid surprise auto-activation.

**Why not the alternative:** Waiting for Salesforce to auto-activate updates means any breakage is a production incident with no pre-tested fix ready.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Release notes just published, no review done yet | Run the Feature Impact filter triage immediately | Structured triage prevents missed items and review fatigue |
| Release Update enforcement date is within 30 days | Activate in sandbox today, schedule production activation for after validation | Auto-activation with no prior testing is the most common source of release-related production incidents |
| Team wants to preview the release before production upgrade | Opt one sandbox into Sandbox Preview during the enrollment window | Preview gives 4–6 weeks of early exposure; do not opt in a sandbox shared with active work if the team isn't ready for the upgrade |
| No sandboxes available that can be disrupted for preview | Use a Developer sandbox refreshed specifically for preview testing | Cost of a temporary Developer sandbox is lower than production breakage |
| Stakeholders have not been told about end-user changes | Draft a plain-language change brief from the End User feature impact items | Stakeholders need adequate lead time before the production upgrade date |
| Org is on a Gov Cloud instance | Confirm the specific upgrade date from trust.salesforce.com; do not assume standard commercial dates | Gov Cloud instances upgrade on separate schedules and may have different feature availability |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Identify the upgrade date** — Look up the org's Salesforce instance on trust.salesforce.com and confirm the production upgrade date for the upcoming release. Note whether any sandboxes are eligible for preview and when the enrollment window closes.
2. **Triage the release notes** — Open the release notes for the upcoming release on help.salesforce.com. Apply the Feature Impact filter for Admin, Developer, and End User items. Cross-filter by the org's active feature areas. Output: a prioritized triage list of items requiring action or decision.
3. **Audit Release Updates** — In Setup > Release Updates (ideally in the preview sandbox if enrolled, otherwise in a Developer sandbox), review all non-Enforced updates. Note enforcement dates. Classify each as: no action needed, activate and test now, or already handled.
4. **Sandbox Preview enrollment** — If a suitable sandbox exists and the enrollment window is open, enroll it via Setup > Sandboxes following the process in Knowledge Article 000391927. Document which sandbox was enrolled and why it was chosen.
5. **Test Release Updates and behavior changes** — In the preview sandbox, activate each Release Update and run Apex tests, Flow tests, and key UAT scripts. Log any failures. Fix before the production auto-activation date.
6. **Draft stakeholder communication** — Produce a plain-language brief covering: what changes visibly for end users, what admin actions are required, and the production upgrade date. Include a go-no-go sign-off step.
7. **Production activation and sign-off** — Before the production upgrade, activate Release Updates in production (ahead of auto-activation) once sandbox validation passes. Confirm the stakeholder brief was sent. Mark the checklist complete.

---

## Review Checklist

Run through these before marking release preparation complete:

- [ ] Production upgrade date confirmed from trust.salesforce.com for the org's specific instance
- [ ] Release notes triaged using Feature Impact filter for Admin, Developer, and End User items
- [ ] All Release Updates in Setup > Release Updates reviewed; enforcement dates logged
- [ ] Each Release Update activated and tested in a sandbox; no unresolved Apex test failures
- [ ] At least one sandbox enrolled in Sandbox Preview (or documented reason for skipping)
- [ ] Stakeholder communication brief drafted and approved by release sponsor
- [ ] Production activation of Release Updates scheduled for before auto-activation deadline
- [ ] Post-upgrade monitoring plan in place for the 48 hours following production upgrade

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Sandbox Preview opt-in is irreversible** — Once a sandbox is enrolled in preview and the upgrade runs, it cannot be rolled back to the prior release version. Enrolling a sandbox that development teams depend on mid-sprint will strand them on the new release version before the org is ready.
2. **Release Update auto-activation happens silently in production** — Salesforce does not send a banner warning to users when an auto-activation fires. If the admin missed the enforcement date and the update activates automatically, production behavior changes without any notification. The only indication is the update moving to "Enforced" status in Setup > Release Updates.
3. **Gov Cloud instance upgrade schedules are different** — US Government Cloud instances (USALX, USG, etc.) upgrade on separate maintenance windows from commercial instances. Assuming the same upgrade weekend as a commercial instance will result in missed preparation windows.
4. **The Feature Impact filter does not replace reading the detail** — Release notes items tagged "Admin" may still require developer action if the configuration change touches Apex, Flow formulas, or custom metadata. Reading only the summary without the detail leads to incomplete impact assessment.
5. **Sandbox enrollment window closes before production upgrade** — The preview enrollment window typically closes one to two weeks before the sandbox preview upgrade runs. Missing the enrollment window means the next opportunity is when production upgrades. Do not wait until the week of the upgrade to plan enrollment.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Release Notes Triage List | Filtered, prioritized list of items requiring admin action or decision, organized by impact type |
| Release Updates Action Plan | Table of all non-Enforced Release Updates with activation status, enforcement date, assigned owner, and test status |
| Sandbox Preview Enrollment Record | Which sandbox was enrolled, rationale, enrollment date, and post-upgrade test plan |
| Stakeholder Communication Brief | Plain-language summary of end-user-visible changes, admin actions required, and production upgrade date |
| Release Readiness Checklist | Completed sign-off checklist confirming all preparation steps done before production upgrade |

---

## Related Skills

- **admin/sandbox-strategy** — Use when choosing which sandbox types to maintain for release testing or designing the overall environment topology. NOT for managing the release preparation process itself.
- **admin/change-management-and-deployment** — Use when promoting org-specific configuration and code changes between environments as part of a release. NOT for managing Salesforce seasonal release readiness.
- **admin/change-management-and-training** — Use when the stakeholder communication and training plan for a release is the primary deliverable. NOT for technical release notes triage or Release Updates management.
