---
name: entitlements-and-milestones
description: "Use this skill to design, configure, and troubleshoot Salesforce Entitlement Management on Cases: entitlement processes, milestone definitions, recurrence types, milestone actions (success/warning/violation), business hours assignment, and entitlement templates. Covers the deployable EntitlementProcess / MilestoneType / EntitlementTemplate / EntitlementSettings metadata, signed timeLength time triggers, recurrenceType semantics, process versioning, and how a milestone actually completes. Trigger keywords: entitlement process, milestone, SLA timer, milestone tracker, first response SLA, time trigger, recursChained, CaseMilestone, EntitlementId, SlaProcess, stopped clock. NOT for SLA milestones on Field Service work orders — use admin/fsl-sla-configuration-requirements. NOT for time-based case escalation rules — use admin/escalation-rules. NOT for the business-hours calendar itself — use admin/business-hours-and-holidays."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
  - User Experience
tags:
  - entitlements
  - milestones
  - SLA
  - service-cloud
  - case-management
  - business-hours
triggers:
  - "how do I set up SLA milestones so agents get email alerts before a case breaches"
  - "entitlement process is configured but milestone timers are not showing on cases"
  - "how do I auto-create entitlements when a customer purchases a support product"
  - "milestone warning actions are not firing at 75 percent elapsed time"
  - "SLA clock is not pausing over the weekend even though business hours are set"
  - "deploy an entitlement process with its milestones from sandbox by metadata"
  - "milestone shows as violated even though the agent already replied to the customer"
  - "change the milestone time limit on an entitlement process that is already active"
  - "flow creates the entitlement but the milestones run on the wrong business hours"
  - "what is the difference between recursChained and recursIndependently on a milestone"
  - "find every open case that has no entitlement so no SLA is being tracked"
inputs:
  - "Support tier names and SLA commitments (e.g., Platinum 1-hour response 8-hour resolution)"
  - "Business hours schedules already configured in Setup"
  - "Whether the org sells Support products via Products and Price Books"
  - "Whether Lightning Experience or Classic is the primary UI"
  - "Whether entitlement versioning is already enabled in the target org"
  - "How each intake channel supplies the entitlement on the case"
  - "What marks each milestone complete, and who owns that automation"
outputs:
  - "Configured entitlement process with milestone definitions and action timers"
  - "Decision guidance on recurrence type, action thresholds, and business hours scope"
  - "Entitlement template strategy for automating entitlement creation"
  - "Checklist for validating live milestone timer behavior"
  - "Deployable entitlementProcesses/, milestoneTypes/, entitlementTemplates/ and settings/ metadata with package.xml"
  - "Verification SOQL for SlaProcess versions, active Entitlements and violated CaseMilestones"
  - "Version-bump plan when SLA terms change, including re-derived time-trigger offsets"
dependencies: []
version: 1.1.0
author: Pranav Nagrecha
updated: 2026-09-04
---

# Entitlements and Milestones

This skill activates when an org needs to define and enforce time-based SLA commitments on cases using Salesforce Entitlement Management. It covers the full configuration path from enabling entitlements to wiring milestone actions that fire email alerts, create tasks, or update fields when SLA thresholds are approached or breached.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm Entitlement Management is enabled: Setup > Entitlement Settings > enable Entitlements.
- Know the business hours schedules in use. Milestone timer behavior depends entirely on which business hours object is attached — process-level or milestone-level.
- Confirm whether the org uses Products & Price Books to sell support contracts. Entitlement templates attach to products, but in Lightning the attachment UI does not exist — a Flow is required to auto-apply entitlements on product purchase.
- Clarify whether SLA clocks should pause outside business hours or run 24/7. This is a common misunderstanding that causes milestone timers to fire at unexpected times.

---

## Questions to Ask Before Configuring

