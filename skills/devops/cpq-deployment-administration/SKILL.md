---
name: cpq-deployment-administration
description: "Use when deploying Salesforce CPQ (Steelbrick/SBQQ) configuration between orgs — Product Rules, Price Rules, Price Actions, Price Conditions, Option Constraints, Quote Templates, and Custom Settings. Covers data-migration-based deployment strategies, parent-child ordering, external-ID mapping, and tooling selection (Prodly, Copado, Salto, custom data loader). NOT for deploying standard Salesforce metadata via Change Sets or Metadata API, not for OmniStudio/Industries CPQ DataPacks, not for CPQ managed-package upgrades or CPQ Apex class customizations."
category: devops
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
  - Security
triggers:
  - "how do I deploy CPQ product rules and price rules to production without losing configuration"
  - "CPQ configuration is not moving between sandboxes with Change Sets or metadata deploy"
  - "price rule stopped working after sandbox refresh and we need to redeploy CPQ data records"
  - "what order should I deploy CPQ objects like Price Actions and Option Constraints"
  - "CPQ custom field rename broke a product rule silently in production"
  - "what tools can migrate Salesforce CPQ configuration records between environments"
tags:
  - cpq
  - salesforce-cpq
  - sbqq
  - deployment
  - devops
  - price-rules
  - product-rules
  - quote-templates
  - data-migration
inputs:
  - "Source org API access (username, connected app, or session token)"
  - "Target org API access"
  - "List of CPQ objects to deploy (e.g. SBQQ__ProductRule__c, SBQQ__PriceRule__c)"
  - "External ID fields configured on SBQQ objects in both orgs (required for upsert-based migration)"
  - "Tooling choice: Prodly, Copado, Salto, or custom data loader approach"
outputs:
  - "Ordered deployment plan listing which CPQ objects to migrate in which sequence"
  - "External-ID field setup checklist for source and target orgs"
  - "Data loader job configurations or tool-specific mapping files"
  - "Post-migration validation checklist confirming rules fire correctly"
dependencies:
  - devops/salesforce-devops-tooling-selection
  - devops/copado-essentials
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-13
---

# CPQ Deployment Administration

This skill activates when you need to move Salesforce CPQ configuration records — Product Rules, Price Rules, Price Actions, Price Conditions, Option Constraints, Quote Templates, and related Custom Settings — between Salesforce orgs. CPQ configuration is stored as data records, not metadata, and therefore cannot be deployed with Change Sets, Metadata API, or the Salesforce CLI deploy command. A specialized data-migration approach with strict parent-before-child ordering is required.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Confirm the CPQ managed package version** is identical in both source and target orgs. A version mismatch means object shapes differ and a migration will silently drop fields or fail mid-run.
- **Identify external ID fields** on each SBQQ object. External IDs (e.g. a custom `CPQ_External_Id__c` text field marked as External ID) are mandatory for upsert-based migration; without them you cannot deduplicate records on re-deployment.
- **Understand that CPQ stores API names as plain-text strings** inside configuration records (e.g. the `SBQQ__SourceField__c` value on a Price Condition is a raw string like `SBQQ__Quantity__c`). Renaming any custom field that is referenced by CPQ rules will silently break those rules with no deployment-time error.
- **Determine the full dependency graph** of your CPQ configuration before starting. Price Actions depend on Price Rules; Option Constraints depend on Products and Options; Quote Template Sections depend on Quote Templates. Any attempt to load children before parents causes foreign-key lookup failures that may be silent (blank lookup) or hard failures (required field missing).

---

## Core Concepts

### CPQ Configuration Is Data, Not Metadata

SBQQ objects such as `SBQQ__ProductRule__c`, `SBQQ__PriceRule__c`, `SBQQ__PriceAction__c`, `SBQQ__PriceCondition__c`, `SBQQ__OptionConstraint__c`, and `SBQQ__QuoteTemplate__c` are ordinary sObject records stored in each org's database. They do not have corresponding metadata components and are completely invisible to the Metadata API, Change Sets, and `sf project deploy`. This is the foundational reason why CPQ deployments require a dedicated data-migration strategy rather than a standard DevOps pipeline.

### Parent-Before-Child Ordering Is Mandatory

CPQ objects have strict hierarchical dependencies. Attempting to insert a Price Action before its parent Price Rule is present in the target org will produce a lookup failure. The canonical safe ordering is:

