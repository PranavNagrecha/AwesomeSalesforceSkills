# Gotchas — CPQ Product Catalog Setup

Non-obvious Salesforce CPQ platform behaviors that cause real production problems in this domain.

## Gotcha 1: Bundle Nesting Max 4 Levels — Deep Nesting Significantly Impacts Configurator Load Time

**What happens:** When a bundle contains nested bundles (a Product Option whose product is itself a bundle), CPQ opens each nested level with additional SOQL queries at configurator load time. At 3–4 levels of nesting with a large product catalog, the configurator page can take 10–20 seconds to open, and in pathological cases can hit Apex governor limits (particularly the 100-SOQL-query limit or heap size).

**When it occurs:** Nesting impact is felt most when: (a) the parent bundle has many options, (b) nested sub-bundles each have many options, or (c) the org has large amounts of product data that CPQ must evaluate for pricing context. It becomes a production crisis when sales reps complain that the configurator "freezes" or times out.

**How to avoid:** Keep nesting to 2 levels maximum as a design principle. If a 3-level structure is genuinely required, test configurator load time with representative data volume before go-live. If 4-level nesting is requested, push back strongly — in nearly all cases, a flat bundle with a Configuration Attribute + Filter rules can achieve the same business outcome without the performance cost.

---

## Gotcha 2: Product Rules Fire in Sequence Number Order — Rule Order Matters for Selection Rules

**What happens:** CPQ evaluates Product Rules in ascending order of `SBQQ__Sequence__c`. For Selection rules specifically, earlier rules can trigger option changes that affect the conditions of later rules. If two Selection rules share the same sequence number, CPQ's tie-breaking order is undefined and may vary between CPQ package versions.

**When it occurs:** This bites most often when building complex configurators where one auto-selection should trigger another (chained rules). A common failure mode: Rule 10 auto-selects Option B when Option A is chosen. Rule 20 should auto-select Option C when Option B is present — but because CPQ evaluated Option B's presence before Rule 10 fired, Rule 20 misses it on the first pass. The rep must re-open the configurator or interact with the page to trigger a re-evaluation.

**How to avoid:** Always assign unique, spaced sequence numbers (10, 20, 30, 40) — never duplicate sequence numbers across rules on the same bundle. For chained Selection rules, test whether CPQ's single-pass evaluation is sufficient. If chaining is required, use the `SBQQ__EvalEvent__c` field to set evaluation to "Always" rather than just on selection change, so rules are re-evaluated on each UI interaction.

---

## Gotcha 3: Configuration Attributes Are Bundle-Scoped, Not Product-Scoped or Globally Inherited

**What happens:** A Configuration Attribute defined on a parent bundle does not automatically propagate to nested sub-bundles. If you have a 2-level bundle (Cloud Platform > Storage Module) and you want the "Service Tier" attribute to drive Filter rules on both the parent's options and the nested Storage Module's options, you must create separate Configuration Attribute records for each bundle level.

**When it occurs:** This surprises teams building multi-level bundles where a single header attribute (e.g., geography, customer segment, contract type) is intended to control visibility across all levels. They create one Configuration Attribute, write Filter rules on the sub-bundle, and discover the sub-bundle's Filter rules never fire because the attribute value is not in scope.

**How to avoid:** Model Configuration Attributes per bundle level. If a shared attribute needs to drive rules at multiple nesting levels, consider flattening the catalog or using a custom field on the Quote Line object that is explicitly mapped at each bundle level.

---

## Gotcha 4: Filter Rules Hide Options from the Configurator UI but Do Not Enforce at the API or Flow Layer

**What happens:** Filter Product Rules are evaluated only within the CPQ configurator experience. When Product Options are added or modified via the SBQQ API directly (e.g., through a Salesforce Flow using the `SBQQ.QuoteAPI.save` or via direct DML on `SBQQ__QuoteLine__c`), Filter rules are not evaluated. A hidden option can be explicitly added via API regardless of what Filter rules specify.

**When it occurs:** Integration scenarios are the typical trigger — a backend process or external system calls the CPQ Quote API to build a quote programmatically. The process adds options that the configurator would have hidden. Alternatively, a Flow built by a developer who is unfamiliar with CPQ adds a quote line directly via DML, bypassing rule evaluation entirely.

**How to avoid:** Use Filter rules to improve the configurator UX (hide irrelevant options, reduce cognitive load). For constraints that must be enforced as data-level invariants — including in API and automation contexts — also create a Validation rule that checks the same conditions on save. The Validation rule fires during the CPQ Quote save cycle (including when called via the SBQQ API's save method), providing a safety net.

---

## Gotcha 5: Product Option Sort Order Field Is Not Automatically Renumbered on Deletion

**What happens:** Product Options have a `SBQQ__Number__c` field that controls display order within a Feature. If you delete a Product Option in the middle of an existing sequence (e.g., option at position 30 is deleted from a sequence 10, 20, 30, 40, 50), the remaining options retain their original numbers. The sequence is now 10, 20, 40, 50 — cosmetically fine in most cases but becomes a maintenance issue when CPQ logic depends on sort order for rule evaluation or when new options are inserted.

**When it occurs:** Catalog maintenance — removing discontinued products from a bundle. The product manager or admin deletes the Product Option record without realizing the remaining options retain their original sort numbers.

**How to avoid:** After deleting or inserting Product Option records, audit and renumber the remaining options within each Feature. Consider using spaced numbering from the start (10, 20, 30) to leave room for future insertions without full renumbering.
