# Analytics Data Governance — Work Template

Use this template when implementing or auditing CRM Analytics data governance controls.
Fill in each section before starting work. Return to it when verifying completion.

---

## Scope

**Skill:** `analytics-data-governance`

**Request summary:** (describe the governance task: lineage audit, access log setup, retention enforcement, erasure, compliance review, etc.)

**Org:** (instance URL / sandbox name)

**Initiated by:** (team, compliance request reference, audit finding)

---

## Pre-Work: Context Gathered

Answer each question before proceeding. These determine which patterns apply.

**Event Monitoring license status:**
- [ ] Confirmed active — add-on licensed and enabled
- [ ] Not licensed — compensating controls needed; document below
- [ ] Unknown — check Setup > Company Information > Feature Licenses

**Org release (for ELO availability):**
- Summer '24 or later: [ ] Yes / [ ] No / [ ] Unknown

**Event log delivery mechanism available:**
- [ ] Event Log Objects (WaveInteractionLog / WaveChangeLog) — Summer '24+, ELO enabled
- [ ] EventLogFile CSV (hourly delivery) — fallback when ELO not available

**Dataset ingestion types in scope:**
- [ ] Recipe-produced datasets
- [ ] Dataflow-produced datasets
- [ ] External Data API uploads
- [ ] Live datasets (remote connections — no ingested data, lineage different)

**Compliance driver:**
- [ ] GDPR right-to-erasure
- [ ] GDPR / HIPAA access audit
- [ ] Internal data classification policy
- [ ] SOC 2 / ISO 27001 audit evidence
- [ ] Other: ___________

**Datasets in scope:**
| Dataset Name | Dataset ID | Sensitivity | Known Producer (recipe/dataflow) |
|---|---|---|---|
| | | | |
| | | | |

---

## Lineage Map

*Complete this section before making any schema or retention changes.*

**Lineage script run:** [ ] Yes / [ ] No

**Results summary:**

| Dataset Name | Producer Type | Producer Name / ID | Output Node / outputDatasets entry |
|---|---|---|---|
| | recipe | | |
| | dataflow | | |
| | external-data-api | (no API metadata) | N/A |

**Orphaned datasets** (datasets with no identifiable producer):
- (list here — these may be from deleted recipes or manual uploads)

---

## Data Classification Gap Analysis

*For each in-scope dataset, document which source fields carry classification metadata and how the dataset layer compensates.*

| Dataset Column | Source Object.Field | Source Classification | Dataset-Layer Control Applied |
|---|---|---|---|
| | | Restricted | Column excluded in recipe |
| | | Confidential | Row-level predicate applied |
| | | None | No control needed |

**Governance register updated:** [ ] Yes / [ ] No / [ ] Not applicable

---

## Access Audit Log Plan

**Event types to enable:** [ ] WaveInteraction [ ] WaveChange [ ] WavePerformance

**Query approach:**

```soql
-- Event Log Objects (Summer '24+):
SELECT UserId, SessionKey, QueriedEntities, Timestamp
FROM WaveInteractionLog
WHERE Timestamp >= [START_DATE]
  AND Timestamp <  [END_DATE]
ORDER BY Timestamp ASC

-- OR EventLogFile (older orgs / fallback):
SELECT Id, EventType, LogDate
FROM EventLogFile
WHERE EventType IN ('WaveInteraction', 'WaveChange')
  AND LogDate >= [START_DATE]
  AND LogDate <  [END_DATE]
ORDER BY LogDate ASC
```

**Log delivery / export target:** (SIEM name, S3 bucket, Salesforce Big Object, spreadsheet)

**Cadence:** (daily export, weekly review, quarterly audit report)

**Audit query validated:** [ ] Yes — successful log retrieval confirmed

---

## Retention Implementation

*Complete one row per in-scope dataset.*

| Dataset Name | Retention Window | Enforcement Mechanism | Schedule | Version Cleanup? | Owner |
|---|---|---|---|---|---|
| | 90 days | Scheduled recipe filter | Daily 02:00 UTC | Yes — API version delete | |
| | 1 year | Manual deletion | Quarterly review | Yes | |

**Recipe failure alert configured:** [ ] Yes / [ ] No

**Post-run assertion / validation step:** [ ] Yes / [ ] No

**Retention runbook location:** (link to runbook document or Confluence page)

---

## Erasure / Right-to-Erasure Runbook (if applicable)

*Complete this section only for GDPR or other erasure requests.*

**Data subject ID / request reference:** ___________

**Datasets containing subject data:**
1. Dataset: ___________ | Dataset ID: ___________
2. Dataset: ___________ | Dataset ID: ___________

**Steps completed:**

- [ ] Identified all datasets and dataset versions containing subject data
- [ ] Deleted all dataset versions via REST API (`DELETE /wave/datasets/{id}/versions/{vid}`)
- [ ] Deleted dataset current reference (`DELETE /wave/datasets/{id}`)
- [ ] Confirmed zero remaining versions (`GET /wave/datasets/{id}/versions` returns empty)
- [ ] Updated governance register to reflect deletion
- [ ] Erasure confirmation record created with: dataset ID, version count deleted, timestamp, operator

---

## Deviations from Standard Pattern

*Document any steps skipped, modified, or compensated for — and the reason.*

| Standard Step | Deviation | Reason | Compensating Control |
|---|---|---|---|
| | | | |

---

## Review Checklist

- [ ] Event Monitoring license confirmed (active or absence documented)
- [ ] Dataset lineage map produced — all production datasets have a documented producer
- [ ] Data classification gap documented — source-field classifications re-applied at dataset layer
- [ ] Retention policy implemented — scheduled recipe filter or documented deletion cadence
- [ ] Dataset versions addressed in any erasure or purge process
- [ ] Access audit log query validated — at least one successful log retrieval confirmed
- [ ] Governance register updated — dataset inventory, classification tier, retention window, owner

---

## Sign-Off

**Completed by:** ___________

**Reviewed by (data governance / privacy team):** ___________

**Date:** ___________

**Notes:**
