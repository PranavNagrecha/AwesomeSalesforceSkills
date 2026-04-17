# Examples — Agent Metric Dashboards

## Example 1: Deflection with baseline

**Context:** Service org with 40% pre-agent escalation rate.

**Problem:** Post-deployment escalation is 30% — but is that deflection or demand shift?

**Solution:**

Split the dashboard into cohorts: 'Queue A (agent on)' vs 'Queue B (agent off)'. Deflection = (A.escalation - B.escalation) / B.escalation, normalized to same traffic mix.

**Why it works:** Causal attribution requires a control; the dashboard must not conflate trend with treatment.


---

## Example 2: Tokens/conversation trend

**Context:** Costs spike after a topic-instruction rewrite.

**Problem:** Unclear whether cost rise is engagement or bloat.

**Solution:**

Stack chart: tokens-per-turn × turns-per-conversation. Lets reviewers separate 'users engaged more' (good) from 'each turn is fatter' (possibly bad).

**Why it works:** Decomposing cost into intensity × volume makes causality legible.

