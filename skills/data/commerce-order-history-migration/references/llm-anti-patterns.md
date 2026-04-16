# LLM Anti-Patterns — Commerce Order History Migration

Common mistakes AI coding assistants make when generating or advising on Salesforce Order Management historical order migrations.

---

## Anti-Pattern 1: Inserting OrderSummary via Bulk API or Direct DML

**What the LLM generates:** A Data Loader job or Bulk API script that inserts OrderSummary records directly after inserting Order and OrderItem records.

**Why it happens:** LLMs treat OrderSummary as a standard insertable object like Order or OrderItem. They do not model the ConnectAPI requirement.

**Correct pattern:** OrderSummary must be created via `ConnectAPI.OrderSummary.createOrderSummary()` in Apex or the "Create Order Summary" Flow core action. Direct DML either fails or creates malformed records that break Order Management state.

**Detection hint:** If instructions include a Data Loader job or DML insert statement targeting the `OrderSummary` object, the approach is incorrect.

---

## Anti-Pattern 2: Using LifeCycleType = Managed for Historical Orders

**What the LLM generates:** ConnectAPI code or Flow configuration that creates OrderSummary with `LifeCycleType = MANAGED` (or omits the field, defaulting to Managed) for historical orders.

**Why it happens:** LLMs default to the standard lifecycle type without considering whether the orders are historical or active.

**Correct pattern:** Historical orders that are no longer being serviced must use `LifeCycleType = UNMANAGED`. This disables refund, cancel, and fulfillment core actions on those records, preventing agents from accidentally taking actions on historical data.

**Detection hint:** If ConnectAPI code does not set `LifeCycleType` explicitly, or sets it to `MANAGED` for a historical order migration, the value is wrong.

---

## Anti-Pattern 3: Omitting OrderDeliveryGroup from the Load Sequence

**What the LLM generates:** A migration plan that loads Order and then OrderItem directly, skipping OrderDeliveryGroup.

**Why it happens:** LLMs model Order → OrderItem as a standard parent-child relationship like in CPQ or standard Salesforce orders, not knowing that Order Management inserts OrderDeliveryGroup as a mandatory intermediate object.

**Correct pattern:** The correct load sequence is: Order (Draft) → OrderDeliveryGroup → OrderItem → Order Activation → OrderSummary via ConnectAPI. OrderItem requires a valid OrderDeliveryGroup reference; skipping it causes a field integrity exception.

**Detection hint:** If the migration plan shows OrderItem being inserted before or without OrderDeliveryGroup, the sequence is incorrect.

---

## Anti-Pattern 4: Creating OrderSummary Before Order Activation

**What the LLM generates:** ConnectAPI or Flow code that creates OrderSummary immediately after inserting the Order record, before the Order is activated.

**Why it happens:** LLMs do not model the Draft → Activated state machine transition as a prerequisite for ConnectAPI OrderSummary creation.

**Correct pattern:** Order must be in Activated status before `ConnectAPI.OrderSummary.createOrderSummary()` can be called. Insert Order (Draft), insert child objects, then update Order.Status = Activated, then create OrderSummary.

**Detection hint:** If ConnectAPI is called in the same transaction or batch step as Order insertion without an intervening status update, it will fail with `FIELD_INTEGRITY_EXCEPTION`.

---

## Anti-Pattern 5: Conflating Salesforce Order Management with B2C Commerce Cloud Order Import

**What the LLM generates:** Instructions referencing Business Manager, OCAPI, or SCAPI for order migration, when the target is Salesforce Order Management on the CRM platform.

**Why it happens:** LLMs conflate "Salesforce Commerce order migration" with "Salesforce B2C Commerce Cloud order import" — two entirely different platforms with different APIs and object models.

**Correct pattern:** Salesforce Order Management uses the standard Order object, ConnectAPI, and Bulk API on the CRM platform. B2C Commerce Cloud (formerly Demandware) uses Business Manager and OCAPI/SCAPI in a separate SaaS system. Confirm which platform is the target before applying any migration approach.

**Detection hint:** If instructions reference Business Manager, OCAPI, SCAPI, or cartridges in the context of an Order Management migration, the wrong platform is being described.
