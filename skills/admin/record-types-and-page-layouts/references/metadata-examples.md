# Metadata Examples — Record Types and Page Layouts

Deployable shapes taken from the Metadata API Developer Guide (v62 PDF: `RecordType`, `BusinessProcess`, `Layout`, `Profile`, `PermissionSet`). Four metadata types cooperate to make one record type usable, and three of them live in different files:

| Piece | Metadata type | Where it lives |
|---|---|---|
| The record type itself | `RecordType` | inside the `CustomObject` definition |
| The Status/Stage value set it uses | `BusinessProcess` | inside the same `CustomObject` definition |
| The page it renders | `Layout` | `layouts/` directory, suffix `.layout` |
| Who can pick it, and which page they get | `Profile` / `PermissionSet` | `profiles/` and `permissionsets/` |

Deploying only the first two produces a record type nobody can select. See gotchas #6 and #7.

## Where the files live

| Type | package.xml `<name>` | Member format | Wildcard `*`? | API |
|---|---|---|---|---|
| RecordType | `RecordType` | `Case.Customer_Support` (object-qualified) | **No** — the guide states this type doesn't support `*` | 12.0+ |
| BusinessProcess | `BusinessProcess` | `Case.Customer Support Process` (object-qualified) | Only when a `RecordType` is also specified | 17.0+ |
| Layout | `Layout` | `Case-Case Customer Support` (object, hyphen, layout name) | Yes | 13.0+ |
| CustomObject | `CustomObject` | `Case` | Yes | — |

MDAPI (source of the shapes below) nests `recordTypes` and `businessProcesses` inside one `<CustomObject>` file. A DX source-format project decomposes the same content into `objects/Case/recordTypes/Customer_Support.recordType-meta.xml` and `objects/Case/businessProcesses/Customer_Support_Process.businessProcess-meta.xml`, with layouts at `layouts/Case-Case Customer Support.layout-meta.xml`. <!-- UNVERIFIED (2026-09-04): the decomposed DX directory layout is a Salesforce DX Developer Guide convention; the Metadata API PDF documents only the nested CustomObject form and the `layouts/` + `.layout` suffix. The nested XML below is the grounded shape and deploys in either project format. -->

## Case record type with a business process and two picklist value sets

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomObject xmlns="http://soap.sforce.com/2006/04/metadata">
    <businessProcesses>
        <fullName>Customer Support Process</fullName>
        <description>Status lifecycle for externally reported cases.</description>
        <isActive>true</isActive>
        <values>
            <fullName>New</fullName>
            <default>true</default>
        </values>
        <values>
            <fullName>Awaiting Customer</fullName>
            <default>false</default>
        </values>
        <values>
            <fullName>Escalated</fullName>
            <default>false</default>
        </values>
        <values>
            <fullName>Closed</fullName>
            <default>false</default>
        </values>
    </businessProcesses>
    <recordTypes>
        <fullName>Customer_Support</fullName>
        <active>true</active>
        <businessProcess>Customer Support Process</businessProcess>
        <compactLayoutAssignment>Case_Customer_Compact</compactLayoutAssignment>
        <description>Externally reported cases raised by customers.</description>
        <label>Customer Support</label>
        <picklistValues>
            <picklist>Priority</picklist>
            <values>
                <fullName>High</fullName>
                <default>false</default>
            </values>
            <values>
                <fullName>Medium</fullName>
                <default>true</default>
            </values>
            <values>
                <fullName>Low</fullName>
                <default>false</default>
            </values>
        </picklistValues>
        <picklistValues>
            <picklist>Origin</picklist>
            <values>
                <fullName>Email</fullName>
                <default>true</default>
            </values>
            <values>
                <fullName>Web</fullName>
                <default>false</default>
            </values>
        </picklistValues>
    </recordTypes>
</CustomObject>
```

How to read it:

- `<businessProcess>` carries the **bare** process name (`Customer Support Process`), not the object-qualified one. The guide is explicit: the enclosing object already supplies the entity context, so `Case.Customer Support Process` here is wrong — that form is only for `package.xml` members and retrieve results.
- The Metadata API guide requires `businessProcess` on record types for **lead, opportunity, solution, and case**, and forbids it everywhere else. The Object Reference's `RecordType.BusinessProcessId` entry states it more narrowly ("required for Opportunity and Lead record types in API version 17.0 and later"). Supply it on all four; a custom object that carries it fails to deploy.
- A `BusinessProcess` drives the object's *status* picklist (`Case.Status` — "the status of the case, such as New, Closed, or Escalated"). It is not a general picklist filter. Every other picklist you want to restrict goes in a `picklistValues` block.
- Each `picklistValues` block is one `RecordTypePicklistValue`: `<picklist>` names the field, and each `<values><fullName>` is one value the record type exposes. Values omitted from the block are unavailable on that record type — that is the mechanism behind the picklist-wipe gotcha (gotchas #1).
- Exactly one `<default>true</default>` per block. `Priority` defaults to `Medium`, `Origin` to `Email` on this record type only.
- `active` is required. `label` is required and is what users see; `fullName` is the stable API name — reports keyed on the label break when the label changes (gotchas #4).
- `description` is capped at 255 characters, and the guide warns in bold that **every user with object access can read the record type's description, name, and label** — never put sensitive information there (gotchas #10).

## Custom-object record type — no business process allowed

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomObject xmlns="http://soap.sforce.com/2006/04/metadata">
    <recordTypes>
        <fullName>Hardware_Warranty_Claim</fullName>
        <active>true</active>
        <description>Claims raised against a physical device warranty.</description>
        <label>Hardware Warranty Claim</label>
        <picklistValues>
            <picklist>Claim_Category__c</picklist>
            <values>
                <fullName>Manufacturing Defect</fullName>
                <default>true</default>
            </values>
            <values>
                <fullName>Shipping Damage</fullName>
                <default>false</default>
            </values>
        </picklistValues>
    </recordTypes>
</CustomObject>
```

