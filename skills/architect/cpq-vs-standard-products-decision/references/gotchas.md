# Gotchas — CPQ vs Standard Products Decision

Non-obvious Salesforce platform behaviors that cause real production problems in this domain. Each gotcha names its source. Claims that could not be confirmed from a fetched source carry an inline `UNVERIFIED (2026-10-03):` marker.

## Gotcha 1: CPQ Is Feature-Frozen, So Today's Gap Is Permanent

**What happens:** A team buys or renews Salesforce CPQ expecting a missing capability to arrive "in a later release". It will not. The official guide states the managed package "continues to be available for existing customers, however, there is no longer any new feature development", with support "for the duration of your contract" and the option to add licences and renew. Salesforce points customers wanting "a more comprehensive and robust CPQ solution" to Revenue Cloud.

**When it occurs:** In any decision record written from older comparison material, and whenever an AI assistant treats CPQ as the default answer for complex quoting.

**How to avoid:** Put the lifecycle notice in the decision record's Context, quoted with its document version. Score requirements against CPQ as it exists today. For a customer without a CPQ subscription, CPQ is not on the table: Salesforce "is no longer selling new Salesforce CPQ licenses to new customers". Route the complex-quoting evaluation to `architect/revenue-cloud-architecture`. Existing customers face "no forced migration".

**Source:** Salesforce CPQ Developer Guide, Version 67.0 (Summer '26), Chapter 1 notice; "Navigating the Future of Salesforce CPQ: Product End of Sale (Not End of Life)", salesforce.com, 10 July 2026 (https://www.salesforce.com/sales/cpq/end-of-life/, read 2026-10-03).

---

## Gotcha 2: CPQ Licences Follow Everyone Who Edits A Quote

**What happens:** The budget covers account executives. Sales engineers, deal desk analysts, and managers who edit quotes also need a CPQ licence, so the real count runs higher than planned. UNVERIFIED (2026-10-03): the often-quoted "30-50% higher" range is a practitioner estimate.

**When it occurs:** During procurement, and again after go-live when non-rep users cannot work on CPQ quote objects.

**How to avoid:** Count distinct users who created or edited quotes over the last year (query in `references/examples.md`), then add deal desk and sales engineering roles. Existing customers can add licences during the current term, so an undercount is fixable, but it is a budget event.

**Source:** CPQ Developer Guide v67.0, Chapter 1 notice: "You can also add more user licenses to your Salesforce org during your current subscription term." Licence-per-editor rule: UNVERIFIED (2026-10-03), stated in Salesforce Help only.

---

## Gotcha 3: The Standard Price Must Exist Before Any Other Price, With Or Without CPQ

**What happens:** A team loads custom price book entries, or relies on CPQ price rules, without first creating the standard price book entry. The load fails, or products cannot be added to quotes.

**When it occurs:** During initial catalog migration and whenever a product is added by integration rather than through the UI. UNVERIFIED (2026-10-03): the exact CPQ error text "No standard price defined for this product" was not confirmed.

**How to avoid:** Load standard price book entries first, in every currency the product sells in, then custom price books. Treat the standard entry as the base price that CPQ adjusts.

**Source:** Object Reference v67.0, PricebookEntry: "You must load the standard price for a product before you're permitted to load its custom prices"; `UseStandardPrice` "must be set to true" for entries in the standard price book.

---

## Gotcha 4: Catalog Size Is Products Times Price Books Times Currencies

**What happens:** A 200-product catalog in five price books and four currencies is 4,000 price book entries, not 200. Integration jobs, data loads, and price-change processes are sized for the wrong number.

**When it occurs:** In multi-currency orgs and in orgs with regional or partner price books, on both the standard and CPQ paths.

**How to avoid:** Size the catalog as entries, not products, before choosing a tool. Count current entries per price book and currency with the query in `references/examples.md`.

**Source:** Object Reference v67.0, PricebookEntry: "Create one PricebookEntry record for each standard or custom price and currency combination for a product in a Pricebook2"; `CurrencyIsoCode` exists only with multicurrency enabled.

---

## Gotcha 5: The Standard Bundle Object Exists Only Under Other Licences

**What happens:** Someone proposes modeling bundles on standard objects with `ProductRelatedComponent`, and selling models with `ProductSellingModel`. In a plain Sales Cloud org neither object is available.

**When it occurs:** When object names are found in documentation without reading their access rules.

**How to avoid:** Check licences before designing. `ProductRelatedComponent` (API 58.0+) is available when B2B Commerce, B2C Commerce, Industries Automotive, Industries EPC, or Subscription Management is enabled. `ProductSellingModel` is available with Revenue Cloud and Subscription Management. Without those, bundles on the standard path mean custom objects you own and maintain.

**Source:** Object Reference v67.0, ProductRelatedComponent and ProductSellingModel, Special Access Rules.

---

## Gotcha 6: CPQ Package Upgrades Still Need Regression Tests

**What happens:** Custom Apex triggers, validation rules, or flows on `SBQQ__Quote__c` and `SBQQ__QuoteLine__c` fail after a package upgrade, or double-fire alongside CPQ's own trigger logic.

**When it occurs:** On package upgrades, and when custom automation updates CPQ records several times in one transaction. With no new feature development, upgrades are maintenance releases, which lowers but does not remove the risk.

**How to avoid:** Install upgrades in a full sandbox first and run regression tests on every automation that touches CPQ objects. Where custom code updates CPQ records, use the documented mechanism to disable CPQ and Billing trigger logic for that update rather than fighting it.

**Source:** CPQ Developer Guide v67.0, "Disable CPQ Triggers in Apex": "You can manually disable Salesforce CPQ and Salesforce Billing application logic when you update records ... when you update a record several times in one transaction and want triggers to run only on the last iteration."

---

## Gotcha 7: Standard Quote Templates Do Not Read CPQ Quote Lines

**What happens:** After CPQ adoption the existing quote template produces blank or partial PDFs. CPQ stores lines on `SBQQ__QuoteLine__c`, not `QuoteLineItem`.

**When it occurs:** When a team assumes it can keep its standard quote template after moving to CPQ.

**How to avoid:** Plan document generation with the CPQ quote document capability or a document tool that reads `SBQQ__QuoteLine__c`. UNVERIFIED (2026-10-03): that standard quote templates render only `QuoteLineItem` is stated in Salesforce Help, not in a fetched source.

**Source:** CPQ Developer Guide v67.0, CPQ API Models (`QuoteModel.record` is `SBQQ__Quote__c`; `QuoteLineModel.record` is `SBQQ__QuoteLine__c`) and "Generate Quote Document API: Creates and saves a CPQ quote document." Object Reference v67.0, QuoteLineItem.

---

## Gotcha 8: Moving Between Quote Models Is A Data Migration

**What happens:** CPQ is installed on top of years of standard quotes. Existing `Quote` and `QuoteLineItem` records stay where they are, CPQ writes new quotes to `SBQQ__Quote__c`, and reports and integrations now see half the history. The reverse move has the same shape.

**When it occurs:** In any org with quoting history, in either direction.

**How to avoid:** Decide in the record: migrate history, report across both models, or set a cutover date and freeze the old model. Inventory every report, integration, and automation that reads `Quote` or `QuoteLineItem` before go-live.

**Source:** CPQ Developer Guide v67.0, CPQ API Models (CPQ quote objects); Object Reference v67.0, Quote ("Quotes can be created from and synced with opportunities") and QuoteLineItem.
