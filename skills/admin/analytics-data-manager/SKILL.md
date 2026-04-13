---
name: analytics-data-manager
description: "Use this skill when configuring Data Manager in CRM Analytics: enabling objects for sync, scheduling data sync runs, setting up remote connections to external databases, monitoring sync status and error logs, or troubleshooting connected object issues. Trigger keywords: data sync, connected objects, Data Manager, sync schedule, remote connection, Snowflake connector, sync error, incremental sync, CRM Analytics data pipeline. NOT for dataflow or recipe authoring, dataset row-level security, or dashboard/lens design — those belong to the analytics-dataset-management or analytics-dashboard-design skills."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Performance
  - Operational Excellence
triggers:
  - "my CRM Analytics data sync is failing and I need to find out why"
  - "how do I connect Snowflake or BigQuery as an external data source in CRM Analytics"
  - "connected objects are showing in Data Manager but I cannot use them in a dashboard"
  - "incremental sync is not picking up recent changes to my Salesforce records"
  - "how many objects can I enable for sync in CRM Analytics and what are the limits"
  - "data sync ran but my dataset still shows old data — what should I check"
tags:
  - crm-analytics
  - data-manager
  - data-sync
  - connected-objects
  - remote-connections
  - incremental-sync
  - salesforce-data-pipeline
inputs:
  - "Names of Salesforce objects or external tables to be synced"
  - "License type (CRM Analytics Plus, Revenue Intelligence, etc.)"
  - "External database type if applicable (Snowflake, BigQuery, Redshift, Amazon S3)"
  - "Sync schedule requirements (frequency, business hours constraints)"
  - "Current sync error messages or status from Data Manager monitoring"
outputs:
  - "Data Manager sync configuration plan (objects, schedule, mode)"
  - "Remote connection setup instructions for external databases"
  - "Connected object inventory with downstream recipe/dataflow dependencies mapped"
  - "Sync monitoring and error remediation guidance"
  - "Documented hard limits and capacity constraints for the org"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-13
---

# Analytics Data Manager

This skill activates when a practitioner needs to configure, troubleshoot, or operate the Data Manager layer of CRM Analytics — the upstream sync and connection tier that replicates Salesforce objects and external data into connected objects before they can be processed by recipes or dataflows. Data Manager is distinct from the recipe/dataflow/dataset layer: it owns the pipeline from source to staging; it does not own transformation or visualization.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm whether the request is about the sync/connection layer (Data Manager) or the transformation/dataset layer (dataflows, recipes). These are separate tools with separate skill coverage.
- Identify which license the org has — CRM Analytics Plus, Revenue Intelligence, Health Cloud Analytics, etc. License determines which connectors are available and what sync limits apply.
- Know the hard platform limits before recommending any configuration: max 100 objects enabled for sync, max 3 concurrent sync runs at any time.
- Determine whether the failing or targeted objects use `LastModifiedDate` — this is the sole field incremental sync relies on. Any field whose value changes due to related-object roll-ups but whose `LastModifiedDate` does not update will drift silently.

---

## Core Concepts

### Connected Objects Are Staging-Layer Replicas, Not Datasets

When an admin enables a Salesforce object for sync in Data Manager, the platform replicates that object's records into an intermediate store called a **connected object**. Connected objects are internal staging copies — they do not count against dataset row limits, but they are not queryable via SAQL, cannot be referenced in dashboards or lenses, and cannot be used as direct inputs to dashboard widgets. Every connected object must be consumed by a recipe or dataflow that materializes it into an actual dataset before it can be visualized. This is the most common source of confusion: the object appears healthy in Data Manager, but nothing shows up in Analytics Studio because no downstream recipe has been run.

### Incremental Sync Relies Exclusively on LastModifiedDate

CRM Analytics incremental sync detects changed records by comparing `LastModifiedDate` on each Salesforce object against the last successful sync timestamp. This has a critical implication: if a field's value changes because a related object changed (for example, a roll-up summary field on Account driven by Opportunity changes), but the Account's own `LastModifiedDate` is not bumped by Salesforce, that Account record will not be included in the next incremental sync. The connected object will show the old value indefinitely until a full sync is forced. Formula fields that reference related objects are particularly vulnerable. There is no automatic detection of this drift — admins must proactively identify cross-object formula fields and schedule periodic full syncs to compensate.

