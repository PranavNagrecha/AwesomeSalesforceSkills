# LLM Anti-Patterns — Marketing Automation Requirements

Common mistakes AI coding assistants make when generating or advising on Marketing Automation Requirements.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Setting MQL Threshold Without Requiring Sales Alignment

**What the LLM generates:** A requirements document or MQL specification that defines a score threshold (e.g., "Score >= 80") based on platform defaults or marketing input alone, with no mention of a joint marketing/sales sign-off requirement.

**Why it happens:** LLMs tend to optimize for completeness and specificity in output documents. Producing a concrete number (80, 100, 150) looks like a complete answer. The political and process requirement — that the threshold must be a joint marketing+sales decision with a documented approver and date — is not a technical rule, so it is frequently omitted from generated content.

**Correct pattern:**

```
MQL Threshold Definition (DRAFT — REQUIRES SIGN-OFF)
Proposed threshold: Score >= 100 AND Grade >= B
[BLOCKER] This threshold is a proposal only. It must be reviewed and
approved in a joint session with both VP Marketing and VP Sales before
implementation begins. Record approver names and sign-off date here:

Marketing approver: _______________  Date: ___________
Sales approver:    _______________  Date: ___________

Implementation is BLOCKED until this section is complete.
```

**Detection hint:** Any requirements document that specifies an MQL score threshold without a "sign-off" or "approved by" field containing two named approvers (marketing AND sales) is incomplete. Flag and return for alignment.

---

## Anti-Pattern 2: Conflating MCE Automation Studio with MCAE Engagement Studio

**What the LLM generates:** Requirements language that describes using "Automation Studio" to route individual leads to Sales when they reach an MQL score threshold, or that uses MCE and MCAE terminology interchangeably.

**Why it happens:** Both platforms use the word "automation" and both are Salesforce marketing products. LLMs trained on broad Salesforce documentation often collapse the distinction because the terms co-occur in Salesforce marketing content. The architectural difference — Automation Studio is a batch SQL engine; Engagement Studio is a real-time prospect-level rule engine — is non-obvious from product names alone.

**Correct pattern:**

```
MCAE Automation Rule (prospect-level, near-real-time):
  Trigger: Prospect Score >= 100 AND Grade >= B
  Actions: Assign to Sales Queue, Create CRM Task, Update Is_MQL__c = true
  Engine: MCAE Automation Rules (NOT Automation Studio)

MCE Automation Studio (batch, scheduled):
  Activities: data extract, SQL queries on data extensions, file imports
  Scope: batch data operations only — NOT for real-time prospect routing
```

**Detection hint:** If generated requirements mention "Automation Studio" in the context of real-time lead routing, score-threshold triggers, or individual prospect assignment — flag as incorrect. Automation Studio handles batch data operations, not individual prospect routing.

---

## Anti-Pattern 3: Omitting Score Decay Rules from Scoring Specification

**What the LLM generates:** A scoring model specification that lists activity types and point values but does not include score decay rules, treating the score as cumulative and permanent.

**Why it happens:** Score decay is a less prominent concept than scoring weights in Salesforce documentation and marketing content. LLMs default to generating what they see most frequently — the activity-to-points mapping — and omit decay because it is a secondary, platform-specific concept that requires explicit prompting to surface.

**Correct pattern:**

```
SCORE DECAY RULES (required — omitting this section is a specification error):
Rule 1: Reduce score by 10 points after 30 days of no tracked activity
Rule 2: Reduce score by 20 additional points after 60 days of no tracked activity
Notes:
- Decay does not reduce score below 0
- Decay is applied by MCAE on a scheduled cadence, not in real time
- Decay does not trigger automation rules or completion actions
- MQL threshold should be calibrated with decay in effect (e.g., if max score
  is 200 and decay removes 30 points after 60 days, the effective sustained
  MQL threshold should account for the decay floor)
```

**Detection hint:** Any scoring specification that does not contain a "decay" or "score reduction" section is incomplete. The absence of decay rules in a scoring model specification is always a gap, not an intentional omission.

---

## Anti-Pattern 4: Treating the MCAE Lifecycle Report as a CRM Data Source

**What the LLM generates:** Requirements or dashboards specs that reference "the Lifecycle Stage field" on Lead or Opportunity as if it is automatically populated by MCAE, or that specify CRM reports filtered by lifecycle stage without requiring a custom field to store that value.

**Why it happens:** The MCAE Lifecycle Report is prominent in MCAE documentation and marketing analytics discussions. LLMs associate "lifecycle stage" with CRM reporting and assume a field exists because the report exists. The distinction between a computed report metric and a stored CRM field value is not surfaced in most training content.

**Correct pattern:**

```
LIFECYCLE STAGE CRM FIELD REQUIREMENT:
The MCAE Lifecycle Report computes stage metrics at report runtime from MCAE
activity data. It does NOT write a stage value to a CRM field automatically.

To enable CRM-side lifecycle reporting, the following custom field must be
created on Lead and Contact:
  Field: Lifecycle_Stage__c
  Type: Picklist
  Values: Visitor | Prospect | MQL | SQL | Opportunity | Customer | Won
  Write access: MCAE integration user only (protected from manual edits)

An MCAE Automation Rule or Engagement Studio Completion Action must update
this field at each stage transition. Enumerate all required automation actions
that write to this field in the handoff mechanism specification.
```

**Detection hint:** Any requirements document that references lifecycle stage reporting in Salesforce CRM without specifying a custom `Lifecycle_Stage__c` picklist field and the automation that populates it is missing a data model requirement.

---

## Anti-Pattern 5: Specifying Score Threshold Without Score Ceiling or Negative Scoring

**What the LLM generates:** A scoring specification that defines point weights for positive activities and an MQL threshold, but omits (a) a ceiling score that caps maximum accumulation, and (b) negative score deductions for disqualifying signals such as unsubscribe, hard bounce, or opt-out.

**Why it happens:** Positive scoring is the most discussed aspect of lead scoring in training content. Score ceilings are an advanced configuration concept that LLMs do not generate unless explicitly prompted. Negative scoring (unsubscribe, hard bounce deductions) is mentioned in MCAE documentation but is less prominent than positive scoring examples.

**Correct pattern:**

```
NEGATIVE SCORING (required — disqualification signals):
  Unsubscribe (opt-out):  -50 points
  Hard bounce:            -75 points
  Spam complaint:         -50 points
Negative scoring prevents disengaged or undeliverable contacts from
retaining accumulated score from past campaigns.

CEILING SCORE: 200 points
Points are not awarded above the ceiling. This prevents highly active but
non-converting contacts (competitors, researchers) from permanently occupying
the top of the MQL queue and consuming Sales capacity.

Rationale: a contact who browses 200 pages scores 200 points at default weights
(1 pt per page view) without ceiling enforcement. A ceiling ensures that score
reflects recent, diverse engagement rather than sheer volume of low-intent activity.
```

**Detection hint:** Any scoring specification that does not include (a) at least two negative scoring entries (unsubscribe, hard bounce) and (b) a ceiling score is incomplete. Check for both omissions independently — they often appear separately.
