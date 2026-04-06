# LLM Anti-Patterns — Product Catalog Data Model

Common mistakes AI coding assistants make when generating or advising on Salesforce product catalog data model.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Inserting Custom PricebookEntries Without First Inserting Standard PricebookEntries

**What the LLM generates:** Code or a load plan that inserts a custom PricebookEntry immediately after inserting a Product2 — skipping the Standard PricebookEntry step entirely.

**Why it happens:** LLMs trained on general OOP patterns treat PricebookEntry as a simple junction object. The Standard PBE prerequisite is a Salesforce-specific platform constraint not obvious from the object's field list.

**Correct pattern:**

```apex
// Step 1: Get Standard Pricebook ID
Id standardPbId = [SELECT Id FROM Pricebook2 WHERE IsStandard = true LIMIT 1].Id;

// Step 2: Insert Standard PBE FIRST
PricebookEntry stdPbe = new PricebookEntry(
    Pricebook2Id = standardPbId,
    Product2Id   = p.Id,
    UnitPrice    = 99.00,
    IsActive     = true
);
insert stdPbe;

// Step 3: Only THEN insert custom PBE
PricebookEntry customPbe = new PricebookEntry(
    Pricebook2Id     = customPricebookId,
    Product2Id       = p.Id,
    UseStandardPrice = false,
    UnitPrice        = 79.00,
    IsActive         = true
);
insert customPbe;
```

**Detection hint:** Any Apex snippet or CSV load plan that creates a custom PricebookEntry without a prior Standard PricebookEntry insert for the same Product2 is wrong. Search the output for "PricebookEntry" — if a custom Pricebook2Id appears without a preceding Standard PBE insert, flag it.

---

## Anti-Pattern 2: Hardcoding the Standard Pricebook ID

**What the LLM generates:** Apex code, CSV files, or configuration snippets that embed a literal Pricebook2 ID for the Standard Pricebook.

**Why it happens:** LLMs extrapolate from examples where an ID is shown in a snippet and assume it can be used as-is. They may not know that the Standard Pricebook ID is org-specific and non-portable.

**Correct pattern:**

```apex
// Production code — query at runtime
Id standardPbId = [SELECT Id FROM Pricebook2 WHERE IsStandard = true LIMIT 1].Id;

// Apex test code — use the platform method
Id standardPbId = Test.getStandardPricebookId();
```

**Detection hint:** Any literal `'01s...'` Salesforce record ID assigned to a pricebook variable in generated code or a CSV is a red flag. Flag any Apex code where a string starting with `01s` is assigned to a pricebook-related variable.

---

## Anti-Pattern 3: Setting Both UseStandardPrice = true and UnitPrice in the Same Record

**What the LLM generates:** A CSV template or Apex code that sets `UseStandardPrice = true` on a custom PricebookEntry while also populating the `UnitPrice` field.

**Why it happens:** LLMs treat `UseStandardPrice` as a flag that copies the price at insert time (like a default value), and assume providing an explicit price would override it. In reality, the two fields are mutually exclusive — the platform rejects the combination.

**Correct pattern:**

```
UseStandardPrice = true  → UnitPrice must be blank/omitted
UseStandardPrice = false → UnitPrice is required and must be numeric
```

**Detection hint:** Search generated CSV or DML code for rows where `UseStandardPrice` is `true` AND `UnitPrice` is also non-null/non-blank. That combination is always invalid.

---

## Anti-Pattern 4: Using SOQL to Query the Standard Pricebook in Apex Tests

**What the LLM generates:** Apex test methods that query the Standard Pricebook via SOQL, which returns zero rows in test context.

**Why it happens:** LLMs generate test code by adapting production code patterns. They use the same SOQL query that works in production without knowing that Apex test context isolates data and hides the Standard Pricebook from queries.

**Correct pattern:**

```apex
@isTest
static void testProductCreation() {
    // Always use Test.getStandardPricebookId() in test methods — never SOQL
    Id pbId = Test.getStandardPricebookId();

    Product2 p = new Product2(Name = 'Test Product', IsActive = true);
    insert p;

    PricebookEntry pbe = new PricebookEntry(
        Pricebook2Id = pbId,
        Product2Id   = p.Id,
        UnitPrice    = 100.00,
        IsActive     = true
    );
    insert pbe;
}
```

**Detection hint:** In generated Apex test methods, look for `SELECT Id FROM Pricebook2 WHERE IsStandard = true`. If present without `@isTest(SeeAllData=true)` on the class, it will return null at runtime. The correct substitute is `Test.getStandardPricebookId()`.

---

## Anti-Pattern 5: Treating the Three-Object Model as a Two-Object Model

**What the LLM generates:** Explanations or code that describe Salesforce pricing as "Product2 has a price" or that try to insert PricebookEntry without a Pricebook2Id.

**Why it happens:** LLMs familiar with simpler product-pricing models collapse the three-object chain into a simpler structure. They may know PricebookEntry links Product2 to a price but omit the mandatory Pricebook2 reference.

**Correct pattern:**

```
Product2 (product master — no price)
    ↓ Product2Id
PricebookEntry (price in a specific list) — requires BOTH Product2Id AND Pricebook2Id
    ↑ Pricebook2Id
Pricebook2 (price list — Standard or custom)
```

PricebookEntry.Pricebook2Id is a required field. A PricebookEntry with no Pricebook2Id will fail with a required field missing error.

**Detection hint:** Flag any PricebookEntry insert that omits `Pricebook2Id`. Also flag any explanation that says "Product2 stores the price" or "you can insert a PricebookEntry without specifying a pricebook."

---

## Anti-Pattern 6: Recommending Insert Instead of Upsert for Bulk PricebookEntry Loads

**What the LLM generates:** A Data Loader or Bulk API load plan that uses insert for PricebookEntry records with no idempotency strategy.

**Why it happens:** LLMs default to insert as the simplest operation. They do not account for the scenario where a partial load failure requires the job to be re-run, and re-running an insert job creates duplicate PricebookEntries (blocked by the uniqueness constraint, causing a different error).

**Correct pattern:**

```
For initial loads:
  Step 1: Upsert Product2 using ProductCode or a custom external ID
  Step 2: Query existing Standard PBE IDs for the target products; route existing to update, new to insert
  Step 3: Query existing custom PBE IDs; route existing to update, new to insert

OR for pipelines with guaranteed clean state:
  Step 1: Upsert Product2
  Step 2: Insert Standard PBEs (safe only if confirmed no prior Standard PBEs exist)
  Step 3: Insert custom PBEs (safe only if confirmed no prior custom PBEs exist)
```

**Detection hint:** A load plan that lists "insert" as the operation for PricebookEntry without any upsert or idempotency strategy should be flagged. Ask: what happens if this job is re-run after a partial failure?
