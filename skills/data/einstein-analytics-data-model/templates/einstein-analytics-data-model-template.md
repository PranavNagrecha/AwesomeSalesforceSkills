# Einstein Analytics Data Model (XMD): Work Template

Use this template when changing CRM Analytics dataset field formatting through XMD.

---

## Scope

**Dataset API Name:** _______________
**Dataset ID:** _______________
**Current version ID (`currentVersionId`):** _______________
**Change type:** [ ] Field label  [ ] Value labels (`members`)  [ ] Number format  [ ] Hide from explorer  [ ] Chart colors  [ ] Record actions
**Delivery path:** [ ] REST PUT of this version's user XMD (one org)  [ ] `WaveXmd` metadata deploy plus dataflow run (cross-org)

---

## Pre-Change Backup

- [ ] `GET /wave/datasets/<datasetID>/versions/<versionID>/xmds/user` saved to: `xmd-user-<dataset>-<date>.json`
- [ ] `GET .../xmds/system` saved (reference schema)
- [ ] `GET .../xmds/main` saved (reference only; not writable)

---

## Fields to Update

| Field API Name | Section (dimensions / measures / derived*) | Current Label | New Label (max 40 chars) | Format or other change |
|---|---|---|---|---|
| | | | | |

---

## Complete User XMD for the PUT

Paste the full edited document here, not a delta.

```json
{
  "dimensions": [],
  "measures": []
}
```

---

## Post-Change Validation

- [ ] PUT returned an Xmd with `"type": "user"`
- [ ] `errorMessage` is absent or empty
- [ ] Labels verified in a lens on the dataset
- [ ] `python3 scripts/check_einstein_analytics_data_model.py --manifest-dir <folder>` exits 0
- [ ] For a `WaveXmd` deploy: the dataflow ran after the deploy, and nobody edits this XMD in the UI afterwards
