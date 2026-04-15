---
name: analytics-data-governance
description: "Use this skill when implementing or auditing data governance controls for CRM Analytics (Tableau CRM / Wave Analytics): dataset lineage tracing, access audit logging, data classification handling, retention management, and compliance readiness. Trigger keywords: CRM Analytics audit, dataset lineage, event monitoring analytics, access logging Wave, data classification propagation, analytics retention, GDPR analytics datasets, analytics compliance. NOT for general Salesforce data governance (use data-quality-and-governance), NOT for row-level security predicates or app sharing (use analytics-security-architecture), NOT for user licensing and sharing roles (use analytics-permission-and-sharing)."
category: data
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
  - Operational Excellence
triggers:
  - "How do I audit who accessed CRM Analytics datasets and when?"
  - "We need to trace which dataflow or recipe produced a specific CRM Analytics dataset for lineage reporting"
  - "Does Salesforce Data Classification metadata propagate into CRM Analytics datasets automatically?"
  - "How do I set up Event Monitoring to log CRM Analytics dashboard access for compliance?"
  - "What is the correct way to delete or purge a CRM Analytics dataset for GDPR erasure?"
tags:
  - crm-analytics
  - data-governance
  - event-monitoring
  - audit-logging
  - dataset-lineage
  - data-classification
  - compliance
  - retention
inputs:
  - "CRM Analytics org (Tableau CRM / Wave Analytics) — enabled and accessible"
  - "Event Monitoring add-on license status (required for access audit logs)"
  - "List of datasets requiring compliance treatment (PII, HIPAA, GDPR scope)"
  - "Existing dataflow / recipe names and IDs for lineage tracing"
  - "Salesforce metadata project directory (for checker script)"
outputs:
  - "Dataset lineage map: which dataflows/recipes produce each dataset, traced via REST API"
  - "Event log query plan: event types to enable, retention window, export cadence"
  - "Data classification gap analysis: source-object classifications vs. dataset coverage"
  - "Retention management runbook: manual deletion steps or scheduled recipe for data aging"
  - "Compliance readiness checklist for analytics-specific PII/sensitive data handling"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-15
---

# Analytics Data Governance

This skill activates when a practitioner needs to implement or audit data governance controls specifically within CRM Analytics (also called Tableau CRM or Wave Analytics). It covers how to trace dataset lineage through the REST API, configure access audit logging via Event Monitoring, handle the propagation gap between Salesforce field-level data classification and CRM Analytics datasets, manage dataset retention in the absence of native TTL controls, and satisfy compliance requirements for analytics-stored PII or sensitive data.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Event Monitoring license status** — access audit logging for CRM Analytics requires the Event Monitoring add-on. Without it, the `WaveChange` and `WaveInteraction` event types are not available. Confirm license before designing an audit architecture.
- **Dataset origin** — know whether datasets are produced by Dataflows (`.wdf` JSON), Recipes (Data Prep), or External Data API uploads. Lineage tracing differs by mechanism.
- **Field-level Data Classification status on source objects** — CRM Analytics does NOT inherit Salesforce field-level data classification metadata. Any fields tagged as Restricted or Confidential on source objects carry no tag inside a CRM Analytics dataset after ingestion.
- **Compliance scope** — clarify whether GDPR right-to-erasure, HIPAA minimum-necessary, or internal data classification policy is driving the requirement. Each has different implications for dataset retention and access controls.
- **Salesforce org Edition and release** — Event Log Objects (real-time queryable via SOQL, 15-minute post-event latency) require Summer '24+ and are not available in all editions. Hourly CSV file delivery is the older and more broadly available mechanism.

---

## Core Concepts

### 1. Dataset Lineage Is API-Derived, Not UI-Native

CRM Analytics has no native visual lineage graph as of Spring '26. To determine which dataflow or recipe produced a given dataset, query the CRM Analytics REST API:

- **Dataflows:** `GET /services/data/vXX.X/wave/dataflows` returns all dataflow definitions. Each dataflow's JSON body (the `.wdf` schema) contains node definitions with `parameters.dataset.name` fields naming the output datasets.
- **Recipes:** `GET /services/data/vXX.X/wave/recipes` returns all recipe metadata including `outputDatasets` arrays naming produced datasets.
- **Data Manager UI:** shows input/output connections per recipe/dataflow run, but does not provide a cross-recipe lineage graph or dataset-to-source tracing.

To build a dataset-to-producer map, iterate all dataflows and recipes via the REST API, parse output dataset names, and cross-reference against dataset IDs returned by `GET /services/data/vXX.X/wave/datasets`.

