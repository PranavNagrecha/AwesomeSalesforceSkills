# Examples — Flow Action Framework

## Example 1: Wire a bulk-safe Apex action from a record-triggered Flow

**Context:** A record-triggered Flow runs after save on Case. For each Case in the batch, a custom scoring algorithm in Apex must run, but the team wants one invocable call per transaction chunk instead of looping per record.

**Problem:** An early design used **Loop → Apex action** with a single-Id input. In full bulk saves, the Flow approached governor limits and behaved inconsistently compared to sandbox tests with one Case.

**Solution:**

1. Refactor the Apex class to expose `@InvocableMethod` with `List<CaseScoreRequest>` in and `List<CaseScoreResult>` out (see `invocable-methods` for wrapper details).
2. In the Flow, pass `{!$Record}` via a **Get Records** collection or the triggering record collection into the Apex action’s collection input once per path, not inside a loop.
3. Map `CaseScoreResult` output fields back with **Assignment** to related records or staging variables.

**Why it works:** The invocable contract is list-first; Flow’s bulk interview aligns with a single bulk-chunked Apex call, reducing overhead and matching platform expectations.

---

## Example 2: Replace duplicated element blocks with a subflow action

**Context:** Three department-specific onboarding flows each repeated the same ten-step “provision chatter group and log milestone” sequence.

**Problem:** A wording change in one branch was updated in only two of three flows, causing production divergence.

**Solution:**

1. Extract the shared sequence into **Onboarding_Common_Subflow** with defined input variables (user Id, department code) and output variables (success flag, log Id).
2. In each department Flow, replace the block with **Run Subflow**, mapping parent variables into the child inputs and reading outputs for branching.

**Why it works:** Subflows are first-class actions with a stable boundary; updates ship once in the child flow.

---

## Anti-Pattern: Use Apex action for pure field updates

**What practitioners do:** Create an `@InvocableMethod` that only performs `update` on fields available in **Update Records**.

**What goes wrong:** Higher maintenance (tests, deployments), loss of self-documenting Flow, and unnecessary governor use for logic the platform already expresses declaratively.

**Correct approach:** Use **Update Records** or **Assignment** plus **Update Records** unless a genuine gap (validation, unsupported logic, reuse outside Flow) forces Apex.
