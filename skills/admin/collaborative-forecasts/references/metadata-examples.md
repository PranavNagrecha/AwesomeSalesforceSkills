# Metadata Examples — Collaborative Forecasts

Deployable shapes for the forecasting metadata family. Element names, enum values and skeletons come from the Metadata API Developer Guide (v62 PDF — `ForecastingSettings`, `ForecastingType`, `ForecastingSourceDefinition`, `ForecastingTypeSource`, `ForecastingFilter`, `ForecastingFilterCondition`, `StandardValueSet`, `CustomValue`) and the Object Reference (`ForecastingQuota`, `ForecastingType`, `ForecastingItem`, `Period`, `UserRole`, `User`). The worked examples extend the guide's own samples to a realistic two-motion org. Lint them with:

```bash
python3 skills/admin/collaborative-forecasts/scripts/check_collaborative_forecasts.py --manifest-dir force-app/main/default
```

## Where the files live

| Type | package.xml `<name>` / `<members>` | File in a DX project | API |
|---|---|---|---|
| `ForecastingSettings` | `Settings` / `Forecasting` | `settings/Forecasting.settings-meta.xml` | 28.0+ (restructured at 30.0 and 53.0) |
| `ForecastingType` | `ForecastingType` / `*` or developer name | `forecastingTypes/<name>.forecastingType-meta.xml` | 52.0+ |
| `ForecastingSourceDefinition` | `ForecastingSourceDefinition` / `*` | `forecastingSourceDefinitions/<name>.forecastingSourceDefinition-meta.xml` | 52.0+ |
| `ForecastingTypeSource` | `ForecastingTypeSource` / `*` | `ForecastingTypeSources/<name>.forecastingTypeSource-meta.xml` | 52.0+ |
| `ForecastingFilter` | `ForecastingFilter` / `*` | `forecastingFilters/<name>.forecastingFilter-meta.xml` | 55.0+ |
| `ForecastingFilterCondition` | `ForecastingFilterCondition` / `*` | `ForecastingFilterConditions/<name>.ForecastingFilterCondition-meta.xml` | 55.0+ |
| `StandardValueSet` | `StandardValueSet` / `OpportunityStage` | `standardValueSets/OpportunityStage.standardValueSet-meta.xml` | 38.0+ |

Two file-name traps live in this table. The settings file is named **`Forecasting.settings`**, not `ForecastingSettings.settings` — "ForecastingSettings values are stored in a single file named `Forecasting.settings` in the settings directory." And the `ForecastingTypeSource` / `ForecastingFilterCondition` folders are capitalised in the guide (`ForecastingTypeSources`, `ForecastingFilterConditions`) while their siblings are not.

Settings do not accept the `*` wildcard for an individual setting: "The wildcard character `*` in the package.xml manifest file doesn't apply to metadata types for feature settings. The wildcard applies only when retrieving all settings." `ForecastingType`, `ForecastingSourceDefinition`, `ForecastingTypeSource`, `ForecastingFilter` and `ForecastingFilterCondition` all do support it.

---

## 1. Two forecast types in one `Forecasting.settings`

