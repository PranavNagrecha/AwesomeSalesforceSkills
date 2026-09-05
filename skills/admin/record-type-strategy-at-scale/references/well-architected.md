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

- **Metadata API Developer Guide — `RecordType`** (https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf) — `active`, `businessProcess`, `picklistValues` / `RecordTypePicklistValue`; the "Don't use record types as an access control mechanism" warning behind the Security pillar note; the note that retrieving a record type makes it appear in any `Profile` and `PermissionSet` retrieved in the same package; and "This metadata type doesn't support the wildcard character `*`" behind gotchas #9.
- **Metadata API Developer Guide — `Profile`** (same PDF) — `ProfileRecordTypeVisibility` (`recordType`, `visible`, `default`, `personAccountDefault`) and `ProfileLayoutAssignments` (`layout` required, `recordType` optional), which together are the N x M matrix this skill governs; plus `recordTypeVisibilities` "isn't retrieved or deployed for inactive record types" in API 29.0 and later (gotchas #8).
- **Metadata API Developer Guide — `PermissionSet`** (same PDF) — `PermissionSetRecordTypeVisibility` carrying only `recordType` and `visible`, and no `layoutAssignments` field at all. This is the grounding for the Operational Excellence claim that a permission-set-first org still edits profiles per record type, and for gotchas #5 and #6.
- **Object Reference — `RecordType`** (https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf) — supported calls, `DeveloperName`, `IsActive` ("Only active record types can be applied to records"), `BusinessProcessId`, `IsPersonType`, `SobjectType`. Behind every audit query in `metadata-examples.md` sections 4 and 8.
- **Apex Reference Guide — `RecordTypeInfo` Class** (https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf) — `getRecordTypeInfos()`, `getRecordTypeInfosByDeveloperName()`, `isActive()`, `isAvailable()`, `isDefaultRecordTypeMapping()`, `isMaster()`. Behind the per-persona availability audit and the Master-fallback claim in gotchas #5.
- **Apex Developer Guide — Triggers and Order of Execution** (same PDF) — the save-order steps a `RecordTypeId` update actually runs, behind gotchas #7 and the Scalability note that a consolidation's cost is dominated by the data migration, not the metadata deploy.
- **Bulk API 2.0 Developer Guide** (https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_asynch.pdf) — the ingest job request shape (`object`, `contentType`, `operation`, `lineEnding`), the `insert / update / delete / hard delete / upsert` operation list, and the `LF` / `CRLF` rule used in the migration step.
- **Salesforce Well-Architected** (https://architect.salesforce.com/well-architected/overview) — the pillar framing used in the Relevant Pillars section above.