Ask these before opening Setup. Each one maps to a failure in `references/gotchas.md`, and an agent
that skips them ships a process that deploys cleanly and tracks nothing.

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "How does a case get its entitlement, on each intake channel we run?" | An entitlement process only ever runs on a case that carries an entitlement; Email-to-Case and Web-to-Case do not supply one (gotcha 2) | The per-channel automation list, and the fallback for cases with no account |
| "What ends the commitment — the case closing, or something we stamp ourselves?" | Exit criteria are the boundary for recurrence, so `Status = Closed` restarts every non-recurring milestone on a reopen (gotcha 9) | The exit-criteria filter, and whether reopens are new commitments |
| "Who or what marks a milestone complete?" | Nothing completes a milestone; `CaseMilestone.CompletionDate` has to be written (gotcha 8) | Either satisfiable completion criteria, or the Apex/Flow that stamps the date |
| "Which calendar wins: the process, the milestone, or the Case?" | Three calendars can disagree, and milestones read none of `Case.BusinessHoursId` by default | One named authority per SLA policy, and the milestone-level overrides written down |
| "Do we ever stop the clock, and who is allowed to?" | `Case.IsStopped` is writable by anything with edit access, and stopped time is hidden unless a setting is on (gotcha 10) | A stop policy, FLS on the field, and `enableMilestoneStoppedTime` set before go-live |
| "Is entitlement versioning on, and who owns the next version?" | The version fields do nothing until the org switch is on, and an SLA change means a new file with every time-trigger offset re-derived (gotchas 6 and 12) | The versioning switch state and a named owner for version bumps |
| "Do the same milestones serve more than one tier?" | Recurrence lives on the shared `MilestoneType`, so one edit changes every process that names it (gotcha 7) | The milestone-type-to-process map, and any type that needs splitting |

What a proper configuration adds over just building it in Setup: every intake channel actually enters
the process, the clock counts on a calendar somebody chose, milestones close because something closes
them, and next quarter's SLA change is a reviewed deploy of a new version rather than an edit whose
blast radius nobody can state.

---

## Core Concepts

### Entitlement Processes

An entitlement process is a timeline that cases move through once an entitlement is applied. It defines the ordered set of milestones a case must satisfy and the actions to fire when thresholds are hit. Each entitlement process has:

- A **version** — processes are versioned; a case stays on the version that was active when the entitlement was applied.
- A **business hours** reference — the default timer cadence for all milestones in the process unless overridden at the milestone level.
- A **start condition** — when the process clock begins (e.g., on case creation, on status change).
- An **exit criteria** — when the process ends (e.g., case closed).

Entitlement processes support up to 10 milestones per process. UNVERIFIED (2026-09-04): that figure is not in the Metadata API Developer Guide's `EntitlementProcess` section (api_meta.txt:59069–59308) and `grep -i "entitlement\|milestone"` over the Salesforce App Limits Cheat Sheet returns no milestone limit row at all — treat 10 as folklore until you confirm it in the target org. Multiple processes can exist in an org (e.g., Platinum, Gold, Standard), and each is assigned to a specific entitlement record.

The whole thing is deployable metadata, not Setup-only clicking. The process, its milestones and their
time triggers live in one `entitlementProcesses/*.entitlementProcess-meta.xml` file per **version**;
the milestone definitions are separate `MilestoneType` components; the org switches are a `Settings`
file. `references/metadata-examples.md` carries the complete, well-formed set with a `package.xml` and
the `sf project retrieve/deploy` commands.

| Component | What it owns |
|---|---|
| `MilestoneType` | The milestone's identity and its `recurrenceType`. Shared by every process that names it. |
| `EntitlementProcess` | Entry field, exit criteria, `SObjectType`, the process calendar, versioning, and per-milestone timing and actions. One file per version. |
| `Workflow` (member `Case`) | The alerts and field updates the milestone actions reference by name. |
| `EntitlementTemplate` | Default terms — process, calendar, `term` in days, per-incident case count. |
| `Settings` (member `Entitlement`) | `enableEntitlements`, `enableEntitlementVersioning`, stopped-time and feed-item switches. |

### Milestone Types and Recurrence

Each milestone within a process has a **recurrence type** that controls when the milestone resets:

- **No Recurrence** (`recurrenceType` = `none`) — the milestone fires once and is complete. The guide's exact wording is "the milestone occurs only one time **until the entitlement process exits**" (api_meta.txt:88339–88341), which is why a reopened case starts it again. Use for first-response SLAs.
- **Sequential** (`recurrenceType` = `recursChained`) — the milestone repeats but only after the previous instance is completed. Use for periodic check-ins where each check-in must close before the next opens.
- **Independent** (`recurrenceType` = `recursIndependently`) — the milestone repeats regardless of completion state. Use for ongoing commitments like "respond to every new comment within 2 hours."

