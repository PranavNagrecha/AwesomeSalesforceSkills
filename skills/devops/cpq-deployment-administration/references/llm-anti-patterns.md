# LLM Anti-Patterns — CPQ Deployment Administration

Common mistakes AI coding assistants make when generating or advising on CPQ deployment administration.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Recommending Change Sets or sf project deploy for CPQ Configuration

**What the LLM generates:** Instructions to add `SBQQ__PriceRule__c` or `SBQQ__ProductRule__c` to a Change Set or an `sf project deploy start` command to move CPQ configuration between environments.

**Why it happens:** LLMs conflate metadata and data. Change Sets and Metadata API are the canonical Salesforce deployment mechanism, and training data heavily features their use. The distinction between sObject records (data) and metadata components is not surfaced prominently in general Salesforce documentation, so models default to the most frequently seen deployment advice.

**Correct pattern:**

```
CPQ configuration objects (SBQQ__PriceRule__c, SBQQ__ProductRule__c, SBQQ__PriceAction__c, etc.)
are sObject data records and cannot be deployed via Change Sets or Metadata API.

Correct approach: Use a data migration tool — Prodly AppOps, SFDMU, Copado Data Deploy, or Salto.
Export records from source in parent-before-child order. Upsert to target using external ID fields.
```

**Detection hint:** Response contains `sf project deploy` or "Change Set" together with any SBQQ object name. Flag immediately.

---

## Anti-Pattern 2: Inserting Child CPQ Records Before Parent Records

**What the LLM generates:** A data loader plan or SOQL export sequence that exports Price Actions before Price Rules, or Option Constraints before Products and Options.

**Why it happens:** LLMs generate export queries based on the objects mentioned in the prompt, without modeling the foreign-key dependency graph. Without explicit prompt context about parent-child ordering, the model produces an alphabetical or prompt-order sequence.

**Correct pattern:**

```
Mandatory parent-before-child ordering for CPQ data migration:

1. Product2, Pricebook2, PricebookEntry (product catalog)
2. SBQQ__ProductRule__c
3. SBQQ__PriceRule__c
4. SBQQ__PriceCondition__c, SBQQ__PriceAction__c  (children of Price Rules)
5. SBQQ__OptionConstraint__c                        (depends on Products)
6. SBQQ__QuoteTemplate__c
7. SBQQ__TemplateSection__c, SBQQ__TemplateContent__c

Never export/insert children before their parent lookup records exist in the target.
```

**Detection hint:** Any migration plan that lists `SBQQ__PriceAction__c` before `SBQQ__PriceRule__c`, or `SBQQ__TemplateSection__c` before `SBQQ__QuoteTemplate__c`.

---

## Anti-Pattern 3: Using Salesforce Record IDs as Migration Keys

**What the LLM generates:** An export/import plan that uses standard Salesforce 18-character Record IDs (e.g. `a0B5g000003ABCDEF`) as the matching key to upsert CPQ records into the target org.

**Why it happens:** Record IDs are the most visible identifier in Salesforce and appear in all SOQL results. LLMs default to them without understanding that IDs are org-specific and have no meaning in a different environment.

**Correct pattern:**

```
Never use Salesforce Record IDs as migration keys across orgs.
Record IDs are org-scoped — a Record ID from Sandbox A does not exist in Production.

Correct approach: Add a custom text field (External ID = true, Unique = true) to each SBQQ object.
Populate it with a deterministic, human-meaningful value before export.
Use that field as the upsert external ID in the target org.

Example external ID value: 'PRICERULE_Volume_Discount_Tier_1'
```

**Detection hint:** Migration plan references `Id` field as the upsert key, or uses `WHERE Id IN (...)` with hardcoded 15/18-character IDs from one org in queries intended for another org.

---

## Anti-Pattern 4: Claiming Custom Field Renames Are Safe for CPQ Orgs

**What the LLM generates:** Reassurance that renaming a custom field using Setup is a safe, backward-compatible operation in Salesforce and that CPQ rules will continue working.

**Why it happens:** For standard Salesforce automation (Flow, Process Builder, Validation Rules, Apex classes), Salesforce does automatically update API name references in metadata. LLMs learn this general rule and incorrectly apply it to CPQ, which uses a different mechanism — string-stored field names — that is not updated automatically.

**Correct pattern:**

```
Renaming a custom field is NOT safe in CPQ orgs without a manual data patch.

CPQ stores field API names as plain text strings in:
- SBQQ__PriceCondition__c.SBQQ__TestedField__c
- SBQQ__PriceAction__c.SBQQ__TargetField__c
- SBQQ__ProductAction__c.SBQQ__TargetField__c
- SBQQ__ErrorCondition__c.SBQQ__TestedField__c

These strings are NOT updated when you rename a field. Before renaming, query all SBQQ
rule objects for the old API name. After rename, update all matching records to the new name
in every org (dev, sandbox, production) independently.
```

**Detection hint:** Response contains "field rename is backward compatible" or "Salesforce updates references automatically" in a context that involves CPQ or SBQQ objects.

---

## Anti-Pattern 5: Treating CPQ Quote Template Migration as Pure sObject Export

**What the LLM generates:** A SFDMU or Data Loader plan that exports `SBQQ__QuoteTemplate__c` and `SBQQ__TemplateSection__c` records and considers the template fully migrated.

**Why it happens:** The standard data migration mental model covers sObject records. LLMs are not trained to consider that template visual content may be stored as file attachments (ContentDocument/ContentVersion) linked to the template records — this is a Salesforce-specific pattern not commonly discussed.

**Correct pattern:**

```
CPQ Quote Templates with embedded images or HTML content store file bodies as ContentDocument
records linked to the template via ContentDocumentLink.

A complete Quote Template migration requires:
1. Export SBQQ__QuoteTemplate__c, SBQQ__TemplateSection__c, SBQQ__TemplateContent__c records
2. Query ContentDocumentLink WHERE LinkedEntityId IN (SELECT Id FROM SBQQ__QuoteTemplate__c)
3. Export associated ContentVersion (file bodies)
4. Import ContentVersion into target org and re-create ContentDocumentLink to the new template record IDs

Using Prodly or a custom file-aware export script is recommended over generic SFDMU for orgs
with rich template content.
```

**Detection hint:** Migration plan includes `SBQQ__QuoteTemplate__c` but does not mention `ContentDocument`, `ContentVersion`, or `ContentDocumentLink`.

---

## Anti-Pattern 6: Omitting CPQ Custom Settings From the Migration Scope

**What the LLM generates:** A migration plan that covers all SBQQ rule and template objects but does not include `SBQQ__CustomClass__c` or other CPQ Hierarchy Custom Settings records.

**Why it happens:** Custom Settings are a less prominent Salesforce concept and are often mentioned only in advanced CPQ documentation. LLMs generating migration object lists from context about "Price Rules and Product Rules" naturally omit settings objects that are not rule-like in name or function.

**Correct pattern:**

```
Always include CPQ Custom Settings in the migration scope:

Objects to include:
- SBQQ__CustomClass__c  (CPQ Custom Settings — controls plugin class assignments)
- Any org-specific CPQ Custom Setting records at Org, Profile, and User level

Validate after migration:
  Setup > Custom Settings > SBQQ Custom Class > Manage
  Confirm all fields (QuoteCalculatorPlugin, ContractingClass, etc.) match source org values.
```

**Detection hint:** Migration scope list contains 5+ SBQQ objects but does not include `SBQQ__CustomClass__c` or any Custom Settings object.
