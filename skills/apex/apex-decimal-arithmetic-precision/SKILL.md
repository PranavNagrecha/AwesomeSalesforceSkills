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
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-05-07
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

## Core Concepts

### Apex Decimal is fixed-precision, scale-tracking

Apex's `Decimal` type is a fixed-point decimal — internally a Java `BigDecimal`. Every Decimal value carries a *scale* (number of digits after the decimal point). Scale is preserved through addition, subtraction, and multiplication. Division is the operation where Apex *requires* you to declare what scale the result should have, because most divisions don't terminate in finite digits.

A Decimal literal in Apex source picks up its scale from how you wrote it:

- `1.5` — scale 1
- `1.50` — scale 2
- `1` — Integer (no scale, not Decimal)
- `1.0` — Decimal, scale 1

Once the value is in a Decimal variable, scale is "sticky" across arithmetic in predictable ways:

- `Decimal a = 1.50; Decimal b = 1.5; Decimal c = a + b;` → `c` is `3.00` (scale 2, the larger of the two)
- `Decimal d = 1.25 * 1.0;` → `d` is `1.250` (scale = sum of operand scales for multiply)
- `Integer e = 10 / 4;` → `e == 2` (Integer / Integer truncates). The compiler does not warn.

### Division requires `divide(divisor, scale, roundingMode)` for non-terminating results

`Decimal.divide(Decimal divisor)` (single-argument) throws `System.MathException: Division does not result in an exact result, set scale and rounding mode for an inexact result` when the result has more digits than the result's natural scale can hold. `1.0 / 3` blows up; `1.0 / 4 == 0.25` works.

Always prefer the three-argument form for any production calculation:

```apex
Decimal result = numerator.divide(denominator, 4, System.RoundingMode.HALF_UP);
```

The two-argument `divide(divisor, scale)` exists but uses `HALF_EVEN` (banker's rounding) silently — fine if that's what you want, dangerous if you assumed `HALF_UP`.

### Rounding modes that matter

| Mode | Behavior | Use for |
|---|---|---|
| `HALF_UP` | 0.5 rounds away from zero | Retail prices, most user-facing money |
| `HALF_EVEN` (banker's) | 0.5 rounds to even neighbor | Tax, GAAP/IFRS reporting, statistics |
| `HALF_DOWN` | 0.5 rounds toward zero | Rare; specific contractual rounding |
| `UP` / `DOWN` | Always away / toward zero | Truncation; commission caps |
| `CEILING` / `FLOOR` | Always up / down (signed) | Inventory ceiling, never-overcharge |
| `UNNECESSARY` | Throws if rounding actually needed | Use to prove no rounding loss occurred |

The platform's currency-field UI uses `HALF_EVEN` for display rounding. If your Apex uses `HALF_UP` and writes to a Currency field, the value persists as you wrote it but a downstream formula that re-rounds via the platform may shift it back. Match the rounding mode end-to-end or accept the difference.

### Scale of currency, percent, and number fields

- Standard `Currency` fields: scale 2 (or more in multi-currency orgs after Dated Exchange Rate conversion — the stored value retains source scale).
- Custom `Number(length, decimal)`: scale = `decimal`.
- Custom `Percent(length, decimal)`: scale = `decimal`. Stored as the displayed value (5.25% → `5.25`, not `0.0525`).

When you write a higher-scale Decimal into a field with smaller scale, the platform truncates **without an explicit rounding mode** at the DML boundary. To control rounding, call `setScale(fieldScale, RoundingMode.X)` *before* assignment.

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

Notes: intermediate `tax` carries scale 6 to avoid double-rounding; the outer `setScale(2, HALF_EVEN)` aligns to the currency-field display behavior; `qty` (Integer) is implicitly promoted by `unitPrice * qty` because `unitPrice` is already Decimal.

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
| Storing into a currency field | `setScale(2, HALF_EVEN)` before DML | Matches platform display rounding |
| User-visible price (retail) | `setScale(2, HALF_UP)` | Matches consumer expectation |
| Tax calculation | `HALF_EVEN` | Required by most tax authorities; defensible in audit |
| Cumulative average / weighted avg | Carry scale 6+ in intermediates, round at end | Avoid double-rounding error compounding |
| `1 / 3`-style division | Three-arg `divide(d, scale, mode)` | One-arg form throws on non-terminating |
| Equality compare | Round both sides to same scale first | `1.50 == 1.5` is **true** in Apex but `Decimal.valueOf('1.50').equals(1.5)` is **false** |

---

## Recommended Workflow

1. Identify every division in the calculation. For each, decide the result scale and rounding mode based on the destination field — write them down before writing code.
2. Identify every Integer literal (`1`, `100`, `qty`) being divided or multiplied. If the operation could produce a fraction, change the literal to a Decimal (`1.0`, `100.0`) or wrap with `Decimal.valueOf()`.
3. Carry intermediates at scale ≥ 4 even when the final answer is scale 2. Round only at the boundary (UI display, DML write, contract output).
4. Replace any one-argument `divide(d)` with the three-argument form. Search the codebase for `\.divide\([^,]+\)` to find single-arg divides.
5. Add tests for the boundary cases: zero divisor (expect `MathException`), exact-terminating divide (`1.00 / 4`), repeating divide (`1.00 / 3`), half-way value with both `HALF_UP` and `HALF_EVEN` to confirm the chosen mode.
6. If the calculation feeds a Currency field, write a final `setScale(2, HALF_EVEN)` and confirm the stored value matches a hand calculation.
7. Where the calculation is reused, lift it into a `LineItemCalc`-style stateless utility class with a single rounding-mode parameter so the policy is one place, not seven.

---

## Review Checklist

- Every `divide()` call uses the three-argument form (or there is an inline comment explaining why one-arg is safe — e.g. divisor is a literal power of 2).
- Every Integer-typed operand in a fraction-producing operation is either deliberately Integer (count, index) or has been promoted to Decimal.
- Final scale matches the destination field's scale; intermediate scale is at least 2 higher than final.
- The chosen rounding mode is `HALF_EVEN` for tax/financial reporting, `HALF_UP` for consumer-visible prices, or has a comment explaining the deviation.
- Splitting / allocation logic uses the residual-on-last-item pattern; tests assert sum-equals-total to the cent.
- Equality comparisons round both sides to the same scale before comparing, OR use `==` (value-equal) deliberately rather than `.equals()` (scale-equal).

---

## Salesforce-Specific Gotchas

| Gotcha | Behavior |
|---|---|
| Currency fields in multi-currency orgs | `Decimal` reads from a Currency field carry the *record's* currency, not the user's. Apex doesn't auto-convert; use `UserInfo.getDefaultCurrency()` and the `DatedConversionRate` SObject if conversion is needed. |
| `Decimal.valueOf(Double)` | Passes through Java double's binary float, reintroducing `0.1 + 0.2 = 0.30000000000000004` errors. Use `Decimal.valueOf(String)` or a Decimal literal. |
| Aggregate query types | `SUM(Amount__c)` returns Decimal in Apex but `AVG()` always returns scale 6 regardless of source field. Round explicitly when consuming. |
| Formula-field evaluation | Cross-object formulas evaluate at platform-level with `HALF_EVEN`; if Apex pre-computed the same value with `HALF_UP`, expect a 1-cent shift. |
| `==` vs `.equals()` | Apex `==` on Decimal is value-equal (`1.50 == 1.5` is `true`); `.equals()` is scale-strict. Use `==` for "same number" semantics. |

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
