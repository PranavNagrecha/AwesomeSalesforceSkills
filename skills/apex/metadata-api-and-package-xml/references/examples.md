# Examples — Metadata API and Package.xml

## Example 1: Retrieving a Mixed Metadata Set for Version Control

**Context:** A developer needs to bring all custom objects, all Apex classes, all Lightning flows, and the Account standard object into a Git repository for the first time. The org has been configured through the UI with no prior source control.

**Problem:** Without a correct package.xml, the developer either retrieves nothing (missing type declarations), retrieves too much (pulling unrelated metadata), or misses the Account standard object entirely by using a wildcard that only covers custom objects.

**Solution:**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
  <types>
    <members>*</members>
    <name>CustomObject</name>
  </types>
  <types>
    <members>Account</members>
    <members>Contact</members>
    <members>Opportunity</members>
    <name>CustomObject</name>
  </types>
  <types>
    <members>*</members>
    <name>ApexClass</name>
  </types>
  <types>
    <members>*</members>
    <name>ApexTrigger</name>
  </types>
  <types>
    <members>*</members>
    <name>Flow</name>
  </types>
  <version>66.0</version>
</Package>
```

Run: `sf project retrieve start --manifest package.xml --target-org myOrg`

**Why it works:** The wildcard on `CustomObject` gets all custom objects. Standard objects (Account, Contact, Opportunity) are listed by name because wildcards do not include standard objects. The `<version>66.0</version>` tag ensures the retrieval uses the current API capabilities and metadata type support.

---

## Example 2: Deploying Apex with Dependency Cleanup Using Post-Destructive Changes

**Context:** A developer needs to remove a legacy custom object `LegacyInvoice__c` from a sandbox. The object is referenced in two Apex classes (`InvoiceService` and `InvoiceTriggerHandler`) which must first be updated to remove the reference before the object can be deleted.

**Problem:** If only a `destructiveChanges.xml` is deployed without first clearing the code references, the deployment fails with a "component in use" error. The default ordering (deletions run before additions) makes this impossible to fix in a single deployment unless `destructiveChangesPost.xml` is used.

**Solution:**

`package.xml` — update both Apex classes to remove the object references:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
  <types>
    <members>InvoiceService</members>
    <members>InvoiceTriggerHandler</members>
    <name>ApexClass</name>
  </types>
  <version>66.0</version>
</Package>
```

`destructiveChangesPost.xml` — delete the object after the class updates are committed:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
  <types>
    <members>LegacyInvoice__c</members>
    <name>CustomObject</name>
  </types>
</Package>
```

Deploy: `sf project deploy start --manifest package.xml --test-level NoTestRun --target-org mySandbox`

**Why it works:** Using `destructiveChangesPost.xml` forces the Apex class updates to be committed before the deletion is attempted. The dependency is cleared by the time the platform tries to delete the object. Using `destructiveChanges.xml` (the default pre-deletion file) would fail because the classes still reference the object at the point the deletion runs.

---

## Anti-Pattern: Using a Wildcard to Retrieve All Objects Including Standard Objects

**What practitioners do:** Write `<members>*</members>` for `CustomObject` assuming it retrieves all objects including standard objects like Account, Contact, and Lead.

**What goes wrong:** The retrieval completes successfully but standard objects are absent from the output. The developer proceeds assuming the retrieved package is complete, commits to source control, and then discovers during deployment to another org that all standard object customizations (field-level security, custom fields on standard objects, page layouts) are missing.

**Correct approach:** List each standard object by name in the `<members>` element. Standard objects do not support the wildcard specifier — only custom objects (those ending in `__c`) are covered by the `*` wildcard. Run a separate retrieval pass using a package.xml that explicitly names every standard object your org has customized.
