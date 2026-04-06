---
name: customer-effort-scoring
description: "Designing a customer experience measurement strategy using CSAT, NPS, and CES metrics in Salesforce Feedback Management: metric selection, survey timing, Feedback Management license requirements, Flow-triggered survey delivery, and CX KPI integration into Service Analytics dashboards. Use when choosing which CX metric to deploy, defining survey timing rules, or connecting survey response data to operational KPIs. NOT for building or configuring the technical survey objects, flows, or email templates (use admin/salesforce-surveys for that). NOT for custom programmatic survey delivery via API."
category: architect
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
  - User Experience
triggers:
  - "which customer satisfaction metric should we use — CSAT, NPS, or CES — and when"
  - "we want to measure how easy it is for customers to resolve support issues — how do we set that up"
  - "our CSAT scores are good but customer churn is still high — what other CX metrics should we be tracking"
  - "how soon after a case closes should we send a satisfaction survey to get accurate feedback"
  - "how do I connect survey response data to our service performance dashboards"
tags:
  - customer-effort-scoring
  - CSAT
  - NPS
  - CES
  - feedback-management
  - survey-strategy
  - cx-metrics
  - service-kpis
inputs:
  - Service org type (B2B, B2C, or mixed) and primary support channels
  - Current or target Feedback Management license tier (Starter, Growth, or Enterprise)
  - Use cases driving measurement need (relationship health vs. transactional quality vs. effort)
  - Existing CRM reporting structure and dashboards
  - Expected survey volume per month (informs license tier selection)
outputs:
  - CX metric selection recommendation (CSAT vs. NPS vs. CES) with rationale
  - Survey timing and trigger configuration guidance
  - Feedback Management license tier recommendation
  - KPI integration map connecting survey scores to Service Analytics or CRM Analytics dashboards
  - Review checklist for measurement strategy completeness
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-06
---

# Customer Effort Scoring

This skill activates when an architect or admin needs to design a CX measurement strategy using Salesforce Feedback Management — selecting the right metric (CSAT, NPS, or CES), defining survey timing and delivery rules, choosing the appropriate license tier, and connecting response data to service KPIs. It focuses on measurement strategy decisions; for the technical build of survey objects and flows, use the `admin/salesforce-surveys` skill.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Confirm Feedback Management license tier.** Salesforce Surveys is available in most editions, but advanced features (branded surveys, response analytics, merge fields, automated invitations via Flow) require a Feedback Management license — Starter, Growth, or Enterprise. The tier also sets a monthly survey response cap. Without the correct license, Flow-triggered invitations and response reporting will be blocked or severely limited.
- **Understand the measurement intent before choosing a metric.** The most common wrong assumption is that all three metrics (CSAT, NPS, CES) are interchangeable and any one will do. Each measures a fundamentally different thing: CSAT measures satisfaction at a moment in time, NPS measures relationship loyalty and likelihood to recommend, and CES measures transactional friction. Deploying the wrong metric produces data that cannot answer the business question you care about.
- **Survey fatigue is a real constraint.** Sending all three surveys after every interaction will destroy response rates within weeks. Most orgs should pick one primary metric per interaction type and rotate or combine sparingly.

---

## Core Concepts

### CSAT — Customer Satisfaction Score

CSAT uses a 1–5 rating scale (sometimes 1–10, but 1–5 is the Salesforce Surveys native scale for the Rating question type). It measures satisfaction with a specific, discrete interaction — a resolved case, a completed service appointment, or a recently handled chat. CSAT is a lagging indicator of interaction quality and is best suited to high-volume transactional support where you need a volume-adjusted benchmark.

CSAT is calculated as: (number of satisfied responses — typically 4s and 5s — divided by total responses) × 100. The threshold for "satisfied" is org-configurable but 4-5 on a 5-point scale is the industry standard.

Because CSAT measures a moment in time, it has low predictive power for long-term loyalty or churn. An org can maintain high CSAT while still losing customers who find the overall relationship low-value.

### NPS — Net Promoter Score

