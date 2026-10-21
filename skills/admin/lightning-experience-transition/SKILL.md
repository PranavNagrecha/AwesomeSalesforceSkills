---
name: lightning-experience-transition
description: "Use when planning, sequencing, or troubleshooting an org-wide migration from Salesforce Classic to Lightning Experience. Covers the LEX Transition Assistant Readiness Check, asset triage matrix (Visualforce, JavaScript buttons, page layouts, Knowledge, email templates, list views, AppExchange), pilot/wave rollout sequencing, end-user adoption telemetry, and cutover criteria. Triggers: 'lightning experience transition', 'classic to lightning migration plan', 'LEX readiness check', 'why are some users still on Classic', 'turning on Lightning for everyone'. NOT for individual asset migrations like a single VF page (use lwc/visualforce-to-lwc-migration), a single JavaScript button (use admin/custom-button-to-action-migration), or Knowledge article migration (use admin/knowledge-classic-to-lightning) — this skill orchestrates the program. NOT for Lightning App Builder page design (use admin/lightning-app-builder-advanced)."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Reliability
  - User Experience
tags:
  - lightning-experience
  - lex-transition
  - classic-migration
  - readiness-check
  - transition-assistant
  - adoption
  - change-management
  - visualforce
  - permission-set
triggers:
  - "we still have a few hundred users in Salesforce Classic and need a plan to move them"
  - "running the Lightning Experience Transition Assistant Readiness Check before turning LEX on"
  - "users keep switching back to Classic — what does our migration plan need to cover"
  - "do I migrate Visualforce pages, JavaScript buttons, and Knowledge before or after enabling Lightning"
  - "how do we sequence a wave-based rollout of Lightning Experience across business units"
inputs:
  - "Output of the Lightning Experience Transition Assistant Readiness Check (PDF or org-pinned report)"
  - "User segmentation by profile, role, region, or business unit"
  - "Inventory of legacy assets: Visualforce pages, JavaScript buttons, on-click S-controls, Console apps, customized page layouts, Email Templates, Letterheads, Knowledge articles in Classic format"
  - "Currently installed AppExchange packages and their LEX-ready status"
  - "License footprint and whether Lightning is enabled at the org-default level"
outputs:
  - "Phased migration plan with wave dates, scope, success criteria, and rollback trigger"
  - "Asset triage matrix classifying every legacy asset as Replace, Rebuild, Retain (LEX-compatible), or Retire"
  - "Permission-set-driven cohort plan mapping users to waves"
  - "Adoption telemetry plan citing the LightningUsageByAppTypeMetrics and LightningExitByPageMetrics objects"
  - "Cutover playbook with go/no-go gates and rollback path"
dependencies: []
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-10-20
---

# Lightning Experience Transition

This skill activates when a practitioner is planning, sequencing, or troubleshooting the **org-wide program** to move users from Salesforce Classic to Lightning Experience. It does not duplicate piece-skills for individual asset migrations (Visualforce, JavaScript buttons, Knowledge, email templates) — it sits above them and provides the orchestration layer: readiness scoring, asset triage, wave sequencing, adoption telemetry, and cutover gates. Use it when the question is "how do we run this program," not "how do I migrate this one asset."

---

## Before Starting

Gather this context before working on anything in this domain:

- The Lightning Experience Transition Assistant and the Lightning Experience Readiness Report are named platform features (`UserEngagementSettings`, api_meta 264 L131557-131558, L131696-131702). The Readiness Check is the canonical starting point — every program plan should reference its scored output, not opinions about "what's blocking us." UNVERIFIED (2026-10-20): the Setup path and the report's contents are Help-only.
- Lightning is **on by default** for orgs created after Winter '20 (UNVERIFIED (2026-10-20): Help-only). The transition program is therefore mostly about (a) the long tail of legacy orgs that still have Classic users and (b) ensuring assets render correctly in LEX. Confirm which case applies before proposing a plan.
- A common cause of failed transitions is users **switching back to Classic** because a workflow they rely on (a JavaScript button, a custom VF page in a related list, a print-friendly Console layout) does not work in LEX. Plan asset triage **before** turning Lightning on at the profile level.
- JavaScript buttons (`WebLink` `linkType` `javascript`, api_meta 264 L47926-47931) are not supported in Lightning Experience and are not auto-migrated (UNVERIFIED (2026-10-20): Help-only). They must be replaced with Quick Actions, Lightning Component actions, headless flows, or `invocable` Apex actions before users can rely on them in LEX.
- Permission Set-based gradual rollout is the safest sequencing strategy: assign the **Lightning Experience User** permission via permission sets keyed to user cohorts (UNVERIFIED (2026-10-20): the permission name is Help-only), rather than flipping the org-wide switch — `enableLexEndUsersNoSwitching` / `enableUsersAreLightningOnly` in `LightningExperienceSettings`, which "removes the Switcher for all users in the org" (api_meta 264 L124742-124756, L124831-124835).

