# Gotchas — Assignment Rules

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: API Integrations Bypass Assignment Rules by Default

**What happens:** Records inserted via REST API, SOAP API, Data Loader, or Apex `Database.insert()` do NOT trigger assignment rules unless the caller explicitly opts in. The record owner becomes the running user (typically an integration service account), not the expected queue or rep.

**When it occurs:** Every time a third-party system, Data Loader job, or Apex integration creates Leads or Cases without the correct assignment configuration. Common in migrations, Marketo/HubSpot syncs, and nightly ETL jobs. It is also common during sandbox refreshes when developers test integrations without the header.

**How to avoid:**
- **REST API:** Add the `Sforce-Auto-Assign: true` header to the request, or use `Sforce-Auto-Assign: <rule-id>` for a specific rule.
- **SOAP API:** Include `<AssignmentRuleHeader><useDefaultRule>true</useDefaultRule></AssignmentRuleHeader>` in the SOAP envelope.
- **Data Loader:** In the Settings dialog, set the `Assignment Rule` property to the rule's 15- or 18-character ID.
- **Apex:** Set `Database.DMLOptions dml = new Database.DMLOptions(); dml.assignmentRuleHeader.useDefaultRule = true;` before calling `Database.insert(records, dml);`.
- Document the required header in integration runbooks and code review checklists.

---

## Gotcha 2: Activating a New Rule Silently Deactivates the Existing One

**What happens:** When you check "Active" on a new assignment rule and save, Salesforce automatically unchecks "Active" on the previously active rule — with no warning or confirmation dialog. If administrators are not aware, they may believe both rules are still running.

**When it occurs:** When building a new routing strategy while the old one is still in production use, or when a second admin activates a test rule without knowing the first admin set up the production rule.

**How to avoid:**
- Before activating any new rule, explicitly document which rule is currently active.
- After activating a new rule, navigate to the Assignment Rules list and confirm the old rule shows "Inactive."
- Use a naming convention that includes the date of activation (e.g., "Lead Routing 2025-Q2") so the active rule's age is visible in the list.
- In orgs where rule changes are controlled, treat assignment rule activation as a change management event requiring communication to the sales or support team.

---

## Gotcha 3: UI-Created Records Require Manual Checkbox; Users Often Skip It

**What happens:** When a sales rep or support agent creates a Lead or Case via the Lightning UI, a checkbox labeled "Assign using active assignment rule" (Lead) or "Run assignment rules" (Case) appears in the assignment section of the creation form. If the user does not check this box, the record is assigned to the creating user and no rule fires.

**When it occurs:** Any time a record is created manually by a logged-in user. This is the most common cause of leads sitting in rep mailboxes rather than the intended regional queue, especially for inbound calls where reps manually create leads during the call.

**How to avoid:**
- Use a record-triggered Flow (before-save) to set a boolean field or set OwnerId programmatically when manual creation is detected, bypassing the checkbox entirely.
- Alternatively, use a Flow to present a guided creation screen that always calls assignment rules.
- If relying on the checkbox, add the default checkbox state using Lightning App Builder configuration or profile-level customization — note that the default state is unchecked, and there is no org-wide setting to change this.
- Consider whether the use case is better served by Web-to-Lead (which always runs the rule) rather than manual rep entry.

---

## Gotcha 4: Deactivated Users in Queue Membership Block Case Acceptance

**What happens:** If a user is deactivated but remains a member of a queue, the queue still accepts assignments and still appears to have members. However, the deactivated user cannot log in to accept or work records. The queue notification email (if configured to send to individual members rather than a queue email address) will fail silently for the deactivated member.

**When it occurs:** After user offboarding when the deactivation checklist does not include removing the user from queue memberships.

**How to avoid:**
- Add "remove user from all queues" to the offboarding checklist.
- Periodically audit queue membership: `SELECT Id, QueueId, UserOrGroupId FROM GroupMember WHERE Group.Type = 'Queue'` — join with User.IsActive to find inactive members.
- Configure queues with a queue email address (rather than relying on member notifications) so routing is not disrupted by individual member status.

---

## Gotcha 5: Rule Entry Criteria Use Snapshot Values, Not Formula Results

**What happens:** Assignment rule entry criteria evaluate the field values on the record at the time the rule runs. If a criterion references a formula field or a roll-up summary field, the evaluated value may not reflect real-time calculations because those field types can lag or are not recalculated before rule evaluation in all contexts.

**When it occurs:** When rule criteria include formula fields (e.g., a formula that calculates a tier from multiple raw fields), especially during API inserts where the record snapshot may not have formulas recalculated before the assignment rule header fires.

**How to avoid:**
- Prefer criteria on raw editable fields (text, picklist, number) rather than formula fields.
- If formula-based routing is needed, use a record-triggered Flow (before-save) to compute and write the result to a plain field, then base the assignment rule criteria on that plain field.
- Test rule entry criteria via API insert, not just UI creation, to catch formula evaluation order issues.
