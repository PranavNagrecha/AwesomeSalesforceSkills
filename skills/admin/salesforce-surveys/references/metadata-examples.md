# Metadata Examples — Salesforce Surveys

Deployable shapes for the parts of Salesforce Surveys that **are** metadata, plus the record-level
artefacts for the parts that are not. Field names, enum values, and the skeletons come from the
Metadata API Developer Guide (v62/262 PDF), the Object Reference, and the Apex Reference Guide;
the worked examples extend the guides' own samples to a realistic post-case-closure survey.

Validate everything below with:

```bash
python3 skills/admin/salesforce-surveys/scripts/check_salesforce_surveys.py \
  --manifest-dir force-app/main/default
```

---

## What is metadata and what is not

| Artefact | Metadata type | package.xml `<name>` | File in a DX project |
|---|---|---|---|
| Org-level Surveys switch | `SurveySettings` | `Settings` (member `Survey`) | `settings/Survey.settings-meta.xml` |
| The survey definition itself (pages, questions, branching) | `Flow` with `processType` = `Survey` | `Flow` | `flows/<DeveloperName>.flow-meta.xml` |
| Survey Data Mapper flow | `Flow` with `processType` = `SurveyEnrich` | `Flow` | `flows/<DeveloperName>.flow-meta.xml` |
| Customer lifecycle map | `BusinessProcessGroup` | `BusinessProcessGroup` | `businessProcessGroups/<name>.businessProcessGroup-meta.xml` |
| Guest user object access | `Profile` / `PermissionSet` | `Profile` | `profiles/<Site> Profile.profile-meta.xml` |
| External domain allowed to iframe the survey | `IframeWhiteListUrlSettings` | `Settings` (member `IframeWhiteListUrl`) | `settings/IframeWhiteListUrl.settings-meta.xml` |
| `SurveyInvitation`, `SurveySubject`, `SurveyEngagementContext` | **not metadata — records** | n/a | CSV / Apex / Flow |
| `Survey`, `SurveyVersion`, `SurveyPage`, `SurveyQuestion`, `SurveyResponse`, `SurveyQuestionResponse` | **not metadata and not createable** | n/a | read-only, Survey Builder writes them |

**How to read it:**

- A Salesforce Survey is a **Flow**. `processType` = `Survey` is a documented Flow enum value,
  "A flow for Salesforce Surveys. From the UI, this type of flow is created in Survey Builder",
  available API 42.0+ (`api_meta.txt` L68322–68324). The REST translation resources say the same
  thing from the other side: "The translated values of surveys fields are stored in Flow fields"
  (`api_rest.txt` L20037–20038).
- Because a survey is a Flow, every Flow metadata limitation applies to it — including
  "To deploy changes in a production org, you must enable the **Deploy processes and flows as
  active** preference" and "You can delete a flow version if it isn't active and doesn't have any
  paused interviews" (`api_meta.txt` L68035–68040).
- The Survey/SurveyVersion/SurveyQuestion **objects are the read model**, not the write model.
  `Survey` supports only `describeLayout(), describeSObjects(), getDeleted(), getUpdated(),
  query(), retrieve(), search()` (`object_reference.txt` L274221–274223) — there is no `create()`.
  You cannot Data Loader a survey into an org.
- `SurveyInvitation`, `SurveySubject` and `SurveyEngagementContext` **do** support `create()`
  (`object_reference.txt` L274588–274590, L275870–275872, L274515–274517), which is why sending and associating is
  automatable and authoring is not.

---

## 1. SurveySettings — enable the feature

The guide's own sample definition (`api_meta.txt` L127650–127658), corrected: the shipped PDF text
renders the opening tag as `<SurveySettingsxmlns=...>` with the space eaten by the PDF extractor.
Deploy this shape.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<SurveySettings xmlns="http://soap.sforce.com/2006/04/metadata">
    <enableSurvey>true</enableSurvey>
    <enableSurveyOwnerCanManageResponse>true</enableSurveyOwnerCanManageResponse>
    <enableIndustriesCxmEnabled>false</enableIndustriesCxmEnabled>
    <enableGenerativeAISurveys>false</enableGenerativeAISurveys>
