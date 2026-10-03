# Examples — Analytics KPI Definition

## Example 1: Win Rate KPI with Target Attainment

**Context:** A sales operations team needs a "Win Rate by Region" KPI in CRM Analytics. The CFO wants to see actuals vs quarterly targets.

**Problem:** The developer builds a lens using a `count` of Closed Won Opportunities divided by total Opportunities without stakeholder sign-off. The VP of Sales disputes the formula — they count only Opportunities above $10K. The lens is rebuilt, but the targets dataset was never designed. Target attainment requires a complete rebuild.

**Solution:**
KPI register entry created before any lens build:
```
KPI Name: Win Rate by Region
Definition: Count of Opportunities with Stage=Closed Won AND Amount >= 10000
             divided by Count of Opportunities with CreatedDate IN reporting period AND Amount >= 10000
Measure: Opportunity count (derived by formula)
Dimension: Territory__c (Region grouping)
Formula (SAQL sketch, corrected 2026-10-03: field names need single quotes, and the
original inner cogroup dropped territories with no wins):
  q = load "OpportunityDataset";
  q = filter q by 'Amount' >= 10000;
  q_won = filter q by 'StageName' == "Closed Won";
  result = cogroup q by 'Territory__c' left, q_won by 'Territory__c';
  result = foreach result generate q.'Territory__c' as 'Territory__c',
           count(q) as 'total', coalesce(count(q_won), 0) as 'won',
           coalesce(count(q_won), 0) / count(q) * 100 as 'WinRate';

Target model: Separate "SalesTargets" dataset with columns: Territory__c, Quarter__c, WinRate_Target
Join key: Territory__c (exact string match required — verify capitalization)
```

**Why it works:** The formula, inclusion/exclusion criteria, and target join model are agreed upon and documented before build, eliminating mid-project formula disputes and the targets dataset retrofit.

---

## Example 2: Revenue per Account KPI with Sparse Field Risk

**Context:** A customer success team wants a "Revenue per Account" KPI in CRM Analytics. The dataset has a custom field `Total_Revenue__c` that has a fill rate of about 55% (populated only for accounts with billing activity).

**Problem:** The developer builds the KPI using `avg(Total_Revenue__c)` in the lens. The average is skewed because 45% of records have null revenue (treated as 0 in some aggregation contexts). The dashboard shows misleadingly low average revenue.

**Solution:**
KPI register documents the sparse field risk:
```
KPI Name: Revenue per Active Account
Definition: Sum of Total_Revenue__c for accounts with at least one closed invoice in the past 12 months
Field used: Total_Revenue__c (55% fill rate — NULL = no billing activity, NOT zero revenue)
Filter requirement: Apply HasInvoice__c == true filter before aggregation to exclude non-billed accounts
Aggregation: sum(Total_Revenue__c) / count(distinct AccountId) for filtered set
Benchmark: Industry average $45K/account (source: Gartner 2025)
```

**Why it works:** Documenting the fill rate and the correct filter in the KPI register prevents the developer from including null-revenue accounts in the denominator, which would produce an artificially low average.

---

## Anti-Pattern: Building Lens Before KPI Register Is Complete

**What practitioners do:** They accept a stakeholder request for "a dashboard showing pipeline and win rate" and immediately start building CRM Analytics lenses and configuring dataset fields.

**What goes wrong:** Stakeholders see the dashboard and dispute the formula — "win rate should only count opps above $50K" or "pipeline should exclude Partner-sourced." Each change requires rebuilding the lens formulas and potentially re-joining datasets. The targets dataset was never designed because no one asked about target attainment until the dashboard was shown.

**Correct approach:** Complete the KPI register before any lens is built. The KPI register requires stakeholder sign-off on formulas, inclusion/exclusion criteria, dimension groupings, and target attainment model. The dashboard builder uses the register as an authoritative spec.

---

## Example 3: A KPI Register Entry, Its Targets Dataset, And The Attainment Query

**Context:** Sales leadership wants "Quarterly Bookings Attainment by Territory." Targets come from Finance as a spreadsheet each quarter. The register entry, the targets file format, and the query are agreed before any lens is built.

**The register entry** (`docs/analytics/kpi-register.md`):

