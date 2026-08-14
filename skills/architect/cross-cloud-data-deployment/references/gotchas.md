# Gotchas — Cross-Cloud Data Deployment

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Change-event triggers batch at 2,000, and the batch is not the transaction

**What happens:** "The Apex trigger batch size for platform events and Change Data Capture events is 2,000." That is
an order of magnitude larger than the 200-record batch every Salesforce developer has internalised for record triggers,
and it applies to the subscriber side of every cross-cloud CDC flow.

The consequence is arithmetic. A subscriber trigger that issues one SOQL query per event is fine at 200 and dead at
2,000 — the 100-query synchronous governor is exhausted 5% of the way through the batch. Code review habits calibrated
to record triggers do not catch it, because the loop looks identical.

**When it occurs:** On the first bulk load into the publishing cloud. Steady-state traffic produces small batches and
the trigger looks healthy for months; a data migration or a mass update fills the batch and the subscriber fails
against a governor limit rather than a business error.

**How to avoid:** Bulkify the change-event subscriber against 2,000, not 200, and load-test it with a batch of that
size before go-live. Where the downstream work is expensive, have the subscriber enqueue rather than do the work
inline — a Queueable starts a fresh transaction with its own limits.

---

## Gotcha 2: A change event is an sObject with a header, and `changedFields` is version-gated

**What happens:** CDC events surface in Apex as change event sObjects with a `ChangeEventHeader` field. The event object
is named `<StandardObject>ChangeEvent` for standard objects (`AccountChangeEvent`, `CaseChangeEvent`) and
`<CustomObject>__ChangeEvent` for custom ones — getting that wrong is the first compile error. A subscriber trigger
reads the change type from the header rather than from the record:

```apex
trigger OnProductChangeEvent on Products__ChangeEvent (after insert) {
    for (Products__ChangeEvent event : Trigger.new) {
        EventBus.ChangeEventHeader header = event.ChangeEventHeader;
        String changeType = header.changeType;   // property, not a getter method
    }
}
```

The header's documented fields are `entityName`, `recordIds`, `changeType`, `changeOrigin`, `transactionKey`,
`sequenceNumber`, `commitTimestamp`, `commitUser`, `commitNumber`, `nulledFields`, `diffFields`, and `changedFields`.
Three of them decide most cross-cloud designs: `changedFields` — "A list of the fields that were changed in an update
operation. This field is empty for other operations, including record creation. This field includes the LastModifiedDate
and LastModifiedById system fields only if they have changed compared to before the update." (the Apex Reference adds
that the property "is available in Apex saved using API version 47.0 or later"); `transactionKey` — "A string that
uniquely identifies each Salesforce transaction. You can use this key to identify and group all changes that were made
in the same transaction"; and `recordIds` — "One or more record IDs for the changed records", so one event is not
necessarily one record.

**When it occurs:** When a subscriber tries to answer "did the field I care about change?" by comparing values. It
cannot — a change event carries the changed fields, not a before-image — so value comparison silently treats every
event as relevant and the downstream cloud gets updated on every unrelated edit. The second trap is assuming
`changedFields` is always populated: it is "empty for other operations, including record creation", so a filter written
against it will drop every CREATE unless the code branches on `changeType` first.

**How to avoid:** Filter on `changedFields` for updates and branch on `changeType` for everything else, and confirm the
trigger is saved at API version 47.0 or later before relying on the property at all. Design the cross-cloud contract
around "which fields did this event carry", not around reconstructing prior state. Where the receiving cloud needs a
consistent view of a multi-object commit, group by `transactionKey` rather than by arrival order.

---

## Gotcha 3: The connector is separate metadata from the objects it feeds