Opportunity revenue by role, plus opportunity quantity by product family. Cumulative rollups, adjustments and quotas on, six months displayed.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ForecastingSettings xmlns="http://soap.sforce.com/2006/04/metadata">
    <enableForecasts>true</enableForecasts>
    <defaultToPersonalCurrency>false</defaultToPersonalCurrency>

    <!-- Org-wide from API 53.0. All forecast types must share these values. -->
    <globalAdjustmentsSettings>
        <allowExpandedColumns>true</allowExpandedColumns>
        <enableAdjustments>true</enableAdjustments>
        <enableOwnerAdjustments>true</enableOwnerAdjustments>
    </globalAdjustmentsSettings>
    <globalForecastRangeSettings>
        <beginning>1</beginning>
        <displaying>6</displaying>
        <periodType>Month</periodType>
    </globalForecastRangeSettings>
    <globalQuotasSettings>
        <showQuotas>true</showQuotas>
    </globalQuotasSettings>

    <!-- All EIGHT category mappings are required, whichever rollup style you use. -->
    <forecastingCategoryMappings>
        <forecastingItemCategoryApiName>openpipeline</forecastingItemCategoryApiName>
        <weightedSourceCategories>
            <sourceCategoryApiName>pipeline</sourceCategoryApiName>
            <weight>1.0</weight>
        </weightedSourceCategories>
        <weightedSourceCategories>
            <sourceCategoryApiName>best case</sourceCategoryApiName>
            <weight>1.0</weight>
        </weightedSourceCategories>
        <weightedSourceCategories>
            <sourceCategoryApiName>commit</sourceCategoryApiName>
            <weight>1.0</weight>
        </weightedSourceCategories>
    </forecastingCategoryMappings>
    <forecastingCategoryMappings>
        <forecastingItemCategoryApiName>bestcaseforecast</forecastingItemCategoryApiName>
        <weightedSourceCategories>
            <sourceCategoryApiName>best case</sourceCategoryApiName>
            <weight>1.0</weight>
        </weightedSourceCategories>
        <weightedSourceCategories>
            <sourceCategoryApiName>commit</sourceCategoryApiName>
            <weight>1.0</weight>
        </weightedSourceCategories>
        <weightedSourceCategories>
            <sourceCategoryApiName>closed</sourceCategoryApiName>
            <weight>1.0</weight>
        </weightedSourceCategories>
    </forecastingCategoryMappings>
    <forecastingCategoryMappings>
        <forecastingItemCategoryApiName>commitforecast</forecastingItemCategoryApiName>
        <weightedSourceCategories>
            <sourceCategoryApiName>commit</sourceCategoryApiName>
            <weight>1.0</weight>
        </weightedSourceCategories>
        <weightedSourceCategories>
            <sourceCategoryApiName>closed</sourceCategoryApiName>
            <weight>1.0</weight>
        </weightedSourceCategories>
    </forecastingCategoryMappings>
    <forecastingCategoryMappings>
        <forecastingItemCategoryApiName>pipelineonly</forecastingItemCategoryApiName>
        <weightedSourceCategories>
            <sourceCategoryApiName>pipeline</sourceCategoryApiName>
            <weight>1.0</weight>
        </weightedSourceCategories>
    </forecastingCategoryMappings>
    <forecastingCategoryMappings>
        <forecastingItemCategoryApiName>bestcaseonly</forecastingItemCategoryApiName>
        <weightedSourceCategories>
            <sourceCategoryApiName>best case</sourceCategoryApiName>
            <weight>1.0</weight>
        </weightedSourceCategories>
    </forecastingCategoryMappings>
    <forecastingCategoryMappings>
        <forecastingItemCategoryApiName>commitonly</forecastingItemCategoryApiName>
        <weightedSourceCategories>
            <sourceCategoryApiName>commit</sourceCategoryApiName>
            <weight>1.0</weight>
        </weightedSourceCategories>
    </forecastingCategoryMappings>
    <forecastingCategoryMappings>
        <forecastingItemCategoryApiName>closedonly</forecastingItemCategoryApiName>
        <weightedSourceCategories>
            <sourceCategoryApiName>closed</sourceCategoryApiName>
            <weight>1.0</weight>
        </weightedSourceCategories>
    </forecastingCategoryMappings>
    <forecastingCategoryMappings>
        <forecastingItemCategoryApiName>omittedonly</forecastingItemCategoryApiName>
        <weightedSourceCategories>
            <sourceCategoryApiName>omitted</sourceCategoryApiName>
            <weight>1.0</weight>
        </weightedSourceCategories>
    </forecastingCategoryMappings>

    <!-- Type 1: Opportunity revenue, role hierarchy, close date. -->
    <forecastingTypeSettings>
        <name>OpportunityRevenue</name>
        <masterLabel>Opportunities</masterLabel>
        <active>true</active>
        <isAmount>true</isAmount>
        <isQuantity>false</isQuantity>
        <isAvailable>true</isAvailable>
        <hasProductFamily>false</hasProductFamily>
        <forecastingDateType>OpportunityCloseDate</forecastingDateType>
        <displayedCategoryApiNames>openpipeline</displayedCategoryApiNames>
        <displayedCategoryApiNames>bestcaseforecast</displayedCategoryApiNames>
        <displayedCategoryApiNames>commitforecast</displayedCategoryApiNames>
        <displayedCategoryApiNames>closedonly</displayedCategoryApiNames>
        <forecastedCategoryApiNames>openpipeline</forecastedCategoryApiNames>
        <forecastedCategoryApiNames>bestcaseforecast</forecastedCategoryApiNames>
        <forecastedCategoryApiNames>commitforecast</forecastedCategoryApiNames>
        <forecastedCategoryApiNames>closedonly</forecastedCategoryApiNames>
        <managerAdjustableCategoryApiNames>bestcaseforecast</managerAdjustableCategoryApiNames>
        <managerAdjustableCategoryApiNames>commitforecast</managerAdjustableCategoryApiNames>
        <ownerAdjustableCategoryApiNames>bestcaseforecast</ownerAdjustableCategoryApiNames>
        <ownerAdjustableCategoryApiNames>commitforecast</ownerAdjustableCategoryApiNames>
        <opportunityListFieldsSelectedSettings>
            <field>OPPORTUNITY.NAME</field>
            <field>OPPORTUNITY.ACCOUNT_NAME</field>
            <field>OPPORTUNITY.STAGE_NAME</field>
            <field>OPPORTUNITY.CLOSE_DATE</field>
        </opportunityListFieldsSelectedSettings>
    </forecastingTypeSettings>

    <!-- Type 2: Opportunity product QUANTITY by product family. -->
    <forecastingTypeSettings>
        <name>OpportunityLineItemQuantity</name>
        <masterLabel>Product Families - Quantity</masterLabel>
        <active>true</active>
        <isAmount>false</isAmount>
        <isQuantity>true</isQuantity>
        <isAvailable>true</isAvailable>
        <hasProductFamily>true</hasProductFamily>
        <forecastingDateType>ProductDate</forecastingDateType>
        <displayedCategoryApiNames>openpipeline</displayedCategoryApiNames>
        <displayedCategoryApiNames>bestcaseforecast</displayedCategoryApiNames>
        <displayedCategoryApiNames>commitforecast</displayedCategoryApiNames>
        <displayedCategoryApiNames>closedonly</displayedCategoryApiNames>
        <forecastedCategoryApiNames>openpipeline</forecastedCategoryApiNames>
        <forecastedCategoryApiNames>bestcaseforecast</forecastedCategoryApiNames>
        <forecastedCategoryApiNames>commitforecast</forecastedCategoryApiNames>
        <forecastedCategoryApiNames>closedonly</forecastedCategoryApiNames>
        <opportunityListFieldsSelectedSettings>
            <field>OPPORTUNITY.NAME</field>
        </opportunityListFieldsSelectedSettings>
    </forecastingTypeSettings>

    <!-- Product families the quantity type is allowed to forecast on. -->
    <forecastingDisplayedFamilySettings>
        <productFamily>Hardware</productFamily>
    </forecastingDisplayedFamilySettings>
    <forecastingDisplayedFamilySettings>
        <productFamily>Subscriptions</productFamily>
    </forecastingDisplayedFamilySettings>
