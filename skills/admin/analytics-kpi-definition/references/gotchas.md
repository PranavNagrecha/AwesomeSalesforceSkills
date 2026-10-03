# Gotchas: Analytics KPI Definition

Non-obvious behaviours that make a CRM Analytics KPI compute something other than what the register says. Each gotcha names its source. Claims that could not be confirmed from a fetched source carry an inline `UNVERIFIED (2026-10-03):` marker. "SAQL Guide" means the Analytics SAQL Developer Guide (Summer '26, https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/bi_dev_guide_saql.pdf); "Setup Guide" means the Analytics Platform Setup Guide (Spring '26); "Dashboard JSON Guide" means the Analytics Dashboard JSON Developer Guide (Summer '26).

## Gotcha 1: Target Join Keys Must Match Exactly, Including Case

**What happens:** Actuals carry `Region = "North America"` and the uploaded targets CSV carries `"north america"`. The attainment column is blank for that region with no error. SAQL string equality is case-sensitive, and identifiers are case-sensitive too, so a key that differs only in case does not match.

**When it occurs:** Targets uploaded by hand from spreadsheets, and keys such as Owner name, Region, Product Family, or Account Tier.

**How to avoid:** Record the exact key format in the KPI register, prefer Ids or picklist API values over display names, and normalise both sides with `lower()` in the recipe or query when case cannot be controlled (`lower("JAVA") == "java"`).

**Source:** SAQL Guide, SAQL Basic Elements ("SAQL identifiers are case-sensitive"); Comparison Operators (`==`: "String comparisons that use the equals operator are case-sensitive"; `matches` is not); String Functions, `lower()`.

---

## Gotcha 2: Dimensions Cannot Be Summed, And A "Count" Of A Dimension Is A Unique Count

**What happens:** A field stored as a dimension (postal code, year, a numeric-looking code) cannot be used with `sum()` or `avg()`, which take measure fields, so the formula fails. Worse, a count picked on a dimension in the user interface is not a row count: "a count on a dimension in the user interface calculates the number of unique dimension values," and the JSON shows `unique_<dimension_field_name>`. A "number of accounts" KPI built that way counts distinct accounts, not records.

**When it occurs:** KPIs designed from source-object field types instead of the dataset's measure and dimension classification, and counts built in the lens explorer.

**How to avoid:** Classify every formula field as measure or dimension from the dataset, not the source object. Write "row count" (`count()`) or "distinct count" (`unique()`) explicitly in the register. Reclassify numeric dimensions as measures in the recipe if they must be aggregated.

**Source:** SAQL Guide, Aggregate Functions (`avg()` "Returns the average of the values of a measure field"; `sum()`; `unique()`; `count()` "operates on the stream that is input to the group or cogroup statement"). Dashboard JSON Guide, parameters Properties, `measureField` (formulas `avg`, `max`, `min`, `sum`, `unique`; the dimension count note).

---

## Gotcha 3: Targets Belong In Their Own Dataset, Joined With A Left Outer Cogroup

**What happens:** Practitioners add target columns to the actuals dataset in a recipe. Fixed targets survive; targets that vary by owner, region, or quarter bloat the dataset, and every target change forces a full reload. The documented attainment pattern keeps quotas in their own dataset and joins them at query time.

**When it occurs:** Any KPI with dimension-specific targets.

**How to avoid:** Model a targets dataset with one row per grouping combination (Owner + Quarter + Region) and one target measure. Join it with a left outer cogroup from the targets side so every target row appears, and use `coalesce()` for groups with no actuals.

**Source:** SAQL Guide, cogroup, Example: Left Outer cogroup With coalesce (`q = group quota by 'Employee' left, opp by 'Employee';` and `trunc(coalesce(sum(opp.'Amount'),0)/sum(quota.'Quota')*100, 2) as 'Percent Attained'`).

---

## Gotcha 4: An Inner Cogroup Silently Drops Groups With No Matches

**What happens:** A win-rate KPI cogroups "all opportunities" with "won opportunities" by territory. The default cogroup is inner: "The resulting data stream only contains values that exist in both data streams. That is, unmatched records are dropped." Territories with no wins vanish from the KPI instead of showing 0%, so the overall rate looks better than it is.

**When it occurs:** Ratio KPIs built from two filtered streams, and actual-versus-target joins where some groups have no actuals.

**How to avoid:** Use a left outer cogroup from the stream that defines the population (`cogroup all_opps by 'Territory' left, won by 'Territory'`) and wrap the numerator in `coalesce(..., 0)`. Check the row count of the result against the number of territories.

**Source:** SAQL Guide, cogroup (inner, left outer, right outer, full outer; inner cogroup drops unmatched records; left outer returns null for missing values; tip to use `coalesce`).

---

## Gotcha 5: Whether A Blank Number Is Null Or Zero Depends On An Org Setting

**What happens:** An average revenue KPI is far too low because accounts with no billing count as zero. With null measure handling, a blank numeric value becomes null when no other default value is specified; without it, blanks take the column's default. The setting is "Allow null measure handling in datasets," on by default and not removable for orgs that set up CRM Analytics after Spring '17. Null dimensions are a separate setting ("Include null values in CRM Analytics queries").

**When it occurs:** Sparse measures (revenue, scores, durations) and older orgs set up before Spring '17.

**How to avoid:** For each measure in the register, record whether blank means "unknown" (null) or "zero," check the org's null handling settings, and filter the population explicitly ("accounts with at least one invoice") rather than relying on how blanks aggregate.

**Source:** SAQL Guide, SAQL Null Measures and Dimensions (null measure handling setting, Spring '17 default, null dimensions setting).

---

## Gotcha 6: One Currency, Fiscal Calendars, And Numeric Precision Need A Decision Before The Formula

**What happens:** A pipeline KPI in a multi-currency org adds amounts without conversion: CRM Analytics "doesn't convert to another currency." Quarter KPIs disagree with Salesforce reports because the org uses a custom fiscal year that was never imported (`AnalyticsSettings.enableWaveCustomFiscal`). Very large or very precise values overflow: more than 17 decimal places, or beyond 36,028,797,018,963,967, gives "unpredictable" results, including nulls or wrong sums. UNVERIFIED (2026-10-03): `AnalyticsSettings.enableWaveMulticurrency` (Beta, API 56.0+) suggests a multiple-currency option; the Setup Guide still lists multiple currencies as unsupported.

**When it occurs:** Global orgs, orgs with custom fiscal years, and KPIs on amounts stored in small units.

**How to avoid:** State the KPI's currency and the converted field it uses, enable and test custom fiscal year support before defining fiscal-period KPIs, and keep measure precision and scale inside the documented limits.

**Source:** Setup Guide, CRM Analytics Limitations, Localization and Internationalization (multiple currencies); CRM Analytics Limits, Dataset Field Limits (17 decimal places, maximum and minimum values, overflow behaviour). Metadata API Developer Guide, Version 67.0, AnalyticsSettings (`enableWaveCustomFiscal`: "lets admins import custom fiscal year definitions from Salesforce to Analytics"; `enableWaveMulticurrency`).

---

## Gotcha 7: Historical KPI Trends From Snapshots Are Capped

**What happens:** A team trends a report's KPI over time with a trended dataset and hits caps: 5 trended datasets per user, 100,000 rows per snapshot, 500,000 report rows for admins (100,000 for others), 5,000,000 rows per trended dataset, and 40 million snapshot rows per org per month. Trended rows also count toward the org's total row allocation.

**When it occurs:** KPIs whose history is not in the source data (pipeline snapshots, backlog levels).

**How to avoid:** Decide in the register whether history comes from source fields (close dates, history objects) or from snapshots, and size snapshot volume against the limits before promising multi-year trends.

**Source:** Setup Guide, CRM Analytics Limits, Trending Data Limits.

---

## Gotcha 8: Sparse Fields Behave Differently When A KPI Feeds Einstein Discovery

**What happens:** A KPI that depends on a sparsely filled field is reused as an Einstein Discovery outcome or predictor and the field's influence is weaker than expected. UNVERIFIED (2026-10-03): the earlier statement that fields below about 70% fill rate are silently dropped from Einstein Discovery feature selection was not found in the Einstein Discovery REST API Developer Guide or any other fetched source.

**When it occurs:** KPI registers later reused for predictive models.

**How to avoid:** Record each field's fill rate in the register and review it with the Einstein Discovery story's own field analysis before reuse.

**Source:** None confirmed; see the UNVERIFIED marker above. Einstein Discovery REST API Developer Guide (local corpus `knowledge/imports/bi-dev-guide-rest-sdd.md`) was searched for fill-rate rules without a match.
