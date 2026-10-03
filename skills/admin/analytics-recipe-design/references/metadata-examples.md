# Metadata Examples: Analytics Recipe Design

A deployable worked example for the Lookup-enrichment recipe in `examples.md` Example 1: an Opportunity dataset enriched with Account industry, protected by a row-level predicate, scheduled after the local sync, and promoted between orgs.

Grounding: Metadata API Developer Guide, WaveRecipe and WaveApplication (`api_meta L138986-139058`, `L138608-138650`); Data Prep Recipe REST API Developer Guide (`salesforce_recipes_api L420-616`, Join Parameters Input `L2770-2795`); CRM Analytics REST API Developer Guide, Schedule resource (`bi_dev_guide_rest L1480-1570`, `L6266-6300`). Element names not found in those guides are marked UNVERIFIED.

## 1. Recipe metadata

`WaveRecipe` extends `MetadataWithContent`, uses the `.wdpr` suffix, and lives in the `wave` folder (API 41.0 and later). The recipe body is the content file; the fields below are the metadata.

`force-app/main/default/wave/Opportunity_Enriched.wdpr-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<WaveRecipe xmlns="http://soap.sforce.com/2006/04/metadata">
    <application>Sales_Analytics</application>
    <dataflow>02KB0000000b5c7MAA</dataflow>
    <format>R3</format>
    <masterLabel>Opportunity Enriched</masterLabel>
    <securityPredicate>'OwnerId' == "$User.Id"</securityPredicate>
    <targetDatasetAlias>Opportunity_Enriched</targetDatasetAlias>
</WaveRecipe>
```

| Element | Value here | Notes |
|---|---|---|
| `application` | `Sales_Analytics` | Internal name of the Analytics app that holds the recipe |
| `dataflow` | `02KB...` | Required. The recipe's dataflow ID. Retrieve it from the source org; do not type it. UNVERIFIED (2026-10-03): how a target org resolves a source-org ID on deploy |
| `format` | `R3` | Recipes created at API 48 or later can only be R3 (`salesforce_recipes_api L459`) |
| `masterLabel` | `Opportunity Enriched` | Required. Name shown in the UI |
| `securityPredicate` | owner predicate | Applies when the dataset is created; later edits in the recipe have no effect (gotcha 5) |
| `targetDatasetAlias` | `Opportunity_Enriched` | Dataset the recipe writes |

UNVERIFIED (2026-10-03): the guide's sample shows `<content xsi:nil="true"/>` inside `WaveRecipe`. In source format the content travels as `Opportunity_Enriched.wdpr` beside this file, following the usual `MetadataWithContent` pattern; retrieve the pair rather than authoring the content file by hand.

## 2. The app that shares the dataset

`force-app/main/default/wave/Sales_Analytics.wapp-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<WaveApplication xmlns="http://soap.sforce.com/2006/04/metadata">
    <assetIcon>/analytics/wave/web/proto/images/app/icons/11.png</assetIcon>
    <description>Opportunity datasets enriched with Account attributes</description>
    <folder>Sales_Analytics</folder>
    <masterLabel>Sales Analytics</masterLabel>
    <shares>
        <accessLevel>View</accessLevel>
        <sharedTo>Sales_Reps</sharedTo>
        <sharedToType>Group</sharedToType>
    </shares>
    <shares>
        <accessLevel>Manage</accessLevel>
        <sharedTo>Analytics_Admins</sharedTo>
        <sharedToType>Group</sharedToType>
    </shares>
</WaveApplication>
```

App sharing decides who can open the dataset. The security predicate decides which rows they see. Both are needed.

## 3. package.xml

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Sales_Analytics</members>
        <name>WaveApplication</name>
    </types>
    <types>
        <members>Opportunity_Enriched</members>
        <name>WaveDataflow</name>
    </types>
    <types>
        <members>Opportunity_Enriched</members>
        <name>WaveRecipe</name>
    </types>
    <version>67.0</version>
</Package>
```

The `WaveDataflow` member is listed by name because wildcard retrieval of `WaveRecipe` "doesn't return the recipe's associated dataflows". UNVERIFIED (2026-10-03): the recipe's dataflow API name is assumed to match the recipe name here; read the real name from a retrieve of the source org.

## 4. What the recipe definition looks like over REST

`GET /services/data/v67.0/wave/recipes/05vB0000000xxxxxxx?format=R3` returns the definition. This excerpt shows the node map for the enrichment design. Review it; do not hand-author it for a POST, because `recipeDefinition` also requires a `ui` object that Data Manager writes.

```json
{
  "format": "R3",
  "recipeDefinition": {
    "name": "Opportunity_Enriched",
    "runMode": "Full",
    "version": "67.0",
    "nodes": {
      "LOAD_OPPS": {
        "action": "load",
        "parameters": {
          "dataset": { "label": "Opportunities", "name": "opportunity", "type": "analyticsDataset" },
          "fields": ["Id", "AccountId", "Amount", "StageName", "CloseDate"]
        },
        "sources": []
      },
      "LOAD_ACCOUNTS": {
        "action": "load",
        "parameters": {
          "dataset": { "label": "Accounts", "name": "account", "type": "analyticsDataset" },
          "fields": ["Id", "Industry", "AnnualRevenue"]
        },
        "sources": []
      },
      "JOIN_ACCOUNT": {
        "action": "join",
        "parameters": {
          "joinType": "Lookup",
          "leftKeys": ["AccountId"],
          "leftQualifier": "Opportunity",
          "rightKeys": ["Id"],
          "rightQualifier": "Account"
        },
        "sources": ["LOAD_OPPS", "LOAD_ACCOUNTS"]
      },
      "OUTPUT0": {
        "action": "save",
        "parameters": {
          "dataset": { "folderName": "Sales_Analytics", "label": "Opportunity Enriched", "name": "Opportunity_Enriched", "type": "analyticsDataset" },
          "fields": []
        },
        "sources": ["JOIN_ACCOUNT"]
      }
    }
  },
  "targetDataflowId": "02KB000000xxxxxxxx"
}
```

`joinType`, `leftKeys`, `leftQualifier`, `rightKeys`, and `rightQualifier` are the required Join Parameters Input properties. The load and save shapes follow the guide's Inspect Recipe Nodes example. UNVERIFIED (2026-10-03): the exact casing of the `action` value for joins in a GET response (`join`) is inferred from the guide's lowercase `load`, `filter`, and `save` examples.

## 5. Schedule and run after deploy

Schedules are not part of the metadata. Recreate the schedule in each target org.

```bash
# Event-based: run after the Salesforce Local connection syncs
curl -X PUT "$INSTANCE/services/data/v67.0/wave/asset/05vB0000000xxxxxxx/schedule" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"frequency":"eventdriven","triggerRule":"$ALL_SALESFORCE_OBJECTS"}'

# First run now, using the targetDataflowId from the GET above
curl -X POST "$INSTANCE/services/data/v67.0/wave/dataflowjobs" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"dataflowId":"02KB000000xxxxxxxx","command":"start"}'
```

## Deploy order

1. Public groups named in the app shares (`Sales_Reps`, `Analytics_Admins`).
2. `WaveApplication`.
3. `WaveDataflow` and `WaveRecipe` together.
4. Schedule (REST, per org).

## Verification

- `GET /wave/recipes/<id>?format=R3` in the target org returns the recipe with `"format":"R3"` and a `targetDataflowId`.
- `GET /wave/asset/<id>/schedule` returns the event-based schedule.
- After the first job, the output dataset row count equals the Opportunity input row count (Lookup keeps every left row).
- A user outside the predicate sees no rows they do not own.
