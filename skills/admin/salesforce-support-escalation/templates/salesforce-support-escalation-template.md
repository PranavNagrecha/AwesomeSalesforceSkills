# Salesforce Support Escalation — Work Template

Use this template when opening or escalating a Salesforce Technical Support case.

---

## Scope

**Skill:** `salesforce-support-escalation`

**Request summary:** (describe what is broken and what the business is asking for)

---

## Pre-Flight Context

Complete this before opening or escalating any case.

| Item | Value |
|---|---|
| Org ID (15 or 18 char) | |
| Instance (from Setup > Company Information) | |
| Environment | Production / Sandbox / Scratch |
| Support Plan tier | Standard / Premier / Signature |
| Number of affected users | |
| Time issue first observed | |
| Has issue occurred before? | Yes / No |

---

## Trust Site and Known Issues Check

- [ ] Checked `trust.salesforce.com` for active incidents on this instance
  - Result: _No incidents / Incident ID: ____________ Status: __________
- [ ] Searched `help.salesforce.com/s/issues` for matching known bug
  - Result: _No match / Known Issue W-__________ Status: ______________
  - If match found: registered "This issue affects me" on (date): ________

---

## Severity Assessment

**Salesforce Severity Definitions:**

| Level | When to Use |
|---|---|
| Sev1 | Production completely down OR core business process inoperative for all users. No workaround. |
| Sev2 | Major feature broken in production. Significant impact. Temporary workaround may exist. |
| Sev3 | Feature not working as expected. Workaround exists. Business continues with minimal disruption. |
| Sev4 | Cosmetic, documentation request, general question, or enhancement. |

**Selected severity:** Sev___

**Rationale:** (explain why this severity applies based on the actual business impact)

---

## Case Description (paste into Help portal)

```
Org ID: [paste 18-char Org ID]
Instance: [e.g., NA135, EU15, or Hyperforce region]
Support Plan: [Standard / Premier / Signature]
Severity: [Sev1 / Sev2 / Sev3 / Sev4]

IMPACT
Number of affected users:
Business process affected:
Revenue or operational impact (if applicable):
Time issue started:

SYMPTOMS
What the user sees:
Error message or HTTP status:
Frequency: [Always / Intermittent / Under specific conditions]

STEPS TO REPRODUCE
1.
2.
3.

ENVIRONMENT
Browser / client:
API version (if applicable):
Recent changes (deployment, config, release):

WORKAROUND TRIED
[Yes / No] — describe:
```

---

## Escalation Log

Use this section if the case is not progressing within the SLA window.

| Timestamp | Action Taken | By Whom | Notes |
|---|---|---|---|
| | Case opened | | |
| | In-case Escalate button used | | SLA breach at: |
| | Success Manager contacted | | |
| | TAM contacted (Signature only) | | |
| | Premier phone support called | | |
| | Engineer assigned | | |
| | Root cause identified | | |
| | Case resolved | | |

**Premier SLA reference:**
- Sev1: 15-minute initial response
- Sev2: 1-hour initial response
- (Response = first engineer contact, not resolution)

---

## Grant Login Access (if required by support)

- [ ] Access granted via: Setup > My Personal Information > Grant Login Access
- Duration set to: ___ hours / days (minimum needed)
- Logged in change management: Yes / No — Reference: ____________
- Access revoked after session: Yes / No — Date/time revoked: ____________

---

## Stakeholder Communication

**Internal incident channel:** (Slack/Teams channel name)

**Case number:** (fill when case is opened)

**Status update template:**
```
[Time] — Case [number] update
Status: [In Progress / Escalated / Engineer assigned / Resolved]
Last Salesforce action: [describe]
Next update expected: [time]
ETA: [known / unknown]
```

---

## Post-Incident Review

Complete this within 48 hours of case resolution.

| Field | Value |
|---|---|
| Case number | |
| Date opened | |
| Date resolved | |
| Total time to resolution | |
| Severity | |
| Root cause | |
| Was it a known issue? | Yes (W-_______) / No |
| Was it on Trust site during incident? | Yes / No |

**What went well:**

**What could be improved:**

**Preventive actions:**

- [ ] Subscribed to Trust site alerts for this instance
- [ ] Registered on Known Issue (if applicable)
- [ ] Updated internal runbook / incident response process
- [ ] Considered Support Plan upgrade (if response time was inadequate)

---

## Notes

(Record any deviations from the standard pattern, additional context, or follow-up items.)