**What happens:** In the Metadata API, Data 360 (Data Cloud) splits into three independent deployables. The org-level
switch is `CustomerDataPlatformSettings` ("an org's Data 360 settings"). The ingestion side is its own type per
mechanism — `DataConnector` ("the white-labeled metadata configuration for an external connector in Data 360"),
`DataConnectorS3` ("the connection information specific to Amazon S3"), `DataConnectorIngestApi` ("the connection
information specific to Ingestion API"). The modelled objects travel as a data kit: `DataPackageKitDefinition` is "the
top-level data kit container definition", with `DataKitObjectTemplate`, `DataPackageKitObject`, and
`DataKitObjectDependency` ("the dependency between two data kit objects") inside it. Activation targets are a fourth
group — `ActivationPlatform` carries "platform name, delivery schedule, output format, and destination folder".

**When it occurs:** On the first sandbox-to-production promotion. The kit deploys, the objects appear, and nothing
ingests, because the connector metadata was never in the manifest and the org settings were never enabled in the target.

**How to avoid:** Order the promotion explicitly — settings, then connectors, then the kit that depends on them, then
activations — and verify ingestion with a single test record before declaring the environment ready. Search the guide
for `Data 360` rather than `Data Cloud`; the old product name returns nothing and reads like a coverage gap.

---

## Gotcha 4: Long-running cross-cloud calls contend for a fixed concurrency slot

**What happens:** "The following table lists the limits for various types of orgs for concurrent inbound requests
(calls) with a duration of 20 seconds or longer": 25 for Production orgs and Sandboxes, 5 for Developer Edition and
Trial orgs. "If the number of long running requests exceeds the limit, the API returns a `REQUEST_LIMIT_EXCEEDED`
exception code. Any new concurrent requests aren't processed until there are fewer requests than the allowed limit."
And crucially: "There isn't a limit on the number of concurrent requests shorter than 20 seconds."

**When it occurs:** When one cloud's sync job issues wide, slow queries against the hub org. Twenty-five slow callers
is not many when a middleware platform is retrying. The failure presents to every other integration in the org, not
just the offender — which is why it is usually diagnosed as "Salesforce is down".

**How to avoid:** Design cross-cloud reads to complete in under 20 seconds — narrow the query, page it, or move it to
Bulk API — because sub-20-second requests are not counted at all. That single threshold is the difference between an
uncounted call and a slot in a pool of 25. Separately, note the API timeout: "The timeout limit for REST and SOAP API
calls is 10 minutes", returning `REQUEST_RUNNING_TOO_LONG` (SOAP) or `QUERY_TIMEOUT` (REST), and "For calls to
Composite Resources in REST API, this timeout applies to the entire composite request, not to each subrequest" — a
composite that bundles cross-cloud work shares one budget.

## Official Sources Used

- Salesforce Developer Limits and Allocations Quick Reference (last updated 7 August 2026) — *Per-Transaction Apex
  Limits*: "The Apex trigger batch size for platform events and Change Data Capture events is 2,000."
  https://developer.salesforce.com/docs/atlas.en-us.salesforce_app_limits_cheatsheet.meta/salesforce_app_limits_cheatsheet/salesforce_app_limits_platform_apexgov.htm (verified 2026-08-14)
- Salesforce Developer Limits and Allocations Quick Reference — *Concurrent API Request Limits* and *API Timeout
  Limits*: the 25/5 concurrency figures for requests of 20 seconds or longer, `REQUEST_LIMIT_EXCEEDED`, the absence of
  a limit below 20 seconds, the 10-minute timeout, and the composite-request timeout scope.
  https://developer.salesforce.com/docs/atlas.en-us.salesforce_app_limits_cheatsheet.meta/salesforce_app_limits_cheatsheet/salesforce_app_limits_platform_api.htm (verified 2026-08-14)
- Apex Reference Guide — *ChangeEventHeader Class*: the header's properties (`changedfields`, `changetype`,
  `recordids`, `transactionkey` and the rest are properties, not getter methods) and "This property is available in
  Apex saved using API version 47.0 or later" for `changedFields`.
  https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_class_eventbus_ChangeEventHeader.htm (verified 2026-08-14)
- Change Data Capture Developer Guide — *ChangeEventHeader Fields*: the full field list and the descriptions of
  `changedFields`, `transactionKey`, `recordIds`, `changeType`, `commitNumber`, `nulledfields`, and `diffFields`.
  https://developer.salesforce.com/docs/atlas.en-us.change_data_capture.meta/change_data_capture/cdc_event_fields_header.htm (verified 2026-08-14)
- Change Data Capture Developer Guide — *Change Event Triggers*: standard-object change events are suffixed
  `ChangeEvent` (`AccountChangeEvent`); custom-object change events are suffixed `__ChangeEvent`.
  https://developer.salesforce.com/docs/atlas.en-us.change_data_capture.meta/change_data_capture/cdc_trigger_intro.htm (verified 2026-08-14)
- Metadata API Developer Guide, Version 67.0 — *Data 360 Metadata Types*: `CustomerDataPlatformSettings`,
  `DataConnector`, `DataConnectorS3`, `DataConnectorIngestApi`, `DataPackageKitDefinition`, `DataKitObjectTemplate`,
  `DataPackageKitObject`, `DataKitObjectDependency`, `ActivationPlatform`.
  https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_data_cloud_types.htm (verified 2026-08-14)
