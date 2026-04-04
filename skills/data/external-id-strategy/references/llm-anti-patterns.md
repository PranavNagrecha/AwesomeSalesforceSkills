# LLM Anti-Patterns — External ID Strategy

Common mistakes AI coding assistants make when generating or advising on External ID Strategy.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Recommending Name Field as the Upsert Key

**What the LLM generates:** Advice to use the `Name` field as the match key for upsert operations, often framed as "use the Account Name as a natural key."

**Why it happens:** Name is the most prominent text field on every standard object and appears prominently in training data examples. LLMs conflate "uniquely identifies a record in human context" with "valid upsert key." The platform distinction between External ID fields (indexed, upsert-eligible) and regular fields (not upsert-eligible by API) is not always represented in training examples.

**Correct pattern:**
```
The Name field is not an External ID and cannot be used as the upsert key in
REST API PATCH or Bulk API 2.0 upsert jobs. Create a dedicated custom field,
mark it as External ID and Unique, and use that field as the externalIdFieldName
in the Bulk API job or the URL path in the REST API PATCH request.
```

**Detection hint:** Flag any suggestion to upsert "by Name" or "using the Name field." Name is never a valid external ID field unless a custom field explicitly named `Name` is created as type Text with External ID marked.

---

## Anti-Pattern 2: Assuming Text External IDs Are Case-Sensitive by Default

**What the LLM generates:** Code or instructions that treat a Text external ID field as case-sensitive without noting that the platform default is case-insensitive, leading to integrations that assume `ABC-001` and `abc-001` are distinct external IDs when Salesforce will treat them as duplicates.

**Why it happens:** Most programming languages and databases treat string equality as case-sensitive by default. LLMs apply this default assumption to Salesforce Text fields. The Salesforce-specific behavior — case-insensitive uniqueness by default on Text fields unless the case-sensitive option is explicitly checked — is a platform nuance that conflicts with general programming intuition.

**Correct pattern:**
```
Text external ID fields enforce case-INSENSITIVE uniqueness by default.
"ORDER-001" and "order-001" are treated as the same value.
To enforce case-sensitive uniqueness, check the "Treat 'ABC' and 'abc' as different
values (case-sensitive)" option at field creation time.
Regardless of the setting, normalize all external ID values to a consistent
case (e.g., all uppercase) in the ETL layer before loading.
```

**Detection hint:** Look for integration designs that rely on mixed-case external ID values being distinct without explicitly noting the case-sensitive field option has been enabled.

---

## Anti-Pattern 3: Using Salesforce Record IDs as the Cross-System Identifier

**What the LLM generates:** Integration designs that query Salesforce for record IDs after initial load, store those IDs in the source system, and then use them as the match key for subsequent loads (e.g., by including the `Id` column in upsert CSV files).

**Why it happens:** Storing the returned ID from a create operation is a standard database integration pattern. LLMs trained on generic API patterns apply this convention to Salesforce without accounting for the org-specificity of Salesforce record IDs or the idempotency requirements of data migration and continuous integration pipelines.

**Correct pattern:**
```
Never store Salesforce record IDs as the primary cross-system identifier.
Salesforce IDs are org-specific and invalidate on sandbox refresh, record
deletion, or org migration. Design the external ID field strategy before
the first load so the source system's natural key is the only cross-system
reference. The Salesforce ID is an internal artifact — treat it as opaque
and transient in the context of integration design.
```

**Detection hint:** Integration specs or code that include steps like "store the returned Salesforce ID in the source system database" or "query Salesforce IDs to embed in the child load file."

---

## Anti-Pattern 4: Omitting the Unique Constraint When Marking a Field as External ID

**What the LLM generates:** Field configuration or metadata XML that sets `<externalId>true</externalId>` without setting `<unique>true</unique>`, or UI instructions that direct the user to check "External ID" without also checking "Unique."

**Why it happens:** LLMs often treat External ID as a single concept and reproduce the minimum configuration seen in training examples. The fact that Unique is a separate, independently configurable attribute is easily dropped in generated instructions. Some training examples show external IDs used for cross-system correlation (not upsert) where Unique is intentionally omitted — LLMs generalize this pattern incorrectly.

**Correct pattern:**
```xml
<!-- Always set both flags for a field used as a upsert key -->
<externalId>true</externalId>
<unique>true</unique>
```

```
When an external ID field will be used as an upsert key, both External ID
and Unique must be set. External ID alone creates an index but does not
prevent duplicate values. Without Unique, duplicates can be introduced
through the UI or non-upsert DML, causing all future upsert operations
on those values to error.
```

**Detection hint:** Any CustomField metadata XML with `<externalId>true</externalId>` but no `<unique>true</unique>` element, or UI setup instructions that mention External ID without Unique.

---

## Anti-Pattern 5: Using the Wrong Relationship Column Syntax for Parent Resolution in Bulk API

**What the LLM generates:** Incorrect column header formats for parent relationship resolution in Bulk API 2.0 CSV files, such as using the Salesforce `Id` field name (`AccountId`) when attempting to resolve by external ID, or inverting the syntax to `ExternalIdField__c.RelationshipName__r`.

**Why it happens:** The `RelationshipName__r.ExternalIdField__c` syntax is specific to Salesforce Bulk API and is not a general REST or database pattern. LLMs frequently confuse it with the SOQL relationship traversal syntax (which uses `Account.Name` for standard relationships on standard objects) or produce inverted versions of the column header based on partial recall.

**Correct pattern:**
```
Standard object lookup (e.g., Account lookup on Contact):
  Column header: Account.Legacy_CRM_Id__c
  (relationship name without __r for standard relationships)

Custom object lookup (e.g., custom Account__c lookup):
  Column header: Account__r.Legacy_CRM_Id__c
  (relationship name with __r for custom relationship fields)

The format is always: <RelationshipName>.<ExternalIdField__c>
NOT: <ExternalIdField__c>.<RelationshipName>
NOT: <LookupFieldApiName> with a Salesforce ID value
```

**Detection hint:** Column headers in Bulk API CSV files that contain `Id` (e.g., `AccountId`) when the intent is to resolve a parent by external ID. Also flag column headers with the external ID field name first (`Legacy_CRM_Id__c.Account`).

---

## Anti-Pattern 6: Claiming the External ID Field Limit Is 3

**What the LLM generates:** Guidance that states each Salesforce object is limited to 3 external ID fields, often citing this as a hard constraint that forces composite key design.

**Why it happens:** Older Salesforce documentation (pre-Summer '16 era) stated a limit of 3 indexed custom fields per object, and some community resources conflated this with external ID fields specifically. The current platform limit is 25 external ID fields per object, all indexed automatically. LLMs trained on a mix of historical and current documentation reproduce the outdated 3-field limit.

**Correct pattern:**
```
The current Salesforce platform limit is 25 external ID fields per object,
all automatically indexed. The historical 3-field limit applied to custom
indexed fields in older API versions and is no longer accurate.
Confirm the current limit in the official Salesforce Help article on
Custom External ID Fields before advising on field budget constraints.
```

**Detection hint:** Any guidance stating "you can only have 3 external ID fields per object" or "external ID fields are limited to 3 (indexed)."
