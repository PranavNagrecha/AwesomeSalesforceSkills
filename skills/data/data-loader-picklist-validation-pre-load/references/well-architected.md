# Well-Architected Notes — Data Loader Picklist Validation (Pre-Load)

This skill maps primarily to **Reliability** and **Operational Excellence** in the Salesforce Well-Architected framework. It also touches Security indirectly: rejecting non-conforming values at the gate keeps downstream automations from making decisions on data the UI does not show.

## Relevant Pillars

- **Reliability** — pre-load validation prevents partial-success bulk loads that corrupt the org state:
  - *Resilient* — rejecting invalid rows BEFORE the API job means the load either runs cleanly or does not run at all. The half-loaded state ("3,000 rows succeeded, 600 failed, business owner cannot tell what was loaded") is the failure mode that costs days to clean up. Pre-load validation eliminates it.
  - *Available* — Bulk API jobs consume daily API limits and platform parallelism. A run that blows up at the 600th batch wastes the limit AND blocks other consumers. Catching the 600 bad rows at the CSV stage costs zero API.
  - *Recoverable* — when a load does fail, the validator's report tells you exactly which rows to retry vs which to escalate. Without it, the error CSV from Bulk API gives terse reason codes that take an hour to map back to root cause.
- **Operational Excellence** — pre-load validation is observable, repeatable, and auditable by construction:
  - *Observable* — the validator emits a structured per-finding report (`line, column, value, record_type, severity, reason`) suitable for log aggregation. Compare runs over time and you can see whether picklist drift is improving.
  - *Manageable* — the picklist map JSON is the single artefact that captures "what the org expected at load time." Store it next to the CSV and you have a reproducible record of the load's preconditions.
  - *Repeatable* — every load uses the same script with different inputs. The runbook is one command, not a checklist of UI clicks. New team members run validations correctly on their first day.
  - *Compliant* — for regulated data loads (HIPAA, financial reporting), the validator's clean exit is the audit evidence that no out-of-policy values were inserted.

## Concrete reliability wins

| Without pre-load validation | With pre-load validation |
|---|---|
| Bulk API job fails 600/5000 rows mid-flight; partial state in production | Validator catches all 600 in 30 seconds before the load runs |
| Error CSV with cryptic `BAD_VALUE_FOR_RESTRICTED_PICKLIST`, 600 manual lookups | Structured report grouped by reason, one remediation per group |
| Hours spent matching errors to source rows; data team blocks on Salesforce admin | One picklist map regen + one CSV remap; load runs same day |
| Silent non-conforming values written to unrestricted picklists, surface weeks later | Non-conforming rows flagged as warnings before they land |

## Architectural Tradeoffs

- **Picklist map freshness.** The validator is only as accurate as the JSON map. A stale map (sandbox metadata, day-old export) will pass values the live org will reject, or fail values the live org would now accept. Mitigation: regenerate the map immediately before each load, not from a cached file.
- **Dependent picklist matrix cost.** Decoding the `validFor` byte string for every dependent value adds setup work to the picklist map generation. For orgs with many dependent picklists this is non-trivial. Mitigation: cache the decoded matrix in the JSON map; regenerate only when controlling/dependent metadata changes.
- **Validator vs platform behaviour drift.** Platform releases sometimes adjust picklist enforcement (e.g. tightening unrestricted picklists). The validator reflects today's behaviour, not future. Mitigation: tag the validator output with the Salesforce release version it was authored against; review on Spring/Summer/Winter release.
- **Stdlib-only constraint.** This skill's checker uses Python stdlib so it runs in any environment. That excludes richer libraries like `pandas`. Mitigation: stdlib `csv` is sufficient for CSVs up to ~1M rows; for larger loads, sample or stream.

## Anti-Patterns

1. **Loading first and reading the error CSV** — turns a deterministic problem into an interactive debugging session, consumes API limits, and risks partial state. Always validate before the load runs.
2. **Validating against a sandbox describe** — sandboxes drift from production. A clean validator run against a stale sandbox is a false positive. The map must come from the *target* org.
3. **Ignoring dependent-picklist rules "because validation rules will catch it"** — validation rules do not run on Bulk API by default unless `assignmentRuleHeader` and other settings are explicit, and even then dependent-picklist enforcement is at the platform level, not user-defined VRs.
4. **Treating the validator as optional for "small loads"** — picklist drift is independent of load size. A 50-row load can have the same picklist mismatch rate as a 50,000-row load. Run the validator regardless.

## Official Sources Used

- **Salesforce Help — Data Loader picklist behavior**: <https://help.salesforce.com/s/articleView?id=sf.data_loader.htm&type=5> — overall Data Loader behavior including picklist value handling.
- **Salesforce Help — Manage Picklists** (active, inactive, restricted, GVS): <https://help.salesforce.com/s/articleView?id=sf.fields_managing_picklists.htm&type=5>.
- **Salesforce Help — Define Dependent Picklists**: <https://help.salesforce.com/s/articleView?id=sf.fields_defining_dependent_picklists.htm&type=5>.
- **Apex Developer Guide — `Schema.PicklistEntry` and `getRecordTypeInfos`**: <https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_methods_system_picklistentry.htm> — the describe surface the picklist map is built from.
- **Object Reference — `RecordType` object and `DeveloperName` upsert key**: <https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_recordtype.htm>.
- **Bulk API 2.0 Developer Guide — Field requirements and picklist value handling**: <https://developer.salesforce.com/docs/atlas.en-us.api_asynch.meta/api_asynch/asynch_api_intro.htm>.
- **Salesforce Architects — Well-Architected Reliability pillar**: <https://architect.salesforce.com/well-architected/trusted/resilient> — frames the recoverability and resilience benefits cited above.
- **Salesforce Architects — Well-Architected Operational Excellence pillar**: <https://architect.salesforce.com/well-architected/well-architected-framework/operational-excellence> — frames the observability and manageability benefits cited above.
