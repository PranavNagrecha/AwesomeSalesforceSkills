# Gotchas — Record Triggered Flow Patterns

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## The Wrong Save Context Creates Architecture Debt Fast

**What happens:** A same-record field update is implemented in after-save, and the org pays the cost forever through extra DML and re-entry risk.

**When it occurs:** Teams choose after-save by default instead of checking whether the requirement is only about the current record.

**How to avoid:** Start with before-save unless the design clearly needs committed side effects.

---

## Broad Entry Criteria Makes Debugging Look Random

**What happens:** The flow appears to run unpredictably because it fires on unrelated updates and collides with other automations.

**When it occurs:** Start conditions are set to run on every update without field-specific logic or prior-value checks.

**How to avoid:** Use explicit criteria and changed-field logic wherever the business event is narrower than "any save."

---

## Flow And Apex Still Share The Same Object Lifecycle

**What happens:** Admins design a record-triggered flow as if it owns the object, but an Apex trigger or validation rule changes the outcome.

**When it occurs:** Mixed-automation orgs with declarative and programmatic logic on the same object.

**How to avoid:** Review record-triggered flows alongside order-of-execution neighbors instead of in isolation.

---

## `$Record__Prior` Only Helps If The Logic Actually Uses It

**What happens:** A flow is configured to run on update, but it does not compare the old and new value of the important field.

**When it occurs:** Teams rely on broad start criteria and forget to encode the real business transition.

**How to avoid:** Use prior-value comparisons or equivalent start logic whenever the requirement depends on a field changing, not merely being present.