NPS uses a 0–10 scale with a single question: "How likely are you to recommend us to a friend or colleague?" Salesforce Surveys natively supports the NPS question type, which automatically buckets responses into the three fixed ranges: **Detractor** (0–6), **Passive** (7–8), and **Promoter** (9–10). These bucket boundaries are hardcoded in the platform and cannot be customized — any attempt to remap them requires custom reporting outside the native NPS question type.

NPS is calculated as: (% Promoters) − (% Detractors). Scores range from −100 to +100. NPS measures relationship health and loyalty, not transactional satisfaction. It is best used as a periodic relationship pulse (quarterly or post-onboarding) rather than after every interaction — high-frequency NPS surveys depress response rates and inflate negative responses because customers see the survey as friction itself.

### CES — Customer Effort Score

CES measures how easy it was for a customer to resolve their issue. It typically uses a 1–7 scale with a question such as "The company made it easy for me to handle my issue" (strongly agree to strongly disagree). Salesforce Surveys supports CES via the standard Rating question type configured with a 7-point scale and appropriate label text — there is no dedicated CES question type in the platform.

CES is the strongest predictor of customer disloyalty (churn and reduced repurchase intent) among the three metrics, according to the original CEB/Gartner research that introduced the concept. A customer who found their issue hard to resolve is significantly more likely to churn, even if they rate their satisfaction as moderate. CES is most valuable for high-effort interactions: complex technical issues, billing disputes, escalation cases, or any interaction requiring the customer to contact support more than once.

**Critical timing constraint:** CES must be triggered within **60 minutes of case closure** to capture the customer's effort perception accurately. Sending CES more than a few hours after resolution allows the emotional salience of the effort to fade, and response rates drop sharply after 2 hours. The Salesforce native approach is a Record-Triggered Flow on Case, After Save, when Status changes to Closed, with a Scheduled Path set to run 15 minutes after closure.

### Feedback Management License and Response Caps

Salesforce Feedback Management is a paid add-on available in three tiers. Each tier sets a monthly survey response cap and unlocks progressively more advanced features. As of Spring '25:

| Tier | Monthly Response Cap | Key Features Unlocked |
|---|---|---|
| Starter | 1,000 responses/month | Basic survey builder, email invitations, Flow triggers |
| Growth | 10,000 responses/month | Branded surveys, merge fields, lifecycle maps, advanced reporting |
| Enterprise | 50,000 responses/month | All Growth features plus bulk send, CRM Analytics integration |

Exceeding the monthly cap blocks new survey invitations from being sent until the cap resets at the start of the next calendar month. Plan license tier based on expected case closure volume × target survey send rate.

---

## Common Patterns

### Pattern: Post-Case CES Trigger with 15-Minute Delay

**When to use:** The org's primary support model is case-based (email, web, or phone-to-case) and the business question is "are we making it easy enough for customers to get help?"

**How it works:**

1. Create a Salesforce Survey with a 7-point Rating question: "Overall, how easy was it to resolve your issue today?" (1 = Very Difficult, 7 = Very Easy). Add one optional open-text follow-up question for qualitative context.
2. Create a Record-Triggered Flow on the Case object, After Save, triggered when `Status` changes to `Closed`.
3. Add a Scheduled Path: 15 minutes after the trigger condition is met (not immediately — an immediate trigger sends the survey before the customer has had a moment to process the closure).
4. In the Scheduled Path, create a `SurveyInvitation` record linked to the survey and the Contact associated with the case. Set `ParticipantId` to `Case.ContactId` and `SurveyId` to the CES survey's record ID.
5. The platform sends an email invitation to the contact's email address using the configured survey email template.
6. Map the response to the originating Case via `SurveyResponse.CaseId` (custom lookup or flow-set field) for case-level CES reporting.

**Why not the alternative:** Sending the survey immediately on case closure catches the customer mid-wrap-up and before they have had a chance to verify the resolution actually worked. The 15-minute delay reduces premature responses and improves data quality. A 24-hour delay is too long — customers no longer remember the interaction effort vividly.

### Pattern: NPS as Periodic Relationship Pulse

**When to use:** The business needs a high-level loyalty benchmark to track relationship health over time, independent of individual transactions.

**How it works:**

