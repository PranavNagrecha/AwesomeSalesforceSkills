# Examples — Consumer Goods Cloud Setup

## Example 1: The Load Order for Retail Execution Reference Data

**Scenario:** A beverage manufacturer is standing up CG Cloud across 4,200 stores in three banners, with planogram compliance in scope.

**Problem:** Every one of these objects has a hard dependency on the one above it, and loading out of order produces records that look fine and score nothing. The dependency is not obvious from the object names, and half the model is standard while the other half sits behind the `cgcloud__` namespace.

**Solution:** Load in dependency order, standard layer first:

```
1. Account                       business relationship (the retailer / banner)
2. RetailStore                   "physical retail stores associated to business accounts"
3. RetailLocationGroup           "Group retail stores based on shared features, such as
                                  size, location, or part of a retail chain"
4. RetailStoreGroupAssignment    junction: store -> group
5. InStoreLocation               "locations within a retail store's layout such as
                                  aisles, shelves, or backrooms"
6. Product2 / ProductCategory    catalogue
7. Assortment + AssortmentProduct   "a list of products that are eligible for sale in a store"
8. StoreAssortment               assortment -> store, store group, or account
9. StoreProduct                  "a product to a retail store or to a specific in-store location"
10. AssessmentIndicatorDefinition   "markers of compliance ... to compare target and actual values"
11. RetailStoreKpi               targets, mapped to store GROUPS (not individual stores)
--- managed package layer ---
12. cgcloud__Visit_Template__c   "Template that describes the basic call behavior"
13. cgcloud__Trip_List__c        "plan visits based on a predefined sequence of customers"
```

A pre-go-live check that catches the most common gap — indicators with no target for a store group in scope:

```sql
-- The lookup on RetailStoreKpi is RetailStoreGroupId ("ID of the retail
-- store group for which the assessment indicator definition is defined"),
-- not RetailLocationGroupId -- the field name and the object name differ.
SELECT Id, Name
FROM RetailLocationGroup
WHERE Id NOT IN (SELECT RetailStoreGroupId FROM RetailStoreKpi)
```

**Why it works:** The order follows the actual foreign keys, so nothing is inserted against a parent that does not exist yet. Step 11 is the one teams skip: targets attach to store groups, so a group created after the KPI load silently has no targets and every visit against it records an actual with nothing to score against. Confirm each object's field API names against the Consumer Goods Cloud developer guide before building the load files.

---

## Example 2: Where a Visit's Work Actually Lives

**Scenario:** A weekly Tier-1 visit: merchandising check, order capture, endcap photo for an active promotion, signature on completion.

**Problem:** Each of those four is a different object, and two of them are not what their names suggest. Reps see one screen; the model underneath is five tables.

**Solution:**

```
Visit                            "information related to a field rep's visit to a retail
                                  store where they perform retail activities" (API 47.0+)
├── Visitor                      "the sales reps performing visits"
├── VisitedParty                 "the contact person at the account that's being visited"
├── AssessmentTask               "planogram check, inventory check, promotion check,
│   │                             in-store survey, or custom task in stores"
│   ├── AssessmentTaskContentDocument   photos: "content documents to visits, tasks,
│   │                                    promotions, or planograms"
│   └── RetailVisitKpi           "the actual information during a visit against the
│                                 defined assessment indicator definition and target values"
├── AssessmentTaskOrder          "an order activity that the sales rep can perform
│                                 during a visit to stores"
├── DeliveryTask                 "shipments and orders to be delivered to a store in a visit"
└── SignatureTask                "signature-related information that a visitor captures
    └── SignatureTaskLineItem     as part of a visit"
```

The promotion the endcap check scores against is scoped separately:

```
Promotion                        "promotional activities that are either part of a campaign
                                  or isolated targeted promotions to run at retail stores"
├── PromotionChannel             "Associate a promotion with a store, store group, or an account"
├── PromotionProduct             promotion -> product
└── PromotionProductCategory     promotion -> product category
```

**Why it works:** Separating the task from its result (`AssessmentTask` vs `RetailVisitKpi`) is what makes the same task definition reusable across store tiers with different targets. Separating the promotion from its scope (`PromotionChannel`) is what lets one promotion run in two banners at different store groups without duplicating it. Reporting joins `RetailVisitKpi` to `RetailStoreKpi` through the shared `AssessmentIndicatorDefinition` — read either side alone and the compliance number is meaningless.

---

## Anti-Pattern: Building the Retail Hierarchy as Account Record Types

**What practitioners do:** Model Retailer → Banner → Store as an Account hierarchy with a "Retail Store" record type on the leaf, because that is how a general Salesforce data model would express it:

```xml
<!-- WRONG. Visits, KPIs, assortments and store products all relate to
     RetailStore, which is its own standard object. -->
<RecordType xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Retail_Store</fullName>
    <label>Retail Store</label>
    <active>true</active>
</RecordType>
```

**What goes wrong:** `RetailStore` is a standard object — "Create records for physical retail stores associated to business accounts" — and every retail-execution object relates to it, not to an Account. The typed Accounts have nothing to attach visits, KPIs, store products, or in-store locations to. By the time this surfaces, the Accounts are already referenced by contacts and opportunities and cannot be retyped away.

**Correct approach:** Keep the two layers distinct and let each do its job:

```
Account (Retailer)                 the commercial relationship
  └── Account (Banner)             optional, if banners contract separately
        └── RetailStore            the physical location a rep visits
              └── InStoreLocation  aisle / shelf / backroom
```

Segment for visit targeting with `RetailLocationGroup` and `RetailStoreGroupAssignment` rather than with record types — grouping is many-to-many, so one store can belong to a size-based group and a chain-based group at once, which a record type cannot express. Do this before the first `Visit` or trip-list record exists.
