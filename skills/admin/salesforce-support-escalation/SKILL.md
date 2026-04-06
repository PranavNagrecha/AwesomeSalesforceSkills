---
name: salesforce-support-escalation
description: "Guide practitioners through opening, classifying, and escalating support cases with Salesforce Technical Support via the Help portal, including choosing the correct severity level, engaging Premier Success resources, using the Escalate to Technical Support Management path, and tracking incidents on the Trust site. NOT for configuring Salesforce Case Escalation Rules (declarative platform automation), Entitlement Management or SLA milestones, or building customer-facing support processes inside an org."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
triggers:
  - "how do I open a Sev1 case with Salesforce support when our org is down"
  - "case with Salesforce support is not getting attention and I need to escalate"
  - "what severity level should I assign to a Salesforce support ticket"
  - "how to escalate to technical support management when a P1 issue is unresolved"
  - "where do I check the status of a Salesforce incident or service degradation"
  - "does Premier Success plan change response time for critical issues"
  - "how to use the Trust site to monitor a Salesforce outage"
tags:
  - salesforce-support
  - severity-levels
  - premier-success
  - trust-site
  - incident-management
  - help-portal
inputs:
  - "Description of the business impact: what is broken, how many users are affected, which Salesforce product or feature"
  - "Current Support or Success Plan tier (Standard, Premier, Signature)"
  - "Org ID and environment type (production vs. sandbox)"
  - "Any existing case number if a ticket is already open"
  - "Steps to reproduce and error messages or screenshots"
outputs:
  - "Recommended severity level with rationale"
  - "Step-by-step procedure for opening or escalating the support case"
  - "Escalation path guidance if the case is stalled (Escalate button, Success Manager contact)"
  - "Trust site monitoring checklist for tracking incident status"
  - "Post-incident review template"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-06
---

# Salesforce Support Escalation

This skill activates when a practitioner or admin needs to engage Salesforce Technical Support — opening a new support case, choosing the correct severity, escalating a stalled case to management, or tracking an active incident through the Trust site. It covers the full support engagement lifecycle from initial ticket creation through resolution and post-incident review.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Confirm the Support Plan tier.** Response time commitments and escalation paths differ substantially between Standard, Premier, and Signature plans. Premier provides 1-hour response for Severity 2 issues 24/7; Standard does not. Check the org's plan before promising a resolution timeline to stakeholders.
- **Use a production org for Sev1/Sev2 cases.** Salesforce defines severity based on production business impact. A broken sandbox is almost never a Sev1. Conflating sandbox issues with production outages wastes escalation capital and can damage the relationship with your Technical Account Manager.
- **Org ID is mandatory.** Every support case requires the 15- or 18-character Org ID. Find it under Setup > Company Information. Without it, the intake form will not route correctly and response may be delayed.

---

## Core Concepts

### Severity Level Definitions

Salesforce uses four severity levels, defined by business impact, not technical severity. Choosing the wrong severity is the single most common mistake practitioners make.

| Level | Name | Definition |
|---|---|---|
| Sev1 | Business-Stopping | Production org is completely down or a core business process is completely inoperative for all users. Data loss or data corruption is occurring. No workaround exists. |
| Sev2 | Major Impairment | A major feature is broken in production and the impact is significant, but the org is not completely down. A temporary workaround may exist. |
| Sev3 | Minor Impairment | A feature is not working as expected but a workaround exists and business operations continue with minimal disruption. |
| Sev4 | Cosmetic/General | A low-impact issue: incorrect display, documentation request, general question, or enhancement enquiry. |

Source: Salesforce Knowledge Article 000382814 — Severity Level Descriptions.

**Severity drives everything downstream:** Premier SLA response times are 1 hour for Sev2 and 15 minutes for Sev1 (24/7). Sev3 and Sev4 responses are measured in hours or business days. Overstating severity to get faster attention is a known anti-pattern that erodes the working relationship with Salesforce support teams.

### Support Plan Tiers and Response Commitments

Three plan tiers govern support entitlement:

- **Standard** — Included with every Salesforce license. Online case submission only. No guaranteed response time. No 24/7 phone support.
- **Premier** — Paid add-on. 24/7 phone and online support for Sev1 and Sev2. 1-hour response target for Sev2. Dedicated onboarding and success resources.
- **Signature** — Highest tier. Dedicated Technical Account Manager (TAM). Proactive health checks. Fastest response commitments and named escalation contacts.

Knowing the org's plan tier before opening a Sev2 case at 2 AM determines whether a 1-hour callback is a realistic expectation or an unfounded promise to your stakeholders.

### The Escalation Path When a Case Is Stalled

