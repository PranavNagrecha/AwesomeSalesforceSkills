# Well-Architected Mapping: Duplicate Management

## Pillars Addressed

### Reliability

Duplicate prevention and survivorship protect the accuracy and usability of core records.

- Matching and duplicate rules prevent avoidable record fragmentation.
- Merge governance keeps authoritative values consistent.

### Operational Excellence

Good duplicate management requires ownership, stewardship, and repeatable remediation.

- Steward workflows convert alerts into action.
- Metrics help tune rules instead of guessing.

### User Experience

Users trust Salesforce more when search, reports, and activity history point to one believable record.

- Reduced duplicate clutter improves day-to-day navigation.
- Clear blocking and alert behavior reduces confusion during data entry.

## Pillars Not Addressed

- **Security** - duplicate management touches access only incidentally.
- **Scalability** - the focus is record quality and stewardship, not system throughput design.

## Official Sources Used

- Metadata API Developer Guide, `DuplicateRule` — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf (the `actionOnInsert` / `actionOnUpdate` `Allow`|`Block` enum, the `operationsOnInsert` / `operationsOnUpdate` `alert`|`report` arrays, the `alertText` constraint that at least one action must be `Allow`, `securityOption` `EnforceSharingRules` vs `BypassSharingRules`, `duplicateRuleFilter`, `sortOrder`, and the `DuplicateRuleMatchRule` / `ObjectMapping` cross-object shape used throughout `references/metadata-examples.md`)
- Metadata API Developer Guide, `MatchingRule` — same PDF (the one-file-per-object `<MatchingRules>` container, `matchingRuleItems` with `fieldName` / `blankValueBehavior` / `matchingMethod`, the closed `matchingMethod` enum `Exact`|`FirstName`|`LastName`|`CompanyName`|`Phone`|`City`|`Street`|`Zip`|`Title`, `booleanFilter`, and the rule that only `Active` and `Inactive` are declarable in a package)
- Metadata API Developer Guide, `FilterItem` / `FilterOperation` — same PDF (the operator set available to `duplicateRuleFilterItems`, cited in the filtered Block-rule example)
- Object Reference, `DuplicateRule` and `MatchingRule` / `MatchingRuleItem` standard objects — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf (query-only supported calls, the four-value `sObjectType` picklist behind the "Standard Duplicate Rules Cover a Short, Fixed Object List" gotcha, the `RuleStatus` values behind the asynchronous-activation gotcha, and the Summer '20 View Setup and Configuration access rule that constrains steward reporting)
- Object Reference, `DuplicateRecordSet` / `DuplicateRecordItem` / `DuplicateJob` — same PDF (the artefacts the `report` operation produces, their read-write access model, `RecordCount`, and the polymorphic `RecordId` that limits custom report types to Account, Contact, Individual, Lead)
- Apex Developer Guide, "Triggers and Order of Execution" and "Setting DML Options" — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf (duplicate rules at step 6 and the block action halting after-triggers and workflow; the step 11b statement that duplicate rules are not re-run after a workflow field update; the scope limit that `DMLOptions` applies to Apex DML and not the UI)
- Apex Reference Guide, `DMLOptions.DuplicateRuleHeader`, `Database.DuplicateError`, `Datacloud.DuplicateResult` and `Datacloud.FindDuplicates` — Apex Reference Guide PDF (`allowSave` scoped to Alert rules, `runAsCurrentUser` and its lead-conversion recommendation, the `getDuplicateRule()` / `getErrorMessage()` / `isAllowSave()` result surface, and the 50-record input cap plus the `System.HandledException` thrown when no rule is active)
- Salesforce Well-Architected — data quality and stewardship framing behind the Reliability and Operational Excellence sections above