</SurveySettings>
```

**How to read it:**

- File name is fixed: `Survey.settings`, in the `settings` folder — "SurveySettings values are
  stored in a single file named Survey.settings in the settings folder"
  (`api_meta.txt` L127618–127620). `SurveySettings` is API 47.0+ (L127623).
- `enableSurvey` defaults to `false` (L127641–127642). Nothing else in this skill works until it
  is `true`.
- `enableSurveyOwnerCanManageResponse` defaults to `false` (L127644–127646). Leave it `false`
  unless survey owners are meant to edit or delete participant responses — flipping it to `true`
  widens who can touch response data.
- `enableIndustriesCxmEnabled` (Customer Lifecycle Maps) and `enableGenerativeAISurveys`
  (API 62.0+, L127634–127637) both default to `false`. `enableIndustriesCxmEnabled` gates the
  `BusinessProcessGroup` type, which "is available in orgs with Surveys enabled with the Customer
  Lifecycle Designer license" (L31301).
- Settings do **not** accept the `*` wildcard for an individual setting: "The wildcard character *
  … doesn't apply to metadata types for feature settings. The wildcard applies only when retrieving
  all settings, not for an individual setting" (L127680–127683).

---

## 2. package.xml

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Survey</members>
        <members>IframeWhiteListUrl</members>
        <name>Settings</name>
    </types>
    <types>
        <members>Post_Case_CSAT</members>
        <name>Flow</name>
    </types>
    <types>
        <members>Case_Closed_Send_CSAT</members>
        <name>Flow</name>
    </types>
    <types>
        <members>Customer Support Site Profile</members>
        <name>Profile</name>
    </types>
    <version>62.0</version>
</Package>
```

**How to read it:**

- `Settings` is the container name for every feature setting; the *member* is the setting's short
  name (`Survey`, not `SurveySettings`). The guide's own SurveySettings package.xml sample uses
  `<members>Survey</members>` / `<name>Settings</name>` (`api_meta.txt` L127665–127673).
- `Post_Case_CSAT` here is the survey (a `processType` = `Survey` Flow) and
  `Case_Closed_Send_CSAT` is the record-triggered Flow that sends it. Both are the `Flow` type;
  only the `processType` inside the file differs.
- Retrieving a survey Flow pulls its **currently retrievable versions**, not its response data.
  Responses are records and never move with a deployment.

---

## 3. IframeWhiteListUrlSettings — embedding a survey on your own website

```xml
<?xml version="1.0" encoding="UTF-8"?>
<IframeWhiteListUrlSettings xmlns="http://soap.sforce.com/2006/04/metadata">
    <iframeWhiteListUrl>
        <context>Surveys</context>
        <url>https://www.example.com</url>
    </iframeWhiteListUrl>
    <iframeWhiteListUrl>
        <context>Surveys</context>
        <url>*support.example.com</url>
    </iframeWhiteListUrl>
</IframeWhiteListUrlSettings>
```

**How to read it:**

- `context` valid values are `LightningOut` (reserved for future use, API 60.0+), `Surveys`,
  `VisualforcePages`, `DisclosureAndComplianceHubConnector` (`api_meta.txt` L118501–118506).
- `url` "Accepts these formats: example.com, *example.com, and https://example.com"
  (`api_meta.txt` L118517–118521).
- The guide's printed sample contains a typo — `<context>Surveys></context>` with a stray `>`
  (`api_meta.txt` L118528). Do not copy it; the deploy fails on the unmatched character.
- Without an entry here, an `<iframe>` of the survey link on your marketing site is blocked by the
  frame policy and the respondent sees an empty frame, not an error.

---

