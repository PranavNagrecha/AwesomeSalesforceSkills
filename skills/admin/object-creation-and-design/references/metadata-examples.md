# Metadata Examples — Object Creation and Design

Deployable shapes for `CustomObject` and `CustomTab`, extended from the sample definitions in the Metadata API Developer Guide (v62 PDF, `CustomObject` and `CustomTab` types). The worked example is a parent request object with an Auto Number name, a `Private` sharing model and history tracking, plus one master-detail child on `ControlledByParent`.

## Where the files live

| Type | package.xml `<name>` | File in a DX project | API |
|---|---|---|---|
| CustomObject | `CustomObject` | `objects/Project_Request__c/Project_Request__c.object-meta.xml` | 10.0+ (external objects 32.0+) |
| CustomField | `CustomField` (`Object__c.Field__c`) | `objects/Project_Request__c/fields/Status__c.field-meta.xml` | — |
| CustomTab | `CustomTab` (wildcard `*` allowed) | `tabs/Project_Request__c.tab-meta.xml` | 10.0+ |

The guide documents the Metadata API shape: one `.object` file per object in the `objects` folder, with `fields`, `recordTypes`, `listViews` and the rest nested inside it (api_meta.txt L41914–41917, L42437–42460). DX source format keeps the *object-level* elements in `<Name>__c.object-meta.xml` and splits each nested component into its own file under a sibling sub-folder (`fields/`, `recordTypes/`, `listViews/`, `compactLayouts/`, `validationRules/`, `webLinks/`, `fieldSets/`, `businessProcesses/`). UNVERIFIED (2026-09-04): the DX sub-folder decomposition is a Salesforce CLI source-format convention; the Metadata API Developer Guide documents only the single-file `.object` shape, and help.salesforce.com cannot be fetched to confirm the folder list.

`nameField` stays in the object file in both formats — it is not a separate `CustomField` component.

## Parent object — Auto Number name, Private OWD, history tracking

`objects/Project_Request__c/Project_Request__c.object-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomObject xmlns="http://soap.sforce.com/2006/04/metadata">
    <compactLayoutAssignment>Project_Request_Compact</compactLayoutAssignment>
    <deploymentStatus>Deployed</deploymentStatus>
    <description>Internal intake for project requests. Owner is the submitting employee; PMO reads all records through a sharing rule. History is tracked for audit of status and target date changes.</description>
    <enableActivities>false</enableActivities>
    <enableBulkApi>true</enableBulkApi>
    <enableFeeds>false</enableFeeds>
    <enableHistory>true</enableHistory>
    <enableReports>true</enableReports>
    <enableSearch>true</enableSearch>
    <enableSharing>true</enableSharing>
    <enableStreamingApi>true</enableStreamingApi>
    <externalSharingModel>Private</externalSharingModel>
    <label>Project Request</label>
    <nameField>
        <displayFormat>REQ-{00000}</displayFormat>
        <label>Request Number</label>
        <startingNumber>1</startingNumber>
        <type>AutoNumber</type>
    </nameField>
    <pluralLabel>Project Requests</pluralLabel>
    <sharingModel>Private</sharingModel>
    <visibility>Public</visibility>
</CustomObject>
```

How to read it:

- `label` / `pluralLabel` are the user-facing names and are editable forever. `pluralLabel` is required on custom objects "to ensure that object names are localizable" (api_meta.txt L42197–42199). The API name is the file name, not an element in the file.
- `nameField` is required for custom objects and holds "the field that this object's name is stored in ... usually a string or autonumber" (api_meta.txt L42187–42195). `displayFormat` and `startingNumber` only apply when `type` is `AutoNumber`.
- `startingNumber` is write-only: "You can't retrieve the starting number of an auto-number field through Metadata API" (api_meta.txt L43623–43635). A retrieve of a deployed object will not contain it, so a retrieve/redeploy round trip silently drops the value and the default for custom fields (1) applies.
- `deploymentStatus` is `InDevelopment` or `Deployed` (api_meta.txt L45713–45718). Ship `Deployed`; an object left `InDevelopment` is not visible to non-admin users.
- `sharingModel` is the internal OWD. Valid values in the `SharingModel` enum are `Private`, `Read`, `ReadWrite`, `ReadWriteTransfer`, `FullAccess`, `ControlledByParent`, `ControlledByCampaign`, `ControlledByLeadOrContact`; the guide notes that "accounts, opportunities, and custom objects support `Private`, `Read` and `ReadWrite` values" (api_meta.txt L45801–45814) — `Read` is Public Read Only, `ReadWrite` is Public Read/Write. `ControlledByParent` is the value a detail object carries (see the child below). The field is settable through the API only in version 30.0 and later (api_meta.txt L42250–42256).
- `externalSharingModel` is a second, separate OWD "which determines the access level for external users" (api_meta.txt L42132–42134). It matters whenever `SharingSettings.enableExternalSharingModel` is on, which "has a default value of `true` if Salesforce Experiences are enabled" (api_meta.txt L127055–127059). Omitting it in an Experiences org leaves external access at whatever the org already had.
- `enableBulkApi`, `enableSharing` and `enableStreamingApi` are a set: each one's description says the other two "must also be enabled" (api_meta.txt L42013–42019, L42079–42092). Deploy all three or none.
- `enableSearch`: "By default, search is disabled for new custom objects" from API version 35.0 (api_meta.txt L42062–42066). Set it explicitly if users must find records through global search or SOSL.
- `enableHistory` turns on the History framework for the object; it does not select fields. Field selection is `trackHistory` on each field, and "to set `trackHistory` to `true`, the `enableHistory` field on the associated standard or custom object must also be `true`" (api_meta.txt L43675–43682).
- `visibility` is `Public`, `Protected` or `PackageProtected`, default `Public`, available in API version 34.0 and later (api_meta.txt L42278–42297). It only bites when the object is packaged.
- `compactLayoutAssignment` names the compact layout shown in the highlights panel (api_meta.txt L41951–41953); the referenced `CompactLayout` must be in the same deployment.

## The tracked field

`objects/Project_Request__c/fields/Status__c.field-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Status__c</fullName>
    <description>Lifecycle state of the request. Tracked for audit.</description>
    <externalId>false</externalId>
    <label>Status</label>
    <required>true</required>
    <trackFeedHistory>false</trackFeedHistory>
    <trackHistory>true</trackHistory>
    <type>Picklist</type>
    <valueSet>
        <restricted>true</restricted>
        <valueSetDefinition>
            <sorted>false</sorted>
            <value>
                <fullName>Submitted</fullName>
                <default>true</default>
                <label>Submitted</label>
            </value>
            <value>
                <fullName>In Review</fullName>
                <default>false</default>
                <label>In Review</label>
            </value>
            <value>
                <fullName>Approved</fullName>
                <default>false</default>
                <label>Approved</label>
            </value>
            <value>
                <fullName>Declined</fullName>
                <default>false</default>
                <label>Declined</label>
            </value>
        </valueSetDefinition>
    </valueSet>
</CustomField>
```

Field shape and the `trackHistory` / `trackFeedHistory` pair follow the guide's own two-field sample (api_meta.txt L43951–43971). Up to twenty fields total, standard or custom, can be tracked on one object (object_reference.txt L110674). Field design itself is `admin/custom-field-creation`.

## Master-detail child on Controlled by Parent

`objects/Project_Request_Task__c/Project_Request_Task__c.object-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomObject xmlns="http://soap.sforce.com/2006/04/metadata">
    <deploymentStatus>Deployed</deploymentStatus>
    <description>Work item under a Project Request. Access follows the parent request; the object has no Owner field of its own.</description>
    <enableActivities>true</enableActivities>
    <enableHistory>false</enableHistory>
    <enableReports>true</enableReports>
    <enableSearch>false</enableSearch>
    <label>Project Request Task</label>
    <nameField>
        <label>Task Name</label>
        <type>Text</type>
    </nameField>
    <pluralLabel>Project Request Tasks</pluralLabel>
    <sharingModel>ControlledByParent</sharingModel>
</CustomObject>
```