Salesforce provides a defined escalation path when an open case is not making progress. The steps are:

1. **In-case Escalate button** — Every open case in the Help portal has an "Escalate to Technical Support Management" action. This sends a formal escalation notice to a Support Manager and adds a timestamp to the case audit trail (source: Salesforce Knowledge Article 000386150).
2. **Success Manager engagement** — Premier and Signature customers have an assigned Success Manager who can coordinate internally. Use them when a technical escalation has been raised but the case is still not moving after 2–4 hours on a Sev1.
3. **Technical Account Manager (TAM)** — Signature only. The TAM is a named Salesforce employee who can open doors across engineering, support, and product. They should be contacted directly for any Sev1 that threatens a business-critical deadline.

Do not skip steps. Contacting a TAM for a Sev4 cosmetic issue damages the escalation relationship and reduces responsiveness when a genuine Sev1 occurs.

### Known Issues and the Trust Site

Two resources complement the support case process:

- **Known Issues site** (`help.salesforce.com/s/issues`) — Salesforce's public database of known bugs. Search here before opening a Sev3 or Sev4 case. If a known issue already covers the problem, you can subscribe to updates rather than creating a duplicate case (source: Salesforce Knowledge Article 000386216).
- **Trust site** (`trust.salesforce.com`) — Real-time status of all Salesforce services, instances, and environments. When you suspect an outage, check the Trust site first. If the instance (e.g., NA135, EU15) shows "Service Degradation" or "Major Incident," Salesforce engineers are already aware. Opening a separate Sev1 case for an already-known incident is redundant and slows your case queue (source: Salesforce Knowledge Article 000387502).

Trust site incidents follow a documented communication cadence: Detection → Investigating → Identified → Monitoring → Resolved. The Incident Communications article (000389335) explains how and where Salesforce posts status updates for active incidents.

---

## Common Patterns

### Pattern: Opening a Sev1 Case for a Production Outage

**When to use:** The production org is inaccessible, all users are locked out, or a revenue-critical integration is completely down.

**How it works:**

1. Check `trust.salesforce.com` first — if the instance is already on a Major Incident, subscribe to updates and only open a case if you have unique diagnostic data.
2. Navigate to `help.salesforce.com` and click "Contact Support."
3. Select the affected product and choose severity Sev1.
4. In the case description, lead with: org ID, number of affected users, business impact (e.g., "$X/hour revenue loss" or "no orders can be processed"), exact error messages or HTTP status codes, and the time the issue started.
5. Check "Request phone callback" if available under your plan. Phone callbacks are initiated faster than async case routing for Sev1.
6. Post the case number in your internal incident channel immediately so stakeholders have a reference.

**Why it works:** A Sev1 with a clear business impact statement and org ID routes directly to an on-call engineer's queue. Vague descriptions ("it's not working") delay triage.

### Pattern: Escalating a Stalled Sev2 Case

**When to use:** A Sev2 case has been open for more than the SLA window without meaningful progress. You have Premier or Signature. Stakeholders are asking for an update.

**How it works:**

1. Open the case in the Help portal.
2. Add a case comment with a timeline of what has and has not been communicated.
3. Click the "Escalate to Technical Support Management" button. This is a formal action — it triggers an internal alert to a Support Manager. Note the timestamp for your records.
4. If no response within 1 hour (Sev2, Premier), contact your Success Manager directly.
5. Update your internal stakeholders with the case number, the escalation timestamp, and a realistic ETA based on the SLA commitment.

**Why it works:** The in-case escalation button creates a formal audit record and moves the case to a manager's queue, bypassing the standard agent rotation. Using it without first adding a clear comment reduces its effectiveness because the manager has no context.

### Pattern: Using the Known Issues Site to Avoid Duplicate Cases

**When to use:** A Sev3 or Sev4 issue appears suddenly across multiple users after a release. The behavior feels like a platform bug, not a config issue.

**How it works:**

1. Go to `help.salesforce.com/s/issues`.
2. Search by product area, feature name, or error message keyword.
3. If a matching known issue exists, click "This issue affects me" to register your org as impacted. Salesforce product and support teams use impact counts to prioritize fix delivery.
4. Subscribe to the known issue for email updates when the fix is released.
5. Do not open a separate support case for the same bug — it will be closed as a duplicate and delays cases that do need engineering attention.

