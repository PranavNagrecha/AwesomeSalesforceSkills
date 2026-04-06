---
name: sla-design-and-escalation-matrix
description: "Use when designing the SLA tier definition table, escalation matrix document, and milestone threshold configuration for a Salesforce Service Cloud implementation. Covers designing the artifact layer — tier tiers (e.g., Enterprise/Professional/Basic), response and resolution time targets, business hours mapping, milestone percentage thresholds at 50/75/90/100%, and the escalation action matrix that maps thresholds to notification targets and automated actions. Triggers: SLA design, escalation matrix, milestone thresholds, tier definition, business hours alignment, SLA enforcement design. NOT for entitlement process configuration steps (use admin/case-management-setup), NOT for escalation rule setup (use admin/escalation-rules), NOT for CPQ quoting SLAs."
category: architect
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
  - Security
triggers:
  - "design an SLA matrix for our Enterprise and Professional support tiers"
  - "what milestone percentage thresholds should we configure for first response and resolution"
  - "how do we map business hours to entitlement processes and escalation rules so SLA timing is correct"
  - "create an escalation matrix document that shows who gets notified at 50%, 75%, 90%, and breach"
  - "define SLA tiers and escalation paths before we configure entitlements in Salesforce"
  - "our SLA escalation fires on weekends even though we have business hours configured"
tags:
  - sla-design
  - escalation-matrix
  - entitlement-processes
  - milestones
  - business-hours
  - service-cloud
  - tier-design
inputs:
  - Support tier names and the customer segment each tier covers (e.g., Enterprise, Professional, Basic)
  - First response and resolution SLA targets per tier and per case priority (P1–P4)
  - Business operating hours per region or support team
  - Escalation path for each tier — who gets notified at each threshold and what automated action fires
  - Whether SLAs apply to the whole case or differ by channel (email, phone, chat)
outputs:
  - SLA tier definition table (tier name, priority, first-response target, resolution target, business hours group)
  - Escalation matrix document (tier x priority grid with threshold percentages, notification targets, and automated actions)
  - Business hours mapping table (which entitlement process and which escalation rule entries reference which business hours record)
  - Milestone configuration plan listing milestone names, time targets, percentage-threshold action sequences, and success criteria
  - Decision record on SLA clock behavior (business hours vs 24/7, age-over field choice)
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-06
---

# SLA Design and Escalation Matrix

Use this skill when a Salesforce project needs to design the SLA enforcement artifacts before configuring entitlement processes, milestones, and escalation rules. It activates when a practitioner must define support tier tables, set milestone percentage thresholds, map business hours to the correct enforcement objects, and produce a documented escalation matrix that shows who is notified and what automated action fires at each threshold. This skill produces the design artifacts — the tier definition table, escalation matrix document, and milestone configuration plan — that a Salesforce admin then implements using entitlement process configuration.

---

## Before Starting

Gather this context before working on anything in this domain:

- **What support tiers exist and what customer segment do they cover?** Enterprise, Professional, and Basic are common names, but the actual tier count, names, and eligibility criteria vary. Gather this from the support operations team or the customer contract.
- **What are the most common wrong assumptions?** That business hours need to be configured only on the entitlement process. In Salesforce, business hours must be attached to both the entitlement process AND each escalation rule entry independently — the two objects do not share a clock. Missing one side means the other still runs 24/7.
- **What limits are in play?** An org can have a maximum of 2,000 entitlement processes. Each entitlement process supports up to 10 milestones. Each milestone can have up to 40 milestone actions total (across warning, violation, and success). Escalation rules have a single active rule per org with up to 3,000 entries.

---

## Core Concepts

### SLA Tiers and the Tier Definition Table

An SLA tier defines the support commitment level for a customer segment. The tier definition table is the canonical design artifact: it captures tier name, applicable customer segment, case priority levels (P1–P4), first response time target, resolution time target, and the business hours group applied. This table becomes the input spec for entitlement process configuration. Without a formal tier definition table, entitlement processes and milestones are configured inconsistently — different admins interpret verbal agreements differently, producing mismatched milestone values.

