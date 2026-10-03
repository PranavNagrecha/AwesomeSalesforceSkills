# Well-Architected Notes: OmniStudio Debugging

## Relevant Pillars

- **Operational Excellence**: This skill exists primarily to improve operability. OmniStudio assets that fail silently, produce ambiguous output, or are impossible to trace in production are operability failures. Structured debug procedures, explicit error propagation via `rollbackOnError`, and observable failure responses are all direct Operational Excellence improvements. A well-operated OmniStudio deployment is one where failures surface immediately, can be triaged without tribal knowledge, and have a clear owner.

- **Reliability**: Unobserved failures in Integration Procedures (silent HTTP errors, empty DataRaptor responses, missing Named Credentials) undermine the reliability of experiences built on OmniStudio. Making failures visible and deliberately handled is a prerequisite for reliable behavior. Environment parity, ensuring active version, Named Credentials, Remote Site Settings, and Custom Settings are consistent across sandbox and production, is a core reliability concern for OmniStudio-based implementations.

## Architectural Tradeoffs

- **Fail-open default vs. explicit error handling**: OmniStudio is designed to fail open, elements that encounter errors continue execution unless explicitly configured to stop. This makes initial development faster (nothing breaks visibly) but creates reliability debt. The tradeoff is between development convenience and production observability. The correct resolution is to always configure explicit failure behavior for critical elements, accepting the upfront cost for long-term reliability.

- **Centralized debug via IP Debug tab vs. distributed tracing**: The IP Debug tab provides per-element granularity but is a manual, synchronous tool only usable in the designer. For production issues in live transactions, debug output is not persisted unless the org has custom logging instrumentation. Teams operating at scale must decide whether lightweight in-designer debugging is sufficient or whether they need a persistent logging pattern (for example, using a Platform Event from a custom Apex action to capture IP execution details). The tradeoff is implementation cost against operational depth.

- **Preview as the testing surface vs. full deployment testing**: Preview is low-friction and fast but excludes Navigation Actions, runs in the designer user's context, and does not exercise environment-specific dependencies. Full deployment testing is higher friction but catches more real failure modes. Teams should use Preview for iteration and deployment context testing for validation, not treat them as equivalent.

## Anti-Patterns

1. **Treating Preview as a substitute for end-to-end testing**: Preview excludes Navigation Actions by platform design, runs in the admin designer's security context rather than the runtime user's context, and does not exercise production Named Credentials or Remote Site Settings. Teams that ship OmniStudio experiences validated only in Preview will encounter failures that Preview never surfaces. Always test in a deployed context with a representative user before promoting to production.

2. **Deploying OmniStudio assets without verifying activation**: Deployment creates a version but does not activate it. If teams assume deployment equals activation, the old version remains active in production and the new behavior is never exercised. Every OmniStudio deployment runbook must include an explicit activation verification step.

3. **No rollbackOnError on Integration Procedure roots**: An IP without `rollbackOnError: true` will silently continue after element failures, returning partial or empty data to the caller with no signal that something went wrong. This makes production failures nearly impossible to detect without actively monitoring the user experience. Every production IP must have explicit failure behavior configured.

## Official Sources Used

- Trailhead, Omnistudio Omniscripts, "Dig into the Omniscript Designer" (Preview with Context ID, Data JSON, Reset Data, Action Debugger) - https://trailhead.salesforce.com/content/learn/modules/omnistudio-omniscript/dig-into-the-omniscript-designer
- Trailhead, Omnistudio Integration Procedures, "Explore the Integration Procedure Designer" (Preview pane Errors/Debug Output, Cache Block, Conditional Block, Loop Block, Try-Catch Block, Execution Conditional Formula, Response Action) - https://trailhead.salesforce.com/content/learn/modules/omnistudio-integration-procedures/explore-omnistudio-integration-procedure-designer
- Trailhead, Omnistudio Integration Procedures, "Get Started with Omnistudio Integration Procedures" (single server call, Response Action trims data) - https://trailhead.salesforce.com/content/learn/modules/omnistudio-integration-procedures/get-started-omnistudio-integration-procedures
- Trailhead, Omnistudio Data Mappers, "Build a Data Mapper Turbo Extract and Data Mapper Load" (Preview saves Load records, Upsert Key behavior) - https://trailhead.salesforce.com/content/learn/modules/omnistudio-dataraptors/build-a-dataraptor-turbo-extract-and-dataraptor-load
- Industries Common Resources Developer Guide, Summer '26: OmniScript and OmniIntegrationProcedure `isActive` (no `rollbackOnError` field on OmniIntegrationProcedure), OmniDataTransform `active`, `fieldLevelSecurityEnabled`, `rollbackOnError`, `errorIgnored` - https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_industries_dev_guide.pdf
- Apex Developer Guide, Summer '26: "Adding Remote Site Settings" (named credential endpoints need no remote site setting) - https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf
- Metadata API Developer Guide, Summer '26: RemoteSiteSetting type and sample - https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf
- Salesforce CLI source-deploy-retrieve 12.22.6 metadata registry (`omniIntegrationProcedures`/`oip`, `omniScripts`/`os`, `omniDataTransforms`/`rpt`), local install at /usr/local/lib/sf/node_modules/@salesforce/source-deploy-retrieve/lib/src/registry/metadataRegistry.json

### Cited by earlier revisions, not re-fetched (UNVERIFIED (2026-10-03))

- Preview and Test an OmniScript - https://help.salesforce.com/s/articleView?id=sf.os_preview_an_omniscript_8849.htm&language=en_US&type=5
- Debug and Activate an Integration Procedure - https://help.salesforce.com/s/articleView?id=sf.preview_debug_and_activate_an_omnistudio_integration_procedure.htm&language=en_US&type=5
- Error Handling in Integration Procedures - https://help.salesforce.com/s/articleView?id=sf.os_error_handling_in_integration_procedures.htm&language=en_US&type=5
