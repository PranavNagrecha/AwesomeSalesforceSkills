# Examples — Revenue Intelligence Setup

## Example 1: The deployable half of the prerequisites

**Context:** Standing up Revenue Intelligence in a new org. Before any dashboard renders usefully, forecasting has to be on, Einstein Opportunity Scoring has to be on, and the pivot fields have to be collecting history.

**Problem:** Teams treat "enable Revenue Intelligence" as one switch. It is at least three independent metadata settings plus a Setup step that is not deployable at all, and each fails silently in its own way — an empty waterfall, a missing insight, a forecast page with no rollups.

**Solution:** Deploy what is deployable, and list what is not.

`force-app/main/default/settings/Forecasting.settings-meta.xml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ForecastingSettings xmlns="http://soap.sforce.com/2006/04/metadata">
    <enableForecasts>true</enableForecasts>
    <globalQuotasSettings>
        <enableQuotas>true</enableQuotas>
    </globalQuotasSettings>
</ForecastingSettings>
```

`force-app/main/default/settings/OpportunityScore.settings-meta.xml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<OpportunityScoreSettings xmlns="http://soap.sforce.com/2006/04/metadata">
    <enableOpportunityScoring>true</enableOpportunityScoring>
</OpportunityScoreSettings>
```

A forecast type, one of the four you get:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ForecastingType xmlns="http://soap.sforce.com/2006/04/metadata">
    <developerName>Revenue_By_Close_Date</developerName>
    <masterLabel>Revenue (Close Date)</masterLabel>
    <active>true</active>
    <amount>true</amount>
    <quantity>false</quantity>
    <dateType>OpportunityCloseDate</dateType>
    <hasProductFamily>false</hasProductFamily>
</ForecastingType>
```

`sfdx-project.json`, pinned above the 53.0 restructuring:

```json
{
  "packageDirectories": [{ "path": "force-app", "default": true }],
  "sourceApiVersion": "67.0"
}
```

**Why it works:** Each setting is its own switch with its own default — `enableOpportunityScoring`'s "default value is false", and nothing about enabling Forecasts turns it on. `ForecastingType` is available in API version 52.0 and later and `globalQuotasSettings` in 53.0 and later, so the pinned `sourceApiVersion` is what makes the file deployable at all. The `dateType` value of `OpportunityCloseDate` is one of six the Metadata API documents (`OpportunityCloseDate`, `ProductDate`, `ScheduleDate`, `OLIMeasureCloseDateOnly`, `ProductDateOnly`, `ScheduleDateOnly`), and it is the one decision here that is expensive to change later.

**What this file cannot do:** turn on field history tracking for `Opportunity.Amount` and `Opportunity.CloseDate`. `CustomField.trackHistory` is documented as "Also available for standard object fields (picklist and lookup fields only) in API version 30.0 and later" — Amount is currency and CloseDate is date, so neither is covered. Those go in the manual section of the runbook.

---

## Example 2: A go-live readiness check that actually proves the prerequisites

**Context:** The environment is "done" according to the deploy log. Before training forty sales managers, someone should verify the intelligence has data to be intelligent about.

**Problem:** Every prerequisite in this domain fails silently. An empty waterfall looks identical whether history tracking was never enabled, was enabled last week (so there is no history yet), or is enabled and working with genuinely no changes in the period.

**Solution:** Four assertions, run as anonymous Apex against the target org, each of which distinguishes those cases.

```apex
// 1. Is stage history being written at all? OpportunityHistory rows are
//    created by the platform; zero rows in a 90-day window on a live org
//    means the pipeline is not moving or the org is not in use yet.
Integer stageRows = [
    SELECT COUNT() FROM OpportunityHistory
    WHERE CreatedDate = LAST_N_DAYS:90
];
System.debug('OpportunityHistory rows (90d): ' + stageRows);

// 2. Is FIELD history being written for the pivot fields? This is the one
//    that is not deployable, so it is the one most likely to be missing.
List<AggregateResult> byField = [
    SELECT Field field, COUNT(Id) c
    FROM OpportunityFieldHistory
    WHERE CreatedDate = LAST_N_DAYS:90
      AND Field IN ('Amount', 'CloseDate', 'StageName', 'ForecastCategoryName')
    GROUP BY Field
];
for (AggregateResult ar : byField) {
    System.debug(ar.get('field') + ' -> ' + ar.get('c'));
}
// Any of the four missing from this result = tracking is off for that field.

// 3. Are forecast types configured, and how many of the four are used?
// (Only Id/DeveloperName/IsActive are asserted here — check the object's own
//  field list in Object Manager before adding measure-specific columns.)
List<ForecastingType> types = [
    SELECT Id, DeveloperName, IsActive
    FROM ForecastingType
];
System.debug('Forecast types configured: ' + types.size() + ' of 4 -> ' + types);

// 4. Is Einstein scoring switched on? Only the setting is asserted here.
//    OpportunityScoreSettings.enableOpportunityScoring defaults to false, so a
//    silently-unscored org is usually a never-enabled org.
System.debug('Confirm Einstein Opportunity Scoring is enabled in Setup, then ' +
    'confirm scores are populating from the Opportunity page layout or the ' +
    'scoring related list in the target org — the score field/object name is ' +
    'documented on help.salesforce.com and is NOT asserted here.');
```

**Why it works:** Each check separates a distinct failure. Step 2 is the important one — it is the prerequisite that cannot be deployed, so it is the one that survives into production unnoticed. Step 3 makes the four-type ceiling visible before someone promises a fifth segmentation; the Metadata API is unambiguous that "The maximum number of forecast types is four." Step 4 is deliberately not a query: Einstein scoring needs closed-deal history before it produces anything, so an empty score column during week one is a timing observation and not a defect — and the API name of the score field is not something this package verifies.

Run this in the sandbox at the end of configuration and again in production on go-live day. Record the numbers — they are also the baseline against which "is adoption working" gets measured a quarter later.

---

## Anti-Pattern: Rebuilding the shipped pipeline views as custom reports

**What practitioners do:** Decide the shipped Pipeline Inspection view "doesn't have our fields", and build a parallel set of custom Opportunity reports with formula fields that approximate deal-change deltas.

**What goes wrong:** The deltas are the hard part, and hand-rolled versions get them subtly wrong — a report comparing today's Amount to a snapshot field updated by a nightly job misses intra-day changes, double-counts a deal edited twice, and cannot answer "changed since I last looked" for a manager who last looked on Tuesday. Meanwhile the shipped view keeps working and nobody uses it, so the org now maintains two answers to the same question and trusts neither.

**Correct approach:** Configure the shipped view first and find out what is genuinely missing. Most "our fields aren't there" complaints are a column configuration away. If a metric truly is absent, extend rather than replace — build the one additional component against the same underlying history objects, and leave deal-change detection to the feature that already does it correctly.
