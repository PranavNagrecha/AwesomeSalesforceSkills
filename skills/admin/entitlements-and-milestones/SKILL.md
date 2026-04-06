---
name: entitlements-and-milestones
description: "Use this skill to design, configure, and troubleshoot Salesforce Entitlement Management: entitlement processes, milestone definitions, recurrence types, milestone actions (success/warning/violation), business hours assignment, and entitlement templates. NOT for case escalation rules, assignment rules, or omni-channel routing configuration."
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
inputs:
  - "Support tier names and SLA commitments (e.g., Platinum 1-hour response 8-hour resolution)"
  - "Business hours schedules already configured in Setup"
  - "Whether the org sells Support products via Products and Price Books"
  - "Whether Lightning Experience or Classic is the primary UI"
outputs:
  - "Configured entitlement process with milestone definitions and action timers"
  - "Decision guidance on recurrence type, action thresholds, and business hours scope"
  - "Entitlement template strategy for automating entitlement creation"
  - "Checklist for validating live milestone timer behavior"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-06
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

## Core Concepts

### Entitlement Processes

An entitlement process is a timeline that cases move through once an entitlement is applied. It defines the ordered set of milestones a case must satisfy and the actions to fire when thresholds are hit. Each entitlement process has:

- A **version** — processes are versioned; a case stays on the version that was active when the entitlement was applied.
- A **business hours** reference — the default timer cadence for all milestones in the process unless overridden at the milestone level.
- A **start condition** — when the process clock begins (e.g., on case creation, on status change).
- An **exit criteria** — when the process ends (e.g., case closed).

Entitlement processes support up to 10 milestones per process. Multiple processes can exist in an org (e.g., Platinum, Gold, Standard), and each is assigned to a specific entitlement record.

### Milestone Types and Recurrence

Each milestone within a process has a **recurrence type** that controls when the milestone resets:

- **No Recurrence** — the milestone fires once and is complete. Use for first-response SLAs.
- **Sequential** — the milestone repeats but only after the previous instance is completed. Use for periodic check-ins where each check-in must close before the next opens.
- **Independent** — the milestone repeats on a fixed schedule regardless of completion state. Use for ongoing commitments like "respond to every new comment within 2 hours."

Choosing the wrong recurrence type is a common source of SLA gaps. Independent milestones can stack if cases go unworked.

### Milestone Actions

Each milestone has three action categories, each of which can contain one or more automated actions (email alerts, field updates, task creation, outbound messages):

- **Warning actions** — fire before the milestone time limit is reached. Configure at 50%, 75%, and 90% of elapsed time to give agents progressive notice.
- **Violation actions** — fire when the milestone time limit is reached or exceeded (100% elapsed). These represent an actual SLA breach.
- **Success actions** — fire when the milestone is completed before the time limit. Use to trigger confirmation emails or close follow-up tasks.

Action triggers are percentage-based relative to the milestone time limit, not absolute times. This means a 4-hour milestone with a 75% warning fires at 3 hours elapsed.

### Business Hours and Timer Behavior

Business hours can be assigned at two levels:

1. **Process level** — all milestones in the process inherit the process's business hours unless overridden.
2. **Milestone level** — an individual milestone can specify its own business hours, which overrides the process-level setting for that milestone only.

When a case is open outside the configured business hours, the milestone timer **pauses**. When business hours resume, the timer continues from where it left off. If no business hours are attached (neither at process nor milestone level), the timer runs 24/7 including weekends and holidays.

This has a critical implication: a "1 business hour" response milestone with 8am–5pm M–F business hours means the timer only ticks during those windows. A case created Friday at 4:45 PM with no business hours attached will breach its 1-hour milestone at 5:45 PM Friday — which may be unintended.

---

## Common Patterns

### Pattern: Multi-Tier SLA Process with Progressive Warning Actions

**When to use:** The business has defined Platinum, Gold, and Standard support tiers, each with different first-response and resolution SLA commitments, and agents need automated reminders before breach.

**How it works:**
1. Create one entitlement process per support tier (e.g., "Platinum SLA Process").
2. Assign the process-level business hours matching the tier's coverage (e.g., 24/7 for Platinum, business hours for Standard).
3. Add a "First Response" milestone with No Recurrence. Set the time limit to the tier's response SLA (e.g., 1 hour for Platinum).
4. Add warning actions at 50% (30 min) and 75% (45 min) — email alert to assigned agent and queue manager.
5. Add a violation action at 100% — email alert to VP of Support + field update setting `Case.SLA_Breached__c = true`.
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
3. In the Flow, create an `Entitlement` record referencing `EntitlementTemplateId` from the matching template, set `AccountId`, `StartDate`, `EndDate`, and `EntitlementProcessId`.

