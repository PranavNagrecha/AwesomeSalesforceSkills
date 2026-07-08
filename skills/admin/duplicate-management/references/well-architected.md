# Well-Architected Mapping: Duplicate Management

## Pillars Addressed

### Reliability

Duplicate prevention and survivorship protect the accuracy and usability of core records.

- Matching and duplicate rules prevent avoidable record fragmentation.
- Merge governance keeps authoritative values consistent.
- Coverage is bounded by the create paths a rule evaluates and by the platform's rule ceilings (5 active duplicate rules per object; 3 matching rules per duplicate rule; 5 active matching rules per object across rules). A design that exceeds a ceiling fails at activation, not at design review.

### Operational Excellence

Good duplicate management requires ownership, stewardship, and repeatable remediation.

- Steward workflows convert alerts into action.
- Metrics help tune rules instead of guessing.

### User Experience

Users trust Salesforce more when search, reports, and activity history point to one believable record.

- Reduced duplicate clutter improves day-to-day navigation.
- Clear blocking and alert behavior reduces confusion during data entry.

## Pillars Not Addressed

- **Security** - duplicate management is not an access control, but it is coupled to two of them, and the coupling is load-bearing rather than incidental. Matching rules read fields through the acting user's field-level security, so missing FLS on a referenced field silently disables detection for that user. A duplicate rule set to bypass sharing rules evaluates all potential duplicates regardless of ownership while withholding the matched record from a user who lacks access to it. Design both deliberately; neither is a security feature, and both fail quietly when they are assumed rather than decided.
- **Scalability** - the focus is record quality and stewardship, not system throughput design.

## Official Sources Used

- Salesforce Well-Architected Overview — data quality and stewardship framing
- Metadata API Developer Guide — duplicate and matching rule metadata deployment behavior
- Salesforce Help — Duplicate Rules (limits, skipped create paths, field-level access precondition, match keys):
  https://help.salesforce.com/s/articleView?id=sales.duplicate_rules_overview.htm&language=en_US&type=5
- Salesforce Help — Matching Methods Used with Matching Rules (algorithms and thresholds per standard fuzzy method):
  https://help.salesforce.com/s/articleView?id=sales.matching_rules_matching_methods.htm&language=en_US&type=5
- Salesforce Help — Duplicate Prevention (bypass sharing rules, supported objects, Lightning vs. Classic behavior):
  https://help.salesforce.com/s/articleView?id=sales.duplicate_prevention.htm&language=en_US&type=5
- Salesforce Help — Manage Duplicates Using Duplicate Record Sets (how sets are created; reporting on duplicates):
  https://help.salesforce.com/s/articleView?id=sf.duplicate_management_duplicate_record_sets.htm&language=en_US&type=5
- Apex Reference Guide — `Database.DMLOptions.DuplicateRuleHeader` (`allowSave`, `runAsCurrentUser`):
  https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_class_Database_DMLOptions_DuplicateRuleHeader.htm
- Object Reference — `DuplicateRecordSet` (grouping object for duplicate rule and duplicate job results):
  https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_duplicaterecordset.htm
- Object Reference — `DuplicateRecordItem` (each record flagged as a duplicate within a set):
  https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_duplicaterecorditem.htm
