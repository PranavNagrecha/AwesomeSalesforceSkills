# Metadata Examples — Path and Guidance

Deployable XML for `PathAssistant`, the record type and business process it depends on, the org
preference, and the Lightning page that renders it. Shapes are taken from the Metadata API Developer
Guide's own sample definitions and field tables and extended to a realistic Opportunity path.

Source: Metadata API Developer Guide (Summer '26 / v66), `PathAssistant` L94490–94615,
`PathAssistantSettings` L124200–124240, `BusinessProcess` L42955–43060, `RecordType` L44968–45131,
`StandardValueSet` L130740–130828, `FlexiPage` sample L67728–67999, `Settings` L108356–108385.
PDF: https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf

---

## The five artifacts and what each one owns

| Artifact | Metadata type | Owns |
|---|---|---|
| `Enterprise_New_Business_Process` | `BusinessProcess` (inside the object file) | *Which* `StageName` values exist for the record type |
| `Enterprise_New_Business` | `RecordType` (inside the object file) | Binding the business process + the per-record-type picklist value list |
| `Enterprise_New_Business_Path` | `PathAssistant` | Key fields (`fieldNames`) and guidance (`info`) per step |
| `PathAssistant.settings` | `PathAssistantSettings` | The org-wide Path preference and the auto-collapse override |
| `Opportunity_Record_Page` | `FlexiPage` | Where the Path component actually renders |

Deploy in that order. `PathAssistant` is the only one of the five that names steps; every step name
must already exist as a picklist value on the record type, or the step silently does not render.

---

## 1. Business process + record type — `objects/Opportunity/Opportunity.object-meta.xml`

`BusinessProcess` is not a standalone file: "Business processes are defined as part of the custom
object or standard object definition" (api_meta.txt L42969). `RecordType.businessProcess` uses
the **bare** process name, not the object-qualified form (api_meta.txt L45006–45012), and is required
for lead, opportunity, solution, and case record types.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomObject xmlns="http://soap.sforce.com/2006/04/metadata">
    <businessProcesses>
        <fullName>Enterprise_New_Business_Process</fullName>
        <description>Stage set for enterprise new-business deals.</description>
        <isActive>true</isActive>
        <values>
            <fullName>Qualification</fullName>
            <default>true</default>
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
        <fullName>Enterprise_New_Business</fullName>
        <active>true</active>
        <businessProcess>Enterprise_New_Business_Process</businessProcess>
        <label>Enterprise New Business</label>
        <picklistValues>
            <picklist>StageName</picklist>
            <values>
                <fullName>Qualification</fullName>
                <default>true</default>
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
        </picklistValues>
    </recordTypes>
</CustomObject>
```

How to read it:

- `businessProcesses/fullName` is the bare name here, but the package.xml member is object-qualified
  (`Opportunity.Enterprise_New_Business_Process`) — the guide states both forms explicitly
  (api_meta.txt L42991–43000).
- `recordTypes/businessProcess` points at the bare process name. Prefixing it with `Opportunity.`
  is the most common deploy failure on this file.
- `picklistValues/picklist` is the **field API name** (`StageName`), not the label `Stage`.
- Every `<values><fullName>` string here is what a `PathAssistant` step's `picklistValueName` must
  match, character for character, including the `/` in `Proposal/Price Quote`.
- The record type file does *not* control the values' existence — `StandardValueSet` /
  `OpportunityStage` does. This file controls which of them the record type exposes.

### If the stage value itself is new — `standardValueSets/OpportunityStage.standardValueSet-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<StandardValueSet xmlns="http://soap.sforce.com/2006/04/metadata">
    <sorted>false</sorted>
    <standardValue>
        <fullName>Qualification</fullName>
    </standardValue>
    <standardValue>
        <fullName>Proposal/Price Quote</fullName>
    </standardValue>
    <standardValue>
        <fullName>Negotiation/Review</fullName>
    </standardValue>
    <standardValue>
        <fullName>Closed Won</fullName>
    </standardValue>
    <standardValue>
        <fullName>Closed Lost</fullName>
    </standardValue>
</StandardValueSet>
```

`OpportunityStage` is the standard value set name for `Opportunity.StageName`; `LeadStatus` maps to
`Lead.Status`, `CaseStatus` to `Case.Status`, `QuoteStatus` to `Quote.Status` (api_meta.txt Appendix C,
L142674, L142581, L141982, L142923). When you deploy a StandardValueSet, the array must contain at
least one picklist value or the deploy errors (api_meta.txt L130771–130772).

**The trap the guide states outright:** "new picklist values loaded into your organization through the
Metadata API don't display in the picklist UI by default. For users to see the new values, go to the
Record Types list for the object containing the picklist field, click Edit, and add the new value to
the Selected Fields list" (api_meta.txt L130774–130779). A Path step for a value that is in the value
set but not on the record type renders nothing.

---

## 2. The path — `pathAssistants/Enterprise_New_Business_Path.pathAssistant-meta.xml`

"PathAssistant components have the suffix `.pathAssistant` and are stored in the `pathAssistants`
folder" (api_meta.txt L94502). Fields are exactly `active`, `entityName`, `fieldName`, `masterLabel`,
`pathAssistantSteps`, `recordTypeName`; each step is exactly `fieldNames`, `info`, `picklistValueName`
(api_meta.txt L94510–94529, L94545–94549).

```xml
<?xml version="1.0" encoding="UTF-8"?>
<PathAssistant xmlns="http://soap.sforce.com/2006/04/metadata">
    <active>true</active>
    <entityName>Opportunity</entityName>
    <fieldName>StageName</fieldName>
    <masterLabel>Enterprise New Business Path</masterLabel>
    <pathAssistantSteps>
        <fieldNames>Economic_Buyer__c</fieldNames>
        <fieldNames>Metrics__c</fieldNames>
        <fieldNames>Budget_Confirmed__c</fieldNames>
        <fieldNames>CloseDate</fieldNames>
        <fieldNames>NextStep</fieldNames>
        <info>Exit criteria: economic buyer identified and contacted, measurable business value confirmed, next step scheduled.</info>
        <picklistValueName>Qualification</picklistValueName>
    </pathAssistantSteps>
    <pathAssistantSteps>
        <fieldNames>Decision_Process__c</fieldNames>
        <fieldNames>Paper_Process__c</fieldNames>
        <fieldNames>Amount</fieldNames>
        <fieldNames>CloseDate</fieldNames>
        <info>Before sending the proposal: confirm the decision process and timeline, document legal and procurement steps, and have the champion validate the proposal against their success criteria.</info>
        <picklistValueName>Proposal/Price Quote</picklistValueName>
    </pathAssistantSteps>
    <pathAssistantSteps>
        <fieldNames>Amount</fieldNames>
        <fieldNames>Discount_Approved_By__c</fieldNames>
        <fieldNames>Contract_Sent_Date__c</fieldNames>
        <info>Discount above the standard band needs deal-desk approval before the redline goes out. Record the approver here, not in Chatter.</info>
        <picklistValueName>Negotiation/Review</picklistValueName>
    </pathAssistantSteps>
    <pathAssistantSteps>
        <fieldNames>Amount</fieldNames>
        <fieldNames>CloseDate</fieldNames>
        <fieldNames>Contract_Signed__c</fieldNames>
        <info>Submit the order form within 24 hours, schedule the customer-success kickoff, and complete the win report by end of week.</info>
        <picklistValueName>Closed Won</picklistValueName>
    </pathAssistantSteps>
    <recordTypeName>Enterprise_New_Business</recordTypeName>
</PathAssistant>
```

How to read it:

- `entityName` and `fieldName` are "hard coded for Opportunity, Lead, and Quote" / "hard coded for
  StageName and Status"; for a custom object you supply both explicitly and `fieldName` must be the
  picklist field that determines the steps (api_meta.txt L94513–94521).
- `entityName`, `fieldName`, and `recordTypeName` are all marked **not updateable**
  (api_meta.txt L94515, L94521, L94529). Re-pointing an existing path at a different driver field or
  record type is a delete-and-recreate, not an edit.
- `recordTypeName` is the bare record type developer name, matching the guide's own sample
  (`Test_Record_Type`, api_meta.txt L94573).
- `fieldNames` repeats — one element per key field. It is **not** a comma-separated string.
- **Closed Lost has no step here on purpose.** "Note that a missing step in the .xml file means it has
  not been configured, not that it doesn't exist" (api_meta.txt L94525–94526). The chevron still
  appears; it just carries no key fields and no guidance.
- There is **no celebration/confetti element** anywhere in the `PathAssistant` or `PathAssistantStep`
  field tables. Celebration configuration does not travel with this file — see
  `references/gotchas.md` Gotcha 8.
- `info` is shown as plain text, matching the guide's sample (`<info>Some Text</info>`,
  api_meta.txt L94564). UNVERIFIED (2026-09-05): the guide calls the field "rich text guidance
  information" (api_meta.txt L94497) but never shows escaped HTML in `info`, so the exact markup
  subset accepted there is not established by these sources. If you deploy HTML, XML-escape it
  (`&lt;p&gt;…&lt;/p&gt;`) and verify the render in a sandbox before promoting.

---

## 3. The org preference — `settings/PathAssistant.settings-meta.xml`

"PathAssistantSettings components have the suffix `.settings` and are stored in the `settings` folder"
(api_meta.txt L124206). The manifest member is the type name without the `Settings` suffix — so
`PathAssistant` (api_meta.txt L108368–108369).

```xml
<?xml version="1.0" encoding="UTF-8"?>
<PathAssistantSettings xmlns="http://soap.sforce.com/2006/04/metadata">
    <pathAssistantEnabled>true</pathAssistantEnabled>
    <canOverrideAutoPathCollapseWithUserPref>true</canOverrideAutoPathCollapseWithUserPref>
</PathAssistantSettings>
```

How to read it:

- `pathAssistantEnabled` default is **`true` for Enterprise Edition and `false` for other editions**
  (api_meta.txt L124222–124224). A Developer Edition scratch org therefore starts with Path off,
  which is why a path that worked in a full sandbox renders nothing in a fresh scratch org.
- `canOverrideAutoPathCollapseWithUserPref` (API 47.0+) keeps a user's path expanded across their
  records until they collapse it. Default is `false` **for all editions**, and when false "the user's
  path is collapsed when the page loads" (api_meta.txt L124216–124221). Ship this as `true` unless
  you have a reason not to — otherwise every user sees a collapsed bar with the guidance you wrote
  hidden behind a click.
- `pathAssistantForOpportunityEnabled` exists but is API 34.0 **and earlier**
  (api_meta.txt L124226–124228). Do not put it in a modern package.
- Deploying `PathAssistant` does not require this: "The preference does not need to be on to retrieve
  or deploy PathAssistant" (api_meta.txt L94498). That is precisely how paths land in production
  fully configured and completely invisible.

---

## 4. Rendering the component — `flexipages/Opportunity_Record_Page.flexipage-meta.xml`

The component name and its canonical region come from the guide's own FlexiPage sample
(api_meta.txt L67766–67779, template at L67993–67996):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<FlexiPage xmlns="http://soap.sforce.com/2006/04/metadata">
    <flexiPageRegions>
        <itemInstances>
            <componentInstance>
                <componentInstanceProperties>
                    <name>hideUpdateButton</name>
                    <value>false</value>
                </componentInstanceProperties>
                <componentInstanceProperties>
                    <name>variant</name>
                    <value>linear</value>
                </componentInstanceProperties>
                <componentName>runtime_sales_pathassistant:pathAssistant</componentName>
            </componentInstance>
        </itemInstances>
        <name>subheader</name>
        <type>Region</type>
    </flexiPageRegions>
    <flexiPageRegions>
        <itemInstances>
            <componentInstance>
                <componentName>force:detailPanel</componentName>
            </componentInstance>
        </itemInstances>
        <name>main</name>
        <type>Region</type>
    </flexiPageRegions>
    <masterLabel>Opportunity Record Page</masterLabel>
    <sobjectType>Opportunity</sobjectType>
    <template>
        <name>flexipage:recordHomeWithSubheaderTemplateDesktop</name>
    </template>
    <type>RecordPage</type>
</FlexiPage>
```

How to read it:

- `runtime_sales_pathassistant:pathAssistant` is the component name — not `flexipage:path`,
  not `lightning:path`.
- It sits in the region named `subheader`, and the template that provides that region is
  `flexipage:recordHomeWithSubheaderTemplateDesktop`. A record page built on a template without a
  `subheader` region has nowhere canonical to put the component.
- `hideUpdateButton=false` keeps the stage-advance button that drives the celebration animation.
  Set it to `true` and users can read the path but must change the stage elsewhere.
- `variant=linear` is the value in the guide's sample.

---

## 5. package.xml

Modelled on the guide's own PathAssistant manifest (api_meta.txt L94576–94611), extended with the
FlexiPage and the custom fields this path's `fieldNames` reference.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Opportunity.Enterprise_New_Business_Process</members>
        <name>BusinessProcess</name>
    </types>
    <types>
        <members>Opportunity.Budget_Confirmed__c</members>
        <members>Opportunity.Contract_Sent_Date__c</members>
        <members>Opportunity.Contract_Signed__c</members>
        <members>Opportunity.Decision_Process__c</members>
        <members>Opportunity.Discount_Approved_By__c</members>
        <members>Opportunity.Economic_Buyer__c</members>
        <members>Opportunity.Metrics__c</members>
        <members>Opportunity.Paper_Process__c</members>
        <name>CustomField</name>
    </types>
    <types>
        <members>Opportunity.Enterprise_New_Business</members>
        <name>RecordType</name>
    </types>
    <types>
        <members>OpportunityStage</members>
        <name>StandardValueSet</name>
    </types>
    <types>
        <members>Enterprise_New_Business_Path</members>
        <name>PathAssistant</name>
    </types>
    <types>
        <members>Opportunity_Record_Page</members>
        <name>FlexiPage</name>
    </types>
    <types>
        <members>PathAssistant</members>
        <name>Settings</name>
    </types>
    <version>66.0</version>
</Package>
```

Manifest notes:

- `PathAssistant` supports the `*` wildcard (api_meta.txt L94614–94615) — use
  `<members>*</members>` to inventory every path in an org before an audit.
- `RecordType` does **not** support the wildcard (api_meta.txt L45129–45131), so record types must be
  named individually.
- `StandardValueSet` does not support the wildcard either (api_meta.txt L130826–130828).
- Settings wildcards apply "only when retrieving all settings, not for an individual setting"
  (api_meta.txt L124194–124197).

---

## 6. Retrieve and deploy

```bash
# Inventory every path in the org before changing anything
sf project retrieve start --metadata "PathAssistant:*" --target-org prod

# Pull the whole dependency set for one path
sf project retrieve start \
  --metadata "PathAssistant:Enterprise_New_Business_Path" \
  --metadata "RecordType:Opportunity.Enterprise_New_Business" \
  --metadata "BusinessProcess:Opportunity.Enterprise_New_Business_Process" \
  --metadata "StandardValueSet:OpportunityStage" \
  --metadata "FlexiPage:Opportunity_Record_Page" \
  --metadata "Settings:PathAssistant" \
  --target-org uat

# Static check before deploying
python3 scripts/check_path_and_guidance.py --manifest-dir force-app/main/default

# Validate, then deploy
sf project deploy validate --manifest manifest/package.xml --target-org prod
sf project deploy start   --manifest manifest/package.xml --target-org prod
```

**Deploy order inside one package is handled by the platform, but split deploys must go:**

1. `StandardValueSet` (new stage values must exist)
2. `CustomField` (every `fieldNames` entry must exist as a field on `entityName`)
3. `BusinessProcess` + `RecordType` (the object file — the record type must expose the values)
4. `PathAssistant`
5. `Settings:PathAssistant` and `FlexiPage` (make it visible last, so nobody sees a half-built path)

---

## 7. Verification after deploy

**Setup check** — Setup → Path Settings. The org toggle reflects `pathAssistantEnabled`; the path
appears in the list with its object, record type, and driver field, and shows as Active.

**SOQL 1 — every step name must be a real, active picklist value.** Compare the `ApiName` column
against every `picklistValueName` in the deployed file:

```sql
SELECT ApiName, MasterLabel, IsActive, IsClosed, IsWon, SortOrder
FROM OpportunityStage
ORDER BY SortOrder
```

`ApiName` "uniquely identifies a picklist value so it can be retrieved without using an id or master
label"; `IsActive` false means the value "is not available in the picklist and [is] retained for
historical purposes only" (object_reference.txt L195449, L195511–195514). A step pointed at an
inactive value is dead configuration.

**SOQL 2 — the record type must be bound to the business process you deployed:**

```sql
SELECT Id, DeveloperName, SobjectType, BusinessProcessId, IsActive
FROM RecordType
WHERE SobjectType = 'Opportunity'
```

`BusinessProcessId` is "Required for Opportunity and Lead record types in API version 17.0 and later"
(object_reference.txt L244515–244521). A null here on an Opportunity record type means the stage set
is undefined and the path has nothing coherent to render.

**SOQL 3 — "the path is collapsed for one user" is a user preference, not a config bug:**

```sql
SELECT Id, Username, UserPreferencesPathAssistantCollapsed
FROM User
WHERE Username = 'rep@example.com'
```

"When true, Sales Path appears collapsed or hidden to the user" — API 35.0 and later, and the field is
createable and updateable (object_reference.txt L296509–296515). Use
`UserPreferencesProcessAssistantCollapsed` only against API 33.0–34.0; in 35.0+ it is superseded
(object_reference.txt L296517–296524).

---

## Related reading

- `references/gotchas.md` — the failure modes these files produce
- `references/examples.md` — the design conversation that precedes the XML
- `scripts/check_path_and_guidance.py` — enforces the cross-file rules above before you deploy