Each tier typically maps to an Entitlement Process in Salesforce, and each priority level within the tier maps to one or more milestones within that process. A three-tier model (Enterprise, Professional, Basic) with four priority levels (P1–P4) produces up to 12 distinct milestone configurations. Designing these on paper before configuring saves significant rework.

### Milestone Percentage Thresholds and the Escalation Matrix

Milestones in Salesforce Entitlement Processes support time-based actions at configurable percentage thresholds — most commonly 50%, 75%, 90%, and 100% (violation). Each threshold can trigger an email alert, a field update, an outbound message, or an Apex action. The escalation matrix document maps each threshold percentage to the specific notification target and automated action:

- **50%** — Informational: notify the assigned agent that the clock is running. No escalation yet.
- **75%** — Warning: notify the team lead or supervisor. Case may need help.
- **90%** — Pre-breach: notify the support manager. Ownership transfer or escalation path should start.
- **100% (violation)** — Breach: notify executive stakeholder and/or create a follow-up task. Trigger field update to mark the milestone as violated on the case record.

The escalation matrix is a grid of tier x priority x threshold, with columns for notification target, automated action, and SLA clock basis. Designing this artifact before Salesforce configuration ensures consistent, reviewable coverage and makes the design auditable by business stakeholders.

### Business Hours Alignment: Dual Configuration Requirement

Salesforce SLA enforcement uses two distinct execution paths that both require business hours to be configured independently:

1. **Entitlement Process Business Hours** — set on the Entitlement Process record itself. Controls how milestone elapsed time is calculated. If omitted, the milestone clock runs 24 hours a day, 7 days a week even if agents only work Mon–Fri 9–5.
2. **Escalation Rule Business Hours** — set on each individual escalation rule entry. Controls when case escalation rules evaluate and fire their time-based actions. An escalation entry configured to fire after 4 hours uses 4 calendar hours, not 4 business hours, unless the business hours field on that specific entry is populated.

These two configurations are not linked. An org that correctly configures business hours on its entitlement process will still fire escalation rule entries on weekends if the escalation rule entries omit the business hours field. This is the single most common SLA design defect in Service Cloud implementations.

A third location that affects business hours behavior is the **Entitlement record itself** — it can override the process-level business hours for individual customers (useful for 24/7 premium customers or customers in different time zones).

### Milestone vs Escalation Rule: When to Use Which

Milestones (within entitlement processes) and escalation rules serve overlapping but distinct purposes:

| Enforcement Mechanism | Trigger | Primary Use |
|---|---|---|
| Milestone actions | Percentage of milestone time elapsed | SLA compliance notifications tied to entitlement contract (customer-facing) |
| Escalation rules | Case age or time since last modification | Internal operational routing — re-assign or notify when a case sits too long |

Best practice: use milestones for customer-facing SLA commitment enforcement. Use escalation rules for internal operational safety nets (e.g., a case has not been touched in 24 hours). Design both together in the escalation matrix so the two mechanisms complement rather than duplicate each other.

---

## Common Patterns

### Pattern: Three-Tier SLA Matrix with Milestone Percentage Actions

**When to use:** Most B2B software or platform support models with differentiated support tiers by contract level.

**How it works:**
1. Define the tier definition table: Enterprise (P1 1h/4h, P2 4h/8h, P3 8h/24h, P4 24h/72h), Professional (P1 4h/8h, P2 8h/16h, P3 1d/3d, P4 2d/5d), Basic (P1 8h/24h, P2 24h/48h, P3 3d/5d, P4 5d/10d). All values are business-hours-based.
2. Create one Entitlement Process per tier. Attach the correct Business Hours record to each process.
3. Add milestones to each process: one for First Response, one for Resolution, per priority. Use entry criteria to activate the correct milestone based on case Priority field.
4. For each milestone, configure four milestone actions: 50% warning (email to agent), 75% warning (email to team lead), 90% pre-breach (email to manager + task), 100% violation (email to manager + field update to mark violated).
5. Design the escalation matrix document that captures this grid for stakeholder sign-off before configuration.

