# Gotchas — Salesforce Surveys

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

Line citations are to the Summer '26 / v62 PDF text extracts:
`object_reference.txt` ([PDF](https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf)),
`api_meta.txt` ([PDF](https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf)),
`apexrefguide.txt`, `api_rest.txt`.

## Gotcha 1: Base Tier 300-Response Lifetime Cap Is Absolute

**What happens:** The Base Salesforce Surveys tier includes exactly 300 survey responses across all surveys in the org -- lifetime, not per month or per year. Once this cap is reached, all surveys stop accepting responses with no advance warning. There is no email notification, no dashboard alert, and no grace period.

**When it occurs:** Orgs that start with surveys for a pilot project can silently exhaust the cap before the real rollout begins. Testing in production also consumes responses against the cap.

**How to avoid:** Check the current response count before designing any new survey (`SELECT COUNT() FROM SurveyResponse`). If the org expects more than a few hundred responses total, budget for Feedback Management Starter (100K) or Growth (unlimited) before investing in survey design.

UNVERIFIED (2026-09-05): the 300 / 100,000 / unlimited response figures are not stated in any of the
grounding documents available here — `grep -n -i "survey" salesforce_app_limits_cheatsheet.txt`
returns **zero hits**, and neither `api_meta.txt` nor `object_reference.txt` quotes a response cap.
What the docs *do* confirm is that tiers are real and gate features: `SurveyResponse.DataMapperExecutionStatus`
is "available in API v49.0 and later, with Feedback Management - Starter and Feedback Management - Growth
licenses" (`object_reference.txt` L275527–275540), `SurveyQuestion.RelatedQuestionId` and
`SubQuestionDisplayOrder` carry the same restriction (L274991–275016), and the
`sfdc_surveys.SurveyInvitationLinkShortener` interface requires "the Salesforce Feedback Management
license enabled" (`apexrefguide.txt` L196164–196165). Confirm the numeric cap against the org's
Company Information page or the current Feedback Management datasheet before quoting it to a customer.

---

## Gotcha 2: Guest User Profile Permissions Are Not Inherited from the Survey

**What happens:** Creating and activating a survey does not automatically grant guest users the ability to respond. The Experience Cloud site's Guest User Profile must explicitly have Read and Create permissions on Survey, SurveyInvitation, SurveyResponse, and SurveyQuestionResponse objects. Without these, external respondents see a blank page or a generic "insufficient privileges" error.

**When it occurs:** Every time an admin creates their first external-facing survey. Internal testing while logged in as an admin will never surface this issue because the admin has full access.

**How to avoid:** Immediately after creating an external survey, test it in an incognito browser with no Salesforce session. If the survey does not render or submit, check the Guest User Profile's object and field-level permissions.

Note on shape: `Survey`, `SurveyResponse` and `SurveyQuestionResponse` have **no `create()` call**
(`object_reference.txt` L274221–274223, L275502–275503, L275136–275137), so Create on those three is
what Setup grants rather than what the API honours; only `SurveyInvitation` genuinely accepts an
insert (L274588–274590). Grant Read on `Survey` and leave `viewAllRecords`/`modifyAllRecords` off.
UNVERIFIED (2026-09-05): the exact required guest-profile permission set is not enumerated in the
grounding docs; this gotcha preserves the skill's existing four-object guidance and the incognito
test is the authority.

---

## Gotcha 3: Branching Is Page-Level, and a BASIC Survey Has No Branching At All

**What happens:** Admins who are used to tools like Google Forms or SurveyMonkey expect to branch based on individual question answers. Salesforce Surveys route between *pages*. Worse, whether the survey can branch at all is fixed at creation by `Survey.SurveyType`, which is nillable, read-only and cannot be changed afterwards.

**When it occurs:** When designing surveys with complex conditional logic, and when someone picked the wrong survey type in the Survey Builder's first dialog months earlier.

