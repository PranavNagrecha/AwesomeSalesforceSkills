---
name: salesforce-release-preparation
description: "Use when preparing for a Salesforce seasonal release — triaging release notes, reviewing Release Updates, opting into Sandbox Preview, and communicating change impact to stakeholders. Triggers: 'upcoming Salesforce release', 'release notes triage', 'Release Updates', 'sandbox preview opt-in', 'release readiness checklist', 'production upgrade date', 'feature impact', 'critical update', 'roll out the Spring release safely', 'is our org ready for the Spring release', 'release update settings metadata', 'FlowSettings release update field', 'release run sheet', 'preview sandbox refresh freeze', 'settings deploy flipped a release update'. Also covers: which Release Updates are deployable as Settings metadata, the release run sheet artefact, and the preview opt-in refresh-date rule. NOT for planning your own release train — use devops/release-management. NOT for user training and go-live comms — use admin/change-management-and-training."
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
  - "upcoming Salesforce release preparation checklist"
  - "how do I triage release notes for my org"
  - "sandbox preview opt-in before production upgrade"
  - "which Release Updates need action before enforcement"
  - "communicating Salesforce upgrade impact to stakeholders"
  - "OmniStudio standard runtime vs managed package upgrade calendar"
  - "a Release Update auto-activated in production and nobody noticed"
  - "which Release Updates can I deploy as metadata instead of clicking in Setup"
  - "settings deploy turned a release update on by accident"
  - "the settings file says false but the release update is already enforced"
  - "MyDomainSettings field ignores the value I deploy"
  - "picked the wrong sandbox for preview and now it is stuck on the new release"
  - "which sandbox should we opt into Sandbox Preview"
  - "flows broke after the seasonal upgrade"
  - "Apex tests fail only in the preview sandbox"
  - "enforcement date moved and we closed the item too early"
  - "old Apex class did not pick up the new release behaviour"
  - "put our release update posture into source control"
  - "build a release run sheet for the Winter release"
  - "what breaks when the org upgrades this weekend"
dependencies: []
version: 1.1.0
author: Pranav Nagrecha
updated: 2026-09-04
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

## Questions to Ask Before Configuring

Ask these before opening the release notes. The answers decide whether the cycle produces a reviewable artefact or a folder of screenshots, and each one traces to a way this goes wrong in `references/gotchas.md`.

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "Which pending Release Updates are also a field on a `Settings` type we already deploy?" | Those updates move on deploy, not only in Setup, so a settings file review is a release-update review whether anyone framed it that way (Gotcha 9) | The `metadata_backed` column of the run sheet, and a settings `package.xml` scoped to just those types |
| "Which sandbox can we lose for the whole cycle, and when is it next due a refresh?" | Preview opt-in cannot be undone for the cycle and the only exit is a refresh, whose floor differs by type (Gotchas 1 and 11) | A named preview sandbox with a refresh freeze date, not a sandbox chosen by prestige |
| "What does Setup > Release Updates say *this* cycle — not what we logged last cycle?" | Enforcement releases get postponed, and a postponed update is the one the team has rehearsed ignoring (Gotcha 6) | An `enforcement_release` re-read this cycle, and postponed items still open rather than closed |
| "How many distinct Apex API versions are pinned across the codebase?" | A pinned class keeps the semantics it was saved with after the org upgrades, so 'the org upgraded' and 'this class changed' are different events (Gotcha 12) | A per-version list of skipped behaviour changes on the regression checklist |
| "Which behaviour changes this release have no toggle in Setup at all?" | Salesforce enables some changes progressively with no Release Update entry, so the Setup list is necessary but not sufficient (Gotcha 7) | Rows marked `metadata_backed: false` with a reason, instead of a silent gap |
| "Who reviews a diff on a `.settings` file, and do they know what those booleans do?" | An enforced update's field can read `false` forever and ignore what you set, so a settings diff is not self-explanatory (Gotcha 10) | A named reviewer, and inert fields annotated rather than re-investigated each October |
| "For each release-notes area we actually use, who runs the regression and what do they read first?" | The Feature Impact label routes by configuration surface, not by who has to fix it (Gotcha 4) | A triage table whose every row has an owner and a `reads` skill path |

What a proper release preparation adds over just reading the notes: the org's release-update posture is a reviewed diff in source control rather than a set of checkboxes someone clicked, every pending update has an owner and an enforcement release re-read this cycle, and the preview sandbox decision is a recorded trade-off instead of whichever environment looked free.

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

Two qualifiers the status list alone does not convey:

- **The enforcement release can move.** When adoption lags, Salesforce postpones enforcement by a cycle — "Restrict User Access to Run Flows" was scheduled for Winter '25 and was enforced in Winter '26. Re-read the enforcement release from Setup > Release Updates every cycle instead of carrying forward the date logged last time, and keep postponed updates on the checklist as "re-confirm next cycle" rather than closing them.
- **Not every behavior change is gated by a Release Update.** Salesforce also enables changes progressively across all orgs with no toggle anywhere in Setup, opening a Release Update only for the part it cannot change unilaterally — in the case below, behavior originating from Apex and flows. Release Updates triage is necessary but not sufficient; the release notes still have to be read. See `references/gotchas.md` Gotcha 7 for the asynchronous sharing recalculation case.

Release Updates are managed in Setup > Release Updates. Each update includes a description, an enforcement date, and a test-activation toggle. Admins should activate and test every non-enforced update in a sandbox before the auto-activation date. Allowing auto-activation without prior testing means any breakage surfaces first in production.

### What Part of a Release Update Is Actually Metadata

Setup > Release Updates is a screen, not a metadata type — there is no `ReleaseUpdate` object in the Object Reference and no `ReleaseUpdate` component in the Metadata API. But a large share of individual updates *are* source-controllable, because the org's on/off state for them lives on a boolean field of an org `Settings` type whose description in the Metadata API Developer Guide names the update outright.

| Settings type | Deployed as | Example field | Corresponds to |
|---|---|---|---|
| `FlowSettings` | `Flow.settings` (api_meta.txt L116823) | `doesEnforceApexCpuTimeLimit` | Accurately Measure the CPU Time Consumption of Flows and Processes (L116849–116853) |
| `FlowSettings` | as above | `isTimeResumedInSameRunContext` | Make Paused Flow Interviews Resume in the Same Context with the Same User Access (L117048–117054) |
| `ApexSettings` | `Apex.settings` (api_meta.txt L110701) | `enableAuraApexCtrlGuestUserAccessCheckPref` | Restrict Access to `@AuraEnabled` Apex Methods for Guest and Portal Users Based on User Profile (L110753–110758) |
| `LightningExperienceSettings` | `.settings` in the settings folder (L121340–121343) | `enableStackedModalManagerEnabled` | Enable LWC Stacked Modals (L121509–121514) |
| `MyDomainSettings` | `MyDomain.settings` (api_meta.txt L122095) | `useStabilizedSandboxMyDomainHostnames` | Stabilize the Hostname for My Domain URLs in Sandboxes — **inert**, always `true` as of API 49.0 (L122427–122440) |

Three consequences drive the whole workflow below:

- **The posture is auditable.** Retrieve those types and the org's release-update stance becomes a diff a second person can review, not a screen someone remembers clicking. `references/worked-examples.md` §4–6 has the deployable files, the manifest and the retrieve commands.
- **The posture is also accidentally mutable.** A settings file carried along by a pipeline moves release updates on deploy. See `references/gotchas.md` Gotcha 9.
- **Not every update is in there.** Some are Setup-only, and some behaviour changes ship with no toggle at all. Run the full inventory (`grep -n -i "release update" api_meta.txt`) rather than assuming a field exists for the update in front of you; record the ones that have none, with a reason.

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

Seven steps, in order. Each names the file it produces or reads and the command that checks it.

