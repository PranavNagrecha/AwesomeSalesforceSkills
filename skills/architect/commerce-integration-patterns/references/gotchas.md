# Gotchas — Commerce Integration Patterns

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: After-Phase Callouts Throw System.CalloutException

**What happens:** Any HTTP callout placed after a DML operation (or after any other operation that creates uncommitted work) within a `CartExtension` calculator method throws `System.CalloutException: You have uncommitted work pending.` at runtime. This can be intermittent — it fires only when a prior DML path has executed before the callout code is reached.

**When it occurs:** Inside any `CartExtension.PricingCartCalculator`, `ShippingCartCalculator`, `InventoryCartCalculator`, or `TaxCartCalculator` `calculate()` method when the callout follows any DML statement, SOQL with a `FOR UPDATE` clause, or other uncommitted-work-producing operation in the same synchronous frame.

**How to avoid:** Structure `calculate()` so all HTTP callouts are at the top of the method, before any DML or uncommitted-work operations. If a logging or audit write is needed alongside the callout, defer it to a `Queueable` or `@future` method invoked after the callout completes and the synchronous calculation frame has ended.

---

## Gotcha 2: Only One Class Per Extension Point Name Per Store

**What happens:** Only one `RegisteredExternalService` custom metadata record per Extension Point Name (EPN) per store is active. If two records exist for the same EPN and store, the platform invokes only one class — which one is not guaranteed and may vary by release. The second class is silently skipped with no error or warning.

**When it occurs:** When multiple developers or deployment pipelines independently register calculator classes for the same store without auditing existing registrations. Also occurs when an AppExchange package registers a class for an EPN (e.g., a tax package that registers `CartExtension__Taxes`) and a custom class is then also registered for the same EPN.

**How to avoid:** Before scaffolding any new CartExtension class, query `RegisteredExternalService` custom metadata for the target store and list all registered EPNs. If a registration already exists for the target EPN, extend the existing class rather than creating a competing registration. Document EPN ownership in the project integration architecture record.

---

## Gotcha 3: Raw Card Data Must Never Transit Salesforce

**What happens:** The Commerce payment framework assumes the storefront's card capture form is a provider-hosted iframe or redirect that sends card data directly to the payment gateway, never to Salesforce. If any design routes raw PANs, CVVs, or expiry dates through an Apex endpoint — even transiently for validation or logging — the org is considered in PCI DSS scope for that data path and is not covered by Salesforce's compliance programs.

**When it occurs:** When a developer builds a custom LWC payment form that posts card fields to an Apex REST endpoint for "pre-validation" before handing off to the gateway. Also occurs when the payment gateway's integration guide suggests a server-side tokenization flow without distinguishing Salesforce-hosted vs. gateway-hosted server.

**How to avoid:** Always use the gateway's client-side JavaScript SDK or iframe to capture card fields. The LWC payment component must only receive and forward the opaque token or nonce returned by the provider's client-side capture flow. Apex should only ever see this token, never raw card field values.

---

## Gotcha 4: No Native PIM Connector — Missing External ID Causes Duplicate Product2 Records

**What happens:** Salesforce Commerce has no out-of-the-box PIM integration. If PIM sync jobs use `insert` for all incoming products (or use a query-then-insert pattern without an idempotency key), each sync run creates new `Product2` records for products that already exist. Duplicates accumulate silently — storefront search may display either record, and `PricebookEntry` records associate with only one copy, causing pricing inconsistencies.

**When it occurs:** When the External ID field is not defined on `Product2` before the first sync run, or when the sync job uses `Database.insert()` rather than `Database.upsert()` with the External ID field specified.

**How to avoid:** Define a custom External ID field on `Product2` (marked `External ID` and `Unique`) that holds the PIM system's canonical identifier before any data is loaded. All sync operations — initial load and incremental updates — must use `Database.upsert()` with this External ID field as the upsert key. Run a deduplication check on `Product2` using the External ID field before going live.

---

## Gotcha 5: ExtensionPointName in RegisteredExternalService Is Case-Sensitive

**What happens:** The `ExtensionPointName` field on the `RegisteredExternalService` custom metadata record must exactly match the platform's EPN constant string, including namespace prefix and underscores (e.g., `CartExtension__Pricing`, not `CartExtension_Pricing`, `Pricing`, or `CartExtension__pricing`). An incorrect value results in the calculator class never being invoked — with no error message surfaced in the store UI or standard debug logs.

**When it occurs:** When records are hand-authored in Setup UI without copy-pasting the exact EPN string from the documentation, or when records are created programmatically with a human-readable label substituted for the technical constant.

**How to avoid:** Copy EPN values directly from the Salesforce B2B and D2C Commerce Developer Guide. The correct constants are `CartExtension__Pricing`, `CartExtension__Shipping`, `CartExtension__Inventory`, and `CartExtension__Taxes`. After deploying a new registration, test by triggering a cart recalculation and verifying via debug logs that the calculator class's `calculate()` method is entered.

---

## Gotcha 6: SOM Capture and Refund Require a Separate License

**What happens:** Salesforce Order Management (SOM) provides out-of-the-box fulfillment workflow nodes for payment capture, refund, and order lifecycle orchestration. However, SOM is a separately licensed product. If a Commerce implementation assumes SOM is available without confirming the license, the post-authorization capture step has no platform-provided handler — orders remain in "authorized" state indefinitely.

**When it occurs:** When Commerce is sold and implemented without explicit SOM scoping, particularly in B2B scenarios where the order management requirement was assumed to be included.

**How to avoid:** Confirm SOM license status at project kickoff. If SOM is not licensed, the integration must either use the payment adapter's own capture API (invoked by a custom post-order flow or Platform Event handler) or integrate with a third-party OMS that handles capture on order fulfillment confirmation.
