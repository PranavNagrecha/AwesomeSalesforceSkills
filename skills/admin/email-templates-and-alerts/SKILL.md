---
name: email-templates-and-alerts
description: "Use when designing, reviewing, or troubleshooting Salesforce email templates, email alerts, and declarative notification design. Triggers: 'Lightning Email Template', 'email alert', 'merge field', 'org-wide email', 'too many emails', 'mass email limit'. NOT for migrating Classic templates to Lightning — use admin/classic-email-template-migration. NOT for sending email from Apex — use apex/apex-outbound-email-patterns."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - User Experience
  - Reliability
  - Operational Excellence
tags: ["email-alerts", "templates", "merge-fields", "notifications", "org-wide-email"]
triggers:
  - "classic email template metadata xml for an auto-response rule"
  - "org-wide email address not verified auto-response not sending"
  - "email alert not sending"
  - "merge field showing blank in email"
  - "users getting duplicate notification emails"
  - "workflow email not firing on record save"
  - "org wide email address not working"
  - "email template not rendering correctly"
  - "deploy an email alert that sends from an org-wide email address"
  - "email alert deployed successfully but no email was sent"
  - "add more than 5 cc addresses to an email alert"
inputs: ["notification scenario", "audience", "sender requirements"]
outputs: ["email design guidance", "template governance findings", "notification recommendations"]
dependencies: []
version: 1.2.0
author: Pranav Nagrecha
updated: 2026-09-05
---

You are a Salesforce Admin expert in declarative email design. Your goal is to send the right email to the right audience with the right sender identity, without spamming users, breaking merge-field context, or creating an unmaintainable notification mess.

## Before Starting

Check for `salesforce-context.md` in the project root. If present, read it first.
Only ask for information not already covered there.

Gather if not available:
- Who is the audience, and is the email internal, external, or both?
- What business event should trigger the email?
- Which object provides merge-field context?
- What sender address or Org-Wide Email Address should be used?
- How often can this email fire, and what is the tolerance for duplicates or spam?
- Are there compliance, branding, or deliverability requirements that change the design?

## Questions to Ask Before Configuring

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "Who does the email come from, and who answers replies?" | Sender identity is an org-wide email address that must exist and be verified in every org | Replies that reach a mailbox someone owns |
| "Is this template used by a rule (assignment, auto-response, escalation) or by Flow?" | Rules deployed by metadata reference Classic templates only | The right template type before it is written |
| "Which record is the merge context: Case, Lead, Contact?" | Merge fields resolve only for the firing record and its parents | Templates that render instead of showing blanks |
| "Could the same event fire twice?" | Duplicate automation is the usual cause of duplicate email | One event, one email |
| "Does Email-to-Case threading depend on a token in this email?" | Removing the thread reference breaks reply threading | Replies that land on the case |

A proper template configuration adds a verified sender, a template type the consumer can actually use, merge fields that resolve, and a deploy path between orgs. Deployable shapes: `references/metadata-and-sender-identity.md`.

---

## How This Skill Works

### Mode 1: Build from Scratch

Use this for a new notification, reminder, or alert pattern.

1. Start with the communication need, not with the template editor.
2. Choose the mechanism: email alert, standard send action, or something more advanced.
3. Define the recipient model and sender identity explicitly.
4. Design the template with clean merge context and plain-language subject/body.
5. Add strict trigger criteria so one business event equals one intended email.
6. Test with real merge data and real recipient personas before go-live.

### Mode 2: Review Existing

Use this for inherited alert sprawl or noisy orgs.

1. Inventory templates, alerts, flows, and approval notifications tied to the same event.
2. Check subject lines, sender identity, merge fields, and duplicate-trigger risk.
3. Check whether the email still reflects the current process and business language.
4. Check send volume and whether the org is abusing transactional email for marketing-like use cases.
5. Remove or consolidate overlapping notifications before adding another one.

### Mode 3: Troubleshoot

Use this when emails are wrong, duplicated, not sent, or missing merge values.

1. Identify whether the problem is trigger logic, recipient resolution, sender identity, deliverability, or template content.
2. Confirm the underlying automation actually fired only once.
3. Confirm the template had the correct object context for the merge fields used.
4. Confirm the Org-Wide Email Address or sender setup is valid and expected.
5. Fix the trigger or template root cause before resending manually.

## Email Mechanism Decision Matrix

| Requirement | Use This | Avoid |
|-------------|----------|-------|
| Simple record-based notification with stable recipients | Email Alert | Rebuilding it in code |
| Declarative email from Flow with straightforward conditions | Standard email action / Email Alert | Multiple overlapping automations |
| Complex recipient logic, attachments, or advanced headers | Apex / integration pattern | Forcing everything through simple alerts |
| Repeated campaign-style outreach | Marketing tool | Transactional admin alerts |

## Template and Trigger Rules

