# Examples — CRM Analytics Dashboard JSON

## Example 1: Cross-Dataset Binding — Industry Filter Driving an Opportunities Chart

**Scenario:** A dashboard has a list-selector widget backed by an Accounts dataset, and a bar chart backed by an Opportunities dataset. The user wants selecting an Industry in the list to filter the Opportunities chart.

**Problem:** Faceting (automatic cross-widget filtering) only works within the same dataset. Without JSON editing, the list selector cannot drive the Opportunities chart because the two steps reference different datasets.

**Solution:**

Step 1 — Define the source step (Accounts dataset, exposes Industry as a selectable field):

```json
"accountIndustryStep": {
  "type": "saql",
  "query": "q = load \"0FbXXXXXXXXXXXXX/0FcXXXXXXXXXXXXX\"; q = group q by 'Industry'; q = foreach q generate 'Industry' as 'Industry', count() as 'count'; q = order q by 'count' desc; q = limit q 50; q;",
  "datasets": [
    {
      "id": "0FbXXXXXXXXXXXXX",
      "label": "Accounts",
      "name": "Accounts",
      "version": "0FcXXXXXXXXXXXXX"
    }
  ],
  "selectMode": "single",
  "selectionFields": ["Industry"],
  "limit": 50
}
```

Step 2 — Define the target step (Opportunities dataset, conditionally filtered by the binding):

```json
"oppsByIndustryStep": {
  "type": "saql",
  "query": "q = load \"0FbYYYYYYYYYYYYY/0FcYYYYYYYYYYYYY\"; q = filter q by 'Account.Industry' == \"{{cell(accountIndustryStep.selection, 0, \"Industry\")}}\"; q = group q by 'StageName'; q = foreach q generate 'StageName' as 'StageName', sum('Amount') as 'TotalAmount'; q = order q by 'TotalAmount' desc; q = limit q 2000; q;",
  "datasets": [
    {
      "id": "0FbYYYYYYYYYYYYY",
      "label": "Opportunities",
      "name": "Opportunities",
      "version": "0FcYYYYYYYYYYYYY"
    }
  ],
  "limit": 2000
}
```

Step 3 — In the bar chart widget's `parameters`, reference `oppsByIndustryStep` for its data source. No additional binding is needed at the widget level — the binding is embedded in the SAQL query string.

**Why it works:** The mustache expression `{{cell(accountIndustryStep.selection, 0, "Industry")}}` is evaluated at render time against the current selection state. When the user picks "Technology" in the list selector, the binding resolves to `"Technology"` and the Opportunities step re-runs with that filter. When no selection exists, the binding returns an empty string; the `==` comparison then either returns no rows or behaves as a no-op depending on the data — test this edge case explicitly and handle it in the SAQL if needed.

---

## Example 2: Raising the SAQL Row Limit for a Full-Population Table

**Scenario:** A dashboard contains a table widget displaying all open Opportunities for a territory. The territory has 3,400 open opportunities but the table only shows 2,000 rows, with no indication that results are truncated.

**Problem:** The step's `limit` property was not set explicitly, so the platform applied the default of 2,000 rows. The SAQL query also has no `limit` clause, but that alone does not override the step-level default.

**Solution:**

Before (broken — silently truncated):

```json
"openOppsStep": {
  "type": "saql",
  "query": "q = load \"0FbXXXXXXXXXXXXX/0FcXXXXXXXXXXXXX\"; q = filter q by 'IsClosed' == \"false\"; q = foreach q generate 'Name' as 'Name', 'Amount' as 'Amount', 'CloseDate' as 'CloseDate'; q;",
  "datasets": [
    {
      "id": "0FbXXXXXXXXXXXXX",
      "label": "Opportunities",
      "name": "Opportunities",
      "version": "0FcXXXXXXXXXXXXX"
    }
  ]
}
```

After (correct — explicit limit on both step object and SAQL query):

```json
"openOppsStep": {
  "type": "saql",
  "query": "q = load \"0FbXXXXXXXXXXXXX/0FcXXXXXXXXXXXXX\"; q = filter q by 'IsClosed' == \"false\"; q = foreach q generate 'Name' as 'Name', 'Amount' as 'Amount', 'CloseDate' as 'CloseDate'; q = limit q 10000; q;",
  "datasets": [
    {
      "id": "0FbXXXXXXXXXXXXX",
      "label": "Opportunities",
      "name": "Opportunities",
      "version": "0FcXXXXXXXXXXXXX"
    }
  ],
  "limit": 10000
}
```

**Why it works:** The `limit` property on the step object controls how many rows the platform will surface to widgets and bindings. The `limit` clause in the SAQL query string controls how many rows the SAQL engine returns from the dataset. Both must be set; setting only one is not sufficient to guarantee the higher row count is returned. The platform hard cap is 10,000 per step regardless of what value is supplied.

---

## Anti-Pattern: Referencing a Dataset by Name Instead of ID

**What practitioners do:** When writing or editing a SAQL step, they copy the dataset's display name from the Analytics Studio UI and use it as the dataset reference in the `datasets` array `id` field, or embed the name directly in the SAQL `load` statement:

```json
"datasets": [
  {
    "id": "Opportunities",
    "label": "Opportunities",
    "name": "Opportunities",
    "version": ""
  }
]
```

or in the SAQL query:

```
q = load "Opportunities";
```

**What goes wrong:** In the authoring org, this may resolve correctly because CRM Analytics performs a name-based lookup as a fallback. However, when the dashboard is deployed to another org (sandbox, production, or a different sandbox), dataset IDs differ. The name-based lookup either fails silently (step returns zero rows) or resolves to the wrong dataset version. There is no error message in the dashboard UI — the affected widgets simply show empty or stale data.

**Correct approach:** Always retrieve the `datasetId` and `datasetVersionId` from `GET /services/data/vXX.X/wave/datasets` before constructing SAQL steps. Use these IDs in both the `load` statement and the `datasets` array:

```json
"datasets": [
  {
    "id": "0FbXXXXXXXXXXXXX",
    "label": "Opportunities",
    "name": "Opportunities",
    "version": "0FcXXXXXXXXXXXXX"
  }
]
```

```saql
q = load "0FbXXXXXXXXXXXXX/0FcXXXXXXXXXXXXX";
```
