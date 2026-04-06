# LLM Anti-Patterns — Salesforce Surveys

Common mistakes AI coding assistants make when generating or advising on Salesforce Surveys.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Hallucinating Question-Level Branching

**What the LLM generates:** Instructions to set branching rules on individual questions, such as "On question 3, if the answer is X, skip to question 7."

**Why it happens:** Most survey tools (Google Forms, SurveyMonkey, Typeform) support question-level branching. LLMs generalize from the broader survey domain and assume Salesforce works the same way.

**Correct pattern:**

```text
Branching in Salesforce Surveys is page-level only.
Place the decision-driving question on its own page.
Configure page-level routing rules: "If answer on Page 2 is X, go to Page 4."
```

**Detection hint:** Look for phrases like "skip to question," "question-level branching," or "conditional question visibility" -- these do not exist in Salesforce Surveys.

---

## Anti-Pattern 2: Ignoring the Response Cap on Base Tier

**What the LLM generates:** Survey implementation guidance that assumes unlimited responses, with no mention of the 300-response lifetime cap on the Base tier.

**Why it happens:** LLMs treat survey response collection as a standard feature with no cap. Training data rarely emphasizes the Base tier limitation because most documentation focuses on Feedback Management editions.

**Correct pattern:**

```text
Before designing any survey:
1. Confirm the org's Feedback Management tier (Base, Starter, or Growth).
2. If Base tier: SELECT COUNT() FROM SurveyResponse to check remaining capacity.
3. Base = 300 lifetime responses. Starter = 100K. Growth = unlimited.
4. If projected volume exceeds the cap, stop and recommend a tier upgrade.
```

**Detection hint:** If the output describes survey design without mentioning response limits or licensing tier, the cap check is missing.

---

## Anti-Pattern 3: Assuming Surveys Deploy Through Change Sets or Metadata API

**What the LLM generates:** Instructions to include survey components in change sets, destructive manifests, or CI/CD pipelines alongside other metadata.

**Why it happens:** LLMs know that most Salesforce configuration is metadata-deployable and generalize this to surveys. Survey content is actually stored as data in SurveyVersion records, not as traditional metadata types.

**Correct pattern:**

```text
Surveys are NOT deployable through change sets or standard Metadata API.
To move a survey between orgs:
  - Document the design (questions, pages, branching, scoring).
  - Recreate manually in the target org.
  - Or use the Survey REST API to script creation.
Do not include Survey in package.xml or change set selections.
```

**Detection hint:** Look for "Survey" in package.xml type lists, change set instructions, or CI/CD deployment manifests.

---

## Anti-Pattern 4: Omitting Guest User Profile Configuration for External Surveys

**What the LLM generates:** External survey setup instructions that create the survey and generate an invitation link but skip the Guest User Profile permission configuration.

**Why it happens:** LLMs focus on the survey builder workflow (create survey, add questions, generate link) and treat access control as a separate topic. In reality, guest user permissions are the most critical step for external surveys and the most common point of failure.

**Correct pattern:**

```text
For external (unauthenticated) survey respondents:
1. Navigate to the Experience Cloud site's Guest User Profile.
2. Grant Read and Create on: Survey, SurveyInvitation, SurveyResponse, SurveyQuestionResponse.
3. Verify field-level security on all fields used in the survey flow.
4. Test in an incognito browser with no Salesforce session.
```

**Detection hint:** If external survey instructions do not mention "Guest User Profile," "guest user permissions," or "unauthenticated access," the critical step is missing.

---

## Anti-Pattern 5: Generating Apex to Manually Calculate NPS from Raw Scores

**What the LLM generates:** Custom Apex code or formulas that manually bucket survey responses into Detractor/Passive/Promoter categories, even when using the native NPS question type.

**Why it happens:** LLMs default to building things from scratch. They do not know that the NPS question type in Salesforce automatically calculates bucketing and stores it in SurveyQuestionScore. The LLM writes redundant logic that can drift from the platform's built-in calculation.

**Correct pattern:**

```text
When using the NPS question type:
  - Salesforce automatically categorizes: Detractor (0-6), Passive (7-8), Promoter (9-10).
  - Scores are stored in SurveyQuestionScore.
  - Query SurveyQuestionScore for bucketed results — do not recompute.

Only write custom bucketing if:
  - You are using a Slider or Rating question instead of the NPS type.
  - Your organization requires non-standard NPS ranges.
```

**Detection hint:** Look for Apex or formula logic that contains `IF(score <= 6, 'Detractor', IF(score <= 8, 'Passive', 'Promoter'))` when the question type is NPS. This is redundant.

---

## Anti-Pattern 6: Recommending Survey Analytics Without Checking Tier

**What the LLM generates:** Instructions to use Survey Analytics dashboards, sentiment analysis, or advanced feedback reporting features that are only available on Feedback Management Starter or Growth tiers.

**Why it happens:** LLMs conflate Salesforce Surveys (Base) with Feedback Management (Starter/Growth). Training data includes documentation for all tiers without clearly demarcating which features require which license.

**Correct pattern:**

```text
Before recommending analytics features, confirm the tier:
  - Base: Standard reports on SurveyResponse only. No built-in analytics dashboards.
  - Starter: Includes pre-built survey analytics dashboards and lifecycle maps.
  - Growth: Adds sentiment analysis and advanced text analytics.

If the org is on Base tier, build custom reports and dashboards manually
using the Survey data model objects.
```

**Detection hint:** If the output mentions "Survey Analytics app," "sentiment analysis," or "lifecycle maps" without confirming the Feedback Management tier, the recommendation may reference unavailable features.
