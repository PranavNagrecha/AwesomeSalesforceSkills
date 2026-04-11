# Analytics Dataset Management — Work Template

Use this template when building, updating, or troubleshooting a CRM Analytics dataset.

---

## Scope

**Skill:** `analytics-dataset-management`

**Request summary:** (describe what was asked — e.g., "Schedule nightly Opportunity dataset refresh" or "Fix CloseDate showing as Text in pipeline dataset")

---

## Context Gathered

Answer these before starting work:

| Question | Answer |
|---|---|
| How many dataflows and recipes are currently active in this org? | |
| What is the current estimated total runs per 24-hour window? | |
| Are there managed-package dataflows (Revenue Intelligence, Service Analytics, etc.)? | |
| Which Salesforce objects will feed this dataset? | |
| Which fields are Date or Datetime and must support SAQL filtering? | |
| What is the approximate row count per object per day? | |
| Is this a new dataset or a change to an existing one? | |
| Is the dataset currently append-mode or full-replace? | |

---

## Quota Assessment

Fill in before scheduling any new or changed dataflow:

| Dataflow Name | Runs per Day | Source |
|---|---|---|
| (existing custom flow 1) | | Custom |
| (existing custom flow 2) | | Custom |
| (managed package flows) | | Managed |
| **NEW: (this dataflow)** | | Custom |
| **Total** | | |

**Quota headroom:** `60 - [total] = [headroom]`

If headroom drops below 10, raise a scheduling concern before proceeding.

---

## Date Field Inventory

List every Date or Datetime field that will be loaded into the dataset:

| Field Name | Source Object | SAQL Usage (timeseries / filter / group-by) | Schema Node Added? |
|---|---|---|---|
| | | | [ ] |
| | | | [ ] |
| | | | [ ] |

---

## Dataflow Design

**Flow name:**

**Objects included:**

| Object | sfdcDigest Node Name | Fields Pulled |
|---|---|---|
| | | |
| | | |

**Transformation nodes (in order):**

1. `sfdcDigest` — (object name)
2. `schema` — date field type declarations
3. (additional augment/join/filter nodes if needed)
4. `sfdcRegister` — dataset name: ___________

**Dataset mode:** [ ] Full-replace  [ ] Append

If append-mode: rolling window filter: _______________________ (e.g., last 13 months on ActivityDate)

**Scheduled run window:** _____________ UTC

---

## Validation Steps

After the first successful run, confirm each item:

- [ ] Dataset appears in Data Manager with correct name and alias
- [ ] All date fields show column type `Date` (not `Text`) in the dataset column list
- [ ] Ran a test SAQL query with a date range filter — confirmed data returns correctly
- [ ] Ran a `timeseries` SAQL expression against at least one date field — confirmed non-empty result
- [ ] Dataset row count is within expected range
- [ ] For append-mode: trim filter is present and verified in the dataflow JSON
- [ ] Failure notification is configured in Data Manager > Notification Settings
- [ ] Dataflow owner and escalation contact are documented

---

## Row-Count Projection (for append-mode datasets)

| Metric | Value |
|---|---|
| Rows added per day (estimate) | |
| Rows after 6 months | |
| Rows after 12 months | |
| Org-wide current total rows | |
| Projected org total after 12 months | |
| Action required if > 400M org-wide? | |

---

## Notes

Record any deviations from the standard pattern and why:

(free text)
