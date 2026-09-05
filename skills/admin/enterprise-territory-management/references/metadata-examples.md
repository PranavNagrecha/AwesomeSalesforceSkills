# Metadata Examples — Enterprise Territory Management

Deployable source for a small but complete Sales Territories (ETM) model. Every XML block below is a
complete, well-formed file. Field names, enum values and folder layout come from the Metadata API
Developer Guide sections for `Territory2Model`, `Territory2`, `Territory2Rule`, `Territory2Type` and
`Territory2Settings`.

---

## Source layout

Sales Territories metadata is folder-shaped: territories and rules live *inside* the model folder, and
the type catalogue lives outside it.

```text
force-app/main/default/
├── settings/
│   └── Territory2.settings-meta.xml
├── territory2Models/
│   └── FY26_NA/
│       ├── FY26_NA.territory2Model-meta.xml
│       ├── territories/
│       │   ├── NA_Region.territory2-meta.xml
│       │   ├── US.territory2-meta.xml
│       │   └── Canada.territory2-meta.xml
│       └── rules/
│           └── NA_Billing_Country.territory2Rule-meta.xml
└── territory2Types/
    ├── Region.territory2Type-meta.xml
    └── Country.territory2Type-meta.xml
```

Guide statements this layout rests on: "Territory2 components have the suffix `territory2` and are
stored in the `territories` folder under the folder for the corresponding Territory2Model";
"Territory2Rule components have the suffix `territory2Rule` and are stored in the `rules` folder under
the folder for the corresponding Territory2Model"; "Territory2Type components … are stored in the
`territory2Types` folder"; "Territory2Settings values are stored in a single file named
`Territory2.settings` in the `settings` directory."

---

## 1. Org settings — enable Sales Territories and set the access floor

`settings/Territory2.settings-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Territory2Settings xmlns="http://soap.sforce.com/2006/04/metadata">
    <enableTerritoryManagement2>true</enableTerritoryManagement2>
    <defaultAccountAccessLevel>Read</defaultAccountAccessLevel>
    <defaultOpportunityAccessLevel>Read</defaultOpportunityAccessLevel>
    <defaultContactAccessLevel>Read</defaultContactAccessLevel>
    <defaultCaseAccessLevel>None</defaultCaseAccessLevel>
    <t2ForecastAccessLevel>View</t2ForecastAccessLevel>
    <tm2EnableUserAssignmentLog>true</tm2EnableUserAssignmentLog>
    <tm2BypassRealignAccInsert>false</tm2BypassRealignAccInsert>
    <showTM2EnabledBanner>false</showTM2EnabledBanner>
    <supportedObjects>
        <objectType>Lead</objectType>
        <defaultAccessLevel>Read</defaultAccessLevel>
        <state>Disabled</state>
    </supportedObjects>
</Territory2Settings>
```

How to read it:

- `enableTerritoryManagement2` is the feature switch. The guide is explicit that "Enabling and disabling
  Sales Territories is exclusive of all other operations, and the field value must be `true` before other
  territory-management operations can run" — so this settings file deploys **on its own, first**, not in
  the same deployment as the model. It is available in API version 47.0 and later.
- The four `default*AccessLevel` fields set the fallback used by any territory that leaves its own
  access field empty.
- `t2ForecastAccessLevel` (API 49.0+) is the access a parent territory's users get to opportunities
  assigned to its child territories, "regardless of who owns the opportunities". Valid values: `View`,
  `Edit`.
- `tm2EnableUserAssignmentLog` (API 57.0+) starts populating `UserTerritory2AssocLog`, the object that
  records when a user was assigned to and unassigned from a territory.
- `tm2BypassRealignAccInsert` (API 53.0+) — when `true`, "account assignment rules don't run during
  account insert jobs". Leave it `false` unless a bulk load is deliberately bypassing realignment.
- `supportedObjects` (API 57.0+) is the per-object territory-assignment switch. The guide states "The
  only supported object type is `Lead`" — this block is not how you configure Account, Opportunity,
  Contact or Case access.

---

## 2. Territory types

