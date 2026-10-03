---
name: einstein-analytics-data-model
description: "Use this skill when working with CRM Analytics (Einstein Analytics) extended metadata (XMD) — the multi-layer metadata system controlling field display labels, aliases, number and date formatting, measure/dimension classification, and dataset versioning. Trigger keywords: XMD API, dataset field formatting CRM Analytics, wave dataset labels, main XMD update, dataset versioning Analytics, update the user XMD, deploy WaveXmd. NOT for recipe node configuration — use admin/analytics-recipe-design. NOT for dataflow development, node types, and scheduling — use admin/analytics-dataflow-development."
category: data
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
triggers:
  - "how do I change field labels in a CRM Analytics dataset without breaking existing dashboards"
  - "what is XMD and how does it control field display in Einstein Analytics"
  - "my CRM Analytics dataset is showing technical API names instead of business-friendly labels"
  - "how do I apply org-wide formatting to a CRM Analytics field versus per-user customization"
  - "can I query WaveXmd using SOQL to see dataset metadata"
  - "my PATCH to the CRM Analytics XMD REST API is overwriting all existing field settings"
  - "update the XMD for a dataset version with the REST API"
  - "deploy CRM Analytics XMD formatting to another org in a package"
tags:
  - crm-analytics
  - einstein-analytics
  - xmd
  - dataset-metadata
  - wave
inputs:
  - "CRM Analytics dataset API name and dataset ID"
  - "Current dataset version ID (from the dataset's currentVersionId)"
  - "Field API names requiring formatting or label customization"
  - "Delivery path: one-off REST update of the version's user XMD, or packaged WaveXmd metadata"
outputs:
  - "Complete user XMD JSON for a PUT to /wave/datasets/<datasetID>/versions/<versionID>/xmds/user"
  - "WaveXmd metadata file and package.xml entry when the formatting must move between orgs"
  - "Guidance on which XMD type is readable versus writable"
  - "Dataset versioning awareness documentation"
dependencies: []
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-10-03
---

# Einstein Analytics Data Model (XMD and Dataset Versioning)

Use this skill when a practitioner needs to understand the CRM Analytics dataset model behind field display: the extended metadata (XMD) types, dataset versions, and the REST and Metadata API mechanics for changing how dataset fields look. Transformation logic in dataflows and recipes is out of scope.

---

## Before Starting

Gather this context before working on anything in this domain:

- What is the dataset ID, and what is its `currentVersionId`? Every XMD REST URL contains both: `/wave/datasets/<datasetID>/versions/<versionID>/xmds/<xmdType>`.
- Is the change a label, a value label (`members`), a number format, a hidden field, a chart color, or a record action?
- Must the change survive a move to another org? The version-bound user XMD cannot be packaged; the WaveXmd metadata type can.
- Does the running user hold Edit CRM Analytics Dataflows or Upload External Data to CRM Analytics? The XMD guide names those as the permissions needed to edit XMD.

---

## Questions to Ask Before Configuring

| Question | Why it matters | What a good answer adds | What proper configuration adds over just doing it |
|---|---|---|---|
| "Is this a one-time fix in this org, or must the formatting deploy from sandbox to production?" | The Standard User XMD is tied to a dataset version and cannot be packaged; only the Primary User XMD (WaveXmd metadata) can | The delivery path: REST PUT on the version's user XMD, or a WaveXmd file in source control | Formatting that arrives with the release instead of a manual rework in every org |
| "Which dashboards query this dataset together with another dataset?" | A multi-dataset query is formatted with the XMD of the first loaded dataset only | The list of SAQL `load` orders to check, or the second dataset whose XMD needs the same labels | Labels and number formats that stay consistent on blended widgets |
| "Are we hiding a field because users should not see it, or only to declutter the explorer?" | `showInExplorer: false` removes a field from the explorer, but SAQL, dashboard JSON, and the REST API still reach it | A decision to use a security predicate or a different dataset when the goal is access control | No sensitive field left one SAQL edit away from a viewer |
| "When does the next dataflow or recipe run change this dataset's schema?" | A new version gets a new system XMD; a renamed or dropped field breaks XMD entries and surfaces only in the `errorMessage` property | A post-run check of `errorMessage` on the new version's user XMD | Schema changes that come with an XMD update instead of a silently broken action menu |
| "Who owns the current XMD file, and where is the last known-good copy?" | An upload or PUT of an invalid file reverts all formatting to defaults, and the API keeps no history | A saved copy of the user XMD for the current version before every change | A one-step rollback instead of rebuilding labels from screenshots |
| "Will users download this data to CSV or Excel?" | Custom delimiters are not honored in CSV downloads, and a multiplier of 0 downloads every value as 0 | Format choices that read correctly in both the dashboard and the export | Exports that match what the dashboard shows |

