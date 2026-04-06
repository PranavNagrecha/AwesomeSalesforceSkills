# LLM Anti-Patterns — Customer Effort Scoring

Common mistakes AI coding assistants make when generating or advising on Customer Effort Scoring in Salesforce.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Recommending a Custom NPS Bucketing Formula on an NPS Question Type

**What the LLM generates:** Advice like "use a formula field on SurveyResponse to reclassify Detractors as 0–5 instead of 0–6 by overriding the NPS question's bucketing logic" — or a formula field that references the NPS response value and attempts to redefine the bucket thresholds on a survey using the native NPS question type.

**Why it happens:** LLMs know that formula fields are flexible in Salesforce and often suggest formulas as the solution to "how do I customize X." They do not reliably know that NPS bucket boundaries on the NPS question type are read-only platform metadata, not a configurable value.

**Correct pattern:**

```
If custom NPS bucketing is required:
1. Do NOT use the native NPS question type.
2. Use a Rating question type with a 0–10 scale.
3. Create a formula field on SurveyResponse with custom IF/THEN bucketing logic:
   IF(Response_Value__c <= 5, 'Detractor', IF(Response_Value__c <= 7, 'Passive', 'Promoter'))
4. Document that this departs from the Salesforce native NPS calculation.
```

**Detection hint:** If the generated advice references "overriding NPS buckets" or "customizing Detractor thresholds" while still using the NPS question type, flag it as incorrect.

---

## Anti-Pattern 2: Creating SurveyInvitation Without an Opted-Out Email Check

**What the LLM generates:** A Flow or Apex snippet that creates a `SurveyInvitation` record directly from a Case closure trigger without checking `Contact.HasOptedOutOfEmail` first.

**Why it happens:** LLMs follow the "happy path" when generating survey trigger code and omit defensive null/boolean checks that are not explicitly mentioned in the prompt. The Salesforce Surveys documentation examples often also omit the opt-out check, reinforcing this pattern in training data.

**Correct pattern:**

```
Flow Decision before Create Records (SurveyInvitation):
  Condition: {!Get_Contact.HasOptedOutOfEmail} = false
             AND {!Get_Contact.Email} != null
  → True: Create SurveyInvitation
  → False: End (or log skip reason to a custom field)
```

**Detection hint:** Any generated Flow or code that creates `SurveyInvitation` without referencing `HasOptedOutOfEmail` is missing this guard.

---

## Anti-Pattern 3: Treating CSAT, NPS, and CES as Interchangeable

**What the LLM generates:** Recommendations that deploy all three metrics simultaneously (e.g., "add CSAT, NPS, and CES questions to the same post-case survey for comprehensive data"), or that substitute one metric for another without acknowledging what each measures differently.

**Why it happens:** LLMs often present CX metrics as a list of "popular options" without encoding the distinct measurement purpose of each. They default to "more data is better" reasoning that ignores survey fatigue and respondent burden.

**Correct pattern:**

```
Metric selection rules:
- CSAT: transactional satisfaction after a specific interaction (1–5 scale, Salesforce native Rating)
- NPS: relationship-level loyalty measurement, periodic (quarterly), not per-interaction
- CES: transactional friction measurement, best for support interactions where effort is the primary risk
- Rule: deploy ONE primary metric per interaction type
- Rule: NPS must have ≥90-day re-send suppression per Contact to prevent fatigue
- Rule: Never combine NPS with CSAT or CES in the same survey send window for the same Contact
```

**Detection hint:** Any recommendation to send more than one metric type to the same contact within the same send event (e.g., same case closure) should be flagged.

---

## Anti-Pattern 4: Ignoring the 60-Minute CES Trigger Window

**What the LLM generates:** A Record-Triggered Flow that sends the CES survey with a 24-hour Scheduled Path delay ("to give the customer time to verify the resolution"), or with no delay at all (immediate send on case closure).

**Why it happens:** LLMs approximate "best practices" for survey timing without encoding the specific empirical research that shows CES memory decay after 2 hours. They also commonly mirror email follow-up timing norms (24 hours) rather than CES-specific timing requirements.

**Correct pattern:**

```
Flow Scheduled Path configuration for CES:
- Delay: 15 minutes after trigger (NOT 0 minutes, NOT 24 hours)
- Acceptable range: 15–60 minutes after Case.Status = Closed
- Maximum delay for valid CES data: 2 hours post-closure
- CSAT acceptable range: up to 2–4 hours post-closure
- NPS: not time-sensitive to interaction; use periodic scheduled send
```

**Detection hint:** Any Flow configuration that sets a Scheduled Path delay of `0` minutes or `1 day` for a CES survey should be flagged as a timing anti-pattern.

---

## Anti-Pattern 5: Assuming SurveyResponse Has a Native Case Lookup Field

**What the LLM generates:** Report type recommendations or SOQL queries that reference `SurveyResponse.CaseId` as if it were a standard field — e.g., `SELECT CaseId, ResponseValue FROM SurveyResponse WHERE CaseId = :caseId`.

**Why it happens:** LLMs often model the `SurveyResponse` object by analogy to other transactional objects (CaseComment, Task, etc.) that do have standard parent lookup fields. They generate plausible-sounding field names that do not exist on the actual object schema.

**Correct pattern:**

```
SurveyResponse has no standard CaseId field.
To link CES responses to Cases:

Option A: Custom Lookup on SurveyInvitation
  - Create SurveyInvitation.Related_Case__c (Lookup to Case)
  - Populate in Flow when creating SurveyInvitation
  - Report via: SurveyInvitation → SurveyResponse (joined via SurveyInvitationId)

Option B: Custom Lookup on SurveyResponse (requires Trigger or Flow on SurveyResponse)
  - More complex; only use if response-level case attribution is required

SOQL (correct):
SELECT Id, Related_Case__c, (SELECT Id, ResponseValue FROM SurveyResponses)
FROM SurveyInvitation
WHERE Related_Case__c = :caseId
```

**Detection hint:** Any SOQL, Apex, or report type that references `SurveyResponse.CaseId` without noting it is a custom field should be flagged as a hallucinated standard field reference.

---

## Anti-Pattern 6: Recommending Feedback Management Features Without License Tier Qualification

**What the LLM generates:** Recommendations to use merge fields in survey emails, branded survey domains, lifecycle survey maps, or CRM Analytics integration without noting that these features require specific Feedback Management license tiers (Growth or Enterprise).

**Why it happens:** LLMs often present Salesforce feature capabilities without encoding the licensing gate that controls access. They describe the full feature set as if it were universally available, which leads to solution designs that cannot be implemented with the org's actual license tier.

**Correct pattern:**

```
Before recommending any Feedback Management feature, confirm the license tier:
- Starter: Basic surveys, email invitations, Flow triggers — NO merge fields, NO CRM Analytics
- Growth: Branded surveys, merge fields, lifecycle maps, advanced dashboards
- Enterprise: All Growth features + bulk send + full CRM Analytics integration

Always state the required tier alongside the feature recommendation.
Example: "Merge fields in survey email templates require Feedback Management Growth or higher."
```

**Detection hint:** Any recommendation to use merge fields, branded surveys, or CRM Analytics survey dashboards without referencing a required license tier should be flagged.
