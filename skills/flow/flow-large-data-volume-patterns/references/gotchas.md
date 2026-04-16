# Gotchas — Flow Large Data Volume Patterns

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Query-rows limit is about returned rows, not “number of Get Records”

**What happens:** Multiple `Get Records` elements, or one element returning a huge collection, consume the same **total row** budget for the transaction. Practitioners tune “100 SOQL queries” mentally but miss that **row return volume** can fail the interview first.

**When it occurs:** LDV orgs, wide related lists, migrations, or integrations that trigger flows with generous filters.

**How to avoid:** Model **total rows returned** per transaction path. Cap retrieval, reduce selected fields, and reduce the number of separate wide reads.

---

## Gotcha 2: “Works in sandbox” is a false negative

**What happens:** Developer sandboxes and small seed data never stress `Get Records`. The identical metadata fails only when production-like cardinality appears.

**When it occurs:** First mass update, integration go-live, or customer with years of history on the same parent.

**How to avoid:** Test with realistic **child counts** and concurrent parent updates. Use full-copy sandboxes or controlled volume tests where possible.

---

## Gotcha 3: Other automation shares the same transaction

**What happens:** A Flow that is “just under” the limit in isolation fails when validation rules, other flows, Apex triggers, or managed-package automation add more queries and rows in the same transaction.

**When it occurs:** Bulk API loads, Data Loader batches, and cascading updates across related objects.

**How to avoid:** Inventory **all** synchronous participants in the transaction, not only the flow you own. Leave headroom or move work async.