`territory2Types/Region.territory2Type-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Territory2Type xmlns="http://soap.sforce.com/2006/04/metadata">
    <name>Region</name>
    <description>Multi-country roll-up level. Used for forecast roll-up, not for OTA.</description>
    <priority>10</priority>
</Territory2Type>
```

`territory2Types/Country.territory2Type-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Territory2Type xmlns="http://soap.sforce.com/2006/04/metadata">
    <name>Country</name>
    <description>Leaf coverage level. Highest priority, so it wins opportunity territory assignment.</description>
    <priority>20</priority>
</Territory2Type>
```

How to read it:

- `priority` is required and is an `int`. The guide: "The account-assigned territory whose territory type
  priority is **highest** is then assigned to the opportunity. The `priority` field value on each
  territory type must be unique." The reference Apex filter in the Apex Reference Guide confirms the
  direction with `ota.Territory2.Territory2Type.Priority > tp.priority` — a numerically larger integer
  wins. `Country` (20) therefore beats `Region` (10), which is what you want for a leaf-wins design.
- The guide's own `Territory2Type` sample omits `priority`, but the field table marks it **Required** —
  include it.
- If two territories of the same type (and therefore the same priority) are assigned to the account,
  the guide states no territory is assigned to the opportunity. That is a silent null, not an error.

---

## 3. Territory model (Planning state)

`territory2Models/FY26_NA/FY26_NA.territory2Model-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Territory2Model xmlns="http://soap.sforce.com/2006/04/metadata"
                 xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                 xmlns:xsd="http://www.w3.org/2001/XMLSchema">
    <name>FY26 North America</name>
    <description>FY26 geographic coverage for US and Canada field sales.</description>
    <customFields>
        <name>Alignment_Owner__c</name>
        <value xsi:type="xsd:string">Sales Operations</value>
    </customFields>
    <customFields>
        <name>Planned_Activation__c</name>
        <value xsi:type="xsd:date">2026-02-07</value>
    </customFields>
</Territory2Model>
```

How to read it:

- **There is no `state` element.** State is a field on the `Territory2Model` *SOAP object*, not on the
  metadata component. The guide: "Whenever a model is created, its initial state is `Planning`." So a
  first deploy always lands in Planning, and you promote to Active in Setup afterwards. A model that
  already exists keeps whatever state it has.
- `customFields` uses `name`/`value` pairs with an `xsi:type` — which is why the two extra namespace
  declarations are on the root element. `Territory2` and `Territory2Model` "do not handle values for
  Text Area (Long), Text Area (Rich), and text-encrypted custom fields", and required custom fields are
  enforced at deploy time.
- To clear a custom field, deploy `<value xsi:nil="true"/>` instead of a typed value.

---

## 4. Territory hierarchy with access levels

`territory2Models/FY26_NA/territories/NA_Region.territory2-meta.xml` — root, no `parentTerritory`.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Territory2 xmlns="http://soap.sforce.com/2006/04/metadata">
    <name>North America</name>
    <description>Roll-up node for US and Canada. No rules of its own.</description>
    <territory2Type>Region</territory2Type>
    <accountAccessLevel>Read</accountAccessLevel>
    <opportunityAccessLevel>Read</opportunityAccessLevel>
    <contactAccessLevel>Read</contactAccessLevel>
    <caseAccessLevel>None</caseAccessLevel>
</Territory2>
```

`territory2Models/FY26_NA/territories/US.territory2-meta.xml` — child, owns the rule locally.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Territory2 xmlns="http://soap.sforce.com/2006/04/metadata">
    <name>United States</name>
    <description>US field sales coverage.</description>
    <territory2Type>Country</territory2Type>
    <parentTerritory>NA_Region</parentTerritory>
    <accountAccessLevel>Edit</accountAccessLevel>
    <opportunityAccessLevel>Edit</opportunityAccessLevel>
    <contactAccessLevel>Edit</contactAccessLevel>
    <caseAccessLevel>None</caseAccessLevel>
    <ruleAssociations>
        <ruleName>NA_Billing_Country</ruleName>
        <inherited>false</inherited>
    </ruleAssociations>
</Territory2>
```

