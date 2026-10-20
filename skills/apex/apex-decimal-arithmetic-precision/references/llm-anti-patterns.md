# LLM Anti-Patterns — Apex Decimal Arithmetic Precision

Common mistakes AI coding assistants make when generating or advising on Apex Decimal arithmetic.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: One-argument `divide()` in generated code

**What the LLM generates:** Apex that divides Decimals using a single-argument `divide`, often because Java/C#/Python examples in the training data use a single-argument division method. The Decimal class has no such overload (apexref 262 L212672-212677), so the code does not compile.

```apex
// WRONG — no one-argument divide exists
Decimal share = total.divide(parts);
```

**Why it happens:** LLMs treat `divide` as analogous to Java's `BigDecimal.divide(BigDecimal)`. Apex exposes only the scale-taking overloads.

**Correct pattern:**

```apex
Decimal share = total.divide(parts, 6, System.RoundingMode.HALF_EVEN);
```

**Detection hint:** Grep for `\.divide\(` and inspect the argument count. Any `divide(x)` with no top-level comma will not compile; a two-argument call leaves the rounding mode unstated.

---

## Anti-Pattern 2: Integer literals on both sides of a fraction

**What the LLM generates:** Code that expects fractional behavior from `Integer / Integer`, often because the surrounding language (Python 3, Kotlin) auto-promotes Integer division to Float.

```apex
// WRONG — taxRate is Integer, 100 is Integer, result is 0
Integer taxRate = 7;
Decimal effective = price * (taxRate / 100);
```

**Why it happens:** Most modern languages outside Java/C# have abandoned C-style truncating Integer division. LLMs blend the conventions and forget that Apex inherits Java's behavior.

**Correct pattern:**

```apex
Integer taxRate = 7;
Decimal effective = price * (Decimal.valueOf(taxRate) / 100);
// Or:
Decimal effective = (price * taxRate).divide(100, 6, System.RoundingMode.HALF_EVEN);  // Decimal has no multiply()
```

**Detection hint:** Look for any binary `/` where both operands are Integer-typed and the result is assigned to a Decimal. The Apex compiler will not warn.

---

## Anti-Pattern 3: `Decimal.valueOf(double)` for parsed JSON values

**What the LLM generates:** Apex that reads `Object` values from `JSON.deserializeUntyped()` (UNVERIFIED (2026-10-20): that it produces Doubles for numbers) and converts via `Decimal.valueOf((Double) raw)`, expecting a clean conversion.

```apex
// WRONG — money routed through a Double (binary-float noise is UNVERIFIED; the habit is the point)
Map<String,Object> body = (Map<String,Object>) JSON.deserializeUntyped(payload);
Decimal amount = Decimal.valueOf((Double) body.get('amount'));
```

**Why it happens:** The training data treats `Decimal.valueOf` as a generic conversion. The Double overload exists (apexref 262 L212716-212717) and the call compiles, so LLMs accept it. UNVERIFIED (2026-10-20): that it adds binary-float noise; the safe habit stands.

**Correct pattern:**

Use the typed JSON parser:

```apex
JSONParser p = JSON.createParser(payload);
while (p.nextToken() != null) {
    if (p.getCurrentName() == 'amount' && p.nextValue() == JSONToken.VALUE_NUMBER_FLOAT) {
        Decimal amount = p.getDecimalValue();  // never via Double
    }
}
```

Or, if you must use untyped: convert via String — `Decimal.valueOf(String.valueOf(body.get('amount')))`.

**Detection hint:** Grep for `Decimal\.valueOf\([^'"]` — any non-String argument (no quote) is suspect. Inspect typed casts to `Double` near JSON parsing.

---

## Anti-Pattern 4: Comparing or keying Decimals without normalising scale

**What the LLM generates:** Reconciliation or assertion code that compares two Decimals using `.equals()`, expecting numeric-value comparison.

```apex
// WRONG — false when scales differ
System.assert(expectedTotal.equals(actualTotal));  // 1.50 vs 1.5 → false
```

**Why it happens:** LLMs default to `.equals()` for object equality. UNVERIFIED (2026-10-20): that Decimal's `.equals()` is scale-strict and `==` value-equal. What the guide does say is that numerically equal Decimals with different scale generally have different hashcodes (apex dev guide 264 L1244-1246).

**Correct pattern:**

```apex
// normalise scale first, then compare:
System.assert(
    expectedTotal.setScale(2, System.RoundingMode.HALF_EVEN)
        .equals(actualTotal.setScale(2, System.RoundingMode.HALF_EVEN))
);
```

**Detection hint:** Grep for `\.equals\(` on Decimal values. Most uses are unintentional.

---

## Anti-Pattern 5: Misdescribing what single-argument `setScale(n)` does

**What the LLM generates:** Code that calls `setScale(2)` (single-arg) and writes a comment about "HALF_UP rounding for currency" or "throws if rounding is needed". The guide says `setScale(scale)` rounds "using half-even rounding, if necessary" (apexref 262 L212707-212709).

```apex
// WRONG comment — single-arg setScale does not throw; it rounds half-even
Decimal stored = computed.setScale(2);  // 1.005 is rounded, not rejected
```

**Why it happens:** Java's `BigDecimal.setScale(int)` uses `UNNECESSARY` (throws on rounding); Apex's overload does not. LLMs carry the Java behaviour across, or treat it as truncation.

**Correct pattern:**

```apex
Decimal stored = computed.setScale(2, System.RoundingMode.HALF_EVEN);
```

**Detection hint:** Grep for `setScale\(\s*\d+\s*\)` — a single integer argument rounds half-even implicitly. Always pair with a `RoundingMode` so the policy is written down.
