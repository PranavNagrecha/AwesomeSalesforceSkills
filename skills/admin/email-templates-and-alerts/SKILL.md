---
name: email-templates-and-alerts
description: "Use when designing, reviewing, or troubleshooting Salesforce email templates, email alerts, and declarative notification design. Triggers: 'Lightning Email Template', 'email alert', 'merge field', 'org-wide email', 'too many emails', 'mass email limit'. NOT for marketing automation or custom Apex email services."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - User Experience
  - Reliability
  - Operational Excellence
tags: ["email-alerts", "templates", "merge-fields", "notifications", "org-wide-email"]
triggers:
  - "email alert not sending"
  - "merge field showing blank in email"
  - "users getting duplicate notification emails"
  - "workflow email not firing on record save"
  - "org wide email address not working"
  - "email template not rendering correctly"
inputs: ["notification scenario", "audience", "sender requirements"]
outputs: ["email design guidance", "template governance findings", "notification recommendations"]
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-03-13
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

- **Template owns wording and branding**: keep business copy out of formula spaghetti.
- **Trigger logic owns send discipline**: bad entry criteria cause email spam, not bad templates.
- **Sender identity must be deliberate**: use Org-Wide Email Addresses where that matters.
- **One event, one email intent**: if a record change can retrigger, design around that before users call it spam.


## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. Gather context — confirm the org edition, relevant objects, and current configuration state
2. Review official sources — check the references in this skill's well-architected.md before making changes
3. Implement or advise — apply the patterns from Core Concepts and Common Patterns sections above
4. Validate — run the skill's checker script and verify against the Review Checklist below
5. Document — record any deviations from standard patterns and update the template if needed

---

## Salesforce-Specific Gotchas

- **Merge fields only work in the context you actually have**: wrong related record context means blank or misleading content.
- **Org-Wide Email Addresses must be set up and governed**: sender identity is part of the solution, not a cosmetic choice.
- **Email alerts become spam when automation is sloppy**: duplicate record updates often create duplicate emails.
- **Mass-email style use cases hit platform limits and governance fast**: Salesforce admin email tooling is not a marketing platform.
- **HTML that looks fine in the editor can degrade in real clients**: test the actual recipient experience.

## Proactive Triggers

Surface these WITHOUT being asked:
- **Multiple automations send emails from the same event** -> Flag for consolidation before users get duplicate notifications.
- **Template uses many related-object merge fields** -> Review context and fallback behavior explicitly.
- **No Org-Wide Email Address decision documented** -> Raise it before go-live.
- **Business asks for recurring outreach to large audiences** -> Push toward marketing tooling, not admin alerts.
- **Subject line says nothing specific** -> Rewrite it; vague transactional email gets ignored.

## Output Artifacts

| When you ask for... | You get... |
|---------------------|------------|
| Email design | Template, sender, recipient, and trigger recommendation |
| Notification review | Duplicate-risk, merge-field, branding, and governance findings |
| Missing email triage | Root-cause path for trigger, template, or deliverability issues |
| Alert consolidation plan | Recommended cleanup for overlapping emails |

## Related Skills

- **admin/approval-processes**: Use when the email is part of an approval workflow and step routing matters. NOT for general template governance.
- **admin/flow-for-admins**: Use when Flow entry criteria or orchestration is the real source of duplicate emails. NOT for template wording and sender design.
- **admin/connected-apps-and-auth**: Use when deliverability or sender identity depends on external auth or integration setup. NOT for day-to-day admin email alerts.
