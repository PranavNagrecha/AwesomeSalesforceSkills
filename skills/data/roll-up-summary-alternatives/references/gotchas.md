# Gotchas - Roll Up Summary Alternatives

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Backfill Jobs Are The Real Test

**What happens:** The summary logic behaves under normal edits but fails or slows badly during migration or data cleanup.

**When it occurs:** The design was tested only for one-record transactions.

**How to avoid:** Validate recalculation behavior at bulk volume before calling the pattern complete.

---

## Gotcha 2: Parent Contention Can Dominate

**What happens:** Many child changes compete to update the same parent summary field.

**When it occurs:** High-volume child writes converge on a small number of parent records.

**How to avoid:** Prefer recalculation-from-source patterns and be deliberate about lock concentration.

---

## Gotcha 3: Declarative Does Not Mean Free

**What happens:** Teams choose a tool or Flow path assuming no engineering ownership is needed.

**When it occurs:** Nobody plans for drift correction, failure handling, or recalculation utilities.

**How to avoid:** Assign explicit operational ownership for summary accuracy.
