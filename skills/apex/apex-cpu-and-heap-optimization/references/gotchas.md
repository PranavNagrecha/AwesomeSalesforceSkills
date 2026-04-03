# Gotchas — Apex CPU And Heap Optimization

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Bulkified Code Can Still Blow CPU

**What happens:** SOQL and DML are already outside loops, yet CPU still fails.

**When it occurs:** The remaining algorithm still does too much in-memory work.

**How to avoid:** Inspect nested-loop shape, repeated parsing, and expensive string or regex operations.

---

## Debugging Can Inflate The Heap

**What happens:** Diagnostic serialization or giant debug strings push the transaction over the heap limit.

**When it occurs:** Teams log whole payloads or collection contents during an incident.

**How to avoid:** Log counts, keys, and narrow samples instead of full payloads.

---

## JSON Work Is Often A Double Hit

**What happens:** Parsing and re-serializing large payloads costs both CPU and heap.

**When it occurs:** Integration payloads are repeatedly transformed or copied.

**How to avoid:** Parse once, process in smaller chunks, and avoid duplicate payload representations.

---

## Micro-Optimizing Syntax Rarely Beats Algorithm Refactors

**What happens:** Teams spend time changing minor syntax choices while the real bottleneck remains nested data traversal.

**When it occurs:** There is no measurement-driven hotspot identification.

**How to avoid:** Measure first, then attack the biggest compute or memory structure.
