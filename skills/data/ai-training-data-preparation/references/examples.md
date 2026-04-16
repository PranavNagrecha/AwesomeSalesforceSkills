# Examples — AI Training Data Preparation

## Example 1: Einstein Discovery Story for Opportunity Win Prediction

**Context:** A sales operations team wants to use Einstein Discovery to predict which open opportunities will close won. They have 18 months of historical opportunity data in Salesforce.

**Problem:** The team created an Einstein Discovery story using all available opportunity fields and the `IsClosed` and `IsWon` fields as the outcome. After training, the model showed 95% accuracy but had zero business predictive value — the model was essentially memorizing closed records.

**Solution:** The data preparation team audited the feature fields and found three leakage sources: (1) `StageName` was set to "Closed Won" at the same time `IsWon` was set — classic leakage; (2) a custom `Win_Reason__c` field was only populated after close; (3) `Probability` (auto-updated by stage) jumped to 100% at close. These three fields accounted for essentially all of the model's "accuracy." After removing leakage fields and retraining with only fields populated during the opportunity lifecycle (Industry, Owner Role, Competitor presence, Days in Stage, Lead Source), accuracy dropped to 73% but the model now genuinely predicted future outcomes.

**Why it works:** Leakage detection requires checking whether each candidate field was populated before or because of the outcome. High-correlation fields (StageName at "Closed Won") that are causally downstream of the outcome are definitional leakage.

---

## Example 2: Einstein Prediction Builder Setup for Case Escalation

**Context:** A service team wants to use Einstein Prediction Builder to flag cases likely to escalate before they actually do.

**Problem:** The team defined the outcome as "Case has Escalated__c = true" and found that only 3% of cases had ever been escalated — creating a severe class imbalance. Initial EPB setup produced a model that predicted "not escalated" for every record (technically accurate on 97% of cases) but never flagged any actual escalations.

**Solution:** The data preparation work focused on: (1) verifying that at least 200 positive-class (escalated) records existed (they had 180 — just under the minimum); (2) working with the service team to find proxy datasets from legacy system import and recovering 400+ escalated cases; (3) identifying that `Resolution_Time__c` was a post-escalation field and removing it; (4) adding `Customer_Tier__c`, `Product_Category__c`, and `Days_Without_Response__c` as features. After remediation, the model reached useful recall at the 40% prediction threshold.

**Why it works:** EPB requires at least 200 positive-class records. Severe class imbalance (< 5% positive) also requires adjusting the prediction threshold below the default 50% to achieve usable recall.
