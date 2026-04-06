# Customer Effort Scoring — Work Template

Use this template when designing or reviewing a CX measurement strategy for a Salesforce org.

## Scope

**Skill:** `customer-effort-scoring`

**Request summary:** (fill in what the user asked for)

---

## Context Gathered

Answer each question before selecting a metric or configuring any survey.

- **Primary business question:** (e.g., "Why are customers churning despite high CSAT?", "How much friction do customers experience in our support process?")
- **Service org type:** B2B / B2C / Mixed
- **Primary support channels:** (e.g., web-to-case, email-to-case, phone-to-case, Agentforce bot)
- **Monthly case closure volume:** (number — used to size license tier)
- **Existing CX data:** (any current CSAT/NPS/CES program? What is the response rate?)
- **Feedback Management license tier confirmed:** Starter / Growth / Enterprise / Not yet licensed
- **CRM Analytics licensed?** Yes / No (affects reporting pattern options)

---

## Metric Selection

| Metric | Business Question It Answers | Use This When |
|---|---|---|
| CSAT (1–5) | Was the customer satisfied with this interaction? | High-volume transactional support; benchmarking interaction quality |
| NPS (0–10) | How loyal is this customer and will they recommend us? | Periodic relationship health; executive reporting; churn prediction at account level |
| CES (1–7) | How easy was it for the customer to resolve their issue? | Post-support interaction; re-contact reduction; friction diagnosis |

**Selected primary metric for this engagement:** [ ] CSAT  [ ] NPS  [ ] CES

**Rationale:** (1–2 sentences explaining why this metric answers the primary business question)

---

## Survey Configuration Decisions

### Trigger Timing

| Metric | Recommended Trigger | Max Delay for Valid Data |
|---|---|---|
| CES | 15 minutes after case closure (Scheduled Path) | 60 minutes post-closure |
| CSAT | 15–30 minutes after case closure | 4 hours post-closure |
| NPS | Periodic (quarterly), NOT per-interaction | N/A — not time-sensitive to interaction |

**Configured trigger:** Record-Triggered Flow / Scheduled-Triggered Flow

**Scheduled Path delay:** _______ minutes (must be ≥ 15 for CES/CSAT)

### License Tier Sizing

| Field | Value |
|---|---|
| Monthly case closures | |
| Target survey send rate (%) | |
| Expected monthly response volume | |
| Current license tier cap | |
| Headroom (cap − expected responses) | |
| Upgrade needed? | Yes / No |

### Flow Guards (Required Before Go-Live)

- [ ] Decision: `Contact.HasOptedOutOfEmail = false` before creating `SurveyInvitation`
- [ ] Decision: `Case.ContactId != null` before looking up Contact
- [ ] Decision: `Contact.Email != null` before creating `SurveyInvitation`
- [ ] Scheduled Path delay ≥ 15 minutes (not 0 or immediate)
- [ ] Re-send suppression: custom date field on Contact populated after each send

---

## Case-Level Reporting Linkage

The `SurveyResponse` object has no native `CaseId` field. To report CES/CSAT at the case level:

- [ ] Custom Lookup field created: `SurveyInvitation.Related_Case__c` (Lookup to Case)
- [ ] Flow populates `Related_Case__c` with the triggering Case Id when creating `SurveyInvitation`
- [ ] Custom Report Type created: Case → SurveyInvitation → SurveyResponse
- [ ] Dashboard or report owner defined

---

## Low-Score Escalation Path

Define what happens when a customer returns a low CES or CSAT score.

| Threshold | Action | Owner |
|---|---|---|
| CES ≤ 2 (out of 7) | | |
| CSAT = 1 (out of 5) | | |
| NPS Detractor (0–6) | | |

Examples: create a follow-up Task on the Case, reopen the Case, send alert email to team lead.

---

## Governance and Ownership

- **Survey program owner (admin):**
- **Metric reporting owner (analyst/manager):**
- **Re-send suppression policy documented?** Yes / No
- **Response rate target:** _______ % (recommended: ≥ 15% for email-based)
- **Review cadence:** Monthly / Quarterly

---

## Review Checklist

Copy from SKILL.md and tick as complete:

- [ ] Business question documented and maps to selected metric
- [ ] Feedback Management license tier confirmed; monthly cap exceeds projected volume
- [ ] Survey trigger timing validated (CES: ≤60 min; NPS: 90-day suppression)
- [ ] `HasOptedOutOfEmail` check in Flow before `SurveyInvitation` creation
- [ ] Null-Contact guard present for cases without a linked Contact
- [ ] Response-to-case linkage field set (custom lookup on `SurveyInvitation`)
- [ ] Reporting model defined: report type, dashboard, and owner
- [ ] Low-score escalation path documented
- [ ] Re-send suppression policy documented per survey type

---

## Notes

(Record any deviations from the standard pattern and the rationale.)