`territory2Models/FY26_NA/territories/Canada.territory2-meta.xml` — child, inherits the same rule.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Territory2 xmlns="http://soap.sforce.com/2006/04/metadata">
    <name>Canada</name>
    <description>Canadian field sales coverage.</description>
    <territory2Type>Country</territory2Type>
    <parentTerritory>NA_Region</parentTerritory>
    <accountAccessLevel>Edit</accountAccessLevel>
    <opportunityAccessLevel>Read</opportunityAccessLevel>
    <contactAccessLevel>Read</contactAccessLevel>
    <caseAccessLevel>None</caseAccessLevel>
    <ruleAssociations>
        <ruleName>NA_Billing_Country</ruleName>
        <inherited>true</inherited>
    </ruleAssociations>
</Territory2>
```

How to read it:

- `parentTerritory` takes the **developer name**, not the label and not a fully qualified name — the
  guide says so explicitly: "When you specify the parent territory, use the developer name. Do not use
  the 'fully qualified' name." `NA_Region` is the file/developer name; `North America` is the label in
  `<name>`.
- `territory2Type` is required and refers to a `Territory2Type` developer name that must already exist
  in the org or ship in the same deployment.
- Access-level enums differ per object. `accountAccessLevel`: `Read`, `Edit`, `All`. `opportunityAccessLevel`,
  `caseAccessLevel`, `contactAccessLevel`: `None`, `Read`, `Edit`. These are the **Metadata API** spellings;
  the same settings appear in SOAP/UI as `Read Only` / `Read/Write` / `Owner` / `Private`. Do not copy a
  UI value into XML.
- If your Account sharing model is Public Read/Write, the guide restricts `accountAccessLevel` to `Edit`
  and `All` only. For opportunities/cases and for contacts under Public Read/Write (or Controlled By
  Parent for contacts), the guide says to specify **no value** at all.
- An omitted access field falls back to the matching `default*AccessLevel` in `Territory2Settings`.
- `ruleAssociations` is how a rule reaches a territory. The rule itself lives in the model's `rules`
  folder, not on the territory — `ruleName` needs no model qualifier because "Metadata API assumes that
  the rule belongs to the same model as the territory."
- `inherited` is documented inconsistently between the two guides. **UNVERIFIED (2026-09-04): I could
  not reconcile them from the extracted text.** Metadata API Developer Guide, `Territory2RuleAssociation`:
  "Indicates whether the rule is inherited from a parent territory (true) or local to the current
  territory (false)." Object Reference, `ObjectTerritory2AssignmentRule.IsInherited`: "An inherited rule
  also acts upon territories below it in the territory hierarchy. A local rule is created at the
  immediate territory and only impacts the immediate territory." The XML above follows the Metadata API
  wording — `false` on the territory that owns the rule, `true` on the descendant that receives it.
  Before hand-writing this element, build the rule in Setup in a sandbox, retrieve the territories, and
  match the retrieved shape.
- `objectAccessLevels` (API 57.0+) is available on `Territory2` for objects enabled through
  `Territory2Settings.supportedObjects`; today that is `Lead` only. It is omitted here because the
  settings file above leaves Lead `Disabled`.

---

## 5. Account assignment rule

`territory2Models/FY26_NA/rules/NA_Billing_Country.territory2Rule-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Territory2Rule xmlns="http://soap.sforce.com/2006/04/metadata">
    <name>NA Billing Country</name>
    <objectType>Account</objectType>
    <active>true</active>
    <ruleItems>
        <field>BillingCountry</field>
        <operation>equals</operation>
        <value>United States,USA,US</value>
    </ruleItems>
    <ruleItems>
        <field>BillingCountry</field>
        <operation>equals</operation>
        <value>Canada,CA</value>
    </ruleItems>
    <booleanFilter>1 OR 2</booleanFilter>
