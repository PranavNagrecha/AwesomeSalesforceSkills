# Examples — Collaborative Forecasts

## Example 1: Configuring Two Forecast Types for a Direct + Overlay Sales Model

**Context:** A SaaS company has two sales teams: Account Executives who own direct revenue, and Solutions Engineers who contribute to deals as overlays. Finance wants separate forecast views for each motion. The company uses Opportunity Revenue Splits to credit each rep.

**Problem:** Without separate Forecast Types, direct and overlay revenue are combined into a single forecast. Managers cannot see AE-attributable pipeline versus SE-attributed overlay separately. If a single Opportunity-based type is used, SE contributions are invisible.

**Solution:**

```
Forecast Type 1 — AE Direct Revenue
  Source Object:      Opportunity (Amount field)
  Hierarchy:          Role hierarchy
  Period Type:        Monthly
  Rollup Method:      Cumulative
  Active:             Yes

Forecast Type 2 — SE Overlay Splits
  Source Object:      Opportunity Splits (Revenue split type)
  Hierarchy:          Role hierarchy
  Period Type:        Monthly
  Rollup Method:      Cumulative
  Active:             Yes
```

Stage-to-category mapping (applies to both types — mapping is global):
```
Prospecting           → Pipeline
Qualification         → Pipeline
Needs Analysis        → Pipeline
Value Proposition     → Best Case
Id. Decision Makers   → Best Case
Perception Analysis   → Commit
Proposal/Price Quote  → Commit
Negotiation/Review    → Commit
Closed Won            → Closed
Closed Lost           → Omitted
```

Loading SE quotas for Forecast Type 2 via Data Loader:
```
Object: ForecastingQuota
Required fields:
  QuotaOwnerId       = <UserId of SE rep>
  StartDate          = 2025-01-01   (first day of period — must be exact)
  QuotaAmount        = 50000
  ForecastingTypeId  = <Id of "SE Overlay Splits" ForecastingType>
  CurrencyIsoCode    = USD
```

To retrieve the ForecastingTypeId before loading:
```soql
SELECT Id, DeveloperName, Name FROM ForecastingType
```

**Why it works:** Split-based types roll up only the split percentage credited to each rep, isolating SE overlay revenue from the AE's direct Amount. The two types appear as separate tabs on the Forecasts page. Cumulative rollup means the Commit column already includes Closed Won deals, which matches finance reporting expectations.

---

## Example 2: Diagnosing Missing Revenue After a Stage Mapping Change

**Context:** A sales ops admin added a new "Pilot" opportunity stage. After the update, the regional sales manager noticed roughly $2M of open pipeline disappeared from the forecast overnight.

**Problem:** The new "Pilot" stage was not explicitly mapped when created, so Salesforce assigned it to Omitted by default. Opportunities in the Pilot stage were excluded from all forecast rollup totals.

**Solution:**

1. Navigate to Setup > Forecasts Settings > Opportunity Stages in Forecasts.
2. Locate the "Pilot" stage in the mapping list.
3. Confirm it is mapped to Omitted (the default for newly created stages).
4. Change the mapping to the correct category — in this case, Best Case (represents active evaluation but not yet committed).
5. Save the mapping.
6. Refresh the Forecasts tab and confirm pipeline totals are restored.

```
Before fix:
  Pilot → Omitted   (excluded from all rollups — $2M invisible)

After fix:
  Pilot → Best Case (included in Pipeline, Best Case, and Commit cumulative rollups)
```

**Why it works:** Forecast category mapping is applied to all open opportunities in real time. Once the stage is remapped to a non-Omitted category, those opportunities re-enter all forecast rollups immediately — no data migration or adjustment is required.

---

## Anti-Pattern: Changing Rollup Method on a Live Forecast Type

**What practitioners do:** An admin switches a Forecast Type from single-category to cumulative rollup mid-quarter because managers complain the Commit column does not include Closed Won deals.

**What goes wrong:** Salesforce immediately and permanently deletes all existing manager adjustments and owner adjustments for that Forecast Type. The deletion happens silently — no confirmation dialog, no notification to affected managers, no export of existing values. If the team had been building adjustments for 6 weeks, all of that data is lost with no undo.

**Correct approach:**
1. Export all existing adjustments from the `ForecastingAdjustment` object via Data Loader before making any rollup method change.
2. Schedule the change at a low-impact time (e.g., start of a new quarter before any adjustments have been entered).
3. Communicate the change to all forecast managers before execution.
4. After switching, use the exported adjustment data as a reference to re-enter critical values if needed.