## Questions to Ask Before Configuring

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| Which JavaScript buttons do the cohort's pages carry? | JS buttons do nothing in LEX (Gotcha 1) | A replacement per button before its wave |
| How many users have the Classic preference set today? | The per-user preference survives profile changes (Gotcha 2) | A reset plan per cohort |
| Does any team work in a Classic Console app? | Console apps need a Lightning rebuild (Gotcha 3) | A Lightning Console track in the plan |
| Which managed packages does each cohort use? | "Lightning Ready" is not feature parity (Gotcha 4) | A workflow walkthrough per package |
| Which Visualforce pages touch `window.parent` or the URL hash? | VF runs in a different frame in LEX (Gotcha 5) | A test list before the wave |
| When was the Readiness Check last run? | It is a snapshot (Gotcha 6) | A re-run before every wave |
| Will telemetry be read in production? | The Lightning usage metrics objects are not available in sandbox orgs (Core Concepts) | Go/no-go gates measured where data exists |

UNVERIFIED (2026-10-20): rows 1, 2, 4, 5 and 6 restate Help-only behaviour (JS buttons in LEX, preference precedence, "Lightning Ready" semantics, VF framing, Readiness Check scope); row 7 is obj 264 L170640.

A proper configuration adds per-cohort gates measured against real telemetry, where "just turning Lightning on" surfaces every triage miss at once.

---

## Core Concepts

### The Readiness Check Is The Plan's Backbone

The Lightning Experience Transition Assistant runs a **Readiness Check** that scans the org for assets and configurations that affect LEX rollout: Visualforce pages with `<apex:page>` features incompatible with LEX rendering, JavaScript buttons, Lightning-incompatible AppExchange packages, custom Console apps, hard pinning to Classic via `UserPreferencesLightningExperiencePreferred`, and unmigrated Knowledge articles.

The output ships as a PDF and is also surfaced in the Transition Assistant UI. UNVERIFIED (2026-10-20): the scan's coverage and output format are Help-only. **Treat the Readiness Check report as the single source of truth for asset count and LEX-blocker classification.** Do not start the program by inventorying assets manually — let the Readiness Check do that scan and use its output as the input to triage.

### Asset Triage: Replace / Rebuild / Retain / Retire

Every legacy asset surfaced by the Readiness Check must be sorted into one of four buckets:

| Bucket | When it applies | What to do |
|---|---|---|
| Replace | A Lightning-native equivalent exists (JS button → Quick Action; Classic email template → Lightning Experience template, `UiType` `SFX`, api_meta 264 L59147-59152) | Build the replacement, validate, then disable the old asset |
| Rebuild | Needed but cannot be 1:1 replaced (VF + JS Console layout → LWC + flow + utility-bar combo) | Re-architect; ship before the wave that uses it |
| Retain | Asset already works in LEX (most page layouts, validation rules, workflow rules, standard Apex) | Confirm in Readiness Check; no change required |
| Retire | Asset is dead (Last Used > 12 months; not in any active workflow) | Delete; do not migrate dead assets |

The triage matrix is the program's working artifact. It enumerates every asset, its bucket, owner, target wave, and acceptance criteria.

### Wave-Based Rollout Via Permission Sets

Flipping the org-wide switch (`enableLexEndUsersNoSwitching` / `enableUsersAreLightningOnly`, api_meta 264 L124742-124756, L124831-124835) is the final cutover, not the first move. The gradual approach uses two permission sets (UNVERIFIED (2026-10-20): both permission names below are Help-only):

