# Examples: Analytics Data Preparation (XMD and External Data)

Paths, methods, and properties come from the CRM Analytics REST API Developer Guide (Xmd Resources, Dataset Resource), the Analytics XMD Developer Guide, and the Analytics External Data API Developer Guide, all Summer '26.

## Example 1: Relabel Two Fields on the Current Dataset Version

**Context:** A recipe registers `Acct_Tier__c` and `Prod_Cat__c`, and dashboard filters show those API names.

**Problem:** The first attempt sent `PATCH /wave/datasets/{id}/xmds/main` with two entries. The XMD resource documents no PATCH, and PUT is allowed only on the user type, so nothing changed.

**Solution:**
1. `GET /services/data/v67.0/wave/datasets/Opportunity_Pipeline` and read the current version ID (shown here as `0FcXX0000000001`).
2. `GET /services/data/v67.0/wave/datasets/Opportunity_Pipeline/versions/0FcXX0000000001/xmds/user` and save it as `xmd/Opportunity_Pipeline.user.before.json`.
3. Edit only the two `label` values in a copy, keeping every other entry. File: `xmd/Opportunity_Pipeline.user.xmd.json` (abridged to the relevant arrays; the real file keeps every entry from step 2):

```json
{
  "dimensions": [
    {"field": "Acct_Tier__c", "label": "Account Tier", "showInExplorer": true,
     "members": [{"member": "T1", "label": "Tier 1 (Strategic)"}]},
    {"field": "Prod_Cat__c", "label": "Product Category", "showInExplorer": true}
  ],
  "measures": [
    {"field": "Amount", "label": "Amount",
     "format": {"customFormat": "[\"$#,###.##\",1]"}}
  ],
  "dates": [],
  "derivedDimensions": [],
  "derivedMeasures": [],
  "organizations": [],
  "showDetailsDefaultFields": []
}
```

4. `PUT /services/data/v67.0/wave/datasets/Opportunity_Pipeline/versions/0FcXX0000000001/xmds/user` with the complete edited file.
5. Open a lens and confirm the labels and the member label "Tier 1 (Strategic)."

**Why it works:** The user XMD is the only writable XMD type through REST, and the full document is sent because each upload overwrites. The `format.customFormat` value uses the shape shown in the XMD guide's Format Measures examples (`"[\"$#,###.##\",1]"`), and member labels use the `members` array shown in Change Display Labels for Dataset Fields and Values.

---

## Example 2: Territory Mapping From an ERP CSV With the External Data API

**Context:** Sales operations maintains a territory-to-region table outside Salesforce and wants it as a dataset that recipes can join.

**Problem:** A first upload with no metadata file produced a dataset where every column was text, and a second upload of a header-less CSV lost one row per 10 MB part.

**Solution:** Send a metadata JSON, insert the header, upload parts, and process. File: `external/territory_map.metadata.json`:

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
      "connector": "ErpCsvConnector",
      "fullyQualifiedName": "TerritoryMap",
      "label": "Territory Map",
      "name": "TerritoryMap",
      "fields": [
        {"fullyQualifiedName": "TerritoryMap.Territory_Code", "name": "Territory_Code",
         "label": "Territory Code", "type": "Text", "isUniqueId": true},
        {"fullyQualifiedName": "TerritoryMap.Region_Name", "name": "Region_Name",
         "label": "Region Name", "type": "Text"},
        {"fullyQualifiedName": "TerritoryMap.Quota", "name": "Quota",
         "label": "Annual Quota", "type": "Numeric", "precision": 18, "scale": 2,
         "defaultValue": "0"}
      ]
    }
  ]
}
```

Then, through any Salesforce API:
1. Insert `InsightsExternalData` with `Format` = `Csv`, `EdgemartAlias` = `TerritoryMap`, `MetadataJson` = the file above (Base64-encoded when using REST), `Operation` = `Overwrite`, `Action` = `None`.
2. Split the CSV into parts under 10 MB and insert each as `InsightsExternalDataPart` with `InsightsExternalDataId` = the header ID and `PartNumber` = 1, 2, 3...
3. Update the header `Action` to `Process` and poll `Status`.
4. For later refreshes, insert a new header with `Operation` = `Upsert` (keyed on the single text unique ID) or `Append`, and `Mode` = `Incremental` for faster appends.

**Why it works:** The metadata file types the columns, `numberOfLinesToIgnore` matches the header row, the numeric field has a default and a precision within 18, and exactly one text field is the unique ID.
