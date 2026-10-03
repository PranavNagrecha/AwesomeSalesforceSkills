---
name: analytics-data-preparation
description: "Use this skill when customizing CRM Analytics dataset field metadata via the XMD (Extended Metadata) REST API, or augmenting recipes with external non-Salesforce data: field labels, display formats, measures vs dimensions, user XMD PUT and WaveXmd deploys. Trigger keywords: XMD field labels, CRM Analytics main XMD update, dataset field formatting wave, analytics external data augmentation, WaveXmd REST API. NOT for recipe node transformation logic — use admin/analytics-recipe-design. NOT for dataflow node types or SOQL extraction — use admin/analytics-dataflow-development."
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
  - "PATCH main XMD CRM Analytics REST API field formatting overwriting"
  - "deploy WaveXmd field labels for a CRM Analytics dataset with the Metadata API"
  - "upload a CSV into a CRM Analytics dataset with the External Data API"
tags:
  - crm-analytics
  - xmd
  - dataset-metadata
  - analytics
  - data-preparation
inputs:
  - "CRM Analytics dataset ID or API name, and the current version ID"
  - "Field API names requiring label or format changes"
  - "Whether the XMD must travel in a package or deployment (Primary User XMD) or only live on one dataset version (Standard User XMD)"
  - "External data source details if loading non-CRM data into a dataset"
outputs:
  - "Complete user XMD JSON for a dataset version, or a WaveXmd metadata file for deployment"
  - "Step-by-step XMD update procedure using the CRM Analytics REST API or Metadata API"
  - "External Data API upload plan (InsightsExternalData header, 10 MB parts, metadata JSON)"
dependencies: []
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-10-03
---

# Analytics Data Preparation (XMD Metadata and External Data)

Use this skill when applying field-level formatting to CRM Analytics datasets through extended metadata (XMD): labels, member labels, number formats, hidden fields, colors, and dimension actions. It also covers loading non-Salesforce data into a dataset with the External Data API. Almost all XMD settings can now be made in the dataset edit page and lens UI; use the API path when the change must be repeatable or deployed.

Correction (2026-10-03): earlier versions of this skill said to PATCH `/wave/datasets/{id}/xmds/main` as an additive merge. The CRM Analytics REST API Developer Guide documents the XMD resource under a dataset version (`/wave/datasets/<datasetID>/versions/<versionID>/xmds/<xmdType>`) with GET for all types and PUT "on Xmd User type only." It states that PUT "cannot be used to update System or Main Xmd types." No PATCH method is documented on the XMD resource, and the XMD guide says each upload "overwrites the current dataset customizations."

---

## Before Starting

Gather this context before working on anything in this domain:

- What are the dataset ID and its current version ID? Every XMD REST path includes `/versions/<versionID>/`.
- Must the formatting survive a deployment or package install? Then it belongs in the Primary User XMD (WaveXmd metadata or the Dataset resource `userXmd` property), not only on the current dataset version.
- Does the user have Edit CRM Analytics Dataflows or Upload External Data to CRM Analytics? One of them is required to edit XMD.
- Is the external data a one-off reference table or a recurring feed? The External Data API limits jobs per dataset per day.

---

## Questions to Ask Before Configuring

Each question traces to a gotcha in `references/gotchas.md`.

| Question | Why it matters | What a good answer adds | What proper configuration adds over just doing it |
|---|---|---|---|
| "Should this formatting move between orgs or survive a package install?" | Standard User XMD is tied to a dataset version and can't be packaged; Primary User XMD can (Gotcha 3) | WaveXmd in source control, or a REST update on one version | Labels arrive with the deployment instead of being re-typed per org |
| "Who else edits this dataset's XMD in the UI?" | Each upload overwrites the whole XMD, and REST or UI edits make an MDAPI retrieve return an empty XMD (Gotchas 2, 4) | One owner and one write path | A Friday UI tweak is not silently erased by Monday's deploy |
| "Which fields are renamed or removed by the next dataflow or recipe change?" | XMD that references old field names causes errors when configuring actions (Gotcha 6) | A rename list reviewed with the XMD | Dashboards keep their labels and actions after the data change |
| "Is hiding a field meant to keep data from users?" | Hidden fields are still reachable in SAQL, dashboard JSON, and the REST API (Gotcha 5) | Row-level security or a narrower dataset for sensitive data | Hiding is used for tidiness, and security is done where it holds |
| "Does the external file have a header row, numeric columns, and a unique key?" | No header plus a default `numberOfLinesToIgnore` drops rows; numeric fields need a default value; only one text field can be the unique ID (Gotchas 7, 8) | A metadata JSON that matches the CSV column order | The upload succeeds first time and upserts match on the right key |
| "How often will the external data refresh?" | 50 external data jobs per dataset per rolling 24 hours, and 50 GB per day across uploads (Gotcha 9) | A refresh cadence within those limits | Hourly feeds do not run out of jobs by mid-afternoon |