`fullName` must begin with a letter, contain only underscores and alphanumerics, hold no spaces, not end with an underscore, and not contain two consecutive underscores. Adding `<businessProcess>` to this block is a deploy error, not a warning.

## Page layout with two sections and one required field

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Layout xmlns="http://soap.sforce.com/2006/04/metadata">
    <layoutSections>
        <customLabel>true</customLabel>
        <detailHeading>true</detailHeading>
        <editHeading>true</editHeading>
        <label>Case Information</label>
        <layoutColumns>
            <layoutItems>
                <behavior>Required</behavior>
                <field>Subject</field>
            </layoutItems>
            <layoutItems>
                <behavior>Edit</behavior>
                <field>Priority</field>
            </layoutItems>
            <layoutItems>
                <behavior>Edit</behavior>
                <field>Origin</field>
            </layoutItems>
        </layoutColumns>
        <layoutColumns>
            <layoutItems>
                <behavior>Edit</behavior>
                <field>Status</field>
            </layoutItems>
            <layoutItems>
                <behavior>Edit</behavior>
                <field>OwnerId</field>
            </layoutItems>
            <layoutItems>
                <emptySpace>true</emptySpace>
            </layoutItems>
        </layoutColumns>
        <style>TwoColumnsTopToBottom</style>
    </layoutSections>
    <layoutSections>
        <customLabel>false</customLabel>
        <detailHeading>true</detailHeading>
        <editHeading>false</editHeading>
        <label>System Information</label>
        <layoutColumns>
            <layoutItems>
                <behavior>Readonly</behavior>
                <field>CreatedById</field>
            </layoutItems>
        </layoutColumns>
        <layoutColumns>
            <layoutItems>
                <behavior>Readonly</behavior>
                <field>LastModifiedById</field>
            </layoutItems>
        </layoutColumns>
        <style>TwoColumnsTopToBottom</style>
    </layoutSections>
    <quickActionList>
        <quickActionListItems>
            <quickActionName>LogACall</quickActionName>
        </quickActionListItems>
        <quickActionListItems>
            <quickActionName>FeedItem.TextPost</quickActionName>
        </quickActionListItems>
    </quickActionList>
    <relatedLists>
        <fields>TASK.SUBJECT</fields>
        <fields>TASK.WHO_NAME</fields>
        <fields>TASK.DUE_DATE</fields>
        <relatedList>RelatedActivityList</relatedList>
    </relatedLists>
    <showEmailCheckbox>true</showEmailCheckbox>
    <showRunAssignmentRulesCheckbox>true</showRunAssignmentRulesCheckbox>
    <showKnowledgeComponent>true</showKnowledgeComponent>
</Layout>
```

How to read it:

- `layoutSections` order is the on-screen order. `style` is one of `TwoColumnsTopToBottom`, `TwoColumnsLeftToRight`, `OneColumn`, `CustomLinks`; `layoutColumns` must match — 1, 2, or 3 columns ordered left to right.
- `customLabel` says whether `label` is your own text or one of the built-in labels. Built-in labels ("System Information") translate automatically; custom ones must be translated separately.
- `detailHeading` and `editHeading` are independent. `System Information` above shows its heading on the detail page and hides it on the edit page.
- `behavior` is `Edit`, `Required`, or `Readonly`. **`Required` here is a layout-level requirement, not a field-level one** — the same field is optional on a layout that omits it (gotchas #11). Setting `behavior` explicitly on a Knowledge article layout raises an exception.
- A `layoutItems` entry sets exactly one of `field`, `customLink`, `component`, `page`, `scontrol`, `analyticsCloudComponent`, or `reportChartComponent`. `emptySpace` reserves a blank grid cell so the two columns stay aligned.
- `showEmailCheckbox` is allowed only on Case, CaseClose, and Task layouts; `showRunAssignmentRulesCheckbox` only on Case, Lead, and Account; `showKnowledgeComponent` only on Case. Deploying one on the wrong object fails.
- `relatedLists/fields` for standard fields use retrieval **aliases**, not API names — Fax, Mobile, and Home Phone come back as `Phone2`, `Phone3`, `Phone4`. Round-tripping a retrieved layout preserves them; hand-writing API names there does not.

## Making the record type visible and assigning the page

A permission set can grant *visibility* only. It has `recordTypeVisibilities` (API 29.0+) with just `recordType` and `visible` — no `default`, and no `layoutAssignments` field at all. The default record type and the page layout assignment exist only on `Profile`.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<PermissionSet xmlns="http://soap.sforce.com/2006/04/metadata">
    <hasActivationRequired>false</hasActivationRequired>
    <label>Support Agent — Customer Cases</label>
    <recordTypeVisibilities>
        <recordType>Case.Customer_Support</recordType>
        <visible>true</visible>
    </recordTypeVisibilities>
</PermissionSet>
```

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Profile xmlns="http://soap.sforce.com/2006/04/metadata">
    <custom>true</custom>
    <layoutAssignments>
        <layout>Case-Case Customer Support</layout>
        <recordType>Case.Customer_Support</recordType>
    </layoutAssignments>
    <layoutAssignments>
        <layout>Case-Case Internal IT</layout>
        <recordType>Case.Internal_IT</recordType>
    </layoutAssignments>
    <recordTypeVisibilities>
        <default>true</default>
        <recordType>Case.Customer_Support</recordType>
        <visible>true</visible>
    </recordTypeVisibilities>
    <recordTypeVisibilities>
        <default>false</default>
        <recordType>Case.Internal_IT</recordType>
        <visible>true</visible>
    </recordTypeVisibilities>
