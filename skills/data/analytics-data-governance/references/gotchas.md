# Gotchas — Analytics Data Governance

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Dataset Deletion Does Not Delete Dataset Versions

**What happens:** When you delete a CRM Analytics dataset — via the Data Manager UI or via `DELETE /services/data/{version}/wave/datasets/{id}` — only the current dataset reference is removed. All historical dataset versions stored by CRM Analytics version history remain accessible via `/wave/datasets/{id}/versions` and continue to consume storage.

**When it occurs:** Any time a dataset is deleted for compliance purposes (GDPR erasure, data breach response, retention enforcement). Also occurs when a dataset is replaced by a renamed version: the old dataset ID's versions can linger.

**How to avoid:** Always enumerate dataset versions explicitly before or after deletion:
```
GET /services/data/{version}/wave/datasets/{id}/versions
```
Delete each version ID individually. Treat version cleanup as a required step in any dataset deletion runbook. Include version count in the compliance confirmation record.

---

## Gotcha 2: Event Log Objects (WaveInteractionLog) Are Release- and Edition-Gated

**What happens:** `WaveInteractionLog` and `WaveChangeLog` are Event Log Object (ELO) types introduced in Summer '24. When a practitioner runs a SOQL query against these objects on a pre-Summer '24 org, or on an org without the Event Monitoring add-on, the query returns `Object type 'WaveInteractionLog' is not supported` — it does not return an empty result set, it errors.

**When it occurs:** Any org not yet on Summer '24+ release, any org without the Event Monitoring Shield add-on license, and any Developer Edition or Trailhead Playground org (which do not include Event Monitoring by default).

**How to avoid:** Before designing an ELO-based audit pipeline, confirm two prerequisites independently: (1) `EventMonitoring` feature license is active in Setup > Company Information > Feature Licenses, and (2) org release is Summer '24 or later (check `SELECT SystemModstamp FROM Organization`). If either check fails, use the `EventLogFile` sObject with hourly CSV delivery instead. Document which mechanism is in use in the governance register.

---

## Gotcha 3: WaveInteraction Logs Record Dataset Queries, Not Column-Level Reads

**What happens:** Practitioners expecting column-level audit trails (i.e., "user X read the SSN column") discover that `WaveInteraction` / `WaveInteractionLog` records only that a user queried a dataset or viewed a dashboard. The log does not enumerate which columns were accessed, what filter values were used, or what rows were returned.

**When it occurs:** Compliance requirements that specify column-level or row-level access auditing (e.g., HIPAA minimum-necessary audit, PCI-DSS field-level access review). Architects assume CRM Analytics audit logs provide the same granularity as database query logging.

**How to avoid:** Explicitly document the audit granularity gap to compliance stakeholders before committing to an Event Monitoring-based audit architecture. For requirements that genuinely need column-level access logging, consider whether the data should remain in the CRM layer (where field-level auditing is possible via Field History Tracking or Einstein Data Detect), rather than being ingested into CRM Analytics.

---

## Gotcha 4: Salesforce Data Classification Is Invisible in CRM Analytics — Including via the API

**What happens:** A practitioner queries the CRM Analytics REST API for dataset column metadata (`GET /wave/datasets/{id}/xmd`) expecting to see Data Classification values (Sensitivity Level, Compliance Categorization) carried over from the source Salesforce object fields. The XMD (Extended Metadata) response contains column aliases, labels, field types, and formatting — but no Data Classification attributes. Classification tags from the source object do not appear anywhere in the dataset or XMD metadata.

**When it occurs:** Any dataset produced from Salesforce objects that have Data Classification configured. This affects all CRM Analytics ingestion paths: Dataflow, Recipe, and External Data API.

**How to avoid:** Maintain a separate governance register (a spreadsheet, a Confluence page, or a custom Salesforce object) that maps each dataset column to its source field and source field's classification. This register must be maintained manually and updated any time the recipe/dataflow schema changes. Do not assume any automated propagation will ever keep the register current without explicit tooling.

---

## Gotcha 5: Recipe Failure During a Scheduled Data Aging Run Does Not Roll Back or Alert by Default

**What happens:** A Recipe configured to enforce a rolling 90-day retention window fails mid-run (due to a data sync issue, API timeout, or recipe logic error). The dataset is not updated. The previous dataset version — which contained data outside the retention window — continues to be the current version. No automatic rollback occurs; the stale data remains live and queryable. Unless the team monitors recipe run status, the failure may go undetected for days or weeks.

**When it occurs:** Any org using a scheduled recipe as its sole retention enforcement mechanism. Recipe failures are more frequent during Salesforce maintenance windows, large data sync delays, and when upstream connected object schemas change.

**How to avoid:** Configure recipe run failure notifications via CRM Analytics admin alerts or via the REST API job status polling. Treat a failed data aging recipe run as a retention SLA breach requiring immediate remediation. Do not rely on recipe success as the only indicator that retention policy was enforced — also spot-check dataset row counts and max date values on a periodic basis. Consider adding a post-run assertion step (a lightweight Recipe that validates no rows exceed the retention boundary) as a compensating control.

---

## Gotcha 6: Dataflow-Produced Datasets and Recipe-Produced Datasets Have Different Lineage Representations

**What happens:** Practitioners building lineage tooling discover that Recipes expose `outputDatasets` as a top-level array in the REST API response, while Dataflows require parsing the internal `.wdf` JSON node graph to identify output dataset names. Using the same parsing logic for both produces incomplete lineage maps.

**When it occurs:** Any org that uses a mix of legacy Dataflows and newer Recipes (which is common in orgs that migrated incrementally from Dataflows to Recipes). The REST API endpoints (`/wave/dataflows` vs. `/wave/recipes`) are separate and return different schema shapes.

**How to avoid:** Handle both asset types explicitly in any lineage script. For recipes: iterate `recipe.outputDatasets[]`. For dataflows: `GET /wave/dataflows/{id}` and parse `definition.nodes` for nodes where `action` is `sfdcRegister` or where `parameters.dataset.name` is present. Test the lineage script against a sample org with both dataflows and recipes before relying on it for compliance documentation.
