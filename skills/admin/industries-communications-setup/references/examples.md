# Examples — Industries Communications Setup

## Example 1: Configuring an EPC Bundle for a Triple Play Offer

**Context:** A telecom operator is launching a "Triple Play" bundle (Broadband 100Mbps + Basic TV + Voice Line) in a new Communications Cloud org. The admin needs to model this in EPC so that when an order is placed, the decomposition engine can generate three separate technical fulfillment records.

**Problem:** The admin creates three Product2 records directly ("Broadband 100Mbps", "Basic TV", "Voice Line") and a fourth Product2 record ("Triple Play Bundle") with a custom lookup field pointing to the child products. When an order is placed, Industries Order Management cannot decompose the bundle because it reads EPC Child Item relationships (vlocity_cmt__ProductChildItem__c), not custom lookup fields on Product2. The commercial order is created but no technical order records are generated.

**Solution:**

```text
EPC Configuration Sequence:

1. Create Product Specifications (one per component):
   - "Broadband-Spec" (Type: Service)
   - "TV-Basic-Spec"  (Type: Service)
   - "Voice-Spec"     (Type: Service)

2. Create atomic Product Offerings referencing each Specification:
   - "Broadband 100Mbps" → references Broadband-Spec, priced at $40/mo
   - "Basic TV"          → references TV-Basic-Spec, priced at $20/mo
   - "Voice Line"        → references Voice-Spec, priced at $15/mo

3. Create a bundle Product Offering:
   - "Triple Play Bundle" → priced at $60/mo (discounted)

4. Create ProductChildItem records linking the bundle to each component:
   - Parent: Triple Play Bundle
   - Child 1: Broadband 100Mbps (Quantity: 1)
   - Child 2: Basic TV (Quantity: 1)
   - Child 3: Voice Line (Quantity: 1)

5. Create a Catalog Assignment for each offering → "Consumer Catalog"

6. Test: Place an order for "Triple Play Bundle" and verify that
   Industries Order Management generates three technical order
   line items (one per child item).
```

**Why it works:** The EPC `ProductChildItem` relationship is the decomposition map the Industries Order Management engine reads at runtime. Without these records, the engine has no instruction set for how to decompose the bundle into technical fulfillment actions. The commercial order is created, but the technical order remains empty.

---

## Example 2: Querying Accounts by Subtype Without Mixing Record Types

**Context:** A developer is building an Apex batch job to process all "Service Accounts" in a Communications Cloud org for a periodic service health check. The org also has Billing Accounts and Consumer Accounts stored as Account records.

**Problem:** The developer queries `SELECT Id, Name FROM Account` and processes all returned records as if they are Service Accounts. The batch triggers service health logic on Billing Accounts and Consumer Accounts, producing incorrect status updates and corrupted service records.

**Solution:**

```soql
-- Always filter by RecordType.DeveloperName, not RecordType.Name
SELECT Id, Name, ParentId, vlocity_cmt__BillingAccountId__c
FROM Account
WHERE RecordType.DeveloperName = 'Service_Account'
AND IsDeleted = false

-- To query the Billing Account parent alongside:
SELECT Id, Name, ParentId, Parent.RecordType.DeveloperName
FROM Account
WHERE RecordType.DeveloperName = 'Service_Account'
AND Parent.RecordType.DeveloperName = 'Billing_Account'
```

```apex
// Apex equivalent — never query Account without RecordType filter in Comms Cloud
List<Account> serviceAccounts = [
    SELECT Id, Name, ParentId
    FROM Account
    WHERE RecordType.DeveloperName = 'Service_Account'
    LIMIT 200
];
```

**Why it works:** `RecordType.DeveloperName` is locale-stable (unlike `RecordType.Name`, which changes with translation settings). Filtering at the SOQL level eliminates the possibility of processing Billing or Consumer Account records in logic designed for Service Accounts, preventing data integrity failures at the source.

---

## Anti-Pattern: Using Standard Contract Workflow to Activate Communications Contracts

**What practitioners do:** After configuring a subscriber contract, they use a standard Salesforce Process Builder or Flow to set `Contract.Status = 'Activated'`, mirroring how standard CRM contracts are activated.

**What goes wrong:** Standard contract activation bypasses the Industries Contract Management activation sequence. The entitlement creation step, provisioning trigger, and billing event generation that Communications Cloud registers on the Industries activation path are never fired. The contract shows "Activated" in the UI but no entitlements are created, no provisioning order is generated, and the billing system receives no activation event. The subscriber appears active in the CRM but has no provisioned services.

**Correct approach:** Use the Industries Contract Management activation action (available via the Industries managed package) which executes the full activation sequence:
1. Validate contract terms and entitlement eligibility
2. Create Entitlement records linked to the service account
3. Trigger the provisioning order via Industries Order Management
4. Fire the billing activation event to the billing system

This is exposed as an Apex invocable action or REST API endpoint in the vlocity_cmt namespace, not as a field update on the Contract standard object.
