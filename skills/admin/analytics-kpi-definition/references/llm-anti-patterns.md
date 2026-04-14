# LLM Anti-Patterns — Analytics KPI Definition

Common mistakes AI coding assistants make when generating or advising on CRM Analytics KPI definition. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Confusing KPI Definition with Dashboard Tile Configuration

**What the LLM generates:** When asked "define the Win Rate KPI for CRM Analytics," the LLM outputs dashboard configuration steps — "add a KPI tile, set the measure to Opportunity.Amount, select the chart type, configure the color threshold" — skipping the formula definition and stakeholder sign-off phase entirely.

**Why it happens:** LLMs associate "CRM Analytics KPI" with the visible end result (a KPI widget in a dashboard). They jump to implementation without modeling that KPI definition is a pre-build BA requirements task.

**Correct pattern:**
```
KPI definition is a pre-build artifact:
Name: Win Rate
Formula: count(Stage='Closed Won') / count(all) for Opportunities in period
Dimension: Territory__c
Target model: separate SalesTargets dataset, joined by Territory__c
Stakeholder sign-off required before development
```

**Detection hint:** Output begins with dashboard or lens configuration steps rather than formula definition, inclusion/exclusion criteria, and dimension specification.

---

## Anti-Pattern 2: Recommending Standard Reports for KPI Target Attainment

**What the LLM generates:** "Create a custom report type with Opportunities and add a formula column for Win Rate. You can add target values as a custom field on the Opportunity object."

**Why it happens:** LLMs default to standard Salesforce Reports for KPI work because Reports are the dominant pattern in training data. They don't model CRM Analytics's separate targets dataset pattern.

**Correct pattern:**
```
CRM Analytics KPI target attainment:
1. Create a separate CRM Analytics dataset called "SalesTargets"
2. Load target values via CSV or External Data API with dimension columns matching actuals
3. Join at query time using SAQL cogroup on matching dimension keys
4. Compute attainment: count(won) / count(total) vs Target from targets dataset
Standard Reports cannot model multi-dimensional attainment tracking in CRM Analytics.
```

**Detection hint:** Answer recommends standard Reports, custom fields on objects, or formula fields as the mechanism for KPI target attainment.

---

## Anti-Pattern 3: Treating Dimension Fields as Measures in SAQL

**What the LLM generates:** SAQL queries that apply SUM() or AVG() to a field that is likely configured as a Dimension in the dataset:
```saql
q = load "OpportunityDataset";
result = foreach q generate sum(CloseMonth) as TotalCloseMonth; // CloseMonth is a dimension
```

**Why it happens:** LLMs generate SAQL based on the field name and apparent data type, without knowing how the field is configured in the CRM Analytics dataset schema. Fields like "CloseMonth," "FiscalYear," or "Score" look numeric but may be configured as dimensions.

**Correct pattern:**
```
Before writing SAQL formulas:
1. Check dataset field types in CRM Analytics Data Manager
2. Only apply aggregation functions (sum/avg/min/max) to Measure-type fields
3. Dimension fields can only appear in GROUP BY / foreach generate clauses
4. If a numeric field is configured as a dimension, update the dataset recipe to mark it as a measure
```

**Detection hint:** SAQL uses SUM(), AVG(), or COUNT(distinct) on fields whose names suggest categorical data (Month, Year, Quarter, Region, Score, Code).

---

## Anti-Pattern 4: Storing Targets Inline in Actuals Dataset

**What the LLM generates:** "Add a Target_Revenue__c column to the Opportunity dataset recipe with a fixed value based on Region" — modeling targets as columns in the source dataset.

**Why it happens:** LLMs model datasets as monolithic tables where all data lives in one place. They don't model the separate-dataset join pattern required for dimension-specific, period-varying targets.

**Correct pattern:**
```
Target attainment data model:
- Actuals dataset: source data (Opportunities)
- Targets dataset: separate CRM Analytics dataset
  Columns: Region__c, Quarter__c, Target_Revenue
  Load: External Data API or CSV upload each period
- Join: SAQL cogroup actuals by Region__c, targets by Region__c
  Result: actual_revenue, target_revenue per Region per Quarter
```

**Detection hint:** SAQL or recipe contains hardcoded target values or target columns added to the source dataset rather than a separate joined dataset.

---

## Anti-Pattern 5: Skipping Measure vs Dimension Validation in KPI Design

**What the LLM generates:** A KPI register that lists field names without specifying whether they are Measures or Dimensions in the CRM Analytics dataset, leaving the formula type implicit.

**Why it happens:** LLMs treat CRM Analytics datasets as standard database tables where any numeric field can be aggregated. They don't model that CRM Analytics enforces a strict Measure/Dimension distinction at the dataset level.

**Correct pattern:**
```
KPI register must include for each field:
- Field name: Amount
- Dataset field type: Measure (confirmed in Data Manager)
- Aggregation to apply: SUM
- Grouping fields (dimensions): Region__c, CloseQuarter__c (both Dimension type)
Any field whose type is not confirmed as a Measure CANNOT be aggregated.
```

**Detection hint:** KPI register or formula documentation lists fields without "Measure" or "Dimension" type designation.