- **Lightning Experience User** (or a copy named for your program) — grants `Lightning Experience User` permission, which lets users opt into LEX.
- **Lightning Experience Hides Classic Switcher** (or your equivalent) — removes the "Switch to Salesforce Classic" link from the user menu, locking the cohort into LEX.

A typical wave plan: Wave 0 (pilot — IT, super-users, internal volunteers) → Wave 1 (a low-risk business unit with no JS buttons or VF dependencies) → Wave N (the high-customization unit with the most legacy assets) → Cutover (org-wide switch + remove Classic). Each wave has go/no-go criteria measured against adoption telemetry.

### Adoption Telemetry Is Object-Backed

The platform exposes adoption metrics via standard objects, not just dashboards:

- `LightningUsageByAppTypeMetrics` — "number of users on Lightning Experience and Salesforce Mobile", by `AppExperience` and `MetricsDate` (obj 264 L170406-170443)
- `LightningUsageByPageMetrics` — "standard pages users viewed most frequently in Lightning Experience", with `PageName` and `TotalCount` (L170514-170515, L170540-170552)
- `LightningExitByPageMetrics` — "the standard pages within which users switched from Lightning Experience to Salesforce Classic", with `PageName`, `RecordCount`, `UserId` (L170630-170670) — the most actionable signal in the program

All three are query-only and "Not available in sandbox orgs" (L170415, L170523, L170640) — a sandbox pilot produces no telemetry.

`LightningExitByPageMetrics` is the program's leading indicator. A page with a high switch-back rate identifies an asset triage miss (a JS button or VF page that didn't get migrated). Investigate every page above your wave's switch-back threshold before promoting the next wave.

### The Switch-Back Trap

`UserPreferencesLightningExperiencePreferred` — "When true, redirects the user to the Lightning Experience interface" — is Create/Filter/Update, so it can be reset by DML (obj 264 L299363-299369). Users who clicked "Switch to Salesforce Classic" carry it as `false`; even after a profile-level rollout they land in Classic until you reset it or remove the switcher (UNVERIFIED (2026-10-20): the profile-versus-preference precedence is Help-only). A migration program that doesn't track switch-back preference at the user level will report a higher LEX adoption rate than reality.

---

## Common Patterns

### Pattern 1: Readiness-Check-Driven Wave Plan

**When to use:** First-time Lightning Experience Transition program for an org with > 100 users still on Classic.

**How it works:**

1. Run the Readiness Check from **Setup → Lightning Experience Transition Assistant → Discover phase**. Export the PDF; archive a copy in the program folder so you have a baseline.
2. Build the asset triage matrix from the Readiness Check output. Assign every asset a bucket (Replace / Rebuild / Retain / Retire) and an owner.
3. Segment users by profile and business unit. Identify Wave 0 candidates (IT, super-users), Wave 1 (low-customization business unit), Wave N (high-customization).
4. Map each wave's user cohort to a permission set (e.g., `LEX_Wave1_Sales`). Migration of in-scope assets must complete before the wave's permission set is assigned.
5. Establish go/no-go telemetry: switch-back rate < 5% from `LightningExitByPageMetrics`, no Sev-1 incidents in 7 days, and active LEX users / total cohort > 90% from `LightningUsageByAppTypeMetrics`.
6. Run the cutover after the final wave: assign the "Hides Classic Switcher" permission set to all production users (UNVERIFIED (2026-10-20): permission name) and (optionally) set `enableLexEndUsersNoSwitching` in `LightningExperienceSettings` (api_meta 264 L124742-124756).

**Why not the alternative:** A profile-level org-wide flip without wave validation surfaces every triage miss simultaneously and floods the help desk. Permission-set-driven waves contain blast radius and let you fix asset gaps wave by wave.

### Pattern 2: JavaScript Button Triage Sub-Program

**When to use:** The Readiness Check flags > 20 JavaScript buttons. Buttons cannot run in LEX (UNVERIFIED (2026-10-20)), so this is always blocking work.

**How it works:**

