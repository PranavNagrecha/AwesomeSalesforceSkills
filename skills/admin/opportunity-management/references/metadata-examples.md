# Metadata Examples — Opportunity Management

Deployable XML for the metadata types this skill owns: `OpportunitySettings`,
`BusinessProcess` (the "Sales Process" in Setup), the `RecordType` that binds it,
`PathAssistant`, and the `Layout` that exposes the opportunity team. Every element
name below comes from the Metadata API Developer Guide field tables cited beside it.

Two neighbouring packages own metadata this skill deliberately does **not** repeat:

| Metadata | Owner | Why |
|---|---|---|
| `StandardValueSet` → `OpportunityStage` (the stage values themselves, with `forecastCategory` / `probability` / `won` / `closed`) | `admin/picklist-and-value-sets` §3 of its `references/metadata-examples.md` | It owns the standard-value-set deploy semantics, including the partial-deploy trap that deactivates every value you omit |
| `RecordType` + `BusinessProcess` pairing rules, layout assignment, picklist filtering | `admin/record-types-and-page-layouts` | It owns which objects require `businessProcess` and the bare-vs-qualified `fullName` rule |
| `ForecastingType` / `ForecastingSettings` beyond the split pointer below | `admin/collaborative-forecasts` | It owns forecast types, rollups, quotas and adjustments |

---

## Where the files live

```text
force-app/main/default/
├── settings/
│   └── Opportunity.settings-meta.xml
├── objects/Opportunity/
│   ├── businessProcesses/
│   │   └── New_Business.businessProcess-meta.xml
│   └── recordTypes/
│       └── New_Business.recordType-meta.xml
├── pathAssistants/
│   └── Opportunity_New_Business_Path.pathAssistant-meta.xml
└── layouts/
    └── Opportunity-Opportunity New Business Layout.layout-meta.xml
```

Grounded file-location facts:

- "Opportunities values are stored in a single file named `Opportunity.settings` in the `settings` directory" (api_meta.txt:123277–123278).
- "Business processes are defined as part of the custom object or standard object definition. See CustomObject" (api_meta.txt:42968–42969) — MDAPI nests them; a DX project decomposes them.
- "PathAssistant components have the suffix `.pathAssistant` and are stored in the `pathAssistants` folder" (api_meta.txt:94502).