</Territory2Rule>
```

How to read it:

- `name`, `objectType` and `active` are the three required fields. The guide's own sample definition for
  this type shows `<label>` instead of `<name>` — that contradicts its own field table. Use `<name>`.
- `objectType`: the guide's Territory2Rule field table says "For API version 32.0, the only available
  object is `Account`", and the Object Reference entry for `ObjectTerritory2AssignmentRule.ObjectType`
  says "For API version 31, Account only." Neither extract documents a wider list, so treat anything
  other than `Account` as unsupported until you confirm it against a current org describe.
- `operation` is a fixed enumeration: `equals`, `notEqual`, `lessThan`, `greaterThan`, `lessOrEqual`,
  `greaterOrEqual`, `contains`, `notContain`, `startsWith`, `includes`, `excludes`, and `within`
  (DISTANCE criteria only). There is no `greater_than` despite what the guide's sample shows.
- Multiple values in one `value` element are comma-separated, as in the guide's own
  `94105,94404,94536` sample.
- `booleanFilter` numbering "must start at 1 and must be contiguous", and "the sort order of rule items
  is implicitly derived from the position of the rule items in the XML" — reordering the `ruleItems`
  silently renumbers your filter.
- A rule can have **up to 10 rule items**.
- `active` true means "active rules run automatically when object records are created and edited",
  except where `IsExcludedFromRealign` on the record is `true`.
- The rule file carries no territory pointer. A rule with no `ruleAssociations` entry pointing at it
  from any `Territory2` deploys cleanly and assigns nothing.

---

## 6. package.xml

Wildcards are supported for `Territory2Model`, `Territory2`, `Territory2Rule` and `Territory2Type` —
each of those four sections in the guide ends with "This metadata type supports the wildcard character
`*`". Settings types do **not** take a wildcard for an individual setting.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>FY26_NA</members>
        <name>Territory2Model</name>
    </types>
    <types>
        <members>FY26_NA.NA_Region</members>
        <members>FY26_NA.US</members>
        <members>FY26_NA.Canada</members>
        <name>Territory2</name>
    </types>
    <types>
        <members>FY26_NA.NA_Billing_Country</members>
        <name>Territory2Rule</name>
    </types>
    <types>
        <members>Region</members>
        <members>Country</members>
        <name>Territory2Type</name>
    </types>
    <version>62.0</version>
</Package>
```

How to read it:

- `Territory2` and `Territory2Rule` members are **model-qualified** (`Model.Component`). The guide's own
  package.xml samples show `FY13.USA` and `FY13.AccRule1`, and note that rules "can have identical
  developer names within different models" — the qualifier is what disambiguates them. A wildcard in
  place of the model name retrieves all of them across all models.
- `Territory2Type` members are **not** model-qualified; types are org-wide.
- The settings file ships in its own separate deployment (see below) because
  `enableTerritoryManagement2` "is exclusive of all other operations".

Separate manifest for the settings-only deployment:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Territory2</members>
        <name>Settings</name>
    </types>
    <version>62.0</version>
</Package>
```

---

## 7. Retrieve and deploy

```bash
# 0. One-time, on its own: enable the feature.
sf project deploy start \
  --manifest manifest/territory2-settings.xml \
  --target-org myDevHub --wait 30

# 1. Retrieve an existing model to seed source. Run as a user with Manage Territories.
sf project retrieve start \
  --metadata "Territory2Model:FY26_NA" \
  --metadata "Territory2:FY26_NA.*" \
  --metadata "Territory2Rule:FY26_NA.*" \
  --metadata "Territory2Type" \
  --target-org prod

# 2. Validate against the target before committing to it.
sf project deploy validate \
  --manifest manifest/territory2-model.xml \
  --target-org uat --wait 60

# 3. Deploy the model, types, territories and rules together.
sf project deploy start \
  --manifest manifest/territory2-model.xml \
  --target-org uat --wait 60