`objects/Project_Request_Task__c/fields/Project_Request__c.field-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Project_Request__c</fullName>
    <label>Project Request</label>
    <referenceTo>Project_Request__c</referenceTo>
    <relationshipLabel>Tasks</relationshipLabel>
    <relationshipName>Tasks</relationshipName>
    <relationshipOrder>0</relationshipOrder>
    <reparentableMasterDetail>false</reparentableMasterDetail>
    <required>true</required>
    <trackHistory>false</trackHistory>
    <type>MasterDetail</type>
    <writeRequiresMasterRead>false</writeRequiresMasterRead>
</CustomField>
```

How to read it:

- `sharingModel` on a detail object is `ControlledByParent`. The detail "inherits the sharing and security settings of its master record", its Owner field "isn't available and is automatically set to the owner of its associated master record", and consequently detail-side custom objects "can't have sharing rules, manual sharing, or queues, because these elements require the Owner field" (object_reference.txt L3259–3261). That last clause is the one that surprises people: a detail object can never be an assignment-rule or queue target.
- `relationshipOrder` is `0` for a normal detail object; `0` and `1` are the only valid values, and a non-zero value is meaningful only on a junction object with two master-detail fields, where "one parent object as primary (0), the other as secondary (1)" (api_meta.txt L43582–43591).
- `reparentableMasterDetail` defaults to `false`, meaning a child cannot be moved to a different parent (api_meta.txt L43593–43597; object_reference.txt L3264–3266). Set it at creation if the business ever re-files records.
- `writeRequiresMasterRead` is the sharing lever: `false` (the default, more restrictive) requires Read/Write on the parent to create, edit or delete children; `true` lets Read on the parent be enough (api_meta.txt L43725–43738).
- Not every standard object can be the master. `BusinessHours`, `Idea`, `Lead`, `OrderItem`, `PriceBook2`, `Product2`, `QuoteLineItem` and `User` cannot be the primary object of a master-detail relationship with a custom object, and a standard object can never be on the detail side (object_reference.txt L3267–3278, L3041–3060). Relationship selection itself is `admin/lookup-and-relationship-design`.

## The tab

`tabs/Project_Request__c.tab-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomTab xmlns="http://soap.sforce.com/2006/04/metadata">
    <customObject>true</customObject>
    <description>Project intake requests</description>
    <motif>Custom18: Form</motif>
</CustomTab>
```

How to read it:

- For a custom object tab the file name *is* the object name and `customObject` must be `true` (api_meta.txt L47286–47297, L47322–47332). `label` is for web tabs only — a custom object tab takes its name from the object.
- `motif` is required and is the style string, for example `Custom18: Form` or `Custom70: Handsaw`; the guide lists `Custom1:Heart` through `Custom100:TVWidescreen` (api_meta.txt L47362–47396).
- `frameHeight` is required for s-control and page tabs only (api_meta.txt L47319–47320); leave it out of an object tab.
- Only one of `auraComponent`, `customObject`, `flexiPage`, `lwcComponent`, `page`, `scontrol`, `url` may be set (api_meta.txt L47276–47285).
- Tab **visibility** per profile is not in this file. It lives in `Profile` / `PermissionSet` metadata, and the guide warns that "retrieving a component of this metadata type in a project makes the component appear in any Profile and PermissionSet components that are retrieved in the same package" (api_meta.txt L47260–47261). Deploying only the tab leaves every non-admin profile on the org default.

## Description length

`CustomObject.description` and `CustomField.description` are not the same field with the same limit, and it is worth being precise about which is which.

`CustomObject.description` is grounded directly in the Metadata API Developer Guide's `CustomObject` field table: "A description of the object. Maximum of 1000 characters" (`api_meta.txt` L42007). That is a much higher ceiling than the 255-character limit documented elsewhere in the same guide for `CustomPermission`, `PermissionSet`, `Profile` and `RecordType` descriptions — do not carry that 255 figure over to a custom object's own description.

