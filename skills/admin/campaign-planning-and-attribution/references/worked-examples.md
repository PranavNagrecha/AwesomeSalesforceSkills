# Worked Examples — Campaign Planning And Attribution

One scenario carried end to end: **Acme Cloud's demand-gen team planning Q3 FY27**.
Three channels under one program, member statuses per campaign type, an attribution
model decision, the ROI queries, the report type, and the acceptance tests.

Every XML element, enum value and field name below is quoted from the Metadata API
Developer Guide or the Object Reference; the line ranges are given per block so the
next author can re-check them. Line numbers are into the plain-text extracts of the
Summer '26 (v62) PDFs:
<https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf> and
<https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf>.

---

## Where the files live

```text
force-app/main/default/
├── settings/
│   └── Campaign.settings-meta.xml                       # CampaignSettings
├── campaignInfluenceModels/
│   ├── Salesforce_Model.campaignInfluenceModel-meta.xml
│   ├── Acme_First_Touch.campaignInfluenceModel-meta.xml
│   └── Acme_Last_Touch.campaignInfluenceModel-meta.xml
├── objects/Campaign/
│   ├── fields/Acme_Region__c.field-meta.xml
│   ├── fields/Acme_Funnel_Stage__c.field-meta.xml
│   └── recordTypes/Acme_Demand_Gen.recordType-meta.xml
├── standardValueSets/
│   ├── CampaignType.standardValueSet-meta.xml
│   └── CampaignMemberStatus.standardValueSet-meta.xml
├── reportTypes/
│   └── Acme_Campaign_Influence_by_Model.reportType-meta.xml
└── manifest/package.xml
```

`CampaignInfluenceModel` files live in the `campaignInfluenceModels` directory with the
extension `.campaignInfluenceModel`, and the file name matches the model name
(api_meta.txt:31882–31883). The type is available in API 38.0 and later
(api_meta.txt:31887). `CampaignSettings` lives in one `Campaign.settings` file in the
`settings` folder and is available in API 48.0 and later (api_meta.txt:111523–111528).

---

## 1. The campaign plan record — the artefact this skill produces

This is the machine-readable form of Acme's quarter plan. It is the input to
`scripts/check_campaign_planning_and_attribution.py --file acme-q3-campaign-plan.yaml`,
and every downstream XML block on this page is generated from one of its sections.

```yaml
plan_id: ACME-Q3FY27-DEMANDGEN
quarter: FY27-Q3
owner: marketing.ops@acme.example
naming_convention: "^(FY\\d{2})-Q[1-4]-(AMER|EMEA|APAC)-(PROG|EMAIL|EVENT|ADS|WEBINAR)-[A-Za-z0-9]+$"
hierarchy_max_depth: 3

campaigns:
  - campaign_id: CMP-001
    name: FY27-Q3-AMER-PROG-PipelineDrive
    type: Other
    record_type: Acme_Demand_Gen
    parent: null
    level: 1
    is_active: true
    budgeted_cost: 250000
    expected_revenue: 1500000
    owns_budget: true
    member_status_set: program
  - campaign_id: CMP-002
    name: FY27-Q3-AMER-WEBINAR-PlatformSeries
    type: Webinar
    record_type: Acme_Demand_Gen
    parent: CMP-001
    level: 2
    is_active: true
    actual_cost: 60000
    member_status_set: event
  - campaign_id: CMP-003
    name: FY27-Q3-AMER-ADS-LinkedInABM
    type: Advertisement
    record_type: Acme_Demand_Gen
    parent: CMP-001
    level: 2
    is_active: true
    actual_cost: 120000
    member_status_set: advertising
  - campaign_id: CMP-004
    name: FY27-Q3-AMER-EMAIL-NurtureTrack
    type: Email
    record_type: Acme_Demand_Gen
    parent: CMP-001
    level: 2
    is_active: true
    actual_cost: 18000
    member_status_set: email

member_status_sets:
  - set_id: program
    statuses:
      - label: Planned
        is_default: true
        has_responded: false
        sort_order: 1
      - label: Engaged
        is_default: false
        has_responded: true
        sort_order: 2
  - set_id: event
    statuses:
      - label: Invited
        is_default: true
        has_responded: false
        sort_order: 1
      - label: Registered
        is_default: false
        has_responded: true
        sort_order: 2
      - label: Attended
        is_default: false
        has_responded: true
        sort_order: 3
      - label: No Show
        is_default: false
        has_responded: false
        sort_order: 4
  - set_id: advertising
    statuses:
      - label: Targeted
        is_default: true
        has_responded: false
        sort_order: 1
      - label: Clicked Through
        is_default: false
        has_responded: true
        sort_order: 2
  - set_id: email
    statuses:
      - label: Sent
        is_default: true
        has_responded: false
        sort_order: 1
      - label: Opened
        is_default: false
        has_responded: false
        sort_order: 2
      - label: Clicked
        is_default: false
        has_responded: true
        sort_order: 3
      - label: Unsubscribed
        is_default: false
        has_responded: false
        sort_order: 4

attribution:
  default_model: Acme_First_Touch
  models:
    - developer_name: Salesforce_Model
      model_type: Primary Campaign Source Model
      is_active: true
      is_default_model: false
      is_model_locked: true
      record_preference: AllRecords
    - developer_name: Acme_First_Touch
      model_type: Custom Model
      is_active: true
      is_default_model: true
      is_model_locked: true
      record_preference: RecordsWithAttribution
    - developer_name: Acme_Last_Touch
      model_type: Custom Model
      is_active: true
      is_default_model: false
      is_model_locked: true
      record_preference: RecordsWithAttribution

source_skills:
  - skills/admin/campaign-planning-and-attribution
  - skills/admin/report-type-strategy
  - skills/admin/opportunity-management
```

