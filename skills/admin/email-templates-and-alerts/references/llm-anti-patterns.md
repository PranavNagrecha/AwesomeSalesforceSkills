# LLM Anti-Patterns — Email Templates and Alerts

Common mistakes AI coding assistants make when generating or advising on Salesforce email templates and email alerts.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Using Classic email templates instead of Lightning email templates

**What the LLM generates:** "Go to Setup → Communication Templates → Email Templates → New Template (Text/HTML/Visualforce)."

**Why it happens:** LLMs reference the Classic email template creation path. Lightning Email Templates (available under Setup → Email Templates or via the App Launcher → Email Templates) provide a drag-and-drop builder, enhanced merge field support, and folder-based sharing. Classic templates are legacy and do not support the Enhanced Letterhead feature.

**Correct pattern:**

```
For new email templates, use Lightning Email Templates:
1. App Launcher → Email Templates → New.
   Or: Setup → Email Templates (Lightning).
2. Use the drag-and-drop builder with Enhanced Letterhead.
3. Insert merge fields using the {{{Object.Field}}} Handlebars syntax
   (Lightning) rather than {!Object.Field} (Classic).

Classic templates still work but are legacy:
- Text, HTML, Visualforce templates remain functional.
- Use Classic only if an existing workflow rule or legacy
  process specifically requires a Classic template ID.
```

**Detection hint:** If the output navigates to "Communication Templates" in Setup or uses `{!Object.Field}` merge syntax, it is describing Classic templates. Search for `Communication Templates` or `{!` merge field syntax.

---

## Anti-Pattern 2: Using merge fields from unrelated objects without considering context

**What the LLM generates:** "In your Case email template, use `{{{Opportunity.Amount}}}` to show the deal amount."

**Why it happens:** LLMs pick merge fields from any object without verifying the merge context. Email templates resolve merge fields based on the object the template is associated with. A template sent from a Case cannot directly merge Opportunity fields unless there is a direct lookup relationship from Case to Opportunity.

**Correct pattern:**

```
Merge field context rules:
1. The template resolves fields from its associated object (the "Related Entity Type").
2. Cross-object merge fields work ONLY through direct relationship fields:
   - Case template can merge: {{{Case.Account.Name}}} (via AccountId lookup).
   - Case template CANNOT merge: {{{Opportunity.Amount}}} (no direct relationship).
3. For the recipient context, use {{{Recipient.Name}}}, {{{Recipient.Email}}}.
4. To include data from unrelated objects, use a formula field on the
   source object that pulls the value, then merge that formula field.
```

**Detection hint:** If the output uses merge fields from objects not directly related to the template's context object, those fields will render blank. Check if a lookup relationship exists between the template object and the merged object.

---

## Anti-Pattern 3: Ignoring Org-Wide Email Address requirements for sender identity

**What the LLM generates:** "The email alert will be sent from the running user's email address."

**Why it happens:** LLMs do not distinguish between email alerts and manual email sends. Email alerts (used in flows, workflow rules, and approval processes) use the "From" address configured in the email alert definition. If no Org-Wide Email Address is specified, the email is sent from the default "noreply" address or the org's default, not the running user.

**Correct pattern:**

```
Email alert sender identity:
1. Email alerts do NOT send from the running user's personal email.
2. Configure the sender:
   - Org-Wide Email Address: Setup → Organization-Wide Addresses → Add.
     Must be verified. Use for branded sender (support@company.com).
   - Default No-Reply: if no Org-Wide Email is configured, Salesforce
     uses the org default (often noreply@salesforce.com).
   - "Current User's Email Address" option: available in some alert configs,
     but the user's email must be verified as an Org-Wide Email Address.
3. For external-facing emails, always use a branded Org-Wide Email Address.
```

**Detection hint:** If the output says email alerts send from the "running user" or "current user" without configuring an Org-Wide Email Address, the sender identity is undefined. Search for `Org-Wide Email` or `From address` in the alert configuration.

---

## Anti-Pattern 4: Not accounting for email send limits

**What the LLM generates:** "Set up the flow to send an email alert every time a record is updated."

**Why it happens:** LLMs do not consider Salesforce email sending limits. Single email sends are limited to 5,000 per day per org (standard). Mass email has separate limits. An email alert that fires on every record update in a high-volume org can exhaust the daily limit, causing all subsequent email sends (including critical notifications) to fail silently.

**Correct pattern:**

```
Email send limits (standard):
- Single Email Messages: 5,000 per day per org.
  (Email alerts, Apex SingleEmailMessage, manual sends.)
- Mass Email: varies by edition (typically 1,000-5,000/day).
- Workflow email alerts: count toward the 1,000 per standard
  workflow action limit per hour (if using legacy workflow).

Guard against limit exhaustion:
1. Add criteria to the email alert: only send on meaningful changes,
   not every field update.
2. Batch similar notifications (daily digest instead of per-record).
3. Monitor usage: Setup → Email Log or Deliverability → Email Limits.
4. For high-volume notifications, use Platform Events or an external
   email service (SendGrid, Mailgun) instead of Salesforce email.
```

**Detection hint:** If the output creates an email alert on a high-frequency trigger without mentioning email limits, the org may hit the daily cap. Search for `email limit`, `5,000`, or `daily limit` in the output.

---

## Anti-Pattern 5: Hardcoding recipient email addresses in email alert definitions

**What the LLM generates:** "Add john.doe@company.com as an additional recipient in the email alert."

**Why it happens:** LLMs use specific email addresses for clarity. Hardcoded recipients become stale when people change roles, leave the company, or change email addresses. Email alerts should use dynamic recipients (record owner, related contact, queue members) or public groups.

**Correct pattern:**

```
Use dynamic recipients instead of hardcoded emails:
1. Object email fields: select "Email Field" recipients that resolve
   from the record (e.g., Contact.Email, Case.ContactEmail).
2. Related User: select the record owner, creator, or last modifier.
3. Public Groups: create a Public Group with the relevant users,
   and select it as a recipient. When team membership changes,
   update the group — not the email alert.
4. Roles and Subordinates: select a role to dynamically include
   all users in that role.
5. Hardcoded emails: use ONLY for external addresses that are truly
   static (e.g., a vendor inbox that will not change).
```

**Detection hint:** If the output adds specific email addresses (user@company.com) as alert recipients instead of dynamic fields or groups, the recipients will become stale. Regex: `\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b` in the alert recipient configuration.
