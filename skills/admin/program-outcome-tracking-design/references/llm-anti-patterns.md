# LLM Anti-Patterns — Program Outcome Tracking Design

Common mistakes AI coding assistants make when generating or advising on Program Outcome Tracking Design.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Assuming PMM Has Outcome__c or Indicator__c Objects

**What the LLM generates:** SOQL like `SELECT Id FROM pmdm__Outcome__c` or data model designs referencing `pmdm__Indicator__c`, `pmdm__LogicModel__c`, or similar PMM-namespaced outcome objects.

**Why it happens:** LLMs trained on nonprofit Salesforce content encounter the phrase "PMM for program impact measurement" without distinguishing operational service tracking from outcome measurement. The assumption is that a "program management" package includes outcomes.

**Correct pattern:**

```text
PMM standard objects (pmdm namespace): 8 objects only
- Program__c, Service__c, ProgramEngagement__c, ProgramCohort__c
- ServiceDelivery__c, ServiceSchedule__c, ServiceParticipant__c, ServiceSession__c

There is NO pmdm__Outcome__c, pmdm__Indicator__c, or pmdm__LogicModel__c

For outcome tracking on NPSP/PMM: design custom objects
For outcome tracking on NPC: use Outcome Management feature
```

**Detection hint:** Any SOQL or object reference with `pmdm__Outcome` or `pmdm__Indicator` is wrong. These objects do not exist in the PMM package.

---

## Anti-Pattern 2: Using NPSP Opportunities for Program Outcome Reporting

**What the LLM generates:** Reports or SOQL using `npe01__Amount__c` on Opportunity, filtered by Campaign (representing a program), to produce "program metrics" or "participants served" counts.

**Why it happens:** NPSP Opportunity is the most prominent NPSP object in training data. LLMs use it for all reporting tasks without understanding the separation between fundraising data and program data.

**Correct pattern:**

```soql
-- WRONG: Opportunities are gifts, not program deliveries
SELECT COUNT(Id) FROM Opportunity WHERE Campaign.Name = 'Employment Program 2026'

-- CORRECT: ServiceDelivery for output counts
SELECT COUNT(Id) FROM pmdm__ServiceDelivery__c 
WHERE pmdm__ProgramEngagement__r.pmdm__Program__r.Name = 'Employment Program 2026'

-- CORRECT: ProgramEngagement for completion counts
SELECT COUNT(Id) FROM pmdm__ProgramEngagement__c 
WHERE pmdm__Stage__c = 'Graduated' AND pmdm__Program__r.Name = 'Employment Program 2026'
```

**Detection hint:** Any program metrics query filtering on Opportunity with a Campaign filter is a flag for program/fundraising data conflation.

---

## Anti-Pattern 3: Recommending NPC Outcome Management for NPSP/PMM Orgs

**What the LLM generates:** Implementation guidance that says "use Outcome Management" or references Outcome, Indicator, or Indicator Result objects for an org that is on NPSP/PMM (not Nonprofit Cloud).

**Why it happens:** NPC Outcome Management is well-documented and appears in nonprofit Salesforce content alongside PMM content. LLMs recommend it without confirming whether the org is NPC or NPSP/PMM.

**Correct pattern:**

```text
Platform check before outcome design:
- NPSP/PMM org: no Outcome Management feature; design custom Outcome__c objects
- Nonprofit Cloud (NPC) org: use Outcome Management (Setup > Outcome Management > Enable)

How to confirm: check for pmdm__ namespace (NPSP/PMM) vs no namespace on Program objects (NPC)
Or: check Installed Packages for "Nonprofit Success Pack" (NPSP/PMM) vs 
    "Nonprofit Cloud" (NPC native objects)
```

**Detection hint:** Any guidance recommending "Outcome Management" or `OutcomeResult` objects without confirming NPC platform should be flagged.

---

## Anti-Pattern 4: Linking Outcome Records Directly to Contact Instead of ProgramEngagement

**What the LLM generates:** Custom Outcome__c object designs with a `Contact__c` lookup as the primary relationship, bypassing the PMM program context.

**Why it happens:** Contact is the most common Salesforce record type for individual-level data. LLMs default to Contact relationships without understanding that program context requires linking through ProgramEngagement.

**Correct pattern:**

```text
Correct Outcome__c relationship design:
- ProgramEngagement__c (Lookup) — primary relationship, preserves program/cohort context
- Contact__c can be a formula field or secondary lookup derived from ProgramEngagement

Benefits of ProgramEngagement linkage:
- Reports can filter by Program, Service, Cohort, and Outcome together
- Participants in multiple programs have distinct outcome sets per enrollment
- Grant reports filter by program enrollment date, not Contact creation date
```

**Detection hint:** Any custom Outcome object with only a Contact lookup and no ProgramEngagement lookup should be reviewed for program context loss.

---

## Anti-Pattern 5: Treating Service Delivery Quantity as Outcome Data

**What the LLM generates:** Grant report designs that use `SUM(pmdm__Quantity__c)` on ServiceDelivery__c as the primary outcome metric, labeling it as "program outcomes" in the reporting artifact.

**Why it happens:** ServiceDelivery Quantity is the most accessible quantitative field in PMM. LLMs use available numeric fields for "metrics" without understanding the output/outcome distinction.

**Correct pattern:**

```text
ServiceDelivery Quantity = OUTPUTS (units of service delivered)
Examples: sessions attended, meals delivered, hours of tutoring

Program OUTCOMES require measured changes in participant condition:
- Employment gained (Y/N, wage, employer)
- Housing stability improved (custom assessment)
- Health metric change (pre/post measurement)
- Skills certified (credential type, issuer)

Use ServiceDelivery Quantity for output reporting.
Use custom Outcome__c or NPC Indicator Result for outcome reporting.
Both are needed for complete grant compliance reporting.
```

**Detection hint:** Any grant report design that relies solely on ServiceDelivery Quantity for "outcome" metrics without custom outcome tracking should be flagged.
