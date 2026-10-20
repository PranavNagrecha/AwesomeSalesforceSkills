---
name: apex-decimal-arithmetic-precision
description: "Use when Apex code performs arithmetic on currency, tax, percentage, or quantity values and the result is wrong by a cent, a penny, or a fraction — Decimal scale collapses to 0 after divide, totals don't match the sum-of-line-items, currency-field rounding differs from in-app calculation, or `divide()` throws on a non-existent rounding mode. Triggers: 'apex decimal divide rounded wrong', 'currency calculation off by a penny', 'apex setScale rounding mode', 'integer divided by integer truncated to zero', 'apex Decimal precision lost'. NOT for dated exchange rates — use data/multi-currency-and-advanced-currency-management. NOT for Flow formula rounding — use flow/flow-formula-and-expression-patterns. NOT for SOQL aggregate queries — use apex/apex-aggregate-queries."
category: apex
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Security
triggers:
  - "apex decimal divide returning wrong number of decimal places"
  - "apex currency calculation off by a penny rounding"
  - "apex integer divided by integer truncated zero result"
  - "apex setScale rounding mode argument required"
  - "apex sum of line items does not match header total"
  - "apex Decimal precision scale lost after arithmetic"
tags:
  - apex
  - decimal
  - rounding
  - currency
  - arithmetic
  - precision
inputs:
  - "the Apex calculation in question and the expected vs actual result"
  - "the field metadata (length, decimal places, currency code) of any SObject fields involved"
  - "whether the result is displayed in the UI, written to a currency field, or compared in an equality check"
outputs:
  - "corrected Apex with explicit `setScale(scale, RoundingMode)` calls and Decimal-typed literals"
  - "test data covering the boundary cases (terminating, repeating, half-way, divide-by-zero)"
  - "rounding-mode decision aligned with the business rule (banker's rounding for tax, HALF_UP for retail price)"
dependencies: []
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-10-20
---

# Apex Decimal Arithmetic Precision

Activate when an Apex calculation produces a value that is wrong by a cent, by a fraction, or — more dangerously — looks correct in unit tests but disagrees with a hand-totalled spreadsheet by enough to fail an audit. The skill resolves the calculation by giving Decimal an explicit scale and rounding mode at every step where rounding can occur, separating the "calculate" path from the "store" path, and matching Apex's behavior to the platform's currency-field behavior.

---

## Before Starting

Gather this context before working on anything in this domain:

- The calculation in plain language: what's the formula, and what is the expected output for one or two specific input rows. "Tax = subtotal × rate, rounded to 2 places, banker's rounding" is enough.
- The Decimal *destination*: a currency field with 2 decimal places, a percent field with 4, a number(18,6), or a transient variable. The destination dictates the final scale; intermediates should generally carry more.
- Whether any of the operands could be a literal `1` or `100` (Integer) rather than `1.0` or `100.0` (Decimal). This is the most common source of "the result truncated to 0" reports.

---

## Questions to Ask Before Configuring

Each question traces to a gotcha in `references/gotchas.md`.

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "Which `divide` overload does the code call, and does it name a rounding mode?" | Only the two- and three-argument forms exist; the two-argument mode is not documented (gotcha 1) | A rounding mode written at every division |
| "Are both operands of any fraction Integers?" | Integer division truncation is the usual cause of a result of 0 (gotcha 2) | Decimal-typed operands or an explicit `Decimal.valueOf` |
| "Does money pass through a Double, for example from JSON?" | A Decimal made from a Double is first converted to a String and takes its scale from it; what that String holds for a binary fraction is not documented (gotcha 3) | `JSONParser.getDecimalValue()` or the String overload |
| "Are Decimals compared or used as Set/Map keys?" | Equal numbers at different scale generally hash differently (gotcha 4) | One scale applied before comparing or keying |
| "Does the code consume an aggregate result?" | An aggregate's scale is not documented (gotcha 5) | An explicit `setScale` on the value read from `AggregateResult` |
| "What is the destination field's scale, and which mode should reach it?" | The platform's rounding at the DML boundary is not documented (gotcha 6) | `setScale(fieldScale, mode)` before assignment |
| "Does Flow or a formula compute the same figure?" | Cross-engine rounding agreement is unproven (gotcha 6) | A written decision on which engine owns the figure |

