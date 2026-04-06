# Well-Architected Notes — Record Type Strategy At Scale

## Relevant Pillars

- **Security** — Record type assignments control which picklist values and page layouts users see, but they are not a data access control. Security design must pair record types with field-level security (FLS) and object permissions to enforce actual data visibility. Dynamic Forms visibility rules are UI-only and do not replace FLS. Misconfiguring record type access on profiles can inadvertently expose picklist values from business processes that a user should not interact with.

- **Scalability** — The N x M layout assignment problem is the primary scalability concern. As the org adds profiles and record types, the layout assignment matrix grows quadratically. At scale (50+ profiles, 10+ record types per object), maintenance becomes a bottleneck. Dynamic Forms breaks this growth curve by decoupling field visibility from layout assignments. Reducing profile count by migrating to permission sets also reduces the M dimension.

- **Operational Excellence** — Record type strategy directly affects deployment reliability and change management velocity. Layout assignments deploy per profile, so a single record type addition can touch dozens of profile metadata files. Hardcoded Record Type IDs cause cross-environment deployment failures. Disciplined use of DeveloperName-based resolution, metadata-aware deployment packaging, and automated validation scripts reduces deployment risk and speeds release cycles.

## Architectural Tradeoffs

The central tradeoff is **granularity vs. maintainability**. More record types give finer-grained control over picklist values, page layouts, and business processes, but each new record type multiplies the maintenance surface. The key decision points:

1. **Record types for business process vs. field visibility.** If the only difference is which fields appear, Dynamic Forms is almost always cheaper to maintain than a new record type. But if picklist values or stage definitions differ, a separate record type is necessary.

2. **Profile count as a hidden multiplier.** Reducing profile count (by shifting entitlements to permission sets) reduces layout assignment burden across all objects. This is a cross-cutting architectural decision that pays dividends beyond any single object.

3. **Deployment granularity.** Fewer record types mean fewer profile metadata touchpoints per deployment, which reduces merge conflicts in version control and speeds CI/CD pipelines.

## Anti-Patterns

1. **One record type per team or department** — Creating record types as organizational groupings rather than business process differentiators leads to layout explosion without corresponding functional value. Use a custom field for team identity and Dynamic Forms for UI differentiation instead.

2. **Hardcoding Record Type IDs in Apex, Flows, or formulas** — IDs are org-specific and break on any cross-environment deployment. Always use `Schema.SObjectType.<Object>.getRecordTypeInfosByDeveloperName()` in Apex and `$Record.RecordType.DeveloperName` in declarative tools.

3. **Using Dynamic Forms as a security mechanism** — Dynamic Forms hides fields on the Lightning record page but does not restrict API, report, or list view access. Treating it as a security control creates a false sense of data protection. Always enforce access through FLS and object permissions.

## Official Sources Used

- Object Reference — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_concepts.htm
- Metadata API Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_intro.htm
- Metadata API — RecordType — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_recordtype.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Salesforce Architect Decision Guide — Build Forms — https://architect.salesforce.com/decision-guides/build-forms
- Assign Record Types and Page Layouts — https://help.salesforce.com/s/articleView?id=sf.customize_recordtype.htm
