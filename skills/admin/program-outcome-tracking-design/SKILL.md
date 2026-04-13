---
name: program-outcome-tracking-design
description: "Design guidance for program outcome measurement in Salesforce nonprofit orgs: logic model structure, indicator taxonomy, impact reporting design, and grant compliance reporting using NPSP Program Management Module (PMM) or Nonprofit Cloud (NPC) Outcome Management. NOT for CRM Analytics dashboards, NPSP PMM implementation/setup, or fundraising data analysis."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Reliability
triggers:
  - "how do I design outcome tracking and impact reporting for a nonprofit program in Salesforce"
  - "building a logic model with indicators in NPSP or Nonprofit Cloud PMM"
  - "what objects do I use to track program indicators and outcomes for grant reporting"
  - "designing service delivery metrics and evaluation framework in Salesforce nonprofit"
  - "NPSP PMM has no Outcome or Indicator objects — how do I track program impact"
tags:
  - npsp
  - nonprofit-cloud
  - pmm
  - program-management
  - outcomes
  - impact-reporting
  - grant-compliance
inputs:
  - "NPSP vs Nonprofit Cloud (NPC) — which platform is the org on"
  - "Program types and service delivery models (direct service, training, advocacy)"
  - "Grant reporting requirements and indicator definitions"
  - "Existing PMM program and service configuration"
outputs:
  - "Program outcome data model design (custom objects or NPC Outcome Management)"
  - "Indicator taxonomy and measurement approach"
  - "Grant compliance report design"
  - "Logic model structure mapped to Salesforce objects"
dependencies:
  - npsp-program-management
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-13
---

# Program Outcome Tracking Design

This skill activates when a nonprofit BA or program staff member needs to design an outcome measurement framework in Salesforce — mapping logic model components to platform objects, building indicator tracking, and designing grant compliance reports. It does NOT cover CRM Analytics report building, PMM package setup, or fundraising analysis.

---

## Before Starting

Gather this context before working on anything in this domain:

- **NPSP vs Nonprofit Cloud (NPC):** The outcome data model differs significantly between platforms. NPSP with PMM has NO native Outcome or Indicator objects — all outcome tracking requires custom objects. NPC has a dedicated Outcome Management feature with native objects. Confirm which platform the org is on before designing anything.
- **PMM operational objects:** PMM ships 8 operational objects (Program__c, Service__c, ProgramEngagement__c, ProgramCohort__c, ServiceDelivery__c, ServiceSchedule__c, ServiceParticipant__c, ServiceSession__c). Outcome data in PMM lives only as `Quantity__c` and `UnitOfMeasurement__c` on ServiceDelivery__c, and `Stage__c` on ProgramEngagement__c. Structured indicator tracking requires custom fields or custom objects.
- **Grant compliance requirements:** Grant reports typically require aggregated indicators (number served, number completing program, percentage achieving outcomes) mapped to specific services and date ranges. Design reports before designing the data model — reports drive what fields are needed.
- **NPSP is no longer offered in new production orgs** as of December 2025. New nonprofits use Nonprofit Cloud (NPC). Orgs on NPSP are legacy; NPC orgs have different object models.

---

## Core Concepts

### PMM Does Not Ship Outcome or Indicator Objects

NPSP Program Management Module (pmdm namespace) provides operational service delivery tracking — who received what service when. It does NOT provide dedicated Outcome__c, Indicator__c, or LogicModel__c objects. Nonprofits that expect PMM to "do outcomes" are commonly disappointed.

What PMM provides for outcome-adjacent tracking:
- `Stage__c` on ProgramEngagement__c (Active, Inactive, Graduated, etc.) — crude completion tracking
- `Quantity__c` and `UnitOfMeasurement__c` on ServiceDelivery__c — units of service delivered
- Custom fields on any PMM object — requires implementor design

Structured logic model outcome tracking (indicators, targets, actuals, baseline comparisons) requires **custom objects** on NPSP/PMM orgs.

### NPC Outcome Management (NPC Only)

Nonprofit Cloud has a distinct Outcome Management feature with native objects:
- **Outcome** — represents a program result statement
- **Indicator** — a measurable proxy for an Outcome
- **Indicator Result** — the actual measured value at a point in time
- **Participant Goal** — an individual-level outcome target

This feature is NOT available in NPSP/PMM orgs. Designs using Outcome or Indicator objects require NPC licensing.

### Logic Model Structure in Salesforce

A standard nonprofit logic model maps inputs → activities → outputs → outcomes → impact. In Salesforce:

| Logic Model Layer | PMM Object | Notes |
|---|---|---|
| Activities | Service__c | Type of service delivered |
| Outputs | ServiceDelivery__c (Quantity__c) | Units delivered |
| Outcomes (completion) | ProgramEngagement__c (Stage__c) | Graduated/completed status |
| Outcomes (measured) | Custom Outcome__c or NPC Indicator | Requires custom design or NPC |
| Impact | Reports and dashboards | Aggregated across cohorts |

---

## Common Patterns

### Custom Outcome Tracking on NPSP/PMM

