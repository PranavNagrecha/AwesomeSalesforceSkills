# DataRaptor Transform Optimization — Gotchas

## 1. Bulk Mode Is Opt-In

The designer default varies across versions. Always verify in the exported JSON that `isBulk` or equivalent is true for array inputs.

## 2. Apex Expressions Use Parent IP's Limits

SOQL and DML issued inside a Transform's Apex expression count against the calling Apex or IP context. A chatty Transform can push the parent over limits.

## 3. JavaScript Evaluator Is Stateless Per Row

No memoization across rows. If you computed something expensive row 1, row 2 computes it again.

## 4. Formula Errors Produce Empty Values

A formula that references a missing field emits an empty string or null — not an exception. Downstream code often treats these as legitimate.

## 5. Chained Transforms Materialize Intermediate JSON

Each Transform in a chain produces a full intermediate array. Large arrays can push heap use; merging chains saves memory too.