</Profile>
```

How to read it:

- `recordType` is object-qualified (`Case.Customer_Support`) in both files, matching the guide's `Account.MyRecordType` example.
- `layoutAssignments/layout` is the layout's **file name form** — object, hyphen, layout name. `recordType` on a layout assignment is optional; omit it for the assignment that applies when no record type matches.
- Exactly one `recordTypeVisibilities` entry per profile per object may carry `<default>true</default>`. `personAccountDefault` is the separate Person Account equivalent, and is inert when Person Accounts is off.
- Neither file is retrieved or deployed for a record type whose `active` is `false` — see gotchas #8, which is what makes deactivation look like an unexplained profile diff.

## package.xml

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Case</members>
        <name>CustomObject</name>
    </types>
    <types>
        <members>Case.Customer Support Process</members>
        <name>BusinessProcess</name>
    </types>
    <types>
        <members>Case.Customer_Support</members>
        <members>Case.Internal_IT</members>
        <name>RecordType</name>
    </types>
    <types>
        <members>Case-Case Customer Support</members>
        <members>Case-Case Internal IT</members>
        <name>Layout</name>
    </types>
    <types>
        <members>Support_Agent</members>
        <name>Profile</name>
    </types>
    <types>
        <members>Support_Agent_Customer_Cases</members>
        <name>PermissionSet</name>
    </types>
    <version>62.0</version>
</Package>
```

`RecordType` must be listed member by member — the guide states this type doesn't support `*`, so a wildcard-only manifest retrieves the object and its layouts but silently no record types. `BusinessProcess` accepts `*` only because a `RecordType` entry is present in the same manifest.

## Retrieve, check, deploy

```bash
sf project retrieve start --manifest manifest/record-types.xml --target-org my-sandbox

python3 skills/admin/record-types-and-page-layouts/scripts/check_record_type_layouts.py \
  --manifest-dir force-app/main/default
# add --strict to fail on MEDIUM/LOW/INFO as well as CRITICAL/HIGH

sf project deploy start --manifest manifest/record-types.xml --target-org my-sandbox --dry-run
sf project deploy start --manifest manifest/record-types.xml --target-org my-sandbox
```

Point the checker at the whole tree, not at one step's directory: with no record types and no layouts to resolve against, the profile cross-references are reported as `N reference(s) unresolvable at this scope` (INFO) rather than checked. Retrieve the object, the layouts, **and** every profile and permission set in the same package. The guide notes that retrieving a `RecordType` or a `Layout` makes that component appear in any `Profile` and `PermissionSet` retrieved in the same package — retrieve them separately and the profiles you commit will be missing assignments they actually have in the org (gotchas #7).

## Verify after deploy

```sql
SELECT SobjectType, DeveloperName, Name, IsActive, BusinessProcessId, IsPersonType
FROM RecordType
WHERE SobjectType = 'Case'
ORDER BY DeveloperName
```

Every row you deployed should be present with `IsActive = true` — only active record types can be applied to records. Then confirm the assignment actually landed:

```sql
SELECT Parent.Profile.Name, Parent.Label, SobjectType, RecordTypeId, Visible
FROM RecordTypeVisibility
WHERE SobjectType = 'Case'
```

<!-- UNVERIFIED (2026-09-04): the `RecordTypeVisibility` Tooling-API object used in the second query is not documented in the extracted Object Reference or Metadata API PDFs. The `RecordType` query above is fully grounded; if the second query is unavailable in your org, verify visibility instead in Setup → Object Manager → Case → Record Types, and the layout assignment under Page Layouts → Page Layout Assignment. -->

Setup check that needs no API: Setup → Object Manager → Case → Page Layouts → **Page Layout Assignment**. The grid is the profile × record type matrix the `Profile` file above encodes; a blank cell means that profile falls through to the assignment with no `recordType`.