**When to use:** NPSP org with PMM where grant reporting requires measured outcomes beyond service counts.

**How it works:**
1. Create a custom `Outcome__c` object with fields: `Program__c` (lookup to Program__c), `Indicator__c` (text or lookup), `TargetValue__c`, `ActualValue__c`, `MeasurementDate__c`, `ProgramEngagement__c` (lookup).
2. Define the indicator taxonomy based on grant requirements (e.g., "Number who gained employment," "Percentage with improved housing stability").
3. Staff enter Outcome records per participant per measurement period.
4. Build reports joining ProgramEngagement__c → Outcome__c to aggregate indicators by program and grant period.

**Why not ServiceDelivery Quantity:** ServiceDelivery Quantity tracks units of service (sessions, hours) — not outcomes. Using it for outcome measurement conflates activity outputs with program results, producing grant reports that describe activity, not impact.

### NPC Outcome Management

**When to use:** Nonprofit Cloud org with Outcome Management enabled.

**How it works:**
1. Enable Outcome Management in NPC Setup.
2. Create Outcome records defining program result statements.
3. Create Indicator records linked to each Outcome with measurement type and unit.
4. Create Indicator Results at assessment intervals (monthly, quarterly, program end).
5. Create Participant Goal records for individual-level targets.
6. Build reports on Indicator Result to track aggregate progress vs. targets.

**Why not custom objects:** NPC Outcome Management provides a structured, supported framework that connects outcomes to program enrollments natively, reducing custom development and avoiding data model fragmentation.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| NPSP/PMM org — simple output counting | ServiceDelivery__c Quantity__c + reports | Built-in, no custom objects needed |
| NPSP/PMM org — grant requires measured outcomes | Custom Outcome__c object + ProgramEngagement lookup | PMM has no native Outcome object |
| NPC org — outcome measurement | NPC Outcome Management (Outcome, Indicator, Indicator Result) | Native, supported, no custom dev |
| Grant reporting on participants who completed program | ProgramEngagement Stage__c = Graduated | Built-in completion tracking |
| Pre/post measurement (surveys, assessments) | Custom Outcome__c with pre/post measurement date fields | PMM does not have survey instruments |
| CRM Analytics impact dashboards | CRM Analytics with PMM data sources | This skill does NOT cover CRM Analytics — separate skill |

---

## Recommended Workflow

1. **Platform confirmation** — Determine NPSP/PMM or Nonprofit Cloud (NPC). This is the branching decision point for all subsequent design choices.
2. **Grant requirements analysis** — Collect all grant reporting templates and indicator definitions before designing objects. Reports drive data model requirements.
3. **Logic model mapping** — Map each logic model component (outputs, outcomes, impact) to available PMM objects and identify gaps requiring custom objects.
4. **Data model design** — For NPSP/PMM, design custom Outcome__c object with appropriate fields and lookups. For NPC, configure Outcome Management.
5. **Report design** — Design the grant compliance report layout first; validate that the data model supports the required aggregations (by program, by service, by cohort, by grant period).
6. **Staff training design** — Define the data entry workflow for staff: when to create Outcome records, how to measure indicators, and how measurement dates align with grant reporting periods.
7. **Review** — Validate that outcome objects use PMM standard object lookups (not Contact directly), that all grant indicator definitions are reflected in the data model, and that report date ranges match grant periods.

---

## Review Checklist

- [ ] Platform confirmed: NPSP/PMM or Nonprofit Cloud (NPC)
- [ ] Grant indicator definitions collected and mapped to data model fields
- [ ] Custom Outcome__c designed if NPSP/PMM (PMM ships no native Outcome object)
- [ ] Outcome records linked to ProgramEngagement__c (not Contact directly)
- [ ] Report design reviewed against grant compliance template before building
- [ ] NPSP Opportunity-based reports are NOT used for program impact data
- [ ] NPC Outcome Management objects are NOT referenced in NPSP/PMM org designs

---

## Salesforce-Specific Gotchas

1. **PMM ships no Outcome or Indicator objects** — The most common misconception. PMM provides operational service delivery tracking, not outcome measurement. Outcome tracking requires custom objects on NPSP/PMM orgs or the NPC Outcome Management feature.
2. **Using NPSP Opportunity reports for program impact is incorrect** — Opportunities in NPSP represent gifts, not program results. Reports on Opportunity Amount have no relationship to program outcomes. Grant reports using Opportunity data to claim program impact conflate fundraising data with program data.
3. **NPC Outcome Management is not available in NPSP/PMM orgs** — Attempting to create Outcome or Indicator objects in an NPSP/PMM org fails — these are NPC-specific objects. Design for each platform separately.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Logic model to Salesforce mapping | Logic model components mapped to PMM objects and custom objects |
| Outcome data model design | Custom Outcome__c or NPC Outcome Management object model |
| Grant compliance report design | Report layout showing indicator aggregations aligned to grant template |

---

## Related Skills

- `npsp-program-management` — For PMM configuration, service delivery setup, and operational PMM administration
- `donor-lifecycle-requirements` — For designing the donor engagement side of nonprofit CRM alongside program tracking
