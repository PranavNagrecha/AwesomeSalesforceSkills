# Analytics Data Preparation (XMD and External Data): Work Template

Use this template when updating CRM Analytics dataset XMD or loading external data into a dataset.

---

## Scope

**Dataset API Name:** _______________
**Dataset ID:** _______________
**Current Version ID:** _______________
**Task:** [ ] User XMD update on this version  [ ] Deployable WaveXmd  [ ] External Data API upload
**Write path that owns this dataset's XMD:** [ ] Metadata API (WaveXmd)  [ ] REST user XMD  [ ] Dataset edit page

---

## XMD Update

**Backup before any write:**
- [ ] `GET /wave/datasets/{id}/versions/{versionId}/xmds/user` saved to: _______________
- [ ] or WaveXmd retrieved and confirmed not empty

**Fields to update:**

| Field API Name | Change Type (label, member label, format, hide) | New Value |
|---|---|---|
| | | |

**Write:** [ ] `PUT /wave/datasets/{id}/versions/{versionId}/xmds/user` with the complete document  [ ] WaveXmd deploy followed by a dataflow run

**Checker:** [ ] `python3 scripts/check_analytics_data_preparation.py --manifest-dir <folder>` exit 0

---

## External Data Upload

**CSV file name:** _______________
**Has header row:** [ ] Yes (`numberOfLinesToIgnore` 1)  [ ] No (`numberOfLinesToIgnore` 0)
**Metadata JSON file:** _______________ (fields in CSV column order)
**Unique ID field (one text field):** _______________
**Operation:** [ ] Overwrite  [ ] Append  [ ] Upsert  [ ] Delete    **Mode:** [ ] Incremental  [ ] None
**Refresh cadence and jobs per day (limit 50 per dataset):** _______________

---

## Validation

- [ ] Labels and member labels visible in a lens
- [ ] No empty strings in the XMD; `dataset` block untouched
- [ ] InsightsExternalData `Status` checked after `Action` = Process
- [ ] Sensitive fields protected by security, not by hiding