1. Configure a Scheduled Survey send cadence — quarterly for B2B accounts, or 60–90 days after onboarding for new customers.
2. Use a Flow with Scheduled-Triggered activation (not Record-Triggered) targeting Contacts with `Account.Type = 'Customer'` who have not received an NPS survey in the past 90 days (filter by a custom date field on Contact: `Last_NPS_Survey_Sent__c`).
3. After each successful invitation send, update `Last_NPS_Survey_Sent__c` on the Contact record to prevent duplicate sends.
4. Report NPS in CRM Analytics or a custom report type that joins `SurveyResponse` to `Contact.Account` so scores can be segmented by account tier, region, or product line.
5. Track NPS trend over time — a rolling 3-quarter average is more meaningful than a single point-in-time score.

**Why not the alternative:** Triggering NPS on every case closure treats NPS as a transactional metric, which it is not designed to be. This drives survey fatigue, depresses response rates, and produces volatile scores that cannot distinguish relationship health from single bad interactions.

---

## Decision Guidance

| Situation | Recommended Metric | Reason |
|---|---|---|
| Measuring quality of a specific case or interaction | CSAT (1–5) | Captures satisfaction at a discrete moment; native question type available |
| Measuring overall customer loyalty and churn risk | NPS (0–10) | Designed for relationship-level measurement; strong churn predictor at the portfolio level |
| Measuring friction in the support process | CES (1–7) | Strongest predictor of individual customer disloyalty; directly actionable for process improvement |
| B2C high-volume transactional support | CSAT | Simple, fast to complete, benchmarkable at scale |
| B2B account-based service org | NPS (quarterly) + CES (per interaction) | NPS for exec-level health reporting; CES for operational improvement |
| Post-escalation or repeat-contact cases | CES | Effort is the dimension that most needs measurement when cases required re-work |
| Agentforce containment measurement | CSAT + Containment Rate | CES alone does not reflect bot-to-human handoff experience; pair with containment metric |
| Response volume under 1,000/month | Feedback Management Starter | Lower tier sufficient; avoid over-licensing |
| Response volume 1,000–10,000/month | Feedback Management Growth | Needed for merge fields and advanced reporting |

---

## Recommended Workflow

Step-by-step instructions for designing a CX measurement strategy:

