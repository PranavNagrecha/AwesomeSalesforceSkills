# Examples — Agentforce Service AI Setup

## Example 1: License Gap Discovery Before Work Summaries Enablement

**Context:** A financial services company purchased Service Cloud Einstein to enable AI features for their contact center. The implementation team was tasked with enabling Work Summaries so agents could auto-generate post-call summaries from voice transcripts. The project was two weeks from go-live.

**Problem:** The team navigated to Setup > Service > Einstein Work Summaries and found the option completely absent from the Setup menu. They assumed this was a permission or org configuration issue and spent several days investigating page layouts, permission sets, and feature flags — none of which resolved the missing option.

**Solution:**

The correct diagnostic sequence:

```
1. Setup > Company Information > Feature Licenses
   → Confirmed: "Service Cloud Einstein" = 50 seats provisioned
   → Confirmed: No "Einstein Generative AI" or "Einstein 1 Service" PSL present

2. Root cause: Service Cloud Einstein add-on does NOT include generative AI features.
   Work Summaries requires Einstein Generative AI entitlement (or Einstein 1 Service edition).

3. Resolution path:
   → Escalate to Salesforce AE for Einstein Generative AI add-on procurement
   → Estimated license provisioning time: 5–10 business days
   → Adjusted go-live date accordingly
   → Enabled Case Classification and Article Recommendations (covered by existing license)
     as Phase 1 while procurement completed
```

**Why it works:** The license gap between predictive AI (Service Cloud Einstein) and generative AI (Einstein Generative AI or Einstein 1 Service) is the single most common blocker for Work Summaries enablement. Diagnosing it in Setup > Company Information takes two minutes. Diagnosing it by investigating page layouts and permission sets can take days. Running the license check first eliminates the longest troubleshooting path immediately.

---

## Example 2: Case Classification Deferred Due to Insufficient Data Quality

**Context:** A B2B software company migrated to Salesforce 14 months ago and wanted to enable Case Classification to auto-populate Case Type, Priority, and Case Reason on inbound cases. Their closed case count was 1,450 — above the stated minimum of 400.

**Problem:** Case Classification was enabled and the model trained. After two weeks of production use, agents reported that the auto-populated Case Type field was wrong approximately 35% of the time. Agents began overriding values so frequently that the feature created more work than it saved. AI adoption stalled.

**Solution:**

```
Pre-enablement data audit (what should have been done first):

-- Case field completeness query (SOQL for reference)
SELECT COUNT(Id) TotalClosed,
       COUNT(Type) TypeNotNull,
       COUNT(Priority) PriorityNotNull,
       COUNT(Reason) ReasonNotNull
FROM Case
WHERE Status = 'Closed'
AND ClosedDate >= LAST_N_DAYS:365

-- Results:
-- TotalClosed: 1,450
-- TypeNotNull: 790  → 54% completeness (BELOW threshold)
-- PriorityNotNull: 1,380 → 95% completeness (OK)
-- ReasonNotNull: 620 → 43% completeness (BELOW threshold)

Corrective action:
1. Remove Case Type and Case Reason from the classification model
2. Retain Priority classification only (95% training data completeness)
3. Run model retrain
4. After 90 days of agents filling Case Type and Reason consistently,
   re-assess completeness and add fields back to the model
```

**Why it works:** Case Classification accuracy is bounded by training data quality. Enabling classification for fields with poor historical completeness produces a model that reflects the randomness of past data entry habits, not genuine case patterns. Auditing field completeness before enabling classification — and limiting the initial model scope to high-completeness fields — produces a model agents can trust. A high-accuracy model for one field is more valuable than a low-accuracy model for three fields.

---

## Example 3: Reply Recommendations Enabled But Producing No Suggestions

**Context:** A retail company activated Einstein Reply Recommendations for their Messaging channel and added the Suggested Replies component to the messaging console. Agents reported seeing the component in the UI but it never showed any suggested replies, even for common questions they handle dozens of times per day.

**Problem:** The feature was technically enabled and the UI component was correctly placed, but the model had no corpus to generate suggestions from.

**Solution:**

```
Diagnostic steps:

1. Setup > Service > Einstein Reply Recommendations
   → Status shows: "Enabled" (correct)
   → Training Data section shows: "No training data loaded" ← ROOT CAUSE

2. Resolution:
   → Click "Build Training Data" in Setup > Service > Einstein Reply Recommendations
   → The Training Data job processes historical messaging transcripts
   → Job runtime: 2–24 hours depending on transcript volume
   → After job completion, model training begins automatically
   → Suggestions appear in the console after model training is complete (additional 24–48 hours)

3. Confirm messaging transcript volume:
   → Salesforce recommends several thousand historical messaging interactions
     for useful recommendation quality
   → Orgs with < 1,000 historical messaging sessions will see very limited
     or low-quality suggestions even after the Training Data job completes
```

**Why it works:** Reply Recommendations is the only Einstein for Service feature with a mandatory prerequisite step that is separate from the feature enablement toggle. Every other feature begins model training automatically after being enabled. Reply Recommendations requires an explicit admin action (running the Training Data job) that is easily missed. The Training Data job is the model's entire learning corpus — without it, there is nothing to base suggestions on.

---

## Anti-Pattern: Enabling All Einstein for Service Features Simultaneously at Project Start

**What practitioners do:** On day one of an Einstein for Service implementation, an admin goes to Setup and enables every Einstein for Service feature available — Case Classification, Article Recommendations, Reply Recommendations — all at once before any data readiness assessment.

**What goes wrong:** With all features enabled simultaneously and no data validation done first:

- Case Classification may train on fields with 30–50% null rates, producing unreliable predictions that agents override constantly
- Article Recommendations returns no results if agents have never linked articles to cases (no training signal)
- Reply Recommendations shows no suggestions because the Training Data job was never run
- The project sponsor sees "nothing is working" across all features simultaneously with no way to determine which issue belongs to which feature
- All three failures look like a single broken implementation, when in reality each has a different root cause and different fix

**Correct approach:** Assess data readiness before enabling anything. Enable features in phases, with a validation gate and model training wait period between each phase. Start with the feature that has the highest data readiness and work toward features that require more setup (or procurement) time.
