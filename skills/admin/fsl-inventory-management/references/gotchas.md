# Gotchas — FSL Inventory Management

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: ProductItemTransaction Records Are Auto-Generated — Manual DML Corrupts QuantityOnHand

**What happens:** Every time `QuantityOnHand` on a ProductItem changes (via ProductTransfer Received, ProductConsumed, or ReturnOrderLineItem), Salesforce automatically creates a `ProductItemTransaction` record as an audit entry. If a developer, admin, or integration directly creates, updates, or deletes these records via Apex DML, Data Loader, or Flow, the transaction log diverges from the actual `QuantityOnHand`. There is no platform-native tool to repair a corrupted inventory ledger.

**When it occurs:** Most commonly when developers discover ProductItemTransaction in the schema and attempt to use it as a "manual adjustment" mechanism, or when data migration scripts import historical transactions directly, or when admins delete "duplicate-looking" transaction records to clean up.

**How to avoid:** Treat ProductItemTransaction as read-only in all custom code, integrations, and admin tooling. Use adjusting ProductTransfer records (from/to a dedicated "adjustment" Location) as the only supported mechanism to correct QuantityOnHand discrepancies. Document this constraint in developer guidelines and validation rules cannot prevent all DML paths, so code review gates are essential.

---

## Gotcha 2: QuantityOnHand Updates on ProductTransfer Received — Not on Creation

**What happens:** Creating a ProductTransfer record does NOT decrement the source ProductItem's `QuantityOnHand` or increment the destination's. The update only fires when the ProductTransfer status is set to **Received**. Organizations that create transfers but never enforce the Received step end up with source locations perpetually overstating on-hand counts and destination locations (vans) perpetually understating them.

**When it occurs:** Any time the "Received" step is treated as optional, administrative overhead, or is not operationally enforced. Common in go-live scenarios where the ProductRequest → ProductTransfer workflow is configured but the field operations team was not trained on marking transfers Received upon physical arrival.

**How to avoid:** Build a Record-Triggered Flow or validation check that alerts dispatchers when a ProductTransfer has been in transit status for more than N days without being marked Received. Add the ProductTransfer status field to the dispatcher's view so it is visible. Train operations teams that physical stock receipt must always be mirrored by a Received status update in Salesforce.

---

## Gotcha 3: Van Stock Requires Location Record with Mobile Location Checked

**What happens:** Technicians log into the FSL mobile app but see no inventory. ProductItem records exist and QuantityOnHand is correct, but the mobile app shows nothing. The cause is that the technician's van Location record has `IsMobile = false` (the default). The FSL mobile app only surfaces locations where `IsMobile = true` in the inventory experience.

**When it occurs:** During FSL rollout when Location records are created for vans via Data Loader or manual entry without explicitly setting the Mobile Location field. The field defaults to unchecked. This is consistently overlooked because the Location record appears correct in the UI and the ProductItems appear to exist.

**How to avoid:** During Location record creation for vans and trucks, explicitly set `IsMobile = true`. If retroactively fixing existing Location records, update the field in bulk (Data Loader or Flow), then verify technician inventory visibility in the FSL mobile app with a test login. Add a validation rule or field history tracking on the Mobile Location field if operational accuracy requires an audit trail of when this flag was changed.

---

## Gotcha 4: No Native Cycle-Count UI — Custom Build Required

**What happens:** Field service orgs expecting a built-in "count sheet" or physical inventory reconciliation screen find that Field Service Lightning has no such native feature. There is no standard way for a technician to submit a physical count and have the system reconcile the discrepancy. Attempting to use the ProductItem list view for manual count updates is not a supported pattern.

**When it occurs:** Post-go-live, when operations management requests a monthly or quarterly physical stock count to verify system accuracy. This is a standard warehouse management capability that practitioners expect to be native but is absent from FSL.

**How to avoid:** Plan for this requirement at design time. The recommended pattern is: (1) build a Screen Flow or LWC that queries ProductItems for a given Location, displays `QuantityOnHand`, and collects a physical count input; (2) compute the delta; (3) create an adjusting ProductTransfer with a dedicated "Inventory Adjustment" Location as source or destination, set to Received immediately. Document and test this pattern before go-live to avoid post-launch scrambling.

---

## Gotcha 5: ProductConsumed SourceProductItemId Must Reference an Existing ProductItem

**What happens:** When a technician or dispatcher creates a ProductConsumed record on a Work Order, the `SourceProductItemId` (or the Product2 + Location lookup combination that resolves to a ProductItem) must reference an existing ProductItem record. If no ProductItem exists for that product at the technician's van location, the record creation fails with a validation error or lookup exception. Technicians then cannot log parts used on the job.

**When it occurs:** When ProductItem records are not pre-created for every product/location combination that technicians are expected to carry. Common when new products are added to the catalog but no one creates the corresponding ProductItem at each van location. Also occurs when new technician vans are added without seeding their ProductItem records.

**How to avoid:** Establish a process: whenever a new product is approved for field use or a new van location is created, create the corresponding ProductItem records. Automate this with a Record-Triggered Flow on Location or Product2 creation that generates ProductItem stubs (with QuantityOnHand = 0) so the lookup always resolves, even before stock is physically loaded. Opening stock can then be transferred in via the standard ProductTransfer workflow.
