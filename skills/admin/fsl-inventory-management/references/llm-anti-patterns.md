# LLM Anti-Patterns — FSL Inventory Management

Common mistakes AI coding assistants make when generating or advising on FSL Inventory Management.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Suggesting Direct Update of QuantityOnHand to Adjust Stock

**What the LLM generates:** Code or instructions that directly set the `QuantityOnHand` field on a `ProductItem` record via Apex DML, Flow "Update Records", or Data Loader to correct an inventory discrepancy.

```apex
// WRONG — Do not do this
ProductItem pi = [SELECT Id, QuantityOnHand FROM ProductItem WHERE Id = :itemId];
pi.QuantityOnHand = 17;
update pi;
```

**Why it happens:** `QuantityOnHand` looks like a writable numeric field. LLMs trained on generic CRM patterns assume all numeric fields are directly updatable. The platform-managed nature of this field is a domain-specific constraint that is not apparent from the schema alone.

**Correct pattern:**

```
Create an adjusting ProductTransfer:
- Source: a dedicated "Inventory Adjustment" Location record
- Destination: the target Location
- QuantitySent: the delta (positive adjustment)
- Status: set to Received immediately

This fires the platform-managed QuantityOnHand update and creates a ProductItemTransaction audit record.
```

**Detection hint:** Any code or instruction containing `QuantityOnHand` on the left side of an assignment (`pi.QuantityOnHand =`) targeting a `ProductItem` record is wrong. Flag immediately.

---

## Anti-Pattern 2: Creating or Deleting ProductItemTransaction Records to Manage the Ledger

**What the LLM generates:** Instructions to delete "duplicate" or "incorrect" ProductItemTransaction records, or Apex code that inserts ProductItemTransaction records to represent manual adjustments.

```apex
// WRONG — Do not do this
List<ProductItemTransaction> toDelete = [SELECT Id FROM ProductItemTransaction WHERE ProductItemId = :pid];
delete toDelete;
```

**Why it happens:** LLMs see ProductItemTransaction as just another object in the schema and treat it as configurable. The auto-generated, read-only nature of these records is domain-specific knowledge. The LLM does not know that these records are written by the platform trigger chain and that DML against them corrupts the ledger.

**Correct pattern:**

```
ProductItemTransaction records are auto-generated and read-only.
Never create, update, or delete them directly.
Use SOQL queries on ProductItemTransaction to DIAGNOSE discrepancies.
Use adjusting ProductTransfer records to CORRECT discrepancies.
```

**Detection hint:** Any `insert`, `update`, or `delete` DML targeting `ProductItemTransaction` is wrong. Any Flow action on `ProductItemTransaction` other than "Get Records" is wrong.

---

## Anti-Pattern 3: Assuming ProductTransfer Creation Immediately Updates QuantityOnHand

**What the LLM generates:** Documentation or code that describes creating a ProductTransfer and then immediately reads or asserts the updated `QuantityOnHand` as if the transfer already applied.

```
// WRONG ASSUMPTION in documentation or test
ProductTransfer pt = new ProductTransfer(...);
insert pt;
// LLM then asserts: "QuantityOnHand on destination is now incremented"
ProductItem dest = [SELECT QuantityOnHand FROM ProductItem WHERE Id = :destItemId];
System.assertEquals(expectedQty, dest.QuantityOnHand); // This will FAIL
```

**Why it happens:** LLMs model inventory systems generically — in most systems, recording a stock transfer is equivalent to moving stock. The FSL-specific constraint that QuantityOnHand only updates when status = Received is non-obvious and counterintuitive relative to standard inventory modeling.

**Correct pattern:**

```
// Correct: QuantityOnHand updates only when ProductTransfer status = Received
ProductTransfer pt = new ProductTransfer(
    SourceLocationId = warehouseLocId,
    DestinationLocationId = vanLocId,
    QuantitySent = 5,
    Status = 'Received'   // Must be Received to trigger QuantityOnHand update
);
insert pt;
// Now QuantityOnHand has updated on source and destination ProductItems
```

