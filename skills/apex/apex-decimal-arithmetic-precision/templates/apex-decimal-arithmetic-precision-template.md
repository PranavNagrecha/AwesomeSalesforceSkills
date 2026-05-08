# Apex Decimal Arithmetic Precision — Work Template

Use this template when working on tasks in this area.

## Scope

**Skill:** `apex-decimal-arithmetic-precision`

**Request summary:** (fill in what the user asked for)

## Context Gathered

- The calculation in plain English (formula, expected output for 1–2 sample rows):
- Destination type and scale (Currency(16,2), Number(18,6), Percent(5,4), transient):
- Whether any operand is an Integer literal (`1`, `100`, `qty`):
- Source of inputs (user form, API response, JSON parse, SOQL aggregate):
- Rounding-mode requirement (HALF_UP retail, HALF_EVEN tax, contractual other):

## Approach

- [ ] Centralize rounding policy in a single utility class (one `RoundingMode` argument)
- [ ] Carry intermediates at scale ≥ destination + 2
- [ ] Use three-arg `divide(divisor, scale, RoundingMode)` for every divide
- [ ] Use `setScale(n, RoundingMode)` before any DML write to a scale-bound field
- [ ] Replace any `Decimal.valueOf(Double)` with String overload or `JSONParser.getDecimalValue()`

## Review Checklist

- [ ] Every `divide()` is three-argument (or has an inline justification comment)
- [ ] No Integer/Integer division feeds a Decimal-typed result
- [ ] Final scale matches the destination field; intermediate scale is at least 2 higher
- [ ] Rounding mode aligns with the documented business rule (and the design note says so)
- [ ] Allocation/split logic uses residual-on-last-item; tests assert sum == header
- [ ] Equality compares use `==` for "same number" or `setScale()` before `.equals()`
- [ ] Tests cover terminating, repeating, half-way, and zero-divisor cases

## Notes

Record any deviations from the standard pattern (e.g. matching an external system's
HALF_UP requirement when the platform default is HALF_EVEN) and the reason.
