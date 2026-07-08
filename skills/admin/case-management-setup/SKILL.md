---
name: case-management-setup
description: "Configuring Salesforce case management: case queues, assignment rules, escalation rules, auto-response rules, Email-to-Case, Web-to-Case, Case Feed, case teams, entitlements, and milestones. Use when setting up or troubleshooting the Service Cloud case handling layer, including the single-active-rule slots that assignment, auto-response, and escalation rules each occupy. Trigger keywords: email-to-case, web-to-case, escalation rules, case teams, entitlements, milestones, auto-response, case queue, case feed, activate assignment rule, only one active rule. NOT for case assignment rule logic only (use assignment-rules skill). NOT for Omni-Channel routing (use omni-channel-routing-setup). NOT for enabling Einstein Case Classification (use agentforce-service-ai-setup). NOT for CTI or telephony integration."
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
  - "activate a new case assignment rule without silently deactivating the one already running"
  - "decide whether support work should be pulled from a case queue or pushed by an assignment rule"
tags:
  - cases
  - email-to-case
  - web-to-case
  - escalation-rules
  - entitlements
  - service-cloud
  - case-teams
  - auto-response-rules
  - case-feed
  - case-queues
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
  - "Rule activation plan naming which single rule occupies each of the three active slots"
  - "Review cadence for rules, queues, and SLA thresholds"
dependencies: []
version: 1.1.1
author: Pranav Nagrecha
updated: 2026-07-08
---

# Case Management Setup

This skill activates when an admin needs to configure or troubleshoot the full Service Cloud case handling layer: inbound channels (Email-to-Case, Web-to-Case), routing and assignment, time-based escalation, auto-response emails, case team collaboration, and entitlement/milestone SLA tracking.

---

## Before Starting

Gather this context before working on case management configuration:

- **Which inbound channels are needed?** Email-to-Case and Web-to-Case have different limits and configuration paths. Email-to-Case uses routing addresses; Web-to-Case generates an HTML form.
- **What are the SLA requirements?** Escalation rules require business hours to be configured first, or the clock runs 24/7. Entitlements require the Entitlements feature to be enabled in Setup before any configuration is possible.
- **Are assignment rules already active?** Auto-response rules ONLY fire when an assignment rule also fires. This is the single most common false assumption in case management setup. If assignment rules are not active or not matching, auto-responses will not send regardless of auto-response rule configuration.
- **What is already occupying each active rule slot?** Assignment, auto-response, and escalation rules each get exactly one active rule for cases at a time. Activating a new one deactivates the incumbent. Inventory the current active rule in each slot — and who owns it — before you build a replacement.
- **What are the queue membership and deletion policies?** Deleting a queue that owns open cases orphans those cases — they have no owner and no queue. Enforce a transfer-before-delete policy.
- **What is the review cadence after go-live?** Salesforce is explicit that case management "isn't a 'set it and forget it' process" — rule entries, queue membership, and SLA thresholds drift as the support org changes. Agree on who reviews them and how often before you configure anything.

---

## Core Concepts

### Inbound Channel Limits and Behaviors

**Email-to-Case** converts inbound customer emails into cases. Key limits and behaviors:

- Maximum inbound email size: **25 MB** (attachments included). Emails exceeding this limit are rejected.
- Email body is truncated at **32,000 characters**. Content beyond that limit is silently dropped — not stored in an attachment.
- Thread ID handling is critical. Salesforce embeds a thread ID token in outgoing case emails. When the customer replies, Salesforce reads the token to find the parent case and adds the reply as a new Email Message record. **If the routing address is misconfigured or the thread ID is stripped by a mail server, the reply creates a new case instead of threading.** Test threading end-to-end before go-live.
- On-Demand Email-to-Case (recommended) uses Salesforce-hosted routing addresses. Classic Email-to-Case uses a local email agent. Use On-Demand unless firewall or data residency requirements prevent it.

**Web-to-Case** converts form submissions from a website into cases. Key limits:

- **50,000 pending Web-to-Case requests** is a hard org-level limit. If this queue is full, new submissions are silently dropped — Salesforce does not queue them or send an error to the submitter. Monitor the pending count in Setup and clear it regularly.
- Web-to-Case has no native field validation. All validation must be done in the HTML form (JavaScript) or via Apex triggers / Flow after the case is created.
- If the submitter's email matches an existing Contact record, Salesforce automatically populates the Contact lookup. If no match is found, the contact field is blank — no new Contact is created automatically.

