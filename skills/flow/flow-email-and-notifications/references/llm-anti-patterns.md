# LLM Anti-Patterns — Flow Email and Notifications

Common mistakes AI coding assistants make when generating or advising on Flow email and notification configuration.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Suggesting Email Address as recipientId for Send Custom Notification

**What the LLM generates:** Instructions or pseudocode that retrieves a Contact's email address (e.g., `{!contact.Email}`) and assigns it to the `recipientIds` collection of the Send Custom Notification action.

**Why it happens:** LLMs conflate "notify a person" with "their email address" because email address is the most common identifier for notification in general software contexts. The distinction that Salesforce custom notifications require User record IDs (not emails) is a platform-specific constraint not well-represented in general training data.

**Correct pattern:**

```text
WRONG: recipientIds = {!contact.Email}   ← email address string
CORRECT: recipientIds = {!ownerUser.Id}  ← 15 or 18-char Salesforce User ID
```

Source the ID from a User record (Get Records on User object), not from an email field on any object.

**Detection hint:** Any reference to `recipientIds` assigned from a field named `Email`, `EmailAddress`, or similar is a red flag.

---

## Anti-Pattern 2: Referencing a Classic Email Template in the Send Email Core Action

**What the LLM generates:** Configuration steps that instruct the user to set a "Template" field on the Flow Send Email action, or to reference a template ID from Setup as an input parameter.

**Why it happens:** The Email Alert concept (which does reference Classic Templates) is closely associated with email-from-flow in training data. LLMs merge these two features into one model and assume a template picker exists in the Send Email action.

**Correct pattern:**

```text
WRONG: Send Email action → Template: "Case_Confirmation_Template"  (does not exist in this action)
CORRECT: Create a Text Template resource in Flow Builder
         → Send Email action → Body: {!myTextTemplate}
```

If Classic Template support is required, use an Email Alert invoked from Flow, not the Send Email core action.

**Detection hint:** Any instruction referencing a "template" parameter, template ID, or template name in the context of the Flow Send Email core action is incorrect.

---

## Anti-Pattern 3: Treating Send SMS as a Native Flow Action Without License Check

**What the LLM generates:** Steps that add a Send SMS action to the Flow without any mention of the Digital Engagement / Messaging add-on license requirement. Often presented as simply "drag the Send SMS action onto the canvas."

**Why it happens:** LLMs may have seen documentation about the Send SMS action and assume it is universally available, similar to Send Email. The license gate is an operational constraint not consistently signaled in documentation snippets.

**Correct pattern:**

```text
WRONG: "Add the Send SMS action to your Flow — configure the phone number and message."
CORRECT: "Verify that Digital Engagement (Messaging add-on) is provisioned in the org.
          If the license is not present, the Send SMS action will not appear in Flow Builder."
```

Always include a license prerequisite check before describing SMS configuration.

**Detection hint:** Any Send SMS instructions that do not mention Digital Engagement, Messaging license, or license verification are incomplete.

---

## Anti-Pattern 4: Omitting Fault Connectors on Notification Actions

**What the LLM generates:** Flow configurations for Send Email, Send Custom Notification, Send SMS, or Post Message to Slack with no mention of fault handling or fault connectors.

**Why it happens:** LLMs tend to generate the "happy path" for a requested feature and skip error handling unless specifically asked. Fault connectors are a Salesforce-specific construct that requires deliberate inclusion.

**Correct pattern:**

```text
Every notification action element should include:
- A fault connector leading to an error logging step or admin alert
- Capture of $Flow.FaultMessage in the fault path
- Either a Create Records (error log) or a fallback Send Email to an admin address
```

**Detection hint:** Any Flow configuration that includes notification actions but has no mention of fault connectors, `$Flow.FaultMessage`, or error handling is incomplete.

---

## Anti-Pattern 5: Assuming HTML Renders in Custom Notification Body

**What the LLM generates:** Custom notification body content that includes HTML tags such as `<b>`, `<br>`, or `<a href>` to add formatting or links to the notification message.

**Why it happens:** LLMs associate "notification body" with web notification APIs or email bodies where HTML is standard. Salesforce custom notifications display in the in-app bell panel and mobile push, which render plain text only.

**Correct pattern:**

```text
WRONG: body = "<b>Case Escalated:</b> {!$Record.CaseNumber}<br/>Click to review."
CORRECT: body = "Case Escalated: {!$Record.CaseNumber}. Open the notification to review."
```

Use plain text and Flow merge fields (`{!variableName}`) only. HTML tags will appear as literal characters in the notification panel.

**Detection hint:** Any notification body containing angle brackets (`<`, `>`) or HTML entities (`&amp;`, `&nbsp;`) is applying incorrect formatting assumptions.

---

## Anti-Pattern 6: Building Post Message to Slack Without Verifying Workspace Connection

**What the LLM generates:** Steps to add Post Message to Slack to a Flow and configure the channel and message, presented as complete without mentioning the Salesforce for Slack workspace connection requirement.

**Why it happens:** The action appears in Flow Builder after the managed package is installed, which is the only signal LLMs may have seen. The runtime authentication dependency on an active OAuth-connected workspace is a separate operational prerequisite not visible in Flow Builder UI descriptions.

**Correct pattern:**

```text
Before configuring Post Message to Slack in Flow:
1. Confirm Salesforce for Slack managed package is installed.
2. Verify Setup > Slack > Connected Slack Apps shows an active connected workspace.
3. Use the Slack Channel ID (e.g., C01234ABCDE) — not the channel name — to avoid failures if the channel is renamed.
4. Add a fault connector to handle OAuth expiry or revocation at runtime.
```

**Detection hint:** Any Slack action configuration that does not mention workspace connection verification or uses a channel display name instead of Channel ID is missing critical operational context.