### How to read it

- `hierarchy_max_depth` is Acme's own governance number, not a platform limit. None of
  the eight official extracts states a maximum Campaign hierarchy depth
  — UNVERIFIED (2026-09-05): the widely-repeated "5 levels" figure is not in the Object
  Reference, the Metadata API guide, or the App Limits cheat sheet (a `grep -i campaign`
  over `salesforce_app_limits_cheatsheet.txt` returns nothing at all). Confirm the ceiling
  in the target org before designing to it, and set `hierarchy_max_depth` to the number
  the business actually needs.
- `naming_convention` is a regex the checker enforces. Campaign `Name` is limited to 80
  characters (object_reference.txt:57539–57544), so the convention has to fit inside that.
- `type` values must exist in the `CampaignType` standard value set, which maps to
  `Campaign.Type` (api_meta.txt:141860). `Campaign.Type` is a picklist with a
  40-character limit (object_reference.txt:57812–57817); `Campaign.Status` is likewise
  40 characters (object_reference.txt:57678–57683).
- Exactly one status per set carries `is_default: true` and at least one carries
  `has_responded: true`. Beginning with API version 39.0 there must be a default
  `CampaignMemberStatus` on every campaign, and at least one status per campaign must
  have `hasResponded` = true (object_reference.txt:58627, 58636). The checker fails the
  plan if either rule is broken.
- `owns_budget` records the deliberate choice that the program level carries
  `BudgetedCost` / `ExpectedRevenue` while the tactic level carries `ActualCost`.
- `default_model` must name exactly one model whose `is_default_model` is true —
  `IsDefaultModel` can only be true for one model at a time
  (object_reference.txt:58066).

---

## 2. `CampaignSettings` — the org switch the whole design rests on

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CampaignSettings xmlns="http://soap.sforce.com/2006/04/metadata">
    <enableCampaignInfluence2>true</enableCampaignInfluence2>
    <enableB2bmaCampaignInfluence2>false</enableB2bmaCampaignInfluence2>
    <enableAccountsAsCM>false</enableAccountsAsCM>
    <enableAIAttribution>false</enableAIAttribution>