The three API values are the whole enum (api_meta.txt:88337–88345); the Setup labels are *No Recurrence*, *Recurs Chained* and *Recurs Independently*. Recurrence is a field on the shared `MilestoneType`, **not** on the process's milestone entry — the `EntitlementProcessMilestoneItem` field table has no recurrence field (api_meta.txt:59158–59202). Choosing the wrong recurrence type is a common source of SLA gaps, and changing it changes every process that names that milestone.

### Milestone Actions

Setup presents three action categories — warning, violation, success — but the metadata has only two
elements, and the difference matters the moment you write or read the XML:

| Setup calls it | Metadata element | How it is expressed |
|---|---|---|
| Success actions | `successActions` | A `WorkflowActionReference` list. "The actions triggered when the milestone is completed." (api_meta.txt:59194) |
| Warning actions | `timeTriggers` with a **negative** `timeLength` | "Negative values indicate that the target completion date hasn't yet arrived and correspond to warning time triggers." (api_meta.txt:59213–59217) |
| Violation actions | `timeTriggers` with a **positive** `timeLength` | "Positive values indicate that the target completion date has passed and correspond to violation time triggers." (api_meta.txt:59217–59219) |

Each `timeTrigger` carries `timeLength` (int), `workflowTimeTriggerUnit` (`Minutes` | `Hours` | `Days`)
and an `actions` list whose entries are `name` plus a `type` of `Alert`, `FieldUpdate`, `FlowAction`,
`OutboundMessage` or `Task` (api_meta.txt:59204–59224, 139950–139968).

Thresholds are **offsets from the milestone target, not percentages**. A "75% warning" on a 4-hour
(`minutesToComplete` 240) milestone is deployed as `timeLength` `-60` with unit `Minutes`. Nothing
recomputes it when the time limit changes — see `references/gotchas.md` gotcha 6.

### Business Hours and Timer Behavior

Business hours can be assigned at two levels:

1. **Process level** — all milestones in the process inherit the process's business hours unless overridden.
2. **Milestone level** — an individual milestone can specify its own business hours, which overrides the process-level setting for that milestone only.

When a case is open outside the configured business hours, the milestone timer **pauses**. When business hours resume, the timer continues from where it left off. If no business hours are attached (neither at process nor milestone level), the timer runs 24/7 including weekends and holidays.

This has a critical implication: a "1 business hour" response milestone with 8am–5pm M–F business hours means the timer only ticks during those windows. A case created Friday at 4:45 PM with no business hours attached will breach its 1-hour milestone at 5:45 PM Friday — which may be unintended.

There is a third calendar in play and milestones ignore it. `Case.BusinessHoursId` is what escalation
rules can read (`businessHoursSource` = `Case`); the process and milestone calendars are separate
fields and neither falls back to the Case. `admin/business-hours-and-holidays` `references/gotchas.md`
§ 5 is the authority on that precedence — read it before assuming escalation and milestones agree.
The calendar a milestone instance actually used is recorded on the row as `CaseMilestone.BusinessHoursId`
(object_reference.txt:63350–63356), so the override can be proved rather than assumed.

---

## Common Patterns

### Pattern: Multi-Tier SLA Process with Progressive Warning Actions

**When to use:** The business has defined Platinum, Gold, and Standard support tiers, each with different first-response and resolution SLA commitments, and agents need automated reminders before breach.

**How it works:**
1. Create one entitlement process per support tier (e.g., "Platinum SLA Process").
2. Assign the process-level business hours matching the tier's coverage (e.g., 24/7 for Platinum, business hours for Standard).
3. Add a "First Response" milestone with No Recurrence. Set the time limit to the tier's response SLA (e.g., 1 hour for Platinum).
4. Add warning time triggers. For a 60-minute (`minutesToComplete` 60) milestone, "50% and 75%" deploys as `timeLength` `-30` and `-15`, both `Minutes` — email alert to assigned agent and queue manager.
5. Add a violation time trigger: the smallest positive `timeLength` (`1` `Minutes`) — email alert to VP of Support + field update setting `Case.SLA_Breached__c = true`.
6. Add a "Resolution" milestone with No Recurrence. Set time limit to the tier's resolution SLA (e.g., 4 hours for Platinum).
7. Repeat warning/violation wiring for the Resolution milestone.
8. Create an entitlement record for each customer account referencing the correct process, then associate it to incoming cases via the Case Entitlement lookup.

