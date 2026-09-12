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

---

## Gotcha 6: Auto-Response `senderEmail` Equal to the Email-to-Case Routing Address Creates a Mail Loop

**What happens:** An `autoResponseRules` rule entry's `senderEmail` (or `replyToEmail`) is set to the same address as an Email-to-Case routing address's `emailAddress`. The customer's mail client replies to the acknowledgement, the reply lands back on the routing address, Email-to-Case creates a new Case from it, the assignment rule fires, and the auto-response fires again — an unbounded loop that also multiplies Case counts and, on a metered mail gateway, cost.

**When it occurs:** Most often when an admin reuses the public support address (e.g., `support@acme.example`) as both the Email-to-Case intake address and the auto-response sender because it "is the address customers already know." It also occurs when the sender is a distinct address that silently forwards into the routing address (a mail rule, a distribution list, or a shared mailbox alias), which the metadata cannot detect.

**How to avoid:**
- Give the auto-response rule a dedicated, verified OrgWideEmailAddress (e.g., `support-noreply@acme.example`) that is provisioned only as a sender, never as an Email-to-Case routing address. This address is also a deploy-time prerequisite in the target org — see Gotcha 7.
- Confirm the sender address has no mail-server forwarding rule that points at any routing address, and disable "keep a copy and auto-reply" on any forwarding mailbox in the chain (`admin/email-to-case-configuration`).
- Run `scripts/check_assignment_rules.py` — rule `AR-LOOP-01` cross-references every `autoResponseRules` `senderEmail` against every `routingAddresses/emailAddress` it can find under `settings/Case.settings-meta.xml` in the tree and errors on a match; `AR-LOOP-02` warns when no routing-address inventory is in scope to check against.
- After deploy, send one real email to each public address and confirm the Case count per address stops at one (`admin/email-to-case-configuration`, references/metadata-examples.md, "Loop test").

---

## Gotcha 7: `autoResponseRules` `senderEmail` Fails Deploy Validation, Not Just Send, When the OrgWideEmailAddress Is Missing in the Target Org

**What happens:** An `AutoResponseRule` whose `ruleEntry.senderEmail` names an address (e.g., `support-noreply@acme.example`) that has no matching, verified `OrgWideEmailAddress` record in the target org fails `sf project deploy start` validation itself — before any email is ever sent — with `<address> is an invalid From email address.: Email Address`. This is a deploy-time blocker, not only the send-time symptom described in `admin/email-templates-and-alerts` (unverified addresses "cannot send"). `UNVERIFIED (2026-09-12): proven live in a dry-run, not stated in the guide` — confirmed via `sf project deploy start --dry-run` (API 67.0) against a target org with `SELECT Address FROM OrgWideEmailAddress` returning 0 rows for the address; not documented in the Metadata API reference for `AutoResponseRule`.

**When it occurs:** Promoting an auto-response rule to any org (new sandbox, a freshly refreshed sandbox, first production deploy) where nobody has yet created and verified the org-wide address in Setup — most commonly when the rule metadata is authored and version-controlled ahead of the manual, non-deployable Setup step that has to happen in every org separately (`admin/email-templates-and-alerts` references/metadata-and-sender-identity.md, "Org-wide email address (the sender)": no metadata type exists for it).

**How to avoid:**
- Provision and verify the `OrgWideEmailAddress` in Setup → Organization-Wide Addresses in the target org *before* deploying any `AutoResponseRule` (or workflow email alert) that names it as a sender. Verification requires clicking the confirmation link sent to the mailbox — it cannot be scripted or included in the deploy.
- List this step explicitly under deploy prerequisites in `references/migration-and-sandbox.md` deploy-order and in any release runbook, the same way a required custom field or permission set is listed — not assumed as "already there."
- Keep this address distinct from any Email-to-Case routing address (Gotcha 6, `AR-LOOP-01`); provisioning it for deploy does not relax that separation.
- `scripts/check_assignment_rules.py` rule `AR-SENDER-01` prints one INFO line per distinct `senderEmail`/`replyToEmail` found in an `autoResponseRules` file, naming it as a deploy-time prerequisite to check manually — it is INFO only because the checker has no org connection and cannot query `OrgWideEmailAddress` itself.
- Before deploying, run `SELECT Address, IsVerified FROM OrgWideEmailAddress WHERE Address = '<sender>'` against the target org and confirm one verified row exists.
