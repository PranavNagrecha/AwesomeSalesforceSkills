# Gotchas — Decision Element

## 1. Null Silently Fails Equality

`{!F} = 'X'` evaluates to false when F is null. Not an error, not an
exception — just false. Any branch counting on "field is X or null
means X" will lose the null case.

## 2. Order Matters — First Match Wins

If outcome A includes outcome B as a subset, B must be listed first.
Otherwise B is dead code.

## 3. Label vs API Value For Pick-lists

Comparison uses the API value. Translation makes the label vary by
user; the API value does not.

## 4. Multi-Select Pick-list Uses `INCLUDES` / `EXCLUDES`

Not `=`. `{!Multi} = 'A;B'` only matches the exact serialised string in
that order. Use the operator.

## 5. Default Outcome Is Silent

Unnamed default absorbs every edge case. When a bug routes through the
default you have no audit trail of which condition failed.

## 6. Compound AND/OR Without Parentheses

Flow evaluates logic left-to-right when using the "Custom Condition
Logic" builder. `1 AND 2 OR 3` is **not** `1 AND (2 OR 3)`.

## 7. Formula Reference Recomputes

Every Decision outcome that references a formula recomputes it.
Expensive formulas (nested IFs, cross-object lookups) cost each time.

## 8. Rollup Fields In Before-Save Decision

Rollups are stale inside a before-save context. Decision outcomes that
branch on rollup value will branch on yesterday's number.
