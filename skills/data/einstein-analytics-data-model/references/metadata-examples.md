# Metadata and REST Examples: Einstein Analytics Data Model (XMD)

Two deployable paths. Use the REST path for a one-org fix. Use the `WaveXmd` path when the formatting must move between orgs.

## Path A: REST update of the current version's user XMD

**Step 1: find the current version.**

```http
GET /services/data/v67.0/wave/datasets/Opportunity_Pipeline
Authorization: Bearer [REDACTED]
```

Response (trimmed):

```json
{
  "id": "0Fb5e000000AbCdCAI",
  "name": "Opportunity_Pipeline",
  "currentVersionId": "0Fc5e000000WxYzCAI",
  "versionsUrl": "/services/data/v67.0/wave/datasets/0Fb5e000000AbCdCAI/versions"
}
```

**Step 2: back up, then write the complete user XMD.**

```http
GET /services/data/v67.0/wave/datasets/0Fb5e000000AbCdCAI/versions/0Fc5e000000WxYzCAI/xmds/user
```

```http
PUT /services/data/v67.0/wave/datasets/0Fb5e000000AbCdCAI/versions/0Fc5e000000WxYzCAI/xmds/user
Content-Type: application/json
Authorization: Bearer [REDACTED]

{
  "dimensions": [
    {
      "field": "StageName",
      "label": "Stage",
      "members": [
        { "member": "Closed Won", "label": "Closed (Won)" },
        { "member": "Closed Lost", "label": "Closed (Lost)" }
      ],
      "showInExplorer": true
    },
    { "field": "Owner_Email", "showInExplorer": false }
  ],
  "measures": [
    {
      "field": "Amount",
      "label": "Amount (USD)",
      "format": { "customFormat": "[\"$#,###,###.##\",1]" },
      "showInExplorer": true
    }
  ],
  "derivedMeasures": [
    { "field": "*", "label": "Opportunities" }
  ]
}
```

The response body is an Xmd representation with `"type": "user"`. Check that `errorMessage` is absent or empty.

Grounding: URL, methods, and PUT body shape are from the CRM Analytics REST API Developer Guide (262), "Xmd Resource." The `members`, `showInExplorer`, `customFormat`, and `"field": "*"` row-count label forms are from the XMD Developer Guide (262). `Owner_Email` is hidden for clutter only; it stays reachable through SAQL.

## Path B: WaveXmd metadata (Primary User XMD)

**File:** `wave/Opportunity_Pipeline.xmd` in a Metadata API (mdapi) project. The Metadata API guide gives the suffix `.xmd` and the `wave` folder. UNVERIFIED (2026-10-03): the file name the sf CLI source format uses for this type.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<WaveXmd xmlns="http://soap.sforce.com/2006/04/metadata">
    <dataset>Opportunity_Pipeline</dataset>
    <dimensions>
        <field>StageName</field>
        <isDerived>false</isDerived>
        <label>Stage</label>
        <members>
            <label>Closed (Won)</label>
            <member>Closed Won</member>
            <sortIndex>0</sortIndex>
        </members>
        <members>
            <label>Closed (Lost)</label>
            <member>Closed Lost</member>
            <sortIndex>1</sortIndex>
        </members>
        <showInExplorer>true</showInExplorer>
        <sortIndex>0</sortIndex>
    </dimensions>
    <measures>
        <field>Amount</field>
        <formatCustomFormat>[&quot;$#,###,###.##&quot;,1]</formatCustomFormat>
        <isDerived>false</isDerived>
        <label>Amount (USD)</label>
        <showInExplorer>true</showInExplorer>
        <sortIndex>0</sortIndex>
    </measures>
</WaveXmd>
```

Element names and the required flags (`dataset`, `field`, `isDerived`, `sortIndex`, `member`) are from the Metadata API Developer Guide (262), "WaveXmd," "WaveXmdDimension," "WaveXmdDimensionMember," and "WaveXmdMeasure." UNVERIFIED (2026-10-03): the exact value format the `dataset` element expects (dataset API name is assumed here) and the component's `fullName`.

**package.xml member form:**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Opportunity_Pipeline</members>
        <name>WaveXmd</name>
    </types>
    <types>
        <members>Opportunity_Pipeline</members>
        <name>WaveDataset</name>
    </types>
    <version>67.0</version>
</Package>
```

`WaveDataset` (suffix `.wds`, API 37.0 and later) and `WaveXmd` (API 39.0 and later) both support the `*` wildcard in package.xml.

**Deploy order and verification:**

1. Deploy the dataset container (`WaveDataset`) if the target org does not have it.
2. Deploy `WaveXmd`.
3. Run the dataflow or recipe that refreshes the dataset. The Primary User XMD applies only after that run.
4. GET the new version's user XMD and confirm the labels and an empty `errorMessage`.
5. Do not edit this dataset's XMD in the UI afterwards. A UI or REST edit makes the next MDAPI retrieve return an empty file.
