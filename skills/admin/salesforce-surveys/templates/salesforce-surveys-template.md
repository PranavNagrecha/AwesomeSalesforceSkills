# Salesforce Surveys — Work Template

Use this template when working on tasks in this area.

## Scope

**Skill:** `salesforce-surveys`

**Request summary:** (fill in what the user asked for)

## The Seven Questions

Copy the answers here before opening Survey Builder. See `SKILL.md` § Questions to Ask Before
Configuring for why each one changes the design.

| Question | Answer |
|---|---|
| Which record must every response be traceable to? (Case / Account / Order / nothing) | |
| Do respondents have Salesforce logins, or are they anonymous public? | |
| Does anyone need the responses to be anonymous? (costs Paused/resume) | |
| How does the survey branch, and how many decisions per page? | |
| How many invitations per batch, and from which email address? | |
| Which orgs must this exist in, and who promotes it? | |
| Who owns the response data; can survey owners edit it? | |

## Context Gathered

- Feedback Management tier (Base / Starter / Growth):
- Current response count (`SELECT COUNT() FROM SurveyResponse`):
- `SurveySettings.enableSurvey` in the target org (true / false):
- `Survey.SurveyType` (SURVEY / BASIC / ASSESSMENT) — BASIC cannot branch:
- `Survey.ActiveVersionID` (null means nothing will render):
- Audience: internal (authenticated) / external (guest user):
- Experience Cloud site name and Id (becomes `SurveyInvitation.CommunityId`):
- Question types needed (from the 19-value `QuestionType` picklist):
- Branching required (yes/no) and page map:
- Resume required (yes/no) — if yes, both anonymity flags must stay false:

## Approach

Which pattern from SKILL.md applies?

- [ ] Post-Case Survey via Email Invitation
- [ ] Internal Employee Pulse Survey
- [ ] Bulk Send From Apex (`ConnectApi.Surveys.sendSurveyInvitationEmail`, 300 per call)
- [ ] Other (describe):

Distribution mechanism:

- [ ] Flow `sendSurveyInvitation` action (simplest; add SurveySubject separately)
- [ ] Hand-built `SurveyInvitation` + `SurveySubject` records
- [ ] `ConnectApi.Surveys.sendSurveyInvitationEmail`
- [ ] Embedded Lightning component (internal only)

## Design Artefact

Draft the survey as `surveys/<Name>.survey.json` so the checker can lint it. Shape:

```json
{
  "surveyType": "SURVEY",
  "collectAnonymousResponse": false,
  "allowGuestUserResponse": true,
  "allowParticipantsAccessTheirResponse": false,
  "isPartialSaveEnabled": true,
  "associateSubjectRecord": "Case",
  "pages": [
    {
      "name": "Page1_NPS",
      "questions": [
        {
          "name": "recommend",
          "type": "NPS",
          "required": true,
          "branches": [
            { "when": "<=6", "goToPage": "Page2_Detractor" },
            { "when": ">=9", "goToPage": "Page3_Promoter" }
          ]
        }
      ]
    },
    {
      "name": "Page2_Detractor",
      "questions": [{ "name": "improve", "type": "FreeText", "required": false }]
    },
    {
      "name": "Page3_Promoter",
      "questions": [{ "name": "praise", "type": "FreeText", "required": false }]
    }
  ]
}
```

Rules the checker enforces: one branching question per page, every `goToPage` resolves to a real
page and is not the page itself, every `type` is a `SurveyQuestion.QuestionType` value (not the
Metadata API's `MultiChoice` spelling), `BASIC` surveys carry no branches, and
`isPartialSaveEnabled` is incompatible with either anonymity flag.

## Checklist

- [ ] `SurveySettings.enableSurvey` is `true` in the deployed package and the target org
- [ ] Feedback Management tier confirmed and response cap is sufficient
- [ ] `SurveyType` supports the branching the design assumes
- [ ] Guest User Profile has the survey object permissions, no `viewAllRecords`/`modifyAllRecords`
- [ ] Field-level security on guest user profile covers all referenced fields
- [ ] Branching logic tested with each possible answer path
- [ ] `SurveySubject` created for every invitation that must be reportable against a record
- [ ] Invitation payload sets only createable fields; `ParticipantId` present (it cannot be updated)
- [ ] `InviteExpiryDateTime` set and in the future
- [ ] Survey tested from an unauthenticated browser session (for external)
- [ ] `python3 scripts/check_salesforce_surveys.py --manifest-dir <dir>` exits 0

## Verification Run

Paste the output of the two verification queries from `references/metadata-examples.md`:

```text
Response rate by version:

SurveySubject rows with SubjectEntityType = 'Case':
```

## Notes

Record any deviations from the standard pattern and why.