</ForecastingSettings>
```

How to read it:

- `name` is not free text. It must be one of the guide's fixed strings — `OpportunityRevenue`, `OpportunityQuantity`, `OpportunitySplitRevenue`, `OpportunityOverlayRevenue`, `OpportunityLineItemRevenue`, `OpportunityLineItemQuantity`, `LineItemRevenueScheduleDate`, `Territory_Model_NameN`, and the rest — or the name of a custom opportunity split type enabled as a forecast type. Anything else belongs in a `ForecastingType` file (section 2).
- **All eight** `forecastingCategoryMappings` occurrences are required: "Organizations using either cumulative forecast rollups or individual forecast category columns must include all eight occurrences of this subtype." `weight` has one supported value, `1.0`.
- The rollup style is not an element. It is which set of four values you put in `forecastedCategoryApiNames`: `openpipeline`/`bestcaseforecast`/`commitforecast`/`closedonly` for cumulative, `pipelineonly`/`bestcaseonly`/`commitonly`/`closedonly` for individual. "Changing from one set of four values to the other changes the organization setting for Enable Cumulative Forecast Rollups in Setup. If this field is omitted, the setting isn't changed."
- `displayedCategoryApiNames` must carry the same four values — "Always use the same 4 values for both."
- `managerAdjustableCategoryApiNames` and `ownerAdjustableCategoryApiNames` each appear exactly twice, are limited to the Best Case and Commit rollups, and must match each other when both are present. They are legal only while the matching `enableAdjustments` / `enableOwnerAdjustments` is `true`.
- `isAmount` and `isQuantity` are always opposites, and `hasProductFamily` is required. `isAmount`, `isQuantity`, `isAvailable`, `masterLabel`, `displayedCategoryApiNames`, `managerAdjustableCategoryApiNames`, `ownerAdjustableCategoryApiNames` and `opportunityListFieldsLabelMappings` are all documented read-only — retrieve them, keep them consistent, do not treat them as levers.
- Field names in `opportunityListFieldsSelectedSettings` use the report-style API form the guide samples (`OPPORTUNITY.NAME`, which must be one of the selections); up to 15 fields are allowed. UNVERIFIED (2026-09-05): the guide prints only `OPPORTUNITY.NAME`, so retrieve the org's `opportunityListFieldsLabelMappings` — a read-only list of every Opportunity field's API name and label — to get the exact spelling of the rest rather than guessing.
- `displaying` is capped at 12 months / 8 quarters; `periodType` is `Month`, `Quarter`, `Week` or `Year`.
- Omission is destructive: "Omitting a forecast type field from the XML can deactivate that forecast type: if the forecast type was available in the release specified by the XML package version, that forecast type is deactivated and its quota and adjustment data are deleted." Always deploy a full retrieved file, never a hand-trimmed fragment.

---

## 2. A custom forecast type: `ForecastingType` + `ForecastingSourceDefinition` + `ForecastingTypeSource`

Opportunity revenue splits, role hierarchy, amount measure. Three files, one package.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- forecastingTypes/AE_Split_Revenue.forecastingType-meta.xml -->
<ForecastingType xmlns="http://soap.sforce.com/2006/04/metadata">
    <active>true</active>
    <amount>true</amount>
    <quantity>false</quantity>
    <dateType>OpportunityCloseDate</dateType>
    <developerName>AE_Split_Revenue</developerName>
    <masterLabel>AE Revenue Splits</masterLabel>
    <hasProductFamily>false</hasProductFamily>
    <opportunitySplitType>Revenue</opportunitySplitType>
    <roleType>R</roleType>
</ForecastingType>
```

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- forecastingSourceDefinitions/FSD_OpportunitySplit.forecastingSourceDefinition-meta.xml -->
<ForecastingSourceDefinition xmlns="http://soap.sforce.com/2006/04/metadata">
    <masterLabel>FSD_OpportunitySplit</masterLabel>
    <sourceObject>OpportunitySplit</sourceObject>
    <measureField>OpportunitySplit.SplitAmount</measureField>
    <dateField>Opportunity.CloseDate</dateField>
    <userField>OpportunitySplit.SplitOwnerId</userField>
    <categoryField>Opportunity.ForecastCategoryName</categoryField>