What a proper configuration adds over just editing XMD: the change lands on the writable XMD type, is versioned in a file you can redeploy, and is checked again after the next schema change instead of drifting until a user reports a broken chart.

---

## Core Concepts

### XMD types and which ones you can write

The CRM Analytics REST API lists four XMD types: `asset`, `main`, `system`, and `user` (Xmd response body, `type` property). Only one is writable through REST.

| XMD type | Where it lives | Read | Write |
|---|---|---|---|
| `system` | Per dataset version, generated by the platform | `GET .../versions/<versionID>/xmds/system` | No. The REST guide says the PUT request cannot update System or Main XMD types. |
| `main` | Per dataset version | `GET .../versions/<versionID>/xmds/main` | No (same rule). UNVERIFIED (2026-10-03): that `main` is the merged view of system plus user XMD; the 262 guides list the type without describing it. |
| `user` (Standard User XMD) | Per dataset version; the file you upload on the Edit Dataset page | `GET .../versions/<versionID>/xmds/user` | `PUT .../versions/<versionID>/xmds/user`, or upload on the Edit Dataset page |
| `asset` | A dashboard or lens | `GET /wave/assets/<assetID>/xmds/asset` | Not through this resource |
| Primary User XMD | The dataset container, not a version | MDAPI retrieve (returns the file only if it was deployed with MDAPI) | Deploy the `WaveXmd` metadata type, or set `userXmd` on `PATCH /wave/datasets/<datasetIdOrApiName>` |

The user XMD is not a per-person preference. The XMD guide says that when you modify a dataset's XMD, every visualization that uses the dataset shows the modified format.

### Dataset versions and XMD

Each dataset has a stable ID and a `currentVersionId` (Dataset response body). `GET /wave/datasets/<datasetIdOrApiName>/versions` lists versions. XMD REST resources hang off a version, so a URL built from last month's version ID edits a version that dashboards no longer read.

When a dataflow creates a new version, the platform copies the current user XMD forward. The Xmd response body carries an `errorMessage` property for the case where that copy-forward failed. If a field is renamed or deleted upstream, the XMD guide says you must update the XMD, and the error also appears in `errorMessage`.

### Datasets are not related objects

SAQL combines data streams with `cogroup` (SAQL Developer Guide, "Combine Data from Multiple Data Streams with cogroup"). There is no persistent relationship metadata in XMD. There is no `WaveXmd` sObject in the Object Reference or the Tooling API; `WaveXmd` exists only as a Metadata API type (suffix `.xmd`, `wave` folder, API 39.0 and later). SOQL cannot read XMD.

---

## Common Patterns

### Pattern: Change labels and formats for everyone in one org

1. `GET /services/data/v67.0/wave/datasets/<datasetID>` and read `currentVersionId`.
2. `GET .../versions/<currentVersionId>/xmds/user` and save the response to a file.
3. Edit the saved document. Keep every existing customization in it.
4. `PUT .../versions/<currentVersionId>/xmds/user` with the complete document.
5. Open a lens on the dataset and confirm the labels.

