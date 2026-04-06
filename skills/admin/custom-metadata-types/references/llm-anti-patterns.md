# LLM Anti-Patterns — Custom Metadata Types

Common mistakes AI coding assistants make when generating or advising on Salesforce Custom Metadata Types.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Recommending Custom Settings when Custom Metadata Types are the right fit

**What the LLM generates:** "Store your configuration values in a Hierarchy Custom Setting so admins can update them easily."

**Why it happens:** LLMs trained on older Salesforce content default to Custom Settings because they appeared first. Custom Metadata Types (CMTs) are deployable through change sets, packages, and CI/CD. Custom Settings (Hierarchy or List) are data, not metadata -- they do not travel through metadata deployments without manual data loading in the target org.

**Correct pattern:**

```
Decision guide:
- Values must move through source control, change sets, or packages → Custom Metadata Type.
- Values are environment-specific and change per org → Custom Settings may fit, but
  consider CMT with environment-specific records deployed per-environment.
- Values need per-user or per-profile overrides → Hierarchy Custom Setting.
- Values are secrets (tokens, passwords) → Named Credentials or External Credentials.
- Values need reporting or SOQL query with complex filters → Custom Object.

CMT advantage: records deploy as metadata. Custom Settings require separate data loads.
```

**Detection hint:** If the output recommends Custom Settings for configuration that must be version-controlled or deployed across environments, the storage choice is wrong. Search for `Custom Setting` without a justification for why CMT was rejected.

---

## Anti-Pattern 2: Suggesting DML operations on Custom Metadata Type records in Apex

**What the LLM generates:** "Insert a new Custom Metadata record in Apex: `insert new My_Config__mdt(Label = 'Test', DeveloperName = 'Test');`"

**Why it happens:** LLMs pattern-match from Custom Object DML. Custom Metadata Type records cannot be created, updated, or deleted using standard DML (insert/update/delete) in Apex. They require the Metadata API or the `Metadata.DeployContainer` approach for programmatic upserts.

**Correct pattern:**

```apex
// Custom Metadata records CANNOT be manipulated with standard DML.
// Use the Metadata namespace for programmatic updates:
Metadata.CustomMetadata customMetadata = new Metadata.CustomMetadata();
customMetadata.fullName = 'My_Config__mdt.My_Record';
customMetadata.label = 'My Record';

Metadata.CustomMetadataValue field = new Metadata.CustomMetadataValue();
field.field = 'Value__c';
field.value = 'New Value';
customMetadata.values.add(field);

Metadata.DeployContainer container = new Metadata.DeployContainer();
container.addMetadata(customMetadata);
Metadata.Operations.enqueueDeployment(container, callback);
// Note: this is asynchronous and requires a DeployCallback implementation.
```

**Detection hint:** If the output uses `insert`, `update`, or `delete` DML on an `__mdt` sObject, it will fail at runtime. Regex: `(insert|update|delete)\s+.*__mdt`.

---

## Anti-Pattern 3: Using Custom Metadata Types for high-volume transactional data

**What the LLM generates:** "Store each transaction log entry as a Custom Metadata record so it is deployable."

**Why it happens:** LLMs see "metadata" and "deployable" as universally positive. CMT records are designed for low-volume configuration (hundreds, not thousands). They count toward metadata API limits, have no native reporting, and are not designed for records that change frequently or grow unboundedly.

**Correct pattern:**

```
Custom Metadata Types are for:
- Low-volume configuration: feature flags, routing rules, mapping tables.
- Typically < 200 records per CMT (practical performance guideline).
- Values that change infrequently (quarterly, per release).

For transactional or high-volume data, use:
- Custom Objects (with proper sharing, indexing, and archival).
- Big Objects for very high volume append-only data.
- Platform Events for event-driven transaction logging.
```

**Detection hint:** If the output recommends CMT for data that grows with transaction volume or changes daily, the storage model is wrong. Search for `log`, `transaction`, `each record`, or `every time` combined with `Custom Metadata`.

---

## Anti-Pattern 4: Forgetting that protected Custom Metadata records cannot be edited by subscribers

**What the LLM generates:** "Mark the Custom Metadata records as protected to prevent accidental edits. Admins in the subscriber org can update them if needed."

**Why it happens:** LLMs confuse "protected" with "read-only." Protected CMT records in a managed package are invisible and uneditable in the subscriber org. Only the package developer can see and modify them via a package upgrade. If subscribers need to customize the values, the records should be unprotected.

**Correct pattern:**

```
Protected vs Unprotected CMT records in packages:
- Protected: only the package developer can view and modify.
  Subscribers cannot see these records in Setup.
  Use for: internal package behavior that should not be overridden.
- Unprotected: subscribers can view and edit.
  Use for: configuration the subscriber needs to customize (e.g., API endpoints,
  feature toggles for their org).

If you ship protected records but subscribers need to customize them,
they will file support tickets. Design visibility intentionally.
```

**Detection hint:** If the output recommends "protected" CMT records while also saying admins can edit them, the protection model is misunderstood. Search for `protected` combined with `admin can edit` or `subscriber can update`.

---

## Anti-Pattern 5: Omitting SOQL-free access patterns for Custom Metadata in formulas and flows

**What the LLM generates:** "Query the Custom Metadata records in your Apex class: `SELECT Value__c FROM My_Config__mdt WHERE DeveloperName = 'Key'`."

**Why it happens:** LLMs default to SOQL for all data access. While SOQL works for CMT and does not count against governor limits, CMT records are also accessible without code: in formula fields via `$CustomMetadata`, in validation rules, and in Flows via the Get Records element. Admins should know the no-code access paths.

**Correct pattern:**

```
Access Custom Metadata without code:
- Formula fields / Validation rules:
  $CustomMetadata.My_Config__mdt.My_Record.Value__c
- Flow (Get Records element):
  Object: My_Config__mdt, filter by DeveloperName.
- Apex (SOQL — does NOT count against query limits):
  [SELECT Value__c FROM My_Config__mdt WHERE DeveloperName = 'Key']
- Apex (getInstance):
  My_Config__mdt.getInstance('My_Record').Value__c

Prefer $CustomMetadata in formulas and validation rules for zero-code access.
```

**Detection hint:** If the output only shows SOQL for reading CMT data without mentioning `$CustomMetadata` or Flow access, the no-code paths are being omitted. Search for `$CustomMetadata` in the output.
