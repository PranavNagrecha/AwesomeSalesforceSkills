# Examples — AI Use Case Assessment

## Example 1: Service Cloud org with clean Case data but no Data Cloud

**Context:** A B2C company with 50,000+ Case records per year wants to adopt AI to reduce average handle time in their contact center. They have Service Cloud Enterprise Edition with the Einstein for Service add-on but no Data Cloud license. They come to the assessment with five candidate use cases: Work Summaries, Case Classification, Article Recommendations, Chatbot deflection, and a "360 customer view" agent.

**Problem:** Without a structured assessment, the project team gravitates toward the "360 customer view" Agentforce agent because it sounds the most transformative. They scope it, plan a six-month build, and only discover during implementation that it requires Data Cloud for cross-channel data unification — a license that was not purchased.

**Solution:**

Run the Impact-Effort and Feasibility scoring before any scoping:

```
Use Case                  | Impact | Effort | Quadrant      | Data Readiness | Technical Feasibility
--------------------------|--------|--------|---------------|----------------|----------------------
Work Summaries            |   3    |   1    | Quick Win     | 10/12 — Ready  | Go: license confirmed
Case Classification       |   2    |   1    | Quick Win     | 9/12 — Ready   | Go: license confirmed
Article Recommendations   |   2    |   1    | Quick Win     | 8/12 — Ready   | Go: license confirmed
Chatbot Deflection        |   3    |   2    | Quick Win     | 7/12 — Marginal| Conditional: needs KB
360 Customer View Agent   |   3    |   3    | Big Bet       | 4/12 — Blocked | Blocked: needs Data Cloud
```

The 360 customer view use case is immediately flagged as Blocked — requiring Data Cloud, which is not licensed. It moves to a future-phase list with a remediation requirement: "License and populate Data Cloud before re-assessing." The team proceeds with the four Quick Wins and delivers value in the current quarter.

**Why it works:** The data readiness gate and technical feasibility check surface the Data Cloud dependency before any implementation scoping begins. The team avoids the six-month false start and maintains stakeholder trust.

---

## Example 2: Manufacturing org with dirty Opportunity data wanting Einstein Opportunity Scoring

**Context:** A manufacturing company's sales leadership wants Einstein Opportunity Scoring to help reps focus on deals most likely to close. They have Sales Cloud with Einstein for Sales. Their Opportunity records are inconsistently populated — close dates are frequently set to end-of-quarter by default, Stage values are updated infrequently, and roughly 30% of closed-lost Opportunities have no reason recorded.

**Problem:** The org has the correct license and enough Opportunity records (5,000+), so a surface-level assessment marks this as feasible. After activation, Einstein reports "Model training in progress" for three weeks, then produces a score distribution where 80% of Opportunities cluster at the same score range. Reps ignore the scores because they don't differentiate high-probability from low-probability deals.

**Solution:**

Run the data readiness scoring with sub-dimension granularity before marking technical feasibility as confirmed:

```
Data Readiness Sub-Dimension | Score | Finding
-----------------------------|-------|-----------------------------------------------------------
Availability                 |   3   | Opportunities exist in sufficient volume (5,000+)
Quality                      |   1   | Close dates default-populated; Stage rarely updated;
                             |       | 30% closed-lost missing loss reason — model cannot learn
                             |       | signal from noise
Unification                  |   2   | Single CRM source; no external enrichment
Governance                   |   2   | No documented field-level data quality policy

Composite Score: 8/12 — Conditional (quality gate failed)
```

Recommendation: **Data Blocked — Conditional Approval pending remediation.** Required steps before re-assessment:
1. Audit and enforce Close Date accuracy via a validation rule prohibiting dates more than 90 days in the future on active opportunities.
2. Add a required Loss Reason picklist field enforced on stage-to-Closed-Lost transitions via Flow.
3. Run a 90-day data hygiene campaign with sales managers reviewing stale open opportunities.
4. Re-score data readiness after 90 days. If quality score reaches 2+, proceed to activation.

**Why it works:** Scoring quality as a distinct sub-dimension — not just "do records exist?" — surfaces the signal problem before the org wastes an Einstein license activation on a model that cannot learn valid patterns from the available data.

---

## Anti-Pattern: Scoping Implementation Deliverables During Assessment

**What practitioners do:** During the use case assessment workshop, they let the conversation drift from "is this feasible?" into "how do we build this?" — sketching data flows, assigning developer tasks, and estimating sprint counts before the use case has been formally approved.

**What goes wrong:** The org ends up with implementation scope for use cases that have not passed the data readiness gate or feasibility scoring. When the gate is later applied, blocked use cases have already consumed stakeholder expectations and political capital — walking them back causes conflict. Approved use cases have had their effort scores contaminated by premature implementation assumptions.

**Correct approach:** Maintain a strict boundary between assessment outputs and implementation inputs. The assessment produces a prioritized shortlist and feasibility scorecard. The first implementation planning session happens only after the shortlist is signed off. If stakeholders want to discuss implementation in the same session, park those topics in a "parking lot" document and explicitly defer them.
