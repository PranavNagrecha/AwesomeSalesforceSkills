# Gotchas — Apex Decimal Arithmetic Precision

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: There is no one-argument `divide()`, and the two-argument form hides its rounding mode

**What happens:** Generated code calls `someDecimal.divide(3)` and fails to compile, or a two-argument `divide(3, 2)` rounds in a mode nobody wrote down. The Decimal class lists exactly `divide(divisor, scale)` and `divide(divisor, scale, roundingMode)` (apexref 262 L212672-212677). The earlier text of this gotcha described a one-argument form throwing `System.MathException: Division does not result in an exact result…`; that was CONTRADICTED by the method list, and the message text is UNVERIFIED (2026-10-20).

**When it occurs:** Any division whose result does not terminate (`1.0 / 3`), and any code ported from Java's `BigDecimal.divide(BigDecimal)`.

**How to avoid:** Use `divide(divisor, scale, RoundingMode)` and name the mode. To assert that a divide never needs rounding, pass `System.RoundingMode.UNNECESSARY`, which "asserts that the requested operation has an exact result" and throws `MathException` otherwise (apexref 262 L212619-212622). UNVERIFIED (2026-10-20): the mode the two-argument form applies.

---

## Gotcha 2: Integer-divided-by-Integer truncates without warning

**What happens:** `Integer a = 10, b = 4; Decimal c = a / b;` assigns `c = 2`, not `2.5` (UNVERIFIED (2026-10-20): the corpus holds no Integer-division rule; Integer is "a 32-bit number that doesn't include a decimal point", apex dev guide 264 L1257-1258). The expectation is that `a / b` is evaluated as Integer division before the assignment promotes it.

**When it occurs:** Any time you write `someInteger / anotherInteger` expecting a fractional result. Especially common with `someList.size() / 2` for "halfway through" or `daysOpen / 30.0` style code where one side is forgotten.

**How to avoid:** Promote at least one operand explicitly: `Decimal.valueOf(a) / b`, or `(Decimal) a / b`, or use a `1.0 *` prefix. Or store the field as Decimal in the first place. The Apex compiler will not warn.

---

## Gotcha 3: Money that passes through a `Double` takes its scale from a String conversion

**What happens:** UNVERIFIED (2026-10-20): that `Decimal.valueOf(0.1)` produces `0.1000000000000000055511151231257827021181583404541015625`. The guide says a Decimal created from a non-decimal number is "first converted to a String" and takes its scale from the characters after the decimal point (apex dev guide 264 L1242-1243), which does not support the long binary tail; `valueOf(doubleToDecimal)` is described only as returning "a Decimal that contains the value of the specified Double" (apexref 262 L212716-212717).

**When it occurs:** Most often when consuming JSON parsed via `JSON.deserializeUntyped()` (UNVERIFIED (2026-10-20): that its numbers come back as Doubles). Also when integrating with libraries that hand back Doubles.

**How to avoid:** When parsing JSON that contains money/quantity values, use `JSON.createParser()` and call `getDecimalValue()` at the number tokens — it is valid on `VALUE_NUMBER_FLOAT` and `VALUE_NUMBER_INT` tokens (apexref 262 L219552-219553). When in doubt, convert via String: `Decimal.valueOf(String.valueOf(myDouble))` (lossless across the round trip if the Double was originally derived from a decimal literal).

---

## Gotcha 4: Equal numbers at different scales generally hash differently

**What happens:** The guide warns that "two Decimal objects that are numerically equivalent but differ in scale (such as 1.1 and 1.10) generally don't have the same hashcode" and to use caution in Sets and as Map keys (apex dev guide 264 L1244-1246; apexref 262 L212484-212485). UNVERIFIED (2026-10-20): that `.equals()` returns `false` for `1.50` vs `1.5` while `==` returns `true`.

**When it occurs:** When using Decimals as Map keys or Set elements, the same numeric value at different scales can produce different keys. Reconciliation code that compares across data sources with different scale conventions can report false negatives.

**How to avoid:** For Set/Map key use, normalize to a single scale before insertion: `key.setScale(2, HALF_EVEN)`. For equality compare, normalise both sides to one scale first and test the result in a unit test; the corpus does not state the semantics of `==` or `.equals()` on Decimal.

---

## Gotcha 5: Aggregate-query results have no documented scale

**What happens:** A SOQL `SELECT AVG(Amount) FROM Opportunity` returns its value in an `AggregateResult` row (apex dev guide 264 L9693-9700). UNVERIFIED (2026-10-20): that the value is a Decimal at scale 6 and that `SUM` preserves the source-field scale; the corpus states no scale for aggregates.

**When it occurs:** Reporting Apex that consumes aggregate results and writes them back into a Currency field, or compares them against a hand-totalled scale-2 value.

**How to avoid:** Treat all AggregateResult numeric reads as untrusted-scale. Round explicitly: `Decimal avg = ((Decimal) ar.get('expr0')).setScale(2, RoundingMode.HALF_EVEN);`. UNVERIFIED (2026-10-20): `MEDIAN` and `STDDEV` as SOQL aggregate functions — the corpus shows only `AVG()` in the Apex aggregate section.

---

## Gotcha 6: Writing a higher-scale Decimal to a Currency field has no documented rounding

**What happens:** UNVERIFIED (2026-10-20): that assigning `acc.AnnualRevenue = 12345.6789;` to a Currency(16,0) field stores `12346` without error, and that the platform applies `HALF_EVEN` at the DML boundary. SKILL.md's Core Concepts says "truncates" for the same case; the two statements disagree and the corpus holds neither. If the Apex code intended a specific mode, the stored value may differ from expectation.

**When it occurs:** Any time Apex computes at higher precision and writes to a field with smaller scale. Almost universal in tax/discount/exchange-rate code paths.

**How to avoid:** Always `setScale(field-scale, RoundingMode.X)` *before* the assignment, where `X` is the rounding mode you actually want. Don't rely on the platform's silent rounding — explicit code matches what your tests assert.