**How to avoid:** Query the type before designing anything: `SELECT DeveloperName, SurveyType FROM Survey`. Valid values are `SURVEY` — "Survey with all the available features" — `BASIC` — "a question page with like or dislike, long text, multiple selection, NPS, rating, short text, and single selection questions, and **without** inserted participant responses, display logic, and page branching logic" — and `ASSESSMENT`, a "survey type for sales enablement teams" available from API 58.0 (`object_reference.txt` L274354–274359). A `BASIC` survey that needs branching must be rebuilt, not edited. For a `SURVEY`-type survey, place every routing-driving question on its own page and treat each page as a decision node.

---

## Gotcha 4: The SurveyVersion Status Field Is `SurveyStatus`, Not `Status`

**What happens:** A survey can be saved and appear in the survey builder without being activated. Sending invitations for an inactive SurveyVersion results in broken links or empty pages. The invitation URL technically resolves, but the survey form does not render. The check that would catch this fails first, because the field most people query does not exist.

**When it occurs:** When admins create a survey draft, share the link for stakeholder review, and then forget to activate it before sending to actual respondents — and when the guard Flow or Apex silently returns zero rows.

**How to avoid:** The field is `SurveyVersion.SurveyStatus`, a restricted picklist with values `Active`, `Draft`, `Obsolete`, `InvalidDraft` (`object_reference.txt` L276123–276136). `SurveyVersion.Status` is not a field and a SOQL filter on it throws `No such column`. Prefer the parent-side check — `Survey.ActiveVersionID` is null whenever no version is live (L274231–274235), and note the spelling: `ActiveVersionID` with a capital `D`, while its sibling is `LatestVersionId` (L274284). `InvalidDraft` is the state to look for when Survey Builder saved but activation is refused.

---

## Gotcha 5: NPS Score Bucketing Is Fixed and Cannot Be Customized

**What happens:** The NPS question type automatically categorizes responses into Detractor (0-6), Passive (7-8), and Promoter (9-10). These ranges are hardcoded by Salesforce and cannot be adjusted. Some organizations use different NPS scales or want to count 6 as Passive; this is not possible with the native NPS question type.

**When it occurs:** When stakeholders expect custom NPS bucketing logic or when comparing Salesforce NPS data with data from external tools that use different thresholds.

**How to avoid:** If custom NPS ranges are required, use a Slider or Rating question instead of the NPS question type, and calculate the bucketing in reports or Apex. Accept that the built-in NPS question type follows the standard Bain/Satmetrix NPS methodology with no room for customization.

UNVERIFIED (2026-09-05): the 0-6 / 7-8 / 9-10 bucket boundaries do not appear in `object_reference.txt`,
`api_meta.txt` or `apexrefguide.txt` — grepping for "Detractor" across the Object Reference returns
only an unrelated buyer-relationship-map picklist (L71486). What *is* grounded is that the buckets are
not stored as a field: `SurveyQuestionScore` holds `ScoreType` (`Individual` / `Overall`),
`CumulativeScore`, `ResponseCount`, `ResponseValue`, `QuestionSkippedCount` and `Score` — where for an
Overall record `Score` is "Score of an NPS type question" (`object_reference.txt` L275297–275494).
There is no Detractor/Passive/Promoter column anywhere on the object. Any report that shows the three
buckets is computing them, whoever wrote it.

---

## Gotcha 6: Matrix Questions Need API v55.0, and the Metadata Enum Spells Choice Types Differently

**What happens:** The Matrix question type is not available in every org, and the two places the platform names question types do not agree, so a value copied from one fails in the other.

**When it occurs:** When building surveys in a sandbox on a newer release and deploying to a production org that has not yet received the update; and when an agent copies a question-type value out of the Metadata API guide into a SOQL filter, or vice versa.