**Why not the alternative:** Configuring entitlement processes directly without a tier definition table leads to ad-hoc time values that drift from the contractual commitments in customer agreements. The design artifact provides an audit trail.

### Pattern: Dual Business Hours Assignment Checklist

**When to use:** Any implementation where SLAs must respect business operating hours.

**How it works:**
1. Create named Business Hours records in Setup for each operating region or team (e.g., "US West Coast 8am–6pm PT", "EMEA 9am–6pm CET").
2. Assign the correct Business Hours record to each Entitlement Process.
3. For each Escalation Rule entry, explicitly set the Business Hours field to the same corresponding record.
4. If any individual customers require 24/7 coverage (e.g., Enterprise premium), override at the Entitlement record level by populating the Business Hours field with the 24/7 record on those specific entitlements.
5. Document this mapping in the Business Hours Mapping Table artifact.

**Why not the alternative:** Relying on the platform default "Business Hours" record (which is 24/7 unless manually restricted) means escalations and milestones fire outside working hours, burning through SLA time invisibly while no agent is available to respond.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Customer-facing SLA enforcement with contractual commitments | Entitlement Processes + Milestones with percentage-threshold actions | Only mechanism that is business-hours-aware and ties SLA tracking to an entitlement contract |
| Internal operational safety net (case sitting idle) | Escalation Rules (separate from milestones) | Decoupled from customer contract; can re-assign to a queue or supervisor without affecting milestone clock |
| Different time zones requiring different business hours | Create one Business Hours record per region, assign per entitlement process and per escalation entry | Entitlement record can override process-level hours for individual premium customers |
| SLA with sub-1-hour precision required | Custom Apex Scheduled Job or Platform Events | Declarative milestone and escalation engines are batch-based; sub-hour precision requires custom automation |
| Three support tiers needing different SLA commitments | One Entitlement Process per tier | Process-level separation provides clean tier isolation; milestone entry criteria further segment by case priority |
| Single tier with multiple priority levels | One Entitlement Process + milestone entry criteria per priority | Keeps tier clean; entry criteria on milestones activate the correct time targets based on Priority |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner designing an SLA matrix:

