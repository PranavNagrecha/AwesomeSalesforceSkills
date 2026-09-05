# Metadata Examples — Dynamic Forms and Dynamic Actions

Deployable metadata for a Dynamic Forms + Dynamic Actions record page, plus the
**assignment** metadata that makes the page actually load. The page and the assignment
are two different metadata types in two different folders; shipping only the first
deploys an inert page.

| Artifact | DX path | Metadata type |
|---|---|---|
| The page itself | `force-app/main/default/flexipages/<Name>.flexipage-meta.xml` | `FlexiPage` |
| Org-default assignment | `force-app/main/default/objects/<Obj>/<Obj>.object-meta.xml` | `CustomObject` → `actionOverrides` |
| App / record-type / profile assignment | `force-app/main/default/applications/<App>.app-meta.xml` | `CustomApplication` → `actionOverrides`, `profileActionOverrides` |
| Mobile Dynamic Forms org switch (Beta) | `force-app/main/default/settings/DynamicForms.settings-meta.xml` | `DynamicFormsSettings` |

---

## 1. The record page: `Case_Record_Page_Support.flexipage-meta.xml`

A Case record page with a highlights panel carrying one Dynamic Action, a four-field
section (one `Required`, one `Readonly`), and a second section that appears only once
the case is escalated.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- Excerpt: force-app/main/default/flexipages/Case_Record_Page_Support.flexipage-meta.xml -->
<FlexiPage xmlns="http://soap.sforce.com/2006/04/metadata">

    <!-- Facet A: Dynamic Actions. Each action is a ComponentInstance, so each one can
         carry its own visibilityRule. -->
    <flexiPageRegions>
        <itemInstances>
            <componentInstance>
                <componentInstanceProperties>
                    <name>actionName</name>
                    <value>Case.Escalate_Case</value>
                </componentInstanceProperties>
                <componentName>force:quickActionButton</componentName>
                <identifier>escalateCaseAction</identifier>
                <visibilityRule>
                    <booleanFilter>1 AND 2</booleanFilter>
                    <criteria>
                        <leftValue>{!Record.Status}</leftValue>
                        <operator>NE</operator>
                        <rightValue>Closed</rightValue>
                    </criteria>
                    <criteria>
                        <leftValue>{!$Permission.CustomPermission.Can_Escalate_Case}</leftValue>
                        <operator>EQUAL</operator>
                        <rightValue>true</rightValue>
                    </criteria>
                </visibilityRule>
            </componentInstance>
        </itemInstances>
        <name>actionsFacet</name>
        <type>Facet</type>
    </flexiPageRegions>

    <!-- Facet B and C: the two columns of the "Case Details" section. -->
    <flexiPageRegions>
        <itemInstances>
            <fieldInstance>
                <fieldInstanceProperties>
                    <name>uiBehavior</name>
                    <value>Required</value>
                </fieldInstanceProperties>
                <fieldItem>Record.Subject</fieldItem>
                <identifier>RecordSubjectField</identifier>
            </fieldInstance>
        </itemInstances>
        <itemInstances>
            <fieldInstance>
                <fieldInstanceProperties>
                    <name>uiBehavior</name>
                    <value>None</value>
                </fieldInstanceProperties>
                <fieldItem>Record.Priority</fieldItem>
                <identifier>RecordPriorityField</identifier>
            </fieldInstance>
        </itemInstances>
        <name>detailsColumnOne</name>
        <type>Facet</type>
    </flexiPageRegions>
    <flexiPageRegions>
        <itemInstances>
            <fieldInstance>
                <fieldInstanceProperties>
                    <name>uiBehavior</name>
                    <value>None</value>
                </fieldInstanceProperties>
                <fieldItem>Record.Status</fieldItem>
                <identifier>RecordStatusField</identifier>
            </fieldInstance>
        </itemInstances>
        <itemInstances>
            <fieldInstance>
                <fieldInstanceProperties>
                    <name>uiBehavior</name>
                    <value>Readonly</value>
                </fieldInstanceProperties>
                <fieldItem>Record.Origin</fieldItem>
                <identifier>RecordOriginField</identifier>
            </fieldInstance>
        </itemInstances>
        <name>detailsColumnTwo</name>
        <type>Facet</type>
    </flexiPageRegions>

    <!-- Facet D: the column wrappers the section points at. -->
    <flexiPageRegions>
        <itemInstances>
            <componentInstance>
                <componentInstanceProperties>
                    <name>body</name>
                    <value>detailsColumnOne</value>
                </componentInstanceProperties>
                <componentName>flexipage:column</componentName>
                <identifier>detailsColumnOneWrapper</identifier>
            </componentInstance>
        </itemInstances>
        <itemInstances>
            <componentInstance>
                <componentInstanceProperties>
                    <name>body</name>
                    <value>detailsColumnTwo</value>
                </componentInstanceProperties>
                <componentName>flexipage:column</componentName>
                <identifier>detailsColumnTwoWrapper</identifier>
            </componentInstance>
        </itemInstances>
        <name>detailsColumns</name>
        <type>Facet</type>
    </flexiPageRegions>

    <!-- Facet E: the escalation column, one field. -->
    <flexiPageRegions>
        <itemInstances>
            <fieldInstance>
                <fieldInstanceProperties>
                    <name>uiBehavior</name>
                    <value>Required</value>
                </fieldInstanceProperties>
                <fieldItem>Record.Escalation_Reason__c</fieldItem>
                <identifier>RecordEscalationReasonField</identifier>
            </fieldInstance>
        </itemInstances>
        <name>escalationColumnOne</name>
        <type>Facet</type>
    </flexiPageRegions>
    <flexiPageRegions>
        <itemInstances>
            <componentInstance>
                <componentInstanceProperties>
                    <name>body</name>
                    <value>escalationColumnOne</value>
                </componentInstanceProperties>
                <componentName>flexipage:column</componentName>
                <identifier>escalationColumnOneWrapper</identifier>
            </componentInstance>
        </itemInstances>
        <name>escalationColumns</name>
        <type>Facet</type>
    </flexiPageRegions>

    <!-- Header region: the highlights panel hosts the Dynamic Actions facet. -->
    <flexiPageRegions>
        <itemInstances>
            <componentInstance>
                <componentInstanceProperties>
                    <name>actions</name>
                    <value>actionsFacet</value>
                </componentInstanceProperties>
                <componentInstanceProperties>
                    <name>enableActionsConfiguration</name>
                    <value>true</value>
                </componentInstanceProperties>
                <componentInstanceProperties>
                    <name>numVisibleActions</name>
                    <value>3</value>
                </componentInstanceProperties>
                <componentName>force:highlightsPanel</componentName>
                <identifier>force_highlightsPanel</identifier>
            </componentInstance>
        </itemInstances>
        <name>header</name>
        <type>Region</type>
    </flexiPageRegions>

    <!-- Main region: the two field sections. The second carries the visibility rule. -->
    <flexiPageRegions>
        <itemInstances>
            <componentInstance>
                <componentInstanceProperties>
                    <name>columns</name>
                    <value>detailsColumns</value>
                </componentInstanceProperties>
                <componentInstanceProperties>
                    <name>label</name>
                    <value>Case Details</value>
                </componentInstanceProperties>
                <componentName>flexipage:fieldSection</componentName>
                <identifier>caseDetailsSection</identifier>
            </componentInstance>
        </itemInstances>
        <itemInstances>
            <componentInstance>
                <componentInstanceProperties>
                    <name>columns</name>
                    <value>escalationColumns</value>
                </componentInstanceProperties>
                <componentInstanceProperties>
                    <name>label</name>
                    <value>Escalation</value>
                </componentInstanceProperties>
                <componentName>flexipage:fieldSection</componentName>
                <identifier>escalationSection</identifier>
                <visibilityRule>
                    <criteria>
                        <leftValue>{!Record.Status}</leftValue>
                        <operator>EQUAL</operator>
                        <rightValue>Escalated</rightValue>
                    </criteria>
                </visibilityRule>
            </componentInstance>
        </itemInstances>
        <name>main</name>
        <type>Region</type>
    </flexiPageRegions>

    <masterLabel>Case Record Page - Support</masterLabel>
    <sobjectType>Case</sobjectType>
    <template>
        <name>flexipage:recordHomeTemplateDesktop</name>
    </template>
    <type>RecordPage</type>
