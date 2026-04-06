# LLM Anti-Patterns — Metadata API and Package.xml

Common mistakes AI coding assistants make when generating or advising on Metadata API operations and package.xml manifests.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Using wildcard (*) for metadata types that do not support it

**What the LLM generates:**

```xml
<types>
    <members>*</members>
    <name>StandardObject</name>
</types>
```

**Why it happens:** LLMs apply the wildcard `*` universally. Several metadata types do not support wildcards in retrieval, including `StandardObject`, `CustomLabel` (in some contexts), and nested child types. The retrieve returns zero components with no error, making it look like nothing exists.

**Correct pattern:**

```xml
<!-- For types that don't support wildcards, list members explicitly -->
<types>
    <members>Account</members>
    <members>Contact</members>
    <members>Opportunity</members>
    <name>CustomObject</name>
</types>
```

**Detection hint:** `<members>*</members>` on metadata types that require explicit member names — check against the Metadata Coverage Report.

---

## Anti-Pattern 2: Wrong API version in package.xml

**What the LLM generates:**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <version>48.0</version>
    <!-- Old API version from training data — misses newer metadata types -->
</Package>
```

**Why it happens:** LLMs freeze at training data versions. Using an outdated API version means newer metadata types (e.g., `ExperiencePropertyTypeBundle`, `OmniScript`) are not retrievable, and newer fields on existing types are silently omitted.

**Correct pattern:**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <version>62.0</version>
    <!-- Use the current API version — check release notes -->
</Package>
```

**Detection hint:** `<version>` below `60.0` in newly generated package.xml files.

---

## Anti-Pattern 3: Missing destructiveChangesPost.xml when deleting components

**What the LLM generates:**

```
To delete the old Apex class, remove it from your source directory and deploy.
```

**Why it happens:** LLMs assume that not including a component in a deployment will delete it from the target org. Metadata API does not delete components by omission. You must explicitly include a `destructiveChanges.xml` (pre-deploy) or `destructiveChangesPost.xml` (post-deploy) manifest.

**Correct pattern:**

```xml
<!-- destructiveChangesPost.xml -->
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>OldApexClass</members>
        <name>ApexClass</name>
    </types>
</Package>

<!-- Deploy with an empty package.xml and the destructive manifest -->
<!-- sf project deploy start --manifest package.xml --post-destructive-changes destructiveChangesPost.xml -->
```

**Detection hint:** Advice to "remove the file and deploy" without mentioning `destructiveChanges.xml` or `destructiveChangesPost.xml`.

---

## Anti-Pattern 4: Not accounting for deployment order dependencies

**What the LLM generates:**

```xml
<types>
    <members>MyApexClass</members>
    <name>ApexClass</name>
</types>
<types>
    <members>MyCustomObject__c</members>
    <name>CustomObject</name>
</types>
```

The LLM packages both together but MyApexClass references MyCustomObject__c. If the custom object does not yet exist in the target org, the Apex class compilation fails and the entire deployment rolls back.

**Why it happens:** LLMs generate flat manifests without considering compilation dependencies. When deploying to an org that does not yet have the custom object, the Apex class fails to compile.

**Correct pattern:**

```
Deploy in dependency order:
1. First deployment: CustomObject, CustomField, CustomLabel (schema)
2. Second deployment: ApexClass, ApexTrigger (code that references schema)
3. Third deployment: FlexiPage, Flow, PermissionSet (things referencing code)

Or use a single deployment that includes ALL dependencies — the Metadata API
resolves order within a single deploy, but will fail if the target org is
missing prerequisites not in the package.
```

**Detection hint:** Package.xml that includes both Apex classes and the custom objects they reference, with no guidance about target org prerequisites.

---

## Anti-Pattern 5: Including both package.xml and destructiveChanges.xml members for the same component

**What the LLM generates:**

```xml
<!-- package.xml -->
<types>
    <members>MyField__c</members>
    <name>CustomField</name>
</types>

<!-- destructiveChangesPost.xml -->
<types>
    <members>MyField__c</members>
    <name>CustomField</name>
</types>
```

**Why it happens:** LLMs generate both files independently and may include the same component in both. This creates a conflict — the deployment tries to both deploy and delete the same component, resulting in unpredictable behavior or deployment failure.

**Correct pattern:**

```xml
<!-- A component should appear in EITHER package.xml OR destructiveChanges.xml, never both -->
<!-- package.xml: components to deploy/update -->
<types>
    <members>NewField__c</members>
    <name>CustomField</name>
</types>

<!-- destructiveChangesPost.xml: components to delete AFTER the deploy -->
<types>
    <members>OldField__c</members>
    <name>CustomField</name>
</types>
```

**Detection hint:** Same `<members>` value appearing in both `package.xml` and `destructiveChanges*.xml`.

---

## Anti-Pattern 6: Generating package.xml with incorrect metadata type names

**What the LLM generates:**

```xml
<types>
    <members>*</members>
    <name>LightningComponent</name> <!-- Wrong — should be LightningComponentBundle for LWC -->
</types>
<types>
    <members>*</members>
    <name>CustomSetting</name> <!-- Wrong — custom settings use CustomObject type -->
</types>
```

**Why it happens:** LLMs guess metadata type names from common terminology. The actual Metadata API type names are specific: `LightningComponentBundle` (LWC), `AuraDefinitionBundle` (Aura), `CustomObject` (includes Custom Settings), `Flow` (not `FlowDefinition`). Wrong names cause empty retrieval with no error.

**Correct pattern:**

```xml
<!-- LWC components -->
<types>
    <members>*</members>
    <name>LightningComponentBundle</name>
</types>
<!-- Aura components -->
<types>
    <members>*</members>
    <name>AuraDefinitionBundle</name>
</types>
<!-- Custom Settings are retrieved as CustomObject -->
<types>
    <members>MySetting__c</members>
    <name>CustomObject</name>
</types>
```

**Detection hint:** Metadata type names like `LightningComponent`, `CustomSetting`, `FlowDefinition`, or `WorkflowRule` — all are incorrect or deprecated API names.
