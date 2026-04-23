# Well-Architected Notes — Apex Custom Settings Hierarchy

## Relevant Pillars

### Reliability

Hierarchy Custom Settings fail silently. `getInstance()` always returns a non-null record, so missing configuration doesn't throw — it produces wrong behavior. Reliable code defaults explicitly when a field is null and tests every tier of the hierarchy.

Tag findings as Reliability when:
- null-checks target the record instead of the field
- no code default exists for missing field values
- tests only exercise the org-default tier

### Performance

Custom Settings reads via `getInstance()` are cached per transaction and consume no SOQL. Writes are real DML and count against the 150 DML limit. Performance pain appears when Custom Settings are (a) read via SOQL instead of the accessor, (b) written row-by-row in loops, or (c) read inside long-running async code that loses the transaction cache between `execute()` calls.

Tag findings as Performance when:
- SOQL replaces `getInstance()` without a necessity argument
- DML in loops writes multiple setting rows
- Settings are read every iteration of a batch `execute`

### Operational Excellence

Custom Setting data does not move with metadata deploys. Without a documented seeding process, every sandbox refresh or org-cloning event introduces environment drift. For deploy-time configuration, Custom Metadata Types are the architecturally correct choice.

Tag findings as OpEx when:
- configuration is stored in Custom Settings but never changes in production (should be CMDT)
- no seeding procedure is documented
- audit trail is required but Field History Tracking is not enabled

## Architectural Tradeoffs

- **Custom Settings vs Custom Metadata:** Use Custom Metadata when the configuration is deploy-time-only, needs to be packageable, or must be auditable through source. Use Hierarchy Custom Settings only when admins need to change a value in Setup UI at runtime, per-user or per-profile.
- **Custom Settings vs Platform Cache:** Platform Cache (`Cache.Org`, `Cache.Session`) is for compute results, not config — it has TTL and can evict. Custom Settings are durable but not a cache.
- **Hierarchy vs List Custom Settings:** List Custom Settings predate CMDT and are legacy — no reason to create new List Custom Settings; migrate to CMDT for new lookup-table style data.

## Anti-Patterns

1. **Custom Settings storing deployable config** — endpoint URLs, retry counts, or anything static per environment belongs in Custom Metadata. Custom Setting data requires manual seeding and drifts.
2. **Record null-check on Hierarchy accessor** — `getInstance()` never returns `null`; the pattern never fires and masks missing config.
3. **DML in a loop over user/profile Ids** — burns governor limits and fragments the DML log. Always batch-upsert by `SetupOwnerId`.

## Official Sources Used

- Apex Developer Guide — Custom Settings: https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_customsettings.htm
- Apex Reference — Custom Setting Methods: https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_methods_system_customsettings.htm
- Custom Metadata Types Implementation Guide: https://developer.salesforce.com/docs/atlas.en-us.custommetadatatypes.meta/custommetadatatypes/custom_metadata_types_overview.htm
- Salesforce Help — Custom Setting Types: https://help.salesforce.com/s/articleView?id=sf.cs_types.htm
- Salesforce Well-Architected — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
