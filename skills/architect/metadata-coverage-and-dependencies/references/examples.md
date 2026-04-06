# Examples — Metadata Coverage and Dependencies

Concrete worked examples of metadata coverage assessment and dependency analysis in Salesforce contexts.

---

## Example 1: Pre-Deletion Impact Analysis for a Custom Field

**Context:** A healthcare ISV needs to retire `Patient_SSN__c` from the `Contact` object as part of a data privacy remediation. The field has been in the org for 6 years and the team has no documentation of where it is referenced.

**Approach Applied:**
- Queried `MetadataComponentDependency` via Tooling API:
  ```sql
  SELECT MetadataComponentName, MetadataComponentType
  FROM MetadataComponentDependency
  WHERE RefMetadataComponentName = 'Patient_SSN__c'
    AND RefMetadataComponentType = 'CustomField'
  ```
- Results returned 23 dependent components: 4 Apex classes, 3 Apex triggers, 6 Validation Rules, 5 Reports, 3 Flow definitions, and 2 Page Layouts.
- Each dependency classified as hard (Apex/Flow/Validation Rule — will break) or soft (Report/Page Layout — will degrade gracefully).
- Hard dependencies refactored first: Apex classes updated to remove field references, Flows updated to remove field-based decision nodes, Validation Rules deactivated.
- Soft dependencies cleaned up: Reports had the column removed, Page Layouts had the field removed.
- Field deleted in sandbox, validated, then promoted to production.

**Result:** Zero deployment failures. All 23 dependencies resolved before the destructive change was attempted. Without the dependency query, the team would have discovered broken references through trial-and-error deployment.

---

## Example 2: Packaging Boundary Discovery for Unlocked Package Migration

**Context:** A financial services company is migrating from unpackaged metadata to unlocked packages. The org has 1,200 custom metadata components and no clear modular boundaries.

**Approach Applied:**
- Exported full dependency graph via Bulk API 2.0:
  ```bash
  sf data query \
    --query "SELECT MetadataComponentName, MetadataComponentType, RefMetadataComponentName, RefMetadataComponentType FROM MetadataComponentDependency" \
    --use-tooling-api --bulk --target-org prodOrg \
    --result-format csv > dependencies.csv
  ```
- Loaded the CSV into a graph analysis tool (Python NetworkX). Identified 4 tightly coupled clusters:
  - Lending (280 components, 420 internal edges, 12 external edges)
  - Compliance (190 components, 310 internal edges, 8 external edges)
  - Client Onboarding (340 components, 580 internal edges, 22 external edges)
  - Shared Services (140 components — referenced by all three above)
- Shared Services became the base package. Lending, Compliance, and Client Onboarding each declared a dependency on Shared Services.
- Cross-checked each cluster against the Metadata Coverage Report for unlocked package support. Found that `Territory2Model` metadata (used in Lending) was not supported in unlocked packages — documented as a manual post-install step.

**Result:** Four unlocked packages with clean dependency ordering. Deployment time reduced from 45 minutes (full org deploy) to 8 minutes (incremental package version install). One documented manual step for Territory Management.

---

## Example 3: Coverage Gap Assessment for a Managed Package Release

**Context:** An AppExchange ISV is preparing a 2GP managed package release. QA found that some metadata types in the package source were silently excluded from the package version during `sf package version create`.

**Approach Applied:**
- Reviewed the Metadata Coverage Report at the target API version (v60.0).
- Cross-referenced every metadata type in the package source directory against the "2GP Managed Packages" column.
- Found three unsupported types:
  - `PlatformEventSubscriberConfig` — Beta for 2GP.
  - `ManagedContentType` — Not Supported for 2GP.
  - `AIApplication` — Not Supported for 2GP.
- For `PlatformEventSubscriberConfig`: accepted the Beta risk since the feature was non-critical and the subscriber config could be recreated manually.
- For `ManagedContentType`: moved to a post-install script that creates the content type via REST API.
- For `AIApplication`: documented as a manual setup step in the package installation guide.

**Result:** Package version created cleanly. All three gaps documented with workarounds. No silent exclusions in the final package.

---

## Example 4: Dependency Graph for Apex Refactoring Safety

**Context:** A development team needs to refactor a utility Apex class (`DataTransformUtils`) that has grown to 2,400 lines. Before splitting it into smaller classes, they need to know every component that calls it.

**Approach Applied:**
- Queried downstream dependents:
  ```sql
  SELECT MetadataComponentName, MetadataComponentType
  FROM MetadataComponentDependency
  WHERE RefMetadataComponentName = 'DataTransformUtils'
    AND RefMetadataComponentType = 'ApexClass'
  ```
- Found 34 dependent Apex classes, 2 Apex triggers, and 5 Flow Apex Actions.
- Grouped the 34 dependent classes by functional area (matching the packaging boundary analysis from an earlier project).
- Split `DataTransformUtils` into `DataTransformUtils_Lending`, `DataTransformUtils_Compliance`, and `DataTransformUtils_Core`.
- Updated each dependent component to reference the correct new class.
- Re-queried the dependency graph after refactoring to confirm no references to the original class name remained.

**Result:** Refactoring completed with zero test failures. Dependency graph confirmed clean separation.
