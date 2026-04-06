# Gotchas — Salesforce Surveys

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Base Tier 300-Response Lifetime Cap Is Absolute

**What happens:** The Base Salesforce Surveys tier includes exactly 300 survey responses across all surveys in the org -- lifetime, not per month or per year. Once this cap is reached, all surveys stop accepting responses with no advance warning. There is no email notification, no dashboard alert, and no grace period.

**When it occurs:** Orgs that start with surveys for a pilot project can silently exhaust the cap before the real rollout begins. Testing in production also consumes responses against the cap.

**How to avoid:** Check the current response count before designing any new survey (`SELECT COUNT() FROM SurveyResponse`). If the org expects more than a few hundred responses total, budget for Feedback Management Starter (100K) or Growth (unlimited) before investing in survey design.

---

## Gotcha 2: Guest User Profile Permissions Are Not Inherited from the Survey

**What happens:** Creating and activating a survey does not automatically grant guest users the ability to respond. The Experience Cloud site's Guest User Profile must explicitly have Read and Create permissions on Survey, SurveyInvitation, SurveyResponse, and SurveyQuestionResponse objects. Without these, external respondents see a blank page or a generic "insufficient privileges" error.

**When it occurs:** Every time an admin creates their first external-facing survey. Internal testing while logged in as an admin will never surface this issue because the admin has full access.

**How to avoid:** Immediately after creating an external survey, test it in an incognito browser with no Salesforce session. If the survey does not render or submit, check the Guest User Profile's object and field-level permissions.

---

## Gotcha 3: Branching Is Page-Level, Not Question-Level

**What happens:** Admins who are used to tools like Google Forms or SurveyMonkey expect to branch based on individual question answers. Salesforce Surveys only support page-level branching. If two questions on the same page need different routing destinations, the branching logic cannot distinguish between them.

**When it occurs:** When designing surveys with complex conditional logic, especially if mixing NPS and Multiple Choice questions on a single page.

**How to avoid:** Place every question that drives branching on its own page. Treat each page as a decision node in a flowchart. Plan the page structure before building the survey.

---

## Gotcha 4: SurveyVersion Must Be Activated Before Responses Are Accepted

**What happens:** A survey can be saved and appear in the survey builder without being activated. Sending invitations for an inactive SurveyVersion results in broken links or empty pages. The invitation URL technically resolves, but the survey form does not render.

**When it occurs:** When admins create a survey draft, share the link for stakeholder review, and then forget to activate it before sending to actual respondents.

**How to avoid:** Always verify the SurveyVersion status is "Active" before generating invitations. In automation, query SurveyVersion where `Status = 'Active'` and fail the process explicitly if no active version exists.

---

## Gotcha 5: NPS Score Bucketing Is Fixed and Cannot Be Customized

**What happens:** The NPS question type automatically categorizes responses into Detractor (0-6), Passive (7-8), and Promoter (9-10). These ranges are hardcoded by Salesforce and cannot be adjusted. Some organizations use different NPS scales or want to count 6 as Passive; this is not possible with the native NPS question type.

**When it occurs:** When stakeholders expect custom NPS bucketing logic or when comparing Salesforce NPS data with data from external tools that use different thresholds.

**How to avoid:** If custom NPS ranges are required, use a Slider or Rating question instead of the NPS question type, and calculate the bucketing in reports or Apex. Accept that the built-in NPS question type follows the standard Bain/Satmetrix NPS methodology with no room for customization.

---

## Gotcha 6: Matrix Questions Require Spring '23 or Later

**What happens:** The Matrix question type (grid with rows and columns) was introduced in Spring '23. Orgs on older API versions or with delayed release updates do not have access to this question type. Attempting to deploy a survey containing Matrix questions to a pre-Spring '23 org fails silently in metadata deployment or renders an incomplete survey.

**When it occurs:** When building surveys in a sandbox on a newer release and deploying to a production org that has not yet received the update, or when referencing older documentation that does not mention Matrix questions.

**How to avoid:** Confirm the target org's release version before using Matrix questions. If cross-org compatibility is required, stick to Rating, Multiple Choice, and NPS question types.

---

## Gotcha 7: Survey Metadata Is Not Easily Deployable Across Orgs

**What happens:** Surveys are stored as unstructured metadata that does not deploy cleanly through standard change sets or Metadata API. Survey content (questions, pages, branching) is stored in SurveyVersion records as data, not metadata. Moving a survey from sandbox to production often requires recreating it manually.

**When it occurs:** When following standard ALM practices and expecting surveys to move through the deployment pipeline like other configuration.

**How to avoid:** Treat surveys as org-specific configuration rather than deployable metadata. Document the survey design thoroughly (question types, page layout, branching logic) so it can be recreated manually in each target org. Alternatively, use the Survey REST API to script the creation process.