### Remote Connections for External Databases Are Configured in Data Manager

Connections to external databases — Snowflake, Google BigQuery, Amazon Redshift, Amazon S3, and others — are set up under **Remote Connections** inside Data Manager, not inside dataflow JSON or recipe builder. A remote connection defines the credentials, host, database, and schema; once established it appears as a connection source that recipe or dataflow steps can reference. Misconfiguring a remote connection (wrong IP allowlist, expired credentials, incorrect schema name) causes sync failures that surface in Data Manager monitoring rather than in the recipe run log — a common source of confusion when practitioners look in the wrong place.

### Sync Scheduling and Concurrency Limits

Sync schedules are set per-connection, not per-object. Full syncs replicate all enabled rows from scratch; incremental syncs replicate only changed records since the last run. The platform enforces a maximum of **3 concurrent sync runs** across all connections simultaneously. Orgs with more than 3 connections that trigger at the same time will queue the excess runs. Monitoring the concurrent sync count is essential in orgs with many data sources or tight scheduling windows.

---

## Common Patterns

### Enabling a Salesforce Object for Sync and Materializing It as a Dataset

**When to use:** A new Salesforce object needs to be available in CRM Analytics dashboards for the first time, or an existing object that was not previously synced must be added.

**How it works:**
1. In Analytics Studio, navigate to **Data Manager > Connect** tab.
2. Locate the Salesforce Local connection (always present) and click **Edit Connection**.
3. Find the target object in the object list. Enable it for sync by toggling it on.
4. Set the sync mode: **Full** for first-time sync or objects without reliable `LastModifiedDate`; **Incremental** for standard ongoing sync on objects where `LastModifiedDate` is maintained.
5. Save and run a sync manually to validate. Check the **Monitor** tab to confirm the object completes successfully with the expected row count.
6. In **Recipe Builder** or a **Dataflow**, add an input node that reads the now-available connected object.
7. Run the recipe/dataflow to produce a dataset. Only at this point is the data accessible in dashboards.

**Why not the alternative:** Skipping step 6 and expecting the connected object to be directly usable in a dashboard is the most common mistake. Connected objects are staging replicas; they require materialization.

### Configuring a Remote Connection to Snowflake

**When to use:** Analytics data needs to pull from an external Snowflake warehouse rather than (or in addition to) Salesforce object data.

