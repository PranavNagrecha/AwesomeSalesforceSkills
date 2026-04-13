# CRM Analytics Dashboard Design — Work Template

Use this template when designing or troubleshooting a CRM Analytics dashboard.

## Scope

**Skill:** `analytics-dashboard-design`

**Dashboard name:** (fill in)

**Target audience:** (executive / operations / self-service)

**Datasets in use:** (list all dataset names the dashboard will reference)

## Interaction Design

**Single dataset?** [ ] Yes  [ ] No (multiple datasets)

**Filtering mechanism:**
- [ ] Faceting (same-dataset) — no JSON editing required
- [ ] Selection bindings (cross-dataset) — requires JSON editing
- [ ] Both

**Dynamic measure/grouping?** [ ] Yes  [ ] No

If Yes: [ ] columnMap replaced with `"columns": []` for affected widgets

## Widget Plan

| Widget Name | Step Name | Dataset | Chart Type | Participates in Faceting? |
|---|---|---|---|---|
| | | | | [ ] Yes / [ ] No |
| | | | | [ ] Yes / [ ] No |
| | | | | [ ] Yes / [ ] No |

## Binding Configuration (if applicable)

| Source Step | Field | Target Step | Binding Syntax |
|---|---|---|---|
| | | | `{{cell(sourceStep.selection, 0, 'FieldName')}}` |

## Chart Type Rationale

| Widget | Chart Type Selected | Reason |
|---|---|---|
| | | |
| | | |

## Mobile Layout

**Mobile access required?** [ ] Yes  [ ] No

If Yes:
- [ ] Mobile Designer mode opened
- [ ] Widgets arranged in single-column mobile layout
- [ ] Tested on mobile device

## columnMap Audit

For any widget using dynamic bindings:

| Widget Name | Binding Type | columnMap → columns: [] Applied? |
|---|---|---|
| | measure / grouping / filter | [ ] Yes / [ ] N/A |

## Post-Build Verification Checklist

- [ ] All SAQL steps execute without errors in isolation
- [ ] Faceting tested: clicking a chart element filters other same-dataset widgets
- [ ] Bindings tested: cross-dataset filtering works as expected
- [ ] Dynamic measure/grouping selector tested: chart renders correct data for each selection
- [ ] columnMap fix confirmed for any dynamic binding widgets
- [ ] Mobile layout tested on a real mobile device (if applicable)
- [ ] Dashboard tested with a non-admin user account

## Notes

(Record any deviations from standard design and the rationale.)