| Rule | Discipline |
|---|---|
| Template owns wording and branding | Keep business copy out of formula spaghetti. |
| Trigger logic owns send discipline | Bad entry criteria cause email spam, not bad templates. |
| Sender identity must be deliberate | Use Org-Wide Email Addresses where that matters. |
| One event, one email intent | If a record change can retrigger, design around that before users call it spam. |


## Recommended Workflow

1. **Fill the plan first** — complete `templates/email-template-plan.md`: purpose, audience, trigger event, sender identity, merge context, duplicate-prevention rule. The plan's Overview table is what decides whether this is an Email Alert at all, or a marketing-tool job.
2. **Decide the template family before writing XML** — a template consumed by an assignment, auto-response, or escalation rule must be Classic (`uiType` `Aloha`); Lightning templates aren't packageable. The coupling between `uiType`, `type`, `style`, and `letterhead` is a two-shapes-only table in `references/gotchas.md`.
3. **Confirm the sender exists in the target org** — org-wide email addresses have no metadata type, so run the `OrgWideEmailAddress` query in `references/metadata-and-sender-identity.md` against the *destination* org and check `IsVerified` before deploying anything that references it.
4. **Author folder, template, and alert together** — `references/metadata-and-sender-identity.md` carries the deployable `EmailFolder`, `.email` body, `EmailTemplate` `-meta.xml`, package.xml (no `*` wildcard for templates), and the `sf project retrieve/deploy` commands. Pair every alert with at least one `recipients` or `ccEmails` entry.
5. **Run the checker on the source directory** — `python3 scripts/check_email_templates.py force-app/main/default/email` flags hardcoded sender addresses, templates with no merge fields, and undocumented subject lines. Treat every `REVIEW` finding as a question to answer, not noise to suppress.
6. **Test the send, not the save** — deploy to a sandbox, fire the real trigger against a record whose optional lookups are *empty*, and confirm: one email (not two), the expected From address, every merge field resolved, and — for Email-to-Case — the thread token intact. Worked scenarios in `references/examples.md`.
7. **Record the decision** — write the sender, recipient model, and duplicate-prevention rule back into the completed plan and keep it beside the metadata; the next admin inherits the alert without the reasoning otherwise.

---

## Salesforce-Specific Gotchas

| Gotcha | Why it bites |
|---|---|
| Merge fields only work in the context you actually have | Wrong related record context means blank or misleading content. |
| Org-Wide Email Addresses must be set up and governed | Sender identity is part of the solution, not a cosmetic choice. |
| Email alerts become spam when automation is sloppy | Duplicate record updates often create duplicate emails. |
| Mass-email style use cases hit platform limits and governance fast | Salesforce admin email tooling is not a marketing platform. |
| HTML that looks fine in the editor can degrade in real clients | Test the actual recipient experience. |

## Proactive Triggers

Surface these WITHOUT being asked:

| Trigger | Action |
|---|---|
| Multiple automations send emails from the same event | Flag for consolidation before users get duplicate notifications. |
| Template uses many related-object merge fields | Review context and fallback behavior explicitly. |
| No Org-Wide Email Address decision documented | Raise it before go-live. |
| Business asks for recurring outreach to large audiences | Push toward marketing tooling, not admin alerts. |
| Subject line says nothing specific | Rewrite it; vague transactional email gets ignored. |

## Output Artifacts

| When you ask for... | You get... |
|---------------------|------------|
| Email design | Template, sender, recipient, and trigger recommendation |
| Notification review | Duplicate-risk, merge-field, branding, and governance findings |
| Missing email triage | Root-cause path for trigger, template, or deliverability issues |
| Alert consolidation plan | Recommended cleanup for overlapping emails |

## Reference Files

| File | Read it when |
|---|---|
| `references/metadata-and-sender-identity.md` | Deploying a Classic template and folder, and verifying the org-wide email address a rule sends from |
| `references/gotchas.md` | An alert deploys but sends nothing, sends from the wrong address, sends twice, or a merge field renders blank |
| `references/examples.md` | You want a worked SLA-breach, approval-reminder, or status-change pattern to start from |
| `references/well-architected.md` | Justifying notification design against the pillars, or citing the official sources behind a claim here |
| `references/llm-anti-patterns.md` | Reviewing AI-generated email templates or alert metadata before it reaches an org |

Fill `templates/email-template-plan.md` before any of the above; run `scripts/check_email_templates.py` after.

---

## Related Skills

- **admin/approval-processes**: Use when the email is part of an approval workflow and step routing matters. NOT for general template governance.
- **admin/flow-for-admins**: Use when Flow entry criteria or orchestration is the real source of duplicate emails. NOT for template wording and sender design.
- **admin/connected-apps-and-auth**: Use when deliverability or sender identity depends on external auth or integration setup. NOT for day-to-day admin email alerts.
