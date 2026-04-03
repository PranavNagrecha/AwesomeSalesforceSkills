# Gotchas - Subflows And Reusability

## A Subflow Still Shares The Parent Transaction

**What happens:** Teams assume limits or rollback boundaries reset after a subflow call.

**When it occurs:** Reuse is treated like process isolation instead of a call inside the same overall transaction.

**How to avoid:** Review limits, DML, and fault behavior across parent and child together.

---

## Variable Names Become API Surface

**What happens:** Inputs and outputs are renamed casually, and parent flows start failing or returning blank values.

**When it occurs:** Teams treat subflow variables as local implementation detail instead of a caller contract.

**How to avoid:** Name variables intentionally and treat contract changes like release-managed interface changes.

---

## Reuse Can Hide Side Effects

**What happens:** A child flow that started as a simple lookup now creates records, sends notifications, and mutates unrelated fields.

**When it occurs:** New callers keep adding "just one more" behavior to the shared child flow.

**How to avoid:** Separate pure reusable logic from parent-specific side effects and challenge any child flow whose scope keeps widening.

---

## Extraction Can Increase Complexity If The Boundary Is Wrong

**What happens:** The parent becomes shorter on screen, but the end-to-end design is harder to understand.

**When it occurs:** Teams extract logic for aesthetics rather than because the contract is genuinely reusable.

**How to avoid:** Extract only when reuse, maintainability, and stable contract design all improve together.
