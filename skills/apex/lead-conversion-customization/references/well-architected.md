# Well-Architected Notes — Lead Conversion Customization

## Relevant Pillars

- **Reliability** — Lead conversion is a multi-object, multi-trigger transaction. Partial failures can leave orphaned Account or Contact records. Using `allOrNone = false` requires explicit error handling per result; using `allOrNone = true` (the default) rolls back cleanly but may silently skip all conversions if one lead fails. Choose deliberately and handle errors explicitly.

- **Security** — Post-conversion DML updating Contact, Account, and Opportunity must use `with sharing` to respect record-level visibility. Field-level security (FLS) on the custom fields being written should be checked if the method runs in user context. A conversion service running in system mode (`without sharing`) can silently write fields the current user cannot see.

- **Scalability** — The 100-record limit on `Database.convertLead()` is a hard platform constraint. Any implementation that does not chunk to 100 will fail at scale. Batch Apex with a batch size of 100 is the canonical pattern for large-volume conversions.

- **Operational Excellence** — Custom field transfer logic that lives only in a service class is invisible to admins and future developers who expect conversion behavior to be consistent regardless of how conversion is triggered. Where possible, document in Setup field descriptions which fields are transferred programmatically rather than via the Setup field mapping.

## Architectural Tradeoffs

**Trigger vs. Service-Layer Field Transfer**

Putting post-conversion field mapping in an `after update` trigger on Lead covers all conversion paths (UI, API, Flow, Apex) but adds trigger complexity and requires careful guard logic to avoid misfiring on non-conversion updates. Putting it in the service method is simpler but only covers programmatic conversions. For orgs where users convert from the UI, the trigger approach is mandatory.

**allOrNone = true vs. false**

`Database.convertLead(conversions)` defaults to `allOrNone = true`, meaning a single failed lead rolls back the entire batch. This is safer for data integrity but can result in zero conversions when one lead has a bad status or a duplicate conflict. `allOrNone = false` allows partial success but requires iterating `LeadConvertResult` to log and handle individual failures. Choose `true` for transactional integrity requirements, `false` for best-effort bulk jobs.

**Opportunity Suppression**

Always evaluate whether `setDoNotCreateOpportunity(true)` is appropriate. Creating Opportunities on every conversion bloats the pipeline and creates noise for sales teams. Conversely, suppressing them always means qualified leads never get a pipeline record. Parameterize this setting rather than hardcoding it in the service.

## Anti-Patterns

1. **Hardcoded converted status label** — Using `setConvertedStatus('Converted')` as a string literal is fragile. The label may differ from the API name, and orgs with multiple converted statuses need different values for different flows. Always query `LeadStatus WHERE IsConverted = true` dynamically.

2. **Single-record-per-call conversion loop** — Calling `Database.convertLead()` once per lead in a for loop bypasses the spirit of the bulk API and exhausts DML statements rapidly. Always aggregate into a list and chunk to 100 per call.

3. **Post-conversion logic only in the service, not in a trigger** — Assuming all conversions are programmatic is an architectural assumption that breaks when admins convert from the UI or external systems call the conversion API. The trigger-based detection pattern (`IsConverted` flip in `after update`) is the only path-agnostic solution.

## Official Sources Used

- Apex Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_dev_guide.htm
- Apex Reference Guide — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_ref_guide.htm
- Apex Reference: Database.LeadConvert — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_methods_system_database_leadconvert.htm
- Apex Developer Guide: Converting Leads — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_dml_convertLead.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
