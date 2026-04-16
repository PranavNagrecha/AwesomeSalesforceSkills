# LLM Anti-Patterns — AI Training Data Preparation

Common mistakes AI coding assistants make when generating or advising on AI Training Data Preparation.
These patterns help the consuming agent self-check its own output.

---

## Anti-Pattern 1: Treating Outcome Field Selection as Trivial

**What the LLM generates:** "Use IsClosed or IsWon as your outcome field for opportunity prediction."

**Why it happens:** LLMs recognize standard boolean fields and suggest them without auditing whether they are causally appropriate or contain leakage.

**The correct pattern:** The outcome field must be: (1) the event you are actually trying to predict, (2) populated before (not because of) the predicted event, and (3) distinct from proxy fields that are causally downstream. For opportunity win prediction, `IsWon` is appropriate but must be combined with a prediction window — using all closed records regardless of stage at prediction time creates leakage from fields like StageName that change simultaneously with IsWon.

**Detection hint:** If the suggested outcome field or any predictor field is populated at the exact same time as the outcome event, flag it for leakage review.

---

## Anti-Pattern 2: Ignoring Fill-Rate Thresholds for Einstein Discovery

**What the LLM generates:** A field list for an Einstein Discovery story that includes fields with < 50% fill rate without noting the risk.

**Why it happens:** LLMs generate field lists based on field existence, not on fill-rate data that requires a runtime query.

**The correct pattern:** All fields intended as Einstein Discovery predictors must be audited for fill rate before story creation. Fields below ~70% fill rate are silently dropped. The audit requires running SOQL against the actual org data — this cannot be inferred from object schema alone.

**Detection hint:** If the response recommends Einstein Discovery feature fields without explicitly mentioning fill-rate requirements or an audit step, the response is incomplete.

---

## Anti-Pattern 3: Recommending Einstein Prediction Builder for Non-Binary Outcomes

**What the LLM generates:** "Use Einstein Prediction Builder to predict churn probability score or customer lifetime value."

**Why it happens:** LLMs conflate Einstein Prediction Builder with Einstein Discovery. EPB supports only binary (yes/no) outcomes.

**The correct pattern:** EPB supports binary classification only. Regression (continuous numeric output like revenue or churn score), multi-class classification, or time-series predictions require Einstein Discovery with a CRM Analytics license.

**Detection hint:** Any recommendation to use EPB for a non-binary, numeric, or continuous outcome is incorrect.

---

## Anti-Pattern 4: Using Proxy Fields Known Only Post-Outcome

**What the LLM generates:** Including `StageName = 'Closed Won'`, `Probability = 100`, or custom "Reason" fields in the predictor list.

**Why it happens:** LLMs list fields that correlate strongly with the outcome, without checking whether the correlation is because the field was set at the same time as the outcome.

**The correct pattern:** Fields that are populated simultaneously with or because of the outcome are proxy fields that cause leakage. Even if they correlate strongly in training data, they will not be available at prediction time for open records.

**Detection hint:** Review each suggested predictor: ask "Is this field populated before the outcome occurs, or at/after?" Fields populated only when the outcome is finalized are leakage candidates.

---

## Anti-Pattern 5: Omitting Class Balance Check for EPB

**What the LLM generates:** "Enable Einstein Prediction Builder using the outcome condition 'Escalated__c = true'." — without checking positive class count.

**Why it happens:** LLMs recommend EPB setup steps without running a class balance audit.

**The correct pattern:** EPB requires at least 200 positive-class records (where the outcome condition is true) and at least 200 negative-class records. When positive class is < 5% of total records, the model will predict the negative class for nearly everything and appear accurate while being useless. Class balance must be verified before enabling EPB.

**Detection hint:** If the response does not include a step to count positive-class vs. negative-class records before enabling EPB, the data preparation is incomplete.