</CampaignSettings>
```

### How to read it

| Element | What the guide says | Line |
|---|---|---|
| `enableCampaignInfluence2` | "Indicates whether Customizable Campaign Influence is enabled (true) or not (false). When true, Campaign Influence 1.0 is hidden from users and is no longer active. The default value is **true**." | api_meta.txt:111568–111571 |
| `enableAutoCampInfluenceDisabled` | Whether Salesforce creates Campaign Influence information. "`enableCampaignInfluence2` must be **false** to use this setting." | api_meta.txt:111556–111560 |
| `enableB2bmaCampaignInfluence2` | Whether the org can access campaign influence models from other systems such as Pardot. "`enableCampaignInfluence2` must be true to use this setting." Default false. | api_meta.txt:111561–111564 |
| `enableAccountsAsCM` | Whether accounts can be campaign members. Default false. API 51.0+. | api_meta.txt:111543–111545 |
| `enableAIAttribution` / `aiAttributionTimeframe` | Einstein Attribution, and the months between opportunity creation and an engagement activity that Einstein scans. "The value must be a multiple of three, up to 24." API 49.0+. | api_meta.txt:111533–111541 |

The design consequence is the one most plans get backwards: **CCI and Campaign
Influence 1.0 are mutually exclusive by contract, not merely in conflict.** The
`enableAutoCampInfluenceDisabled` switch is only usable while
`enableCampaignInfluence2` is false, and turning CCI on hides 1.0. Set
`enableB2bmaCampaignInfluence2` only when an external system genuinely publishes models
into the org — leaving it true with nothing publishing produces empty model rows in the
influence picker.

`enableCampaignHistoryTrackEnabled`, `enableCampaignMemberTWCF` and
`enableSuppressNoValueCI2` are documented as read-only and reserved for system use
(api_meta.txt:111566, 111573, 111585) — retrieve them, never author them.

---

## 3. `CampaignInfluenceModel` — Acme's three models

The guide is explicit about the boundary: "You can't configure Customizable Campaign
Influence via the Metadata API, but you can add a campaign influence model"
(api_meta.txt:31873–31874). Enabling the feature is the `CampaignSettings` deploy in
§ 2; the models are these files.

The Salesforce-supplied default model, retrieved as-is (this is the guide's own sample
definition at api_meta.txt:31938–31945, reformatted onto separate lines):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CampaignInfluenceModel xmlns="http://soap.sforce.com/2006/04/metadata">
    <isActive>true</isActive>
    <isDefaultModel>false</isDefaultModel>
    <isModelLocked>true</isModelLocked>
    <modelDescription>Primary Campaign gets 100% of the revenue share</modelDescription>
    <name>Salesforce Model</name>
    <recordPreference>AllRecords</recordPreference>
</CampaignInfluenceModel>
```

Acme's first-touch model, which becomes the default:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CampaignInfluenceModel xmlns="http://soap.sforce.com/2006/04/metadata">
    <isActive>true</isActive>
    <isDefaultModel>true</isDefaultModel>
    <isModelLocked>true</isModelLocked>
    <modelDescription>100% of revenue share to the earliest campaign the opportunity
contact was a member of. Populated nightly by AcmeInfluenceWriter; locked so the batch
is the only writer.</modelDescription>
    <name>Acme First Touch</name>
    <recordPreference>RecordsWithAttribution</recordPreference>
</CampaignInfluenceModel>
```

Acme's last-touch model, non-default (the guide's second sample at
api_meta.txt:31952–31960, with Acme's description):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CampaignInfluenceModel xmlns="http://soap.sforce.com/2006/04/metadata">
    <isActive>true</isActive>
    <isDefaultModel>false</isDefaultModel>
    <isModelLocked>true</isModelLocked>
    <modelDescription>This model gives 100% influence attribution to the last campaign
that touched the contact.</modelDescription>
    <name>Acme Last Touch</name>
    <recordPreference>RecordsWithAttribution</recordPreference>
</CampaignInfluenceModel>
```

### How to read it