---

## Core Concepts

### XMD Types

The REST API lists four XMD types: `asset`, `main`, `system`, and `user`. The Metadata API WaveXmd type uses the same names (System, User, Main, Asset).

1. **System XMD**: generated by the platform. The REST guide allows GET only.
2. **Main XMD**: listed with system and user for each dataset version. The REST guide allows GET only, and neither the REST nor the XMD guide describes how to write it. UNVERIFIED (2026-10-03): that main XMD is the merged result of system and user XMD was not stated in a fetched source.
3. **User XMD**: the writable layer. The XMD guide calls it the Standard User XMD and says it "defines custom formatting for dataset fields and values." It is dataset-wide: "If you modify the XMD for a dataset, every UI visualization that uses the dataset shows the modified format." Correction (2026-10-03): earlier versions said user XMD applies only to the user who created it.
4. **Asset XMD**: XMD attached to an asset such as a dashboard, read with `GET /wave/assets/<assetID>/xmds/asset`.

### Standard User XMD Versus Primary User XMD

The Standard User XMD is tied to a dataset version, "that isn't packageable." The Primary User XMD is tied to the dataset container and "can be included in packages." Update it by deploying WaveXmd through the Metadata API, or by setting `userXmd` on `PATCH /wave/datasets/<datasetIdOrApiName>`. It is "applied to a dataset only after a dataflow that updates the dataset runs." Updating the Standard User XMD updates the Primary User XMD automatically, but not the other way round.

### XMD Rules That Catch People

- Each upload overwrites; "Changes in the XMD aren't appended to previous customizations."
- "XMD doesn't support empty strings."
- Date labels can't be customized.
- A query across several datasets is formatted with "the XMD of the first loaded dataset."
- The `dataset` block is maintained by CRM Analytics; "Do not modify it."
- WaveXmd is a Metadata API type (suffix `.xmd`, folder `wave`). No WaveXmd object appears in the Object Reference, so SOQL cannot read it. UNVERIFIED (2026-10-03): the exact SOQL error text.

### External Data API

Load non-Salesforce data into a dataset by inserting an `InsightsExternalData` header (dataset alias in `EdgemartAlias`, `Format` Csv, `Operation` Overwrite, Append, Upsert, or Delete, `Action` None), uploading the CSV in parts under 10 MB to `InsightsExternalDataPart` with contiguous `PartNumber` values from 1, then setting `Action` to Process. Monitor `Status`. A metadata JSON file is recommended; without it "every field is treated as text."

The earlier "Files node plus Augment node in a recipe" pattern is kept as an option. UNVERIFIED (2026-10-03): recipe node names and file-input behaviour were not re-read in a fetched source (the CRM Analytics data integration guide PDF did not resolve under the 262 release path).

---

## Common Patterns

### Pattern: Change Labels and Formats on One Dataset Version

**When to use:** A one-off fix on the current dataset version, with no need to deploy elsewhere.

**How it works:**
1. `GET /wave/datasets/<datasetIdOrApiName>` and read the current version ID.
2. `GET /wave/datasets/<id>/versions/<versionId>/xmds/user` and save the response as the backup and the starting point.
3. Edit the saved JSON: change `label`, `members`, `format`, or `showInExplorer` on the target entries. Keep every other entry.
4. `PUT /wave/datasets/<id>/versions/<versionId>/xmds/user` with the complete edited JSON.
5. Confirm in a lens, and re-run step 2 to compare.

### Pattern: Deployable Labels With WaveXmd

**When to use:** Labels and formats must arrive with a deployment or package, and survive the next dataflow run.

