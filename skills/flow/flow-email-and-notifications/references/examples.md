# Examples — Flow Email and Notifications

## Example 1: Custom Bell Notification on Case Escalation

**Context:** A support team needs to alert a case owner's manager immediately when a case is marked Critical. The manager is a Salesforce user. Email is too slow and adds inbox noise; the requirement is an in-app alert that appears in the bell icon and as a mobile push.

**Problem:** Without guidance, a builder might try to pass the manager's email address into the Send Custom Notification `recipientIds` field, or skip creating the Custom Notification Type record first. Both cause runtime errors that are not clearly labeled.

**Solution:**

```text
Prerequisites:
1. Setup > Notification Builder > Custom Notifications > New
   Name: Case Escalation Alert
   API Name: Case_Escalation_Alert
   Supported Channels: Desktop, Mobile

Flow (Record-Triggered on Case, after save, entry: Status changed to Critical):
1. Get Records — Query User where Id = {!$Record.OwnerId}
   (to confirm owner record, retrieve ManagerId)

2. Get Records — Query User where Id = {!caseOwner.ManagerId}
   (retrieve manager User ID)

3. Create Variable: recipientCollection (Text Collection)
   Add: {!manager.Id}

4. Text Template resource: notificationBody
   Content: "Case {!$Record.CaseNumber} — {!$Record.Subject} has been escalated to Critical. Review now."

5. Action: Send Custom Notification
   Notification Type API Name: Case_Escalation_Alert
   Recipient IDs: {!recipientCollection}
   Title: "Case Escalation — Action Required"
   Body: {!notificationBody}
   Target ID: {!$Record.Id}   ← navigates to the Case on mobile tap

6. Fault Connector → Log Error Record (capture $Flow.FaultMessage)
```

**Why it works:** The `recipientIds` input receives a Text Collection of User IDs, which is what the platform requires. The `targetId` makes the mobile push tap-to-navigate work. The fault connector prevents silent failures when the 1,000/hour org limit is reached.

---

## Example 2: Confirmation Email to External Applicant

**Context:** A recruitment Flow runs when a Job Application record is created. An email must be sent to the applicant's email address (stored on the record) confirming receipt. The email body must include the applicant's name, the job title, and a reference number. The body content changes per record so a fixed Classic Email Template is not flexible enough.

**Problem:** Builders sometimes try to wire a Classic Email Template into the Flow Send Email action. The Send Email core action does not accept template IDs. Attempts to find a template-picker field in the action element's configuration will fail because the feature does not exist there.

**Solution:**

```text
Flow (Record-Triggered on Job_Application__c, after insert):

1. Get Records — Query Job__c where Id = {!$Record.Job__c}
   Store: jobTitle = {!job.Name}

2. Text Template resource: applicantEmailBody
   Content:
   "Dear {!$Record.Applicant_Name__c},

   Thank you for applying for {!jobTitle}.
   Your application reference is {!$Record.Name}.

   We will be in touch within 5 business days.

   Regards,
   The Recruitment Team"

3. Action: Send Email
   To: {!$Record.Applicant_Email__c}
   Subject: "Application Received — {!jobTitle}"
   Body: {!applicantEmailBody}
   (Sender: Org-Wide Email Address configured for recruiting)

4. Fault Connector → Create Error_Log__c record
   (Body: $Flow.FaultMessage, Record: $Record.Id)
```

**Why it works:** The Text Template resource allows fully dynamic merge fields while keeping the structure readable in Flow Builder. The fault connector captures delivery failures — which can occur when the email address is invalid or when the daily send limit is reached — without rolling back the record creation.

---

## Example 3: Slack Notification on High-Value Opportunity Stage Change

**Context:** A sales operations team wants a Slack message posted to the `#big-deals` channel whenever an Opportunity reaches Closed Won with an Amount over $100,000. The Salesforce for Slack integration is already installed and the workspace is connected.

**Problem:** Builders sometimes build this Flow before confirming the workspace connection in Setup. The Post Message to Slack action will appear in Flow Builder after installation, but it will fault at runtime with an authentication error if no workspace has been authenticated.

**Solution:**

```text
Prerequisites:
- Setup > Slack > Connected Slack Apps — confirm workspace is listed and active
- Obtain the Slack Channel ID for #big-deals from Slack channel settings

Flow (Record-Triggered on Opportunity, after save):
Entry Criteria: StageName = "Closed Won" AND Amount > 100000 AND ISCHANGED(StageName)

1. Text Template: slackMessage
   Content: ":trophy: New Closed Won Deal
   Opportunity: {!$Record.Name}
   Amount: {!$Record.Amount}
   Owner: {!$Record.Owner.Name}
   Close Date: {!$Record.CloseDate}"

2. Action: Post Message to Slack
   Channel: C01234ABCDE   ← Slack Channel ID for #big-deals
   Message: {!slackMessage}

3. Fault Connector → Send Email to ops-admin@company.com
   Subject: "Slack notification failed for {!$Record.Name}"
   Body: {!$Flow.FaultMessage}
```

**Why it works:** Using the Slack Channel ID rather than the channel name avoids errors if the channel is renamed. The fault connector uses Send Email so the operations admin still receives the notification even if Slack delivery fails.

---

## Anti-Pattern: Passing Email Address as recipientId for Custom Notification

**What practitioners do:** They retrieve a Contact's email address and pass it as the recipient for Send Custom Notification, reasoning that the notification should go to that person.

**What goes wrong:** The Send Custom Notification action requires Salesforce User IDs in the `recipientIds` collection. A Contact email address is neither a User ID nor accepted by the action. The action faults at runtime with a generic error. Contacts who are not also Salesforce Experience Cloud users cannot receive in-app custom notifications at all.

**Correct approach:** Use Send Email for communication with external contacts. Reserve Send Custom Notification for internal Salesforce users and Experience Cloud users (who have User records). Always pass the User `.Id` field, not an email address.