| Element | Grounded behaviour | Line |
|---|---|---|
| `isActive` | "Active models can generate campaign influence records. **Deactivating a model deletes its campaign influence records.** Custom models are always active and this field is ignored." API 40.0+. | api_meta.txt:31892–31895 |
| `isDefaultModel` | Required. "Only campaign influence records associated with the default model appear on campaigns and opportunities. You can only have one default model at a time. A model must be active to become the default model." | api_meta.txt:31897–31902 |
| `isModelLocked` | Required. "Campaign Influence records for locked models can be manipulated only via the API." | api_meta.txt:31904–31905 |
| `name` | Required. "A unique name for the model." | api_meta.txt:31918 |
| `recordPreference` | `AllRecords` creates records regardless of the revenue attribution percentage; `RecordsWithAttribution` creates records only when the revenue attribution is greater than 0%. API 41.0+. | api_meta.txt:31920–31926 |

The read side of the same object adds two facts the metadata type does not carry.
`CampaignInfluenceModel` as an sObject is **read-only** — its supported calls are
`describeSObjects()`, `query()`, `retrieve()` only (object_reference.txt:58011–58012) —
and its `ModelType` picklist is a restricted, closed set:

| `ModelType` | Meaning |
|---|---|
| `1` | Primary Campaign Source Model |
| `2` | Custom Model |
| `3` | First Touch Model |
| `4` | Last Touch Model |
| `5` | Even Distribution Model |
| `6` | Data-Driven Model |

(object_reference.txt:58105–58118.) The `CampaignInfluenceModel` **metadata** type has no
`modelType` element, so a model added by deploy lands as a custom model; the six values
above are what a query can return, and the checker validates the plan's `model_type`
against exactly this list.

`IsDefaultModel` also decides visibility, not just reporting default: records associated
with the default model appear in the Campaign Influence related list on opportunities,
the Influenced Opportunities related list on campaigns, and the Campaign Statistics
section on campaigns (object_reference.txt:58057–58065). Everything else is
report-and-query only.

**UNVERIFIED (2026-09-05):** time-decay and position-based / U-shaped attribution models,
and the Marketing Cloud Account Engagement Multi-Touch Attribution app that supplies
them, appear nowhere in the eight official extracts — `grep -i "time.decay\|u-shaped\|
position-based\|multi-touch"` over `object_reference.txt` and `api_meta.txt` returns no
hits. The only native model vocabulary the guides define is the six-value `ModelType`
list above. Treat any weighting percentages for those models as a vendor claim to
confirm in the org, not a platform fact.

---

## 4. Campaign custom fields and record type

Dimensions that would otherwise be encoded as hierarchy levels belong on the record.
This is the Metadata API's own `CustomObject` shape for picklist fields
(api_meta.txt:44748–44796) and record types (api_meta.txt:43182–43192,
api_meta.txt:45111–45126), applied to `Campaign`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomObject xmlns="http://soap.sforce.com/2006/04/metadata">
    <fields>
        <fullName>Acme_Region__c</fullName>
        <label>Region</label>
        <picklist>
            <picklistValues>
                <fullName>AMER</fullName>
                <default>true</default>
            </picklistValues>
            <picklistValues>
                <fullName>EMEA</fullName>
                <default>false</default>
            </picklistValues>
            <picklistValues>
                <fullName>APAC</fullName>
                <default>false</default>
            </picklistValues>
            <sorted>false</sorted>
        </picklist>
        <type>Picklist</type>
    </fields>
    <fields>
        <fullName>Acme_Funnel_Stage__c</fullName>
        <label>Funnel Stage</label>
        <picklist>
            <picklistValues>
                <fullName>Awareness</fullName>
                <default>true</default>
            </picklistValues>
            <picklistValues>
                <fullName>Consideration</fullName>
                <default>false</default>
            </picklistValues>
            <picklistValues>
                <fullName>Decision</fullName>
                <default>false</default>
            </picklistValues>
            <sorted>false</sorted>
        </picklist>
        <type>Picklist</type>
    </fields>
    <recordTypes>
        <fullName>Acme_Demand_Gen</fullName>
        <active>true</active>
        <label>Demand Gen</label>
        <picklistValues>
            <picklist>Type</picklist>
            <values>
                <fullName>Webinar</fullName>
                <default>false</default>
            </values>
            <values>
                <fullName>Email</fullName>
                <default>false</default>
            </values>
            <values>
                <fullName>Advertisement</fullName>
                <default>false</default>
            </values>
            <values>
                <fullName>Other</fullName>
                <default>true</default>
            </values>
        </picklistValues>
    </recordTypes>
