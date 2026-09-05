# Examples — Salesforce Surveys

## Example 1: Post-Case Closure CSAT Survey with Flow-Driven Invitations

**Context:** A support org wants to send a Customer Satisfaction survey to the case contact every time a case is closed. Responses must be reportable alongside the originating case.

**Problem:** Without a structured invitation, surveys are sent as anonymous links. Responses cannot be tied back to the case, making it impossible to identify which cases led to poor satisfaction scores.

**Solution:**

```text
Survey Design:
  Page 1: NPS question — "How likely are you to recommend our support?"
  Page 2 (branch: Detractor 0-6): Free text — "What could we improve?"
  Page 2 (branch: Promoter 9-10): Free text — "What did we do well?"
  Page 3: Thank You page (all branches converge)

Flow (Record-Triggered on Case, After Save, Status = Closed):
  1. Get Records: Retrieve Contact email from Case.ContactId
  2. Create Records: Create SurveyInvitation
     - Name          = 'CSAT ' + {!$Record.CaseNumber}   (required)
     - SurveyId      = [your survey's ID]                (required)
     - ParticipantId = {!$Record.ContactId}              (the ONLY writable participant field)
     - CommunityId   = [Experience Cloud site ID]
     - OptionsAllowGuestUserResponse = true
     - InviteExpiryDateTime = {!$Flow.CurrentDateTime} + 30 days
     NOTE: do NOT set ContactId / LeadId / UserId / InvitationLink / ResponseStatus.
           They are derived or generated and the element will fail.
  3. Create Records: Create SurveySubject   <-- this is what ties the response to the Case
     - Name      = 'CSAT subject ' + {!$Record.CaseNumber}
     - ParentId  = {!Create_Invite.Id}      (the SurveyInvitation, not the Case)
     - SubjectId = {!$Record.Id}            (the Case)
     NOTE: do NOT set SurveyId or SubjectEntityType. Salesforce derives both.
  4. Send Email Action: Email the invitation URL to the contact
     - Read SurveyInvitation.InvitationLink back after insert; it is generated, not supplied.

Simpler alternative: skip steps 2-4 and call the platform action `sendSurveyInvitation`
(Flow actionType, API 47.0+), documented for exactly this trigger. You lose the
SurveySubject join unless you add step 3 yourself.
```

**Why it works:** The SurveyInvitation record creates a trackable link that associates the response with the Contact, and the SurveySubject record carries the association back to the Case. Reports then join SurveyResponse to SurveyInvitation to SurveySubject to show CSAT by agent, product, or case category. Without the SurveySubject step the invitation knows who answered but nothing knows why they were asked.

---

## Example 2: Internal Employee Pulse Survey Embedded in a Lightning App

**Context:** HR wants to run a quarterly employee pulse survey. All employees have Salesforce logins and regularly use the platform.

**Problem:** Emailing a survey link to employees results in low response rates because the email is buried among other notifications.

**Solution:**

```text
Survey Design:
  Page 1: Rating question — "How satisfied are you with your work environment?" (1-5 stars)
  Page 2: Multiple Choice — "Which area needs the most improvement?"
          Options: Communication, Tools, Work-Life Balance, Career Growth
  Page 3: Free text — "Any additional comments?"

Distribution:
  1. Create the survey and activate it (publish the SurveyVersion).
  2. In Lightning App Builder, add the Survey component to the Home page.
  3. Set the Survey component properties to point to the active survey.
  4. Assign the updated Home page to the "Employee" app via App Manager.

Reporting:
  - SurveyResponse.SubmitterId is the lookup to the respondent
    (Refers To: Contact, Lead, User). There is no `ResponderId` field.
  - Completion timestamp is SurveyResponse.CompletionDateTime, not CompletedDate.
  - No guest user configuration needed; internal users authenticate normally.
```

**Why it works:** Embedding the survey in the Lightning Home page puts it directly in front of employees during their daily workflow. Response rates increase dramatically compared to email distribution. Because respondents are authenticated, each response automatically links to the user record without any custom association logic.

---

## Anti-Pattern: Sending Raw Survey Links Without SurveyInvitation Records

**What practitioners do:** Copy the survey's generic share URL and paste it into emails, Chatter posts, or external communications without creating SurveyInvitation records.

**What goes wrong:** Responses arrive as anonymous submissions. There is no way to trace which contact, account, or case generated the response. NPS scores exist in aggregate but cannot be segmented by customer, region, or product. If the org hits the response cap, there is no way to identify which survey or campaign consumed the quota.

**Correct approach:** Always generate SurveyInvitation records programmatically (via Flow or Apex) for each intended recipient. Set the ParticipantId to the Contact or User record, and add a SurveySubject so the response knows which business record produced it. Use the invitation-specific URL rather than the generic survey URL.

**How to detect it in an org you inherited.** Two queries. The first counts responses that arrived with no invitation behind them; the second counts invitations with no business record attached. Non-zero in either column is unrecoverable history — you can fix the automation, but those responses stay orphaned.

```sql
-- 1. Responses with no invitation: raw-link submissions
SELECT COUNT(Id) orphanedResponses
FROM SurveyResponse
WHERE InvitationId = NULL

-- 2. Invitations that were never joined to a record
SELECT SurveyId, COUNT(Id) invitations
FROM SurveyInvitation
WHERE Id NOT IN (SELECT SurveyInvitationId FROM SurveySubject WHERE SurveyInvitationId != NULL)
GROUP BY SurveyId

-- 3. What the healthy shape looks like: every invitation has a subject of the right type
SELECT SubjectEntityType, COUNT(Id) joined
FROM SurveySubject
WHERE SurveyId = '0KdRM0000004CVn0AM'
GROUP BY SubjectEntityType
```

Run (1) before promising anyone a "CSAT by product" dashboard. If it returns a large number, the dashboard cannot be built from history — only from responses collected after the automation is fixed.