1. **Define the business question.** Before selecting any metric, articulate the specific business question: Is the priority reducing churn? Improving first-contact resolution? Benchmarking service quality against industry peers? The metric must match the question — do not default to NPS just because it is well known.
2. **Select the primary metric and timing rule.** Use the Decision Guidance table to select the appropriate metric. For CES, confirm the 60-minute post-closure trigger window is achievable with the existing Flow configuration and license tier. For NPS, confirm a 90-day re-send suppression mechanism exists on the Contact record.
3. **Assess the Feedback Management license tier.** Calculate expected monthly survey volume: (monthly case closure count) × (target survey send rate, e.g., 80%). Compare against license tier caps. Upgrade the tier if volume exceeds the cap by more than 20% to avoid mid-month survey blackouts.
4. **Design the survey and trigger Flow.** Work with the `admin/salesforce-surveys` skill to configure the survey object, question type, and record-triggered Flow. For CES, validate that the Scheduled Path is set to 15 minutes (not 0) and that the ContactId lookup handles cases with no associated contact gracefully (null check required).
5. **Map responses to KPIs.** Define the reporting model: which report types join `SurveyResponse` to Case, Contact, and Account. Identify whether CRM Analytics or Service Analytics dashboards will surface the scores. Ensure the response-to-case linkage field is set in the Flow before creating the invitation record.
6. **Set governance rules.** Document the re-send suppression policy (how often a single contact can receive each survey type), the opted-out contact handling (check `HasOptedOutOfEmail` before creating `SurveyInvitation`), and the escalation path for low-score responses (e.g., CES of 1–2 triggers a follow-up case creation).
7. **Baseline and validate.** After 30 days of production data, review response rates (target: 15–25% for email-based CES/CSAT), score distributions, and completion rates. Adjust survey length (ideally 1–3 questions), timing, or email template if response rates fall below 10%.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Business question is documented and maps to the selected metric (CSAT, NPS, or CES)
- [ ] Feedback Management license tier confirmed and monthly response cap exceeds projected volume
- [ ] Survey trigger timing validated: CES triggers within 60 minutes of case closure; NPS has 90-day re-send suppression
- [ ] `HasOptedOutOfEmail` check is in the Flow before `SurveyInvitation` creation
- [ ] Null-contact guard exists for cases without a linked Contact (avoids Flow errors on cases created without a contact)
- [ ] Response-to-case linkage field is set so scores can be reported at the case level
- [ ] Reporting model defined: report type, dashboard, and owner for each metric
- [ ] Low-score response escalation path documented (e.g., CES 1–2 triggers follow-up action)
- [ ] Re-send suppression policy documented per survey type

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **NPS bucket boundaries are hardcoded and cannot be customized.** The native NPS question type in Salesforce Surveys automatically bins responses into Detractor (0–6), Passive (7–8), and Promoter (9–10). There is no configuration to change these ranges. If a business wants non-standard NPS buckets (e.g., Detractor 0–5), the only option is to use a plain Rating question and calculate bucketing in a custom formula field or report — the NPS question type cannot be used.
2. **Survey invitations sent to contacts with `HasOptedOutOfEmail = true` fail silently.** The Flow does not throw an error or fault when creating a `SurveyInvitation` for an opted-out contact. The invitation record is created, but no email is sent, and the response is never collected. This makes response rates appear artificially low. Add a Flow decision element to check `Case.Contact.HasOptedOutOfEmail` before the Create Records step.
3. **CES sent more than 2 hours after case closure produces unreliable data.** Survey science shows that effort memory decays rapidly after a support interaction ends. A CES survey sent the next day captures the customer's general sentiment, not their recollection of effort for that specific interaction. Always use a Scheduled Path with a delay of 15–60 minutes, not a 24-hour delay or a manual send cadence.
4. **Monthly response caps reset on the calendar month, not a rolling 30-day window.** If your org closes 900 cases in the last week of March and sends all 900 survey invitations, and 950 responses arrive in April (month reset), you will not hit the Starter cap. But if you send 950 invitations in the same calendar month and all 950 respond, the 951st response is blocked. Design send rate throttling around the calendar month, not rolling averages.
5. **`SurveyResponse` cannot be linked to a Case via a standard lookup — a custom field is required.** The platform does not provide a standard `CaseId` field on `SurveyResponse`. To report CES at the case level, either set a custom lookup field on `SurveyInvitation` (the invitation record can carry the case reference), or use the Flow to populate a custom relationship field. Without this linkage, response data is only reportable at the contact level.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| CX metric selection record | Documents chosen metric(s), business rationale, trigger timing rules, and suppression policy |
| Feedback Management license recommendation | Tier recommendation with projected volume calculation and cap headroom |
| KPI integration map | Joins survey response fields to Case, Contact, and Account for dashboard reporting |
| Survey timing and trigger specification | Flow trigger type, Scheduled Path delay, null-contact guard, and opted-out contact handling |
| Low-score escalation path | Defines thresholds (e.g., CES ≤ 2) and the downstream action (case creation, callback task) |

---

## Official Sources Used

- Salesforce Feedback Management Overview — https://help.salesforce.com/s/articleView?id=sf.feedback_management_overview.htm
- Set Up Customer Feedback Survey — https://help.salesforce.com/s/articleView?id=sf.feedback_management_setup.htm
- Service Insights CSAT Dashboard — https://help.salesforce.com/s/articleView?id=sf.service_insights_csat_dashboard.htm
- Salesforce Surveys Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.surveys.meta/surveys/surveys_intro.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html

---

## Related Skills

- admin/salesforce-surveys — Use for the technical build: survey object configuration, Flow invitations, guest user profile, and email template setup
- architect/sla-design-and-escalation-matrix — Use when designing the escalation path triggered by low CES or CSAT scores
- architect/service-cloud-architecture — Use for overall Service Cloud architecture decisions of which CX measurement is one component
- agentforce/agent-testing-and-evaluation — Use when CES or CSAT is being used to measure Agentforce bot containment quality alongside containment rate
