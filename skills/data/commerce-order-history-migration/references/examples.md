# Examples — Commerce Order History Migration

## Example 1: OrderSummary Not Created After Bulk API Insert

**Scenario:** A B2C retailer migrated 80,000 historical orders from a legacy OMS to Salesforce Order Management. They inserted Order, OrderItem, and OrderSummary records via Bulk API. The job completed successfully, but Order Management reports showed all orders with missing summary data.

**Problem:** OrderSummary cannot be created via direct DML or Bulk API. It must be created through `ConnectAPI.OrderSummary.createOrderSummary()` or the "Create Order Summary" Flow core action. Direct DML inserts either fail or create malformed records that break Order Management internal state.

**Solution:**
1. Delete the malformed OrderSummary records created by the direct insert
2. Confirm all Orders are in Activated status
3. Run a Batch Apex class calling `ConnectAPI.OrderSummary.createOrderSummary()` with `LifeCycleType = UNMANAGED` for each Order
4. Validate: `SELECT COUNT() FROM OrderSummary WHERE Order.Status = 'Activated'`

**Why this works:** ConnectAPI initializes Order Management's internal state machine correctly and calculates summary totals that Order Management reports and actions depend on.

---

## Example 2: Historical Orders with LifeCycleType = Managed Enable Accidental Refunds

**Scenario:** A retailer migrated 3 years of historical closed orders. After migration, agents saw Refund and Cancel buttons on orders closed for years. An agent accidentally clicked Refund on a historical order, triggering a financial transaction.

**Problem:** OrderSummary records were created with the default `LifeCycleType = Managed`, which enables all Order Management core actions including refund and cancel. Historical orders need `LifeCycleType = Unmanaged` to disable these actions.

**Solution:**
1. Delete incorrectly created OrderSummary records
2. Re-create via ConnectAPI with `LifeCycleType = UNMANAGED`
3. Validate: `SELECT Id, LifeCycleType FROM OrderSummary WHERE LifeCycleType = 'UNMANAGED' LIMIT 5`

**Prevention:** During planning, always specify LifeCycleType = Unmanaged for orders not actively being serviced.

---

## Example 3: ConnectAPI OrderSummary Creation Fails for Draft Orders

**Scenario:** A developer ran Batch Apex to create OrderSummary records immediately after inserting Order records with Status = Draft. The batch failed with `FIELD_INTEGRITY_EXCEPTION` for every record.

**Problem:** `ConnectAPI.OrderSummary.createOrderSummary()` requires the Order to be in Activated status. Draft orders cannot have OrderSummary records.

**Solution:**
1. After inserting Order (Draft) + OrderDeliveryGroup + OrderItem, run a Bulk API update to set Order Status = Activated
2. Confirm: `SELECT Id FROM Order WHERE Status = 'Activated' AND Id IN :migratedOrderIds`
3. Then run the ConnectAPI OrderSummary creation batch

**Why this works:** Order Management requires Orders to be fully committed (Activated) before summary initialization. Draft status indicates an uncommitted order still subject to edits.
