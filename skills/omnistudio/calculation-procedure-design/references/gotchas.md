# Calculation Procedure — Gotchas

## 1. Overlapping Ranges Produce Silent Wrong Answers

Two rows with overlapping age ranges do not error — one wins, and the
answer may be wrong forever. Enforce non-overlap in review.

## 2. Missing Row Fallback Is Not Automatic

If no row matches and no wildcard fallback exists, the procedure returns
null for the output, and downstream steps fail cryptically. Always
include a wildcard row or explicit raise.

## 3. Editing An Active Matrix Breaks Quotes In Flight

Activated matrix edits apply immediately to new invocations but leave
in-flight quotes using stale data. Publish a new version and activate,
do not edit rows on an active version.

## 4. Aggregation Requires List Input

Aggregation steps operate on a named list in the procedure input.
Passing a scalar silently aggregates a list of length one. Validate
shapes in the calling Integration Procedure.

## 5. Test Mode Does Not Validate Schema

Test mode runs with whatever keys you pass. A renamed input will not
error — it will simply not match any row. Keep fixtures current.

## 6. Caching The Procedure Output Is On You

Calculation Procedure results are not cached automatically. Wrap in a
cacheable Integration Procedure if you need to memoize.

## 7. Matrix Version Activation Is Per-Matrix

Activating a new version of Matrix A does not auto-activate a referenced
Matrix B. Coordinate activations, or the procedure runs with a mixed
version set.

## 8. Expression Set Error Messages Are Thin

Expression syntax errors point to the expression, not to the row or
input that triggered the failure. Keep expressions small and named.