</ForecastingSourceDefinition>
```

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- ForecastingTypeSources/FTS_AE_Split_Revenue.forecastingTypeSource-meta.xml -->
<ForecastingTypeSource xmlns="http://soap.sforce.com/2006/04/metadata">
    <forecastingSourceDefinition>FSD_OpportunitySplit</forecastingSourceDefinition>
    <forecastingType>AE_Split_Revenue</forecastingType>
    <masterLabel>FTS_AE_Split_Revenue</masterLabel>
    <parentSourceDefinition>FSD_Opportunity</parentSourceDefinition>
    <relationField>OpportunitySplit.OpportunityId</relationField>
    <sourceGroup>1</sourceGroup>
</ForecastingTypeSource>
```

How to read it:

- `roleType` is `R` (user role-based) or `Y` (Territory2-based). A `Y` type also needs `territory2Model` on the `ForecastingType` and `territory2Field` = `Opportunity.Territory2Id` on the source definition; for role-based types `territory2Field` is null.
- `amount` and `quantity` are both required and mutually exclusive. `dateType` on `ForecastingType` takes the same words as `forecastingDateType` on the settings — `OpportunityCloseDate`, `ProductDate`, `ScheduleDate`, and the `…Only` and `…CustomDate` variants. The guide's own `ForecastingType` samples print `<dateType>0</dateType>`; UNVERIFIED (2026-09-05): the guide does not explain that `0`, and it does not appear in its own valid-value list, so author the named value and treat `0` as something you may see on retrieve rather than something to deploy.
- `measureField` is drawn from a fixed list — `Opportunity.Amount`, `Opportunity.TotalOpportunityQuantity`, `OpportunityLineItem.Quantity`, `OpportunityLineItem.TotalPrice`, `OpportunityLineItemSchedule.Revenue`, `OpportunitySplit.SplitAmount`, and the `.Custom` forms where `Custom` is replaced by your own field API name (the guide's example is `Megawatts__c`).
- `FSD_Opportunity` above is a second `ForecastingSourceDefinition` you must also create (`sourceObject` `Opportunity`, `measureField` `Opportunity.Amount`) — `parentSourceDefinition` points at a real component, not a literal.
- `parentSourceDefinition` and `relationField` are only for non-Opportunity sources. The parent chain is fixed: Opportunity Product's parent is Opportunity, Opportunity Split's parent is Opportunity, Line Item Schedule's parent is Opportunity Product.
- `categoryField` has exactly one documented value, `Opportunity.ForecastCategoryName` — the forecast category always comes from the opportunity even when the measure does not.

### Optional: an amount filter on the type

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- forecastingFilters/FF_LargeDealsOnly.forecastingFilter-meta.xml -->
<ForecastingFilter xmlns="http://soap.sforce.com/2006/04/metadata">
    <filterLogic>1 AND 2</filterLogic>
    <forecastingType>AE_Split_Revenue</forecastingType>
    <forecastingTypeSource>FTS_AE_Split_Revenue</forecastingTypeSource>
    <masterLabel>FF_LargeDealsOnly</masterLabel>
</ForecastingFilter>
```

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- ForecastingFilterConditions/FFC_AmountOverThreshold.ForecastingFilterCondition-meta.xml -->
<ForecastingFilterCondition xmlns="http://soap.sforce.com/2006/04/metadata">
    <fieldName>Amount</fieldName>
    <forecastingFilter>FF_LargeDealsOnly</forecastingFilter>
    <forecastingSourceDefinition>FSD_Opportunity</forecastingSourceDefinition>
    <masterLabel>FFC_AmountOverThreshold</masterLabel>
    <operation>greaterThan</operation>
    <sortOrder>1</sortOrder>
    <value>100000</value>
</ForecastingFilterCondition>
```

How to read it:

- `filterLogic` supports `AND` only — "Only AND is supported" — and a forecast type "can contain up to three filter conditions", so `sortOrder` never exceeds 3.
- `operation` is one of `equals`, `notEqual`, `greaterThan`, `greaterOrEqual`, `lessThan`, `lessOrEqual`. Multiple values in `value` are comma-delimited.
- The filter's `forecastingTypeSource` must resolve to a source definition whose `sourceObject` is `Opportunity`.
- Multi-currency changes the meaning of a currency threshold: "If you have multiple currencies enabled, and add a custom filter on a currency field as part of your forecast type definition, the corporate currency at the time the filter was created is used." Recreate the filter if the corporate currency changes.
- The guide's printed sample of this component is malformed — it carries a stray `colName` element and closes `operation` and `sortOrder` with `</masterLabel>`. The block above is the corrected form.

---

## 3. Stage-to-category mapping as deployable metadata

The mapping is not a separate type. It is the `forecastCategory` element on each opportunity stage value.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- standardValueSets/OpportunityStage.standardValueSet-meta.xml -->
<StandardValueSet xmlns="http://soap.sforce.com/2006/04/metadata">
    <sorted>false</sorted>
    <standardValue>
        <fullName>Prospecting</fullName>
        <default>false</default>
        <forecastCategory>Pipeline</forecastCategory>
        <probability>10</probability>
    </standardValue>
    <standardValue>
        <fullName>Pilot</fullName>
        <default>false</default>
        <forecastCategory>BestCase</forecastCategory>
        <probability>40</probability>
    </standardValue>
    <standardValue>
        <fullName>Proposal/Price Quote</fullName>
        <default>false</default>
        <forecastCategory>Forecast</forecastCategory>
        <probability>75</probability>
    </standardValue>
    <standardValue>
        <fullName>Closed Won</fullName>
        <default>false</default>
        <forecastCategory>Closed</forecastCategory>
        <probability>100</probability>
        <won>true</won>
    </standardValue>
    <standardValue>
        <fullName>Closed Lost</fullName>
        <default>false</default>
        <forecastCategory>Omitted</forecastCategory>
        <probability>0</probability>
        <won>false</won>
    </standardValue>
</StandardValueSet>
```

How to read it:

- The deployable enum is `Omitted`, `Pipeline`, `BestCase`, `Forecast`, `Closed`. **`Forecast` is the Commit category.** There is no `Commit` and no `MostLikely` in this enum, and `forecastCategory` "is only relevant for the standard Stage field in opportunities."
- `won` and `probability` are the two other Stage-only elements on a standard value; `won` "indicates whether this value is associated with a closed or won status". There is no `closed` element for Stage — `closed` on `CustomValue` "is only relevant for the standard `Status` field in cases and tasks".
- The queryable form is different again: `OpportunityStage.ForecastCategory` returns `BestCase`/`Forecast`/`MostLikely`/… while `OpportunityStage.ForecastCategoryName` returns the spaced labels `Best Case`/`Commit`/`Most Likely`/…. Pick the field that matches the vocabulary of whatever is reading it.
- `StandardValueSet` does not accept the `*` wildcard; name `OpportunityStage` explicitly.
- "When you deploy a StandardValueSet, this array must contain at least one picklist value. Otherwise, you receive an error." Retrieve the org's full set and edit it — do not deploy the stages you happen to be changing.
- A stage with no `forecastCategory` is a stage the forecast cannot place. Deploy the mapping in the same change as the stage.

---

## 4. Quota load file

`ForecastingQuota` is data, not metadata. Load it after the types are active.

```csv
QuotaOwnerId,ForecastingTypeId,StartDate,QuotaAmount,CurrencyIsoCode
0055f000009AbCdAAK,0Db5f000000TgHxCAK,2026-10-01,450000,USD
0055f000009AbCeAAK,0Db5f000000TgHxCAK,2026-10-01,380000,USD
0055f000009AbCfAAK,0Db5f000000TgHxCAK,2026-10-01,600000,USD
```

For the product-family quantity type, swap the measure column and add the family:

```csv
QuotaOwnerId,ForecastingTypeId,StartDate,QuotaQuantity,ProductFamily
0055f000009AbCdAAK,0Db5f000000TgHyCAK,2026-10-01,1200,Hardware
0055f000009AbCdAAK,0Db5f000000TgHyCAK,2026-10-01,800,Subscriptions
```

How to read it:

- `PeriodId` is **read only** and must not appear in the file. `StartDate` is what associates the quota with a period: "The start of the quota, expressed as month and year. The date can include any day in a given month. Stored using the first date of the month."
- `IsAmount` and `IsQuantity` have no Create property — they are derived from the forecast type. Load `QuotaAmount` for an amount type and `QuotaQuantity` for a quantity type; never both, never neither.
- The loading user needs **Managed Quotas**, and "users can only edit their subordinates' or child territories' quotas, not their own" — so an admin loading their own row needs View All Forecasts as well.
- `CurrencyIsoCode` defaults to the importing user's personal currency if omitted, which is rarely what a finance-sourced file means.
- `Territory2Id` replaces `QuotaOwnerId` semantics for territory forecasts; `ForecastingGroupItemId` (API 60.0+) is required only when the type has a forecast group.

---

## 5. package.xml, deploy order, and CLI

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Forecasting</members>
        <name>Settings</name>
    </types>
    <types>
        <members>*</members>
        <name>ForecastingType</name>
    </types>
    <types>
        <members>*</members>
        <name>ForecastingSourceDefinition</name>
    </types>
    <types>
        <members>*</members>
        <name>ForecastingTypeSource</name>
    </types>
    <types>
        <members>*</members>
        <name>ForecastingFilter</name>
    </types>
    <types>
        <members>*</members>
        <name>ForecastingFilterCondition</name>
    </types>
    <types>
        <members>OpportunityStage</members>
        <name>StandardValueSet</name>
    </types>
    <version>62.0</version>
</Package>
```

Deploy order is fixed and, helpfully, automatic: "Deploy Metadata API types in this sequence: ForecastingSettings, ForecastingType, ForecastingSourceDefinition, and then ForecastingTypeSource. If all are specified in the package file, the sequence is followed automatically." Put all four in one package rather than splitting the deploy.

```bash
# Retrieve current state before editing anything
sf project retrieve start \
  --metadata "Settings:Forecasting" ForecastingType ForecastingSourceDefinition ForecastingTypeSource \
  --metadata "StandardValueSet:OpportunityStage" \
  --target-org my-sandbox

# Lint, then validate without deploying
python3 skills/admin/collaborative-forecasts/scripts/check_collaborative_forecasts.py --manifest-dir force-app/main/default
sf project deploy validate --manifest manifest/package.xml --target-org my-sandbox

# Deploy TWICE: pass 1 creates the new types inactive, pass 2 activates them
sf project deploy start --manifest manifest/package.xml --target-org my-sandbox
sf project deploy start --manifest manifest/package.xml --target-org my-sandbox
```

The double deploy is the guide's own instruction, not a workaround: "If the forecast type doesn't exist, it's created in the inactive state. If the forecast type exists, the active flag is updated. Deploy the zip file twice to create and activate the forecast type." A CI job that deploys once and asserts success will report green on a forecast nobody can see.

---

## 6. Verification

Run these after the second deploy, before handing the tab to sales.

```sql
-- 1. Types: at most four active; IsPlatformType flags a legacy type you cannot recreate
SELECT Id, DeveloperName, MasterLabel, IsActive, IsPlatformType, IsAmount, IsQuantity,
       DateType, HasProductFamily, HasAdjustments, HasOwnerAdjustments, CanDisplayQuotas,
       LastActivatedDate
FROM ForecastingType
ORDER BY IsActive DESC, DeveloperName

-- 2. Forecast hierarchy: every role that should roll up needs a forecast manager
SELECT Id, Name, DeveloperName, ParentRoleId, ForecastUserId
FROM UserRole
WHERE ForecastUserId = NULL
ORDER BY Name

-- 3. Forecast users: enabled flag is per user and independent of the role
SELECT Id, Name, UserRoleId, ForecastEnabled
FROM User
WHERE IsActive = TRUE AND UserRoleId != NULL AND ForecastEnabled = FALSE

-- 4. Periods: the real forecast period boundaries, for reconciling a quota file
SELECT Id, StartDate, EndDate, Type, FullyQualifiedLabel, IsForecastPeriod
FROM Period
WHERE IsForecastPeriod = TRUE AND StartDate = THIS_FISCAL_YEAR
ORDER BY StartDate

-- 5. Quota coverage per type for the current period
SELECT ForecastingTypeId, COUNT(Id) quotaRows, SUM(QuotaAmount) totalQuota
FROM ForecastingQuota
WHERE StartDate = THIS_FISCAL_QUARTER
GROUP BY ForecastingTypeId

-- 6. Adjustment inventory — export this BEFORE any settings change that can purge it
SELECT Id, ForecastingItemId, ForecastingTypeId, AdjustedAmount, AdjustedQuantity, AdjustmentNote
FROM ForecastingAdjustment

-- 7. The numbers a manager actually sees, per rollup column
SELECT OwnerId, PeriodId, ForecastingTypeId, ForecastingItemCategory, ForecastCategoryName,
       ForecastAmount, OwnerOnlyAmount, AmountWithoutAdjustments, HasAdjustment, HasOwnerAdjustment
FROM ForecastingItem
WHERE PeriodId = :currentPeriodId
```

Setup check, for what SOQL cannot see: open **Setup → Forecasts Settings** and confirm the four displayed columns match the four `forecastedCategoryApiNames` you deployed, then open the **Forecasts** tab as a manager whose subordinates have open pipeline and confirm a non-zero row appears under each column.

Two reading notes on query 7. `ForecastingItem` is read-only and "other users can see the ForecastingItem object, but not its records" — without View All Forecasts you see only your own subordinates and child territories, so run it as an admin who has that permission or the result is silently narrower than you think. And `ForecastCategoryName` "can be null" in a cumulative-rollup org because a cumulative amount spans several categories; group on `ForecastingItemCategory` instead.
