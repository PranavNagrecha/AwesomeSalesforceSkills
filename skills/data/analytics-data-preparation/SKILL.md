---
name: analytics-data-preparation
description: "Use this skill when customizing CRM Analytics dataset field metadata via the XMD (Extended Metadata) REST API or augmenting CRM Analytics recipes with external non-Salesforce data: labeling fields, setting display formats, reclassifying measures vs dimensions, and applying org-level field annotations via main XMD PATCH. Trigger keywords: XMD field labels, CRM Analytics main XMD update, dataset field formatting wave, analytics external data augmentation, WaveXmd REST API. NOT for recipe node transformation logic, dataflow SOQL extraction, dataset row count management, or standard CRM data quality — those are covered by analytics-recipe-design, analytics-dataflow-development, and analytics-dataset-management."
category: data
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
triggers:
  - "how do I update field labels in a CRM Analytics dataset using the REST API"
  - "my WaveXmd PATCH request is wiping out existing field settings in CRM Analytics"
  - "how do I augment a CRM Analytics dataset with external CSV data not in Salesforce"
  - "what HTTP method should I use to update main XMD versus system XMD in CRM Analytics"
  - "can I use SOQL to read WaveXmd metadata from a CRM Analytics dataset"
  - "how do I back up the current XMD before making changes to a CRM Analytics dataset"
tags:
  - crm-analytics
  - xmd
  - dataset-metadata
  - analytics
  - data-preparation
inputs:
  - "CRM Analytics dataset ID and API name"
  - "Field API names requiring label or format changes"
  - "Target XMD layer: main (org-wide) or user (per-user)"
  - "External data source details if augmenting datasets with non-CRM data"
outputs:
  - "XMD PATCH payload for field-level formatting and label changes"
  - "Step-by-step XMD update procedure using the Wave REST API"
  - "External data augmentation design using Files node and Augment node in recipe"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-16
---

# Analytics Data Preparation (XMD Metadata and External Augmentation)

Use this skill when applying field-level metadata customizations to CRM Analytics datasets using the XMD REST API to set labels, aliases, date formats, number formats, and measure/dimension classification at the org level. Also covers the external data augmentation pattern for incorporating non-Salesforce data into CRM Analytics recipes.

---

## Before Starting

Gather this context before working on anything in this domain:

- What is the dataset ID (not API name — find via `GET /wave/datasets` or the Analytics Studio URL)?
- Is the change org-wide (PATCH main XMD) or personal preference (PATCH user XMD)?
- Are there external CSV files or Salesforce Files to be loaded as a recipe lookup source?
- Is this a one-time metadata update or part of a deployment pipeline requiring automated XMD updates post-dataflow?

---

## Core Concepts

### XMD Layer Hierarchy

CRM Analytics uses a three-layer Extended Metadata (XMD) system:

1. **System XMD** (`type=system`): Platform-generated. Immutable. Contains raw field API names and inferred data types. Cannot be modified — PATCH returns HTTP 400.
2. **Main XMD** (`type=main`): Org-customizable. PATCH this layer to apply field label, format, and classification changes for all users.
3. **User XMD** (`type=user`): Per-user customizations. Overrides main XMD only for the user who created the customization.

Resolution order at render time: user XMD → main XMD → system XMD (first non-null value wins).

### XMD REST API Mechanics

```
GET  /services/data/v{version}/wave/datasets/{datasetId}/xmds/{xmdtype}
PATCH /services/data/v{version}/wave/datasets/{datasetId}/xmds/{xmdtype}
```

**Key behaviors:**
- PATCH is an **additive merge** — include only properties you want to change.
- System XMD PATCH returns HTTP 400.
- WaveXmd is **NOT queryable via SOQL** — the REST API is the only interface. SOQL throws INVALID_TYPE.
- Main XMD has no version history — PATCH is destructive. Always GET and save a backup before modifying.

### External Data Augmentation Pattern

CRM Analytics recipes support loading external data via:
1. **Files node (CSV)**: Upload a CSV to Salesforce Files (ContentDocument), then reference it in a Recipe Files node. Best for reference data such as product hierarchies, territory mappings, or cost tables that do not exist in Salesforce objects.
2. **Augment node**: Join the Files node dataset to a primary dataset inside the recipe. The Augment node performs a left outer join keyed on a shared field.

External CSV data loaded via Files node is NOT subject to automatic incremental sync — it must be manually re-uploaded or replaced via Salesforce Files API to refresh the data.

---

## Common Patterns

### Pattern: PATCH Main XMD for Field Label Updates