The XMD guide states that each upload overwrites the current customizations and is not appended. UNVERIFIED (2026-10-03): whether a partial REST PUT body merges; send the complete user XMD so the outcome does not depend on it.

### Pattern: Ship formatting with a release

Deploy a `WaveXmd` component (worked example in `references/metadata-examples.md`). The Primary User XMD applies to the dataset only after a dataflow that updates the dataset runs, because that run sets the Standard User XMD on the new version. Schedule or trigger the run as part of the deployment.

### Pattern: Hide a field from builders

Set `"showInExplorer": false` on the field in `dimensions` or `measures`. Treat this as decluttering only. The XMD reference says the field stays usable in SAQL, dashboard JSON, and the REST API.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Rename a field label for all users in this org | GET then PUT the version's user XMD | `user` is the only REST-writable XMD type |
| Same labels needed in sandbox and production | Deploy `WaveXmd`, then run the dataflow | Standard User XMD is version-bound and not packageable |
| See the platform-generated schema | GET the version's system XMD | Read-only reference |
| Edit system or main XMD | Stop | The REST guide forbids PUT on System and Main |
| Read XMD from Apex or SOQL | Use the REST API | No `WaveXmd` sObject exists |
| Turn a numeric field into a grouping | Change the field type upstream (recipe, dataflow, or External Data metadata `type`) | The XMD guide's list of customizations does not include changing a field's type |
| Field broke after a refresh | Read `errorMessage` on the new version's user XMD | The platform reports copy-forward and stale-field errors there |

---

## Recommended Workflow

1. **Resolve the version.** `GET /wave/datasets/<datasetIdOrApiName>` and record `id` and `currentVersionId`.
2. **Back up.** GET `xmds/user`, `xmds/main`, and `xmds/system` for that version and save them under the change ticket.
3. **Choose the path.** One-org fix: edit the saved user XMD. Cross-org: author a `WaveXmd` file from `references/metadata-examples.md`.
4. **Edit within documented limits.** Labels up to 40 characters, descriptions up to 1,000, no empty strings, no edits to the `dataset` block.
5. **Apply.** PUT the full user XMD, or deploy the `WaveXmd` and run the dataflow that refreshes the dataset.
6. **Verify.** Re-GET the user XMD, confirm `errorMessage` is empty, and open a lens to see the labels. Run `python3 scripts/check_einstein_analytics_data_model.py --manifest-dir <folder>` on the folder holding the XMD file and any script that called the API.

---

## Review Checklist

- [ ] The URL contains the current version ID, not an old one
- [ ] Only `xmds/user` was written; system and main were read only
- [ ] The PUT body is the complete user XMD, saved to a file first
- [ ] No label longer than 40 characters and no empty string values
- [ ] `showInExplorer: false` is not being used as a security control
- [ ] Cross-org formatting is a `WaveXmd` file, and the dataflow ran after deploy
- [ ] `errorMessage` on the refreshed version's user XMD is empty

---

## Salesforce-Specific Gotchas

See `references/gotchas.md` for the full list with sources. The two that cause the most rework: an invalid upload reverts all formatting to defaults, and an MDAPI retrieve returns an empty `WaveXmd` once anyone edits the XMD through the UI or REST.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Pre-change backup | GET responses for user, main, and system XMD of the current version |
| User XMD document | Complete JSON for the PUT |
| WaveXmd component | `wave/<name>.xmd` plus the package.xml entry |
| Post-run check | `errorMessage` value of the refreshed version's user XMD |

---

## Related Skills

- `admin/analytics-dataflow-development`: Use for sfdcDigest, Augment, sfdcRegister node configuration and Data Sync setup
- `admin/analytics-recipe-design`: Use for recipe node types, transformation logic, and formula language
- `admin/analytics-dataset-management`: Use for dataset scheduling, row limits, and dataset sharing settings
- `architect/analytics-data-architecture`: Use for multi-dataset architecture decisions and CRM Analytics platform design