## 4. Guest user profile — the object permissions that make an external survey work

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Profile xmlns="http://soap.sforce.com/2006/04/metadata">
    <custom>false</custom>
    <objectPermissions>
        <object>Survey</object>
        <allowRead>true</allowRead>
        <allowCreate>false</allowCreate>
        <allowEdit>false</allowEdit>
        <allowDelete>false</allowDelete>
        <modifyAllRecords>false</modifyAllRecords>
        <viewAllRecords>false</viewAllRecords>
    </objectPermissions>
    <objectPermissions>
        <object>SurveyInvitation</object>
        <allowRead>true</allowRead>
        <allowCreate>true</allowCreate>
        <allowEdit>false</allowEdit>
        <allowDelete>false</allowDelete>
        <modifyAllRecords>false</modifyAllRecords>
        <viewAllRecords>false</viewAllRecords>
    </objectPermissions>
    <objectPermissions>
        <object>SurveyResponse</object>
        <allowRead>true</allowRead>
        <allowCreate>true</allowCreate>
        <allowEdit>false</allowEdit>
        <allowDelete>false</allowDelete>
        <modifyAllRecords>false</modifyAllRecords>
        <viewAllRecords>false</viewAllRecords>
    </objectPermissions>
    <objectPermissions>
        <object>SurveyQuestionResponse</object>
        <allowRead>true</allowRead>
        <allowCreate>true</allowCreate>
        <allowEdit>false</allowEdit>
        <allowDelete>false</allowDelete>
        <modifyAllRecords>false</modifyAllRecords>
        <viewAllRecords>false</viewAllRecords>
    </objectPermissions>