**How it works:** Keep a WaveXmd file in source control (`references/metadata-examples.md`), deploy it with the Metadata API, then run the dataflow or recipe that updates the dataset so the Primary User XMD is applied. Do not edit the same XMD in the UI afterwards, or an MDAPI retrieve returns an empty file.

### Pattern: External CSV Through the External Data API

**When to use:** A reference table or feed from outside Salesforce must become a dataset or update one.

**How it works:** Build the metadata JSON in CSV column order, insert the header, upload 10 MB parts, set `Action` to Process, and poll `Status`. For later loads, set `Operation` to Append, Upsert, or Delete; set `Mode` to Incremental for faster appends. Upsert and incremental extract need exactly one text field with `isUniqueId: true`.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| One-off label change on the live dataset | Dataset edit page, or PUT the complete user XMD on the current version | Only the user XMD is writable through REST |
| Labels must deploy to another org | WaveXmd through the Metadata API, then run the dataflow | Standard User XMD is version-bound and not packageable |
| Read the generated schema | GET system XMD on the current version | System XMD is read-only and reflects the generated fields |
| SOQL query for WaveXmd | Use the REST XMD resource or a Metadata API retrieve | No WaveXmd object exists for SOQL |
| Reference data from a non-Salesforce source | External Data API with a metadata JSON | Documented limits, typed fields, and Append or Upsert for refreshes |
| Hide a sensitive field | Row-level security or a dataset without the field | Hidden fields remain reachable through SAQL and REST |

---

## Recommended Workflow

1. Identify the dataset, its current version ID, and whether the change must be deployable; pick REST user XMD, WaveXmd, or the dataset edit page from the Decision Guidance table.
2. Back up first: GET the user XMD for the version (or retrieve WaveXmd) and commit the JSON before editing.
3. Edit the complete document: keep every existing entry, remove empty strings, and leave the `dataset` block alone.
4. Validate with `python3 scripts/check_analytics_data_preparation.py --manifest-dir <folder with *.xmd, *.xmd.json, and external metadata JSON>`.
5. Apply it: PUT the user XMD, or deploy WaveXmd and run the dataflow that updates the dataset.
6. For external data, upload with the External Data API using a validated metadata JSON and confirm `Status` on the InsightsExternalData header.
7. Confirm labels, formats, and member labels in a lens, and record which write path owns this dataset's XMD.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] XMD backed up (GET on the version, or WaveXmd retrieved) before any write
- [ ] Writes target the user XMD (REST PUT) or WaveXmd (Metadata API); nothing tries to write system or main
- [ ] The uploaded XMD is complete, because each upload overwrites
- [ ] No empty strings in the XMD; the `dataset` block untouched
- [ ] Field labels verified in a lens after the write
- [ ] For deployments: the dataflow or recipe ran after the WaveXmd deploy
- [ ] For external data: metadata JSON in CSV column order, numeric fields with default values, at most one text unique ID
- [ ] External data refresh cadence fits 50 jobs per dataset per rolling 24 hours

---

## Salesforce-Specific Gotchas

1. **No PATCH on the XMD resource**: The REST guide documents GET for all XMD types and PUT on the user type only. A PATCH to `xmds/main` is not a documented operation.

2. **Uploads replace, they do not merge**: Each XMD upload overwrites the current customizations. Send the full document every time.

3. **Version-bound XMD does not deploy**: The Standard User XMD is tied to a dataset version and can't be packaged. Use the Primary User XMD (WaveXmd) for anything that moves between orgs.

4. **Hidden is not secure**: Hidden fields are still available in dashboard JSON, SAQL, and the REST API.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| XMD backup JSON | GET response of the user XMD for the dataset version, or the retrieved WaveXmd |
| Complete user XMD JSON | The full edited document for PUT on the version |
| WaveXmd metadata file | Deployable Primary User XMD with package.xml entry |
| External data upload plan | Metadata JSON, header values, part sizing, refresh cadence |

---

## Related Skills

- `admin/analytics-recipe-design` — Use for recipe node type selection, join matrices, formula language, and scheduling
- `admin/analytics-dataflow-development` — Use for sfdcDigest, Augment, and sfdcRegister node configuration in legacy dataflows
- `admin/analytics-dataset-management` — Use for dataset scheduling, row limits, and sharing configuration
- `data/einstein-analytics-data-model` — Use for conceptual understanding of the XMD layer hierarchy and dataset versioning model