### 2. Access Audit Logging Requires Event Monitoring (License-Gated)

CRM Analytics access events are captured as Salesforce Event Monitoring log entries. Key event types:

- **`WaveChange`** — captures dataset creates, deletes, permission changes, and dataflow modifications.
- **`WaveInteraction`** — captures dashboard views, lens queries, and dataset reads by user.
- **`WavePerformance`** — captures query execution timing; useful for performance-adjacent access audits.

Event log data is available in two forms:
- **Hourly CSV files** — available via `EventLogFile` sObject (`SELECT Id, EventType, LogDate FROM EventLogFile WHERE EventType = 'WaveChange'`). Files are generated hourly and retained for up to 1 year (retention period is configurable under the Event Monitoring add-on).
- **Event Log Objects (ELO)** — available Summer '24+. Real-time queryable SOQL objects (`WaveChangeLog`, `WaveInteractionLog`) with approximately 15-minute post-event latency. Retained for 6 months. No file download required.

Without the Event Monitoring add-on, neither mechanism is available. There is no free audit trail for dataset-level access in CRM Analytics.

### 3. Salesforce Data Classification Does Not Propagate Into Datasets

Salesforce provides field-level data classification metadata (Data Sensitivity Level, Data Category, Compliance Categorization) on standard and custom fields via the Field metadata type. These tags exist at the CRM object layer.

When data is extracted from a Salesforce object and ingested into a CRM Analytics dataset — whether via a Dataflow, Recipe, or the External Data API — the resulting dataset columns carry no inherited classification metadata. CRM Analytics has no native dataset-column tagging system that maps to Salesforce Data Classification values.

Practical consequence: a field tagged `Restricted` on the source `Contact` object becomes an untagged column in the CRM Analytics dataset. Compliance-driven access controls (row-level predicates, column exclusion) must be re-applied manually at the dataset layer.

### 4. No Native Dataset-Level Retention Controls (No TTL / Purge)

CRM Analytics has no built-in per-dataset TTL or automatic purge mechanism as of Spring '26. Dataset retention must be managed operationally:

- **Manual deletion:** use `DELETE /services/data/vXX.X/wave/datasets/{id}` via the REST API or use the Data Manager UI.
- **Scheduled recipe for data aging:** build a Recipe that filters incoming rows by date before writing back to the dataset, effectively aging out records on each scheduled run.
- **Version management:** CRM Analytics retains dataset versions. Deleting the current dataset version does not automatically purge earlier versions. All versions must be explicitly deleted if a right-to-erasure applies.

---

## Common Patterns

### Pattern: REST API Dataset Lineage Audit Script

**When to use:** A compliance review requires documenting which pipeline (dataflow or recipe) produced each dataset in the org, or a dataset contains PII and its source needs to be traced for a DPIA (Data Protection Impact Assessment).

**How it works:**

```python
# stdlib only — authenticate separately and pass access_token + instance_url
import urllib.request, json

def get_lineage_map(instance_url, access_token, api_version="v63.0"):
    headers = {"Authorization": f"Bearer {access_token}",
               "Content-Type": "application/json"}
    lineage = {}

    # 1. Collect all datasets
    url = f"{instance_url}/services/data/{api_version}/wave/datasets"
    with urllib.request.urlopen(
        urllib.request.Request(url, headers=headers)
    ) as resp:
        datasets = json.load(resp).get("datasets", [])
    dataset_by_name = {d["name"]: d["id"] for d in datasets}

    # 2. Trace recipes
    url = f"{instance_url}/services/data/{api_version}/wave/recipes"
    with urllib.request.urlopen(
        urllib.request.Request(url, headers=headers)
    ) as resp:
        recipes = json.load(resp).get("recipes", [])
    for recipe in recipes:
        for ds in recipe.get("outputDatasets", []):
            lineage.setdefault(ds["name"], []).append(
                {"type": "recipe", "id": recipe["id"], "label": recipe.get("label")}
            )

    # 3. Trace dataflows (parse wdf JSON)
    url = f"{instance_url}/services/data/{api_version}/wave/dataflows"
    with urllib.request.urlopen(
        urllib.request.Request(url, headers=headers)
    ) as resp:
        dataflows = json.load(resp).get("dataflows", [])
    for df in dataflows:
        df_url = f"{instance_url}/services/data/{api_version}/wave/dataflows/{df['id']}"
        with urllib.request.urlopen(
            urllib.request.Request(df_url, headers=headers)
        ) as resp:
            df_detail = json.load(resp)
        for node in df_detail.get("definition", {}).get("nodes", {}).values():
            if node.get("action") == "sfdcDigest" or "dataset" in node.get("parameters", {}):
                ds_name = node.get("parameters", {}).get("dataset", {}).get("name")
                if ds_name:
                    lineage.setdefault(ds_name, []).append(
                        {"type": "dataflow", "id": df["id"], "label": df.get("label")}
                    )
    return lineage
```

