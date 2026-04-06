# Well-Architected Notes — Opportunity Management

## Relevant Pillars

- **Operational Excellence** — The stage and sales process configuration chain directly determines whether the sales team can operate efficiently: correct forecast rollups, appropriate stage guidance, and enforced data quality through validation rules. Poorly designed processes create noise in forecasting and increase admin burden when stages need revision.
- **Security** — Opportunity Teams and Splits introduce team-member-level record access. Adding a user to an Opportunity Team grants them at minimum read access to the record (configurable up to edit). This must align with the org's sharing model. Ensure sales process configuration does not inadvertently expose sensitive deal data through team roles.
- **Reliability** — Silent data corruption from deleted Stage values is a reliability risk. Deactivation rather than deletion, combined with pre-deletion record audits, prevents forecast gaps and broken validation rules from appearing in production.
- **Scalability** — The limit on custom forecast types (4 by default, 7 with Support) constrains how many split types and business motions can have dedicated forecast visibility. Design forecast type allocation early, especially in multi-division orgs.

## Architectural Tradeoffs

**Single Process vs. Per-Motion Processes:** A single catch-all Sales Process is simpler to maintain but forces all record types to expose the full stage list. Per-motion processes keep stages clean and forecast rollups accurate, at the cost of more record types and more Path configurations to maintain.

**Splits vs. Multiple Owners:** Some orgs use workarounds like custom lookup fields or shadow opportunities to represent split credit without enabling Splits. This avoids the permanent enablement risk but introduces custom logic debt and lacks native forecast integration. Native Splits are the correct long-term approach when the business model requires shared credit.

**Path vs. Validation Rules for Enforcement:** Path and validation rules are not mutually exclusive — they serve different purposes. Path guides; validation rules enforce. Choosing only Path because it is "easier to configure" means enforcement is absent. Always evaluate whether the business requires enforcement (validation rule) or recommendation (Path).

## Anti-Patterns

1. **Using a single Sales Process for all record types** — Forces every record type to expose all stages, including irrelevant ones for that motion. Reps skip stages, forecast rollups become unreliable, and reports cannot filter by meaningful pipeline stages per motion. Create separate processes per distinct business motion.

2. **Treating Path as a stage-progression enforcement mechanism** — Path is visual only. Relying on Path alone to enforce required field completion or stage sequencing means enforcement does not exist. Any rep can bypass Path guidance by saving the record at any stage. Validation rules are the enforcement layer.

3. **Enabling Opportunity Splits in production without a permanent business commitment** — Because splits cannot be disabled once data exists, enabling them speculatively or for a short pilot permanently changes the org's data model. Require formal sign-off and pilot in a full sandbox before enabling in production.

4. **Deleting deprecated Stage values without reassigning records** — Picklist value deletion is not blocked by records in use. Silent blank-field corruption breaks forecast rollups and downstream validation rules. Always audit record counts and reassign before deletion; prefer deactivation.

## Official Sources Used

- Object Reference — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_concepts.htm
- Metadata API Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_intro.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Opportunity Teams and Splits Help — https://help.salesforce.com/s/articleView?id=sf.teamselling.htm
- Guidelines for Opportunity Splits — https://help.salesforce.com/s/articleView?id=sf.oppty_splits_guidelines.htm
- Pipeline Forecasting Implementation Guide — https://help.salesforce.com/s/articleView?id=sf.forecasts3_implementing.htm
