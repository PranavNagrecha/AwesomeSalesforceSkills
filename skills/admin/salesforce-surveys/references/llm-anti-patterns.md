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

## Anti-Pattern 3: Naming a `Survey` Metadata Type That Does Not Exist

**What the LLM generates:** A package.xml with `<name>Survey</name>`, or the opposite over-correction — a flat assertion that surveys cannot be deployed at all and must be retyped in every org.

**Why it happens:** LLMs know most Salesforce configuration is metadata-deployable and reach for the obvious type name. Older community writing then over-corrects to "surveys aren't metadata", which is also wrong. Neither describes the actual mechanism.

**Correct pattern:**

```text
There is no `Survey` metadata type. A survey IS a Flow.

package.xml:
  <types><members>Post_Case_CSAT</members><name>Flow</name></types>   <-- the survey
  <types><members>Survey</members><name>Settings</name></types>       <-- the org switch

`Flow.processType` = Survey   (API 42.0+, created in Survey Builder)
`Flow.processType` = SurveyEnrich (API 49.0+, Survey Data Mapper)

So Flow deployment rules apply:
  - Deploying changes to an ACTIVE flow into production needs the
    "Deploy processes and flows as active" org preference. Without it the
    survey lands inactive and every scheduled invitation points at nothing.
  - A flow version with paused interviews cannot be deleted. Survey responses
    ARE flow interviews (SurveyResponse.InterviewId -> FlowInterview).
  - Responses never travel with the deployment; SurveyIds differ per org, so
    any report or automation with a hardcoded SurveyId breaks on promotion.
```

**Detection hint:** `<name>Survey</name>` under a non-`Settings` types block is always wrong. So is any sentence claiming survey content "is stored as data in SurveyVersion records, not metadata".

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

**Why it happens:** LLMs default to building things from scratch, then justify it with a confident but wrong claim about where the platform keeps the result. The redundant logic drifts from the platform's own aggregate, and the justification sends the next reader looking for a field that does not exist.

**Correct pattern:**

```text
Read the platform's own aggregate before writing any:

SELECT QuestionDeveloperName, ScoreType, Score, ResponseValue,
       ResponseCount, CumulativeScore, QuestionSkippedCount
FROM SurveyQuestionScore
WHERE SurveyId = '...' AND SurveyVersionId = '...'

ScoreType = 'Overall'    -> Score is "Score of an NPS type question"
ScoreType = 'Individual' -> ResponseValue is the answer, Score the % who gave it

Raw per-participant answers: SurveyQuestionResponse.NumberValue
(NPS, Rating, Score, Slider all land there; choice types land in ChoiceValue).

What SurveyQuestionScore does NOT have: a Detractor/Passive/Promoter column.
There is no such field anywhere in the survey object model. If a report shows
the three buckets, something computed them. Do not claim the platform stores
them, and do not claim it does not compute the NPS score -- it does, in
SurveyQuestionScore.Score on the Overall record.
```

**Detection hint:** Two failure shapes. (a) Apex or a formula containing `IF(score <= 6, 'Detractor', …)` alongside a claim that the platform already stores it — pick one. (b) Any output asserting that `SurveyQuestionScore` holds "bucketed results" or a `Bucket`/`NPSCategory` field; it holds `ScoreType`, `Score`, `ResponseValue`, `ResponseCount`, `CumulativeScore` and `QuestionSkippedCount`, and nothing named for the buckets.

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

---

## Anti-Pattern 7: Inventing SurveyInvitation Fields That Do Not Exist

**What the LLM generates:** Flow Create Records elements or Apex that set `SurveyInvitation.InvitationType = 'Link'`, `SurveyResponse.ResponderId`, `SurveyResponse.CompletedDate`, or `SurveyVersion.Status`. Also common: a Case lookup field pointing at the survey.

**Why it happens:** These are the names the field *ought* to have. LLMs pattern-match from other Salesforce objects (`Status` is nearly universal; `Owner`/`Responder` reads naturally) and from third-party survey APIs where an invitation genuinely has a type. Nothing in the training signal marks them as absent.

**Correct pattern:**

```text
FABRICATED                        REAL
SurveyInvitation.InvitationType   (no such field -- channel is implied by
                                   CommunityId + OptionsAllowGuestUserResponse)
SurveyResponse.ResponderId        SurveyResponse.SubmitterId (-> Contact, Lead, User)
SurveyResponse.CompletedDate      SurveyResponse.CompletionDateTime
SurveyResponse.ResponseStatus     SurveyResponse.Status
                                  (ResponseStatus lives on SurveyInvitation)
SurveyVersion.Status              SurveyVersion.SurveyStatus
                                  (Active / Draft / Obsolete / InvalidDraft)
Survey.ActiveVersionId            Survey.ActiveVersionID  (capital D --
                                  but LatestVersionId is lowercase d)
Case.Survey__c or similar         SurveySubject: ParentId = the SurveyInvitation
                                  or SurveyResponse, SubjectId = the Case

WRITABLE ON SurveyInvitation: Name, SurveyId, ParticipantId, CommunityId,
  EmailBrandingId, OwnerId, IsDefault, InviteExpiryDateTime,
  OptionsAllowGuestUserResponse, OptionsAllowParticipantAccessTheirResponse,
  OptionsCollectAnonymousResponse.
DERIVED, will fail: ContactId, LeadId, UserId, InvitationLink, ResponseStatus.
```

**Detection hint:** Any survey field name not on the list above should be checked against the Object Reference before it ships. The tell for the derived-field mistake specifically is a Flow that sets `ContactId` — it reads perfectly and fails at run time, because Salesforce populates the typed lookup from `ParticipantId`.
