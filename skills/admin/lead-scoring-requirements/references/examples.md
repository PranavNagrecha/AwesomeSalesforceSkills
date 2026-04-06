# Examples — Lead Scoring Requirements

## Example 1: B2B SaaS — Composite Score with Fit + Engagement Dimensions (Sales Cloud Only)

**Context:** A B2B SaaS company sells project management software to mid-market and enterprise companies. The marketing team captures leads via web-to-lead forms and syncs engagement signals (content downloads, webinar attendance) to custom Lead fields via Zapier. The org has no Account Engagement license. Sales wants automatic MQL routing when a lead crosses a quality threshold.

**Problem:** Without a structured model, reps were manually reviewing every lead from the queue — most were unqualified. Marketing had no feedback loop to improve targeting. The MQL rate was undefined and trust between marketing and sales was low.

**Solution:**

The team defined two scoring dimensions and mapped them to Salesforce fields:

**Fit dimension (max 40 points):**

| Criterion | Condition | Points |
|---|---|---|
| Industry match | `Industry` IN ('Technology', 'Financial Services', 'Healthcare') | 15 |
| Company size | `NumberOfEmployees` >= 100 AND <= 5000 | 15 |
| Decision-maker title | `Title` contains 'VP', 'Director', 'Head of', 'Manager' | 10 |

**Engagement dimension (max 60 points):**

| Criterion | Condition | Points |
|---|---|---|
| Demo request | `Demo_Requested__c` = true | 30 |
| Content downloads | `Content_Downloads__c` >= 3 | 15 |
| Webinar attendance | `Webinar_Attended__c` = true | 15 |

**Field implementation:**

```text
Fit_Score__c          — Number(3,0), updated by record-triggered Flow on Lead create/edit
Engagement_Score__c   — Number(3,0), updated by record-triggered Flow when marketing signals write back
Composite_Score__c    — Number(3,0), updated by Flow: Fit_Score__c + Engagement_Score__c
Is_MQL__c             — Checkbox, set to true by Flow when Composite_Score__c >= 50
                        AND Company != null AND Email != null
MQL_Date__c           — DateTime, stamped by same Flow on MQL transition
```

The record-triggered Flow updates `Fit_Score__c` using a series of Decision elements that evaluate each criterion and assign a running total via assignment variables. A second Flow updates `Composite_Score__c` and evaluates the MQL condition.

MQL threshold was set to 50 (composite) after back-scoring 150 closed-won opportunities from the prior year: 87% scored >= 50, while only 12% of closed-lost opportunities did.

**Why it works:** Separating fit and engagement into stored Number fields makes each dimension independently reportable and keeps the composite score available to Flow entry criteria and Assignment Rules. Calibrating the threshold against historical closed-won data reduces false positives from day one.

---

## Example 2: Account Engagement (Pardot) Score + Grade Composite MQL Definition

**Context:** A manufacturing company uses Account Engagement (Pardot) as their marketing automation platform and Salesforce Sales Cloud as their CRM. Account Engagement is already running email nurture programs and tracking prospect engagement. The AE Score field (0–100) syncs to the Lead record. The team wants to define MQL in a way that combines engagement score with ICP fit.

**Problem:** Relying on AE Score alone produced high-engagement leads who were clearly not buyers — competitors, students, and job seekers. Sales rejected more than 40% of MQLs as unqualified, destroying trust in the marketing pipeline.

**Solution:**

The team used Account Engagement's two-dimensional model — Score (engagement) and Grade (fit) — as the basis for MQL definition:

**AE Grading criteria (configured in Account Engagement):**

| Profile criterion | Grade modifier |
|---|---|
| Job title matches target persona | +1 grade level |
| Industry matches ICP | +1 grade level |
| Company size in target range | +1 grade level |
| Personal email domain (gmail, yahoo) | -2 grade levels |

MQL definition: `AE Score >= 50 AND AE Grade >= B`

**Salesforce side implementation:**

```text
Pardot_Score__c       — Number(3,0), synced from AE, READ-ONLY in Salesforce
                        (do not write to this field from CRM side)
Pardot_Grade__c       — Text(2), synced from AE (values: A+, A, A-, B+, B, B-, C, D, F)
Pardot_Grade_Num__c   — Number(1,0), updated by Flow:
                        A+/A/A-=5, B+/B/B-=4, C=3, D=2, F=1
Is_MQL__c             — Checkbox, set by Flow:
                        Pardot_Score__c >= 50 AND Pardot_Grade_Num__c >= 4
MQL_Date__c           — DateTime, stamped on MQL transition
```

Handoff SLA:
- Rep must accept or recycle within 1 business day
- Required populated fields before handoff: `Company`, `Title`, `Email`, `Phone`
- Recycle reason captured in `Recycle_Reason__c` picklist: No Response / Wrong Timing / Not Decision Maker / Competitor / Other

After 60 days, the sales MQL rejection rate dropped from 40% to 11%.

**Why it works:** The grade filter eliminates high-engagement non-buyers. The Salesforce-side Flow converts the letter grade to a numeric value so it can be evaluated in standard Flow conditions. Writing a Flow-maintained numeric grade field (rather than referencing the text grade directly) makes the model maintainable as AE grade values do not change.

---

## Anti-Pattern: Defining MQL as a Single Behavioral Score Threshold

**What practitioners do:** Set MQL = "Score >= 50" using only email engagement or website visit data, with no fit dimension. Marketing reports high MQL volume; sales consistently rejects leads.

**What goes wrong:** High-engagement low-fit leads (competitors, researchers, students) flood the sales queue. Reps lose confidence in the pipeline. Marketing loses credibility. The MQL metric becomes meaningless because rejection rate is not tracked.

**Correct approach:** Always combine a fit (demographic/firmographic) dimension with an engagement dimension. Require both dimensions to reach a minimum threshold for MQL — a lead can only be MQL if they are both a good fit AND showing intent. Track SQL acceptance rate and recycle reasons as feedback signals to refine weights quarterly.
