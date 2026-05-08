# Gotchas — Apex Decimal Arithmetic Precision

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: One-argument `divide()` throws on non-terminating results

**What happens:** `someDecimal.divide(3)` works fine for `9.0 / 3` but throws `System.MathException: Division does not result in an exact result, set scale and rounding mode for an inexact result` for `1.0 / 3`. The error message is clear; the surprise is that the same call site sometimes works and sometimes throws depending on input data.

**When it occurs:** Any code path where the divisor isn't a guaranteed power of 2/5 of the numerator's last digit. In practice: most production divisions where inputs come from user data or external systems.

**How to avoid:** Treat single-arg `divide()` as a code smell. Always use `divide(divisor, scale, RoundingMode)`. If you need to assert "this divide should never need rounding," use `divide(divisor, scale, RoundingMode.UNNECESSARY)` — that throws if rounding actually occurs, which is what you want for that assertion.

---

## Gotcha 2: Integer-divided-by-Integer truncates without warning

**What happens:** `Integer a = 10, b = 4; Decimal c = a / b;` assigns `c = 2`, not `2.5`. Apex evaluates `a / b` as Integer division (truncation) *before* implicit promotion to Decimal at assignment.

**When it occurs:** Any time you write `someInteger / anotherInteger` expecting a fractional result. Especially common with `someList.size() / 2` for "halfway through" or `daysOpen / 30.0` style code where one side is forgotten.

**How to avoid:** Promote at least one operand explicitly: `Decimal.valueOf(a) / b`, or `(Decimal) a / b`, or use a `1.0 *` prefix. Or store the field as Decimal in the first place. The Apex compiler will not warn.

---

## Gotcha 3: `Decimal.valueOf(Double)` reintroduces binary-float noise

**What happens:** `Decimal.valueOf(0.1)` produces a Decimal with the value `0.1000000000000000055511151231257827021181583404541015625`. The `.toString()` shows the noise. Subsequent `setScale(2, ...)` rounds it back to `0.10`, but any intermediate comparison, hash, or persistence sees the noisy value.

**When it occurs:** Most often when consuming JSON parsed via `JSON.deserializeUntyped()` — JSON numbers come back as Doubles by default. Also when integrating with libraries that hand back Doubles.

**How to avoid:** When parsing JSON that contains money/quantity values, use `JSON.createParser()` and call `getDecimalValue()` at the number tokens — that bypasses Double entirely. When in doubt, convert via String: `Decimal.valueOf(String.valueOf(myDouble))` (lossless across the round trip if the Double was originally derived from a decimal literal).

---

## Gotcha 4: `Decimal.equals()` is scale-strict, `==` is value-equal

**What happens:** `Decimal.valueOf('1.50').equals(Decimal.valueOf('1.5'))` returns `false` even though the numeric values are equal. `Decimal.valueOf('1.50') == Decimal.valueOf('1.5')` returns `true`. The two operators have different semantics.

**When it occurs:** When using Decimals as Map keys or Set elements (`.equals()` is what's used internally), the same numeric value at different scales produces different keys. Reconciliation code that uses `.equals()` for comparison reports false negatives across data sources with different scale conventions.

**How to avoid:** For Set/Map key use, normalize to a single scale before insertion: `key.setScale(2, HALF_EVEN)`. For equality compare, prefer `==` unless scale-equality is what you actually want. Document the choice with a comment if `.equals()` is deliberate.

---

## Gotcha 5: AVG aggregate-query result is scale 6 regardless of source field

**What happens:** A SOQL `SELECT AVG(Amount) FROM Opportunity` against a Currency(16,2) field returns Decimal at scale 6 in Apex (`123.456789`), not scale 2. `SUM` preserves the source-field scale. Code that assumes "the result has the same scale as the field" is wrong half the time.

**When it occurs:** Reporting Apex that consumes aggregate results and writes them back into a Currency field, or compares them against a hand-totalled scale-2 value.

**How to avoid:** Treat all AggregateResult numeric reads as untrusted-scale. Round explicitly: `Decimal avg = ((Decimal) ar.get('expr0')).setScale(2, RoundingMode.HALF_EVEN);`. Same for `MEDIAN`, `STDDEV`, and any other aggregate that involves division.

---

## Gotcha 6: Currency-field DML truncation is silent at scale-overflow

**What happens:** Assigning `acc.AnnualRevenue = 12345.6789;` to a Currency(16,0) field stores `12346` (rounded) without any error. The platform truncates with `HALF_EVEN` at the DML boundary. If the Apex code intended `HALF_UP`, the stored value differs from expectation.

**When it occurs:** Any time Apex computes at higher precision and writes to a field with smaller scale. Almost universal in tax/discount/exchange-rate code paths.

**How to avoid:** Always `setScale(field-scale, RoundingMode.X)` *before* the assignment, where `X` is the rounding mode you actually want. Don't rely on the platform's silent rounding — explicit code matches what your tests assert.