**Why it works:** Salesforce tracks known issue subscriber counts as a signal for fix prioritization. Voting an issue up is more effective than a duplicate case.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Org is completely down, all users affected | Sev1 case via Help portal, phone callback if Premier | Sev1 triggers on-call engineer queue; phone is faster than async |
| Major feature broken but org is accessible | Sev2 case; use Premier phone line 24/7 if applicable | Sev2 gets 1-hour Premier response target; Sev1 is reserved for full outages |
| Broken but workaround exists | Sev3 case; check Known Issues first | Sev3 is appropriate; Known Issues may have a fix timeline already |
| Instance showing incidents on Trust site | Subscribe to Trust incident, open case only with unique data | Duplicate Sev1 cases for known incidents slow your own queue |
| Case stalled with no response | Use in-case Escalate button, then contact Success Manager | Formal escalation path creates audit trail and routes to manager |
| Sandbox-only issue | Sev3 at highest | Sandbox issues are never Sev1 by Salesforce's definition |
| Platform bug that appeared after a release | Search Known Issues site; vote if found | Voting is more effective than a duplicate case |
| Signature plan, critical deadline threatened | Contact TAM directly | TAM can coordinate across engineering and support simultaneously |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. **Assess business impact** — Determine how many users are affected, whether production is involved, and what business process is blocked. This assessment directly drives severity selection.
2. **Check the Trust site and Known Issues** — Before opening a case, verify whether Salesforce is already aware of an outage (`trust.salesforce.com`) or whether a known bug matches the symptoms (`help.salesforce.com/s/issues`). This step prevents duplicate case creation.
3. **Confirm the Support Plan tier** — Identify whether the org has Standard, Premier, or Signature so response expectations are set correctly before engaging stakeholders.
4. **Open the support case** — Navigate to `help.salesforce.com`, select Contact Support, choose the correct severity, and provide: org ID, product, user impact count, business impact statement, reproduction steps, and any relevant screenshots or error messages.
5. **Monitor and document** — Track case progress in the Help portal. Add case comments with new information as it becomes available. Post the case number in the internal incident channel.
6. **Escalate if stalled** — If the response SLA is exceeded with no meaningful update, use the in-case Escalate button, then engage the Success Manager or TAM according to plan tier.
7. **Post-incident review** — Once resolved, capture: root cause, Salesforce case number, time to resolution, lessons learned, and any preventive actions (e.g., Known Issue subscription, Trust site alert setup).

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Org ID confirmed and included in the case (15 or 18 characters from Setup > Company Information)
- [ ] Severity level chosen based on actual business impact, not perceived urgency
- [ ] Trust site checked for active incidents on the org's instance before opening a new case
- [ ] Known Issues site searched for matching bugs before opening a Sev3/Sev4 case
- [ ] Case description includes: affected users count, business impact statement, reproduction steps, error messages
- [ ] Support Plan tier confirmed so response time expectations are accurate
- [ ] Escalation path actioned if SLA window exceeded (Escalate button before Success Manager)
- [ ] Internal stakeholders informed with case number and realistic ETA

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Upgrading severity after case creation can reset queue position.** Changing a Sev3 to Sev1 after the case is submitted does not automatically move it to the top of the on-call queue in real time. The case is re-evaluated, but there may be a delay. Open at the correct severity from the start.

2. **Sandbox cases are not eligible for Sev1 by Salesforce's definition.** Even if your full development team is blocked on a sandbox issue, Salesforce's severity classification requires production business impact for Sev1. Assigning Sev1 to a sandbox case results in a downgrade by the support agent, which delays the response.

3. **The Escalate button is not available on every case status.** Once a case reaches "Pending Customer Input" or a similar closed/waiting state, the escalation button may be disabled. Always add a case comment confirming the issue persists before attempting to escalate.

4. **Trust site instance names do not always match what you see in your org URL.** The instance in your org URL (e.g., `na135.salesforce.com`) maps to a Trust site service entry, but hyperforce orgs and some newer instances use different nomenclature. Look up your exact instance under Setup > Company Information > Instance or use the Trust site's search.

5. **Known Issues votes are org-specific, not user-specific.** Only one person per org needs to click "This issue affects me." Multiple colleagues voting from the same org does not increase the impact count — only unique org IDs count. Coordinate internally so the right person registers the vote with the most detailed comment.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Support case with severity and description | Filed case in the Help portal with correct severity, org ID, impact statement, and reproduction steps |
| Escalation action record | Timestamp and notes confirming the in-case Escalate button was used and Success Manager was contacted |
| Trust site incident subscription | Subscription to the relevant Trust site service for email updates on active incidents |
| Post-incident review notes | Record of root cause, case number, time to resolution, and preventive actions |

---

## Related Skills

- escalation-rules — declarative platform automation for routing cases inside Salesforce; completely distinct from engaging Salesforce Technical Support
- case-management-setup — configuring the Case object, queues, and support processes within the org