A proper configuration adds one stated scale and rounding mode per division and one boundary rounding per write, where "just doing it" gives a total that is a cent off in production only.

---

## Core Concepts

### Apex Decimal is fixed-precision, scale-tracking

Apex's `Decimal` is "an arbitrary precision number" and currency fields are typed Decimal (apex dev guide 264 L1224-1225). Every Decimal has a *scale* — "a count of decimal places" — set by what it is created from: the field's scale for a query, the number of characters after the decimal point for a String, and a non-decimal number is first converted to a String (L1226-1243). UNVERIFIED (2026-10-20): that it is internally a Java `BigDecimal`, and how scale combines through addition, subtraction and multiplication. The Decimal class offers exactly two divide overloads, `divide(divisor, scale)` and `divide(divisor, scale, roundingMode)` (apexref 262 L212672-212677); the scale is something you always state.

A Decimal literal in Apex source picks up its scale from the digits you wrote after the point — the reference example `Decimal myDecimal = 9.27400968;` has `scale()` 8 (apexref 262 L213029-213030):

- `1.5` — scale 1
- `1.50` — scale 2
- `1` — Integer (no scale, not Decimal)
- `1.0` — Decimal, scale 1

Once the value is in a Decimal variable, scale is "sticky" across arithmetic (UNVERIFIED (2026-10-20): every scale rule in the next three bullets, and the Integer-division result — the corpus states only how scale is assigned at creation, L1226-1243):

- `Decimal a = 1.50; Decimal b = 1.5; Decimal c = a + b;` → `c` is `3.00` (scale 2, the larger of the two)
- `Decimal d = 1.25 * 1.0;` → `d` is `1.250` (scale = sum of operand scales for multiply)
- `Integer e = 10 / 4;` → `e == 2` (Integer / Integer truncates). The compiler does not warn.

### Division takes a scale, and a rounding mode when you want to choose it

The Decimal class has no one-argument `divide(Decimal)`: the method list holds only `divide(divisor, scale)` and `divide(divisor, scale, roundingMode)` (apexref 262 L212672-212677). The earlier text described a one-argument form throwing `System.MathException: Division does not result in an exact result…` — CONTRADICTED by that list, and the message text is UNVERIFIED (2026-10-20). The guide's example is `decimalNumber.divide(100, 3)` on `19` giving `0.190` (L212769-212771).

Always prefer the three-argument form for any production calculation:

```apex
Decimal result = numerator.divide(denominator, 4, System.RoundingMode.HALF_UP);
```

The two-argument `divide(divisor, scale)` exists, but UNVERIFIED (2026-10-20): which rounding mode it applies when the result is inexact — the guide says only that it "sets the scale" (L212743-212744). Name the mode instead of relying on it.

### Rounding modes that matter