```

Constraints the guide states about these calls:

- **Permission.** "The Manage Territories permission is required for `deploy()` calls for all territory
  management entities." For `retrieve()`, a user without Manage Territories gets back only entities
  belonging to a model in Active state — the guide "recommends against retrieving without the Manage
  Territories permission because the call retrieves only partial data." A silent partial retrieve is the
  worst failure mode here: source looks complete and is not.
- **Model state gates deployment.** "You can only do a `deploy()` operation for models in `Planning` or
  `Active` state. The same requirement applies to territories and rules associated with those models."
  Deploying into an Active model is supported. Deploying into a model that is `Archived` in the target
  org fails, and the guide calls out exactly this scenario: a model in Planning in the sandbox and the
  same developer name Archived in production.
- **`retrieve()` skips four states** entirely: `Cloning`, `Cloning Failed`, `Deleting`, and
  `Deletion Failed`.
- **Field-level security is relaxed for deploy.** The UI and SOAP API require FLS on every field
  referenced in a rule item; `deploy()` instead requires Manage Territories plus either Modify Metadata
  Through Metadata API Functions or Modify All Data.
- **No change sets, no packaging, no CRUD calls.** Each of the four types' Usage sections repeats
  "Sales Territories components don't support packaging or change sets and aren't supported in CRUD
  calls." `Territory2` adds one carve-out: "For unlocked packaging, Territory2 requires packages without
  a namespace." Plan an ETM release as a source deploy, never as a change set.
- **Triggers on Territory2 don't fire during deploy** unless a component fails and is retried
  individually — for example a child territory deploying before its parent.
- **Rules can't be run via Metadata API.** The deployment installs the rule; it does not assign anything.

---

## 8. Assign users — not metadata

`UserTerritory2Association` is a SOAP object, not a metadata type, so it does not ship in the package.
Load it with Data Loader or Apex after the model exists.

```csv
UserId,Territory2Id,RoleInTerritory2,IsActive
005xx000001Sv1AAAS,0MIxx0000004CDcGAM,Sales Rep,true
005xx000001Sv1BAAS,0MIxx0000004CDcGAM,Administrator,true
005xx000001Sv1CAAS,0MIxx0000004CDdGAM,Owner,true
```

- `RoleInTerritory2` is a picklist with documented values `Owner`, `Administrator`, `Sales Rep`.
- Supported calls on `UserTerritory2Association` are `create()`, `delete()`, `describeSObjects()`,
  `query()` and `retrieve()` — `update()` is not in that list, so treat a role change as delete +
  re-insert rather than an update. The object also "doesn't support adding custom fields."
- Bulk API guidance lists "Updating territory hierarchies" among the operations "likely to cause lock
  contention"; if you hit lock timeouts, run the job in serial concurrency mode.

---

## 9. Run the assignment rules

The rules do not run themselves after a deploy. The guide states plainly: "Rules can't be run via
Metadata API." The run is user-initiated — `Territory2AlignmentLog.RunAsId` is documented as "ID of the
Salesforce user who started the assignment rule run job", and `Territory2Id` on that log "is null" when
the run was for the whole model rather than one territory.

**UNVERIFIED (2026-09-04): none of the Metadata API, Object Reference, REST or Bulk guides names the
entry point that starts the run.** They establish only that Metadata API cannot do it and that a user
initiates it. The Territory Model detail page in Setup ("Run Assignment Rules") is the commonly used
path; confirm it against current Salesforce Help before writing a runbook step or an automation that
depends on it.

After the run, the model records `LastRunRulesEndDate`; filter-based opportunity assignment records
`LastOppTerrAssignEndDate`.

---

## 10. Verification

```sql
-- Exactly one Active model, and when its rules last finished.
SELECT Id, DeveloperName, State, ActivatedDate, LastRunRulesEndDate, LastOppTerrAssignEndDate
FROM Territory2Model
WHERE State = 'Active'

-- Did the rule run finish? Territory2Id is null for a model-level run.
SELECT Id, Territory2ModelId, Territory2Id, Status, StartTime, EndTime, RunAsId
FROM Territory2AlignmentLog
ORDER BY StartTime DESC
LIMIT 20

-- What did the rules actually assign, and by rule or by hand?
-- AssociationCause is Territory2AssignmentRule or Territory2Manual.
SELECT ObjectId, SobjectType, Territory2Id, Territory2.Name, AssociationCause
FROM ObjectTerritory2Association
WHERE Territory2.Territory2Model.State = 'Active'
LIMIT 200

-- Who is in each territory, and in what role.
SELECT UserId, Territory2Id, Territory2.Name, RoleInTerritory2, IsActive
FROM UserTerritory2Association
WHERE Territory2.Territory2Model.State = 'Active'