</FlexiPage>
```

**UNVERIFIED (2026-09-04):** the Metadata API Developer Guide documents the FlexiPage *structure* (flexiPageRegions / itemInstances / componentInstance / fieldInstance / visibilityRule / criteria) and its FlexiPage sample uses force:highlightsPanel and flexipage:tab, but it does not enumerate the component names flexipage:fieldSection, flexipage:column, or force:quickActionButton, nor the property names actions, enableActionsConfiguration, columns, label, or actionName. The fieldSection / column / highlightsPanel names and the columns and body properties come from the Salesforce-published dreamhouse-lwc sample page cited in admin/lightning-record-page-configuration. The Dynamic-Action button component name force:quickActionButton and the highlights-panel actions / enableActionsConfiguration properties are NOT confirmed by either source. Configure one Dynamic Action in App Builder, retrieve the page, and copy the real names before hand-authoring more.

### How to read it

- **`type` = `RecordPage` + `sobjectType` = `Case`** bind the page to one object. `sobjectType` cannot be changed once set (Metadata API Developer Guide, FlexiPage → Fields).
- **A `Facet` region is a container that something else points at by name.** Nothing renders a facet directly; it renders because a `Region` component names it in a property value. That is why the facets are declared before the regions that use them, and why every `<name>` here is referenced exactly once.
- **`fieldInstance` is the Dynamic Forms unit.** It exists only on Dynamic Forms-enabled pages (Metadata API Developer Guide, FieldInstance: *"available only on Lightning Pages that have enabled Dynamic Forms"*). `fieldItem` is the API name **prefixed with its context** — `Record.Subject`, not `Subject`.
- **`uiBehavior` is the only field-behaviour lever.** `FieldInstanceProperty.name` accepts exactly two values, `uiBehavior` (API 49.0+) and `conditionalFormatRuleset` (API 62.0+); `uiBehavior`'s documented values are `None`, `Readonly`, and `Required`. There is no `isRequired` element and no `Edit` value — a field that is neither read-only nor required is `None`.
- **`visibilityRule` attaches to a `componentInstance` or a `fieldInstance`, never to a region.** Omitting it means "always show" (*"If this field is null, the component displays by default"*).
- **`operator` is a closed set**: `CONTAINS`, `EQUAL`, `NE`, `GT`, `GE`, `LE`, `LT`. Not `!=`, not `>=`, not `LIKE`, not `IN`.
- **`booleanFilter` indexes the `criteria` in document order, 1-based** — `1 AND 2`, `(1 OR 2) AND 3`. Omit it and the criteria are ANDed.
- **`leftValue` takes five expression contexts**: `{!Record.<field>}` (record pages only), `{!$User.<field>}`, `{!$Permission.CustomPermission.<name>}`, `{!$Permission.StandardPermission.<name>}`, and `{!$Client.FormFactor}` (`Small` / `Medium` / `Large`). An expression may span **no more than five fields** — `{!Record.Account.Owner.Manager.Manager.Manager.LastName}` has six spans and is rejected.
- **`identifier` is required from API 53.0 and capped at 120 characters.** It must be unique on the page; it is what event bindings and any later diff key off.

---

## 2. Making it the org default: `Case.object-meta.xml`

The FlexiPage file contains no assignment. The org default for the **View** action lives on the object.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- Excerpt: force-app/main/default/objects/Case/Case.object-meta.xml -->
<CustomObject xmlns="http://soap.sforce.com/2006/04/metadata">
    <actionOverrides>
        <actionName>View</actionName>
        <comment>Support record page, org default (desktop).</comment>
        <content>Case_Record_Page_Support</content>
        <formFactor>Large</formFactor>
        <type>flexipage</type>
    </actionOverrides>
</CustomObject>
```

