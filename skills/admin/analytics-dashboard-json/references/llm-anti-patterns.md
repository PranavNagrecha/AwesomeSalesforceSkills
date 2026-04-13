# LLM Anti-Patterns — CRM Analytics Dashboard JSON

Common mistakes AI coding assistants make when generating or advising on CRM Analytics dashboard JSON.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Referencing Datasets by Name Instead of datasetId/datasetVersionId

**What the LLM generates:** SAQL step definitions that reference datasets using the human-readable display name in the `load` statement and a name-based `id` field in the `datasets` array:

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

```saql
q = load "Opportunities";
```

**Why it happens:** LLMs are trained on documentation examples and forum posts that use display names for brevity. The Salesforce UI also uses display names, so training data disproportionately shows names rather than IDs. The LLM correctly associates the dataset with its name but does not know that production-grade SAQL requires the org-specific ID pair.

**Correct pattern:**

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

**Detection hint:** Search the generated SAQL step's `load` statement for the pattern `load "[A-Za-z]` — if the first character after the opening quote is a letter (rather than `0Fb`), the step is using a name-based reference. Also flag any `datasets` entry where `"id"` does not match the pattern `^0Fb[A-Za-z0-9]{12,}$`.

---

## Anti-Pattern 2: Omitting the Step-Level `limit` Property

**What the LLM generates:** SAQL step definitions that include a `limit` clause in the SAQL query string but do not include the `limit` property on the step object itself:

```json
"myStep": {
  "type": "saql",
  "query": "q = load \"0Fb.../0Fc...\"; q = limit q 5000; q;",
  "datasets": [...]
}
```

**Why it happens:** LLMs conflate the SAQL query language `limit` clause with the step object's `limit` property. They often generate only the SAQL clause because that is the more visible pattern in SAQL documentation and examples. The step-level property is a JSON key that appears in dashboard JSON documentation separately from SAQL language references.

**Correct pattern:**

```json
"myStep": {
  "type": "saql",
  "query": "q = load \"0Fb.../0Fc...\"; q = limit q 10000; q;",
  "datasets": [...],
  "limit": 10000
}
```

**Detection hint:** For any step object of `"type": "saql"` that has a `limit` clause in the query string, verify that the step object also has a top-level `"limit"` key. Flag step objects missing `"limit"` when the query string contains `limit q`.

---

## Anti-Pattern 3: Generating a Partial PUT Body Instead of Full Dashboard JSON

**What the LLM generates:** When asked to modify a specific step or widget, the LLM produces only the modified object (e.g., just the step definition) and instructs the practitioner to PUT it directly:

```json
{
  "myStep": {
    "type": "saql",
    "query": "..."
  }
}
```

with instructions to PUT this to `/wave/dashboards/{id}`.

**Why it happens:** LLMs pattern-match on REST API PATCH semantics from other Salesforce APIs (e.g., Composite API, SObject PATCH). CRM Analytics' dashboard PUT does not support partial updates — it replaces the entire body. LLMs do not consistently distinguish the dashboard PUT from other partial-update patterns.

**Correct pattern:**

Always GET the full dashboard body first, modify the relevant section in memory, and PUT the complete body:

```
GET /services/data/vXX.X/wave/dashboards/{id}
→ modify steps["myStep"] in the full response body
PUT /services/data/vXX.X/wave/dashboards/{id}
  Body: { ...full dashboard body with modification... }
```

**Detection hint:** If the LLM produces a JSON object that contains only a `steps` key or only a `widgets` key without a `state` key alongside it, it is likely generating a partial body. Full dashboard JSON always contains all three top-level sections: `steps`, `widgets`, and `state`.

---

## Anti-Pattern 4: Not Handling the Empty Binding Case in SAQL Filters

**What the LLM generates:** A SAQL filter that uses a binding directly in a `where` clause without accounting for the empty-string case:

```saql
q = filter q by 'Industry' == "{{cell(industryStep.selection, 0, "Industry")}}";
```

**Why it happens:** LLMs generate the happy-path binding expression correctly but do not model the runtime state where no user selection is active. The empty-binding behavior (returns `""`) is documented in the bindings guide but is a secondary behavior that LLMs do not consistently include in generated filters.

**Correct pattern:**

Handle the empty-string case explicitly so the filter is skipped when no selection is active:

```saql
q = filter q by ('Industry' == "{{cell(industryStep.selection, 0, "Industry")}}" || "" == "{{cell(industryStep.selection, 0, "Industry")}}");
```

Or pre-seed the `state` object with a default selection so the binding always resolves to a non-empty value.

**Detection hint:** Any SAQL `filter` clause that embeds a `{{cell(...)}}` binding without a corresponding `|| "" ==` guard or equivalent empty-check is a candidate for the empty-binding bug.

---

## Anti-Pattern 5: Using Faceting Syntax for Cross-Dataset Filtering

**What the LLM generates:** Instructions to enable faceting between two widgets that are backed by different datasets, or JSON that attempts to configure faceting (`"isFacet": true`) on a widget connected to a different dataset than the filter source:

```json
"widgets": {
  "oppChart": {
    "type": "chart",
    "parameters": {
      "isFacet": true
    }
  }
}
```

**Why it happens:** LLMs correctly know that faceting enables cross-widget filtering in CRM Analytics but do not consistently enforce the constraint that faceting only works within the same dataset. They generalize faceting as a universal cross-widget mechanism, conflating it with explicit step bindings.

**Correct pattern:**

Faceting works only between widgets that share the same underlying dataset. For cross-dataset filtering, use explicit step bindings via mustache expressions in the target step's SAQL query:

```json
"targetStep": {
  "type": "saql",
  "query": "q = load \"0Fb.../0Fc...\"; q = filter q by 'Account.Industry' == \"{{cell(sourceStep.selection, 0, \\\"Industry\\\")}}\"; q;",
  "datasets": [...]
}
```

**Detection hint:** If a widget's `parameters` include `"isFacet": true` and the widget's data step references a different dataset than the filter source step, the faceting configuration will not work as intended. Check that all faceted widgets share the same primary dataset.
