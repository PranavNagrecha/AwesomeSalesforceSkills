---
name: volunteer-management-requirements
description: "Use when designing or implementing volunteer management in Salesforce for nonprofits using NPSP or Nonprofit Cloud — covers V4S managed package objects vs. NPC-native volunteer objects, hours tracking, scheduling, and recognition workflows. NOT for HR systems, commercial employee volunteering programs, or Field Service Lightning crew management."
category: data
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Reliability
triggers:
  - "How do I track volunteer hours in Salesforce for a nonprofit using NPSP?"
  - "What is the difference between Volunteers for Salesforce and Nonprofit Cloud volunteer management?"
  - "TotalVolunteerHours is not updating in real time after logging hours in NPC"
  - "How to implement volunteer shift scheduling and sign-up in NPSP org"
  - "Volunteer recognition automation not triggering after hours are logged"
tags:
  - volunteer-management
  - npsp
  - nonprofit-cloud
  - V4S
  - data-model
inputs:
  - "Which platform the org runs: legacy NPSP with V4S managed package or Nonprofit Cloud (NPC) native"
  - "Volunteer processes in scope: recruitment, scheduling, hours tracking, recognition, skills matching"
  - "Expected volunteer volume and scheduling frequency"
outputs:
  - "Data model selection recommendation (V4S vs. NPC-native volunteer objects)"
  - "Object and field inventory for the chosen platform with API names"
  - "DPE rollup timing guidance for NPC implementations"
  - "Recognition and hours-tracking implementation plan"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-16
---

# Volunteer Management Requirements

This skill activates when a practitioner needs to design or implement volunteer management in a Salesforce nonprofit org. It provides the critical platform bifurcation guidance between V4S (Volunteers for Salesforce, an open-source managed package for NPSP orgs) and NPC-native volunteer objects, and prevents the most common integration mistakes caused by namespace or rollup timing misunderstandings.

---

## Before Starting

Gather this context before working on anything in this domain:

- Determine whether the org is on **NPSP** (legacy, Nonprofit Success Pack with V4S managed package) or **Nonprofit Cloud (NPC)** — the object model, namespace, and feature set are entirely different between the two.
- As of December 2025, NPSP is no longer offered to new production orgs; new implementations use NPC. Existing NPSP orgs may continue to run V4S.
- Confirm whether the organization requires skills-based volunteer matching — neither V4S nor NPC provides this natively; it requires custom objects or a third-party app.
- Identify the TotalVolunteerHours source of truth: in NPC, this field is calculated by Data Processing Engine (DPE) as a scheduled batch job, not in real time.

---

## Core Concepts

### Platform Bifurcation: V4S vs. NPC-Native

Two entirely distinct object models govern volunteer management in the Salesforce nonprofit ecosystem:

**V4S (Volunteers for Salesforce)** is an open-source managed package (GW_Volunteers namespace) deployed in NPSP orgs. It ships with:
- `GW_Volunteers__Volunteer_Campaign__c` — top-level volunteer campaign aligned to a Salesforce Campaign record
- `GW_Volunteers__Volunteer_Job__c` — a specific volunteer role or task within a campaign
- `GW_Volunteers__Volunteer_Shift__c` — a time-bound slot tied to a Job
- `GW_Volunteers__Volunteer_Hours__c` — the individual volunteer hours record linking a Contact to a Shift
- No native skills-matching object; recognition is built custom using the hours record data

**NPC (Nonprofit Cloud) native** objects are platform-first, no namespace:
- `VolunteerInitiative__c` — the top-level program or initiative
- `JobPositionAssignment__c` — assignment of a volunteer to a specific role
- `TotalVolunteerHours__c` — a calculated field populated by DPE scheduled batch, not by a trigger

### Data Processing Engine Rollup Timing (NPC)

In NPC, `TotalVolunteerHours` is NOT a real-time rollup. It is computed by a Data Processing Engine (DPE) definition that runs on a scheduled basis. This means:
- Newly logged hours do not appear immediately in the volunteer's total
- Any process or flow that reads `TotalVolunteerHours` immediately after an hours insert will see a stale value until the next DPE run
- Production DPE schedules must be configured explicitly in Setup; there is no default trigger
- Recognition workflows based on hour thresholds must trigger after DPE completion, not on the hours record insert event

### Skills Matching (Custom Build Required)

Neither V4S nor NPC ships native skills-matching functionality. Matching volunteers to roles based on skill attributes requires:
- A custom junction object linking Contact to a Skill picklist or taxonomy
- Custom matching logic in Flow or Apex that queries available shifts and filters by skill criteria
- Third-party apps (VolunteerHub, Galaxy Digital) integrated via API if the org cannot support custom development

---

## Common Patterns

### Pattern 1: V4S Shift-Based Scheduling (NPSP Orgs)

**When to use:** Org runs NPSP with V4S installed; volunteer programs are shift-based with defined time slots.

**How it works:**
1. Create a `GW_Volunteers__Volunteer_Campaign__c` record linked to a parent Salesforce Campaign
2. Create `GW_Volunteers__Volunteer_Job__c` records for each role category under the Campaign
3. Create `GW_Volunteers__Volunteer_Shift__c` records with start/end time and volunteer capacity
4. Volunteers sign up via the V4S website plugin or manually through staff; a `GW_Volunteers__Volunteer_Hours__c` record is created with Status = Confirmed
5. Hours are marked Completed post-shift; a rollup summary or trigger aggregates total hours to Contact

