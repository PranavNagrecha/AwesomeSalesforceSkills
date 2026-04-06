# LLM Anti-Patterns — Lead Scoring Requirements

Common mistakes AI coding assistants make when generating or advising on Lead Scoring Requirements.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Recommending Einstein Lead Scoring for All Scoring Requests

**What the LLM generates:** "Enable Einstein Lead Scoring in Setup under Sales Cloud Einstein. It will automatically score your leads based on your historical data."

**Why it happens:** Einstein Lead Scoring is a well-documented Salesforce feature that appears prominently in training data. LLMs default to AI-based solutions when "scoring" is mentioned, conflating the user's need for a transparent, rules-based requirements model with a predictive ML feature that requires a Sales Cloud Einstein license, a minimum of 1,000 converted leads in the past 6 months, and produces opaque scores that marketing and sales cannot interrogate or modify.

**Correct pattern:**

```
Einstein Lead Scoring is explicitly out of scope for this skill.
Rules-based composite scoring uses formula/numeric fields + Flow.
Einstein Lead Scoring:
  - Requires Sales Cloud Einstein license
  - Needs 1,000+ converted leads (6 months)
  - Produces AI scores that cannot be manually tuned
  - Does NOT replace a documented MQL/SQL definition

Recommend Einstein only when: org already has the license, sufficient history,
and the team explicitly wants predictive scoring rather than transparent criteria.
```

**Detection hint:** Output contains "Enable Einstein Lead Scoring" or "Sales Cloud Einstein" without the user asking for Einstein specifically.

---

## Anti-Pattern 2: Using a Formula Field for the Composite Score and Then Referencing It in Flow

**What the LLM generates:**

```
Create a Formula field:
  Composite_Score__c = Fit_Score__c + Engagement_Score__c

Then create a Flow with entry criteria:
  {!Lead.Composite_Score__c} >= 50
```

**Why it happens:** Formula fields are the intuitive choice for derived values. LLMs model the pattern "computed value = formula field" and apply it consistently, without knowing that Flow record-triggered conditions cannot reliably evaluate formula fields at DML time because formula values are computed at read time, not stored.

**Correct pattern:**

```
Composite_Score__c — Number(3,0), maintained by Flow:
  Trigger: When Fit_Score__c or Engagement_Score__c is updated
  Action: Update Composite_Score__c = Fit_Score__c + Engagement_Score__c

Flow entry criterion references the stored Number field:
  {!Lead.Composite_Score__c} >= 50  (valid because it is a real stored field)

Do NOT create Composite_Score__c as a Formula field if it will be used
in Flow conditions, Assignment Rules, or list views with filter criteria.
```

**Detection hint:** Output shows a Formula field definition for a score AND a Flow condition referencing that same field.

---

## Anti-Pattern 3: Defining MQL as a Single Score Threshold With No Fit Gate

**What the LLM generates:**

```
MQL Definition:
  Lead.Score__c >= 50

Set up a Flow: when Score >= 50, check Is_MQL__c = true and notify rep.
```

**Why it happens:** Single-threshold MQL definitions are simpler to specify and appear frequently in marketing automation tutorials. LLMs distill the pattern to its simplest form without accounting for the false-positive problem caused by high-engagement low-fit leads (competitors, researchers, students).

**Correct pattern:**

```
MQL Definition requires BOTH dimensions:
  Composite_Score__c >= [threshold]
  AND Fit_Score__c >= [minimum fit score]  -- e.g., at least 15/40 for Industry match
  AND required fields populated: Company != null AND Email != null

This prevents high-engagement non-buyers from triggering MQL status.
Document the fit minimum separately from the composite threshold.
```

**Detection hint:** MQL definition references only one field/threshold condition with no fit or field-completeness gate.

---

## Anti-Pattern 4: Recommending the Standard `Status` Field as the Lead Lifecycle Stage Field

**What the LLM generates:** "Use the standard Lead Status field to track lifecycle stages. Add values: Raw, Nurture, MQL, SQL, Recycled."

**Why it happens:** The standard `Status` field is the most prominent Lead picklist in Salesforce documentation and training data. LLMs recommend it as the lifecycle stage field without knowing that it controls lead conversion behavior (the "Converted" status triggers the convert dialog) and that mixing marketing lifecycle stages with Salesforce system statuses creates reporting and automation conflicts.

**Correct pattern:**

```
Use a CUSTOM picklist field for marketing lifecycle stage:
  API Name: Lead_Stage__c
  Values: Raw | Nurture | MQL | Accepted | SQL | Converted | Recycled

Keep the standard Status field for its intended purpose:
  New | Working | Unqualified | Converted
  (Converted is a system value — do not repurpose it)

Maintain Lead_Stage__c via Flow. Report on Lead_Stage__c for funnel metrics.
Use Status = Converted only when the Lead is actually being converted.
```

**Detection hint:** Output adds "MQL", "SQL", or "Recycled" as values to the standard `Status` field rather than a custom field.

---

## Anti-Pattern 5: Skipping the Handoff SLA Documentation

**What the LLM generates:** "Set the MQL threshold to 50. Create a Flow that assigns MQL leads to the Sales queue and sends an email notification to the rep."

**Why it happens:** LLMs focus on the technical implementation (Flow, fields, automation) and skip the process documentation that makes the model operationally viable. The handoff SLA is not a Salesforce configuration object — it is a written agreement — so LLMs do not model it as a required deliverable.

**Correct pattern:**

```
A complete lead scoring implementation requires a Handoff SLA document covering:

1. Score threshold for MQL flag (e.g., Composite_Score__c >= 50)
2. Required field completeness gate (e.g., Company, Title, Email must be populated)
3. Rep response time SLA (e.g., 1 business day for score >= 70, 3 days for 50-69)
4. SQL acceptance criteria (BANT/MEDDIC checklist the rep must confirm)
5. Recycle definition: conditions under which an MQL is returned to nurture
6. Recycle tracking fields: Recycle_Count__c, Recycle_Reason__c, Recycle_Date__c

Without this document, the automation is technically correct but operationally
unusable because reps have no clear expectations and marketing has no feedback loop.
```

**Detection hint:** Output describes only technical implementation (fields, Flow) with no mention of a SLA, recycle process, or rep response time requirement.

---

## Anti-Pattern 6: Writing Scoring Logic to the Account Engagement-Synced Score Field

**What the LLM generates:**

```
// Flow action: update the score field
Lead.Pardot_Score__c = Lead.Pardot_Score__c + fitPoints
```

**Why it happens:** When Account Engagement is active, the `Pardot_Score__c` (or standard `Score`) field is the most visible score field on the Lead record. LLMs treat it as a writable field for CRM-side augmentation without knowing that AE sync will silently overwrite any CRM-side edits on the next sync cycle (typically every few minutes).

**Correct pattern:**

```
Pardot_Score__c (or Score) — READ ONLY in Salesforce when AE is active.
Do not write to this field from any CRM-side Flow, Apex, or process.

For blended scoring (AE engagement + CRM fit):
  Create: Composite_Score__c (Number) — owned by Salesforce
  Flow logic: Composite_Score__c = Pardot_Score__c + Fit_Score__c
  MQL condition: Composite_Score__c >= threshold

Pardot_Score__c is a source input to the formula, never the output.
```

**Detection hint:** Output includes a Flow action or formula that writes a computed value back to `Pardot_Score__c` or the standard `Score` field.