</CustomObject>
```

### How to read it

- `recordTypes` carries `fullName`, `active`, `label`, and `picklistValues`
  (api_meta.txt:45006–45041); `RecordTypePicklistValue` is `picklist` (required, the name
  of the picklist) plus `values` (api_meta.txt:45045–45052). The checker parses exactly
  this shape and asserts the record type's `Type` values are a subset of the plan's
  campaign types.
- The guide warns that Metadata API "doesn't retrieve specific picklist fields that are
  associated with a record type" (api_meta.txt:44987) — so a retrieve of this record type
  can come back without the `picklistValues` block you deployed. Keep the source file as
  the record of intent and let the checker, not a retrieve diff, be the gate.
- `description` on a record type is capped at 255 characters, and the guide explicitly
  advises against putting sensitive information in a record type's description, name or
  label because "users with access to an object can read all record type information for
  that object" (api_meta.txt:44977–44979).

---

## 5. Member statuses — the standard value set and the per-campaign object

Two different things share the name `CampaignMemberStatus`, and the plan needs both.

**The org-wide default list** is a `StandardValueSet` whose `fullName` is
`CampaignMemberStatus`, mapping to the `CampaignMember.Status` standard picklist
(api_meta.txt:141856). The shape is the guide's own `StandardValueSet` sample
(api_meta.txt:130786–130793):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<StandardValueSet xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>CampaignMemberStatus</fullName>
    <sorted>false</sorted>
    <standardValue>
        <fullName>Sent</fullName>
    </standardValue>
    <standardValue>
        <fullName>Responded</fullName>
    </standardValue>
</StandardValueSet>
```

```xml
<?xml version="1.0" encoding="UTF-8"?>
<StandardValueSet xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>CampaignType</fullName>
    <sorted>false</sorted>
    <standardValue>
        <fullName>Webinar</fullName>
    </standardValue>
    <standardValue>
        <fullName>Email</fullName>
    </standardValue>
    <standardValue>
        <fullName>Advertisement</fullName>
    </standardValue>
    <standardValue>
        <fullName>Other</fullName>
    </standardValue>
</StandardValueSet>
```

