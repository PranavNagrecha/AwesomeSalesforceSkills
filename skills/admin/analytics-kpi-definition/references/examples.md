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
Formula (SAQL sketch):
  q = load "OpportunityDataset";
  q = filter q by Amount >= 10000;
  q_won = filter q by Stage == "Closed Won";
  result = cogroup q by Territory__c, q_won by Territory__c;
  result = foreach result generate Territory__c, count(q) as total, count(q_won) as won,
           count(q_won) / count(q) * 100 as WinRate;

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
