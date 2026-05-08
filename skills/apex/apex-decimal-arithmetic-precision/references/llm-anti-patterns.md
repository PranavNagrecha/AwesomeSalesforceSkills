# LLM Anti-Patterns — Apex Decimal Arithmetic Precision

Common mistakes AI coding assistants make when generating or advising on Apex Decimal arithmetic.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: One-argument `divide()` in generated code

**What the LLM generates:** Apex that divides Decimals using the single-argument form, often because Java/C#/Python examples in the training data use a single-argument division operator.

```apex
// WRONG
Decimal share = total.divide(parts);  // throws on 1.0 / 3
```

**Why it happens:** LLMs treat `divide` as analogous to Java's `BigDecimal.divide(BigDecimal)`, but Apex's single-arg `divide(Decimal)` throws on non-terminating results — the Java equivalent does the same, but most production examples in training data use the result-scale-aware form indirectly via `MathContext`.

**Correct pattern:**

```apex
Decimal share = total.divide(parts, 6, System.RoundingMode.HALF_EVEN);
```

**Detection hint:** Grep for `\.divide\(` and inspect the argument count. Any `divide(x)` where `x` is a single expression (no commas at the top level) is suspect.

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
Decimal effective = price.multiply(taxRate).divide(100, 6, System.RoundingMode.HALF_EVEN);
```

**Detection hint:** Look for any binary `/` where both operands are Integer-typed and the result is assigned to a Decimal. The Apex compiler will not warn.

---

## Anti-Pattern 3: `Decimal.valueOf(double)` for parsed JSON values

**What the LLM generates:** Apex that reads `Object` values from `JSON.deserializeUntyped()` (which produces Doubles for numbers) and converts via `Decimal.valueOf((Double) raw)`, expecting a clean conversion.

```apex
// WRONG — reintroduces binary-float noise
Map<String,Object> body = (Map<String,Object>) JSON.deserializeUntyped(payload);
Decimal amount = Decimal.valueOf((Double) body.get('amount'));
```

**Why it happens:** The training data treats `Decimal.valueOf` as a generic conversion. The Double overload exists in the API and the call compiles, so LLMs accept it.

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

## Anti-Pattern 4: Comparing Decimals with `.equals()` for numeric equality

**What the LLM generates:** Reconciliation or assertion code that compares two Decimals using `.equals()`, expecting numeric-value comparison.

```apex
// WRONG — false when scales differ
System.assert(expectedTotal.equals(actualTotal));  // 1.50 vs 1.5 → false
```

**Why it happens:** LLMs default to `.equals()` for object equality (correct for most types), but Decimal's `.equals()` is scale-strict — it inherits Java's `BigDecimal.equals` semantics. The numeric-equal `==` behaves differently in Apex than in Java (Java `==` is reference-equal; Apex `==` on Decimal is value-equal).

**Correct pattern:**

```apex
// "same number" semantics:
System.assertEquals(expectedTotal, actualTotal);  // Apex Assert uses ==

// or scale-normalize first if you must use .equals:
System.assert(
    expectedTotal.setScale(2, System.RoundingMode.HALF_EVEN)
        .equals(actualTotal.setScale(2, System.RoundingMode.HALF_EVEN))
);
```

**Detection hint:** Grep for `\.equals\(` on Decimal values. Most uses are unintentional.

---

## Anti-Pattern 5: Assuming `setScale(n)` rounds with the same mode everywhere

**What the LLM generates:** Code that calls `setScale(2)` (single-arg) and assumes platform-default rounding, then writes a comment about "HALF_UP rounding for currency" that disagrees with the actual mode.

```apex
// WRONG — single-arg setScale throws if rounding is required
Decimal stored = computed.setScale(2);  // throws on 1.005
```

**Why it happens:** Java's `BigDecimal.setScale(int)` uses `UNNECESSARY` (throws on rounding) — the same is true in Apex. LLMs sometimes treat single-arg setScale as a safe truncation and add a misleading comment.

**Correct pattern:**

```apex
Decimal stored = computed.setScale(2, System.RoundingMode.HALF_EVEN);
```

**Detection hint:** Grep for `setScale\(\s*\d+\s*\)` — a single integer argument is the danger signature. Always pair with a `RoundingMode`.
