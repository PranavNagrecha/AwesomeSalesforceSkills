# Well-Architected Notes: DataRaptor Load and Extract

## Relevant Pillars

- **Reliability**: DataRaptor Load's absence of rollback on partial multi-object failure means that error handling must be explicitly designed into every Integration Procedure using Load. Without explicit `iferror` checks, failures are invisible to the user and the system reaches an inconsistent state.
- **Operational Excellence**: Using the Preview tab for every DataRaptor before embedding it in an Integration Procedure is a development discipline that prevents regressions. Testing each DataRaptor in isolation makes the overall Integration Procedure easier to debug.
- **Scalability**: DataRaptor Load's standard-DML row-at-a-time approach means it is not appropriate for data volumes that require Bulk API. Architects must document the volume constraints of any DataRaptor Load in the technical design to prevent future misuse.

## Architectural Tradeoffs

**Turbo Extract vs Standard Extract:** Turbo Extract is faster but less capable. For simple field reads in performance-sensitive FlexCards, Turbo is the right choice. For cross-object or relationship data, standard Extract is required. Do not use Turbo Extract and then wonder why relationship fields are empty.

**DataRaptor Load vs Apex DML:** DataRaptor Load is configuration-driven and maintainable by OmniStudio developers without Apex skills. Apex DML supports bulkification, rollback, and complex business logic. For anything beyond simple conversational data entry, Apex DML is more appropriate.

## Anti-Patterns

1. **Using DataRaptor Load for bulk data operations**: No Bulk API support means governor limit violations at scale. Use Bulk API or Batch Apex for volume operations.
2. **Not checking `iferror` after Load steps**: Silent failures lead to inconsistent data state. Always check and handle the `iferror` node.
3. **Using label names in output mapping paths**: API relationship names are required. Using labels produces empty output with no error.

## Official Sources Used

- Industries Common Resources Developer Guide, Summer '26 (release 262): Omnistudio Metadata API Types > OmniDataTransform and OmniDataTransformItem (fields, declarative sample, package.xml), OmniStudioSettings (`enableOmniStudioMetadata`, `enableOmniStudioDrVersion`), Omnistudio Standard Objects (OmniDataTransform is internal use only) - https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_industries_dev_guide.pdf
- Trailhead, Omnistudio Data Mappers, "Discover Data Mapper Types" (four types; Turbo Extract scope; Load creates and updates) - https://trailhead.salesforce.com/content/learn/modules/omnistudio-dataraptors/discover-dataraptor-types
- Trailhead, Omnistudio Data Mappers, "Explore Data Mapper Features" (designer tabs, Options tab FLS check and platform cache) - https://trailhead.salesforce.com/content/learn/modules/omnistudio-dataraptors/explore-dataraptor-features
- Trailhead, Omnistudio Data Mappers, "Build a Data Mapper Turbo Extract and Data Mapper Load" (Extract Output Path, filters, Upsert Key, Is Required For Upsert, Preview saves records) - https://trailhead.salesforce.com/content/learn/modules/omnistudio-dataraptors/build-a-dataraptor-turbo-extract-and-dataraptor-load
- Apex Developer Guide, Summer '26: Execution Governors and Limits (150 DML statements, 10,000 DML rows per transaction) - https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf
- Salesforce CLI source-deploy-retrieve 12.22.6 metadata registry (`omniDataTransforms` directory, `rpt` suffix), local install at /usr/local/lib/sf/node_modules/@salesforce/source-deploy-retrieve/lib/src/registry/metadataRegistry.json

### Cited by earlier revisions, not re-fetched (UNVERIFIED (2026-10-03))

- OmniStudio Help: DataRaptor Extract Overview - https://help.salesforce.com/s/articleView?id=sf.os_dataraptor_extract_overview.htm
- OmniStudio Help: DataRaptor Load Overview - https://help.salesforce.com/s/articleView?id=sf.os_dataraptor_load_overview.htm
- Omnistudio Data Mapper Best Practices ("keep the number of SObjects to three or fewer") - https://help.salesforce.com/s/articleView?id=sf.os_dataraptor_best_practices_47412.htm&language=en_US&type=5
