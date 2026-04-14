# Analytics KPI Definition — Work Template

Use this template to produce the KPI register before any CRM Analytics lens or dashboard is built.

## Scope

**Skill:** `analytics-kpi-definition`

**Project / Dashboard Name:** (fill in)
**CRM Analytics Dataset(s) Used:** (fill in)
**Reporting Period:** (fill in)
**Stakeholder Requestors:** (fill in)
**Sign-off Required From:** (fill in)

---

## KPI Register

Complete one row per KPI. Get stakeholder sign-off before development.

| KPI Name | Plain-English Definition | Aggregation Formula | Measure Field | Dimension Fields (GROUP BY) | Filter Criteria | Target Model | Benchmark |
|---|---|---|---|---|---|---|---|
| | Include: X; Exclude: Y | SUM / AVG / COUNT / RATIO | Field name + Type: Measure | Field names + Type: Dimension | | Fixed value / Targets dataset / None | |

---

## Targets Dataset Schema (if required)

**Dataset Name:** ______

| Column Name | Type | Description | Example Values |
|---|---|---|---|
| | Dimension | Join key (must match actuals exactly) | |
| | Dimension | | |
| | Measure | Target value | |

**Load Schedule:** (quarterly / monthly / on demand)
**Join Key to Actuals:** (exact field name and format)
**Case Sensitivity Warning:** Confirm join key values match actuals dataset exactly (case-sensitive)

---

## SAQL Formula Sketches

For each KPI, document the SAQL pattern:

**KPI 1: [Name]**
```saql
q = load "[DatasetName]";
q = filter q by [FilterCriteria];
result = foreach q generate [DimensionField], [AggregationFunction]([MeasureField]) as KPIValue;
result = order result by KPIValue desc;
result = limit result 100;
```

**KPI with Target Attainment:**
```saql
q_actual = load "[ActualsDataset]";
q_target = load "[TargetsDataset]";
q_joined = cogroup q_actual by [JoinKey], q_target by [JoinKey];
result = foreach q_joined generate [JoinKey],
  sum(q_actual.[MeasureField]) as Actual,
  sum(q_target.Target_Value) as Target,
  sum(q_actual.[MeasureField]) / sum(q_target.Target_Value) * 100 as Attainment;
```

---

## Review Checklist

- [ ] All KPIs have plain-English definitions with inclusion/exclusion criteria
- [ ] Measure vs Dimension type confirmed for all fields used in formulas
- [ ] Target attainment model designed for all KPIs requiring it
- [ ] Targets dataset schema defined with join key and load schedule
- [ ] SAQL formula sketch validated against dataset field types
- [ ] Stakeholder sign-off recorded
- [ ] No KPI left as "TBD formula"
