# LLM Anti-Patterns — Destructive Changes Deployment

Common mistakes AI coding assistants make when generating or advising on destructive changes deployments. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Including `<version>` in the Destructive Manifest

**What the LLM generates:** A `destructiveChanges.xml` file that includes a `<version>` element, mirroring the structure of `package.xml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>MyObject__c.OldField__c</members>
        <name>CustomField</name>
    </types>
    <version>61.0</version>
</Package>
```

**Why it happens:** LLMs are trained on large volumes of `package.xml` examples that always include `<version>`. The destructive manifest schema is a subset of the package schema, so the model generalizes incorrectly.

**Correct pattern:**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>MyObject__c.OldField__c</members>
        <name>CustomField</name>
    </types>
</Package>
```

**Detection hint:** Grep the generated destructive manifest file for `<version>` — its presence is always wrong.

---

## Anti-Pattern 2: Using Wildcards in a Destructive Manifest

**What the LLM generates:** A destructive manifest with a wildcard member, analogous to what works in `package.xml`:

```xml
<types>
    <members>*</members>
    <name>CustomField</name>
</types>
```

**Why it happens:** Wildcards are valid in `package.xml` for retrieval, and many LLM training examples show wildcard usage. The model does not distinguish between retrieve manifests and destructive manifests.

**Correct pattern:**

```xml
<types>
    <members>Account.OldField1__c</members>
    <members>Account.OldField2__c</members>
    <name>CustomField</name>
</types>
```

**Detection hint:** Check for `<members>*</members>` or `<members>\*</members>` in any destructive manifest file.

---

## Anti-Pattern 3: Recommending Pre Variant When Post Is Required

**What the LLM generates:** Advice to use `destructiveChangesPre.xml` or `--pre-destructive-changes` for a deletion where the referencing component is being updated in the same deployment:

```
"Use destructiveChangesPre.xml to delete the field, and include the updated validation rule in package.xml."
```

**Why it happens:** LLMs default to the pre variant because it is more commonly described in documentation and tutorials. The nuance that pre fires before additions — causing a "still referenced" failure when the fix is in the same package — is underrepresented in training data.

**Correct pattern:**

```
When the referencing component is updated in the same deployment, use destructiveChangesPost.xml (--post-destructive-changes). The updated component must land first so the reference is cleared before deletion fires.
```

**Detection hint:** If the generated plan includes both a component update and a deletion of a component it references, and the deletion is in a pre manifest, the ordering is wrong.

---

## Anti-Pattern 4: Suggesting Deletion of Record Types or Picklist Values via Manifest

**What the LLM generates:** A destructive manifest listing a Record Type or Picklist value member, or advice like "add the Record Type to destructiveChanges.xml to remove it":

```xml
<types>
    <members>Account.Customer</members>
    <name>RecordType</name>
</types>
```

**Why it happens:** The model knows Record Types are metadata and generalizes that all metadata can be deleted via destructive manifests. The constraint that Record Types and Picklist values are undeletable via the API is a Salesforce-specific limitation not obvious from general Metadata API patterns.

**Correct pattern:**

```
Record Types cannot be deleted via the Metadata API. Remove them manually in Setup > Object Manager > [Object] > Record Types. Similarly, Picklist field values must be removed through Setup, not through a deployment manifest.
```

**Detection hint:** Scan generated manifest members for `<name>RecordType</name>` or check if the advice involves deleting picklist field values via XML.

---

## Anti-Pattern 5: Omitting the Companion `package.xml` When Using CLI Flags

**What the LLM generates:** A deployment command that only references the destructive manifest, with no `--manifest` flag:

```bash
sf project deploy start \
  --pre-destructive-changes destructiveChanges.xml \
  --target-org myOrgAlias
```

**Why it happens:** The model focuses on the destructive-specific flags and overlooks that `sf project deploy start` requires a `--manifest` (or `--source-dir`) argument. When no additions are needed, an empty-but-valid companion `package.xml` is still required.

**Correct pattern:**

```bash
# Create an empty companion package.xml with just the API version
sf project deploy start \
  --manifest package.xml \
  --pre-destructive-changes destructiveChanges.xml \
  --target-org myOrgAlias
```

**Detection hint:** Look for `sf project deploy start` commands that include `--pre-destructive-changes` or `--post-destructive-changes` but lack a `--manifest` or `--source-dir` argument.