</Profile>
```

**How to read it:**

- `Survey` is **Read only** on purpose. The object has no `create()` call at all
  (`object_reference.txt` L274221–274223), so `allowCreate` on `Survey` grants nothing and only
  widens the audit surface.
- `SurveyResponse` and `SurveyQuestionResponse` likewise have no `create()` in the Object Reference
  (L275502–275503, L275136–275137). The platform writes them on the participant's behalf from inside the
  survey Flow interview. Granting Create is what Salesforce Setup does for the guest profile; it is
  not what makes the row appear.
  UNVERIFIED (2026-09-05): the exact guest-profile object permission set Salesforce requires for
  external survey submission is not stated in `api_meta.txt`, `object_reference.txt` or
  `apexrefguide.txt`; the list above preserves the skill's existing four-object guidance. Verify in
  the target org by submitting from an unauthenticated session before relying on it.
- Never add `viewAllRecords` or `modifyAllRecords` for a guest profile. See
  `admin/experience-cloud-guest-access` for the site-level guest hardening rules that sit around
  this file.

---

## 5. The invitation — a Data Loader CSV

Only these `SurveyInvitation` fields are createable (`object_reference.txt` L274594–274805):
`CommunityId`, `EmailBrandingId`, `InviteExpiryDateTime`, `IsDefault`, `Name`, `OwnerId`,
`ParticipantId`, `SurveyId`, `OptionsAllowGuestUserResponse`,
`OptionsAllowParticipantAccessTheirResponse`, `OptionsCollectAnonymousResponse`.

```csv
Name,SurveyId,ParticipantId,CommunityId,OptionsAllowGuestUserResponse,OptionsCollectAnonymousResponse,OptionsAllowParticipantAccessTheirResponse,InviteExpiryDateTime
CSAT Case 00001001,0KdRM0000004CVn0AM,0035g00000L1a1QAAR,0DBRM0000004n4yOAA,true,false,false,2026-10-05T23:59:59Z
CSAT Case 00001002,0KdRM0000004CVn0AM,0035g00000L1a2RAAR,0DBRM0000004n4yOAA,true,false,false,2026-10-05T23:59:59Z
CSAT Case 00001003,0KdRM0000004CVn0AM,0035g00000L1a3SAAR,0DBRM0000004n4yOAA,true,false,false,2026-10-05T23:59:59Z
```

**How to read it:**

- `ContactId`, `LeadId` and `UserId` are **not** in the CSV because they are not createable — they
  are `Filter, Group, Nillable, Sort` only (`object_reference.txt` L274609, L274673, L274791). Salesforce derives them from `ParticipantId`, which "is the ID of the
  participant if the participant is a Salesforce contact, user, or lead" (L274729–274742).
- `ParticipantId` has `Create` but **not** `Update` (L274729–274735). Point an invitation at the
  wrong contact and the only fix is delete and re-insert.
- `InvitationLink` is absent because it is generated, not supplied — properties are `Group,
  Nillable` with no `Create` (L274624–274631). Load first, then query the link back out.
- `ResponseStatus` is absent for the same reason: read-only picklist with values `NotStarted`,
  `Started`, `Paused`, `PartiallyCompleted` (API 63.0+), `Completed` (L274736–274783).
- `OptionsCollectAnonymousResponse` and `OptionsAllowParticipantAccessTheirResponse` are set to
  `false` here deliberately: when either is `true`, "Paused isn't available" as a response status
  (L274762–274766), so a partially-finished response cannot be resumed.

---

## 6. Associating the invitation with the Case — SurveySubject

`SurveySubject` is the join. The Apex Reference Guide ships this exact pattern under "Example
Implementation to Associate SurveySubjects with SurveyInvitation and SurveyResponses"
(`apexrefguide.txt` L196213–196296), reproduced here with the guide's field assignments and a bulk
-safe wrapper added.

```apex
public with sharing class CaseSurveyInvitationService {

    // Guide sample: apexrefguide.txt L196218-L196292
    public static void inviteForClosedCases(Map<Id, Case> casesById, Id surveyId, Id communityId) {
        List<SurveyInvitation> invitations = new List<SurveyInvitation>();
        List<Id> orderedCaseIds = new List<Id>();

        for (Case c : casesById.values()) {
            if (c.ContactId == null) {
                continue; // no participant -> no personal invitation
            }
            SurveyInvitation inv = new SurveyInvitation();
            inv.Name = 'CSAT ' + c.CaseNumber;
            inv.SurveyId = surveyId;
            inv.ParticipantId = c.ContactId;
            inv.CommunityId = communityId;
            inv.OptionsAllowGuestUserResponse = true;
            inv.InviteExpiryDateTime = System.now().addDays(30);
            invitations.add(inv);
            orderedCaseIds.add(c.Id);
        }
        if (invitations.isEmpty()) {
            return;
        }
        insert invitations;

        List<SurveySubject> subjects = new List<SurveySubject>();
        for (Integer i = 0; i < invitations.size(); i++) {
            SurveySubject subj = new SurveySubject();
            subj.Name = 'CSAT subject ' + orderedCaseIds[i];
            subj.ParentId  = invitations[i].Id;   // SurveyInvitation or SurveyResponse
            subj.SubjectId = orderedCaseIds[i];   // the Case
            subjects.add(subj);
        }
        insert subjects;
    }
}
```

**How to read it:**

- `SurveySubject.ParentId` "Refers To SurveyInvitation, SurveyResponse"
  (`object_reference.txt` L275898–275917) — it is the invitation or the response, never the Case.
  The Case goes in `SubjectId`.
- `SurveyId` and `SubjectEntityType` on `SurveySubject` are **not** createable (L275987–275995,
  L275923–275926); Salesforce derives both. Setting them in a Flow's Create Records element is a
  deploy-time or run-time field-not-writeable error.
- `SubjectEntityType` is a restricted picklist that already contains `Case`, `Account`,
  `Opportunity`, `Order`, `WorkOrder`, `VoiceCall`, `MessagingSession`, `LiveChatTranscript`,
  `User`, and "Custom Objects" (L275926–275986) — so a custom object is a valid survey subject.
- Because `SurveyResponse` fires change events and supports triggers, the guide's companion sample
  attaches a second `SurveySubject` to the *response* from an `after insert` trigger on
  `SurveyResponse` (`apexrefguide.txt` L196298–196308) — do that when the invitation is anonymous
  and only the response can carry the association.

---

## 7. The declarative alternative — `sendSurveyInvitation`

If the trigger is "Case closed", prefer the platform action over hand-built records. `Flow`'s
`actionType` enum includes `sendSurveyInvitation`: "Sends email survey invitations to leads,
contacts, and users in your org based on an action, such as when a customer support case closes.
This value is available in API version 47.0 and later" (`api_meta.txt` L68886–68888).

```xml
<actionCalls>
    <name>Send_CSAT_Invitation</name>
    <label>Send CSAT Invitation</label>
    <locationX>440</locationX>
    <locationY>280</locationY>
    <actionName>sendSurveyInvitation</actionName>
    <actionType>sendSurveyInvitation</actionType>
    <flowTransactionModel>CurrentTransaction</flowTransactionModel>