**Why not manual creation:** Manual entitlement creation on large deal volumes is error-prone. Customers frequently open cases without an active entitlement if the process is ad-hoc, causing milestone processes to not trigger.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| SLA clock must pause on weekends and holidays | Assign a Business Hours object to the entitlement process or milestone | Without business hours, timer runs 24/7 regardless of support coverage |
| Different SLA windows per milestone within one process | Override business hours at the milestone level | Milestone-level business hours override the process-level setting for that milestone only |
| SLA resets every time a customer replies | Use Independent recurrence on the response milestone | Sequential recurrence only resets after the prior instance completes, creating gaps |
| Only one response and one resolution SLA per tier | Use No Recurrence on both milestones | Simpler to configure and audit; prevents accidental stacking |
| Customers purchase support via products in Lightning | Build a Record-Triggered Flow to create entitlements on Opportunity close | Entitlement template product attachment UI does not exist in Lightning |
| Need to track whether an SLA was met for reporting | Add a field update success action that stamps a datetime field | Salesforce does not expose a native "milestone met at" field in standard reports |
| Multiple support tiers | One entitlement process per tier | Process versions are tied to the process; mixing tiers in one process creates maintenance risk |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Enable and configure foundations** — Verify Entitlement Management is enabled in Setup. Confirm Business Hours records exist for each coverage window needed (24/7, M–F 8–5, etc.). Add the Entitlements related list to the Case page layout and the Account/Contact page layouts.
2. **Define entitlement processes** — For each support tier, create an entitlement process: set the process name, version label, business hours (process level), start/exit conditions. Do not add milestones yet.
3. **Add milestones to each process** — For each SLA commitment (first response, resolution), add a milestone: set the time limit, recurrence type (No Recurrence for first response/resolution SLAs), and optionally override business hours at the milestone level.
4. **Wire milestone actions** — For each milestone, add warning actions at 50%, 75%, and 90% of elapsed time (email alerts to assigned agent/queue). Add a violation action at 100% (escalation email + field update). Add success actions if confirmation or reporting stamps are needed.
5. **Create entitlement records and templates** — Create entitlement records for key accounts referencing the correct process. If entitlement templates are needed for product-based automation, create the templates and wire the Flow (Lightning) or attach to products (Classic).
6. **Test milestone timers** — Create a test case, apply the entitlement, then use the Milestone Tracker component on the case to verify timers are counting down. Temporarily set a short time limit (1 minute) in a sandbox to confirm warning and violation actions fire correctly.
7. **Validate and document** — Confirm all page layouts include the Milestone Tracker and Entitlements related list. Document each process version, its tier mapping, and the business hours in use. Run the check script against the metadata export to catch configuration gaps before go-live.

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

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Entitlement templates cannot be attached to products in Lightning** — The "Entitlement Templates" related list on the Product2 record is absent in Lightning Experience. Orgs that rely on this for auto-entitlement creation will silently fail to create entitlements when switching from Classic to Lightning. Mitigation: build a Record-Triggered Flow on Opportunity/Order close.
2. **Missing entitlement lookup on the case means the process never starts** — An entitlement process is only invoked when a case has a populated `EntitlementId` lookup field. Cases created without an entitlement (e.g., via Email-to-Case or Web-to-Case) will have no entitlement and no milestone tracking unless automation populates the field. Mitigation: build a case creation Flow or assignment rule that auto-populates the entitlement lookup based on account.
3. **Business hours must exist before the entitlement process is activated** — Activating an entitlement process that references a deleted or inactive business hours record causes timer calculation errors. Always validate the business hours object is active before activating the process.
4. **Milestone timer pauses do not retroactively adjust violation actions already queued** — Once a violation action is scheduled, pausing the milestone timer (e.g., by updating business hours mid-flight) does not cancel the queued action. The action fires at the originally scheduled time. Test this in sandbox before go-live in orgs with narrow business hours windows.
5. **Process versioning locks milestones on active cases** — When a new version of an entitlement process is published, existing cases remain on the old version. Changes to milestone time limits or actions do not affect in-flight cases. Communicate version cutover dates clearly to operations teams.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Entitlement process configuration | Named process with versioning, business hours, start/exit conditions, and ordered milestones |
| Milestone definitions | Time limits, recurrence types, and business hours override per milestone |
| Milestone action rules | Warning (50/75/90%) and violation (100%) email alerts, field updates, and task actions |
| Entitlement template (optional) | Template referencing a process for auto-creation via Flow or Classic product attachment |
| Flow (Lightning) | Record-Triggered Flow to auto-create entitlements on Opportunity/Order close |
| Check script output | Validation report from `scripts/check_entitlements_and_milestones.py` against metadata export |

---

## Related Skills

- admin/case-management-setup — Core case configuration; entitlements require correct Case page layouts and email-to-case routing to function end-to-end
- admin/products-and-pricebooks — Required context when entitlement templates are attached to products for contract automation
- admin/sales-process-mapping — Upstream process that determines when customer support entitlements are created relative to deal close