- `type` = `flexipage` is *"only valid for the View action in Lightning Experience"*.
- `formFactor` `Large` = Lightning Experience desktop, `Small` = the Salesforce mobile app on phone or tablet, `Medium` is reserved, and **no value at all means Salesforce Classic**. Covering desktop and mobile takes two `actionOverrides` blocks, not one.

---

## 3. Narrowing it by app, record type, and profile: `Support_Console.app-meta.xml`

`profileActionOverrides` is the only place the profile and record-type dimensions exist.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- Excerpt: force-app/main/default/applications/Support_Console.app-meta.xml -->
<CustomApplication xmlns="http://soap.sforce.com/2006/04/metadata">
    <label>Support Console</label>
    <!-- App default: everyone in this app, any record type, any profile. -->
    <actionOverrides>
        <actionName>View</actionName>
        <comment>Action override created by Lightning App Builder during activation.</comment>
        <content>Case_Record_Page_Support</content>
        <formFactor>Large</formFactor>
        <pageOrSobjectType>Case</pageOrSobjectType>
        <skipRecordTypeSelect>false</skipRecordTypeSelect>
        <type>Flexipage</type>
    </actionOverrides>
    <!-- App + record type + profile: the narrowest assignment, and it wins. -->
    <profileActionOverrides>
        <actionName>View</actionName>
        <content>Case_Record_Page_Escalations</content>
        <formFactor>Large</formFactor>
        <pageOrSobjectType>Case</pageOrSobjectType>
        <profile>Support_Tier_2</profile>
        <recordType>Case.Escalation</recordType>
        <type>Flexipage</type>
    </profileActionOverrides>