**How to avoid:** `SurveyQuestion.QuestionType` is a restricted picklist with 19 values — `Boolean` (v49.0+), `CSAT`, `Currency`, `Date`, `DateTime`, `FreeText`, `Image`, `Matrix` (**v55.0+**, not Spring '23), `MultipleChoice`, `MultiSelectPicklist`, `NPS`, `Number`, `Picklist`, `RadioButton`, `StackRank`, `Rating`, `ShortText` (v49.0+), `Slider`, `Toggle` (`object_reference.txt` L274965–274989). The Metadata API's `SurveyQuestionType` enum, used by `BusinessProcessGroup.customerSatisfactionMetric`, covers the same ground but spells the multiple-choice value **`MultiChoice`** and omits `RadioButton` (`api_meta.txt` L31309–31338). Use the picklist spelling in SOQL and reports, the enum spelling in `.businessProcessGroup` XML, and confirm the target org's API version before committing to `Matrix`.

---

## Gotcha 7: A Survey Is a Flow, So Flow Deployment Rules Govern It

**What happens:** Teams assume surveys are unmovable org-specific configuration and recreate them by hand in every environment. They are wrong about the mechanism but often right about the pain, because the real constraint is the Flow deployment rules, not the absence of metadata.

**When it occurs:** When following standard ALM practices, and when a survey deploys "successfully" into production but arrives inactive and every scheduled invitation points at nothing.

**How to avoid:** Treat the survey as the Flow it is. `Flow.processType` includes `Survey` — "A flow for Salesforce Surveys. From the UI, this type of flow is created in Survey Builder", API 42.0 and later (`api_meta.txt` L68322–68324) — and `SurveyEnrich` for the Survey Data Mapper, API 49.0+ and Customer Lifecycle Designer only (L68325–68329). The REST translation resources confirm it from the other direction: "The translated values of surveys fields are stored in Flow fields" (`api_rest.txt` L20037–20038). So retrieve and deploy it as `Flow`, and expect these Flow limits (`api_meta.txt` L68033–68042): a flow from a managed package is inaccessible via Metadata API unless it is a template; **deploying changes to an active flow into production requires the "Deploy processes and flows as active" org preference**; and spaces in a flow file name cause deploy errors. Response records never travel with the deployment — they are data, and the survey IDs differ per org, so any report filtering on a hardcoded `SurveyId` breaks after the first promotion.

---

## Gotcha 8: Only `ParticipantId` Is Writable — `ContactId`, `LeadId` and `UserId` Are Derived

**What happens:** A Flow's Create Records element or a Data Loader CSV that sets `SurveyInvitation.ContactId` fails with a field-not-writeable error, or the column is silently dropped. Admins then conclude "surveys can't be linked to a contact".

**When it occurs:** Every time someone builds the post-case-close automation by browsing the field list in Flow Builder instead of the createable-field list.

**How to avoid:** On `SurveyInvitation`, `ContactId`, `LeadId` and `UserId` all carry only `Filter, Group, Nillable, Sort` — no `Create`, no `Update` (`object_reference.txt` L274609, L274673, L274791). The single writable participant field is `ParticipantId`: "ID of the participant if the participant is a Salesforce contact, user, or lead", with `Create` but **not** `Update` (L274729–274742). Salesforce populates the typed lookup from it. Because it cannot be updated, an invitation pointed at the wrong person must be deleted and re-inserted. `InvitationLink` is likewise generated, not supplied — `Group, Nillable` with no `Create` — and "To query on this field, you need access to the associated Survey record" (L274624–274631), which is why a guest or low-privilege user's query of the link comes back empty rather than erroring.

---

## Gotcha 9: `SurveySubject` Is the Only Association Mechanism, and Its Parent Is the Invitation

**What happens:** Someone tries to relate a survey to a Case by setting a lookup on the Case, or by setting `SurveySubject.SurveyId` directly. Neither works, and the responses arrive with no business context — the exact failure the whole invitation pattern exists to prevent.

**When it occurs:** When an agent infers the join direction from the field names rather than the createable flags.

**How to avoid:** Create a `SurveySubject` with `ParentId` = the `SurveyInvitation` **or** `SurveyResponse` Id (its "Refers To" is exactly those two objects, `object_reference.txt` L275898–275917) and `SubjectId` = the business record. `SurveyId` and `SubjectEntityType` are **not** createable (L275987–275995, L275923–275926) — Salesforce derives both, so writing them fails. `SubjectEntityType` is a restricted picklist that already includes `Case`, `Account`, `Opportunity`, `Order`, `WorkOrder`, `VoiceCall`, `MessagingSession`, `LiveChatTranscript`, `User` and "Custom Objects" (L275926–275986). The Apex Reference Guide ships the canonical implementation under "Example Implementation to Associate SurveySubjects with SurveyInvitation and SurveyResponses" (`apexrefguide.txt` L196213–196296), including an `after insert` trigger on `SurveyResponse` for the anonymous case where only the response can carry the link.

---

## Gotcha 10: Anonymous or Response-Sharing Invitations Silently Disable Resume

**What happens:** A long survey is configured to collect anonymous responses. Participants who close the tab halfway through cannot resume — they start over and mostly do not. Completion rate collapses and nobody connects it to the anonymity checkbox.

**When it occurs:** When `OptionsCollectAnonymousResponse` or `OptionsAllowParticipantAccessTheirResponse` is set `true` on the invitation, which the "make it anonymous so people are honest" instinct does routinely.

**How to avoid:** The Object Reference states the interaction twice, once per object: "Paused isn't available for invitations in which either `OptionsAllowParticipantAccessTheirResponse` or `OptionsCollectAnonymousResponse` is true" (`object_reference.txt` L274762–274766 on `SurveyInvitation.ResponseStatus`, L275811–275816 on `SurveyResponse.Status`). Both fields are createable on the invitation (L274688–274728), so the choice is made at send time and cannot be revised for invitations already out. If resume matters, keep both `false` and get anonymity by restricting who can see the response records instead. Note the separate `Survey.IsPartialSaveEnabled` flag — createable, default `false` (L274261–274270) — which must also be on for partial responses to be retained at all. `PartiallyCompleted` as a status value requires API 63.0 or later.

---

## Gotcha 11: There Is No Single "Answer" Column — the Value Lands in One of Seven Fields

**What happens:** A report or an extract built on `SurveyQuestionResponse` shows blanks for most rows. The NPS scores are there but the free text is empty, or the other way round, and the numbers do not reconcile with what participants typed.

**When it occurs:** As soon as a survey mixes question types, which every real survey does.

**How to avoid:** `SurveyQuestionResponse` splits the answer by data type, and `Datatype` (`Boolean` v49.0+, `Date`, `Double`, `Int`, `Number`, `String`) tells you which column to read (`object_reference.txt` L275132–275296). `ChoiceValue` holds multiple choice, picklist, radio and ranking answers; `NumberValue` holds NPS, Rating, Score and Slider; `DateValue` and `DateTimeValue` hold their respective types; `IsTrueOrFalse` holds two-value questions; `Rank` holds the position for a ranking item. `QuestionChoiceId` points at the selected `SurveyQuestionChoice`. Build the report with one formula column per source field, or a `CASE` on `Datatype`, and join through `QuestionId` — never assume a uniform value column. The object is read-only (`getDeleted(), getUpdated(), query(), retrieve()` only, L275136–275137), so there is no repairing the data afterwards.

---

## Gotcha 12: `ConnectApi.Surveys.sendSurveyInvitationEmail` Caps at 300 Recipients and Only Takes Lightning Templates

**What happens:** A bulk send to a 5,000-contact list throws on the first call, or the send succeeds and nobody receives a link because the Classic email template that was configured was never eligible.

**When it occurs:** On the first campaign-scale send, and whenever an org still standardises on Classic email templates.

**How to avoid:** The method signature is `ConnectApi.Surveys.sendSurveyInvitationEmail(String surveyID, ConnectApi.SurveyInvitationEmailInput input)`, API 50.0, and it will "Email survey invitations to up to 300 participants … either leads, contacts, or users in your org" (`apexrefguide.txt` L105298–105326). `recipients` is documented as "List of up to 300 IDs" and is required, alongside `fromEmailAddress`, `isPersonalInvitation`, `allowGuestUserResponse`, `allowParticipantsAccessTheirResponse` and `collectAnonymousResponse` (L118632–118710) — omit any one and the call fails at run time, not at compile time. `emailTemplateId` accepts Lightning templates only: "Only Lightning email templates are used to send survey invitations" (L118662–118668). The merge token uses double square brackets, `[[SURVEY_INVITATION_URL]]`, while embedded questions use triple braces, `{{{SurveyQuestion.QuestionName}}}` (L118648–118654). `surveyQuestionIds` embeds NPS, rating and score questions only. Finally, the return `status` is `Queued` or `Failed` (L142112–142120) — `Queued` means accepted for sending, not delivered.

---

## Gotcha 13: An Active Survey With Paused Responses Cannot Be Deleted or Cleanly Replaced

**What happens:** A version cleanup or a package uninstall fails on a survey, with an error about the flow version, long after anyone remembers sending it.

**When it occurs:** When `Survey.IsPartialSaveEnabled` is on and participants have half-finished responses sitting in the org.

**How to avoid:** Because the survey is a Flow, "You can delete a flow version if it isn't active and doesn't have any paused interviews. If the flow version has paused interviews, wait for those interviews to resume and finish, or delete them" (`api_meta.txt` L68040–68042). Survey responses *are* flow interviews — `SurveyResponse.InterviewId` is "The ID of the FlowInterview object that's associated with this response" (`object_reference.txt` L275548–275558). So find the blockers with `SELECT Id, Status, InterviewId FROM SurveyResponse WHERE SurveyVersionId = '...' AND Status IN ('Paused','Started','PartiallyCompleted')`, then deactivate the version, let the paused interviews expire or delete them, and only then remove it. Setting `InviteExpiryDateTime` on every invitation bounds how long this tail can last (`object_reference.txt` L274632–274640).

---

## Gotcha 14: Embedding a Survey Off-Platform Needs Two Separate Allowances

**What happens:** The survey link works when pasted into a browser but renders as an empty frame inside the company's own website or inside a Chat/Messaging deployment. There is no console error a non-developer would recognise.

**When it occurs:** When marketing embeds the survey in a landing page, or when Service tries to surface a post-chat survey through an Embedded Service deployment.

**How to avoid:** Two independent settings, neither of which the Survey Builder mentions. (1) For an `<iframe>` on your own domain, add an `IframeWhiteListUrlSettings` entry with `<context>Surveys</context>` and the domain — accepted formats are `example.com`, `*example.com`, `https://example.com` (`api_meta.txt` L118497–118521). Note the guide's own printed sample carries a stray `>` in `<context>Surveys></context>` (L118528); copying it produces malformed XML. (2) For an Embedded Service deployment, the survey flow type is `LA_Survey` on `EmbeddedServiceFlowConfig.flowType`, and `isAuthenticationRequired` "can't be `true` for the `FS_Flow` value and **must be `true` for all other values**" (`api_meta.txt` L57226–57240) — so an embedded-service survey requires an authenticated visitor, which rules it out as a purely anonymous public survey channel.

---

## Gotcha 15: `exportSurveyResponses` Looks Like an Export API and Is Not One

**What happens:** An agent finds `exportSurveyResponses` in the Flow action enum, builds a nightly export around it, and the Flow will not save or the action never appears in the picker.

**When it occurs:** Whenever the response-extract requirement is solved by grepping the metadata guide's action list.

**How to avoid:** `exportSurveyResponses` is listed under "These values are reserved for future use" alongside `metricRefresh` and `thanks` (`api_meta.txt` L69583–69586, repeated at L101301–101303). The usable survey action values in the same enum are `sendSurveyInvitation` (API 47.0+, `api_meta.txt` L68886–68888), `dynamicSendSurveyInvitation` (API 51.0+, L68719–68720) and `performSurveySentimentAnalysis` (API 55.0+, L68891–68893). For extraction, query the objects directly or use Bulk API 2.0 against `SurveyResponse` and `SurveyQuestionResponse` — both are queryable, neither is createable.
