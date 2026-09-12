---
name: case-management-setup
description: "Configuring Salesforce case management: case queues, assignment rules, escalation rules, auto-response rules, Email-to-Case, Web-to-Case, case teams, entitlements, and milestones. Use when setting up or troubleshooting the Service Cloud case handling layer. Trigger keywords: email-to-case, web-to-case, escalation rules, case teams, entitlements, milestones, auto-response, case queue. NOT for Standard vs On-Demand Email-to-Case and routing-address setup — use admin/email-to-case-configuration. NOT for routing case work items to agents — use admin/omni-channel-routing-setup."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Reliability
triggers:
  - "how do I set up email to case so customer replies thread into the same case instead of creating duplicates"
  - "escalation rule is not firing to reassign overdue cases to the manager queue"
  - "auto-response email is not being sent when a customer submits a web-to-case form"
  - "how do I configure entitlements and milestones for SLA tracking in Service Cloud"
  - "web-to-case form hit the 50000 pending request limit and new submissions are being dropped"
  - "case team members cannot see the case even though I added them to the predefined team"
  - "how do I set up email to case so customer replies thread instead of creating new cases"
  - "we're having issues with email to case"
  - "case intake setup from requirements email web form routing sla"
  - "case intake"
  - "set up case intake for a support team"
  - "deploy web-to-case with metadata api instead of clicking through setup"
  - "case status picklist value deployed but agents cannot select it"
  - "web-to-case submissions are all owned by the admin instead of the support queue"
  - "named in package.xml but was not found in zipped directory"
  - "business process not found in zipped directory"
  - "CaseSettings Enter the system user's email address on deploy"
tags:
  - cases
  - email-to-case
  - web-to-case
  - escalation-rules
  - entitlements
  - service-cloud
  - case-teams
  - auto-response-rules
inputs:
  - "Service Cloud org with Cases enabled"
  - "Decision on inbound channel: Email-to-Case, Web-to-Case, or both"
  - "SLA requirements: response time targets, escalation thresholds, business hours"
  - "Support team structure: queues needed, case team roles, entitlement processes"
outputs:
  - "Configured Email-to-Case routing address with thread-ID handling"
  - "Web-to-Case HTML form embedded on external site"
  - "Active case assignment rule with ordered rule entries targeting queues"
  - "Active escalation rule with time-based re-route or notification actions"
  - "Auto-response rule tied to assignment rule execution"
  - "Case team roles and predefined team setup"
  - "Entitlement process with milestones and violation actions (if SLA tracking required)"
dependencies: []
version: 1.3.0
author: Pranav Nagrecha
updated: 2026-09-12
---

# Case Management Setup

This skill activates when an admin needs to configure or troubleshoot the full Service Cloud case handling layer: inbound channels (Email-to-Case, Web-to-Case), routing and assignment, time-based escalation, auto-response emails, case team collaboration, and entitlement/milestone SLA tracking.

---

## Before Starting

Gather this context before working on case management configuration:

- **Which inbound channels are needed?** Email-to-Case and Web-to-Case have different limits and configuration paths. Email-to-Case uses routing addresses; Web-to-Case generates an HTML form.
- **What are the SLA requirements?** Escalation rules require business hours to be configured first, or the clock runs 24/7. Entitlements require the Entitlements feature to be enabled in Setup before any configuration is possible.
- **Are assignment rules already active?** Auto-response rules ONLY fire when an assignment rule also fires. This is the single most common false assumption in case management setup. If assignment rules are not active or not matching, auto-responses will not send regardless of auto-response rule configuration.
- **What are the queue membership and deletion policies?** Deleting a queue that owns open cases orphans those cases — they have no owner and no queue. Enforce a transfer-before-delete policy.

---

