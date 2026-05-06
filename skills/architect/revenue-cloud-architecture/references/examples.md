# Examples — Revenue Cloud Architecture

## Example 1 — Identifying the namespace before any design work

**Context.** Org claims to "use Revenue Cloud" — actual state is
unclear.

**Discovery checklist.**

```
Setup -> Installed Packages
  Look for:
    SBQQ__          -> CPQ classic
    blng__          -> Salesforce Billing
    sbaa__          -> Approvals (CPQ classic add-on)
  Also check Setup -> Object Manager for native RLM objects:
    Pricebook2 / Product2 are native everywhere
    LegalEntity, BillingSchedule, AccountingPeriod -> RLM Billing native
    Quote / Order / OrderItem -> standard, but RLM extends them
```

**Why this matters.** The integration design, the data model, and
the apex extensibility surface differ by namespace. Designing for
RLM and discovering production is `SBQQ__` mid-flight is expensive.

---

## Example 2 — Multi-entity scoping with LegalEntity

**Context.** Global org with US, UK, and DE operations. Finance
needs separate invoicing, accounting periods, and tax treatment per
country.

**Configuration.**

- 3x `LegalEntity` records: US-INC, UK-LTD, DE-GMBH.
- Per-entity Setup of payment terms, fiscal calendar via
  `AccountingPeriod`, tax codes.
- Order objects route through `LegalEntity` lookup that determines
  `BillingSchedule` configuration.

**Risk.** Five years later the business has 47 LegalEntity rows
because every regional team wanted their own. Tax and period config
multiplies; reporting becomes painful. Default architectural rule:
add a `LegalEntity` only when legal / accounting separation
**requires** it (tax-jurisdiction or auditing boundary), not for
operational convenience.

---

## Example 3 — Outbound integration: CDC vs Platform Event vs Apex callout

| Pattern | When | Tradeoffs |
|---|---|---|
| Change Data Capture | Bulk near-real-time replication of Order / Invoice | Durable replay; one-way; consumer (MuleSoft / Kafka) does the routing |
| Platform Event | Discrete business events (OrderActivated, InvoicePosted) | Lower latency; bounded retention; consumer must be reliable |
| `@future(callout=true)` | Per-record callouts where eventing infrastructure isn't available | Loses replay guarantees; tied to Salesforce limits; transactional with the originating DML |
| Queueable + AllowsCallouts | Long-running outbound jobs (batch invoice push) | Chains to handle limits; more code than CDC |

**Architect default.** CDC for high-volume replication, Platform
Events for discrete business events. Apex callouts only when
infrastructure constraints rule out the eventing options. **Never**
synchronous trigger callouts — the platform blocks them.

---

## Example 4 — Why you cannot call the ERP synchronously from a trigger

**Context.** Engineer writes:

```apex
trigger OrderTrigger on Order (after insert) {
    HttpRequest req = new HttpRequest();
    req.setEndpoint('callout:Erp/orders');
    req.setMethod('POST');
    new Http().send(req);
}
```

**What happens.** Runtime exception:

> Callout from triggers are currently not supported.

(The platform blocks synchronous callouts in trigger context to
preserve transactional integrity.)

**Right answer.** Use `@future(callout=true)` for fire-and-forget,
Queueable for chained / retried, or — preferred — fire a Platform
Event and have the consumer (MuleSoft, ERP-side worker) handle the
callout off-platform.

---

## Example 5 — RLM Billing vs `blng__` Salesforce Billing object names

A common LLM confusion. Approximate object-name mapping:

| Concept | RLM (native) | `blng__` (managed) |
|---|---|---|
| Billing schedule | `BillingSchedule` | `blng__BillingSchedule__c` |
| Invoice | `Invoice` | `blng__Invoice__c` |
| Invoice line | `InvoiceLine` | `blng__InvoiceLine__c` |
| Legal entity | `LegalEntity` | `blng__LegalEntity__c` |
| Accounting period | `AccountingPeriod` | `blng__AccountingPeriod__c` |

The behavior, validation, and APIs differ. Code targeting one will
not compile against the other. Confirm namespace at design time.

---

## Example 6 — Contract amendment + asset lifecycle

**Context.** Customer signs a 36-month subscription. Mid-term they
upgrade from Standard to Premium tier.

**Native RLM flow.**

1. Original `Order` is fulfilled; assets are created
   (`Asset` rows linked to the customer Account).
2. Amendment: a new `Order` is created with a reference to the
   existing `Contract`. The amendment captures what changes: which
   assets are upgraded, which are added, which are terminated.
3. `AssetStatePeriod` rows record the historical state of each
   asset (Standard from start to upgrade-date; Premium from
   upgrade-date forward).
4. Billing recalculates affected `BillingSchedule` rows.

**Why this is more than CPQ classic.** RLM models the asset
lifecycle natively (`AssetStatePeriod` is the historical state
table). CPQ classic relied on `SBQQ__` data model for similar
behavior but with package-specific quirks.
