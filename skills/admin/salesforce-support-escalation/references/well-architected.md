# Well-Architected Notes — Salesforce Support Escalation

## Relevant Pillars

### Reliability

Support escalation is fundamentally a reliability practice. The patterns in this skill enable organizations to restore service quickly when Salesforce platform issues occur, minimize mean time to resolution (MTTR), and maintain service continuity commitments to end users. Choosing the correct severity level and following the documented escalation path are the two highest-leverage reliability actions available when a platform incident occurs.

Reliably resolving support escalations requires preparation before an incident: knowing the Support Plan tier, keeping the Org ID documented, and designating an on-call contact who can engage Salesforce support 24/7 without requiring approval chains during a Sev1.

### Operational Excellence

The support engagement lifecycle — from initial case filing to post-incident review — is an operational process. The Well-Architected principle of operational excellence requires that this process be documented, practiced, and improved over time.

Key operational excellence practices in this skill:
- Maintaining a pre-documented "support runbook" so any admin can open a Sev1 case with the right information without decision paralysis during an outage
- Running post-incident reviews after every Sev1 or significant Sev2 to capture lessons learned and improve future response
- Subscribing to Trust site notifications proactively so incidents are detected through Salesforce's own communications, not discovered by end users
- Registering on Known Issues for recurring problems to track platform fix progress

### Security

Support engagement has a security dimension: sharing org-level diagnostic data with Salesforce support often involves granting login access to a production org. The Salesforce support team may request a "Grant Login Access" authorization (Setup > My Personal Information > Grant Login Access). This access should be:
- Time-limited (1 hour or 1 day, not indefinite)
- Logged in the org's internal change management system
- Revoked immediately after the support session ends

Do not share credentials or grant full admin access via alternative channels. The standard Grant Login Access mechanism in Setup is the appropriate, auditable path.

---

## Architectural Tradeoffs

**Speed vs. information quality at case opening:** Filing a case with minimal information gets it into the queue immediately but typically triggers a back-and-forth with the support engineer that delays resolution. Taking 5 minutes to gather org ID, user impact count, error messages, and reproduction steps before opening the case results in faster triage. The tradeoff is front-loaded effort for reduced total resolution time.

**Single escalation path vs. parallel escalation:** Using the in-case Escalate button first (then Success Manager, then TAM) preserves the escalation relationship for genuine emergencies. Jumping immediately to the TAM for a Sev3 issue depletes that channel. However, for genuine Sev1 issues threatening business continuity, parallel engagement (Escalate button + Success Manager call + TAM message simultaneously) may be appropriate. The tradeoff is relationship capital against speed of resolution.

**Standard vs. Premier plan:** Standard support provides no guaranteed response time. Organizations running business-critical processes on Salesforce without a Premier or Signature plan are accepting the risk that a Sev2 production issue may not receive a response within any defined window. This is an architectural reliability decision, not a support process decision.

---

## Anti-Patterns

1. **Severity inflation as a strategy** — Consistently filing Sev1 or Sev2 cases for Sev3/Sev4 issues in hopes of faster response. This erodes the organization's relationship with the Salesforce support team, causes support engineers to approach new cases from the organization with reduced urgency, and can result in a formal notation on the account. The correct strategy is accurate severity + detailed impact description + timely escalation if the SLA is breached.

2. **Not checking Trust site and Known Issues before opening a case** — Filing cases for issues already on the Trust site or already tracked as known bugs adds noise to the support queue and does not accelerate resolution. For Trust site incidents, Salesforce engineers are already engaged. For known bugs, the fix delivery is governed by the engineering team, not the support team — a duplicate case does not change the fix priority unless it adds unique diagnostic data.

3. **No post-incident review process** — Organizations that resolve a Sev1 incident and move on without capturing root cause, timeline, and preventive actions are more likely to experience the same incident again or respond more slowly the next time. Post-incident review artifacts also serve as evidence when negotiating Success Plan upgrades or raising systemic reliability concerns with a TAM.

---

## Official Sources Used

- Salesforce Help: Severity Level Descriptions — https://help.salesforce.com/s/articleView?id=000382814
- Salesforce Help: Escalate Case to Technical Support Management — https://help.salesforce.com/s/articleView?id=000386150
- Salesforce Help: Known Issues Site — https://help.salesforce.com/s/articleView?id=000386216
- Salesforce Help: Trust Site Overview — https://help.salesforce.com/s/articleView?id=000387502
- Salesforce Help: Incident Trust Communications — https://help.salesforce.com/s/articleView?id=000389335
- Salesforce Trust Status User Guide — https://trust.salesforce.com
- Salesforce Success Plans — https://www.salesforce.com/services/success-plans/overview/
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