**Detection hint:** Look for test assertions or narrative text that implies QuantityOnHand changes after ProductTransfer insert without setting status = Received. Also flag any workflow documentation that stops at "create the transfer" without including the Received step.

---

## Anti-Pattern 4: Omitting IsMobile Flag When Creating Van Location Records

**What the LLM generates:** Setup instructions or Data Loader templates for creating van Location records that do not include the `IsMobile` field, or that leave it at its default `false` value.

```csv
// WRONG — missing IsMobile column in a Data Loader template for vans
Name,LocationType,Latitude,Longitude
"Technician Van - Jones","Van",37.7749,-122.4194
```

**Why it happens:** LLMs generating Location record templates focus on the obvious fields (Name, Type, coordinates). The `IsMobile` flag is a FSL-specific field that controls mobile app visibility — not a standard geolocation concept — and LLMs without FSL-specific training data skip it.

**Correct pattern:**

```csv
// CORRECT — IsMobile must be true for technician vans
Name,LocationType,Latitude,Longitude,IsMobile
"Technician Van - Jones","Van",37.7749,-122.4194,true
```

Or in Apex:
```apex
Location__c van = new Location__c(
    Name = 'Technician Van - Jones',
    LocationType__c = 'Van',
    IsMobile__c = true  // Required for FSL mobile app visibility
);
```

**Detection hint:** Any Location record creation template for van/truck locations that does not explicitly set `IsMobile = true` is incomplete. Flag and add the field.

---

## Anti-Pattern 5: Using ProductTransfer as a Substitute for ProductConsumed on Work Orders

**What the LLM generates:** Instructions to record parts usage on a work order by creating a ProductTransfer from the technician's van to a dummy "consumed" Location, rather than creating a ProductConsumed record on the Work Order.

```
// WRONG — do not use ProductTransfer to record parts usage on a WO
// Create ProductTransfer: source = van, destination = "Consumed Parts" location
// This is NOT how FSL records job-level parts consumption
```

**Why it happens:** LLMs that understand the general concept of "moving stock out of a van when parts are used" model this as a transfer to a sink. They are unaware of the `ProductConsumed` object, which is the FSL-specific mechanism for associating parts usage with a Work Order.

**Correct pattern:**

```
Create a ProductConsumed record on the Work Order:
- WorkOrderId: the Work Order that consumed the part
- Product2Id: the product consumed
- QuantityConsumed: how many units
- SourceProductItemId: the van's ProductItem for this product

This decrements QuantityOnHand on the van ProductItem AND links consumption to the Work Order for cost reporting.
ProductTransfer is for moving stock between locations — not for recording parts usage on jobs.
```

**Detection hint:** Any workflow that describes parts usage on a Work Order using ProductTransfer records (especially with a dummy "consumed" or "waste" destination location) is using the wrong object. The correct object for job-level parts consumption is always `ProductConsumed`.

---

## Anti-Pattern 6: Recommending a Native Cycle-Count Screen That Does Not Exist

**What the LLM generates:** Instructions or screenshots describing a built-in "Cycle Count" or "Physical Inventory" screen in Field Service Lightning or the FSL mobile app that allows technicians to enter physical counts and auto-reconcile.

```
// WRONG — this screen does not exist in FSL
// "Navigate to FSL Mobile > Inventory > Cycle Count to submit your physical count"
```

**Why it happens:** Cycle count is a standard feature of enterprise WMS (Warehouse Management System) software. LLMs trained on general inventory management content assume this capability exists in any inventory system, including FSL. It does not — FSL has no native cycle-count UI.

**Correct pattern:**

```
FSL has no native cycle-count screen.
To implement cycle counting:
1. Build a custom Screen Flow or LWC that queries ProductItems for a Location
2. Display QuantityOnHand alongside a text input for physical count
3. On submit, compute delta and create an adjusting ProductTransfer (set to Received)
4. Optionally log the count event in a custom object for audit purposes
```

**Detection hint:** Any mention of a native "Cycle Count", "Physical Count", or "Inventory Reconciliation" screen in the FSL mobile app or Salesforce UI is a hallucination. This feature does not exist natively as of Spring '25.
