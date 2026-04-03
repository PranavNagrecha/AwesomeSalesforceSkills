# Gotchas — Requirements Gathering for Salesforce

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Acceptance Criteria That Cannot Be Tested in a Sandbox

**What happens:** A user story is written with acceptance criteria like "the system should be fast" or "the page should look clean." These criteria cannot be evaluated in a sandbox, produce no clear pass/fail outcome, and get marked "done" in UAT by default because no one knows what "done" looks like.

**When it occurs:** When BAs write acceptance criteria from the stakeholder's language rather than from testable, observable Salesforce behaviors. Common in first drafts of stories when the BA has not yet mapped requirements to specific platform features.

**How to avoid:** Every acceptance criterion must describe an observable state in a Salesforce sandbox. Replace subjective criteria with specific, platform-verifiable statements:
- Replace "the form should be easy to use" with "all required fields are highlighted in red when the Save button is clicked without completing them"
- Replace "managers can see their team's data" with "users with Manager role can see all Opportunities where OwnerId belongs to their direct reports via Role Hierarchy"
- Replace "the integration should work" with "when a new Account is created with Type = Customer, a corresponding record appears in the external billing system within 5 minutes"

---

## Gotcha 2: Confusing Field-Level Security with Sharing

**What happens:** A stakeholder says "only Sales Managers should see the Discount Approved field." The BA writes a story for a sharing rule, but the requirement is actually a Field-Level Security (FLS) requirement. Sharing rules control record access (who sees which records); FLS controls field access (who sees which fields on records they can already see). These are configured in completely different places in Salesforce — sharing rules are in Sharing Settings; FLS is in Object Manager on the field, or on the profile/permission set.

**When it occurs:** When stakeholders describe visibility requirements without distinguishing "who can see this record" from "who can see this field on a record they can already access." Both are called "access" in plain language, but they map to different Salesforce mechanisms.

**How to avoid:** When capturing a visibility requirement, explicitly ask two questions:
1. "Who should be able to see the *record* at all?" → This is a sharing / OWD / role hierarchy question.
2. "Of those who can see the record, who should be able to see *this field*?" → This is an FLS / permission set question.
Document these as separate requirements. Mixing them in a single story leads to the wrong platform feature being configured.

---

## Gotcha 3: Automation Requirements That Assume Cross-Object DML Is Safe

**What happens:** A stakeholder says "when a Case is closed, automatically update the related Account's Last Case Closed Date field." The BA writes this as a single automation requirement. The admin builds it as a record-triggered Flow on Case, which then updates the parent Account. This creates a cross-object DML within the same transaction, which works — until it runs in the context of another flow or trigger that is also touching the Account, causing a "before save" vs "after save" conflict or a row lock.

**When it occurs:** When the BA captures the automation outcome ("update the Account") without asking whether the Account may be updated by other automation at the same time. In high-volume orgs or orgs with complex automation, cross-object updates create transaction ordering problems that are very hard to debug post-deployment.

**How to avoid:** When any automation requirement involves updating a record that is not the trigger record, flag it explicitly in the story:
- Add a note: "This automation writes to [parent/related object] — requires architect review for transaction safety"
- Capture whether the update needs to be synchronous (same transaction) or can be asynchronous (scheduled job, platform event)
- Identify other automations already updating the same target object — this is a dependency that can cause silent failures

---

## Gotcha 4: Volume-Sensitive Requirements Captured Without Volume Data

**What happens:** A BA captures the requirement "when a Lead is converted, create an Opportunity and a Task." The admin builds a record-triggered flow. It works in UAT with 10 test records. In production, a campaign generates 500 lead conversions per hour. The flow hits governor limits; lead conversions fail silently.

**When it occurs:** When the BA treats all automation requirements as equivalent regardless of the number of records affected. Salesforce's governor limits mean that automation behaving correctly on one record may fail catastrophically on 200 records in a single transaction (e.g., a Data Loader import, a mass approval, or a bulk process job).

**How to avoid:** For every automation requirement, capture:
- How many records are affected at once in the worst case?
- Is this triggered by user action (one at a time) or by an integration or batch job (potentially thousands at once)?
- What is the acceptable failure behavior if the automation cannot complete?

If the answer is "hundreds of records per trigger event," flag it as a performance-sensitive requirement and involve a developer or architect before the admin starts building.