**The per-campaign list** is the `CampaignMemberStatus` sObject — "one or more member
status values defined for a campaign" (object_reference.txt:58593). It is not a metadata
type; there is no `.campaignMemberStatus` file. Its fields are `CampaignId`,
`HasResponded`, `IsDefault`, `Label` (limited to 765 characters,
object_reference.txt:58659), and `SortOrder` ("unique number order where this campaign
member status appears in the picklist", object_reference.txt:58666). Acme's event-set
rows therefore look like this, created per campaign rather than deployed:

```sql
SELECT CampaignId, Label, IsDefault, HasResponded, SortOrder
FROM CampaignMemberStatus
WHERE CampaignId = '701XXXXXXXXXXXXXXX'
ORDER BY SortOrder
```

| Label | IsDefault | HasResponded | SortOrder |
|---|---|---|---|
| Invited | true | false | 1 |
| Registered | false | true | 2 |
| Attended | false | true | 3 |
| No Show | false | false | 4 |

### How to read it

- `StandardValueSet` requires at least one picklist value in the `standardValue` array or
  the deploy errors (api_meta.txt:130769–130772), and it does **not** support the `*`
  wildcard in package.xml (api_meta.txt:130826–130828) — name each value set explicitly.
- `HasResponded` on the status object is what `Campaign.NumberOfResponses` counts:
  "the number of contacts and unconverted leads with a Member Status equivalent to
  'Responded' for the campaign" (object_reference.txt:57585–57591). The hierarchy
  equivalents are `HierarchyNumberOfResponses` (object_reference.txt:57353–57359) and
  `TotalNumberofResponses` (object_reference.txt:57795–57802).
- `CampaignMember.HasResponded` is read-only. "Controls the HasResponded flag on this
  object. You can't directly set the HasResponded flag… Each time you update this field,
  you implicitly update the HasResponded flag" — and "when you create or update campaign
  members, use the text value for Status instead of the ID from the CampaignMemberStatus
  object" (object_reference.txt:58504–58513). A load that sends status Ids silently
  misses.

---

## 6. The report type decision

Acme needs one report per model, side by side. `admin/report-type-strategy` owns the
join-design rules — read it before adding a second join here rather than reasoning from
this page. What is specific to attribution:

| Question | Acme's answer | Why |
|---|---|---|
| Base object | `CampaignInfluence` | It is the only object that carries `ModelId`, so it is the only base that lets one report separate models |
| Category | `campaigns` | A valid `ReportTypeCategory` value (api_meta.txt:105815) |
| Join | `Opportunity` | Brings `StageName`, `CloseDate`, `Amount` next to `RevenueShare` |
| Outer join | `false` | An influence row without an opportunity is meaningless |
| `deployed` | `true` | Required boolean; false leaves it invisible to report builders (api_meta.txt:105845–105846) |

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ReportType xmlns="http://soap.sforce.com/2006/04/metadata">
    <baseObject>CampaignInfluence</baseObject>
    <category>campaigns</category>
    <deployed>true</deployed>
    <description>Campaign influence rows with their opportunity, split by model.</description>
    <join>
        <outerJoin>false</outerJoin>
        <relationship>Opportunity</relationship>
    </join>
    <label>Campaign Influence by Model</label>
    <sections>
        <columns>
            <checkedByDefault>true</checkedByDefault>
            <field>CampaignId</field>
            <table>CampaignInfluence</table>
        </columns>
        <columns>
            <checkedByDefault>true</checkedByDefault>
            <field>ModelId</field>
            <table>CampaignInfluence</table>
        </columns>
        <columns>
            <checkedByDefault>true</checkedByDefault>
            <field>Influence</field>
            <table>CampaignInfluence</table>
        </columns>
        <columns>
            <checkedByDefault>true</checkedByDefault>
            <field>RevenueShare</field>
            <table>CampaignInfluence</table>
        </columns>
        <masterLabel>Campaign Influence</masterLabel>
    </sections>
</ReportType>
```

`baseObject`, `deployed`, `label`, `outerJoin` and `relationship` are all documented as
required; `ObjectRelationship.join` is recursive and "a maximum of four objects can be
joined in a custom report type" (api_meta.txt:105869–105874). Column entries take
`checkedByDefault`, `field` and `table`, all required except
`displayNameOverride` (api_meta.txt:105897–105916). The shape is the guide's own
sample definition (api_meta.txt:105924–105986) with Acme's objects substituted.

---

## 7. `package.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>*</members>
        <name>CampaignInfluenceModel</name>
    </types>
    <types>
        <members>Campaign</members>
        <name>CustomObject</name>
    </types>
    <types>
        <members>Campaign.Acme_Region__c</members>
        <members>Campaign.Acme_Funnel_Stage__c</members>
        <name>CustomField</name>
    </types>
    <types>
        <members>Campaign.Acme_Demand_Gen</members>
        <name>RecordType</name>
    </types>
    <types>
        <members>CampaignType</members>
        <members>CampaignMemberStatus</members>
        <name>StandardValueSet</name>
    </types>
    <types>
        <members>Acme_Campaign_Influence_by_Model</members>
        <name>ReportType</name>
    </types>
    <types>
        <members>Campaign</members>
        <name>Settings</name>
    </types>
    <version>62.0</version>
</Package>
```

### How to read it

Four different wildcard answers sit in this one manifest, and each is documented:

| Type | `*` allowed? | Source |
|---|---|---|
| `CampaignInfluenceModel` | **Yes** | api_meta.txt:31964–31966 |
| `RecordType` | **No** | api_meta.txt:45130–45132 |
| `StandardValueSet` | **No** | api_meta.txt:130826–130828 |
| `Settings` (`CampaignSettings`) | Only when retrieving *all* settings, never an individual one | api_meta.txt:111509–111511 |

All org settings metadata types are accessed in the manifest under the name `Settings`
(api_meta.txt:111519–111520) — `<name>CampaignSettings</name>` is not a valid manifest
entry, which is the most common deploy failure on this package.

---

## 8. Retrieve, check, deploy

```bash
# 1. Pull what the org already has, so the models you "create" are not duplicates.
sf project retrieve start \
  --metadata CampaignInfluenceModel \
  --metadata "Settings:Campaign" \
  --metadata "CustomObject:Campaign" \
  --target-org acme-uat

# 2. Lint the plan and the generated metadata before anything leaves the laptop.
python3 skills/admin/campaign-planning-and-attribution/scripts/\
check_campaign_planning_and_attribution.py \
  --file acme-q3-campaign-plan.yaml \
  --manifest-dir force-app/main/default

# 3. Validate-only against the target org.
sf project deploy start \
  --manifest manifest/package.xml \
  --dry-run \
  --target-org acme-uat

# 4. Deploy for real.
sf project deploy start \
  --manifest manifest/package.xml \
  --target-org acme-uat
```

Run step 2 before step 3 every time: a `recordPreference` typo or a second
`isDefaultModel: true` is cheaper to catch locally than in a deploy log.

---

## 9. Verification — the ROI and attribution queries

**The rollup fields are not the ones most plans name.** `Campaign.ActualCost` is "the
amount of money spent to run the campaign" — this campaign, not its descendants
(object_reference.txt:57100–57105). The hierarchy totals are separate, separately-named
calculated fields:

| Single campaign | Hierarchy equivalent | Line |
|---|---|---|
| `ActualCost` | `HierarchyActualCost` | object_reference.txt:57273 |
| `ExpectedRevenue` | `HierarchyExpectedRevenue` | object_reference.txt:57305 |
| `AmountWonOpportunities` | `HierarchyAmountWonOpportunities`, `TotalAmountAllWonOpportunities` | 57289, 57708 |
| `NumberOfLeads` | `HierarchyNumberOfLeads`, `TotalNumberofLeads` | 57337, 57768 |
| `NumberOfResponses` | `HierarchyNumberOfResponses`, `TotalNumberofResponses` | 57353, 57795 |

Program-level ROI therefore reads the `Hierarchy*` fields on the root campaign:

```sql
SELECT Id, Name, IsActive, ParentId,
       ActualCost, HierarchyActualCost,
       ExpectedRevenue, HierarchyExpectedRevenue,
       HierarchyAmountWonOpportunities,
       HierarchyNumberOfResponses,
       TotalNumberofResponses
FROM Campaign
WHERE Name = 'FY27-Q3-AMER-PROG-PipelineDrive'
```

Attribution per model, using the real field names — the revenue column on
`CampaignInfluence` is `RevenueShare`, not `Revenue`
(object_reference.txt:57987–57993):

```sql
SELECT Model.MasterLabel, Model.ModelType, Model.IsDefaultModel,
       Campaign.Name, Opportunity.Name, Opportunity.StageName,
       Influence, RevenueShare
FROM CampaignInfluence
WHERE Opportunity.StageName = 'Closed Won'
  AND Opportunity.CloseDate = THIS_FISCAL_QUARTER
ORDER BY Model.MasterLabel, RevenueShare DESC
```

Member-status health, per campaign — this is the query that finds the campaigns whose
statuses will silently coerce on load:

```sql
SELECT CampaignId, Campaign.Name,
       COUNT(Id) statuses,
       SUM(CASE WHEN IsDefault = true THEN 1 ELSE 0 END) defaults
FROM CampaignMemberStatus
WHERE Campaign.IsActive = true
GROUP BY CampaignId, Campaign.Name
HAVING SUM(CASE WHEN IsDefault = true THEN 1 ELSE 0 END) != 1
```

Note that `Campaign` and `CampaignMemberStatus` are "defined only for those organizations
that have the marketing feature enabled and valid marketing licenses… accessible only to
those users that are enabled as marketing users" (object_reference.txt:57860–57863,
58670–58674). A verification query run as a non-marketing integration user does not
return zero rows — the object does not appear in `describeGlobal()` at all.

---

## 10. Acceptance tests

Given/When/Then, each one runnable in the UAT sandbox by the persona named.

| # | Given | When | Then |
|---|---|---|---|
| A1 | `Campaign.settings` deployed with `enableCampaignInfluence2` = true | Marketing ops opens Setup → Campaign Influence | Campaign Influence 1.0 configuration is not offered; only the CCI model list is (api_meta.txt:111568–111571) |
| A2 | Three models deployed, `Acme First Touch` default | Query `CampaignInfluenceModel` | Exactly one row has `IsDefaultModel` = true (object_reference.txt:58066) |
| A3 | `Acme Last Touch` is locked | An admin tries to add a Campaign Influence row for it in the UI | The UI does not offer it; the row can only be created via the API (object_reference.txt:58068–58074) |
| A4 | A test opportunity is influenced under `Acme First Touch` | Marketing ops deactivates the model | The model's `CampaignInfluence` rows are **gone**, not orphaned (api_meta.txt:31892–31895). Reactivating does not restore them |
| A5 | The event campaign has statuses Invited/Registered/Attended/No Show | Data Loader inserts a `CampaignMember` with `Status` = `Registered!` (an invalid value) | The row inserts with `Status` = `Invited` (the default) and `HasResponded` = false — it is **not** rejected (object_reference.txt:58572–58577) |
| A6 | A campaign has no default status | The same invalid-status load runs | The row keeps the supplied string and `HasResponded` = false (object_reference.txt:58576–58577) |
| A7 | A `CampaignMember` payload carries both `ContactId` and `LeadId` | Data Loader inserts it | The insert **succeeds** and only `ContactId` is stored (object_reference.txt:58553–58555) |
| A8 | The `Attended` status is in use on the event campaign | An admin tries to delete it | Deletion is refused — a status that is the default or in use on a campaign cannot be deleted (object_reference.txt:58609) |
| A9 | The custom report type is deployed with `deployed` = true | A marketing user opens the report builder | "Campaign Influence by Model" is selectable, with `RevenueShare` checked by default |
| A10 | Someone writes a row against the Primary Campaign Source model via the API | The model recalculates | The row is deleted (object_reference.txt:57997–57999) |

---

## What consumes each artefact

| Artefact | Consumed by |
|---|---|
| `acme-q3-campaign-plan.yaml` | `scripts/check_campaign_planning_and_attribution.py`; `templates/campaign-planning-and-attribution-template.md` |
| `Campaign.settings-meta.xml`, `*.campaignInfluenceModel-meta.xml` | `agents/change-impact-planner/AGENT.md` (`/plan-metadata-change`) before any org-level switch |
| Campaign fields and record type | `agents/object-designer/AGENT.md` (`/design-object`), `agents/field-impact-analyzer/AGENT.md` (`/analyze-field-impact`) |
| `*.reportType-meta.xml` | `skills/admin/report-type-strategy` for join design; `skills/admin/reports-and-dashboards` for the report and dashboard built on top |
| Member-status sets | `skills/admin/lead-management-and-conversion` — conversion carries campaign membership forward from Lead to Contact |
| ROI / attribution SOQL | `skills/admin/opportunity-management` for `Opportunity.CampaignId` (the primary campaign source) and contact roles |

---

## Related reading, not duplicated here

| Skill | What it owns that this page deliberately omits |
|---|---|
| `admin/report-type-strategy` | Which object is the base, A-with-B-without joins, the field-display ceiling, outer-join direction rules |
| `admin/reports-and-dashboards` | Building the report and dashboard on the report type, folder sharing, running user |
| `admin/opportunity-management` | Sales processes, stages, `IsClosed`/`IsWon`, opportunity contact roles and splits |
| `admin/lead-management-and-conversion` | Conversion field mapping, `LeadStatus` converted flag, what conversion does to campaign membership |
| `admin/mcae-pardot-setup` | The Account Engagement connector, business units, and the campaign sync that writes members |