| Mode | Behavior | Use for |
|---|---|---|
| `HALF_UP` | 0.5 rounds away from zero | Retail prices, most user-facing money (UNVERIFIED (2026-10-20): the retail and tax-authority use cases are business convention, not corpus) |
| `HALF_EVEN` (banker's) | 0.5 rounds to even neighbor; "statistically minimizes cumulative error" (apexref 262 L212576-212600) | Tax, GAAP/IFRS reporting, statistics |
| `HALF_DOWN` | 0.5 rounds toward zero | Rare; specific contractual rounding |
| `UP` / `DOWN` | Always away / toward zero | Truncation; commission caps |
| `CEILING` / `FLOOR` | Always up / down (signed) | Inventory ceiling, never-overcharge |
| `UNNECESSARY` | Throws if rounding actually needed | Use to prove no rounding loss occurred |

UNVERIFIED (2026-10-20): that the platform's currency-field UI and formulas round `HALF_EVEN`. The corpus confirms that `setScale(scale)` and `round()` use half-even (apexref 262 L212707-212709, L212690-212693); nothing states what the UI or a formula does. Match the rounding mode end-to-end or accept the difference.

### Scale of currency, percent, and number fields

A Decimal read by a query takes the scale of the field returned (apex dev guide 264 L1229-1230). UNVERIFIED (2026-10-20): the scale of standard Currency fields, the multi-currency behaviour, the Percent storage convention (5.25% stored as `5.25`), and what the platform does when a higher-scale Decimal is written to a smaller-scale field (the earlier "truncates" here and "rounds HALF_EVEN" in gotcha 6 disagree with each other). To control rounding, call `setScale(fieldScale, RoundingMode.X)` *before* assignment.

---

## Common Patterns

### Calculating a line-item total with tax

```apex
public class LineItemCalc {
    public static Decimal totalWithTax(Decimal unitPrice, Integer qty, Decimal taxRatePercent) {
        // Force Decimal arithmetic — qty alone is Integer.
        Decimal subtotal = unitPrice * qty;
        Decimal tax = (subtotal * taxRatePercent).divide(100, 6, System.RoundingMode.HALF_EVEN);
        Decimal total = (subtotal + tax).setScale(2, System.RoundingMode.HALF_EVEN);
        return total;
    }
}
```

Notes: intermediate `tax` carries scale 6 to avoid double-rounding; the outer `setScale(2, HALF_EVEN)` is the platform-default mode of `setScale` (apexref 262 L212707-212709; UNVERIFIED (2026-10-20): that it matches currency display); `qty` (Integer) is multiplied with the Decimal `unitPrice` (UNVERIFIED (2026-10-20): the implicit promotion rule).

### Splitting a total across allocations without rounding drift

The classic trap: `total / N` rounded to 2 places, then summed back, drifts by `0.01 × (rounding-direction × N)`. Fix by allocating cumulatively and assigning the residual to the last item:

```apex
public static List<Decimal> allocate(Decimal total, Integer parts) {
    List<Decimal> out = new List<Decimal>();
    Decimal each = total.divide(parts, 2, System.RoundingMode.HALF_DOWN);
    Decimal running = 0;
    for (Integer i = 0; i < parts - 1; i++) {
        out.add(each);
        running += each;
    }
    out.add((total - running).setScale(2, System.RoundingMode.HALF_UP));
    return out;
}
```

The list always sums *exactly* to `total`. Useful for revenue allocation, invoice splits, and percentage-of-total reporting.

---

## Decision Guidance

| Situation | Choice | Rationale |
|---|---|---|
| Storing into a currency field | `setScale(2, HALF_EVEN)` before DML | `setScale` defaults to half-even too (apexref 262 L212707-212709); that the platform display matches is UNVERIFIED (2026-10-20) |
| User-visible price (retail) | `setScale(2, HALF_UP)` | Matches consumer expectation |
| Tax calculation | `HALF_EVEN` | Defensible in audit (UNVERIFIED (2026-10-20): "required by most tax authorities" is a business claim) |
| Cumulative average / weighted avg | Carry scale 6+ in intermediates, round at end | Avoid double-rounding error compounding |
| `1 / 3`-style division | Three-arg `divide(d, scale, mode)` | The mode is stated, not implied; there is no one-arg `divide` |
| Equality compare | Round both sides to same scale first | Equal numbers at different scale "generally don't have the same hashcode" (apex dev guide 264 L1244-1246), so normalise scale before using Decimals as Set/Map keys; UNVERIFIED (2026-10-20): the `==` vs `.equals()` results |

---

## Recommended Workflow

1. Identify every division in the calculation. For each, decide the result scale and rounding mode based on the destination field — write them down before writing code.
2. Identify every Integer literal (`1`, `100`, `qty`) being divided or multiplied. If the operation could produce a fraction, change the literal to a Decimal (`1.0`, `100.0`) or wrap with `Decimal.valueOf()`.
3. Carry intermediates at scale ≥ 4 even when the final answer is scale 2. Round only at the boundary (UI display, DML write, contract output).
4. Replace any two-argument `divide(d, scale)` with the three-argument form so the rounding mode is stated. Search the codebase for `\.divide\([^,]+,[^,]+\)` to find two-argument divides; a one-argument `divide(d)` does not exist and will not compile.
5. Add tests for the boundary cases: zero divisor (UNVERIFIED (2026-10-20): the exception type — assert on the type your test observes), exact-terminating divide (`1.00 / 4`), repeating divide (`1.00 / 3`), half-way value with both `HALF_UP` and `HALF_EVEN` to confirm the chosen mode.
6. If the calculation feeds a Currency field, write a final `setScale(2, HALF_EVEN)` and confirm the stored value matches a hand calculation.
7. Where the calculation is reused, lift it into a `LineItemCalc`-style stateless utility class with a single rounding-mode parameter so the policy is one place, not seven.

---

## Review Checklist

- Every `divide()` call uses the three-argument form (or an inline comment explains why the unstated rounding mode of the two-argument form is acceptable).
- Every Integer-typed operand in a fraction-producing operation is either deliberately Integer (count, index) or has been promoted to Decimal.
- Final scale matches the destination field's scale; intermediate scale is at least 2 higher than final.
- The chosen rounding mode is `HALF_EVEN` for tax/financial reporting, `HALF_UP` for consumer-visible prices, or has a comment explaining the deviation.
- Splitting / allocation logic uses the residual-on-last-item pattern; tests assert sum-equals-total to the cent.
- Equality comparisons and Set/Map keys round both sides to the same scale first (UNVERIFIED (2026-10-20): whether `==` or `.equals()` is value-equal or scale-equal).

---

## Salesforce-Specific Gotchas

| Gotcha | Behavior |
|---|---|
| Currency fields in multi-currency orgs | `UserInfo.getDefaultCurrency()` exists (apexref 262 L243152) and `DatedConversionRate` is an object (object_reference 264 L7778). UNVERIFIED (2026-10-20): that a Decimal read from a Currency field carries the record's currency and that Apex never auto-converts. |
| `Decimal.valueOf(Double)` | The guide says a Decimal made from a non-decimal number is first converted to a String and takes its scale from it (apex dev guide 264 L1242-1243), which does not support the earlier "binary float noise" claim. UNVERIFIED (2026-10-20): that `valueOf(Double)` reintroduces `0.30000000000000004`-style errors. Using `Decimal.valueOf(String)` or `JSONParser.getDecimalValue()` (apexref 262 L219544) is still the safe habit. |
| Aggregate query types | An aggregate query returns `AggregateResult` rows (apex dev guide 264 L9699-9700). UNVERIFIED (2026-10-20): that `SUM` returns Decimal and `AVG()` always returns scale 6. Round explicitly when consuming. |
| Formula-field evaluation | UNVERIFIED (2026-10-20): that formulas evaluate with `HALF_EVEN`; if Apex pre-computed the same value with a different mode, expect a possible 1-cent shift. |
| `==` vs `.equals()` | UNVERIFIED (2026-10-20): that `==` on Decimal is value-equal and `.equals()` scale-strict. The corpus confirms only the hashcode caveat (apex dev guide 264 L1244-1246). |

---

## Output Artifacts

- Corrected Apex utility class with explicit `setScale(scale, RoundingMode)` calls at every rounding point.
- Apex test class with parameterized test for: terminating divide, repeating divide, half-way value with chosen mode, zero divisor, large-N allocation summing exactly to total.
- One-paragraph design note: "this calculation uses HALF_EVEN at scale 2 to match the platform's currency-field display behavior" — kept with the class so the next developer doesn't switch modes accidentally.

---

## Related Skills

- `apex/apex-aggregate-queries` — `SUM` and `AVG` return type quirks.
- `data/multi-currency-and-advanced-currency-management` — Dated Exchange Rates and per-record currency.
- `apex/fsc-financial-calculations` — domain-specific (TWR/IRR) financial math built on top of the Decimal primitives covered here.
- `flow/flow-formula-and-expression-patterns` — Flow's formula engine has its own rounding rules; the gap between Flow and Apex causes the most "Apex says X, Flow says Y" tickets.