</actionCalls>
```

Related enum values, same table: `dynamicSendSurveyInvitation` (API 51.0+, `api_meta.txt`
L68719–68720) and `performSurveySentimentAnalysis` (API 55.0+, L68891–68893). `exportSurveyResponses`
appears in the same enum but is listed under "These values are reserved for future use"
(`api_meta.txt` L69583–69586) — do not build against it.

---

## 8. Bulk sending from Apex — `ConnectApi.Surveys`

```apex
ConnectApi.SurveyInvitationEmailInput input = new ConnectApi.SurveyInvitationEmailInput();
input.recipients = new List<String>{ '0035g00000L1a1QAAR', '0035g00000L1a2RAAR' }; // <= 300
input.fromEmailAddress = 'support@example.com';
input.isPersonalInvitation = true;
input.allowGuestUserResponse = true;
input.allowParticipantsAccessTheirResponse = false;
input.collectAnonymousResponse = false;
input.communityId = '0DBRM0000004n4yOAA';
input.subject = 'How did we do?';
input.body = 'Thanks for contacting support. <a href="[[SURVEY_INVITATION_URL]]">Tell us how we did</a>.';
input.invitationExpirationDate = System.now().addDays(30);

ConnectApi.SurveyInvitationEmailOutput out =
    ConnectApi.Surveys.sendSurveyInvitationEmail('0KdRM0000004CVn0AM', input);
System.debug(out.status);        // Queued or Failed
System.debug(out.errorMessage);  // populated only on Failed
```

**How to read it:**

- Hard cap of 300 recipients per call: "Email survey invitations to up to 300 participants. You can
  email either leads, contacts, or users in your org" (`apexrefguide.txt` L105299–105300), and
  `recipients` is "List of up to 300 IDs of leads, contacts, or users" (L118700–118703). Chunk
  larger sends.
- Required properties are `allowGuestUserResponse`, `allowParticipantsAccessTheirResponse`,
  `collectAnonymousResponse`, `fromEmailAddress`, `isPersonalInvitation`, `recipients`
  (`apexrefguide.txt` L118632–118705). Omitting any of them fails the call, not the deploy.
- The merge token is **double square brackets**: `[[SURVEY_INVITATION_URL]]` to embed the link, and
  `{{{SurveyQuestion.QuestionName}}}` / `{{{SurveyQuestion.QuestionHtmlContent}}}` to embed a
  question (L118648–118654).
- `emailTemplateId` accepts Lightning email templates only — "Only Lightning email templates are
  used to send survey invitations" (L118662–118668). A Classic template silently is not an option.
- `isPersonalInvitation = true` is what preserves traceability: "When a participant responds using
  a personal invitation, the response record is associated with the participant's Salesforce record"
  (L118682–118687).
- `surveyQuestionIds` only supports embedding NPS, rating and score questions in the email body
  (L118706–118710).
- The return is asynchronous-shaped: `status` is `Queued` or `Failed`
  (`apexrefguide.txt` L142112–142120). `Queued` is not proof of delivery.

---

## Retrieve and deploy

```bash
# Retrieve the org switch, the survey itself, and the sending flow
sf project retrieve start \
  --metadata "Settings:Survey" \
  --metadata "Flow:Post_Case_CSAT" \
  --metadata "Flow:Case_Closed_Send_CSAT" \
  --target-org myDevSandbox

