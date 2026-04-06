# Well-Architected Notes — Picklist Field Integrity Issues

## Relevant Pillars

- **Reliability** — Picklist data integrity directly impacts report accuracy, automation reliability, and integration data quality. Orphaned values cause silent failures in formula fields, validation rules, and Flow decision elements that check specific picklist values. Restricting picklists and enforcing dependent relationships at the data layer ensures consistent behavior across all channels.

- **Security** — Unrestricted picklists that accept arbitrary API input can be exploited to inject unexpected values that bypass business logic. Record type picklist mapping drift can expose values to user profiles that should not have access to certain business processes.

- **Operational Excellence** — Proactive picklist hygiene (regular audits, restricted fields, validation rules for dependent picklists) reduces support tickets and data cleanup effort. A documented deployment checklist that includes record type mapping prevents the most common picklist configuration gap.

## Architectural Tradeoffs

1. **Restricted vs. Unrestricted picklists**: Restricted picklists enforce data integrity at the API layer but require explicit value management — every new value must be deployed before integrations can use it. Unrestricted picklists allow flexibility for integrations but create data pollution risk. Decision: restrict fields where data quality is critical; leave unrestricted only where integrations need to write dynamic values AND you have compensating validation.

2. **Validation rule vs. Apex trigger for dependent picklist enforcement**: Validation rules are declarative and easier to maintain but become unwieldy for large dependent picklist matrices. Apex triggers scale better for complex combinations using Custom Metadata mapping tables but add code maintenance overhead.

3. **Global Value Set vs. Object-local picklist**: GVS provides single-source value management across objects but requires record type mapping on every object. Object-local picklists allow independent value sets per object but create duplication.

## Anti-Patterns

1. **"Set and forget" picklist management** — Adding values without auditing record type mappings, dependent picklist matrices, or downstream automation. Over time, value sets drift from actual data and record type mappings become incomplete.

2. **Trusting dependent picklists as validation** — Assuming the UI-only dependent filtering provides data-layer enforcement. This leads to impossible value combinations entering via API, breaking reports and analytics.

3. **Bulk data loads without picklist pre-validation** — Running Data Loader imports without first validating that all picklist values in the CSV exist in the target field's value set.

## Official Sources Used

- Picklist Limitations — https://help.salesforce.com/s/articleView?id=platform.picklist_limitations.htm
- Data Loader allows invalid picklist values — https://help.salesforce.com/s/articleView?id=000381951
- Dependent Picklist Considerations — https://help.salesforce.com/s/articleView?id=platform.fields_dependent_field_considerations.htm
- Picklist Metadata API — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_picklist.htm
- UI API Get Picklist Values — https://developer.salesforce.com/docs/atlas.en-us.uiapi.meta/uiapi/ui_api_resources_picklist_values.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
