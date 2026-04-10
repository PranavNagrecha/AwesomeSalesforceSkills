# Gotchas — CPQ Integration with ERP

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Order Activation Is the Canonical ERP Trigger, Not Quote Close

**What happens:** Teams trigger ERP transmission when the CPQ quote status becomes `Approved` or when the Opportunity reaches `Closed Won`. In some CPQ configurations, Order generation is asynchronous after quote approval. The middleware fires and queries `OrderItem` before the Order has been committed, returning zero line items. The SAP or NetSuite order is created with no line items and the integration team spends hours diagnosing what appears to be a data mapping error.

**When it occurs:** Any time the ERP trigger is placed on a quote or opportunity event rather than an Order record state change. Most common when the integration is built before the CPQ Order generation workflow has been tested end-to-end.

**How to avoid:** Set the ERP trigger exclusively on `Order.Status` reaching the agreed activated value (e.g., `Activated`, `Submitted`). Use a Record-Triggered Flow or platform event on the Order object. Never trigger on `SBQQ__Quote__c.SBQQ__Status__c` or `Opportunity.StageName`. Confirm the specific Status value with the CPQ admin — it is org-specific.

---

## Gotcha 2: QuoteLineItem Is Not Populated by Salesforce CPQ

**What happens:** An ERP integration developer, familiar with standard Salesforce Quotes, writes SOQL against `QuoteLineItem` to pull CPQ quote line details. The query returns zero rows even for quotes with visible line items on the CPQ quote page. The developer concludes the integration is broken or that CPQ is not saving data.

**When it occurs:** Any time a developer builds against the standard `QuoteLineItem` object assuming CPQ uses it. CPQ writes all quote line data to the custom object `SBQQ__QuoteLine__c`. The standard `QuoteLineItem` object is not written to by CPQ at all.

**How to avoid:** Always query `SBQQ__QuoteLine__c` for CPQ quote line data. For order-time data after the Order is generated from a CPQ quote, query `OrderItem` (standard object) joined to the `Order`. Document this object distinction in the integration's data mapping specification so future developers do not repeat the error.

---

## Gotcha 3: Amendment Orders Carry Delta Quantity, Not the New Cumulative Total

**What happens:** A CPQ subscription is amended to add 10 seats to an existing 50-seat contract. The integration receives an Order with `OrderItem.Quantity = 10` and creates a new Sales Order in SAP for 10 seats. The ERP now shows two separate fulfillment records — the original 50-seat order and a new 10-seat order — instead of a single updated 60-seat subscription. Billing, inventory, and fulfillment data become inconsistent.

**When it occurs:** When the integration treats every activated CPQ Order as a net-new ERP order, without checking whether the Order originated from an amendment or renewal. This is especially common when the initial integration is built and tested only with new-business scenarios.

**How to avoid:** Add amendment detection to the Order routing logic. Check `SBQQ__Quote__r.SBQQ__AmendedContract__c` on the Order's source quote — if populated, the Order is a delta amendment. Route amendment Orders to an ERP patch/change-order API call against the existing document, not to a new Sales Order creation endpoint. Test the amendment path explicitly in the integration acceptance test suite.

---

## Gotcha 4: QCP Callout Restriction Causes Quote Calculation Failure

**What happens:** A developer embeds an HTTP callout to an ERP inventory or pricing API directly inside the Quote Calculator Plugin's `calculate()` method. In sandboxes, this may appear to work if the org has external services whitelisted and the timing is favorable. In production, Salesforce throws `System.CalloutException: Callout not allowed from this context`, and the entire quote calculation silently fails — no prices are applied and the rep sees a blank pricing column with no error message.

**When it occurs:** When any HTTP callout (HttpRequest, WebServiceCallout, named credential callout) is made from within a QCP method. This is a platform constraint, not a configuration setting that can be changed.

**How to avoid:** Move all ERP API calls out of QCP. For inventory, use an async LWC-invoked Apex action. For pricing, use a pre-fetch pattern where a scheduled job or Flow pre-populates a Salesforce custom object with ERP prices before quote calculation, and the QCP reads from that object (no callout needed). If real-time pricing at calculation time is truly required, use a QCP callout to a synchronous Apex REST endpoint in the same org that does the external call — but only if that endpoint is annotated correctly and the callout is initiated before the QCP call stack begins.

---

## Gotcha 5: ERP Price Book Drift from Unsynchronized Manual Edits

**What happens:** After a scheduled pricing sync job is set up, a CPQ admin manually adjusts a `PricebookEntry` price to accommodate a one-time customer deal. The next sync run overwrites the manual adjustment with the ERP price, breaking the custom deal pricing. Alternatively, the ERP team updates prices in SAP without notifying the Salesforce team — the sync job is delayed, and CPQ reps quote at stale prices for days.

**When it occurs:** When the pricing sync job has no conflict detection and no audit trail. Both manual overrides in CPQ and delayed ERP-side updates cause drift that goes unnoticed until a customer dispute arises.

**How to avoid:** Add a `Price_Source__c` field to `PricebookEntry` (e.g., `ERP-Synced`, `Manual-Override`). The sync job skips records marked `Manual-Override` unless a reset flag is set. Log every price change with a delta record (`Price_Sync_Log__c`) that captures old price, new price, product code, and timestamp. Alert the integration team when the delta exceeds a configured threshold (e.g., >5% change).