**Why not a simple escalation rule:** Escalation rules fire based on case age from creation, not from when support work began, and cannot distinguish between tiers without complex rule entry logic. Entitlement processes track SLA elapsed time per milestone, pause during non-business hours, and reset on recurrence — behavior that escalation rules cannot replicate natively.

### Pattern: Entitlement Templates for Automatic Entitlement Creation

**When to use:** Customers purchase support contracts via Products & Price Books, and the org needs entitlements auto-created when an opportunity closes or an order is placed.

**How it works (Classic):**
1. Create an entitlement template that references the correct entitlement process and business hours.
2. From the product record in Classic, use the "Entitlement Templates" related list to attach the template to the product.
3. When the product is added to an opportunity and the opportunity closes, Salesforce can auto-create the entitlement on the account.

**How it works (Lightning):**
The Entitlement Templates related list is not available on the product page in Lightning Experience. Instead:
1. Create the entitlement template via Setup > Entitlement Templates.
2. Build a Record-Triggered Flow that fires on `OpportunityLineItem` insert (or `OrderItem`) when the opportunity stage becomes "Closed Won."
3. In the Flow, create an `Entitlement` record referencing the matching template, and set `AccountId`, `StartDate`, `EndDate` and `SlaProcessId`. Do **not** try to set `BusinessHoursId` or `Status` — neither carries the `Create` or `Update` property (object_reference.txt:110216–110222, 110364–110371); the calendar comes from the template and the status is derived from the dates.

**Why not manual creation:** Manual entitlement creation on large deal volumes is error-prone. If the entitlement is per-incident, `RemainingCases` decrements once per case created against it (object_reference.txt:110345–110352) — an exhausted entitlement stops applying the process to new cases as quietly as a missing one does. Customers frequently open cases without an active entitlement if the process is ad-hoc, causing milestone processes to not trigger.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| SLA clock must pause on weekends and holidays | Assign a Business Hours object to the entitlement process or milestone | Without business hours, timer runs 24/7 regardless of support coverage |
| Different SLA windows per milestone within one process | Override business hours at the milestone level | Milestone-level business hours override the process-level setting for that milestone only |
| Escalation rules and milestones must agree on working time | Pick one authority and point both at it | Milestones never read `Case.BusinessHoursId`; see `admin/business-hours-and-holidays` gotcha 5 |
| SLA resets every time a customer replies | Use `recursIndependently` on the response milestone | `recursChained` only resets after the prior instance completes, creating gaps |
| Two tiers need the same milestone with different recurrence | Create two `MilestoneType` components | Recurrence is on the type, so one type cannot behave two ways |
| SLA terms change on a live process | New `EntitlementProcess` file, next `versionNumber`, same `versionMaster`, `isVersionDefault` moved | `SlaProcess` has no `update()` call, and one file holds one version |
| A warning must fire "at 75%" | Compute the offset by hand: `timeLength` = −(0.25 × `minutesToComplete`) | Time triggers are offsets from the target; nothing scales them |
| Cases are stopped while awaiting the customer | Enable `enableMilestoneStoppedTime` before go-live | Otherwise elapsed time excludes stopped intervals with no way to see them |
| An SLA must survive a case being reopened | Exit on a stamped boolean, not `Status = Closed` | Non-recurring means "once until the process exits" — exiting and re-entering restarts it |
| Only one response and one resolution SLA per tier | Use No Recurrence on both milestones | Simpler to configure and audit; prevents accidental stacking |
| Customers purchase support via products in Lightning | Build a Record-Triggered Flow to create entitlements on Opportunity close | Entitlement template product attachment UI does not exist in Lightning |
| Need to track whether an SLA was met for reporting | Add a field update success action that stamps a datetime field | Salesforce does not expose a native "milestone met at" field in standard reports |
| Multiple support tiers | One entitlement process per tier | Process versions are tied to the process; mixing tiers in one process creates maintenance risk |

---

## Recommended Workflow

