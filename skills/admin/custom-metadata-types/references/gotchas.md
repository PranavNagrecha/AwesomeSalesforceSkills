# Gotchas - Custom Metadata Types

## Runtime Writes Are The Wrong Mental Model

**What happens:** A team designs a setup where business users change CMT records as part of daily operations and then discovers the write path does not fit normal record-edit transactions.

**When it occurs:** The metadata type is treated like a Custom Object instead of release-managed configuration.

**How to avoid:** Decide early whether the records are deployable config or business data. If the change frequency is operational rather than release-driven, pick a different storage model.

---

## Protected Visibility Only Solves Package Encapsulation

**What happens:** Architects assume protected CMT is a generic "admins cannot ever see this" feature for any org.

**When it occurs:** The design mixes packaging visibility with general-purpose data security requirements.

**How to avoid:** Use protected metadata only for managed-package boundaries. Use Named Credentials or another supported secret strategy when the concern is sensitive values.

---

## `DeveloperName` Becomes A Stable API

**What happens:** A record name is changed for readability, then Apex, Flow, or formulas that reference the old metadata key start failing or returning no match.

**When it occurs:** The implementation treats metadata names as labels instead of contracts.

**How to avoid:** Separate labels from lookup keys. Keep `DeveloperName` stable and rename only when you are also updating every consumer safely.

---

## Public CMT With Environment-Specific URLs Creates Hidden Drift

**What happens:** Sandbox and production endpoint details get copied into record values and diverge over time, even though the org already uses Named Credentials.

**When it occurs:** Teams put full hostnames or tokens into metadata because it feels convenient during development.

**How to avoid:** Put host and auth concerns in Named Credentials. Keep CMT focused on path fragments, functional flags, thresholds, and non-secret configuration.

---

## `getInstance()` And `getAll()` Silently Truncate Every Field At 255 Characters

**What happens:** A long text or long string value read through `My_Config__mdt.getInstance('Key')` comes back cut off at 255 characters with no exception and no warning. The Apex Reference Guide states it for both accessors: "Only the first 255 characters are returned for any field in a custom metadata type record, so longer text fields get truncated."

**When it occurs:** Someone stores a JSON blob, a message template, a field mapping, or a long endpoint path in a CMT field and reads it with the cached accessor because "it does not cost a query".

**How to avoid:** Use SOQL when any field can exceed 255 characters — the guide's own remedy is "If you want all the field data from a custom metadata type record, use a SOQL query." SOQL is cheap here: custom metadata records can have unlimited SOQL queries in a single Apex transaction. Reserve `getAll()`/`getInstance()` for short scalar config.

---

## An Omitted `<values>` Block Is Not The Same As An Empty One

**What happens:** A record is redeployed with one `<values>` block removed, expecting the field to be cleared. On an existing record the field keeps its previous value; on a newly deployed record the same omission produces null. The two behaviours look identical in the source file and differ only by what already exists in the target org.

**When it occurs:** During a "clean up the config" deploy, or when a script generates record files from a spreadsheet and drops columns that are blank.

**How to avoid:** Emit `<value xsi:nil="true"/>` when you mean null. The guide is explicit: "If you leave out the [values element], the value of the field doesn't change. The field's value is null for newly deployed custom metadata records and left at its previous value for updated custom metadata records." UNVERIFIED (2026-09-04): the corollary — that a record deployed with a value present overwrites an admin's in-org edit to that field — follows from the same upsert-by-fullName semantics but is not stated in these words in the Metadata API guide; treat any per-org edit to a source-controlled record as temporary until you have confirmed it in a sandbox.

---

## `visibility`, `PackageProtected`, And Record `protected` Are Three Different Switches

**What happens:** A design says "make it protected" and someone sets the wrong one of three independent controls, producing either records the subscriber cannot configure or secrets the subscriber can read.

**When it occurs:** Packaging work, where the type-level `visibility` enum and the record-level `protected` boolean are conflated.

**How to avoid:** Keep them separate.