</CustomApplication>
```

**Precedence, as documented:** *"When a user logs in with a profile, a matching ProfileActionOverride assignment takes precedence over existing overrides for the Home tab or record page specified in ActionOverride."* So, narrowest wins:

| Assignment | Lives in | Qualifiers |
|---|---|---|
| Org default | `CustomObject` → `actionOverrides` | object + form factor |
| App default | `CustomApplication` → `actionOverrides` | + app |
| App + record type + profile | `CustomApplication` → `profileActionOverrides` | + record type + profile |

On `AppProfileActionOverride`, `recordType` *"is required when actionName is set to View"* and `pageOrSobjectType` accepts only `record-home` and `standard-home` when the override targets a Home page. There is **no permission-set dimension** — see `admin/lightning-record-page-configuration` gotcha 7 for what that costs a profile-to-permission-set migration.

---

## 4. Dynamic Forms on mobile (Beta org switch)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- Excerpt: force-app/main/default/settings/DynamicForms.settings-meta.xml -->
<DynamicFormsSettings xmlns="http://soap.sforce.com/2006/04/metadata">
    <enableFormsOnMobile>true</enableFormsOnMobile>
</DynamicFormsSettings>
```

`DynamicFormsSettings` is available in API version 58.0 and later and `enableFormsOnMobile` is flagged Beta in the guide. There is exactly one settings file per org, so this is all-or-nothing — no per-page and no per-profile pilot.

Note there is **no** org-level switch for Dynamic Forms itself any more: `RecordPageSettings.enableDynamicForms` was *"Removed in API version 50.0 and later."*

---

## 5. `package.xml`