-- Which territory would filter-based OTA pick for this account? Highest priority wins;
-- a tie at the top leaves Opportunity.Territory2Id null.
SELECT ObjectId, Territory2Id, Territory2.Territory2Type.Priority
FROM ObjectTerritory2Association
WHERE ObjectId = '001xx000003DGb1AAG'
  AND Territory2.Territory2ModelId = '0MIxx0000004CDbGAM'
ORDER BY Territory2.Territory2Type.Priority DESC

-- Prove the share rows exist. Territory = granted by an assignment rule;
-- Territory2AssociationManual = granted by a manual account-to-territory assignment
-- (it replaced the deprecated TerritoryManual value in API version 45.0).
SELECT UserOrGroupId, AccountAccessLevel, OpportunityAccessLevel, CaseAccessLevel, RowCause
FROM AccountShare
WHERE AccountId = '001xx000003DGb1AAG'
  AND RowCause IN ('Territory', 'Territory2AssociationManual')
```

Setup check that no query replaces: open the Territory Model detail page and confirm the state reads
Active rather than one of the transitional states `Activating` or `Activation Failed`. The full
`Territory2Model.State` picklist is `Planning`, `Activating`, `Activation Failed`, `Active`,
`Archiving`, `Archiving Failed`, `Archived`, `Deleting`, `Deletion Failed` — a checker that only tests
for `Active` and `Planning` will misread a stuck activation as a missing model.

Then run the package checker over the source folder:

```bash
python3 scripts/check_enterprise_territory_management.py \
  --manifest-dir force-app/main/default
```

---

## Sources

- Metadata API Developer Guide — `Territory2` (accountAccessLevel/caseAccessLevel/contactAccessLevel/
  opportunityAccessLevel/customFields/parentTerritory/ruleAssociations/territory2Type,
  Territory2RuleAssociation, Territory2AccessLevel, sample definition, package.xml sample, Usage notes
  on triggers/packaging/change sets), `Territory2Model` (customFields/description/name, initial state
  Planning, deploy state gates, retrieve state exclusions, cascade delete), `Territory2Rule`
  (active/booleanFilter/name/objectType/ruleItems, Territory2RuleItem field/operation/value with the
  FilterOperation enumeration, 10-rule-item cap, sort order, "Rules can't be run via Metadata API"),
  `Territory2Type` (name/description/priority and the uniqueness + highest-wins semantics),
  `Territory2Settings` (enableTerritoryManagement2 exclusivity, default access levels,
  opportunityFilterSettings, supportedObjects/Lead, t2ForecastAccessLevel, tm2BypassRealignAccInsert,
  tm2EnableUserAssignmentLog, sample definition).
  https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf
- Object Reference for the Salesforce Platform — `Territory2` (AccountAccessLevel/CaseAccessLevel/
  ContactAccessLevel/OpportunityAccessLevel picklist spellings, DeveloperName, ForecastUserId),
  `Territory2Model` (State picklist, ActivatedDate, LastRunRulesEndDate, LastOppTerrAssignEndDate),
  `Territory2AlignmentLog` (RunAsId, Status, StartTime, EndTime, null Territory2Id for model-level runs),
  `ObjectTerritory2Association` (AssociationCause, SobjectType Account/Lead, 12-hour post-delete query
  window), `UserTerritory2Association` (supported calls, RoleInTerritory2 values, no custom fields),
  `ObjectTerritory2AssignmentRule` / `ObjectTerritory2AssignmentRuleItem`, `AccountShare.RowCause`
  (Territory, Territory2AssociationManual, deprecated TerritoryManual).
  https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf
- Apex Reference Guide — `TerritoryMgmt.OpportunityTerritory2AssignmentFilter` and the
  `OppTerrAssignDefaultLogicFilter` reference implementation (confirms highest-integer-priority wins and
  that a tie yields a null Territory2Id).
  https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/apexrefguide.pdf
- Bulk API 2.0 and Bulk API Developer Guide — "Updating territory hierarchies" listed among operations
  that increase lock contention and may need serial concurrency mode.
  https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_asynch.pdf
