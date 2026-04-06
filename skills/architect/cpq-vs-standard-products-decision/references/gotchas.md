# Gotchas — CPQ vs Standard Products Decision

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: CPQ License Count Is Per Quoting User, Not Per Admin

**What happens:** Organizations budget CPQ licensing for the sales team but forget that sales engineers, deal desk analysts, and managers who edit quotes also need CPQ licenses. The actual license count ends up 30-50% higher than the initial estimate.

**When it occurs:** During CPQ budgeting and procurement. The undercount surfaces after go-live when users receive "insufficient privileges" errors trying to access CPQ quote objects.

**How to avoid:** Audit every user who will create, edit, or clone a CPQ quote — not just the "sales rep" role. Include deal desk, sales operations, sales engineering, and any manager who modifies quotes rather than just approving them.

---

## Gotcha 2: Standard Pricebook Entries Are Required Even with CPQ

**What happens:** CPQ uses its own pricing engine (Price Rules, Discount Schedules, Contracted Prices), but the underlying Product2 and PricebookEntry records must still exist. Teams sometimes skip creating standard pricebook entries thinking CPQ replaces them entirely, then encounter errors when CPQ tries to reference the base price.

**When it occurs:** During initial CPQ setup or when adding new products. The error manifests as "No standard price defined for this product" when adding products to a CPQ quote.

**How to avoid:** Always create a Standard Pricebook Entry for every product, even when CPQ Price Rules will override the price. Treat the standard pricebook entry as the floor price that CPQ adjusts.

---

## Gotcha 3: CPQ Managed Package Upgrades Can Break Custom Triggers

**What happens:** Salesforce CPQ releases managed package updates on its own cadence, separate from the three Salesforce platform releases per year. Custom Apex triggers, validation rules, or Flows that reference CPQ objects (SBQQ__Quote__c, SBQQ__QuoteLine__c) can fail after a package upgrade if field behaviors or object relationships change.

**When it occurs:** During CPQ package upgrades, especially major version bumps. Teams that skip sandbox testing before upgrading production discover broken automations after the upgrade completes.

**How to avoid:** Always install CPQ package updates in a full-copy sandbox first. Run regression tests on all custom automations that touch CPQ objects. Subscribe to CPQ release notes and review breaking changes before upgrading.

---

## Gotcha 4: Standard Quote Templates Cannot Render CPQ Quote Lines

**What happens:** CPQ stores quote lines in SBQQ__QuoteLine__c, not the standard QuoteLineItem object. Standard Salesforce quote templates only render QuoteLineItem records. Teams that expect standard templates to work with CPQ data see blank or incomplete PDFs.

**When it occurs:** When a team deploys CPQ but tries to reuse their existing standard quote template rather than building a CPQ quote template.

**How to avoid:** Plan for CPQ quote document generation from the start. Use CPQ's native quote template engine or a third-party document generation tool that reads from SBQQ__QuoteLine__c. Do not assume standard quote templates are compatible.

---

## Gotcha 5: Switching from Standard to CPQ Requires Data Migration, Not Just Configuration

**What happens:** Teams assume that enabling CPQ on top of an existing standard Products/Quotes implementation is purely additive — just install the package and configure. In reality, existing Quote and QuoteLineItem records are not automatically migrated to CPQ's SBQQ objects. Historical quotes remain in the old model, creating a split data architecture.

**When it occurs:** During CPQ adoption in an org that already has years of quoting history on standard objects. Reporting, dashboards, and integrations that reference standard Quote objects break or show incomplete data.

**How to avoid:** Plan a data migration strategy as part of the CPQ implementation project. Decide whether to migrate historical quotes to CPQ objects, maintain parallel reporting on both object sets, or accept a cutover date where old quotes stay in the legacy model.