`FlexiPage` **does** support the `*` wildcard (Metadata API Developer Guide, FlexiPage → Wildcard Support in the Manifest File). `CustomObject`'s `ActionOverride` section states the opposite for that type, so name objects and apps explicitly.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- Excerpt: manifest/package.xml -->
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>*</members>
        <name>FlexiPage</name>
    </types>
    <types>
        <members>Case</members>
        <name>CustomObject</name>
    </types>
    <types>
        <members>Support_Console</members>
        <name>CustomApplication</name>
    </types>
    <types>
        <members>DynamicForms</members>
        <name>Settings</name>
    </types>
    <version>62.0</version>
</Package>
```

Settings components are always addressed under the `Settings` type name, with the settings file's base name as the member.

---

## 6. Retrieve and deploy

```bash
# Pull the page and BOTH assignment carriers. Retrieving the page alone hides
# every activation decision from your diff.
sf project retrieve start \
  --metadata "FlexiPage:Case_Record_Page_Support" \
  --metadata "CustomObject:Case" \
  --metadata "CustomApplication:Support_Console" \
  --target-org support-uat

# Lint before you ship.
python3 skills/admin/dynamic-forms-and-actions/scripts/check_dynamic_forms_and_actions.py \
  --manifest-dir force-app/main/default

# Validate-only. A malformed visibilityRule fails here, not at activation time.
sf project deploy start \
  --manifest manifest/package.xml \
  --dry-run \
  --target-org support-uat

sf project deploy start --manifest manifest/package.xml --target-org support-uat
```

Run against the three excerpts above, the checker reports one WARN: the `profileActionOverrides` entry in §3 assigns `Case_Record_Page_Escalations`, which is a second page not shown here. That is the orphaned-assignment check working — in a real package, retrieve that page too.

**Deleting an assignment is not a destructive change.** Per the guide: *"You can't delete ActionOverrides by deploying with destructiveChange.xml. To delete an ActionOverride, retrieve the CustomObject. In the definition file, find the `<ActionOverrides>` section, and remove the `<content>` row. Then, change the `<type>` value in that same section to Default."* The `profileActionOverrides` equivalent is to retrieve the app and remove the `<content>` row. Always retrieve fresh — the guide explicitly warns against reusing a previously retrieved file.

---

## 7. Verify the result

**Setup check (this is the authoritative one).** Lightning App Builder → open `Case_Record_Page_Support` → **Activation**. The three tabs — *Org Default*, *App Default*, *App, Record Type, and Profile* — map one-to-one onto the three assignment shapes above. If the page you just deployed does not appear on the tab you expect, the assignment metadata did not deploy, however clean the `FlexiPage` deploy looked.

**Then walk the rules with a real record**, not the App Builder preview:

| Check | Expected |
|---|---|
| Open a Case with `Status` = `New` | "Escalation" section absent; Escalate button absent |
| Set `Status` = `Escalated`, **save** | "Escalation" section appears |
| Same record, as a user without `Can_Escalate_Case` | Escalate button absent, section still present |
| Remove FLS read on `Escalation_Reason__c` for the test profile | Field gone even though the rule says show |

The middle step is the one people skip: a rule on a **field section** is evaluated only after save, while a rule on a **field** re-evaluates live during edit. Toggling the picklist without saving proves nothing.

**Optional inventory query** — the Tooling API exposes a `FlexiPage` object; use it to confirm the page landed, and see `admin/lightning-record-page-configuration` gotcha 6 for the two ways this query fails.

```soql
SELECT Id, DeveloperName, MasterLabel, Type, EntityDefinitionId
FROM FlexiPage
WHERE DeveloperName = 'Case_Record_Page_Support'
```

**UNVERIFIED (2026-09-04):** FlexiPage does not appear in the Object Reference for the Salesforce Platform (checked against the Summer '26 object_reference text), so the field names above are not grounded in that document. It is a Tooling API object; run this with `sf data query --use-tooling-api` and confirm the field list against your org's describe before relying on it in a script.
