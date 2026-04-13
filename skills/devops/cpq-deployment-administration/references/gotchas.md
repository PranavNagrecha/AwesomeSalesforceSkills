# Gotchas — CPQ Deployment Administration

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Renaming a Custom Field Silently Breaks CPQ Rules With No Error

**What happens:** CPQ Price Rules, Price Actions, Price Conditions, and Product Rules store Salesforce field API names as raw text strings rather than true lookup relationships to field metadata. When a custom field is renamed through Setup (which changes its API name), the existing CPQ configuration records retain the old API name string. CPQ's runtime evaluation uses dynamic Apex (`Schema.SObjectType.getDescribe()` style lookups) to resolve the field by name at quote calculation time. If the field no longer exists under that name, CPQ silently skips the rule or action. No error is surfaced on the Quote, in debug logs at a glance, or during deployment — the rule simply stops applying.

**When it occurs:** Any time a custom field referenced by a Price Condition (`SBQQ__TestedField__c`), Price Action (`SBQQ__TargetField__c`), Error Condition, or Product Action is renamed in any org, including in a sandbox. The breakage travels with the CPQ data records when they are later migrated.

**How to avoid:** Before any field rename, run SOQL queries across all SBQQ rule-related objects to find records containing that field's API name as a text value. Perform the rename and the CPQ record update atomically in all environments. Add a post-migration validation step that cross-references all string-stored API names against the target org's active field list.

---

## Gotcha 2: Quote Template File Attachments Are Not Captured by Standard Data Export

**What happens:** Salesforce CPQ Quote Templates (`SBQQ__QuoteTemplate__c`) that contain rich content — HTML blocks, images, or custom section styling — store the visual content as `ContentDocument` records linked to the template via `ContentDocumentLink`. SOQL-based export tools that enumerate SBQQ sObjects will export the template header and `SBQQ__TemplateContent__c` structure records, but will not export the associated files. The target org receives a structurally correct template with blank or broken visual sections.

**When it occurs:** Any time a Quote Template uses embedded images or HTML content uploaded through the Template Builder UI in Setup > CPQ > Quote Templates. Templates that use only standard CPQ line columns and system-generated content are unaffected.

**How to avoid:** Use Prodly AppOps or a custom migration script that queries `ContentDocumentLink WHERE LinkedEntityId IN (SELECT Id FROM SBQQ__QuoteTemplate__c)` to enumerate and export related files, then re-link them in the target org. Alternatively, re-upload template file content manually in the target org immediately after data migration, treating it as a post-migration step in the deployment runbook.

---

## Gotcha 3: CPQ Custom Settings Must Be Migrated Separately and In Order

**What happens:** Salesforce CPQ behavior is heavily controlled by Hierarchy Custom Settings (`SBQQ__CustomClass__c` / CPQ Package Custom Settings). Settings such as which Apex class handles pricing calculations, which class handles approval routing, and which class governs product search are stored as custom setting records, not as ordinary configuration data. Many data migration plans focus on rule and template objects and overlook custom settings entirely. When custom settings differ between environments, CPQ behaves differently — for example, a custom pricing plugin present in the source org is absent in the target, causing fallback to default pricing without warning.

**When it occurs:** Any time an org has configured CPQ Custom Settings fields such as `SBQQ__CustomClass__c.SBQQ__ContractingClass__c`, `SBQQ__CustomClass__c.SBQQ__QuoteCalculatorPlugin__c`, or similar. Settings configured at the org level will not migrate with SBQQ rule data because they live in a different object and are often overlooked in the object scope list.

**How to avoid:** Always include `SBQQ__CustomClass__c` and any other CPQ Custom Settings objects in the migration scope. Because custom settings can have org-default, profile-level, and user-level records, export all three levels if configured. Validate after migration by comparing field values in the source and target Custom Settings Setup pages side by side.

---

## Gotcha 4: CPQ Package Version Mismatch Causes Silent Field Omission

**What happens:** If the CPQ managed package version differs between source and target orgs, the SBQQ objects may have different sets of fields. When a data export from a newer-version org is imported into an older-version org, fields that exist only in the newer version are either dropped silently by the import tool or cause an error on the specific records that contain values in those fields. Conversely, importing from an older to a newer version may leave new fields at their defaults when the configuration intent was to populate them.

**When it occurs:** During sandbox refresh cycles where the production org has been upgraded to a new CPQ version but the sandbox was not, or vice versa. Also occurs when a new sandbox is provisioned from a template at an older package version.

**How to avoid:** Always verify the CPQ package version in both source and target orgs before executing a migration. In Setup > Installed Packages, confirm the package version number is identical. If versions differ, upgrade the lower-version org first, validate CPQ functionality, then proceed with data migration.

---

## Gotcha 5: Option Constraints With Coordinated Products Fail If Products Are Missing in Target

**What happens:** `SBQQ__OptionConstraint__c` records encode relationships between product bundles by storing the Salesforce Record ID of the controlling and constrained `Product2` records in lookup fields. Unlike the string-based API name issue in Price Rules, these are true lookup relationships. If the referenced Product2 records do not exist in the target org (or have different Record IDs), the migration will fail on the option constraint records or insert them with blank lookup fields, silently disabling the constraints.

**When it occurs:** When product catalog records (`Product2`, `PricebookEntry`) have not been synchronized between orgs before the CPQ configuration migration is run. This is especially common when sandboxes are refreshed from production but the product catalog has since diverged, or when developers create test products in sandboxes without ensuring parity.

**How to avoid:** Always migrate or verify the product catalog (`Product2`, `Pricebook2`, `PricebookEntry`) before migrating any CPQ object that references products. Use external IDs on Product2 records as well, or match by `ProductCode` if it is unique. Run the option constraint migration last in the ordering sequence, after all referenced products are confirmed in the target org.