## Questions to Ask Before Configuring

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "Which channels create cases, and at what volume?" | Email-to-Case, Web-to-Case, and manual entry have different limits, routing behaviour, and spam exposure | A channel inventory with the daily limit and pending-queue risk for each |
| "Which mailbox addresses route in, and who owns them?" | Each routing address pre-classifies the case before assignment runs and must never be an auto-response sender | Routing addresses mapped to origin, queue, and calendar |
| "What must happen in the first minute: owner, acknowledgement, calendar, priority?" | Assignment, auto-response, business hours, and priority all resolve during the save; anything set later runs on the wrong clock | The before-save Flow scope and the assignment rule design |
| "What is the SLA, and does it pause outside working hours?" | Escalation entries and milestones read calendars only if wired; the shipped default is 24/7 | Calendar design and the consumer map (`admin/business-hours-and-holidays`) |
| "Who is allowed to reply to the customer from which address?" | Sender identity is a verified org-wide address with profile restrictions | Templates and senders that deploy and deliver |
| "How will we know it works before customers do?" | Threading, auto-response loops, and truncation only show up under real email | A clock test, a threading test, and a loop test in the sandbox |
| "How is Case Priority derived — from the form, from the mailbox, or from the account?" | `Priority` is a picklist stamped at save by three competing sources: a hidden or visible input on the Web-to-Case form, `casePriority` on the Email-to-Case routing address, and any before-save automation. Undecided, they overwrite each other and the SLA fires on the wrong tier | A single named source per channel, the `CasePriority` values it may stamp, and the derivation rule for anything else |
| "Which user should Case History name when a rule, not a person, changed the case — and if that is the system user, which mailbox is it?" | Assignment rules, escalation rules and On-Demand Email-to-Case all write as one configured identity. `useSystemUserAsDefaultCaseUser` `false` requires `defaultCaseUser`; `true` requires `systemUserEmail`, which the guide never says and the org enforces at deploy (gotchas #12) | A named, licensed automation user or a monitored system address — and the pair set explicitly rather than inherited from the target org |
| "Will this deploy in source format — do the file stems match the `fullName`s?" | A DX project decomposes the Case object into one file per business process and record type, and the CLI names each `package.xml` member from the **file stem**. A `Support_Process.businessProcess-meta.xml` whose `<fullName>` reads `Support Process` declares a member that is not in the zip, and the deploy dies before the org sees it | Process and record-type names in stem form (`Inbound_Intake_Process`), display wording moved to `<description>`, and a checker run that proves it (`references/metadata-examples.md` § 2.1) |
| "Which support processes (status sets) exist, and which record type gets each?" | A Case record type is invalid without a support process, and the process is a subset of the `CaseStatus` value set — so the status ladder, the closed states, and the reports are all decided here, before any rule is written | The status ladder per channel, at least one closed status in each, and the record type each intake channel lands on |

A proper case intake configuration adds a channel inventory with limits, deterministic routing on every channel, acknowledgements that cannot loop, an SLA clock that pauses on purpose, and evidence from a sandbox test; "just turning on Email-to-Case" adds an inbox that fills a queue nobody was assigned to.

---

## Core Concepts

### Inbound Channel Limits and Behaviors

**Email-to-Case** converts inbound customer emails into cases. Key limits and behaviors:

- Maximum inbound message size: **35 MB** total (body, HTML, and attachments together; MIME encoding inflation makes roughly 25 MB the effective attachment ceiling). Larger messages are rejected. The sourced limit history is in admin/email-to-case-configuration.
- Email body is truncated at **32,000 characters** and the remainder is dropped without any notice to the agent or customer. UNVERIFIED (2026-09-04): this figure is carried from the Email-to-Case Limits Help page cited in references/well-architected.md and could not be re-checked against a fetchable official source; treat the exact number as approximate and confirm in the org before quoting it to a customer.
- Thread ID handling is critical. Salesforce embeds a thread ID token in outgoing case emails. When the customer replies, Salesforce reads the token to find the parent case and adds the reply as a new Email Message record. **If the routing address is misconfigured or the thread ID is stripped by a mail server, the reply creates a new case instead of threading.** Test threading end-to-end before go-live.
- On-Demand Email-to-Case (recommended) uses Salesforce-hosted routing addresses. Classic Email-to-Case uses a local email agent. Use On-Demand unless firewall or data residency requirements prevent it.

**Web-to-Case** converts form submissions from a website into cases. Key limits:

- Web-to-Case has a **24-hour submission limit** (5,000 by default; the exact allocation depends on edition and can be raised by Support). Requests beyond it are not lost immediately — they go into a **pending request queue shared with Web-to-Lead, capped at 50,000 combined requests**. Only once *that* queue is full are further requests rejected outright and not queued. When rejection starts, **Salesforce emails the administrator for the first five rejected submissions** — a real but easily missed signal, since it stops after five no matter how long the outage lasts. The submitter still sees the form's success page either way. Monitor the pending count in Setup; Support can raise the pending limit.
- Web-to-Case has no native field validation. All validation must be done in the HTML form (JavaScript) or via Apex triggers / Flow after the case is created.
- If the submitter's email matches an existing Contact record, Salesforce automatically populates the Contact lookup. If no match is found, the contact field is blank — no new Contact is created automatically.

### Assignment Rules and Auto-Response Dependency

Only **one assignment rule can be active** per object. For cases, this means one active case assignment rule at all times. Rule entries are evaluated in order; the first match wins.

**Auto-response rules depend entirely on assignment rules.** The auto-response rule fires ONLY when the active assignment rule fires. If no assignment rule is active, if no rule entry matches the incoming case, or if the case was created in a way that does not trigger the assignment rule (e.g., via the API without the `Sforce-Auto-Assign: true` header), the auto-response will not fire. This is a platform behavior, not a configuration bug.

### Escalation Rules

Escalation rules re-route or notify when cases are not resolved within a time threshold. Critical behaviors:

- Only **one active escalation rule** per org (not per object). The rule contains multiple entries with time-based conditions.
- The escalation engine runs on an **hourly cadence**. Escalation is not real-time. A case that crosses the threshold at 9:05 AM will not be escalated until the engine next runs, potentially at 10:00 AM. Design SLAs with this lag in mind.
- **Business hours must be explicitly assigned** to the escalation rule entry, OR the time clock runs 24 hours a day, 7 days a week. Forgetting to attach a business hours record is the most common escalation misconfiguration.
- **Deactivating and reactivating an escalation rule can trigger a wave of immediate escalations** for all cases that were accumulating escalation time while the rule was inactive. Re-activation causes the engine to evaluate all open cases against the rule simultaneously. This can generate hundreds of escalation actions and emails at once in a large org. Always test reactivation in a sandbox and warn stakeholders.

### Case Teams

Case teams allow multiple users to collaborate on a single case, each with a defined access level, without changing the case owner.

- Case team **roles** define the access level (Read Only, Read/Write, Case Owner's role) and must be created before predefined teams can be built.
- A **predefined team** is a template — a named set of users paired with roles. Adding a predefined team to a case grants each member access per their role.
- Case team access is **independent of org-wide sharing and sharing rules**. A user added to a case team can see and edit the case even if they would not have access via normal sharing. This is by design — use it intentionally.
- Case team members do not receive automatic email notifications when added to a case. Use workflow rules or Flow to send notifications if needed.

### Entitlements and Milestones

Entitlements represent the level of support a customer is entitled to (e.g., response within 4 business hours). Milestones are the specific time-based targets within an entitlement process.

- **Entitlements must be enabled in Setup** (Feature Settings → Service → Entitlement Management) before any entitlement configuration is accessible. This is often overlooked.
- Milestones exist within an **entitlement process**. You cannot add milestones directly to a case without an entitlement process.
- **Adding entitlement templates to products** (so that cases auto-receive an entitlement when created for a product) is only available in Salesforce Classic. In Lightning, entitlements must be applied manually or via Flow/Apex.
- Milestone violation and warning actions (emails, field updates) are configured on the milestone within the entitlement process, not on the case itself.

---

## Common Patterns

### Pattern: Email-to-Case with Threaded Reply Handling

**When to use:** Customer support team receives inbound email, needs replies to thread into the same case rather than create new cases.

**How it works:**
1. Navigate to Setup → Email-to-Case → Enable On-Demand Email-to-Case.
2. Create a routing address (e.g., support@yourcompany.com). Salesforce generates a Salesforce-hosted email address for the mail server to forward inbound mail to.
3. Configure your external mail server to forward inbound mail from support@yourcompany.com to the Salesforce routing address.
4. In the routing address settings, enable "Create Task for new emails" if you need agent notification.
5. Set the case origin, default status, and priority for cases created from this address.
6. Test: send an inbound email, confirm a case is created. Reply from Salesforce to the case. Have the customer reply to that email. Confirm the reply appears as an Email Message on the original case (not a new case).

**Why not Classic Email-to-Case:** The local email agent requires a server on-premise or a relay. On-Demand routes through Salesforce infrastructure and requires no local component.

### Pattern: Web-to-Case with Assignment and Auto-Response

**When to use:** Customers submit support requests through a website form; confirmations should be sent automatically.

**How it works:**
1. Navigate to Setup → Web-to-Case. Enable Web-to-Case and configure a default case origin.
2. Select the fields to expose on the form. Salesforce generates the HTML snippet.
3. Embed the HTML in the external web page.
4. Create a case assignment rule with a catch-all entry pointing to the support queue.
5. Create a case auto-response rule. The rule fires when the assignment rule fires, sending the confirmation email to the contact email address submitted on the form.
6. Use Flow to add validation logic if required fields or format checking is needed post-submission.

**Why not use the default case owner alone:** Web-to-Case without an assignment rule means all cases land with the default case owner, bypassing queue routing. Auto-response also will not fire without an active assignment rule.

### Pattern: SLA Tracking with Entitlements and Milestones

**When to use:** Business has contractual or operational SLA commitments (e.g., respond within 4 hours, resolve within 24 hours) and needs automated tracking and violation alerts.

**How it works:**
1. Enable Entitlement Management in Setup.
2. Create business hours records matching support team schedules.
3. Create an entitlement process. Add milestones (e.g., "First Response" — 4 business hours, "Resolution" — 24 business hours). Set warning and violation actions on each milestone.
4. Create an entitlement record for the relevant accounts or contacts.
5. Associate the entitlement with new cases (manually, via Flow, or via entitlement templates on products if using Classic).
6. Monitor milestone completion in the Case Milestones related list on the case.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Auto-response emails not sending | Verify an active assignment rule exists and is matching the case | Auto-response only fires when assignment rule fires — no assignment rule, no auto-response |
| Duplicate cases from customer email replies | Fix thread ID handling in Email-to-Case routing address; test end-to-end | Misconfigured routing strips thread tokens, causing new cases per reply |
| Web-to-Case submissions being lost | Check the admin's mailbox for the rejection notifications Salesforce sends for the first five rejected requests, then check the pending request count in Setup | Over the 24-hour limit, requests queue (50,000 combined Web-to-Case + Web-to-Lead); once that queue is full they are rejected. Nothing is surfaced to the submitter |
| Escalation not firing on time | Attach a business hours record to escalation rule entries | Without business hours, clock runs 24/7; engine cadence is hourly |
| Case team members cannot access case | Verify case team roles are created; user is on the case team (not just the predefined team) | Roles must exist before teams; adding predefined team to case grants access, not just defining the predefined team |
| Entitlements not visible in Setup | Enable Entitlement Management feature flag | Feature must be enabled before any configuration is available |
| Entitlement templates on products not visible in Lightning | Use Flow or Apex to apply entitlements automatically | Template-on-product UI is Classic-only; Lightning requires automation |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. Answer the § Questions to Ask table, then retrieve what the org already has:
   `sf project retrieve start --metadata "Settings:Case" "CustomObject:Case" "StandardValueSet:CaseOrigin" "StandardValueSet:CaseStatus"`. Read `references/worked-example-case-intake.md` for the shape of a complete answer set.
2. Author the value layer from `references/metadata-examples.md` §1: the `CaseOrigin`, `CasePriority` and `CaseStatus` standard value sets, one origin value per channel. Nothing downstream can reference a value that does not exist yet.
3. Author the object layer from §2: one support process per status ladder, one Case record type per intake channel (`businessProcess` is mandatory on Case record types, and its value is the process's file stem — §2.1), and the compact layout assignment. Read `admin/record-types-and-page-layouts` for the `Layout` and profile-visibility half.
4. Build the queues and Classic email templates the settings will name (`admin/queues-and-public-groups`, `admin/email-templates-and-alerts`), then author `settings/Case.settings-meta.xml` from §3 — `webToCase` here, `emailToCase` from `admin/email-to-case-configuration`, both in the one file.
5. Author the rule layer in the sibling skills — assignment rule with a catch-all, then auto-response (it fires only when assignment fires), then escalation entries with business hours explicitly attached (`admin/assignment-rules`, `admin/escalation-rules`, `admin/business-hours-and-holidays`).
6. If SLA tracking is required, add the entitlement process and milestones per `admin/entitlements-and-milestones`, plus the automation that attaches entitlements to new cases.
7. Run `python3 skills/admin/case-management-setup/scripts/check_case_management_setup.py --manifest-dir <metadata-root> --verbose` (it exits 1 on any finding; `ERROR: CMS-STEM-01/02` mean a decomposed file stem and its `<fullName>` disagree, which no org-side validation will catch for you, and `ERROR: CMS-SYSUSER-01` means `useSystemUserAsDefaultCaseUser` is `true` with no `systemUserEmail`, which the org rejects at deploy), deploy in the §5 order (values → object → queues/templates → settings → rules), then run the three verification queries in §6 and the Review Checklist below.

---

## Review Checklist

Run through these before marking case management configuration complete:

- [ ] Email-to-Case routing address is verified and thread ID handling tested end-to-end (reply threads into parent case, not new case)
- [ ] Web-to-Case pending request count is below the 50,000 combined Web-to-Case + Web-to-Lead cap; the address receiving Salesforce's first-five-rejection notifications is a monitored mailbox, not an unread admin inbox
- [ ] Active case assignment rule exists with at least one catch-all entry; no cases are falling to the default case owner unintentionally
- [ ] Auto-response rule entries have a valid email template; confirmed that assignment rule fires for the same creation events
- [ ] Escalation rule entries each have a business hours record explicitly attached; deactivation/reactivation risk communicated to stakeholders
- [ ] All queues referenced by assignment and escalation rules exist, have at least one active member, and have Case in their Supported Objects list
- [ ] Case team roles are created before predefined teams; predefined teams contain current active users
- [ ] `useSystemUserAsDefaultCaseUser` is set explicitly, and its partner element is set with it — `defaultCaseUser` (a real active user) when `false`, `systemUserEmail` (a monitored mailbox) when `true`
- [ ] Every decomposed `*.businessProcess-meta.xml` / `*.recordType-meta.xml` file's stem is exactly its `<fullName>`, no `<fullName>` contains a space, and every record type's `<businessProcess>` names an existing process stem — `check_case_management_setup.py` rules CMS-STEM-01 / CMS-STEM-02 pass
- [ ] If entitlements used: Entitlement Management is enabled, entitlement processes are active, business hours are attached to milestones, and automation applies entitlements to new cases

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Auto-response rule requires assignment rule to fire** — The auto-response rule is not independent. It fires only when the active case assignment rule fires for that case. If the assignment rule is inactive, has no matching entry, or was bypassed (e.g., API insert without `Sforce-Auto-Assign: true` header), the auto-response will not send. This is the most commonly misdiagnosed "auto-response not working" issue.
2. **Escalation reactivation triggers bulk escalations** — Deactivating an escalation rule pauses escalation time accumulation for open cases. When you reactivate the rule, the engine evaluates all open cases at once. Cases that have been open longer than the threshold since deactivation will escalate immediately in a single wave. In a large org, this can generate thousands of emails and re-assignments at once. Always test reactivation volume in a sandbox.
3. **Email-to-Case body truncation is silent** — Long customer emails are truncated (32,000 characters per the cited Help page; figure marked UNVERIFIED in Core Concepts) without any notification to the agent or customer. Content after that limit is not in the case body. If customers send lengthy technical logs or attachments-as-text, critical information may be missing; ask for logs as attachments.
4. **Deleting a queue orphans owned cases** — If you delete a queue that currently owns open cases, those cases lose their owner. They will not appear in any queue view or any individual's My Cases view until manually reassigned. Enforce a case transfer protocol before queue deletion.
5. **Web-to-Case has no native validation** — The generated HTML form contains no JavaScript validation. Required-field enforcement, format checks (phone numbers, email formats), and spam prevention must all be implemented in the HTML form customization or via post-creation Flow/Apex. Without this, garbage data will enter your org.
6. **Entitlement template on product is Classic-only** — Associating an entitlement template with a product (so cases auto-receive an entitlement) is only configurable in Salesforce Classic. In Lightning Experience, there is no equivalent UI. Entitlements must be applied to cases via Flow, Process Builder, or Apex.
7. **A deployed picklist value is not a selectable one** — `StandardValueSet` puts the value on the object; the record type's Selected Values list decides whether anyone can pick it. Deploy both, or the new Status appears in metadata and nowhere else. Detail in `references/gotchas.md` #7.
8. **Web-to-Case cannot name its own owner** — `WebToCaseSettings` has three fields and none is an owner. Unmatched submissions fall to org-level `defaultCaseOwner`, which an Email-to-Case routing address can also overwrite. Detail in `references/gotchas.md` #8.
9. **`keepRecordTypeOnAssignmentRule` covers manual creation only** — neither inbound channel is "manually created", so it does not protect an intake record type. Detail in `references/gotchas.md` #9.
10. **`useSystemUserAsDefaultCaseUser` needs a partner in both directions** — the guide documents only `false` → `defaultCaseUser`. Setting it `true` with no `<systemUserEmail>` is rejected with `CaseSettings: Enter the system user's email address.` UNVERIFIED (2026-09-12): the `true` half is proven live, not in the guide. Checker rule `CMS-SYSUSER-01`. Detail in `references/gotchas.md` #12.
11. **A decomposed file's stem is the package member** — in source format the CLI builds the `package.xml` member from the file stem, so a `Support_Process.businessProcess-meta.xml` carrying `<fullName>Support Process</fullName>` fails with `An object 'Case.Support_Process' of type BusinessProcess was named in package.xml, but was not found in zipped directory`. Detail in `references/gotchas.md` #11.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Email-to-Case routing address | Configured Salesforce routing address; mail server forward rule; thread ID verification |
| Web-to-Case HTML form | Generated HTML snippet embedded in external web page; post-submit Flow for validation |
| Active case assignment rule | One active rule with ordered entries, each targeting a queue; catch-all entry last |
| Active escalation rule | Time-based entries with business hours, re-route/notify actions, tested in sandbox |
| Auto-response rule | Entries with email templates tied to assignment rule execution events |
| Case team roles and predefined teams | Roles with access levels; predefined teams with current members |
| Entitlement process | Business hours, milestones with warning/violation actions, automation to apply to cases |

---

## Reference Files

| File | Read it when |
|---|---|
| `references/metadata-examples.md` | Writing deployable XML: `CaseOrigin`/`CasePriority`/`CaseStatus` value sets, Case support processes and record types, the source-format stem rule (§2.1), the `webToCase` block, package.xml, deploy order, and the three verification queries |
| `references/worked-example-case-intake.md` | Building a whole intake solution from requirements: the questions, decisions, ten-section workbook rows, artefact list, tests, and the gaps found |
| `references/gotchas.md` | Auto-response dependency, escalation reactivation waves, truncation, queue deletion, Web-to-Case validation, invisible picklist values, the default-owner fallback, record-type override, closed-status gaps, the source-format stem rule, the `useSystemUserAsDefaultCaseUser` / `systemUserEmail` pair |
| `references/examples.md` | Diagnosing a live symptom: threading failure, auto-response silence, weekend escalations, case team access |
| `references/llm-anti-patterns.md` | Reviewing AI-generated case-management guidance before acting on it |
| `references/well-architected.md` | Justifying a channel or escalation choice, and the source list behind every claim in this package |

---

## Related Skills

- admin/assignment-rules — use when the focus is on case assignment rule entry logic, criteria design, or API trigger behavior for case assignment specifically
- admin/queues-and-public-groups — use when creating or troubleshooting the queues that assignment and escalation rules route cases into
- admin/email-to-case-configuration — use for the `emailToCase` block, routing addresses, threading switches, and forwarding verification; it owns the other half of `settings/Case.settings-meta.xml`
- admin/record-types-and-page-layouts — use for the `Layout` XML and the profile/permission-set visibility that makes an intake record type selectable
- admin/escalation-rules — use for escalation entry criteria, time triggers, and re-route actions
- admin/entitlements-and-milestones — use when the SLA must be tracked as an entitlement process with milestones
- admin/business-hours-and-holidays — use when the escalation or milestone clock must pause outside working hours
- admin/validation-rules — use when the intake needs server-side enforcement that the Web-to-Case form cannot provide
