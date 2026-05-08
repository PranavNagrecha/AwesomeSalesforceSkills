# Examples — Apex Decimal Arithmetic Precision

## Example 1: Tax calculation that matches the platform's currency field

**Context:** A custom checkout flow computes tax on each line item in Apex, then writes a `Total_With_Tax__c` Currency(16,2) field. QA reports that the Apex value is sometimes 1 cent higher than the same calculation reproduced in a workbook formula or a Flow.

**Problem:** The original code:

```apex
// WRONG — uses HALF_UP on platform that uses HALF_EVEN for currency display
Decimal subtotal = unitPrice * qty;
Decimal tax = subtotal * (taxRate / 100);
Decimal total = (subtotal + tax).setScale(2, System.RoundingMode.HALF_UP);
li.Total_With_Tax__c = total;
```

Two bugs: `taxRate / 100` is Decimal-divided-by-Integer-literal, fine here, but `subtotal * (taxRate / 100)` is not given an explicit scale — relies on the natural scale of the multiply, which compounds with the chosen final-rounding mode. And `HALF_UP` disagrees with the Currency field's display rounding (`HALF_EVEN`) on every halfway value.

**Solution:**

```apex
public class TaxCalc {
    public static Decimal totalWithTax(Decimal unitPrice, Integer qty, Decimal taxRatePercent) {
        Decimal subtotal = unitPrice * qty;
        Decimal tax = subtotal.multiply(taxRatePercent)
            .divide(100, 6, System.RoundingMode.HALF_EVEN);
        return (subtotal + tax).setScale(2, System.RoundingMode.HALF_EVEN);
    }
}
```

**Why it works:** Intermediate `tax` carries scale 6 to absorb the multiply-then-divide rounding without losing precision. The final `setScale(2, HALF_EVEN)` matches the platform's display behavior so the value persisted in `Total_With_Tax__c` matches what a Flow or formula would compute.

---

## Example 2: Allocating a discount across line items so the sum equals the header

**Context:** A revenue-recognition module needs to allocate a header-level discount (`-150.00`) across 7 line items in proportion to their amounts. Naïve `each = total / 7` rounded to 2 places leaves the line-item sum drifting from the header by 0.01–0.04 depending on rounding direction. Finance audit flags the drift.

**Problem:** Naïve approach:

```apex
// WRONG — sum of allocated drifts from header
Decimal each = headerDiscount.divide(items.size(), 2, System.RoundingMode.HALF_UP);
for (LineItem__c li : items) {
    li.Allocated_Discount__c = each;
}
```

For `headerDiscount = -150.00` and `items.size() = 7`, `each = -21.43`, sum = `-150.01`. One cent over.

**Solution:**

```apex
public static void allocateProportional(List<LineItem__c> items, Decimal total) {
    Decimal totalAmount = 0;
    for (LineItem__c li : items) totalAmount += li.Amount__c;
    if (totalAmount == 0) {
        // Avoid divide-by-zero; nothing to allocate.
        return;
    }
    Decimal running = 0;
    for (Integer i = 0; i < items.size() - 1; i++) {
        Decimal share = total
            .multiply(items[i].Amount__c)
            .divide(totalAmount, 6, System.RoundingMode.HALF_EVEN)
            .setScale(2, System.RoundingMode.HALF_EVEN);
        items[i].Allocated_Discount__c = share;
        running += share;
    }
    items[items.size() - 1].Allocated_Discount__c =
        (total - running).setScale(2, System.RoundingMode.HALF_EVEN);
}
```

**Why it works:** First N−1 items get a clean proportional share, scale-2, banker's-rounded. The last item absorbs the residual so the sum is *exactly* the header total. Order of items is irrelevant to correctness; the residual is at most a few cents, which is the irreducible rounding gap of any equal-share allocation.

---

## Example 3: Equality compare without false negatives across scales

**Context:** A reconciliation Apex job compares an Apex-computed `expected` value against a value read from an external API response (parsed via JSON) where the API returns values like `"1.5"` (scale 1) but the Apex side computed `1.50` (scale 2). `.equals()` says the values differ; the team starts adding string-conversion hacks to "fix" it.

**Problem:**

```apex
// WRONG — scale-strict comparison reports false negatives
Decimal apiValue = (Decimal) JSON.deserialize('"1.5"', Decimal.class);
Decimal expected = 1.50;
Boolean ok = expected.equals(apiValue);  // false! scale 2 != scale 1
```

**Solution:**

```apex
public static Boolean equalsAt(Decimal a, Decimal b, Integer scale) {
    return a.setScale(scale, System.RoundingMode.HALF_EVEN)
        .equals(b.setScale(scale, System.RoundingMode.HALF_EVEN));
}

// Or for "same number" semantics:
Boolean ok = expected == apiValue;  // true — Apex == is value-equal on Decimal
```

**Why it works:** Apex's `==` on Decimal is *value-equal* — it ignores scale. `.equals()` is *scale-strict* and reports `false` whenever scales differ even if the numeric value is identical. For "same number" use `==`. When you must use `.equals()` (e.g. inside a Set or Map key), normalize both sides to the same scale first.

---

## Anti-Pattern: Mixing Decimal and Double via `Decimal.valueOf(Double)`

**What practitioners do:** They have a `Double` from a JSON parse or a third-party library and convert it via `Decimal.valueOf(myDouble)`, expecting clean decimal arithmetic afterward.

**What goes wrong:** `Decimal.valueOf(Double)` constructs the Decimal from the *binary* double representation, not the decimal one. Any value that isn't representable in binary floating point (e.g. `0.1`, `0.2`, `0.3`, most non-power-of-2 fractions) gets a long tail of binary-rounding noise: `Decimal.valueOf(0.1) → 0.1000000000000000055511151231257827021181583404541015625`. Subsequent `setScale` calls "round away" the noise, but a `.toString()` or a downstream consumer that expects clean values will show the trailing digits.

**Correct approach:** When parsing JSON, configure the JSON parser to produce strings or BigDecimal-equivalent Decimals (`JSON.createParser` lets you call `getDecimalValue()` directly). When constructing from a literal, use `Decimal.valueOf('0.1')` (String overload) or write `Decimal d = 0.1;` (Apex literal). Never let a Double touch a money calculation.