**Why not use Data Loader to insert directly to Opportunity:** V4S objects use the `GW_Volunteers__` namespace prefix. Any SOQL or Apex referencing these objects must use the fully qualified API name. Mixing raw API names without the prefix results in silent query failure or compile error.

### Pattern 2: NPC Initiative and Position Assignment with DPE Hours Rollup

**When to use:** Org is on Nonprofit Cloud; volunteer hours are tracked at the initiative level with DPE-based aggregation.

**How it works:**
1. Create `VolunteerInitiative__c` records for each program or event
2. Create `JobPositionAssignment__c` records linking a Contact to a defined role within an initiative
3. Log individual attendance or hours via a configured hours-tracking object or Flow
4. DPE definition reads hours logs and updates `TotalVolunteerHours__c` on the Contact during its next scheduled run
5. Recognition workflows trigger from DPE completion events or a scheduled flow, not immediately on hours logging

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| NPSP org, shift-based scheduling | V4S managed package (GW_Volunteers namespace) | Native shift and hours model; existing NPSP orgs likely already have V4S installed |
| New NPC org, initiative tracking | NPC-native VolunteerInitiative and JobPositionAssignment | No managed package required; integrated with NPC data model |
| Skills-based matching required | Custom junction object + Flow or Apex matching logic | Neither V4S nor NPC provides this natively; must be custom built |
| Real-time hours total needed | Custom rollup summary or Flow-based counter on hours object | DPE in NPC is batch, not real-time; V4S relies on trigger-based rollup |
| Volunteer self-service portal | V4S website plugin (NPSP) or Experience Cloud site with NPC objects | V4S ships a Salesforce Site plugin; NPC requires custom Experience Cloud build |
| Recognition automation at hour milestones | Flow triggered after DPE completion event (NPC) or trigger on hours record (V4S) | Timing of the trigger source must match rollup mechanism to avoid stale totals |

---

## Recommended Workflow

1. **Confirm platform** — Verify installed packages (Setup > Installed Packages) to determine if V4S (GW_Volunteers namespace) is present and whether the org is NPSP or NPC. This gates every downstream object model decision.
2. **Map volunteer lifecycle** — Document recruitment, scheduling, hours-logging, and recognition stages. Identify which are in scope and which require custom development.
3. **Select data model and document API names** — Based on platform, produce a complete object hierarchy map with fully qualified API names. For V4S, every object and field reference must include the `GW_Volunteers__` prefix.
4. **Design rollup and hours aggregation** — For NPC, document the DPE definition name, schedule frequency, and the time lag between hours logging and `TotalVolunteerHours` update. For NPSP/V4S, validate that the hours rollup trigger is active.
5. **Plan skills matching if required** — Confirm this is a custom build, not a native feature. Design the junction object model and matching logic in Flow or Apex.
6. **Design recognition workflows accounting for rollup lag** — For NPC, recognition flows must trigger after DPE completion, not on the hours insert event. Use DPE completion notification or schedule flows after the next DPE window.
7. **Validate with a pilot dataset** — Insert test volunteer records, complete a DPE run (NPC) or confirm rollup trigger fires (V4S), and verify hours totals before go-live.

---

## Review Checklist

- [ ] Platform confirmed: org is NPSP+V4S or NPC-native — not assuming one from the other
- [ ] All SOQL and Apex references to V4S objects use fully qualified namespace prefix (`GW_Volunteers__`)
- [ ] DPE schedule documented and downstream processes account for rollup lag (NPC)
- [ ] Skills-matching requirement scoped as custom build if needed — not expected to be native
- [ ] Recognition milestones trigger after DPE rollup completion, not on immediate hours insert
- [ ] Volunteer self-service portal approach selected (V4S plugin vs. Experience Cloud custom)
- [ ] End-to-end hours logging tested with confirmed rollup to Contact total

---

## Salesforce-Specific Gotchas

1. **Namespace prefix omission** — V4S objects and fields require `GW_Volunteers__` prefix in all API references. Apex classes, SOQL queries, and metadata that omit this prefix either fail at compile time or return no rows silently — a particularly dangerous silent failure mode in data migrations.
2. **DPE is not a trigger** — `TotalVolunteerHours` in NPC is updated by a scheduled DPE batch job. It will not reflect hours logged in the same session or even the same day if the DPE has not run. Any real-time display or recognition automation that reads this field immediately after an hours record insert will see a stale value.
3. **V4S and NPC objects must not be mixed** — An org on NPC that also has V4S installed for historical data must carefully segment processes. Cross-joining V4S shift records (GW namespace) with NPC initiative records in SOQL or Flows produces incorrect data associations and is not supported.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Platform selection recommendation | Written guidance confirming V4S or NPC-native with rationale |
| Object and field inventory | List of objects, fully qualified API names, and field mappings for the chosen platform |
| DPE schedule documentation | DPE job name, frequency, and lag impact on downstream processes (NPC only) |
| Custom build scope document | Specification for skills-matching and recognition if required |

---

## Related Skills

- `data/nonprofit-data-architecture` — For overall NPSP/NPC data model design and constituent data governance
- `data/constituent-data-migration` — For migrating volunteer contact records into NPSP using DataImport__c
- `architect/nonprofit-platform-architecture` — For architectural decisions spanning V4S, NPC, and third-party volunteer apps
