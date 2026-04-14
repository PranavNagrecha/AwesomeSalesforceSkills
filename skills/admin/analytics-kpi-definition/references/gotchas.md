# Gotchas — Analytics KPI Definition

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Targets Dataset Join Key Must Be Exact String Match

**What happens:** When joining a targets dataset to an actuals dataset in SAQL for attainment tracking, the join key values must be exact string matches including case sensitivity. If the actuals dataset has `Region = "North America"` and the targets dataset has `Region = "north america"` (lowercase), the join returns nulls for those rows. The KPI attainment column appears blank for affected regions with no error message.

**When it occurs:** When targets datasets are manually uploaded via CSV and the uploader uses different capitalization than the values in the actuals dataset. Common with dimension values like Owner Name, Region, Product Family, and Account Tier.

**How to avoid:** Document the exact string format for all join key fields in the KPI register. Establish a canonical value list (e.g., Region picklist values) and enforce that the targets dataset CSV uses the same values. Consider applying a SAQL LOWER() transformation if case consistency cannot be guaranteed.

---

## Gotcha 2: Dimension Fields Cannot Be Aggregated — Silent SAQL Error

**What happens:** A field configured as a Dimension in the CRM Analytics dataset editor cannot be used in SUM(), AVG(), or COUNT(distinct) aggregations in SAQL, even if the field contains numeric-looking data. The SAQL query fails at runtime with an error that can be cryptic. The developer who did not check the dataset schema is surprised because the field appears numeric in the source data.

**When it occurs:** When a field is configured as a Dimension in the dataset recipe or dataflow (common for string fields that look numeric, like Postal Code, Year, or Integer codes). Practitioners who query the dataset without checking the schema assume all numeric fields are measures.

**How to avoid:** Before finalizing KPI formulas, verify the field type (Measure vs Dimension) in the CRM Analytics dataset editor. For fields that should be measures but are configured as dimensions, update the dataset recipe to reconfigure the field as a numeric measure and reload the dataset.

---

## Gotcha 3: KPI Attainment Cannot Be Stored in the Source Dataset

**What happens:** Practitioners attempt to add target values directly to the actuals dataset (e.g., adding a Target_Amount column to the Opportunity dataset in a recipe). This works for fixed targets but breaks for dimension-specific targets (targets that vary by Owner, Region, or Quarter). The dataset bloats with redundant target data, and updating targets requires re-running the full recipe and dataset reload.

**When it occurs:** When a KPI requires dimension-specific targets and the practitioner models them as additional columns in the actuals dataset instead of a separate targets dataset.

**How to avoid:** Model target attainment as a separate targets dataset joined at query time. The targets dataset has one row per dimension combination (Owner + Quarter + Region) with a single target measure column. SAQL cogroup or recipe join at query time is the correct pattern. Targets can then be updated by replacing the targets dataset alone without touching the actuals dataset.
