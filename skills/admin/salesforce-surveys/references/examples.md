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
     - SurveyId = [your survey's ID]
     - ParticipantId = Case.ContactId
     - InvitationType = "Link"
     - CommunityId = [Experience Cloud site ID]
  3. Send Email Action: Email the invitation URL to the contact
     - Use SurveyInvitation.InvitationLink as the merge field
```

**Why it works:** The SurveyInvitation record creates a trackable link that associates the response with the Contact and, through the Flow context, back to the Case. Reports can then join SurveyResponse to SurveyInvitation to Case to show CSAT by agent, product, or case category.

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
  - SurveyResponse.ResponderId links directly to the User record.
  - No guest user configuration needed; internal users authenticate normally.
```

**Why it works:** Embedding the survey in the Lightning Home page puts it directly in front of employees during their daily workflow. Response rates increase dramatically compared to email distribution. Because respondents are authenticated, each response automatically links to the user record without any custom association logic.

---

## Anti-Pattern: Sending Raw Survey Links Without SurveyInvitation Records

**What practitioners do:** Copy the survey's generic share URL and paste it into emails, Chatter posts, or external communications without creating SurveyInvitation records.

**What goes wrong:** Responses arrive as anonymous submissions. There is no way to trace which contact, account, or case generated the response. NPS scores exist in aggregate but cannot be segmented by customer, region, or product. If the org hits the response cap, there is no way to identify which survey or campaign consumed the quota.

**Correct approach:** Always generate SurveyInvitation records programmatically (via Flow or Apex) for each intended recipient. Set the ParticipantId to the Contact or User record. Use the invitation-specific URL rather than the generic survey URL. This preserves the complete audit trail from response back to the originating business context.