1. Products (`Product2`) and Pricebooks (`Pricebook2`, `PricebookEntry`) — if not already in target
2. `SBQQ__ProductRule__c` (parent of Error Conditions, Product Actions, Summary Variables)
3. `SBQQ__PriceRule__c` (parent of Price Conditions and Price Actions)
4. `SBQQ__PriceCondition__c` and `SBQQ__PriceAction__c` (children of Price Rules)
5. `SBQQ__OptionConstraint__c` (depends on Products and Options)
6. `SBQQ__QuoteTemplate__c` (Quote Template header)
7. `SBQQ__TemplateSection__c` and `SBQQ__TemplateContent__c` (children of Quote Templates)
8. `SBQQ__CustomAction__c` and related custom action targets

### API-Name Strings Are Deployment-Time Invisible References

Many CPQ configuration fields store Salesforce API names as raw text strings rather than actual lookup relationships. For example, `SBQQ__PriceCondition__c.SBQQ__TestedField__c` stores a string value such as `"SBQQ__Quantity__c"`. The CPQ engine evaluates these strings at runtime using dynamic Apex. This has two critical consequences: (1) if a referenced custom field is renamed or deleted, no validation error is raised during deployment — the rule silently stops working at runtime; (2) external ID mapping tools that check relationship integrity will not catch these broken references because they appear as plain text, not as lookup foreign keys.

### Quote Template Content Attachment Handling

Quote Template visual content (line column definitions, term content blocks) is stored in both `SBQQ__TemplateContent__c` records and as `ContentDocument`/`ContentVersion` attachments (for HTML/PDF template sections). Plain data-migration tools that only migrate SBQQ sObject records will miss associated file attachments, producing templates that render with missing sections in the target org.

---

## Common Patterns

### Pattern 1: External-ID Upsert Migration with Data Loader or SFDMU

**When to use:** Teams without a budget for Prodly or Copado who want a repeatable, scripted CPQ configuration migration. Works well for orgs with a stable CPQ configuration that changes infrequently.

**How it works:**
1. Add a custom text field named `CPQ_External_Id__c` (marked as External ID and Unique) to every SBQQ object you intend to migrate.
2. Populate `CPQ_External_Id__c` on all source org records using a deterministic ID — e.g. a concatenation of the object name and the record's `Name` field or a hash of key fields.
3. Export records from source in parent-before-child order using Data Loader, SFDMU (`sf-data-export-plugin`), or the Tooling API.
4. Upsert records into target using the external ID field. SFDMU natively supports relationship mapping and parent-before-child ordering via its `exportTree.json` plan file.
5. After migration, run CPQ quote calculation against a test product to confirm rules fire.

**Why not simply export/import by Salesforce Record ID:** Standard Salesforce IDs are org-specific. If you export a Price Action with `SBQQ__PriceRule__c = a0B...XYZ` and import to the target, that ID does not exist in the target, producing a lookup failure or null parent.

### Pattern 2: Prodly AppOps (Recommended for Enterprise)

**When to use:** Orgs that deploy CPQ configuration frequently, have multiple environments (Developer, QA, Staging, Production), and need audit trails and rollback capability.

**How it works:** Prodly AppOps maintains a pre-built dependency graph for all Salesforce CPQ (SBQQ) objects and handles parent-child ordering automatically. Deployment plans are created in the Prodly UI or API, specifying which object sets to include. Prodly resolves foreign-key relationships using its own mapping store rather than requiring custom external ID fields. Prodly also handles CPQ Custom Settings (`SBQQ__CustomClass__c`) and Quote Template file attachments.

**Why not a generic data loader:** Generic tools require you to manually maintain the dependency graph and re-discover it when Salesforce CPQ releases add new objects or relationships. Prodly updates its graph with each managed-package version.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| One-time or infrequent CPQ migration, limited budget | SFDMU with external IDs and manual ordering plan | Low cost, repeatable, requires upfront external-ID field setup |
| Frequent CPQ deployments across multiple environments | Prodly AppOps | Handles dependency graph automatically, audit trail, rollback |
| Org already using Copado for metadata DevOps | Copado Data Deploy module | Keeps all deployment tooling in one platform |
| IaC / version-controlled CPQ configuration | Salto | Represents CPQ data records as declarative HCL-like config; supports diff and PR-based review |
| Sandbox refresh requires CPQ config restore | Full export from golden sandbox + SFDMU import to refreshed sandbox | Fastest path when a complete refresh is acceptable |
| Quote Template with rich HTML content | Prodly or manual ContentVersion export | Generic data loaders miss associated file attachments |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Audit the source org CPQ configuration scope.** Run SOQL queries against all SBQQ objects to enumerate the records being migrated. Use `SELECT Id, Name, SBQQ__Active__c FROM SBQQ__PriceRule__c` style queries on each object. Record approximate counts to size the migration effort and detect any records that reference custom fields likely to cause broken-string references.