<!-- UNVERIFIED (2026-09-04): the decomposed DX directory layout (objects/Opportunity/businessProcesses/*.businessProcess-meta.xml, objects/Opportunity/recordTypes/*.recordType-meta.xml) is a Salesforce DX source-format convention; the Metadata API PDF documents only the nested <CustomObject> form. The nested XML in §2 is the grounded shape and deploys in either project format. -->

---

## 1. `OpportunitySettings` — enabling opportunity teams

`enableOpportunityTeam` "lets users associate team members with opportunities"
(api_meta.txt:123333). Team selling is the prerequisite for splits, and this element
is the only part of that chain that is deployable at all — see §6.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<OpportunitySettings xmlns="http://soap.sforce.com/2006/04/metadata">
    <autoActivateNewReminders>true</autoActivateNewReminders>
    <doesEnforceStandardOpportunitySaveLogic>true</doesEnforceStandardOpportunitySaveLogic>
    <enableFindSimilarOpportunities>true</enableFindSimilarOpportunities>
    <enableForecastCategoryMetrics>true</enableForecastCategoryMetrics>
    <enableOpportunityFieldHistoryTracking>true</enableOpportunityFieldHistoryTracking>
    <enableOpportunityTeam>true</enableOpportunityTeam>
    <enableUpdateReminders>true</enableUpdateReminders>
    <promptToAddProducts>true</promptToAddProducts>
    <findSimilarOppFilter>
        <similarOpportunitiesMatchFields>OPPORTUNITY.Account</similarOpportunitiesMatchFields>
        <similarOpportunitiesMatchFields>OPPORTUNITY.OpportunityCompetitors</similarOpportunitiesMatchFields>
        <similarOpportunitiesDisplayColumns>OPPORTUNITY.Amount</similarOpportunitiesDisplayColumns>
    </findSimilarOppFilter>
</OpportunitySettings>
```

**How to read it**

- `doesEnforceStandardOpportunitySaveLogic` "Default value is true. **Can't be set to false**"
  (api_meta.txt:123304–123306). Deploy it as `true` or omit it; a `false` is a wasted deploy cycle.
- `enableOpportunityFieldHistoryTracking` "Default value is true" (api_meta.txt:123321–123323).
  Leave it on before the stage ladder ships — history cannot be backfilled.
- `enableOpportunityTeam` is a boolean with no `enableOpportunitySplits` counterpart. The
  `OpportunitySettings` field table (api_meta.txt:123288–123443) has no split element at all;
  splits are enabled in Setup only. See §6.
- `enableOpportunityInsightsInMobile` exists in the field table but is "Deprecated in API version
  59.0 and later because the feature is no longer available… Available in API version 47.0 to 58.0"
  (api_meta.txt:123325–123332). Do not add it to a new manifest.
- `findSimilarOppFilter` takes `similarOpportunitiesMatchFields` (fields to compare) and
  `similarOpportunitiesDisplayColumns` (columns to compare) (api_meta.txt:123386, 123429–123431).

---

## 2. `BusinessProcess` — the "New Business" sales process

A sales process is a `BusinessProcess` whose `values` are a **subset** of the global
`OpportunityStage` value set: "The BusinessProcess metadata type enables you to display
different picklist values for users based on their profile. Multiple business processes allow
you to track separate sales, support, and lead lifecycles" (api_meta.txt:42956–42958).

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- Excerpt of objects/Opportunity/Opportunity.object (MDAPI form). Only the
     businessProcesses and recordTypes members relevant to this skill are shown. -->
<CustomObject xmlns="http://soap.sforce.com/2006/04/metadata">
    <businessProcesses>
        <fullName>New Business</fullName>
        <description>Direct new-logo motion. Six stages, one won and one lost.</description>
        <isActive>true</isActive>
        <values>
            <fullName>Prospecting</fullName>
            <!-- No <default> here. The platform rejects the deploy with
                 "Cannot specify a default on: Opportunity" (org-verified
                 2026-09-18, sfskills-dev at API 62.0). A business process
                 lists which stages a record type exposes and in what order;
                 it does not set the stage a new Opportunity opens at. That
                 comes from the default on the StageName picklist value for
                 the record type. OM-BP-DEFAULT-01 in
                 scripts/check_opportunity_management.py catches it. -->
        </values>
        <values>
            <fullName>Needs Analysis</fullName>
        </values>
        <values>
            <fullName>Proposal/Price Quote</fullName>
            <default>false</default>
        </values>
        <values>
            <fullName>Negotiation/Review</fullName>
            <default>false</default>
        </values>
        <values>
            <fullName>Closed Won</fullName>
            <default>false</default>
        </values>
        <values>
            <fullName>Closed Lost</fullName>
            <default>false</default>
        </values>
    </businessProcesses>
    <recordTypes>
        <fullName>New_Business</fullName>
        <label>New Business</label>
        <active>true</active>
        <businessProcess>New Business</businessProcess>
    </recordTypes>
</CustomObject>
```

**How to read it**

- `fullName` on a `BusinessProcess` is context-dependent, and this is the single most common
  deploy failure in this package. The guide: the `fullName` "is created combining the Entity Name
  and Business Process Name… for a business process called 'Bulk Orders' for opportunities, the
  fullName would be `Opportunity.Bulk Orders`. Use the object-qualified form … for API addressing,
  such as in a `package.xml` member … When creating a business process in a `CustomObject`
  definition, use the bare process name (`Bulk Orders`) for the nested
  `<businessProcesses><fullName>` value. The enclosing object already supplies the entity context"
  (api_meta.txt:42993–43008). Inside the object: `New Business`. In `package.xml`:
  `Opportunity.New Business`.
- `<businessProcess>` on the record type also takes the **bare** name — `admin/record-types-and-page-layouts`
  §"Case record type with a business process" documents the same rule and the four objects
  (lead, opportunity, solution, case) on which `businessProcess` is required.
- `values` is `PicklistValue[]` (api_meta.txt:43015). Each entry needs only `fullName` and
  `default`. A value's `forecastCategory`, `probability`, `won` and `closed` live on the
  `StandardValueSet`, **not** here — that is `admin/picklist-and-value-sets` §3.
- `isActive` marks the process active (api_meta.txt:43009–43010).
- A stage the process omits stays on records that already carry it; it just leaves the picklist for
  users on that record type. See `references/gotchas.md` Gotcha 8.
- Security note straight from the guide: "**Don't use business processes as an access control
  mechanism.** Profile assignment governs create and edit access for business process but doesn't
  govern read access… Don't store sensitive information in the business process description, name,
  or picklist values" (api_meta.txt:42960–42965). Deal-size tiers or named-account labels do not
  belong in a stage or process name.

---

## 3. `PathAssistant` — guidance on `Opportunity.StageName`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<PathAssistant xmlns="http://soap.sforce.com/2006/04/metadata">
    <active>true</active>
    <entityName>Opportunity</entityName>
    <fieldName>StageName</fieldName>
    <masterLabel>New Business Path</masterLabel>
    <recordTypeName>New_Business</recordTypeName>
    <pathAssistantSteps>
        <fieldNames>Amount</fieldNames>
        <fieldNames>CloseDate</fieldNames>
        <fieldNames>NextStep</fieldNames>
        <info>Confirm budget, authority and a compelling event before advancing. Log the economic buyer as an Opportunity Contact Role.</info>
        <picklistValueName>Needs Analysis</picklistValueName>
    </pathAssistantSteps>
    <pathAssistantSteps>
        <fieldNames>Amount</fieldNames>
        <fieldNames>CloseDate</fieldNames>
        <fieldNames>Probability</fieldNames>
        <info>Quote sent and pricing approved. Attach the signed order form before moving to Negotiation/Review.</info>
        <picklistValueName>Proposal/Price Quote</picklistValueName>
    </pathAssistantSteps>
</PathAssistant>
```

**How to read it**

- `entityName` and `fieldName` are "hard coded for Opportunity, Lead, and Quote" and both are
  "not updateable"; `recordTypeName` is likewise "Required… not updateable"
  (api_meta.txt:94513–94530). Retargeting a Path at a different record type is a delete-and-recreate,
  not an edit.
- "**Only one path can be created per record type for each object, including `__Master__` record
  type**" (api_meta.txt:94496). Two motions that need different guidance need two record types.
- `picklistValueName` is required per step (api_meta.txt:94549). Its value must be a stage the
  record type actually exposes — i.e. a value in §2's `businessProcesses`.
- Steps are sparse by design: "a missing step in the .xml file means it has not been configured,
  not that it doesn't exist" (api_meta.txt:94524–94526). A stage with no `pathAssistantSteps` block
  still renders as a chevron; it just carries no key fields and no guidance.
- "The preference does not need to be on to retrieve or deploy PathAssistant"
  (api_meta.txt:94498) — a green Path deploy is not evidence that Path is switched on, nor
  that the component is on the Lightning record page.
- Key-field count per step: `admin/path-and-guidance` states a five-field ceiling.
  **UNVERIFIED (2026-09-04):** no numeric key-field limit appears in the `PathAssistant` field table
  or in `PathAssistantStep` (api_meta.txt:94537–94550), which describes `fieldNames` only as "All the
  fields in `entityName` that will display in this step". Treat five as the sibling's operating
  assumption and confirm in Setup before designing a six-field step.
- Path renders; it does not gate. Enforcement is validation rules — see `references/examples.md` §3.

---

## 4. `Layout` — exposing the opportunity team and splits

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- Excerpt of layouts/Opportunity-Opportunity New Business Layout.layout-meta.xml.
     Only the relatedLists members relevant to team selling are shown. -->
<Layout xmlns="http://soap.sforce.com/2006/04/metadata">
    <relatedLists>
        <fields>NAME</fields>
        <fields>TEAMMEMBERROLE</fields>
        <fields>OPPORTUNITYACCESSLEVEL</fields>
        <relatedList>RelatedOpportunityTeamList</relatedList>
    </relatedLists>
    <relatedLists>
        <relatedList>RelatedNoteList</relatedList>
    </relatedLists>
</Layout>
```

**How to read it**

- `RelatedListItem` takes `relatedList` ("Required. The name of the related list"), `fields`,
  `sortField`, `sortOrder`, `customButtons`, `excludeButtons` and `quickActions`
  (api_meta.txt:83113–83132). `RelatedNoteList` is the guide's own sample value
  (api_meta.txt:83368).
- **UNVERIFIED (2026-09-04):** `RelatedOpportunityTeamList` and the three `fields` aliases above are
  not enumerated anywhere in api_meta.txt — the guide documents the element, not the catalogue of
  related-list names. Retrieve the layout from an org where the team related list is already placed
  and copy the exact strings the retrieve emits before deploying this block.
- The guide does warn that related-list `fields` use aliases rather than API names for standard
  fields — "the Fax, Mobile, and Home Phone fields are retrieved as `Phone2`, `Phone3`, and `Phone4`"
  (api_meta.txt:83121–83124) — so never hand-author these names from the Object Reference.
- Adding the team related list does not grant access. `OpportunityTeamMember.OpportunityAccessLevel`
  does, and its only values are `Read`, `Edit`, `All`
  (object_reference.txt:195697–195700).

---

## 5. `package.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Opportunity.New Business</members>
        <name>BusinessProcess</name>
    </types>
    <types>
        <members>Opportunity.New_Business</members>
        <name>RecordType</name>
    </types>
    <types>
        <members>Opportunity_New_Business_Path</members>
        <name>PathAssistant</name>
    </types>
    <types>
        <members>OpportunityStage</members>
        <name>StandardValueSet</name>
    </types>
    <types>
        <members>Opportunity-Opportunity New Business Layout</members>
        <name>Layout</name>
    </types>
    <types>
        <members>Opportunity</members>
        <name>Settings</name>
    </types>
    <version>62.0</version>
</Package>
```

**Wildcard support, per type — all four answers differ**

| Type | `*` allowed? | Source |
|---|---|---|
| `PathAssistant` | Yes | "This metadata type supports the wildcard character `*`" (api_meta.txt:94616–94617) |
| `BusinessProcess` | **Only when a `RecordType` is also specified** | api_meta.txt:43063–43065 |
| `StandardValueSet` | No — name `OpportunityStage` explicitly | api_meta.txt:130826–130828 |
| `Settings` (`Opportunity`) | No — "The wildcard character `*` … doesn't apply to metadata types for feature settings. The wildcard applies only when retrieving all settings, not for an individual setting" (api_meta.txt:123486–123489) | |

Note the two `fullName` forms in the same manifest: `Opportunity.New Business` (business process,
space and all, per api_meta.txt:42998–43006) alongside `Opportunity.New_Business` (record type
developer name). They are different strings for the same design object; a mismatch between them is
the most common `INVALID_CROSS_REFERENCE_KEY` in this package.

---

## 6. Splits and forecast types — what is *not* deployable

There is no `OpportunitySplitType` metadata type. The Metadata API guide's only mentions of splits
are inside `ForecastingType` and `ForecastingSettings` (api_meta.txt:75253, 75256, 117757).
On the data side, `OpportunitySplitType` supports only `describeSObjects()`, `query()`,
`retrieve()`, `update()` — **no `create()` and no `delete()`**
(object_reference.txt:195284–195285).

Consequence: split types are created in Setup, by hand, in every org. A migration script can
`update()` an existing type's `MasterLabel`, `Description` or `IsActive`, and nothing more.
`IsTotalValidated` is `Create, Defaulted on create, Filter, Group, Sort` — no `Update`
(object_reference.txt:195329–195334) — so a type's 100%-validation behaviour is fixed at creation.

Once the type exists, a forecast type can reference it by name:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ForecastingType xmlns="http://soap.sforce.com/2006/04/metadata">
    <active>true</active>
    <amount>true</amount>
    <dateType>0</dateType>
    <developerName>AE_Revenue_Split</developerName>
    <hasProductFamily>false</hasProductFamily>
    <masterLabel>AE Revenue Split</masterLabel>
    <opportunitySplitType>Revenue</opportunitySplitType>
    <quantity>false</quantity>
    <roleType>R</roleType>
</ForecastingType>
```

`opportunitySplitType` "Indicates whether the forecasting type has a split type and, if so, the name
of the split type" (api_meta.txt:75253–75254); the guide's own sample uses `Custom_Revenue` and
`Revenue` (api_meta.txt:75316, 75330). Everything else about forecast types —
`ForecastingSettings`, `ForecastingSourceDefinition`, quotas, adjustments — belongs to
`admin/collaborative-forecasts`.

---

## 7. Retrieve, check, deploy

```bash
# 1. Pull the current shape out of the source org before changing anything.
sf project retrieve start \
  --metadata "Settings:Opportunity" \
  --metadata "BusinessProcess:Opportunity.New Business" \
  --metadata "RecordType:Opportunity.New_Business" \
  --metadata "PathAssistant:Opportunity_New_Business_Path" \
  --metadata "StandardValueSet:OpportunityStage" \
  --target-org sourceOrg

# 2. Run the skill-local checker over the retrieved tree.
python3 skills/admin/opportunity-management/scripts/check_opportunity_management.py \
  --manifest-dir force-app/main/default

# 3. Validate-only against the target org, running the local tests.
sf project deploy validate \
  --manifest manifest/package.xml \
  --test-level RunLocalTests \
  --target-org targetOrg

# 4. Deploy.
sf project deploy start \
  --manifest manifest/package.xml \
  --target-org targetOrg
```

Deploy order matters and the manifest does not express it. The stage values
(`StandardValueSet:OpportunityStage`) must exist before a `BusinessProcess` can list them, and the
business process must exist before the record type's `<businessProcess>` resolves. A single manifest
containing all three is fine — the platform resolves within one deploy — but a *partial* manifest
that ships the process without the values fails on the missing picklist value.

---

## 8. Verify after deploy

**8a. The stage ladder is coherent** — probabilities monotonic, forecast categories mapped, exactly
one won stage and at least one closed-lost stage.

```sql
SELECT MasterLabel, ApiName, SortOrder, DefaultProbability,
       ForecastCategoryName, IsActive, IsClosed, IsWon
FROM OpportunityStage
ORDER BY SortOrder
```

`OpportunityStage` supports only `describeSObjects()`, `query()`, `retrieve()`
(object_reference.txt:195438–195439) — it is read-only, so this is a verification query, never a
fix-up path. Fixes go back through `StandardValueSet`.

**8b. Pipeline distribution by stage and category** — catches a stage that ships with the wrong
forecast bucket, which is invisible until a forecast period closes.

```sql
SELECT StageName, ForecastCategoryName, COUNT(Id) Deals, SUM(Amount) Pipeline
FROM Opportunity
WHERE IsClosed = FALSE
GROUP BY StageName, ForecastCategoryName
ORDER BY StageName
```

Any row where `ForecastCategoryName` differs from the `OpportunityStage.ForecastCategoryName` for
the same stage is a per-record override — legal, because the field is "implied, but not directly
controlled, by the `StageName` field. You can override this field to a different value than is
implied by the `StageName` value" (object_reference.txt:192487–192489) — but a large count means
an integration is writing it.

**8c. Stage movement is being recorded.**

```sql
SELECT Id, Name, StageName, LastStageChangeDate, LastStageChangeInDays
FROM Opportunity
WHERE IsClosed = FALSE AND LastStageChangeInDays > 60
ORDER BY LastStageChangeInDays DESC
```

`LastStageChangeDate` is "the date of the last change made to the Stage field on this opportunity
record", v52.0+; `LastStageChangeInDays` is "current date minus the last_stage_change_date", and is
"available in API version 52.0 and later **if you enabled Pipeline Inspection**"
(object_reference.txt:192706–192724). If the org has not enabled Pipeline Inspection, fall back to
`OpportunityHistory`, which "represents the history of a change to the Amount, Probability, Stage,
**or Close Date** fields" (object_reference.txt:193618–193619) — see `references/gotchas.md`
Gotcha 12 before treating its row count as a stage count.

**8d. Revenue splits total 100 on every validated split type.**

```sql
SELECT OpportunityId, SUM(SplitPercentage) TotalPct
FROM OpportunitySplit
WHERE SplitType.IsTotalValidated = TRUE
GROUP BY OpportunityId
HAVING SUM(SplitPercentage) != 100
```

An empty result is the pass condition. `SplitPercentage`: "If the split type is validated to a 100%
total, this number can range from 0 to 100. If the total isn't validated, this number can range from
0 to 1,000" (object_reference.txt:195208–195212) — so run the same query with
`IsTotalValidated = FALSE` to see overlay totals, and expect values well above 100 there by design.

**8e. Setup check that no query covers.** Splits enablement, split-type creation, and whether the
Path component is actually on the Lightning record page are all Setup-only states. Confirm in
Setup → Opportunity Settings, Setup → Opportunity Splits, and Lightning App Builder respectively;
a green deploy of §1–§4 proves none of them.