| Field | Value |
|---|---|
| KPI | Quarterly Bookings Attainment by Territory |
| Definition | Sum of `Amount` on Opportunities with `StageName` = "Closed Won" and close date in the quarter, divided by the territory's quarterly target |
| Count rule | Sum of a measure (`sum('Amount')`); no counts |
| Population | Every territory with a target, including territories with no bookings (shown as 0%) |
| Blank rule | Blank `Amount` is excluded; targets are never blank |
| Currency | Corporate currency (CRM Analytics does not convert currencies) |
| Calendar | Fiscal quarter; custom fiscal year support enabled and tested |
| Targets | `SalesTargets` dataset, one row per Territory and Quarter, owner: Sales Finance |
| Join key | `Territory` = Territory picklist API value, exact case |
| Approved by | VP Sales and CFO, 2026-10-03 |

**The targets file and its metadata.** `SalesTargets.csv`:

```text
Territory,Quarter,Target_Amount
NA_East,2026-Q3,1250000.00
NA_West,2026-Q3,1100000.00
EMEA_North,2026-Q3,800000.00
```

`SalesTargets.json`, the metadata file uploaded with the CSV (External Data API format):

```json
{
  "fileFormat": {
    "charsetName": "UTF-8",
    "fieldsDelimitedBy": ",",
    "fieldsEnclosedBy": "\"",
    "linesTerminatedBy": "\n",
    "numberOfLinesToIgnore": 1
  },
  "objects": [
    {
      "connector": "SalesFinanceCSV",
      "fullyQualifiedName": "SalesTargets",
      "label": "Sales Targets",
      "name": "SalesTargets",
      "fields": [
        { "fullyQualifiedName": "SalesTargets.Territory", "label": "Territory", "name": "Territory", "type": "Text", "isSystemField": false, "isUniqueId": false, "isMultiValue": false },
        { "fullyQualifiedName": "SalesTargets.Quarter", "label": "Quarter", "name": "Quarter", "type": "Text", "isSystemField": false, "isUniqueId": false, "isMultiValue": false },
        { "fullyQualifiedName": "SalesTargets.Target_Amount", "label": "Target Amount", "name": "Target_Amount", "type": "Numeric", "precision": 18, "scale": 2, "isSystemField": false, "isUniqueId": false }
      ]
    }
  ]
}
```

The keys (`fileFormat`, `charsetName`, `fieldsDelimitedBy`, `fieldsEnclosedBy`, `linesTerminatedBy`, `numberOfLinesToIgnore`, `objects`, `connector`, `fullyQualifiedName`, `label`, `name`, `fields`, `type`, `precision`, `scale`, `isSystemField`, `isUniqueId`, `isMultiValue`) come from the Analytics External Data API Developer Guide's JSON example. In the text extracted from the Summer '26 PDF, that example is missing commas after `fieldsEscapedBy` and `linesTerminatedBy` and has a trailing comma after `scale`, so copying it verbatim fails to parse; the file above is valid JSON. `Target_Amount` has no `defaultValue`, so with null measure handling a blank target stays null instead of becoming 0. Upload with `InsightsExternalData` (`Operation` = `Overwrite` each quarter) or the CSV upload in Data Manager. UNVERIFIED (2026-10-03): precision 18 with scale 2 was chosen to stay well inside the documented 17-decimal-place and maximum-value limits; confirm against the guide's precision rules before loading.

**The attainment query** (pattern from the SAQL Guide's left outer cogroup with `coalesce()` example):

```sql
quota = load "SalesTargets";
quota = filter quota by 'Quarter' == "2026-Q3";
opp = load "OpportunityDataset";
opp = filter opp by 'StageName' == "Closed Won" && 'Close_Fiscal_Quarter' == "2026-Q3";
q = group quota by 'Territory' left, opp by 'Territory';
q = foreach q generate quota.'Territory' as 'Territory',
    sum(quota.'Target_Amount') as 'Target',
    coalesce(sum(opp.'Amount'), 0) as 'Actual',
    trunc(coalesce(sum(opp.'Amount'), 0) / sum(quota.'Target_Amount') * 100, 2) as 'Percent_Attained';
q = order q by 'Percent_Attained' asc;
q = limit q 2000;
```

UNVERIFIED (2026-10-03): `Close_Fiscal_Quarter` is an assumed derived dimension in the Opportunity dataset; build it in the recipe from the fiscal calendar, or filter on the dataset's date fields instead.

**Why it works:** the register states how to count, who is in the population, what blanks mean, and which currency and calendar apply; the targets file is valid and typed; and the left outer cogroup from the targets side keeps territories with no bookings at 0% instead of dropping them.