### Queues Are a Pull Model, Not a Push Model

A queue is a shared work list. Salesforce describes queues as lists "from which specific reps can jump in to solve certain types of cases" — reps pull the next case they can take, rather than each case being pushed to a named owner at creation.

This distinction drives the whole routing design:

- **Assignment rules push** a case into a queue based on criteria (urgency, issue type, customer status). Once there, ownership is the queue, not a person.
- **Reps pull** from the queue by accepting a case, which transfers ownership to them.
- **Omni-Channel pushes to a person** instead, using rep skills, availability, and workload rather than a rep's decision to accept. If you need that, the queue is an input to Omni-Channel, not a replacement for it — see the boundary section below.

A queue with no active members is a black hole: assignment rules will happily route cases into it and nobody will ever see them. Multiple queues can be active simultaneously — unlike rules, there is no single-active constraint on queues.

### Assignment Rules and Auto-Response Dependency

Only **one assignment rule can be active** per object. For cases, this means one active case assignment rule at all times. Rule entries are evaluated in order; the first match wins.

**Auto-response rules depend entirely on assignment rules.** The auto-response rule fires ONLY when the active assignment rule fires. If no assignment rule is active, if no rule entry matches the incoming case, or if the case was created in a way that does not trigger the assignment rule (e.g., via the API without the `Sforce-Auto-Assign: true` header), the auto-response will not fire. This is a platform behavior, not a configuration bug.

### Three Rule Types, Three Single-Occupancy Slots

Assignment, auto-response, and escalation rules each expose the same activation shape: you may author as many rules as you like, but **only one can be active at a time**. For auto-response rules, Salesforce states it plainly — "you can activate only one rule for leads and one rule for cases at a time." Assignment and escalation rules behave the same way.

The consequence that surprises admins: **activating a rule deactivates whichever rule currently holds that slot.** There is no merge, no warning banner in the case handling flow, and no error. The org silently swaps behavior at the moment of activation.

This makes rule activation a change-management event, not a Setup click:

- Never author a "regional" or "per-channel" second active rule. It cannot exist. Criteria for every channel and region must live as **entries inside the one active rule**.
- Version rules by name (`Case Assignment — 2026 Q3`) so the incumbent is identifiable and reversible.
- Sequence activation deliberately. Between deactivating rule A and activating rule B there is a window where no rule is active — during which incoming cases fall to the default case owner and no auto-response sends. Activating B directly (rather than deactivating A first) closes that window.

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

### Case Feed

Case Feed is the agent-facing surface of the case: a chronological feed of the case's history plus the actions an agent uses to work it. Salesforce describes it as streamlining "the way you create, manage, and view cases," displaying important case events "in chronological order" inside a Chatter feed. Its documented pieces are:

- **Highlights panel** — contact info, case name, description, status, priority, owner.
- **Publisher** — the actions agents work the case with (Email, Case Note, Change Status).
- **Feed filters** — narrow the feed to a subset of items.
- **Articles tool** — find Knowledge articles, attach them to the case, or email them to the customer.
- **Follow button and followers list** — Chatter notifications on case updates.
- **Feed and detail views** — agents toggle between the feed and the case detail layout.

**Read the interface scoping carefully.** The official Case Feed setup topics — enabling Case Feed actions and feed items, creating feed layouts, Case Feed and related lists — sit under the *Salesforce Classic* branch of the help tree ("Use Case Feed in Salesforce Classic"). Do not assume those Setup steps transfer to a Lightning record page. Configuring an agent's feed and actions in Lightning is a Lightning record page and quick-action exercise; see `admin/case-feed-send-email-action` for the Send Email action specifically.

### Where Case Management Setup Stops

Two capabilities sit adjacent to this layer and are frequently conflated with it. Both are real, current Salesforce features. Neither is configured here.

- **Omni-Channel** routes work across email, chat, messaging, and voice based on rep availability, skill set, and workload. Use it when a rep should be *given* the next case rather than picking it out of a queue, or when routing must respect capacity. Queues remain the input; Omni-Channel replaces the pull. Configure it via `admin/omni-channel-routing-setup`.
- **Einstein Case Classification** autofills case fields from AI predictions trained on the org's closed cases. Salesforce documents that Einstein "can then predict field values for most checkbox, picklist, and lookup fields on a case," and that Case Classification makes those predictions when a case is created. Do not conflate it with **Einstein Case Wrap-Up** — a separate app on the same help topic, which predicts when a chat with the customer ends. Classification reduces the manual data entry that otherwise gates correct routing. Licensing runs through Try Einstein (one model per app) or the Einstein for Service add-on (five models per app, plus automated field completion and optional case routing). Prerequisites, data-volume requirements, and enablement are covered by `agentforce/agentforce-service-ai-setup`.

