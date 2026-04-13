# CRM Analytics Dashboard JSON — Work Template

Use this template when editing a CRM Analytics dashboard JSON body directly.

## Scope

**Skill:** `analytics-dashboard-json`

**Request summary:** (describe the change — e.g., "add cross-dataset binding from Account Industry selector to Opportunities chart" or "raise row limit on open opportunities table step")

---

## Context Gathered

Answer these before touching the dashboard JSON:

- **Dashboard ID:** `0FKxxxxxxxxxxxxxxxxx` (from the dashboard URL or Analytics Studio)
- **API version:** `vXX.X` (use the org's current API version)
- **Datasets involved:**

| Dataset Display Name | datasetId (0Fb...) | datasetVersionId (0Fc...) |
|---|---|---|
| (fill in) | (from GET /wave/datasets) | (currentVersionId from GET /wave/datasets) |

- **Step names to create or modify:** (list each step key in the `steps` map)
- **Binding source step(s):** (which step provides the selection or filter value)
- **Binding target step(s):** (which step consumes the binding in its SAQL query)
- **Row limit requirement:** Does any step need more than 2,000 rows? [ ] Yes / [ ] No
  - If yes, max rows needed: ___ (platform max is 10,000)

---

## Pre-Edit Snapshot

```bash
# Retrieve the current dashboard body before any changes
curl -H "Authorization: Bearer {ACCESS_TOKEN}" \
  "https://{INSTANCE}.salesforce.com/services/data/vXX.X/wave/dashboards/{DASHBOARD_ID}" \
  > dashboard_before.json
```

- **Snapshot saved:** [ ] Yes — file: `dashboard_before.json`
- **History snapshot count before edit:** (from GET /wave/dashboards/{id}/histories)

---

## Steps Map Changes

For each step being created or modified:

### Step: `{stepName}`

**Type:** `saql` / `soql`

**Purpose:** (what this step queries and why)

**Datasets referenced:**

```json
"datasets": [
  {
    "id": "0FbXXXXXXXXXXXXXXXX",
    "label": "{DisplayName}",
    "name": "{DisplayName}",
    "version": "0FcXXXXXXXXXXXXXXXX"
  }
]
```

**SAQL query:**

```saql
q = load "0FbXXXXXXXXXXXXXXXX/0FcXXXXXXXXXXXXXXXX";
q = filter q by ... ;
q = group q by ... ;
q = foreach q generate ... ;
q = order q by ... desc;
q = limit q {LIMIT};
q;
```

**Step-level limit:** `{LIMIT}` (must match the `limit q N` in the query above; max 10,000)

**Binding(s) embedded in query:**

| Binding expression | Source step | Field | Empty-string guard added? |
|---|---|---|---|
| `{{cell(sourceStep.selection, 0, "fieldName")}}` | `sourceStep` | `fieldName` | [ ] Yes / [ ] No |

---

## Widgets Map Changes

For each widget being created or modified:

### Widget: `{widgetName}`

**Type:** chart / table / filter / text / other

**Layout (pixels):**

```json
"layout": {
  "top": 0,
  "left": 0,
  "width": 400,
  "height": 300
}
```

**Data step:** `{stepName}` (must exist in the `steps` map)

**Parameters to set or change:** (describe the specific parameter changes, e.g., measures, dimensions, filters)

---

## State Changes

- **Default selections to pre-seed:** (list any `state` keys to set so bindings have a non-empty default on first load)
- **Global filter state:** (any global filter values applied at the dashboard level)

---

## PUT Operation

```bash
# PUT the modified dashboard body back
curl -X PUT \
  -H "Authorization: Bearer {ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  --data @dashboard_modified.json \
  "https://{INSTANCE}.salesforce.com/services/data/vXX.X/wave/dashboards/{DASHBOARD_ID}"
```

- **PUT response `lastModifiedDate`:** (record here)
- **History snapshot count after PUT:** (confirm a new snapshot was created)

---

## Validation Checklist

- [ ] All SAQL `load` statements use `"datasetId/datasetVersionId"` format (not display names)
- [ ] All `datasets` array entries have `"id"` matching `^0Fb[A-Za-z0-9]{15}$` and `"version"` matching `^0Fc[A-Za-z0-9]{15}$`
- [ ] Every step that needs more than 2,000 rows has `"limit"` on the step object AND `limit q N` in the SAQL query
- [ ] Every binding expression with `{{cell(...)}}` in a SAQL `filter` clause has an empty-string guard (`|| "" == "{{cell(...)}}""`)
- [ ] PUT body is the full dashboard JSON (not a partial update) — contains `steps`, `widgets`, and `state` at the top level
- [ ] A new history snapshot was confirmed after the PUT
- [ ] Each modified binding was tested end-to-end in the dashboard UI: with a user selection and without (empty/default state)
- [ ] `python3 scripts/check_analytics_dashboard_json.py --dashboard-file dashboard_modified.json` passes with no warnings

---

## Notes

(Record any deviations from the standard pattern, org-specific constraints, or issues encountered during the edit.)