2. **Set up external ID fields on all SBQQ objects in both orgs** (if using SFDMU or Data Loader). Deploy a single metadata component (custom field definition) to both source and target orgs. Populate the external ID values in source before exporting. This step is not required if using Prodly.

3. **Build the ordered export plan.** Define the parent-before-child sequence (see Core Concepts). For SFDMU, this is the `exportTree.json` plan file. For Data Loader, this is a sequenced set of CSV export and upsert operations. For Prodly, this is a deployment plan within the AppOps UI.

4. **Perform a dry-run import against a scratch org or Developer sandbox.** Never migrate directly to production as the first attempt. A dry run surfaces missing parent records, broken external ID references, and field-level security issues on SBQQ fields in the target profile.

5. **Validate CPQ functionality post-migration.** Create a test Quote in the target org using the products covered by the migrated rules. Confirm Price Rules fire (discounts, totals, fields update as expected). Confirm Product Rules enforce correctly (validation errors appear, options are filtered). Inspect at least one Quote Template by generating a quote document.

6. **Check for broken API-name string references.** After migration, run a SOQL query on `SBQQ__PriceCondition__c.SBQQ__TestedField__c` and `SBQQ__PriceAction__c.SBQQ__TargetField__c` in the target org. Cross-reference the field API names against the target org's field list to confirm none are dangling strings.

7. **Document the migration plan and external ID scheme.** Store the export plan, external ID field names, and the ordered object sequence in the project's DevOps repository so that future migrations are repeatable and peer-reviewable.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] CPQ managed package version is identical in source and target orgs
- [ ] External ID fields exist on all SBQQ objects being migrated (or Prodly plan is configured)
- [ ] All SBQQ objects are imported in parent-before-child order; no foreign-key failures in import logs
- [ ] A test Quote validates that Price Rules and Product Rules fire correctly in the target org
- [ ] At least one Quote Template generates a PDF/document without missing sections
- [ ] API-name string references in Price Conditions and Price Actions are verified against target org field list
- [ ] CPQ Custom Settings (`SBQQ__CustomClass__c`) values migrated and confirmed in target org Setup

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Custom field rename silently breaks CPQ rules** — CPQ stores field API names as raw text strings in `SBQQ__TestedField__c`, `SBQQ__TargetField__c`, and similar fields. If a custom field is renamed in the source org after CPQ configuration records were created, the old API name remains in the records. After migration the target org will have the new field name, but the CPQ records will contain the old string, causing rules to silently do nothing at runtime with no error.

2. **Change Sets and Metadata API cannot migrate SBQQ records** — CPQ configuration objects are sObjects (data), not metadata components. A common mistake is attempting to add `SBQQ__ProductRule__c` to a Change Set; the UI will appear to add it as a custom object definition but will not capture any records. The target org will have the object schema but zero configuration data.

3. **Quote Template file attachments are not migrated by data loaders** — Template sections that contain rich HTML or PDF content reference `ContentDocument` records via `ContentDocumentLink`. Standard SOQL-based data export tools that only query SBQQ objects will export the `SBQQ__TemplateContent__c` records but leave the associated file bodies behind, causing templates to render with blank or broken sections.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| CPQ deployment ordered object sequence | Prioritized list of SBQQ objects with parent-before-child order for your specific CPQ configuration scope |
| SFDMU exportTree.json plan | JSON plan file specifying the ordered export and upsert operations with external ID field mappings |
| Post-migration validation checklist | Per-rule-type verification steps confirming CPQ configuration is firing correctly in target org |
| Broken-string reference SOQL queries | Queries to detect dangling API-name strings in Price Conditions and Price Actions after migration |

---

## Related Skills

- `devops/salesforce-devops-tooling-selection` — Use to choose between Prodly, Copado, Salto, and SFDMU before designing the CPQ deployment pipeline
- `devops/copado-essentials` — Use when the org already uses Copado and you want to extend it with Copado Data Deploy for CPQ records
- `devops/pre-deployment-checklist` — Use to run a pre-migration gate covering environment parity, CPQ package versions, and permission set readiness
- `devops/post-deployment-validation` — Use after CPQ migration to validate rules, templates, and pricing calculations in the target org
- `devops/test-data-management-devops` — Use when building sandbox refresh strategies that include CPQ configuration re-seeding