1. **Gather tier and SLA commitments** — Document all support tiers (names, customer segments), case priority levels (P1–P4 or equivalent), and first response and resolution targets for each tier-priority combination. Confirm whether targets are business-hours or calendar-hours. Obtain sign-off from the account management or product team on contractual commitments.
2. **Build the tier definition table** — Produce the tier x priority x time-target grid as a design artifact. Include the business hours group to be applied and note any tier that requires 24/7 coverage. This table is the input specification for entitlement process configuration.
3. **Design the escalation matrix** — For each tier, for each priority level, define the action at each milestone percentage (50%, 75%, 90%, 100%). Document notification target (agent, team lead, manager, executive), automated action type (email alert, field update, task), and any case reassignment that should occur. Review with support operations for feasibility.
4. **Map business hours** — Create a Business Hours Mapping Table listing every entitlement process and every escalation rule entry with the business hours record each must reference. Flag any object that should run 24/7 vs restricted hours. Use this as a configuration checklist.
5. **Validate the design against platform limits** — Confirm: total entitlement processes is within 2,000; each process has no more than 10 milestones; each milestone has no more than 40 actions total; escalation rule entry count is within 3,000. If the design exceeds these, consolidate tiers or simplify action logic.
6. **Review with stakeholders** — Walk through the tier definition table and escalation matrix with support operations, account management, and the Salesforce admin who will configure it. Confirm that notification recipients and action types are achievable with the org's current email alerts and user records.
7. **Hand off to configuration** — Deliver the tier definition table, escalation matrix document, business hours mapping table, and milestone configuration plan as the specification for admin configuration. Reference admin/case-management-setup for implementation steps.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Tier definition table covers all support tiers, all case priority levels, and includes both first response and resolution targets
- [ ] All SLA time targets are confirmed as business-hours-based or calendar-hours-based with explicit documentation
- [ ] Escalation matrix documents actions at 50%, 75%, 90%, and 100% for every tier-priority combination
- [ ] Business hours mapping table assigns a specific Business Hours record to every entitlement process AND every escalation rule entry — not just one of the two
- [ ] Notification targets in the escalation matrix correspond to real Salesforce users or queues (not just job title descriptions)
- [ ] Platform limits have been checked: ≤2,000 entitlement processes, ≤10 milestones per process, ≤40 milestone actions per milestone
- [ ] Design distinguishes between customer-facing SLA milestones and internal operational escalation rules

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Business hours must be set on both the entitlement process AND each escalation rule entry — they are independent** — Setting business hours on the entitlement process controls the milestone clock only. Escalation rule entries have their own Business Hours field. If you omit it from the escalation rule entry, the escalation fires on calendar hours 24/7 even though the milestone is tracking on business hours. The two objects do not share a clock.
2. **Default Business Hours is 24/7 — "Use Business Hours" is not the same as "restrict to working hours"** — Every org ships with a Default business hours record configured as 24/7. Attaching "Default" to an entitlement process or escalation entry does not restrict timing to working hours. You must create a separate Business Hours record with restricted days and times, then reference that record explicitly.
3. **Milestone actions fire in batch, not in real time — sub-one-hour SLA precision is not achievable declaratively** — The Salesforce time-based workflow engine processes milestone actions in batch cycles (approximately once per hour). A milestone configured to warn at 90% of a 1-hour target may warn at 58 minutes or at 62 minutes. Do not design SLAs that require minute-level precision with declarative milestones.
4. **Entry criteria on milestones use AND logic — complex OR conditions require separate milestones** — When configuring milestone entry criteria (e.g., this milestone applies when Priority = High OR Priority = Critical), the declarative criteria builder uses AND logic only. To handle OR conditions, you must create separate milestones with separate entry criteria. A tier design that assumes one milestone can cover multiple priorities with OR logic will fail silently — the milestone simply never starts.
5. **Entitlement auto-assignment does not trigger if the Account-Entitlement lookup is ambiguous** — If an Account has multiple active entitlements (different tiers for different products), the auto-assignment rule does not know which one to apply. Only one entitlement can be auto-assigned. Design the entitlement structure so each Account-product combination has at most one active entitlement, or implement a custom assignment flow.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Tier definition table | Grid of tier name x case priority x first-response target x resolution target x business hours group |
| Escalation matrix document | Grid of tier x priority x milestone threshold (50/75/90/100%) with notification target and automated action |
| Business hours mapping table | Table listing every entitlement process and every escalation rule entry with the Business Hours record each must reference |
| Milestone configuration plan | List of milestone names, time targets, entry criteria, and the four percentage-threshold actions for each |
| Platform limits validation | Checklist confirming the design stays within entitlement process, milestone, and escalation rule entry limits |

---

## Related Skills

- admin/case-management-setup — Use to implement the entitlement processes and milestones after this design skill produces the specification artifacts
- admin/escalation-rules — Use for the configuration steps for escalation rule entries after the escalation matrix design is complete
- architect/service-cloud-architecture — Use when designing the full end-to-end Service Cloud solution that this SLA matrix is a component of
- admin/products-and-pricebooks — Use when SLA tiers are tied to specific product or support plan entitlements

---

## Official Sources Used

- Salesforce Help: Entitlements Overview — https://help.salesforce.com/s/articleView?id=sf.entitlements_overview.htm
- Salesforce Help: Milestones — https://help.salesforce.com/s/articleView?id=sf.entitlements_milestone_overview.htm
- Salesforce Help: Set Up Entitlement Processes — https://help.salesforce.com/s/articleView?id=sf.entitlements_process_setup.htm
- Salesforce Help: Business Hours — https://help.salesforce.com/s/articleView?id=sf.customize_businesshours.htm
- Salesforce Help: Set Up Case Escalation Rules — https://help.salesforce.com/s/articleView?id=sf.customize_escalation.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/well-architected/overview