| Control | Where | Effect |
|---|---|---|
| `visibility` = `Public` | Type | Default. If packaged, accessible to all subscribing orgs |
| `visibility` = `Protected` | Type | In a managed package, accessible only to the developer org; subscribing orgs can't access it |
| `visibility` = `PackageProtected` | Type (47.0+) | Accessible only by the custom Apex code in the package. The guide names this as the value to "secure secrets such as API access keys and security tokens" |
| `protected` = `true` | Record | In a managed package, the subscriber can't read or modify the record; the developer modifies it with a package upgrade or the Metadata Apex classes |

Two consequences of record-level `protected` that bite later: the **developer name of a protected record can't be changed after release**, and **the subscriber can't create records of a protected type**. Records hidden by these rules are also unavailable to REST, SOAP, SOQL, and Setup — so "the deploy worked but I can't query it" is an expected outcome, not a bug.

Note the nuance against this skill's general rule that secrets do not belong in metadata: `PackageProtected` is Salesforce's documented mechanism for secrets *inside a managed package*, and it is not a substitute for Named Credentials in an ordinary, unpackaged org.

---

## Reading `__mdt` Records Needs Explicit Type Access On The Profile Or Permission Set

**What happens:** SOQL against a `__mdt` object returns zero rows for one user and every row for another, with no sharing rule and no field-level security involved.

**When it occurs:** From API version 47.0 the Metadata API exposes `PermissionSetCustomMetadataTypeAccess` and `ProfileCustomMetadataTypeAccess` — an `enabled` boolean per custom metadata type name that "indicates whether the records for this custom metadata type are readable". A permission set deployed without that entry leaves the type unreadable for its assignees.

**How to avoid:** Ship the `customMetadataTypeAccesses` entry alongside the type in the same release, and test as a non-admin user. Related trap: since API version 54.0, `DescribeSObjectResult.isAccessible()` returns `false` for custom metadata type objects when the user lacks permission — in 53.0 and earlier it returned `true` regardless, so code written against an older API version that gates on `isAccessible()` changes behaviour purely by raising the class's API version.

---

## `enableAdvancedCMTSecurity` Removes Custom Metadata From The API Surface Org-Wide

**What happens:** An integration that has read custom metadata values through the SOAP API for years starts returning nothing after an unrelated security hardening change. Apex, Flow, and formulas keep working.

**When it occurs:** `SchemaSettings.enableAdvancedCMTSecurity` (in `settings/Schema.settings-meta.xml`) is switched to `true`. The Metadata API guide describes it as making custom metadata type values "available only to Apex, flow, and formula operations (true) or exposed in other contexts such as through the Enterprise WSDL or SOAP API (false)". The default is `false`.

**How to avoid:** Inventory the non-Apex readers of every CMT — middleware, ETL, reporting extracts, external test harnesses — before enabling it, and route them through an Apex or REST service instead of direct object access. The sibling setting `enableAdvancedCSSecurity` does the same thing for Custom Settings, so a single hardening deploy can break both at once.

---

## Creating The Type And Creating Its Records Need Different Permissions

**What happens:** A release user can deploy the records but the deploy fails on the type, or an Apex-authoring developer can create the type but not populate it.

**When it occurs:** The two components carry different Special Access Rules in the Metadata API guide: **"To create custom metadata types, you must have the 'Author Apex' permission"**, while **"To create custom metadata records, you must have the 'Customize Application' permission."** A CI service account granted only one of the two deploys half the package.

**How to avoid:** Grant the deployment identity both permissions, and split a large change so that the type/field deploy and the record deploy can be diagnosed separately when one fails. Two further limits from the same section: Apex code "can create, read, and update (but not delete) custom metadata records, as long as the metadata is subscriber-controlled and visible from within the code's namespace", customers who install a managed custom metadata type "can't add new custom fields to it", and audit fields (`CreatedDate`, `CreatedBy`, `LastModifiedDate`, `LastModifiedBy`, `SystemModStamp`) remain uneditable.
