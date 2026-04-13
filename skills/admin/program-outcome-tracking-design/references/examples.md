# Examples — Program Outcome Tracking Design

## Example 1: Custom Outcome Object Design for NPSP/PMM Grant Reporting

**Context:** A workforce development nonprofit uses NPSP with PMM to track employment training programs. A federal grant requires reporting on: (1) number of participants who completed training, (2) number who gained employment within 90 days, and (3) average hourly wage at placement.

**Problem:** The program team assumes PMM has an Outcome object. They find only ServiceDelivery__c with Quantity__c and UnitOfMeasurement__c. There is no way to record "employment placement" or "wage at placement" in standard PMM.

**Solution:**

```text
Custom Outcome__c object design:

Fields:
- ProgramEngagement__c (Lookup) — links outcome to participant program enrollment
- OutcomeType__c (Picklist) — "Employment Placement", "Training Completion", "Certification Earned"
- MeasurementDate__c (Date) — when the outcome was measured
- HourlyWage__c (Currency) — for employment placement records
- EmployerName__c (Text) — for employment placement
- Notes__c (Long Text)

Reports:
- Participants with OutcomeType__c = "Training Completion" grouped by Program__c
- Participants with OutcomeType__c = "Employment Placement" where 
  MeasurementDate__c within 90 days of ProgramEngagement__c Close_Date__c
- Average HourlyWage__c for employed participants by cohort/grant period

Page layout placement: Outcome__c related list on ProgramEngagement__c record
```

**Why it works:** PMM operational objects handle service delivery; the custom Outcome__c object handles the impact layer. Linking outcomes to ProgramEngagement__c (not Contact) keeps the data in the PMM program context and enables reports filtered by program, cohort, and grant period.

---

## Example 2: NPC Outcome Management Setup for a Health Nonprofit

**Context:** A Nonprofit Cloud org runs a diabetes management program. The grant requires tracking: number of participants achieving HbA1c reduction, average reduction percentage, and number completing the full 12-week program.

**Problem:** The team is unfamiliar with NPC Outcome Management and manually tracks outcomes in a spreadsheet uploaded quarterly.

**Solution:**

```text
NPC Outcome Management configuration:

1. Setup > Outcome Management > Enable

2. Create Outcomes:
   - "HbA1c Reduction" — long-term health impact
   - "12-Week Program Completion" — completion milestone

3. Create Indicators:
   - Linked to "HbA1c Reduction":
     - "HbA1c Percentage at Baseline" (Numeric, unit: %)
     - "HbA1c Percentage at 12 Weeks" (Numeric, unit: %)
   - Linked to "12-Week Program Completion":
     - "Sessions Attended" (Numeric, unit: sessions)

4. Create Indicator Results:
   - Per participant per measurement point (baseline, week 6, week 12)
   - Link to Program Engagement record

5. Report: Indicator Result with filter on Program + date range
   Calculate: Average HbA1c change = baseline - 12-week result
```

**Why it works:** NPC Outcome Management provides a structured, supported framework connecting indicators to program enrollments natively. Reports on Indicator Result aggregate across the cohort without custom object development.

---

## Anti-Pattern: Using NPSP Opportunity Reports for Program Impact

**What practitioners do:** Program staff use NPSP Opportunity reports filtered by Campaign (the program campaign) to measure "program impact" — reporting total grant revenue received as evidence of program effectiveness.

**What goes wrong:** Opportunity Amount represents donations to fund the program, not program delivery results. A report showing $50,000 in grants received does not answer "how many participants completed the program" or "what outcomes were achieved." Grant reports built on Opportunity data confuse funder-facing financial reporting with program impact reporting.

**Correct approach:** Use PMM service delivery data (ServiceDelivery__c, ProgramEngagement Stage) for program metrics. Create custom Outcome__c records for measured outcomes. Build separate report sets: (1) fundraising/grant reports from Opportunity, (2) program impact reports from PMM + Outcome objects.