1. **Open the run sheet and fix the two dates.** Copy the `release_run_sheet` and `preview_sandbox` blocks from `references/worked-examples.md` §1 into `release-run-sheet.yaml`. Fill `production_upgrade_date` from the org's *instance* on trust.salesforce.com — not the release calendar headline (`references/gotchas.md` Gotcha 3) — and set `refresh_freeze_from` for whichever sandbox you opt in, using the refresh-floor table in `references/worked-examples.md` §3 (Gotcha 11).
2. **Snapshot the org's current release-update posture.** Run the retrieve in `references/worked-examples.md` §6 against production with `manifest/release-updates-package.xml` (§5). Do not use a `Settings` wildcard — it pulls every settings type and buries the four you care about. Commit the retrieved `.settings` files; that commit is your baseline diff.
3. **Build the Release Updates inventory.** Read Setup > Release Updates in the target org this cycle, one row per update. For each, decide `metadata_backed`: true only if you can quote the Metadata API guide sentence tying a Settings field to that update — the inventory is embedded in `scripts/check_salesforce_release_preparation.py` (`RELEASE_UPDATE_SETTINGS`). Everything else is `metadata_backed: false` with a `not_in_metadata_reason` (Gotcha 7).
4. **Triage the release notes into owners.** Apply the Feature Impact filter, then route each surviving item through the area → skill table in `references/worked-examples.md` §2. Put the skill path in the row's `reads`. An Admin-labelled item that mentions Apex, LWC, API version or an integration gets a developer co-owner regardless of the label (Gotcha 4).
5. **Lint the run sheet, then test in the preview sandbox.** Run `python3 scripts/check_salesforce_release_preparation.py --file release-run-sheet.yaml --repo-root .` — it rejects unknown Settings types, uncited metadata-backed rows, ownerless rows, duplicate ids, and inert fields marked as active work. Then deploy the §4 settings files to the preview sandbox (`--dry-run` first), run the full Apex test suite against the pre-upgrade baseline, and work the checklist in `references/worked-examples.md` §7.
6. **Scan the source tree for what the upgrade will surface.** Run `python3 scripts/check_salesforce_release_preparation.py --manifest-dir force-app/main/default`. It flags settings files that will move a release update on deploy, literal null comparisons in Flow decisions, active Flows with no fault connector, unannotated Schedulable Apex, and the spread of pinned Apex API versions — a pinned class does not pick up the release's behaviour changes (Gotcha 12).
7. **Activate deliberately, then sign off.** Deploy the reviewed settings diff to production ahead of any auto-activation date, activate Setup-only updates by hand, and send the stakeholder brief from `templates/salesforce-release-preparation-template.md`. Re-run step 2's retrieve into a fresh directory and confirm each field reads back as set; a field that reads back inverted is usually an already-enforced inert field, not a failed deploy (Gotcha 10). Leave postponed updates open with status `postponed`, never `complete`.

---

## Review Checklist

Run through these before marking release preparation complete:

