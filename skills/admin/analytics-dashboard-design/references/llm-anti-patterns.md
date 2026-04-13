# LLM Anti-Patterns — CRM Analytics Dashboard Design

Common mistakes AI coding assistants make when generating or advising on CRM Analytics dashboard design.

## Anti-Pattern 1: Leaving columnMap Static with Dynamic Bindings

**What the LLM generates:** Dashboard JSON with a binding that changes the measure field, but the `columnMap` property is still hardcoded to the original measure column name.

**Why it happens:** LLMs generate dashboard JSON templates based on static examples. They add the binding syntax correctly but do not know that the `columnMap` must be cleared when the binding dynamically changes what columns the SAQL returns.

**Correct pattern:**

```json
// WRONG — static columnMap breaks dynamic binding
"columnMap": {
  "measures": ["amount_sum"]
}

// CORRECT — empty columns array allows dynamic column mapping
"columns": []
```

Any widget that uses a binding to inject a dynamic measure name or grouping field must have `columnMap` removed and replaced with `"columns": []`.

**Detection hint:** Dashboard JSON that includes both a selection/results binding on a measure or grouping AND a static `columnMap` mapping the original column name.

---

## Anti-Pattern 2: Recommending Faceting for Cross-Dataset Dashboard Filtering

**What the LLM generates:** "Enable faceting on all your chart widgets. When a user clicks on one chart, the selection will filter the other charts on the dashboard."

**Why it happens:** Faceting sounds like a universal dashboard filtering feature. The dataset-boundary restriction is not obvious from its description.

**Correct pattern:**

```
Faceting: Use ONLY when all participating widgets query the SAME dataset.
Bindings: Required for filtering across DIFFERENT datasets.

For cross-dataset filtering in dashboard JSON:
"filters": [
  ["FieldName", "{{cell(sourceStep.selection, 0, 'FieldName')}}", "=="]
]
```

**Detection hint:** Any recommendation to use faceting on a dashboard that references multiple datasets.

---

## Anti-Pattern 3: Using SOQL Syntax in SAQL Dashboard Steps

**What the LLM generates:** `SELECT StageName, SUM(Amount) FROM Opportunity GROUP BY StageName`

**Why it happens:** LLMs default to SQL/SOQL syntax, which is far more prevalent in training data than SAQL.

**Correct pattern:**

```saql
q = load "OpportunityDataset";
q = group q by 'StageName';
q = foreach q generate 'StageName' as 'StageName', sum('Amount') as 'amount_sum';
q = limit q 2000;
```

SAQL is a pipeline language — every statement is a named stream assignment. SQL syntax (SELECT/FROM/WHERE/GROUP BY) causes immediate parse errors in CRM Analytics steps.

**Detection hint:** Any SQL keyword sequence (SELECT, FROM, WHERE, GROUP BY) in a SAQL/dashboard step context.

---

## Anti-Pattern 4: Not Mentioning columnMap When Explaining Dashboard Bindings

**What the LLM generates:** A complete tutorial on selection bindings — how to write the mustache syntax, how to add filters to steps, how to create selector widgets — without mentioning that dynamic measure or grouping bindings require clearing `columnMap`.

**Why it happens:** Binding tutorials often focus on the binding syntax itself. The `columnMap` interaction is a separate, less-documented consequence.

**Correct pattern:**

When explaining any binding that changes a chart's measure or grouping:
```
Important: If this binding changes what measure or grouping field the chart queries,
you must also update the widget's columnMap in dashboard JSON:
- Remove the columnMap property
- Add "columns": []

Without this change, the chart will silently render zero values.
```

**Detection hint:** Any explanation of bindings that change measure/grouping without mentioning the columnMap requirement.

---

## Anti-Pattern 5: Claiming Mobile Layout Inherits from Desktop Automatically

**What the LLM generates:** "Once you build your desktop dashboard, mobile users can access it — CRM Analytics automatically adjusts the layout for mobile screens."

**Why it happens:** Many BI tools support responsive layout that automatically adapts to screen size. CRM Analytics does not — mobile and desktop are completely separate layout canvases.

**Correct pattern:**

```
CRM Analytics mobile layout is SEPARATE from desktop layout.
Steps to configure mobile:
1. Open the Dashboard in Designer
2. Click the phone icon to switch to Mobile mode
3. Drag and resize widgets on the mobile canvas
4. Mobile canvas uses single-column layout — stack KPI widgets top to bottom
5. Save the mobile layout
Without step 2-5, mobile users see a zoomed-out desktop layout.
```

**Detection hint:** Any claim that CRM Analytics "automatically adjusts" or "is responsive" for mobile without mobile canvas configuration.