1. **Answer the seven questions above, in writing** — especially "how does a case get its entitlement"
   and "who marks a milestone complete". Fill `templates/entitlements-and-milestones-template.md`; an
   unanswered row here becomes a silent failure at go-live, not a deploy error.
2. **Set the org switches first, in their own change** — `settings/Entitlement.settings-meta.xml` with
   `enableEntitlements`, `enableEntitlementVersioning` and `enableMilestoneStoppedTime`. Versioning
   must be on *before* the first process, because the version fields are inert without it
   (`references/gotchas.md` gotcha 12).
3. **Deploy the milestone types and the workflow actions before the process** — `MilestoneType` carries
   the `recurrenceType`; `workflows/Case.workflow-meta.xml` carries every alert and field update the
   process references by name. Shapes and required fields: `references/metadata-examples.md` §§ 1 and 3.
4. **Write the process file from the retrieved name, not a guessed one** — create it once in Setup,
   retrieve `EntitlementProcess`, then edit what came back. Set `SObjectType`, `entryStartDateField`,
   exit criteria, the process calendar, and per milestone `minutesToComplete`, `useCriteriaStartTime`,
   any milestone-level `businessHours`, `successActions` and signed `timeTriggers`
   (`references/metadata-examples.md` § 2).
5. **Wire entitlement creation and the case lookup** — entitlement template plus a Flow for Lightning
   (`references/examples.md`, Anti-Pattern), and the before-save Flow that populates the case's
   entitlement on every intake channel. Let the template carry `businessHours`; a Flow cannot write
   `Entitlement.BusinessHoursId` (`references/gotchas.md` gotcha 11).
6. **Lint, then deploy-validate** — run
   `python3 skills/admin/entitlements-and-milestones/scripts/check_entitlements_and_milestones.py --manifest-dir force-app/main/default`
   and clear every ERROR, then `sf project deploy validate --test-level RunLocalTests`.
7. **Test with the clock and the log, in a sandbox** — create a case through each intake channel; run
   the `Case WHERE EntitlementId = NULL` query in `references/examples.md`; turn on a debug log with
   the **Workflow** category at INFO and confirm `SLA_PROCESS_CASE` appears and `SLA_NULL_START_DATE`
   does not. Then run the `SlaProcess`, `Entitlement` and `CaseMilestone` verification queries in
   `references/metadata-examples.md` § 8 and confirm exactly one default version per `versionMaster`.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Entitlement Management is enabled in Setup
- [ ] Business Hours objects are configured and assigned at the process or milestone level as intended
- [ ] Each entitlement process has at least one warning action (not just violation actions)
- [ ] Recurrence type is appropriate for each milestone (No Recurrence, Sequential, or Independent)
- [ ] Entitlement and Milestone Tracker related lists/components are added to Case page layouts
- [ ] Entitlement records are associated to cases (via the Entitlement lookup on Case) — without this, processes never trigger
- [ ] In Lightning, a Flow handles entitlement creation from products if entitlement templates are used
- [ ] Milestone timer behavior was tested in sandbox with a shortened time limit before go-live
- [ ] Every `timeLength` was re-derived after the last change to `minutesToComplete`
- [ ] Something writes `CaseMilestone.CompletionDate` — completion criteria the platform can satisfy, or deployed Apex/Flow
- [ ] `enableEntitlementVersioning` and `enableMilestoneStoppedTime` are on, and exactly one version per `versionMaster` has `isVersionDefault` true
- [ ] `scripts/check_entitlements_and_milestones.py` reports no ERROR against the deploy directory
- [ ] A Workflow-category debug log on a test case shows `SLA_PROCESS_CASE` and no `SLA_NULL_START_DATE`

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Entitlement templates cannot be attached to products in Lightning** — The "Entitlement Templates" related list on the Product2 record is absent in Lightning Experience. Orgs that rely on this for auto-entitlement creation will silently fail to create entitlements when switching from Classic to Lightning. Mitigation: build a Record-Triggered Flow on Opportunity/Order close.
2. **Missing entitlement lookup on the case means the process never starts** — An entitlement process is only invoked when a case has a populated `EntitlementId` lookup field. Cases created without an entitlement (e.g., via Email-to-Case or Web-to-Case) will have no entitlement and no milestone tracking unless automation populates the field. Mitigation: build a case creation Flow or assignment rule that auto-populates the entitlement lookup based on account.
3. **Business hours must exist before the entitlement process is activated** — Activating an entitlement process that references a deleted or inactive business hours record causes timer calculation errors. Always validate the business hours object is active before activating the process.
4. **Milestone timer pauses do not retroactively adjust violation actions already queued** — Once a violation action is scheduled, pausing the milestone timer (e.g., by updating business hours mid-flight) does not cancel the queued action. The action fires at the originally scheduled time. Test this in sandbox before go-live in orgs with narrow business hours windows.
5. **Process versioning locks milestones on active cases** — When a new version of an entitlement process is published, existing cases remain on the old version. Changes to milestone time limits or actions do not affect in-flight cases. Communicate version cutover dates clearly to operations teams.
6. **Warning and violation thresholds are signed offsets, not percentages** — `timeLength` counts from the milestone target, so shortening `minutesToComplete` without re-deriving every trigger leaves warnings firing after the breach they were meant to pre-empt.
7. **A milestone stays open until something writes `CompletionDate`** — `CaseMilestone` has no `create()` and no `delete()` call; completion is an update your automation performs, or it never happens.

