# Examples — Destructive Changes Deployment

## Example 1: Deleting a Custom Field That Is No Longer Used

**Context:** A project is retiring `Account.LegacyRegion__c`, a custom text field that was replaced by a standard field. No validation rules, formula fields, Apex classes, or page layouts currently reference it.

**Problem:** Without guidance, a practitioner might attempt to delete the field by simply omitting it from a future deployment package, expecting the Metadata API to remove components not listed. The Metadata API does not work this way — components not in the package are left unchanged. The field remains in the org indefinitely.

**Solution:**

Build a `destructiveChanges.xml` alongside an empty companion `package.xml`:

```xml
<!-- destructiveChanges.xml -->
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Account.LegacyRegion__c</members>
        <name>CustomField</name>
    </types>
</Package>
```

```xml
<!-- package.xml (empty companion) -->
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <version>61.0</version>
</Package>
```

Deploy with the sf CLI:

```bash
sf project deploy start \
  --manifest package.xml \
  --pre-destructive-changes destructiveChanges.xml \
  --target-org myOrgAlias
```

**Why it works:** The `CustomField` metadata type uses a `ParentObject.FieldName` member naming convention. By listing the member explicitly and pairing the destructive manifest with a valid `package.xml`, the Metadata API processes the deletion in a single transaction. The companion `package.xml` is required even when nothing is being added — the deployment container must always include a valid package manifest.

---

## Example 2: Removing a Custom Field Still Referenced in a Validation Rule (Post Variant)

**Context:** A team is removing `Opportunity.DiscountOverride__c`. However, a validation rule `Opportunity.BlockHighDiscount` currently checks this field in its formula. Both the field deletion and an updated validation rule formula (which removes the reference) need to be deployed together.

**Problem:** If the practitioner puts the field deletion in `destructiveChangesPre.xml` and the updated validation rule in `package.xml`, the deletion fires first. At the moment of deletion, the validation rule still holds the reference, so Salesforce rejects the deletion with: "This custom field is used in 1 validation rules."

**Solution:**

Put the updated validation rule in `package.xml` and the field deletion in `destructiveChangesPost.xml`:

```xml
<!-- package.xml -->
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Opportunity.BlockHighDiscount</members>
        <name>ValidationRule</name>
    </types>
    <version>61.0</version>
</Package>
```

```xml
<!-- destructiveChangesPost.xml -->
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Opportunity.DiscountOverride__c</members>
        <name>CustomField</name>
    </types>
</Package>
```

```bash
sf project deploy start \
  --manifest package.xml \
  --post-destructive-changes destructiveChangesPost.xml \
  --target-org myOrgAlias
```

**Why it works:** With the post variant, the Metadata API deploys and activates the updated validation rule first (with the reference removed from its formula), and only then processes the field deletion. By the time the deletion fires, no active component references the field, so the API allows it.

---

## Anti-Pattern: Using a Wildcard in a Destructive Manifest

**What practitioners do:** Copy the wildcard syntax from `package.xml` into a destructive manifest to "delete all custom reports in a folder":

```xml
<!-- WRONG — wildcards are not supported in destructive manifests -->
<types>
    <members>*</members>
    <name>Report</name>
</types>
```

**What goes wrong:** The Metadata API does not expand wildcards in destructive manifests. The `*` is treated as a literal member name. The deployment either fails because a member named `*` does not exist, or it silently succeeds but deletes nothing. The practitioner may believe the deletion succeeded when it did not.

**Correct approach:** Enumerate every component explicitly. Use `sf project retrieve start` or SOQL against `MetadataComponent` to get the full list of API names, then list each one as a separate `<members>` element.
