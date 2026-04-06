# LLM Anti-Patterns — Salesforce Support Escalation

Common mistakes AI coding assistants make when generating or advising on Salesforce Support Escalation.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Conflating Salesforce Case Escalation Rules with Salesforce Support Escalation

**What the LLM generates:** When asked "how do I escalate a Salesforce issue," the LLM describes how to configure Case Escalation Rules in Setup — defining time-based entries, business hours, and escalation actions — instead of explaining how to engage Salesforce Technical Support for a platform problem.

**Why it happens:** Both topics contain the word "escalation" and both involve "cases." Training data frequently co-locates Salesforce admin configuration content (escalation rules) with general support escalation advice. The LLM defaults to the more technically detailed, codeable topic.

**Correct pattern:**

```
When the user says "escalate" in the context of a Salesforce issue they are experiencing
(org is down, feature is broken), they mean:
  → Engaging Salesforce Technical Support via help.salesforce.com
  → Using the in-case Escalate button on an open support case
  → Contacting a Success Manager or TAM

When the user says "escalate" in the context of building support automation in their org,
they mean:
  → Setup > Escalation Rules (declarative time-based case routing)

Disambiguate before answering: "Are you experiencing a Salesforce platform issue and
need to contact Salesforce support, or are you setting up automated escalation logic
inside your own org?"
```

**Detection hint:** Check whether the response contains words like "rule entries," "business hours record," or "escalation actions" — these belong to the declarative rules skill, not support engagement.

---

## Anti-Pattern 2: Stating That Severity Guarantees Resolution Time

**What the LLM generates:** "If you open a Sev1 case with Premier support, Salesforce will resolve your issue within 1 hour."

**Why it happens:** The LLM conflates response time SLA with resolution time SLA. Premier's published commitments cover initial response (first engineer contact), not resolution. The LLM generalizes "1 hour" from the response SLA to a resolution promise.

**Correct pattern:**

```
Premier Sev1: 15-minute initial response target (first engineer contact)
Premier Sev2: 1-hour initial response target (first engineer contact)

Resolution time is NOT guaranteed by plan tier for complex platform issues.
The support team works continuously on Sev1 issues, but resolution depends on
root cause complexity.

When setting stakeholder expectations, always say:
"We expect to hear from a Salesforce engineer within [SLA window]. Resolution time
depends on the nature of the issue."
```

**Detection hint:** Look for phrases like "resolve within," "fix within," or "resolved in X hours" used as a guarantee tied to a support plan tier. These are false promises.

---

## Anti-Pattern 3: Advising to Open Multiple Cases for the Same Incident

**What the LLM generates:** "To get faster attention during an outage, have everyone on your team open a Sev1 case so Salesforce sees how many people are affected."

**Why it happens:** The LLM reasons that more cases = more visibility. This logic applies to some support systems, but Salesforce support triages by org, and duplicate cases for the same incident create queue congestion that slows triage for all cases including the org's own.

**Correct pattern:**

```
During an incident:
1. Designate ONE person to open and own the support case.
2. Post the case number in a shared internal channel immediately.
3. All other team members add their observations as COMMENTS on the same case.
4. Use the "This issue affects me" vote on the Trust site incident page if available.

Multiple cases = slower triage, not faster.
```

**Detection hint:** Any suggestion to have "multiple team members open cases" or to "open additional cases to increase priority" is this anti-pattern.

---

## Anti-Pattern 4: Treating the Trust Site as Confirmation That No Action Is Needed

**What the LLM generates:** "The Trust site shows 'Investigating' for your instance, so Salesforce is already working on it. You don't need to open a case."

**Why it happens:** The LLM correctly identifies that the Trust site shows Salesforce is aware, but incorrectly concludes no further action is needed. Trust incidents track infrastructure-level issues. Org-specific symptoms, custom code interactions, or unique configuration factors may require a separate case.

**Correct pattern:**

```
When Trust site shows an active incident for your instance:
1. Subscribe to the incident for email updates.
2. Still open ONE case if:
   - Your symptoms include org-specific factors (custom code, integrations)
   - You need a formal record linked to your org for SLA credit or post-incident review
   - Your org's behavior differs from the general incident description

Do NOT open a case solely because the Trust site says "Investigating" and you
want a faster update — the incident team is already engaged.
```

**Detection hint:** Advice that unconditionally says "don't open a case, just wait for the Trust site to update" is this anti-pattern.

---

## Anti-Pattern 5: Recommending Severity 1 for Sandbox Issues

**What the LLM generates:** "Your entire development team is blocked on this sandbox deployment issue. That sounds like a Sev1 business impact — open a Sev1 case."

**Why it happens:** The LLM correctly identifies that the team is blocked and applies general "all users blocked = highest severity" logic. It fails to apply Salesforce's specific definition that Sev1 requires production org impact.

**Correct pattern:**

```
Salesforce severity is defined by PRODUCTION BUSINESS IMPACT:
- Sev1 = production org completely down OR critical business process inoperative in production
- Sandbox issues = Sev3 at highest, regardless of developer impact

For a blocked sandbox with a production timeline at risk, file Sev3 and state the
context explicitly:
"This is a sandbox issue. However, we have a production deployment window in 48 hours
that this issue will block if unresolved. We are requesting expedited handling given
the timeline."

This keeps the case in the correct queue while communicating urgency accurately.
```

**Detection hint:** Any advice to file Sev1 that does not involve a production org being completely inoperative or experiencing data loss is likely this anti-pattern.

---

## Anti-Pattern 6: Recommending "Grant Login Access" Without Time Limits or Logging

**What the LLM generates:** "Go to Setup > Grant Login Access and give Salesforce Support full admin access so they can investigate."

**Why it happens:** Grant Login Access is the correct mechanism, but the LLM omits the security hygiene requirements: time limiting the access, logging it in the change management system, and revoking it after the session.

**Correct pattern:**

```
Grant Login Access best practices:
1. Set the access duration to the minimum needed: 1 hour for a diagnostic session,
   1 day for a complex investigation. Never leave it open indefinitely.
2. Log the grant in your internal change management system:
   - Who granted it
   - Case number
   - Date and time
   - Access duration
3. After the support session, go back to Setup > Grant Login Access and revoke it.
4. Do not grant access via any other mechanism (e.g., sharing credentials directly).
   The standard Setup path is auditable; other paths are not.
```

**Detection hint:** Any recommendation to grant login access that omits duration limits and post-session revocation is this anti-pattern.
