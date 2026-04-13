# Program Outcome Tracking Design — Work Template

Use this template when working on tasks in this area.

---

## Scope

**Skill:** `program-outcome-tracking-design`

**Request summary:** (fill in what the user asked for)

---

## Context Gathered

Answer each question before designing outcome objects or reports.

**Platform confirmation (critical branching decision):**
- [ ] NPSP with Program Management Module (PMM) — pmdm namespace installed
  - PMM has NO native Outcome or Indicator objects — custom objects required
- [ ] Nonprofit Cloud (NPC) — use native Outcome Management feature
  - Do NOT build custom outcome objects; configure Outcome Management instead
- [ ] Unknown — must confirm before proceeding

**PMM objects present (NPSP/PMM only):**
- [ ] Program__c (pmdm__Program__c)
- [ ] ProgramEngagement__c (pmdm__ProgramEngagement__c)
- [ ] ServiceDelivery__c (pmdm__ServiceDelivery__c)
- [ ] ServiceSchedule__c, ServiceSession__c, ServiceParticipant__c

**Grant reporting requirements collected:**

| Grant Funder | Report Due Date | Required Indicators | Aggregation Level |
|---|---|---|---|
| | | | |

**Program types in scope:**
- [ ] Direct service (case management, counseling, food assistance)
- [ ] Training / workforce development
- [ ] Education / tutoring
- [ ] Advocacy / policy
- [ ] Other: _______________

---

## Logic Model Mapping

Map each logic model component to Salesforce objects before designing custom fields or objects.

| Logic Model Layer | Salesforce Object | Field / Approach | Gap Requiring Custom Design? |
|---|---|---|---|
| Inputs | (organization resources, funding) | Tracked outside Salesforce or in custom fields | |
| Activities | pmdm__Service__c | Service name = activity type | |
| Outputs | pmdm__ServiceDelivery__c | Quantity__c + UnitOfMeasurement__c | Only if additional output fields needed |
| Outputs (attendance/completion) | pmdm__ProgramEngagement__c | Stage__c (Graduated, Active, Inactive) | |
| Outcomes (measured) | Custom Outcome__c OR NPC Indicator | Requires custom design (NPSP) or Outcome Mgmt (NPC) | YES — design required |
| Impact | Reports and dashboards | Aggregated across cohorts | |

**Gap summary:** (list outcome tracking gaps not covered by PMM standard objects)

---

## Outcome Data Model Design

### NPSP/PMM Path: Custom Outcome__c Object

**Custom Outcome__c fields:**

| Field Label | API Name | Type | Notes |
|---|---|---|---|
| Program | Program__c | Lookup (pmdm__Program__c) | |
| Program Engagement | ProgramEngagement__c | Lookup (pmdm__ProgramEngagement__c) | Link outcomes to participant |
| Indicator | Indicator__c | Picklist or Lookup | Grant-defined indicator name |
| Measurement Date | MeasurementDate__c | Date | When measurement was taken |
| Target Value | TargetValue__c | Number | Grant target for this indicator |
| Actual Value | ActualValue__c | Number | Measured result |
| Measurement Period | MeasurementPeriod__c | Picklist (Baseline, Mid, End, Annual) | |
| Notes | Notes__c | Long Text Area | Qualitative context |

**Indicator taxonomy (from grant requirements):**

| Indicator Name | Definition | Measurement Method | Frequency |
|---|---|---|---|
| | | | |

### NPC Path: Outcome Management Configuration

- [ ] Outcome Management enabled in NPC Setup
- [ ] Outcome records created (result statements per program)
- [ ] Indicator records created (measurable proxy per Outcome)
- [ ] Measurement type and unit defined per Indicator
- [ ] Participant Goal records designed (individual-level targets)
- [ ] Indicator Result entry workflow designed for staff

---

## Grant Compliance Report Design

Design reports BEFORE confirming data model — reports define what fields are needed.

**Report 1: [Grant Name] Indicator Summary**

| Report Element | Object / Field | Filter |
|---|---|---|
| Program | pmdm__Program__c.Name | Program = [name] |
| Indicator | Outcome__c.Indicator__c | |
| Count achieved | COUNT(Outcome__c) where ActualValue >= TargetValue | |
| Grant period | Outcome__c.MeasurementDate__c | Date range = grant period |

**Report 2: Participant Completion by Program**

| Report Element | Object / Field | Filter |
|---|---|---|
| Program | pmdm__Program__c.Name | |
| Enrolled | COUNT(pmdm__ProgramEngagement__c) | Stage = Active or Graduated |
| Graduated | COUNT(pmdm__ProgramEngagement__c) where Stage = Graduated | |
| Graduation rate | Formula | |

(Add additional report designs as needed for each grant requirement)

---

## Staff Data Entry Workflow

Define when and how staff enter outcome data.

| Step | Who | When | Object / Action |
|---|---|---|---|
| Program enrollment | Case manager | Day of first service | Create ProgramEngagement__c |
| Service delivery log | Case manager | After each session | Create ServiceDelivery__c |
| Mid-program outcome | Program manager | [Define date trigger] | Create Outcome__c record |
| Program completion | Case manager | Final session | Update ProgramEngagement__c Stage to Graduated |
| End-of-program outcome | Program manager | Within 30 days of graduation | Create Outcome__c record |

---

## Review Checklist

- [ ] Platform confirmed: NPSP/PMM or Nonprofit Cloud (NPC)
- [ ] Grant indicator definitions collected and mapped to data model fields
- [ ] Custom Outcome__c designed if NPSP/PMM (PMM ships no native Outcome object)
- [ ] Outcome records linked to ProgramEngagement__c (not Contact directly)
- [ ] Report design reviewed against grant compliance template before building
- [ ] NPSP Opportunity-based reports NOT used for program impact data
- [ ] NPC Outcome Management objects NOT referenced in NPSP/PMM org designs
- [ ] Staff data entry workflow defined and documented

---

## Notes

(Record deviations from the standard pattern and justification)
