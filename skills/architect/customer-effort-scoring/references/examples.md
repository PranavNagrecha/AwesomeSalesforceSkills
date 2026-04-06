# Examples — Customer Effort Scoring

## Example 1: Post-Case CES Measurement for a B2C Telco Support Org

**Context:** A telecommunications company handles 12,000 case closures per month through a web-to-case portal. Leadership wants to reduce repeat contacts (currently 28% of cases are re-opened within 7 days) and suspects that high friction in the resolution process is the root cause. They already have CSAT data but it shows 78% satisfaction — which does not explain the high re-open rate.

**Problem:** The team chose CSAT because it was familiar, but CSAT measures emotional satisfaction at a moment in time — not process friction. A customer can be satisfied that their case was eventually resolved and still find the process exhausting. CSAT was masking a structural effort problem. The business had no metric to prove it.

**Solution:**

Deploy a CES survey triggered 15 minutes after every case closure, alongside (not replacing) the existing CSAT survey. The CES question: "Overall, how easy was it to resolve your issue today?" (1 = Very Difficult, 7 = Very Easy).

Flow configuration (Record-Triggered, After Save on Case):

```text
Trigger: Case.Status changes to "Closed"
Scheduled Path: +15 minutes after trigger

Decision: Is Case.ContactId null?
  → Yes: End (no contact to survey)
  → No: Continue

Decision: Is Contact.HasOptedOutOfEmail true?
  → Yes: End (respect opt-out)
  → No: Continue

Create Records: SurveyInvitation
  - SurveyId: [CES Survey record ID]
  - ParticipantId: Case.ContactId
  - InvitationStatus: Pending

Update Records: Case
  - CES_Survey_Sent__c = true
  - CES_Survey_Sent_Date__c = NOW()
```

After 90 days, the org built a CRM Analytics dashboard correlating CES scores to re-open rate. Cases with CES ≤ 3 had a 47% re-open rate within 7 days. Cases with CES ≥ 6 had a 4% re-open rate. This gave leadership the data needed to invest in agent resolution guides and knowledge base improvements.

**Why it works:** CES directly measures the friction that drives re-contacts. CSAT was misleading because customers were satisfied the issue was "eventually" closed — but the effort required to get there was the real driver of churn behavior. Running both metrics in parallel allowed the org to demonstrate the gap between perceived satisfaction and actual process quality.

---

## Example 2: NPS Quarterly Pulse for a B2B SaaS Support Org

**Context:** A SaaS company with 800 enterprise accounts needs an exec-level CX metric to report in quarterly business reviews. The support team handles 3,000 cases per month across account tiers (Enterprise, Mid-Market, SMB). They want a metric that tracks relationship health — not just ticket-level satisfaction — because the primary churn risk is low perceived ROI from the product, not individual bad support interactions.

**Problem:** The team initially triggered NPS on every case closure, producing 3,000 NPS surveys per month. Response rates dropped to 2% within six weeks due to survey fatigue, and the scores were dominated by customers who had just had a bad interaction — making the metric useless as a relationship health indicator.

**Solution:**

Switch to a quarterly scheduled NPS send, per Contact, with a 90-day suppression guard on each Contact record.

Suppression mechanism on Contact:

```text
Custom field: Last_NPS_Survey_Sent__c (Date)

Scheduled-Triggered Flow (daily, 6 AM):
  Filter: Contact.Account.Type = 'Customer'
         AND Contact.Email != null
         AND Contact.HasOptedOutOfEmail = false
         AND (Last_NPS_Survey_Sent__c = null
              OR Last_NPS_Survey_Sent__c <= TODAY() - 90)

For each matching Contact:
  Create: SurveyInvitation (NPS Survey, ParticipantId = Contact.Id)
  Update: Contact.Last_NPS_Survey_Sent__c = TODAY()
```

Report NPS broken down by account tier (Enterprise, Mid-Market, SMB) and segment separately — Enterprise NPS consistently runs 15–20 points higher than SMB, so blending all tiers into a single NPS number would mislead the exec audience.

**Why it works:** Quarterly sends with suppression guards maintain response rates of 18–22% for B2B contacts, versus the 2% response rate from over-surveying. Segmenting by account tier surfaces the real signal: if Enterprise NPS drops while SMB is stable, the engineering or CS team needs to investigate enterprise-specific issues — not service delivery in general.

---

## Anti-Pattern: Deploying All Three Metrics Simultaneously

**What practitioners do:** Teams excited about the CX measurement program configure CSAT, NPS, and CES surveys all triggered from the same case closure event, reasoning that "more data is better."

**What goes wrong:** Customers who close a case receive three separate survey emails within an hour. Response rates on all three collapse within 30 days (typically below 5% for each). The response pool becomes biased toward customers with strong positive or negative feelings — the middle cohort (who are the highest churn risk) stops responding entirely. The data is unusable for trend analysis because the response population is not representative.

**Correct approach:** Select a single primary metric for each interaction type. For post-case transactional measurement, choose CES or CSAT — not both. Reserve NPS for periodic relationship measurement on a separate send cadence. If the org genuinely needs two metrics, send them in sequence: close the CSAT survey first, then send CES one week later — never in the same send window.