**Why not the alternative:** The Data Manager UI shows individual recipe/dataflow runs but does not aggregate across all pipelines. Manual UI inspection does not scale to orgs with 50+ recipes.

### Pattern: Event Log Query for Dataset Access Audit

**When to use:** You need to produce an access audit report showing which users accessed which CRM Analytics datasets over a time period (for GDPR, SOC 2, or internal audit).

**How it works:**

Using Event Log Objects (Summer '24+, ELO available):
```soql
SELECT UserId, SessionKey, QueriedEntities, Timestamp, RequestIdentifier
FROM WaveInteractionLog
WHERE Timestamp >= 2026-01-01T00:00:00Z
  AND Timestamp < 2026-04-01T00:00:00Z
ORDER BY Timestamp DESC
```

Using older hourly CSV EventLogFile approach:
```soql
SELECT Id, EventType, LogDate, LogFileLength
FROM EventLogFile
WHERE EventType IN ('WaveChange', 'WaveInteraction')
  AND LogDate >= 2026-01-01T00:00:00Z
ORDER BY LogDate DESC
```
Download each CSV via `Id`-based REST endpoint, parse `USER_ID`, `DATASET_ID`, and `TIMESTAMP` columns.

**Why not the alternative:** Setup Audit Trail captures org configuration changes, not CRM Analytics dataset access. It is not a substitute for Event Monitoring.

### Pattern: Scheduled Recipe for Dataset Data Aging

**When to use:** A dataset contains time-sensitive or PII data that must not be retained beyond a defined window (e.g., 90-day rolling window for activity data).

**How it works:**
1. In the Recipe, add a `Filter` node as the final step before the output node.
2. Filter condition: `date_column >= TODAY() - 90` (use the Recipe date function appropriate to the column type).
3. The output node overwrites the existing dataset on each scheduled run.
4. Schedule the recipe to run daily via the Schedules API or Data Manager UI.
5. Verify that old dataset versions are also purged: use `GET /wave/datasets/{id}/versions` and `DELETE` each version older than the retention window.

**Why not the alternative:** There is no CRM Analytics equivalent of a database TTL index or a Salesforce big object archival job. Without an active recipe or manual deletion, data persists indefinitely.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Need to know which recipe/dataflow produced a dataset | Query `/wave/recipes` and `/wave/dataflows` REST endpoints; parse `outputDatasets` / node definitions | No native UI lineage graph exists |
| Need dataset access audit logs | Enable Event Monitoring add-on; query `WaveInteractionLog` ELO (Summer '24+) or `EventLogFile WHERE EventType='WaveInteraction'` | Standard Salesforce audit trail does not capture analytics access events |
| Field tagged "Restricted" on Contact object — need same treatment in CRM Analytics | Re-apply access controls at dataset layer: exclude column in recipe, or apply row-level security predicate | Field-level Data Classification does not propagate from CRM objects into datasets |
| Need to purge PII from a dataset (GDPR right-to-erasure) | Delete dataset via REST API; also delete all dataset versions explicitly | Dataset deletion does not cascade to versions; stale versions persist |
| Need rolling 90-day data window in a dataset | Build a Recipe filter node on date column; schedule daily; verify version cleanup | No native TTL or purge schedule on CRM Analytics datasets |
| Need to classify dataset columns for governance catalog | Document manually in a governance register; no native column tagging system in CRM Analytics | CRM Analytics has no in-platform dataset-column metadata catalog as of Spring '26 |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner implementing analytics data governance:

1. **Confirm licenses and feature availability** — verify Event Monitoring add-on is active (`SELECT Id, Name FROM PermissionSet WHERE Name LIKE '%EventMonitoring%'` or check Setup > Company Information > Feature Licenses). Confirm org release is Summer '24+ if Event Log Objects are required. Document which audit mechanisms are available before designing the governance architecture.

2. **Build dataset lineage map** — run the REST API lineage script against the org (`GET /wave/recipes`, `GET /wave/dataflows`). Produce a dataset-to-producer table listing each dataset's name, ID, and the recipes/dataflows that write to it. Flag any datasets with unclear or missing lineage (orphaned datasets from deleted recipes are a common finding).

3. **Classify datasets by data sensitivity** — for each dataset, identify which source object fields contributed to it and what Data Classification those fields carry. Document the classification gap explicitly: no inherited tags exist in CRM Analytics. Assign governance tier (e.g., Public / Internal / Confidential / Restricted) manually in a governance register.

4. **Configure access audit logging** — enable the `WaveChange` and `WaveInteraction` event types if not already active under Event Monitoring settings. Define the SOQL query or CSV-download pipeline to extract logs on the required cadence (daily for compliance, weekly for operational review). If external SIEM integration is required, set up log export via MuleSoft, custom Apex scheduled job, or a third-party connector.

5. **Implement retention controls** — for each dataset in scope: determine the required retention window, build or verify a scheduled Recipe filter that enforces the rolling window, and add an API-based version cleanup step. Document the schedule and responsible team member in the governance register.

6. **Validate and document the governance posture** — run the checker script (`scripts/check_analytics_data_governance.py --manifest-dir .`) to surface missing event log configuration or ungoverned dataset indicators in metadata. Complete the compliance readiness checklist. Review with the data governance or privacy team before marking complete.

---

## Review Checklist

Run through these before marking analytics data governance work complete:

- [ ] Event Monitoring add-on confirmed active (or absence explicitly documented with compensating controls)
- [ ] Dataset lineage map produced — every production dataset has a documented producer (recipe, dataflow, or external upload)
- [ ] Data classification gap documented — source-object field classifications are not assumed to propagate; re-applied at dataset layer
- [ ] Retention policy implemented — scheduled recipe filter or documented manual deletion cadence for each in-scope dataset
- [ ] Dataset versions explicitly addressed in any right-to-erasure or purge process
- [ ] Access audit log query validated — at least one successful `WaveInteraction` or `WaveChange` log retrieval confirmed
- [ ] Governance register updated with dataset inventory, classification tier, retention window, and owner

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Deleting a dataset does not delete its versions** — when you delete a dataset via the UI or REST API, older dataset versions remain stored and accessible via `/wave/datasets/{id}/versions`. A GDPR right-to-erasure satisfied by dataset deletion alone is incomplete. Always enumerate and delete all versions explicitly.

2. **Event Log Object availability is edition- and release-gated** — `WaveChangeLog` and `WaveInteractionLog` ELOs require Summer '24+ AND the Event Monitoring add-on. In orgs on older releases, only hourly CSV `EventLogFile` delivery is available. LLM assistants frequently recommend ELO SOQL without checking the release gating.

3. **WaveInteraction logs record dashboard views, not field-level reads** — the log captures which dashboard or lens a user opened and which dataset it queried, but does not enumerate which dataset columns or row values were returned. Column-level access auditing is not natively supported in CRM Analytics audit logs.

4. **Salesforce Data Classification field metadata is invisible inside CRM Analytics** — there is no API or UI in CRM Analytics that exposes Salesforce field Data Classification values for dataset columns. Practitioners who rely on CRM Analytics's dataset column list to identify sensitive data will miss all classification-tagged source fields.

5. **Scheduled recipes do not auto-purge bypassed rows — they overwrite the dataset** — a recipe filter that excludes rows older than 90 days rewrites the dataset on each run, but if the recipe fails or is paused, stale data accumulates. Recipe failure does not trigger a fallback delete. Monitor recipe run success explicitly, and treat a failed run as a retention SLA breach.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Dataset Lineage Map | Table of dataset name → producing recipe/dataflow IDs; produced by the REST API lineage script |
| Data Classification Gap Analysis | Per-dataset documentation of which source-object fields carry Data Classification tags and how they are re-classified at the dataset layer |
| Event Log Query Plan | SOQL queries or CSV export pipeline definition for `WaveChange` and `WaveInteraction` event types |
| Retention Runbook | Per-dataset retention window, scheduled recipe filter logic, version cleanup steps, and responsible owner |
| Governance Register | Consolidated record of dataset inventory, classification tier, retention window, access controls, and audit status |
| Compliance Readiness Checklist | Completed checklist (from Review Checklist above) signed off by data governance or privacy team |

---

## Related Skills

- analytics-security-architecture — for row-level security predicates, dataset sharing rules, and app-level access controls (not audit logging)
- analytics-permission-and-sharing — for CRM Analytics licensing, sharing roles, and permission set assignment (not compliance auditing)
- data-quality-and-governance — for general Salesforce org data governance, field-level validation, and deduplication (not analytics-specific)
- event-monitoring — for the full Event Monitoring add-on setup, event type catalog, log file download, and real-time threat detection (not analytics-specific)
- analytics-dataset-optimization — for dataset sizing, incremental load, and performance tuning (not governance)
