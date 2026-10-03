# Metadata Examples: Vector Database Management

## Example A: Move the index configuration to another org

**Context:** The validated index must be recreated in production.

**Solution:** In Data Cloud Setup > Data Kits, create a data kit, add the search index under Search Index, save, and publish it; then add the data kit to a package in Package Manager. In the target org, use Search Index > New > Data Kit Setup. To keep the data kit in source control, retrieve it with this manifest:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Support_Knowledge_Search</members>
        <name>DataPackageKitDefinition</name>
    </types>
    <types>
        <members>*</members>
        <name>DataPackageKitObject</name>
    </types>
    <version>67.0</version>
</Package>
```

**Grounding:** Data Cloud guide (262), "Add a Search Index Configuration to a Data Kit" and "Create a Search Index Configuration from a Data Kit"; Metadata API Developer Guide (262), "DataPackageKitDefinition" and "DataPackageKitObject" (wildcard supported). UNVERIFIED (2026-10-03): the `referenceObjectType` value a search index uses inside `DataPackageKitObject`; inspect a retrieved kit before editing it by hand.
