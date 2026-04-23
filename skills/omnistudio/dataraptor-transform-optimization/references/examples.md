# DataRaptor Transform Optimization — Examples

## Example 1: Formula Replaces Apex For String Concat

**Before:** Apex expression `AccountAddress.computeDisplay(...)` called per row to build a display string.

**After:** Formula `{Street} + ", " + {City} + ", " + {State} + " " + {PostalCode}`.

Result: per-row CPU time drops to near zero; no SOQL or heap overhead.

---

## Example 2: Bulk Mode On Array Input

**Before:** A Transform invoked from an IP step receives a 200-row array but is configured row-by-row. Total runtime: 4200 ms.

**After:** Same Transform switched to bulk mode. Total runtime: 380 ms.

**Why it works:** Bulk mode pays the evaluator setup once; row-by-row pays it 200 times.

---

## Anti-Pattern: Chain Of Three Transforms With No Consumer Between

A normalize → enrich → shape chain where no downstream step reads the intermediate results. Merging into a single Transform with all three mappings saved 60% of runtime and made the logic easier to read.
