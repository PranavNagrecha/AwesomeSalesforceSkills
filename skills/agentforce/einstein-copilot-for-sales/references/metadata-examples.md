# Metadata Examples: Einstein Copilot for Sales

The Sales Cloud Einstein features in this skill are switched on through settings metadata, and their outputs are queryable standard objects. This file gives a deployable settings bundle, the readiness and verification queries, and the order to run them in.

## Example 1: Enable Opportunity Scoring, Activity Capture and Pipeline Inspection as settings

**Context.** A sales org wants the three features enabled the same way in every sandbox and in production, with Activity Capture sharing locked down before any mail syncs.

### Opportunity Scoring

**File path:** `force-app/main/default/settings/OpportunityScore.settings-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<OpportunityScoreSettings xmlns="http://soap.sforce.com/2006/04/metadata">
    <enableOpportunityScoring>true</enableOpportunityScoring>
</OpportunityScoreSettings>
```

`OpportunityScoreSettings` is stored in `OpportunityScore.settings` and is available from API 49.0 (Metadata API reference).

### Einstein Activity Capture

**File path:** `force-app/main/default/settings/EAC.settings-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<EACSettings xmlns="http://soap.sforce.com/2006/04/metadata">
    <provisionProductivityFeatures>true</provisionProductivityFeatures>
    <enableActivityCapture>true</enableActivityCapture>
    <enableEnforceEacSharingPref>true</enableEnforceEacSharingPref>
    <enableInboxActivitySharing>false</enableInboxActivitySharing>
    <sensitiveEmailFilter>true</sensitiveEmailFilter>
    <syncInternalEvents>false</syncInternalEvents>
</EACSettings>
```

What each element does, from the Metadata API reference for `EACSettings`:

| Element | Effect | Why set it this way |
|---|---|---|
| `provisionProductivityFeatures` | Org is ready for productivity features | `enableActivityCapture` requires it to be true |
| `enableActivityCapture` | Turns on Einstein Activity Capture | The feature itself |
| `enableEnforceEacSharingPref` | New users must keep activity sharing at "Don't Share" | Private by default; users can still share individual items |
| `enableInboxActivitySharing` | When true, new users' default activity sharing is Everyone (default true) | Set false so new users do not share all activity with everyone |
| `sensitiveEmailFilter` | Prevents sensitive emails from being shared (API 54.0 and later) | Privacy |
| `syncInternalEvents` | Syncs events whose attendees are all internal (API 53.0 and later) | Keeps internal meetings out of customer timelines |

Order the elements as your retrieve shows them if a deploy complains; UNVERIFIED (2026-10-03): whether settings files enforce element order. Exclusion lists for domains and addresses are configured in Setup; UNVERIFIED (2026-10-03): no metadata field for exclusion lists was found in `EACSettings`.

### Pipeline Inspection

**File path:** `force-app/main/default/settings/Opportunity.settings-meta.xml` (excerpt; retrieve the full file and change only these elements, because a settings deploy writes every element you send)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- Excerpt of Opportunity.settings: only the Pipeline Inspection elements are shown. -->
<OpportunitySettings xmlns="http://soap.sforce.com/2006/04/metadata">
    <enablePipelineInspection>true</enablePipelineInspection>
    <enableExpandedPipelineInspectionSetup>true</enableExpandedPipelineInspectionSetup>
</OpportunitySettings>
```

`enablePipelineInspection` also turns on historical trending for opportunities, and "additional configuration in Setup is required". `enableExpandedPipelineInspectionSetup` shows admins a setup page with all steps (Metadata API reference, OpportunitySettings, API 52.0 and later).

## package.xml member form

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>OpportunityScore</members>
        <members>EAC</members>
        <members>Opportunity</members>
        <name>Settings</name>
    </types>
    <version>66.0</version>
</Package>
```

Name each settings member. The `*` wildcard does not apply to individual feature settings; it works only when retrieving all settings (Metadata API reference, OpportunitySettings and EACSettings wildcard notes).

## Example 2: Readiness and verification queries

```sql
-- 1. Data readiness, counted separately for won and lost (last 24 months).
SELECT COUNT() FROM Opportunity WHERE IsClosed = true AND IsWon = true  AND CloseDate = LAST_N_DAYS:730
SELECT COUNT() FROM Opportunity WHERE IsClosed = true AND IsWon = false AND CloseDate = LAST_N_DAYS:730

-- 2. Scores on open opportunities. IqScore is the standard Opportunity Score field (1 to 99).
SELECT Id, Name, StageName, IqScore
FROM Opportunity
WHERE IsClosed = false AND IqScore != null
ORDER BY IqScore ASC
LIMIT 50

-- 3. The model's strongest factors (needs the View Scoring Model Factors permission).
SELECT Id, Factor, ScoreCorrelation, FactorSummaryOrgLanguage
FROM SalesAIScoreModelFactor
WHERE Status = 'Active' AND SalesAIScoreCycle.CycleType = 'OpportunityScoreModeling'
ORDER BY ScoreCorrelation DESC
```

Query 3 is the Object Reference's own usage example for `SalesAIScoreModelFactor`. `IqScore` is documented on Opportunity as "the likelihood, measured on a scale of 1 to 99, that an opportunity will be won", with label Opportunity Score, available from API 41.0 when Einstein Opportunity Scoring is enabled. `LAST_N_DAYS:730` with `=` follows SOQL date-literal syntax.

UNVERIFIED (2026-10-03): the training thresholds that query 1 checks against (at least 200 closed-won and 200 closed-lost opportunities in the last 24 months, each open at least two days). They come from a Help article that does not fetch; confirm them in the Opportunity Scoring setup page before promising scores.

## Deploy order

1. Confirm licenses on the Company Information page (Feature Licenses and Permission Set Licenses).
2. Deploy `EAC.settings` first, so mail starts syncing with the private defaults in place.
3. Deploy `OpportunityScore.settings`; scores appear after the first model training completes.
4. Deploy the Pipeline Inspection elements, then finish the Setup steps the feature requires.
5. Assign permissions: the scoring model-factor object needs the View Scoring Model Factors permission, which is not enabled by default.

## Verification

- Query 2 returns open opportunities with a non-null `IqScore` after training.
- Query 3 returns active model factors for a user with the permission. A user without it cannot see model factor information (Object Reference, special access rules); UNVERIFIED (2026-10-03): whether that shows as an error or as no rows.
- A newly activated Activity Capture user shows sharing set to Don't Share.
