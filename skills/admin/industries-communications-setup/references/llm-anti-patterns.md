# LLM Anti-Patterns — Industries Communications Setup

Common mistakes AI coding assistants make when generating or advising on Industries Communications Setup.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Querying Account Without RecordType Filter in Communications Cloud

**What the LLM generates:**

```soql
SELECT Id, Name, Phone, BillingAddress FROM Account WHERE AccountSource = 'Web'
```

Or in Apex:
```apex
List<Account> accounts = [SELECT Id, Name FROM Account WHERE OwnerId = :UserInfo.getUserId()];
```

**Why it happens:** The LLM is trained predominantly on standard CRM Salesforce patterns where Account is a single logical type. It has no signal that the org is Communications Cloud where Account is segmented into Billing, Service, and Consumer subtypes via RecordType.

**Correct pattern:**

```soql
-- Billing Accounts only
SELECT Id, Name, BillingAddress FROM Account
WHERE RecordType.DeveloperName = 'Billing_Account'

-- Service Accounts only
SELECT Id, Name, ParentId FROM Account
WHERE RecordType.DeveloperName = 'Service_Account'

-- Multiple subtypes — explicit IN list required
SELECT Id, Name, RecordType.DeveloperName FROM Account
WHERE RecordType.DeveloperName IN ('Billing_Account', 'Service_Account')
```

**Detection hint:** Any SOQL query on `FROM Account` without `RecordType.DeveloperName` in the WHERE clause in a Communications Cloud context is likely wrong. Regex: `FROM\s+Account\b` not followed by `RecordType\.DeveloperName`.

---

## Anti-Pattern 2: Using Salesforce Commerce Order Management APIs for Communications Cloud Orders

**What the LLM generates:**

```apex
// LLM suggests using OrderSummary and FulfillmentOrder objects
OrderSummary os = [SELECT Id, Status FROM OrderSummary LIMIT 1];
FulfillmentOrder fo = new FulfillmentOrder(OrderSummaryId = os.Id, Status = 'Draft');
insert fo;
```

Or REST API calls to `/services/data/vXX.0/commerce/order-management/...`.

**Why it happens:** "Order management" + "Salesforce" returns Commerce Order Management as the top result in most training data. The LLM conflates Salesforce Order Management (B2C/B2B Commerce) with Industries Order Management (Communications Cloud), which are entirely different platforms.

**Correct pattern:**

```text
In Communications Cloud, order management uses the vlocity_cmt namespace:
- Commercial orders: standard Order object with vlocity_cmt extensions
- Technical orders: vlocity_cmt__DecomposedOrder__c and related objects
- Decomposition: triggered via Industries Order Management rules, not Commerce APIs
- No OrderSummary, FulfillmentOrder, or /commerce/ REST endpoints apply
```

**Detection hint:** Any reference to `OrderSummary`, `FulfillmentOrder`, `OrderDeliveryGroup`, or `/commerce/order-management/` endpoints in a Communications Cloud context is wrong. Look for `vlocity_cmt__` namespace prefixes in correct implementations.

---

## Anti-Pattern 3: Creating Products Directly in Product2 Without EPC

**What the LLM generates:**

```apex
Product2 broadband = new Product2(
    Name = 'Broadband 100Mbps',
    ProductCode = 'BB-100',
    IsActive = true
);
insert broadband;

PricebookEntry pbe = new PricebookEntry(
    Pricebook2Id = [SELECT Id FROM Pricebook2 WHERE IsStandard = true LIMIT 1].Id,
    Product2Id = broadband.Id,
    UnitPrice = 40.00,
    IsActive = true
);
insert pbe;
```

**Why it happens:** The LLM defaults to standard Salesforce product creation patterns (Product2 + PricebookEntry), which work correctly for standard orgs, CPQ, and Commerce. It lacks awareness that Communications Cloud requires EPC (Enterprise Product Catalog) for products to be usable in order decomposition.

**Correct pattern:**

```text
Products in Communications Cloud must be configured through EPC:
1. Create Product Specification in EPC app (not Product2 directly)
2. Create Product Offering referencing the Specification (with pricing in EPC pricing model)
3. Create Catalog Assignment linking the Offering to a Catalog
4. The EPC creates the underlying Product2 record with correct namespace field population

Directly inserting Product2 without EPC creates a product that:
- Cannot be decomposed by Industries Order Management
- Is not visible in EPC-driven order capture UIs
- Will not generate technical order records on purchase
```

**Detection hint:** Any Apex or data load that inserts `Product2` records without corresponding `vlocity_cmt__ProductOffering__c` or EPC Catalog Assignment creation is an anti-pattern in Communications Cloud.

---

## Anti-Pattern 4: Using Standard Contract Status Field Update to Activate Communications Contracts

**What the LLM generates:**

```apex
Contract c = [SELECT Id, Status FROM Contract WHERE Id = :contractId];
c.Status = 'Activated';
update c;
```

Or a Flow that sets `Contract.Status` to "Activated" via a field update action.

**Why it happens:** Standard Salesforce contract activation is a simple field update. The LLM applies this pattern to Communications Cloud contracts without knowing that Industries Contract Management requires a specific activation sequence that triggers entitlement creation, provisioning orders, and billing events.

**Correct pattern:**

```text
Communications Cloud contract activation must go through the Industries
Contract Management activation action:

1. Use the Industries Contract Management invocable action (vlocity_cmt namespace)
   exposed as an Apex method or REST endpoint — NOT a direct Status field update.
2. The activation sequence includes:
   a. Validate contract terms and entitlement eligibility
   b. Create Entitlement records on the Service Account
   c. Trigger provisioning order via Industries Order Management
   d. Fire billing activation event
3. Direct Status = 'Activated' updates bypass all four steps above.
   The contract shows Activated in the UI but no services are provisioned.
```

**Detection hint:** Any code that sets `Contract.Status = 'Activated'` via a field update (Apex, Flow, or Process Builder) in a Communications Cloud org is bypassing the Industries activation sequence. Look for vlocity_cmt invocable action references in correct implementations.

---

## Anti-Pattern 5: Assuming OmniStudio Generic Configuration Applies to Communications Cloud

**What the LLM generates:**

```text
To configure your order capture flow in Communications Cloud:
1. Create an OmniScript with the DataRaptor steps
2. Add a product selection step using a generic lookup to Product2
3. Configure the FlexCard to display the product list
```

**Why it happens:** OmniStudio (formerly Vlocity) is used across multiple Industries clouds and in standalone configurations. The LLM generalizes OmniStudio patterns from any Industries context (or generic OmniStudio documentation) without applying Communications Cloud-specific configuration requirements, particularly EPC integration in product selection steps.

**Correct pattern:**

```text
In Communications Cloud, OmniStudio flows for order capture must:
1. Use EPC-aware DataRaptor extracts that query EPC catalog objects
   (not a generic Product2 lookup)
2. Reference vlocity_cmt catalog assignment objects to filter products
   by the subscriber's account segment (Consumer vs. Business catalog)
3. Use Communications Cloud-specific FlexCard templates that reference
   the EPC product model fields, not generic Product2 fields
4. Integrate with Industries Order Management for order submission,
   not a generic Salesforce record insert

Generic OmniStudio patterns that query Product2 directly will not
populate EPC child item data, will not apply catalog segment eligibility,
and will produce orders that cannot be decomposed.
```

**Detection hint:** Any OmniStudio configuration in a Communications Cloud context that references `Product2` without EPC catalog filtering (by Catalog Assignment or vlocity_cmt namespace fields) is likely missing Communications Cloud-specific configuration.
