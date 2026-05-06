# LLM Anti-Patterns — Revenue Cloud Architecture

Mistakes AI coding assistants commonly make when advising on RLM /
Revenue Cloud architecture.

---

## Anti-Pattern 1: Synchronous Apex callout from a trigger

**What the LLM generates.**

```apex
trigger OrderTrigger on Order (after insert) {
    HttpRequest req = new HttpRequest();
    req.setEndpoint('callout:Erp/orders');
    req.setMethod('POST');
    new Http().send(req);
}
```

**Why it happens.** "Push order to ERP on insert" is a textbook
description; the LLM emits the textbook callout.

**Correct pattern.** The platform blocks synchronous trigger
callouts. Use `@future(callout=true)` or Queueable for
fire-and-forget; use Platform Events or CDC for the architect-
recommended event-driven path.

**Detection hint.** Any `Http.send` or `HttpResponse` inside a
trigger.

---

## Anti-Pattern 2: Conflating native RLM Billing with `blng__` Salesforce Billing

**What the LLM generates.**

```apex
blng__Invoice__c inv = new blng__Invoice__c(...)
// "RLM invoice"
```

or

```apex
Invoice inv = ...
// "Salesforce Billing managed package"
```

**Why it happens.** Training data covers both products under "Revenue
Cloud" / "Salesforce Billing" labels without disambiguation.

**Correct pattern.** Confirm namespace before code. Native RLM uses
unqualified names (`Invoice`, `BillingSchedule`, `LegalEntity`). The
managed package uses `blng__` (`blng__Invoice__c`). They are
different products.

**Detection hint.** Any code mixing both naming conventions, or
either convention named "RLM" without namespace verification.

---

## Anti-Pattern 3: One LegalEntity per region without legal-tax justification

**What the LLM generates.**

> Create a separate LegalEntity for each region (US, UK, DE, FR,
> CA, AU, JP) so each regional team can manage their own invoicing.

**Why it happens.** "One per region" is a common heuristic; the LLM
does not surface the cost.

**Correct pattern.** LegalEntity exists for legal / tax-jurisdiction
separation, not for operational / regional convenience. Each entity
multiplies tax config, accounting periods, and reporting burden.
Default to the smallest count and expand only with finance approval.

**Detection hint.** Multi-entity recommendation that lists more than
one LegalEntity per legal jurisdiction.

---

## Anti-Pattern 4: Treating Order / Asset / Contract as deletable

**What the LLM generates.**

```apex
delete [SELECT Id FROM Asset WHERE ContractId = :c.Id];
// Cleaning up assets after contract cancellation
```

**Why it happens.** SQL-style cleanup intuition.

**Correct pattern.** RLM treats Asset as a long-lived entity with
historical state captured in `AssetStatePeriod`. Cancellation is a
state transition, not a delete. Hard-deleting assets corrupts the
state history.

**Detection hint.** Any DML `delete` against `Asset`, `Contract`, or
`Order` in production code.

---

## Anti-Pattern 5: Bypassing PricebookEntry in custom pricing

**What the LLM generates.**

```apex
QuoteLineItem ql = new QuoteLineItem(
    QuoteId = q.Id, Product2Id = p.Id, UnitPrice = customPrice
);
insert ql;
```

(without setting `PricebookEntryId`)

**Why it happens.** RLM Pricing rules feel like they "replace"
PricebookEntry.

**Correct pattern.** PricebookEntry is the linkage point; RLM
Pricing extends it. QuoteLineItem and OrderItem still require a
valid `PricebookEntryId`.

**Detection hint.** Any QuoteLineItem / OrderItem insert without
`PricebookEntryId`.

---

## Anti-Pattern 6: Asserting "Revenue Cloud and CPQ are the same product"

**What the LLM generates.**

> Revenue Cloud (also known as CPQ-Plus) is the same product, just
> rebranded.

**Why it happens.** Marketing labels conflate generations.

**Correct pattern.** RLM is a native architecture. CPQ classic
(`SBQQ__`) is a managed package and a different code base. They
share quote-to-cash semantics but have different APIs, data models,
and extensibility surfaces.

**Detection hint.** Any architecture recommendation that does not
identify the namespace target.

---

## Anti-Pattern 7: Assuming AccountingPeriod is informational

**What the LLM generates.** Code that posts to invoices without
checking `AccountingPeriod` status.

**Why it happens.** AccountingPeriod sounds like metadata, not a
gating control.

**Correct pattern.** A closed `AccountingPeriod` blocks new posts
into that period. Integrations must handle period-closed errors and
either route to a dead-letter or surface to finance for re-open.

**Detection hint.** Invoice / posting code with no error path for
period-closed errors.