- [ ] Production upgrade date confirmed from trust.salesforce.com for the org's specific instance
- [ ] Release notes triaged using Feature Impact filter for Admin, Developer, and End User items
- [ ] All Release Updates in Setup > Release Updates reviewed; enforcement dates logged
- [ ] Enforcement release re-confirmed this cycle for every pending Release Update, including any carried over from a prior cycle (published enforcement releases get postponed)
- [ ] Each Release Update activated and tested in a sandbox; no unresolved Apex test failures
- [ ] At least one sandbox enrolled in Sandbox Preview (or documented reason for skipping)
- [ ] Stakeholder communication brief drafted and approved by release sponsor
- [ ] Production activation of Release Updates scheduled for before auto-activation deadline
- [ ] `release-run-sheet.yaml` lints clean: `python3 scripts/check_salesforce_release_preparation.py --file release-run-sheet.yaml --repo-root .`
- [ ] Source tree scanned: `python3 scripts/check_salesforce_release_preparation.py --manifest-dir force-app/main/default`
- [ ] Every metadata-backed Release Update row carries a `settings_type`, a `settings_field` and a guide citation
- [ ] Settings diff between production and the preview sandbox reviewed by a second person and committed
- [ ] Preview sandbox refresh frozen from the preview cutover to the production upgrade, and the freeze date recorded
- [ ] Distinct pinned Apex API versions listed, with the versioned behaviour changes each one skips
- [ ] Post-upgrade monitoring plan in place for the 48 hours following production upgrade

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Sandbox Preview opt-in is irreversible** — Once a sandbox is enrolled in preview and the upgrade runs, it cannot be rolled back to the prior release version. Enrolling a sandbox that development teams depend on mid-sprint will strand them on the new release version before the org is ready.
2. **Release Update auto-activation happens silently in production** — Salesforce does not send a banner warning to users when an auto-activation fires. If the admin missed the enforcement date and the update activates automatically, production behavior changes without any notification. The only indication is the update moving to "Enforced" status in Setup > Release Updates.
3. **Gov Cloud instance upgrade schedules are different** — US Government Cloud instances (USALX, USG, etc.) upgrade on separate maintenance windows from commercial instances. Assuming the same upgrade weekend as a commercial instance will result in missed preparation windows.
4. **The Feature Impact filter does not replace reading the detail** — Release notes items tagged "Admin" may still require developer action if the configuration change touches Apex, Flow formulas, or custom metadata. Reading only the summary without the detail leads to incomplete impact assessment.
5. **Sandbox enrollment window closes before production upgrade** — The preview enrollment window typically closes one to two weeks before the sandbox preview upgrade runs. UNVERIFIED (2026-09-04): neither this interval nor any Sandbox Preview window length appears in the Metadata API, Object Reference or Apex Developer guides; read the current dates from the Sandbox Preview Knowledge Article and trust.salesforce.com each cycle. Missing the enrollment window means the next opportunity is when production upgrades. Do not wait until the week of the upgrade to plan enrollment.
6. **A settings deploy can move a Release Update** — `Flow.settings`, `Apex.settings` and friends carry booleans whose guide description names the update they correspond to, so a routine settings deploy changes release-update posture. Full case and the reverse failure (a sandbox snapshot silently reverting an admin's Setup change) in `references/gotchas.md` Gotcha 9.
7. **An enforced update's field goes inert, not away** — `MyDomainSettings.useStabilizedSandboxMyDomainHostnames` reads `false` and ignores what you deploy, because the update behind it was enforced in Summer '20. A retrieved settings file answers "what is stored," not "what is enforced." `references/gotchas.md` Gotcha 10.
8. **Refresh cadence, not prestige, picks the preview sandbox** — opt-in is irreversible for the cycle and the only exit is a refresh, so the type with the longest refresh floor is the worst candidate. A mid-cycle refresh also silently discards the preview. `references/gotchas.md` Gotcha 11, with the floors in `admin/sandbox-strategy`.
9. **The org upgrading is not the same event as a pinned class changing** — a class saved at an older API version keeps that version's semantics after the upgrade, so a green regression proves nothing about the day someone bumps it. `references/gotchas.md` Gotcha 12.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Release Notes Triage List | Filtered, prioritized list of items requiring admin action or decision, organized by impact type |
| Release Updates Action Plan | Table of all non-Enforced Release Updates with activation status, enforcement date, assigned owner, and test status |
| Sandbox Preview Enrollment Record | Which sandbox was enrolled, rationale, enrollment date, and post-upgrade test plan |
| Stakeholder Communication Brief | Plain-language summary of end-user-visible changes, admin actions required, and production upgrade date |
| Release Run Sheet (`release-run-sheet.yaml`) | Machine-checkable record of the cycle: header, preview decision, and one row per Release Update with owner, enforcement release, status, and metadata grounding. Shape in `references/worked-examples.md` §1 |
| Release-Update Settings Files + `package.xml` | Deployable `.settings` files and a scoped manifest putting the org's release-update posture under source control. `references/worked-examples.md` §4–5 |
| Release Readiness Checklist | Completed sign-off checklist confirming all preparation steps done before production upgrade |

---

## Reference Files

| File | Read it when |
|---|---|
| `references/worked-examples.md` | Running the cycle. Holds the run-sheet YAML, the three deployable Settings XML files, `package.xml`, the retrieve/deploy commands, the release-notes triage table and the regression checklist. |
| `references/gotchas.md` | Before deploying a `.settings` file, before choosing a preview sandbox, or when a retrieved field disagrees with Setup. Twelve platform behaviours, each with what happens / when it occurs / how to avoid. |
| `references/examples.md` | Three narrated cases — catching a Release Update before auto-activation, triaging a 340-item note set across three admins, and finding an LWC regression in a preview sandbox — plus the deferred-review anti-pattern. |
| `references/well-architected.md` | Justifying the cycle's cost, choosing preview sandbox tier vs fidelity, or citing the sources behind any claim in this package. |
| `references/llm-anti-patterns.md` | Reviewing output an AI assistant produced about a release — invented upgrade dates, toggle-off-forever advice, and the rest. |
| `templates/salesforce-release-preparation-template.md` | Running the cycle by hand or writing the stakeholder brief; the human-readable counterpart to the run-sheet YAML. |
| `scripts/check_salesforce_release_preparation.py` | Linting `release-run-sheet.yaml` (`--file`) or scanning a metadata source tree (`--manifest-dir`). Also the embedded inventory of which Settings fields the guide ties to a named Release Update. |

---

## Related Skills

- **admin/sandbox-strategy** — Use when choosing which sandbox types to maintain for release testing or designing the overall environment topology. NOT for managing the release preparation process itself.
- **admin/change-management-and-deployment** — Use when promoting org-specific configuration and code changes between environments as part of a release. NOT for managing Salesforce seasonal release readiness.
- **admin/change-management-and-training** — Use when the stakeholder communication and training plan for a release is the primary deliverable. NOT for technical release notes triage or Release Updates management.
- **devops/release-management** — Use when planning your own release train, branching model, and deployment cadence. NOT for preparing the org for Salesforce's seasonal upgrade.
- **devops/sandbox-refresh-and-templates** — Use when a sandbox refresh is part of the cycle and post-copy automation, seeding, or templates need to be re-verified. NOT for deciding which sandbox to opt into preview.
- **integration/api-versioning-strategy** — Use when the release exposes an API version spread and the question is which versions to consolidate to. NOT for the release preparation cycle itself.