Both depend on this layer being correct first. Skills-based routing over a queue nobody staffs, or AI-predicted field values feeding an assignment rule with no catch-all entry, inherit every defect below them.

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
| Web-to-Case submissions being lost | Check pending request count in Setup; clear the queue | 50,000 limit is a hard drop — no error surfaced to submitter |
| Escalation not firing on time | Attach a business hours record to escalation rule entries | Without business hours, clock runs 24/7; engine cadence is hourly |
| Case team members cannot access case | Verify case team roles are created; user is on the case team (not just the predefined team) | Roles must exist before teams; adding predefined team to case grants access, not just defining the predefined team |
| Entitlements not visible in Setup | Enable Entitlement Management feature flag | Feature must be enabled before any configuration is available |
| Entitlement templates on products not visible in Lightning | Use Flow or Apex to apply entitlements automatically | Template-on-product UI is Classic-only; Lightning requires automation |
| Routing behavior changed the moment a new rule was activated | Check whether activation displaced the incumbent rule in that slot | Only one assignment, one auto-response, and one escalation rule can be active for cases at a time; activating one deactivates the other |
| Business asks for a second active assignment rule per region or channel | Add rule *entries* to the one active rule, ordered specific-to-catch-all | A second active rule cannot exist; region and channel logic must live as entries |
| Reps should self-select the next case they can handle | Case queues | Queues are shared work lists reps pull from — no per-case owner assignment needed |
| Work must be pushed to a rep based on skills, availability, or workload | Omni-Channel (`admin/omni-channel-routing-setup`) | Assignment rules route to a queue, not to a person with capacity; Omni-Channel is the routing engine for that |
| Agents spend triage time filling Type/Priority/Reason on every case | Einstein Case Classification (`agentforce/agentforce-service-ai-setup`) | Predicts checkbox, picklist, and lookup field values from closed-case history, so routing criteria are populated before the assignment rule evaluates |
| Configuration was correct at go-live but SLA attainment is drifting | Establish a recurring review of rule entries, queue membership, and thresholds | Salesforce frames case management as ongoing tuning, not one-time setup |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. Confirm the inbound channel scope (Email-to-Case, Web-to-Case, or both) and whether On-Demand or Classic Email-to-Case is appropriate given the org's infrastructure.
2. Configure queues first — all routing depends on queues existing with the correct members and supported objects (Case must be in the queue's Supported Objects list). Confirm each queue has at least one active member who will actually pull from it; queues are shared work lists, not owners.
3. Inventory which rule currently occupies each of the three single-active slots (assignment, auto-response, escalation), then configure the case assignment rule with ordered rule entries targeting the appropriate queues. Activating your new rule deactivates the incumbent — plan that swap, do not discover it.
4. Configure the auto-response rule if customer acknowledgment emails are needed; verify that the assignment rule from step 3 will fire for the same case creation events. Remember there is only one active auto-response rule for cases — per-channel acknowledgments are entries within it.
5. Configure escalation rule entries with explicit business hours records, correct time thresholds, and re-route or notification actions; test in sandbox before activating in production.
6. If SLA tracking is required: enable Entitlement Management, create business hours, build the entitlement process with milestones, create entitlement records, and build the automation to attach entitlements to new cases.
7. Run the `scripts/check_case_management_setup.py` script against exported metadata, validate with the Review Checklist, then schedule the recurring review — Salesforce treats case management as continuously tuned, so rule entries, queue membership, and SLA thresholds need an owner and a cadence, not just a go-live date.

---

## Review Checklist

Run through these before marking case management configuration complete:

- [ ] Email-to-Case routing address is verified and thread ID handling tested end-to-end (reply threads into parent case, not new case)
- [ ] Web-to-Case pending request count is below 50,000; monitoring alert exists if available
- [ ] Active case assignment rule exists with at least one catch-all entry; no cases are falling to the default case owner unintentionally
- [ ] Auto-response rule entries have a valid email template; confirmed that assignment rule fires for the same creation events
- [ ] Escalation rule entries each have a business hours record explicitly attached; deactivation/reactivation risk communicated to stakeholders
- [ ] All queues referenced by assignment and escalation rules exist, have at least one active member, and have Case in their Supported Objects list
- [ ] Case team roles are created before predefined teams; predefined teams contain current active users
- [ ] If entitlements used: Entitlement Management is enabled, entitlement processes are active, business hours are attached to milestones, and automation applies entitlements to new cases
- [ ] Each of the three single-active slots is accounted for: the rule name occupying the assignment, auto-response, and escalation slot is recorded, and no design assumes a second concurrently active rule
- [ ] Rule activation swaps are scheduled and communicated; the displaced rule is named so rollback is a single activation
- [ ] Agent-facing surface is verified in the interface the agents actually use — Case Feed setup topics are documented under Salesforce Classic, so Lightning feed and action configuration was validated separately
- [ ] A named owner and a recurring cadence exist for reviewing rule entries, queue membership, and SLA thresholds after go-live

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Auto-response rule requires assignment rule to fire** — The auto-response rule is not independent. It fires only when the active case assignment rule fires for that case. If the assignment rule is inactive, has no matching entry, or was bypassed (e.g., API insert without `Sforce-Auto-Assign: true` header), the auto-response will not send. This is the most commonly misdiagnosed "auto-response not working" issue.
2. **Escalation reactivation triggers bulk escalations** — Deactivating an escalation rule pauses escalation time accumulation for open cases. When you reactivate the rule, the engine evaluates all open cases at once. Cases that have been open longer than the threshold since deactivation will escalate immediately in a single wave. In a large org, this can generate thousands of emails and re-assignments at once. Always test reactivation volume in a sandbox.
3. **Email-to-Case body truncation is silent** — Long customer emails are truncated at 32,000 characters without any notification to the agent or customer. Content after that limit is permanently lost. If customers send lengthy technical logs or attachments-as-text, critical information may be missing from the case body.
4. **Deleting a queue orphans owned cases** — If you delete a queue that currently owns open cases, those cases lose their owner. They will not appear in any queue view or any individual's My Cases view until manually reassigned. Enforce a case transfer protocol before queue deletion.
5. **Web-to-Case has no native validation** — The generated HTML form contains no JavaScript validation. Required-field enforcement, format checks (phone numbers, email formats), and spam prevention must all be implemented in the HTML form customization or via post-creation Flow/Apex. Without this, garbage data will enter your org.
6. **Entitlement template on product is Classic-only** — Associating an entitlement template with a product (so cases auto-receive an entitlement) is only configurable in Salesforce Classic. In Lightning Experience, there is no equivalent UI. Entitlements must be applied to cases via Flow, Process Builder, or Apex.
7. **Activating a rule silently deactivates the rule already in that slot** — Assignment, auto-response, and escalation rules each hold exactly one active rule for cases. Activating a new one displaces the incumbent with no confirmation prompt and no audit warning in the case handling flow. An admin who activates a "test" assignment rule in production has just replaced the production routing rule org-wide. There is no partial state and no merge; the swap is total and immediate.
8. **Case Feed setup documentation is scoped to Salesforce Classic** — The official Case Feed topics (enabling Case Feed actions and feed items, creating feed layouts, Case Feed and related lists) live under the Salesforce Classic branch of the help tree. Following those Setup steps and expecting the result to appear on a Lightning case record page produces no visible change. Configure the Lightning agent surface through the Lightning record page and quick actions instead.

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
| Rule slot inventory | The one active rule name in each of the assignment, auto-response, and escalation slots, plus the displaced predecessor for rollback |
| Review cadence | Named owner and interval for re-checking rule entries, queue membership, and SLA thresholds |

---

## Related Skills

- assignment-rules — use when the focus is on case assignment rule entry logic, criteria design, or API trigger behavior for case assignment specifically
- queues-and-public-groups — use when creating or troubleshooting the queues that assignment and escalation rules route cases into
- omni-channel-routing-setup — use when cases must be pushed to a rep based on skills, availability, or workload instead of pulled from a queue
- case-feed-send-email-action — use when configuring the Send Email quick action on the Lightning Case Feed agent surface
- agentforce-service-ai-setup — use when enabling Einstein Case Classification to autofill case fields before assignment rules evaluate them