**When to use:** After dataflow or recipe deployment when field API names from source objects are cryptic and dashboards display system names instead of business-readable labels.

**How it works:**
1. `GET /wave/datasets/{id}/xmds/main` — read and save as backup.
2. Locate the target field in the `dimensions` or `measures` array.
3. Construct the PATCH payload with only the `label` property changed:
```json
{
  "dimensions": [
    {
      "field": "Account_Type__c",
      "label": "Account Category"
    }
  ]
}
```
4. `PATCH /wave/datasets/{id}/xmds/main`. Verify HTTP 200.
5. Confirm label in Analytics Studio lens.

### Pattern: External CSV Augmentation in Recipe

**When to use:** When a recipe needs to enrich CRM Analytics data with a reference table not available as a Salesforce object (e.g., a product category mapping from an ERP system).

**How it works:**
1. Upload CSV to Salesforce Files via UI or Content API.
2. In Analytics Studio Recipe Builder, add a Files node and select the uploaded CSV.
3. Add an Augment node joining the Files node to the primary data node on the shared key field.
4. Ensure the join key exists in both sources with the same data type.
5. Schedule the recipe. When the external CSV changes, update the Salesforce File before the next recipe run.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Field label change for all users | PATCH main XMD | Main XMD applies org-wide |
| Personal field label preference | PATCH user XMD | User XMD is per-user only |
| Read field schema without modifying | GET system XMD | System XMD has the raw schema |
| SOQL query for WaveXmd | Use REST API instead | SOQL does not support WaveXmd |
| Reference data from non-Salesforce source | Files node + Augment in recipe | CRM Analytics recipe supports CSV augmentation |
| Reclassify numeric field to dimension | PATCH main XMD, move field to `dimensions` array | Measure/dimension classification is in main XMD |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Obtain the dataset ID** — Use `GET /wave/datasets?q={name}` or find the dataset ID in the Analytics Studio URL.
2. **Back up current main XMD** — `GET /wave/datasets/{id}/xmds/main` and save the response. There is no recovery after PATCH.
3. **Identify fields to update** — List field API names that need label, format, or classification changes. Confirm whether they appear in `dimensions` or `measures` in system XMD.
4. **Construct PATCH payload** — Build a minimal additive-merge JSON containing only changed properties.
5. **PATCH main XMD** — `PATCH /wave/datasets/{id}/xmds/main`. Verify HTTP 200.
6. **For external augmentation** — Upload CSV to Salesforce Files, add Files node in recipe, connect Augment node on join key, re-run recipe, verify field availability in output dataset.
7. **Validate in Analytics Studio** — Open a lens and confirm labels, formats, and classification are correct.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Main XMD backed up before PATCH
- [ ] PATCH targeted at `xmds/main` (not `xmds/system`)
- [ ] PATCH payload is additive-merge format (not full replace)
- [ ] HTTP 200 confirmed on PATCH response
- [ ] Field labels verified in Analytics Studio lens
- [ ] For external data: Augment node join key is the same data type in both sources
- [ ] CSV refresh process documented for recurring updates

---

## Salesforce-Specific Gotchas

1. **SOQL cannot query WaveXmd** — `SELECT … FROM WaveXmd` throws INVALID_TYPE. XMD is accessible only via the Wave REST API. Any documentation or code referencing SOQL for WaveXmd is incorrect.

2. **Modifying system XMD fails with HTTP 400** — System XMD is immutable. Always confirm the endpoint is `xmds/main`, not `xmds/system`.

3. **Main XMD is not versioned — no undo after PATCH** — Always GET and save main XMD before modification. If PATCH is applied with incorrect data, the previous state is lost.

4. **External CSV files are not auto-refreshed** — Files node data is static until the Salesforce File is manually updated. If the reference CSV changes frequently, build a Salesforce Files API upload step into the deployment pipeline.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| XMD backup JSON | GET response of main XMD before modification |
| XMD PATCH payload | Minimal additive-merge JSON for field label/format changes |
| External augmentation recipe plan | Node diagram for Files + Augment join configuration |

---

## Related Skills

- `admin/analytics-recipe-design` — Use for recipe node type selection, join matrices, formula language, and scheduling
- `admin/analytics-dataflow-development` — Use for sfdcDigest, Augment, and sfdcRegister node configuration in legacy dataflows
- `admin/analytics-dataset-management` — Use for dataset scheduling, row limits, and sharing configuration
- `data/einstein-analytics-data-model` — Use for conceptual understanding of the XMD layer hierarchy and dataset versioning model
