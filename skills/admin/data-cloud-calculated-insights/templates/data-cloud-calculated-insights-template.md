# Data Cloud Calculated Insights — Work Template

Use this template when designing, creating, or reviewing a Calculated Insight in Data Cloud.
Complete every section before saving the insight. Measure API names are immutable after creation.

---

## Scope

**Skill:** `data-cloud-calculated-insights`

**Request summary:** (describe what metric or insight the user asked for)

**Insight type:** [ ] Calculated Insight (batch SQL)  [ ] Streaming Insight (real-time event)

---

## Pre-Creation Design (Complete Before Saving — Cannot Change After)

### Insight Identification

| Field | Value |
|---|---|
| Insight API name | (snake_case, org naming convention) |
| Insight display name | (human-readable) |
| Base DMO | (e.g., SalesOrder__dlm, UnifiedIndividual__dlm) |
| Schedule cadence | [ ] Every 6 hours  [ ] Every 12 hours  [ ] Every 24 hours |
| Owner / team | |

### Dimensions

| API Name | Data Type | Business Definition | Immutability Confirmed |
|---|---|---|---|
| (e.g., customer_id) | Text | (Unified Individual ID) | [ ] |
| | | | [ ] |

### Measures

| API Name | Data Type | Rollup Behavior | Business Definition | Immutability Confirmed |
|---|---|---|---|---|
| (e.g., total_lifetime_spend) | Decimal | SUM | Total of all order amounts | [ ] |
| (e.g., purchase_count_90d) | Integer | COUNT | Orders in last 90 days | [ ] |
| | | | | [ ] |

**Design sign-off required before creating the insight:** [ ] Yes — reviewed and approved

---

## Context Gathered

- **Source DMOs available and populated:** (list DMOs, confirm record count > 0)
- **Freshness requirement:** (how stale can the metric be for downstream segments or activations?)
- **Downstream use:** [ ] Segment Builder filter  [ ] Activation field  [ ] Reporting only  [ ] Data Action trigger
- **Org insight count before this addition:** (current count / 300 total; current streaming / 20)

---

## SQL Definition

```sql
-- Calculated Insight SQL
-- Confirm: every non-aggregated SELECT column appears in GROUP BY
-- Confirm: WHERE clause limits date range scanned
-- Confirm: SQL is under 131,021 characters
-- Confirm: estimated execution time is well under 2 hours

SELECT
    <dimension_column>            AS <dimension_api_name>,
    <AGG>(<measure_column>)       AS <measure_api_name>
FROM <DMO_name>
WHERE <date_filter>
GROUP BY <dimension_column>
```

---

## Streaming Insight Configuration (if applicable)

| Field | Value |
|---|---|
| Event source | [ ] Mobile/Web SDK  [ ] Marketing Cloud Personalization |
| Event window | (e.g., last 30 minutes) |
| Event condition / filter | (e.g., event_type = 'cart_abandon') |
| Linked Data Action | (name of the Data Action to trigger) |

**Note:** Streaming Insights are not available as Segment Builder filter fields. If the goal is segmentation, use a Calculated Insight instead.

---

## Checklist

Complete all items before and after creating the insight:

**Pre-creation:**
- [ ] All dimension and measure API names finalized and reviewed
- [ ] All measure data types confirmed (Decimal for monetary, Integer for counts, Text for string dimensions)
- [ ] Rollup behaviors specified for all measures
- [ ] All referenced DMOs confirmed to exist and have non-zero record count
- [ ] Schedule cadence selected (6h / 12h / 24h) and matched to downstream freshness requirement
- [ ] Org insight count checked: total < 300; streaming (if applicable) < 20
- [ ] SQL tested with a limited date range to confirm it runs without error

**Post-creation:**
- [ ] First run completed with status: Completed (not Failed or Timed Out)
- [ ] Row count from first run matches expected data volume
- [ ] Measures appear as filterable fields in Segment Builder (for Calculated Insights used in segmentation)
- [ ] Streaming Insight fires the linked Data Action correctly on a test event (for Streaming Insights)

---

## Decision Rationale

**Why Calculated Insight (not Streaming Insight, or segment filter condition):**

(Document the reasoning here. Reference the Decision Guidance table in SKILL.md if applicable.)

---

## Notes

(Record any deviations from the standard pattern, business-specific constraints, or open questions.)