1. Pull the JavaScript button inventory from the Readiness Check output and from `WebLink` metadata with `linkType` `javascript` (api_meta 264 L47926-47931), then run `scripts/check_lightning_experience_transition.py --manifest-dir <src>`.
2. For each button, classify the action: simple field update → Quick Action; navigation → standard Lightning navigation or Web Link; bulk record action → headless flow with `invocable` Apex; complex multi-record orchestration → LWC + Apex action.
3. Build the replacement, deploy to sandbox, validate side-by-side with the JS button. Mark the button "deprecated" by removing it from page layouts after the Lightning equivalent ships.
4. The `admin/custom-button-to-action-migration` skill is the asset-level playbook for each button. This program-level skill ensures buttons are sequenced before the wave that needs them.

**Why not the alternative:** Carrying JavaScript buttons into LEX cutover guarantees user-visible breakage and switch-back. Triage them before any wave that uses them.

### Pattern 3: AppExchange Package LEX-Compatibility Audit

**When to use:** Org has 5+ installed managed packages and the Readiness Check shows mixed compatibility status.

**How it works:**

1. Pull the package inventory from Setup → Installed Packages. Cross-reference against the Readiness Check's LEX-Ready flag for each package.
2. For each non-Lightning-Ready package: contact the partner for the LEX-ready version, plan a managed-package upgrade, and validate post-upgrade in a dev/UAT sandbox.
3. For deprecated packages with no LEX-ready upgrade path: triage as Replace (find a LEX-ready alternative) or Retire (the package's functionality is not actually used).
4. Sequence package upgrades **before** the wave that depends on them, treating each upgrade as its own change with regression testing.

**Why not the alternative:** A non-LEX-ready managed package can break Lightning rendering for the entire app it ships in (UNVERIFIED (2026-10-20)). Don't roll a wave forward until every package the wave's users touch is on a Lightning-Ready version.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Greenfield org, all users already in LEX | No transition program needed; verify via `LightningUsageByAppTypeMetrics` in production and document compliance | Lightning is default-on for newer orgs (UNVERIFIED (2026-10-20): the Winter '20 cut-off is Help-only) |
| 50–500 Classic users, mixed profiles, low custom-asset count | Single-wave rollout via permission set after asset triage | Risk is low; multi-wave overhead exceeds benefit |
| > 500 Classic users, high custom-asset count, multiple BUs | Wave-based rollout (3–5 waves), each gated on switch-back-rate telemetry | Contains blast radius; lets you fix gaps wave-by-wave |
| Heavy Visualforce + JS-button customization | Asset-triage-first program — do not assign LEX User permission until replacements ship | JS buttons silently fail in LEX; users switch back (UNVERIFIED (2026-10-20)) |
| Highly regulated industry with audit requirements | Add a paper "user attestation" step before each wave; keep `LightningUsageByAppTypeMetrics` extracts as post-cutover evidence | Auditors require evidence that the migration was a controlled change |
| Org with > 50 installed packages | Run package-compatibility audit as Phase 0 before wave 1 | A single non-LEX-ready package can break the wave's apps |
| Users with `UserPreferencesLightningExperiencePreferred = false` on a Classic-disabled profile | Reset the field by User-record DML (it is updateable, obj 264 L299363-299369) or use the switcher-hiding permission | Profile-level flip alone leaves the per-user preference dominant (UNVERIFIED (2026-10-20)) |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. Verify scope: confirm the org has Classic users (`SELECT COUNT() FROM User WHERE UserPreferencesLightningExperiencePreferred = false AND IsActive = true`). If 0, no program is needed — exit with a one-line confirmation.
2. Run the Lightning Experience Transition Assistant Readiness Check. Capture the PDF and the asset counts as the baseline. If the customer cannot run the Readiness Check, build the triage matrix manually but call it out as an estimate.
3. Build the asset triage matrix. Classify every asset (Visualforce pages, JS buttons, AppExchange packages, page layouts, Knowledge, email templates) into Replace / Rebuild / Retain / Retire. Cite the asset-level skill for each Replace/Rebuild row (`lwc/visualforce-to-lwc-migration`, `admin/custom-button-to-action-migration`, etc.).
4. Define waves. Map each user cohort to a permission set, list the in-scope assets that must be migrated before the wave, and write the go/no-go telemetry threshold (typically: switch-back rate < 5%, support tickets < N per 100 users, active LEX users > 90% of cohort).
5. Execute Wave 0 (pilot) in production — the metrics objects are not available in sandboxes (obj 264 L170640). Monitor `LightningExitByPageMetrics` daily. Investigate every page above the switch-back threshold. Do not promote to Wave 1 until Wave 0 holds telemetry for 7 days.
6. Iterate waves. After every wave, refresh the asset triage matrix — usage data exposes assets that the Readiness Check missed (e.g., a VF page surfaced only by a niche workflow).
7. Cutover. Assign the "Hides Classic Switcher" permission set to all production users (UNVERIFIED (2026-10-20): permission name); optionally set `enableLexEndUsersNoSwitching` (api_meta 264 L124742-124756). Document the change in the change-management log; archive the program artifacts for audit.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Lightning Experience Transition Assistant Readiness Check has been run and the PDF is archived
- [ ] Asset triage matrix exists, every asset has a bucket, every Replace/Rebuild row has an owner and target wave
- [ ] JavaScript-button inventory is fully classified and replacements are scoped (no JS button left as "TBD" entering the wave that uses it)
- [ ] AppExchange packages are confirmed LEX-Ready or have an upgrade plan in the wave preceding their use
- [ ] Permission-set-based wave plan is defined; each wave has go/no-go telemetry with explicit thresholds
- [ ] `LightningExitByPageMetrics` is being monitored and a page-by-page action plan exists for any page above the switch-back threshold
- [ ] Switch-back-preference reset plan is in place (User-record DML on `UserPreferencesLightningExperiencePreferred`, or the switcher-hiding permission set per cohort — UNVERIFIED (2026-10-20): permission name)
- [ ] Cutover playbook exists with go/no-go gates and a documented rollback path
- [ ] Audit log capture is configured (Setup audit trail, Lightning usage metrics extracts) for post-cutover compliance evidence

---

## Salesforce-Specific Gotchas

(Detailed entries live in `references/gotchas.md`.) UNVERIFIED (2026-10-20): items 1–5 are field experience and Help-only behaviour; no corpus line states them.

1. **JavaScript buttons fail silently in LEX** — if not replaced, users click and nothing happens; they switch back to Classic to finish the workflow.
2. **The user-level Classic preference outranks profile flips** — a profile-level rollout still lands legacy users in Classic until preference is reset.
3. **Console apps require explicit Lightning Console rebuild** — Classic Service Console layouts do not auto-translate; primary tabs and subtabs must be re-modeled in the Lightning Console app.
4. **Some VF pages render in LEX but with degraded behavior** — `<apex:page>` features like custom JavaScript that manipulates the surrounding Classic chrome silently misbehave inside the LEX iframe.
5. **The Readiness Check is a snapshot, not a continuous scan** — re-run before each wave because new assets get added during the program.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Readiness Check baseline PDF | Snapshot of org's LEX readiness scan; the program's input |
| Asset triage matrix | Rows = legacy assets; cols = bucket, owner, target wave, replacement skill, acceptance criteria |
| Wave plan | Per-wave: cohort permission set, in-scope assets, go/no-go telemetry thresholds, rollback trigger |
| Cutover playbook | Final-wave runbook including LightningExitByPageMetrics monitoring, support staffing, rollback steps |
| Adoption telemetry queries | SOQL against LightningUsageByAppTypeMetrics, LightningUsageByPageMetrics, LightningExitByPageMetrics (production only) with thresholds |

---

## Related Skills

- `lwc/visualforce-to-lwc-migration` — asset-level playbook for migrating individual Visualforce pages to LWC
- `admin/custom-button-to-action-migration` — asset-level playbook for replacing JavaScript buttons with Lightning Quick Actions
- `admin/knowledge-classic-to-lightning` — Knowledge article migration (Classic Knowledge → Lightning Knowledge)
- `admin/classic-email-template-migration` — email template migration (Classic templates → Lightning HEML)
- `admin/dynamic-forms-migration` — page-layout-to-dynamic-form migration once the org is on LEX
- `admin/change-management-and-training` — adoption / training workstream that rides alongside this program
- `lwc/lwc-locker-to-lws-migration` — the parallel LWS migration program if the org has LWC components on Locker