**How it works:**
1. In Data Manager, navigate to **Connect > Remote Connections** and click **New Remote Connection**.
2. Select **Snowflake** as the connector type and supply account identifier, warehouse, database, schema, username, and authentication credentials (password or key pair).
3. Add the Salesforce CRM Analytics IP ranges to the Snowflake network policy allowlist, or the connection test will fail.
4. After saving, click **Test Connection** to confirm connectivity before enabling any objects.
5. Enable the target Snowflake tables for sync exactly as Salesforce objects are enabled — they appear alongside local objects once the connection is active.
6. Monitor the first full sync in the **Monitor** tab before scheduling incremental runs.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Object has never been synced before | Full sync on first run, then switch to incremental | Incremental cannot establish a baseline; first run must be full |
| Object has cross-object formula fields or roll-up summaries | Periodic full sync (weekly or daily) in addition to incremental | `LastModifiedDate` is not bumped by related-object changes, so incremental misses these |
| More than 97 objects already enabled | Audit and disable unused objects before enabling new ones | Hard limit is 100 objects enabled for sync org-wide |
| External database (Snowflake, BigQuery) needed | Create Remote Connection in Data Manager, then enable tables | Remote connections are a Data Manager construct; dataflow JSON cannot define them |
| Dashboard shows stale data despite recent Salesforce changes | Check Monitor tab for sync errors first, then check if recipe/dataflow was re-run | Two-layer problem: sync must succeed AND downstream recipe must materialize the dataset |
| 3 syncs running concurrently and a 4th is queued | Stagger sync schedules to avoid concurrent limit | Platform enforces max 3 concurrent syncs; excess runs queue and delay data freshness |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Clarify the layer** — Confirm the request is about Data Manager (sync configuration, connected objects, remote connections) and not about recipes, dataflows, datasets, or dashboards. If it is about the transformation layer, route to the `analytics-dataset-management` skill.
2. **Audit current capacity** — In Data Manager > Connect, count objects currently enabled for sync. If the count is at or near 100, identify candidates for disabling before enabling new objects. Check the Monitor tab for any currently running syncs before adding to the schedule.
3. **Configure the connection and enable objects** — For Salesforce objects, use the Local connection. For external databases, create or update a Remote Connection first. Enable only the fields and objects actually needed to minimize sync volume.
4. **Set sync mode deliberately** — Choose Full for first-time sync or any object with cross-object formula fields. Choose Incremental for standard ongoing sync. Document the choice and its reason.
5. **Run and validate via Monitor** — Trigger a manual sync and watch the Monitor tab. Confirm row counts match expectations. Check for field-level errors (field not found, type mismatch) that succeed at the object level but silently drop fields.
6. **Confirm downstream materialization** — After sync completes, verify that the recipe or dataflow consuming the connected object has been re-run (or is scheduled to run) to produce an updated dataset. A successful sync that is not followed by a recipe run produces no change in dashboards.
7. **Document schedule and known drift risks** — Record which objects use incremental sync, which objects have cross-object formula fields requiring periodic full syncs, and what the stagger pattern is to stay within the 3-concurrent-sync limit.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Total objects enabled for sync is below 100 (hard platform limit)
- [ ] No more than 3 syncs are scheduled to run at the same time
- [ ] Objects with cross-object formula fields or roll-up summaries have full sync scheduled periodically
- [ ] Remote connection tested successfully before tables were enabled for sync
- [ ] Monitor tab shows successful completion with expected row counts after sync
- [ ] Connected objects are consumed by a recipe or dataflow — none are referenced directly in dashboard queries or lenses
- [ ] Sync schedule documented with rationale for full vs. incremental per object

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Connected objects are invisible to SAQL and dashboard lenses** — A connected object appearing healthy in Data Manager does not mean data is available for analytics. It must be materialized into a dataset by a recipe or dataflow. Dashboards and lenses can only reference datasets, not connected objects. Practitioners who see a green sync status and then look for the object in lens builder will find nothing.

2. **Incremental sync silently misses cross-object formula field updates** — If an Account has a formula field that sums child Opportunity amounts, and an Opportunity is closed, the Account's `LastModifiedDate` is not updated — only the Opportunity's is. Incremental sync on Account will not detect the change. The formula field will show stale data in the connected object until the next full sync. There is no warning or error; the sync succeeds with the wrong data.

3. **Remote connection credentials expire silently** — If a Snowflake or BigQuery credential (password, OAuth token, or key pair) expires, sync jobs for that connection will fail. Data Manager will log the failure in the Monitor tab, but it will not send an alert by default unless a monitoring notification has been explicitly configured. Stale credentials are a common cause of unexplained data freshness failures in production orgs.

4. **Field-level sync failures do not fail the object-level sync** — If a specific field on an object is unsyncable (field type changed, custom field deleted, field API name mismatch), the object sync completes as successful but that field is silently dropped from the connected object. Row counts look correct; only a field-level audit reveals the problem. Always verify critical field presence in connected object schema after enabling or after schema changes.

5. **Enabling too many fields increases sync duration** — Data Manager syncs all enabled fields on each enabled object. Enabling objects with hundreds of fields (such as Account or Opportunity with many custom fields) significantly increases sync time, which can push orgs against the concurrent sync limit. Best practice is to enable only fields that will be used in downstream recipes.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Data Manager sync configuration plan | Table of objects, sync mode (full/incremental), schedule, and downstream recipe dependencies |
| Remote connection setup instructions | Step-by-step guide for configuring Snowflake, BigQuery, Redshift, or S3 connections including IP allowlist requirements |
| Sync monitoring runbook | How to read the Monitor tab, interpret error codes, and escalate field-level vs. object-level failures |
| Capacity audit report | Count of enabled objects vs. limit, concurrent sync schedule review, recommendations for disabling unused objects |

---

## Related Skills

- `analytics-dataset-management` — For recipe and dataflow authoring, dataset configuration, and row-level security. Data Manager feeds this layer; this skill does not cover it.
- `analytics-dashboard-design` — For lens and dashboard creation. Dashboards consume datasets produced by the analytics-dataset-management layer.
- `crm-analytics-app-creation` — For end-to-end app scaffolding including initial Data Manager configuration, permission sets, and app templates.
