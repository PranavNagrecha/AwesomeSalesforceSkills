# Gotchas — Media Cloud Setup

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: The Ad Sales Objects Are Standard and All Prefixed `Ad` — Nothing Is Named "Media…"

**What happens:** A team designs `Media_Deal__c`, `Media_Contract__c`, and `Media_Placement__c` because the product is called Media Cloud. The names are wrong twice over: the objects ship as standard, and the prefix is `Ad`, not `Media`. Everything downstream — shipped components, the AdTech integration, revenue rules — is wired to objects the custom build never touches.

**When it occurs:** In the design phase, before provisioning makes the real objects visible. AI assistants reproduce it reliably, because "Media Cloud" is the product name and `MediaPlacement` is a plausible-sounding object.

**How to avoid:** Read the Media Cloud standard-object list before drawing anything. The spine is `AdOpportunity` ("Represents ad sales specific details of an advertisement campaign opportunity"), `AdQuote` ("the details of a quote for an advertisement campaign") with `AdQuoteLine`, and `AdOrderItem` ("the advertisement campaign specific details of an ad order item"). There is no `MediaDeal`, no `MediaContract`, and no `MediaPlacement`.

---

## Gotcha 2: The Order-Side Children Mix `AdOrderItem…` and `AdOrderLine…` Prefixes

**What happens:** A query or a Flow references `AdOrderItemAdTarget` and fails, because the targeting objects use `AdOrderLine…` while the delivery and creative objects use `AdOrderItem…`. Both prefixes are correct — for different children of the same parent.

**When it occurs:** Every time a name is inferred rather than copied. The split is genuinely inconsistent: `AdOrderItemAdSpaceSpec`, `AdOrderItemCreativeSizeType`, `AdOrderItemDeliveryFrequency`, `AdOrderItemDeliverySchedule`, `AdOrderItemPrintIssue`, and `AdOrderItemUnitsSplit` on one side; `AdOrderLineAdTarget`, `AdOrderLineHiatus`, `AdOrderLineTargetExpression`, and `AdOrderLineTargetValue` on the other.

**How to avoid:** Copy every API name from the object reference, never complete it from a pattern. In Apex, use `SObjectType` tokens so a wrong name fails at compile time. When reviewing generated code or metadata for this domain, check the prefix on every `AdOrder…` reference specifically — it is the single most likely thing to be wrong.

---

## Gotcha 3: Quote-Side and Order-Side Objects Mirror Each Other, and Configuration Does Not Carry Across

**What happens:** Targeting, delivery schedules, creative sizes, hiatus periods, and unit splits are configured on the quote and are expected to be present on the order. They are separate object families — `AdQuoteLineAdTarget` / `AdOrderLineAdTarget`, `AdQuoteLineDeliverySchedule` / `AdOrderItemDeliverySchedule`, `AdQuoteLineHiatus` / `AdOrderLineHiatus`, `AdQuoteLineCreativeSizeType` / `AdOrderItemCreativeSizeType`, `AdQuoteLineUnitsSplit` / `AdOrderItemUnitsSplit`. Anything a customisation writes to only one side is invisible on the other.

**When it occurs:** When custom automation, a data load, or an integration writes to the quote family and the team assumes conversion propagates it. It surfaces as an order that trafficks with no targeting or with the default flight dates.

**How to avoid:** Test the quote-to-order transition explicitly with every child populated, and assert on the order side rather than the quote side. Treat any custom field added to a quote-line child as a two-object change: the mirror on the order family needs it too, plus whatever carries the value across.

---

## Gotcha 4: The AdTech Integration Runs Through MuleSoft and a Generated Named Credential

**What happens:** An ad-server integration is planned as bespoke Apex callouts, then collides with the shipped path. The Media Cloud AdTech Integration API provides "integration APIs and apps for integrating Media Cloud Advertising Sales Management (ASM) with external adtech systems," and enabling it requires accepting terms and connecting both a Salesforce and a MuleSoft instance. On deployment, "Salesforce creates a named credential for the integration instance," specifying "the URL of a callout endpoint and its required authentication parameters."

**When it occurs:** During integration design, when the MuleSoft dependency has not reached the budget conversation. Discovering it late means either an unplanned licence or a hand-built integration that will diverge from the shipped one at every release.

**How to avoid:** Settle the MuleSoft question before the integration design is signed off, and treat the generated named credential as the org's callout endpoint rather than creating a parallel one. Do not hard-code ad-server URLs or credentials in Apex when a named credential already exists for that instance — and never print the credential's secret in any log or agent output.

---

## Gotcha 5: Impression Volumes Belong Outside Salesforce; Only the Aggregate Belongs In It

**What happens:** A delivery-reconciliation job loads raw ad-server impression logs so that invoices can be traced to individual served impressions. A mid-sized publisher's daily log is millions of rows. Data storage fills, the reconciliation job's queries slow past their window, and the org ends up buying storage to hold data nobody queries at row level.

**When it occurs:** In the first month of the ad-server integration, usually because "we need an audit trail" was interpreted as "we need every row". Digital delivery on a single flight can generate more rows in a day than the entire CRM holds.

**How to avoid:** Aggregate upstream — in MuleSoft, the ad server's own reporting, or the warehouse — and sync a daily rollup per order line. Keep the granular log in the system that already stores it and record where it lives, so a disputed invoice can be answered by pointing at the source rather than by holding a copy. Reserve Salesforce for the numbers that drive the order, the invoice, and the customer conversation.