# Retrieve the guest profile with the objects it needs (profiles retrieve sparse)
sf project retrieve start --manifest manifest/package.xml --target-org myDevSandbox

# Validate before you deploy — surveys are Flows, and an active Flow deploy is gated
sf project deploy start --manifest manifest/package.xml --dry-run --target-org myProd

sf project deploy start --manifest manifest/package.xml --target-org myProd
```

Deploying a survey into production only lands as an **active** survey if the org has the *Deploy
processes and flows as active* preference enabled — "You can deploy changes to an active flow if in
a non-production org, such as a scratch or sandbox org. To deploy changes in a production org, you
must enable the Deploy processes and flows as active preference" (`api_meta.txt` L68035–68039).
Without it the survey arrives inactive and every invitation you already scheduled points at nothing.

---

## Verification

### Is the feature on and is the survey active?

```sql
SELECT Id, Name, DeveloperName, SurveyType, IsPartialSaveEnabled,
       ActiveVersionID, LatestVersionId, TotalVersionsCount
FROM Survey
WHERE DeveloperName = 'Post_Case_CSAT'
```

`ActiveVersionID` null means no active version exists and invitations will not render. Note the
field is spelled `ActiveVersionID` — capital `D` — while its sibling is `LatestVersionId`
(`object_reference.txt` L274231, L274284). `SurveyType` returns `SURVEY`, `BASIC` or `ASSESSMENT`;
`BASIC` is "a survey with a question page … **without** inserted participant responses, display
logic, and page branching logic" (L274354–274359), so a `BASIC` survey cannot branch.

### Which version is live, and are older versions blocking cleanup?

```sql
SELECT Id, Name, VersionNumber, SurveyStatus, IsTemplate, BrandingSetId
FROM SurveyVersion
WHERE SurveyId = '0KdRM0000004CVn0AM'
ORDER BY VersionNumber DESC
```

The status field is `SurveyStatus`, **not** `Status`, with values `Active`, `Draft`, `Obsolete`,
`InvalidDraft` (`object_reference.txt` L276123–276136). `InvalidDraft` is the state to look for
when Survey Builder saved but the survey will not activate.

### Response rate by survey version

```sql
SELECT SurveyVersionId, Status, COUNT(Id) responses
FROM SurveyResponse
WHERE SurveyId = '0KdRM0000004CVn0AM'
GROUP BY SurveyVersionId, Status
ORDER BY SurveyVersionId
```

Divide the `Completed` count by the invitations issued for the same version:

```sql
SELECT ResponseStatus, COUNT(Id) invitations
FROM SurveyInvitation
WHERE SurveyId = '0KdRM0000004CVn0AM'
GROUP BY ResponseStatus
```

`SurveyResponse.Status` and `SurveyInvitation.ResponseStatus` are two different fields on two
different objects that share the same picklist values (`object_reference.txt` L275795–275820 and
L274736–274783). Reporting on the wrong one is the usual cause of a response rate that will not
reconcile.

### Did the Case association actually land?

```sql
SELECT Id, Name, ParentId, SubjectId, SubjectEntityType, SurveyId,
       SurveyInvitationId, SurveyResponseId
FROM SurveySubject
WHERE SubjectEntityType = 'Case'
  AND SurveyId = '0KdRM0000004CVn0AM'
ORDER BY CreatedDate DESC
LIMIT 50
```

Zero rows with non-zero invitations means the invitation was created but never joined to a Case —
the single most common reason survey data cannot be segmented afterwards.

### Setup check

Setup → **Survey Settings** should show Surveys enabled (matches `enableSurvey`), and
Setup → **Surveys** → the survey → the version badge should read **Active**. For an external
survey, open the invitation link in a private window with no Salesforce session; if the page
renders but submit does nothing, the guest profile is the suspect, not the survey.