`CustomField.description` carries no stated limit at all. The `CustomField` field table gives only "Description of the field." with no `Limit:` clause (`api_meta.txt` L43360; the `CustomField` section header is confirmed immediately above at L43379). **UNVERIFIED (2026-09-11):** whether the 255-character ceiling used for `CustomPermission`/`PermissionSet`/`Profile` also applies to `CustomField` — `Account.Region__c` in `examples/builds/case-onboarding/artefacts/M1-S01` sits at 249 characters today, which would be six characters from that candidate limit if it applied, but nothing in the guide confirms it does. Until a dry-run rejection or an updated guide confirms a number, treat 255 as a candidate only, not a fact.

**Where rationale goes instead.** Neither field is the place for the reason each irreversible feature (Gotcha 2) was enabled, or the tracked-field audit reasons (Gotcha 11) — put those in the object's own `description` only as a short pointer, and the full rationale in the build's `deploy-order.md` or the configuration workbook.

`scripts/check_object_creation_and_design.py` enforces this: `OCD-DESC-01` (ISSUE) at 1000+ characters on `CustomObject` files only, grounded at the object's own documented limit; `OCD-DESC-02` (WARN, advisory — does not affect the exit code) at 200+ characters on either `CustomObject` or `CustomField` files, as a headroom hint rather than a claimed limit.

## package.xml

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Project_Request__c</members>
        <members>Project_Request_Task__c</members>
        <name>CustomObject</name>
    </types>
    <types>
        <members>Project_Request__c.Status__c</members>
        <members>Project_Request_Task__c.Project_Request__c</members>
        <name>CustomField</name>
    </types>
    <types>
        <members>Project_Request__c</members>
        <name>CustomTab</name>
    </types>
    <version>62.0</version>
</Package>
```

`CustomObject` "supports the wildcard character `*` in the package.xml manifest file for Field Sets and Record Types but not for other components" (api_meta.txt L42668–42670) — list objects by name. `CustomTab` supports `*` outright (api_meta.txt L47465–47467).

## Retrieve and deploy

```bash
sf project retrieve start --metadata CustomObject:Project_Request__c --target-org my-sandbox
sf project retrieve start --manifest manifest/package.xml --target-org my-sandbox

python3 skills/admin/object-creation-and-design/scripts/check_object_creation_and_design.py \
  --manifest-dir force-app/main/default

sf project deploy start --manifest manifest/package.xml --target-org my-sandbox --dry-run
sf project deploy start --manifest manifest/package.xml --target-org my-sandbox
```

Deploy order inside one package: the parent object before the child's master-detail field, and any `CompactLayout` named by `compactLayoutAssignment` in the same deployment. A single `sf project deploy start` resolves these together; splitting them across deployments does not.

## Verify after deploy

Setup check, in order:

1. **Setup → Object Manager → Project Request → Details** — Deployment Status reads *Deployed*, Record Name is *Auto Number* with format `REQ-{00000}`, Allow Field History Tracking is on.
2. **Setup → Object Manager → Project Request → Fields & Relationships → Set History Tracking** — `Status` is checked. `enableHistory` alone tracks nothing.
3. **Setup → Security → Sharing Settings → Custom Object Defaults** — Project Request is *Private*; Project Request Task shows *Controlled by Parent* and is not editable.
4. **Setup → User Interface → Tabs → Custom Object Tabs** — the tab exists; open its profile visibility and confirm the intended profiles are not left on Hidden.

Then create one record and confirm the platform side of it:

```sql
SELECT Id, Name, Status__c, OwnerId FROM Project_Request__c ORDER BY CreatedDate DESC LIMIT 1
SELECT Id, Field, OldValue, NewValue FROM Project_Request__History ORDER BY CreatedDate DESC LIMIT 5
```

`Name` comes back as `REQ-00001` if the Auto Number deployed with its display format. The second query runs against the object's generated history object — the `__History` suffix is reserved for "Field History Tracking for custom objects" (object_reference.txt L4412), and these per-object history objects replaced the withdrawn org-wide `EntityHistory` object (object_reference.txt L110591–110593). An empty result after editing `Status__c` means the field was never marked for tracking.

A detail object has no `OwnerId`, so `SELECT OwnerId FROM Project_Request_Task__c` fails — that failure is the confirmation that `ControlledByParent` took effect.