The full set, each with what happens / when it occurs / how to avoid, is in `references/gotchas.md`.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Entitlement process configuration | Named process with versioning, business hours, start/exit conditions, and ordered milestones |
| Milestone definitions | Time limits, recurrence types, and business hours override per milestone |
| Milestone action rules | Warning (50/75/90%) and violation (100%) email alerts, field updates, and task actions |
| Entitlement template (optional) | Template referencing a process for auto-creation via Flow or Classic product attachment |
| Flow (Lightning) | Record-Triggered Flow to auto-create entitlements on Opportunity/Order close |
| Deployable metadata set | `milestoneTypes/`, `entitlementProcesses/`, `entitlementTemplates/`, `workflows/Case.workflow-meta.xml`, `settings/Entitlement.settings-meta.xml`, plus `package.xml` |
| Verification queries | `SlaProcess` version list, active `Entitlement` list, violated `CaseMilestone` by type |
| Version-bump plan | Next `versionNumber`, re-derived time-trigger offsets, and the `isVersionDefault` move |
| Check script output | Validation report from `scripts/check_entitlements_and_milestones.py` against metadata export |

---

## Reference Files

| File | Read it when |
|---|---|
| `references/metadata-examples.md` | Writing or reviewing the deployable XML, `package.xml`, retrieve/deploy commands, the version bump, the verification SOQL, or the milestone-completion Apex |
| `references/gotchas.md` | A milestone fired late, early, never, or shows violated when the work was done |
| `references/examples.md` | You want the three-tier and ongoing-response scenarios worked end to end, plus the no-entitlement-on-the-case diagnosis queries |
| `references/well-architected.md` | Choosing entitlements over hand-rolled SLA fields, and the official sources behind every claim here |
| `references/llm-anti-patterns.md` | Self-checking generated entitlement guidance before returning it |
| `templates/entitlements-and-milestones-template.md` | Capturing the design before touching Setup |
| `scripts/check_entitlements_and_milestones.py` | Linting an entitlement metadata directory before deploy |

---

## Related Skills

- admin/business-hours-and-holidays — the calendars `businessHours` names at process and milestone level; its `references/gotchas.md` § 5 is the calendar-precedence rule this skill defers to
- admin/escalation-rules — the other SLA clock; a different engine, and it can read a calendar milestones never read
- admin/case-management-setup — how a case gets its entitlement per intake channel; this skill's metadata is the artefact its worked example said was missing
- admin/assignment-rules — case-to-queue routing that runs alongside, and the base shape for object-scoped rule metadata
- architect/sla-design-and-escalation-matrix — the tier table that decides what `minutesToComplete` should be
- admin/workflow-field-update-patterns — the `Workflow` container the milestone alerts and field updates are deployed in
- admin/products-and-pricebooks — Required context when entitlement templates are attached to products for contract automation
- admin/sales-process-mapping — Upstream process that determines when customer support entitlements are created relative to deal close

Design procedure — which tiers, how many milestones, what the matrix should say — belongs to
`agents/entitlement-and-milestone-designer/AGENT.md` (`/design-entitlements`). This skill owns the
deployable shapes and how they behave once live.
