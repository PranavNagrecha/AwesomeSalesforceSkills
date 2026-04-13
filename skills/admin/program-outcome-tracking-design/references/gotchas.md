# Gotchas — Program Outcome Tracking Design

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: PMM Ships No Outcome or Indicator Objects

**What happens:** Program staff and BAs configuring PMM expect to find Outcome__c, Indicator__c, or similar objects in the package. The PMM (pmdm namespace) provides 8 operational objects focused on service delivery logistics. There are no outcome measurement objects. Structured logic model tracking requires custom objects built by the implementor.

**When it occurs:** Every NPSP/PMM implementation where the BA has been told "PMM handles program outcomes." The expectation is set by marketing language around "impact measurement" without clarification that PMM measures service delivery, not outcomes.

**How to avoid:** In the first PMM scoping session, explicitly walk through the 8 PMM objects and show that Stage__c on ProgramEngagement__c and Quantity__c on ServiceDelivery__c are the only outcome-adjacent fields. Scope custom object development for outcome tracking as a separate workstream from PMM setup.

---

## Gotcha 2: NPC Outcome Management Objects Do Not Exist in NPSP/PMM Orgs

**What happens:** A consultant who recently worked on NPC designs an outcome tracking system using Outcome__c and Indicator__c — the NPC Outcome Management objects. In an NPSP/PMM org, these objects do not exist. Attempts to create them as custom objects conflict with the NPC namespace if the org ever migrates to NPC.

**When it occurs:** When the same team works across both NPSP and NPC orgs, or when documentation describing NPC Outcome Management is used as a reference for NPSP design.

**How to avoid:** Explicitly confirm platform (NPSP vs NPC) at the start of every outcome design engagement. Custom Outcome objects for NPSP should use a custom namespace or unambiguous API names (e.g., `ProgramOutcome__c`) that do not conflict with NPC standard object API names.

---

## Gotcha 3: NPSP Service Delivery Quantity Tracks Outputs, Not Outcomes

**What happens:** Program staff record service delivery (1 counseling session = 1 ServiceDelivery record with Quantity = 1) and then report "total sessions delivered" as program outcomes in grant reports. Funders increasingly distinguish between outputs (activities delivered) and outcomes (changes in participant conditions). Quantity__c on ServiceDelivery__c counts outputs only.

**When it occurs:** When grant compliance templates require both output and outcome data, and the team has only configured PMM service delivery without outcome measurement.

**How to avoid:** Review every grant reporting template during requirements gathering. Identify which metrics are outputs (service counts, session attendance) vs. outcomes (employment, housing stability, skills gained). Design custom outcome tracking for any metric that cannot be derived from service delivery counts.

---

## Gotcha 4: Report Date Ranges Must Match Grant Period Definitions

**What happens:** A program reports "number of participants who gained employment" using a date range filter on the ProgramEngagement Close_Date__c or MeasurementDate__c. The grant period runs October 1 – September 30, but the team builds reports with a calendar year filter (January 1 – December 31). Grant numbers do not match what the funder expects.

**When it occurs:** During grant reporting season when staff run the report without verifying that the date filter matches the specific grant's performance period.

**How to avoid:** Build grant period as a field or related object on the Outcome or ProgramEngagement record. Create named report filters or dashboard components that are explicitly labeled with the grant name and date range. Do not rely on ad-hoc date range entry for grant compliance reports.

---

## Gotcha 5: ProgramEngagement Stage Picklist Cannot Be Used Reliably for Outcome Reporting Across Programs

**What happens:** Multiple programs share the same set of ProgramEngagement Stage picklist values (Active, Completed, Withdrawn, etc.) but define "Completed" differently. One program considers a participant "Completed" after 8 sessions; another requires 6 months of engagement. Reports on Stage = "Completed" across all programs return an inflated, undifferentiated count.

**When it occurs:** In orgs with multiple programs managed by different teams who have not agreed on shared Stage value definitions.

**How to avoid:** Define Stage picklist values per program type using Record Types on ProgramEngagement__c, or use a custom Completion Criteria field to capture the program-specific completion definition. Grant reports should filter by both Stage AND Program__c to avoid cross-program contamination.
