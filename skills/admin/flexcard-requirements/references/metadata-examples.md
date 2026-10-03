# Metadata Examples: FlexCard Requirements

FlexCards themselves are not hand-authored as metadata in this skill: the card definition object `OmniUiCard` is internal-use only, and the OmniStudio metadata reference did not fetch for this pass. What a requirements package can hand over as deployable metadata is the access each audience needs. This file turns the "care coordinators" row of the audience register in `examples.md` Example 3 into a permission set.

Grounding: Metadata API Developer Guide, PermissionSet (`classAccesses`, `fieldPermissions`, `objectPermissions`; `api_meta L94772-94840`); Salesforce Industries Developer Guide, `OmniUiCard` internal-use note (`salesforce_industries_dev_guide L91930-91933`); Salesforce Security Guide, guest user access (`salesforce_security_impl_guide L2868-2869`, `L2985-2987`).

Licence gate: FlexCards need an OmniStudio-enabled org. The objects below (`ClinicalEncounter`) are Health Cloud objects that need the FHIR-Aligned Clinical Data Model org pref.

## 1. Permission set for the coordinator audience

`force-app/main/default/permissionsets/Patient_Summary_Card_Coordinator.permissionset-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<PermissionSet xmlns="http://soap.sforce.com/2006/04/metadata">
    <classAccesses>
        <apexClass>PatientSummaryService</apexClass>
        <enabled>true</enabled>
    </classAccesses>
    <description>Access needed by care coordinators to use the Patient Summary FlexCard and its New Encounter action</description>
    <fieldPermissions>
        <editable>false</editable>
        <field>Account.Phone</field>
        <readable>true</readable>
    </fieldPermissions>
    <hasActivationRequired>false</hasActivationRequired>
    <label>Patient Summary Card Coordinator</label>
    <objectPermissions>
        <allowCreate>true</allowCreate>
        <allowDelete>false</allowDelete>
        <allowEdit>true</allowEdit>
        <allowRead>true</allowRead>
        <modifyAllRecords>false</modifyAllRecords>
        <object>ClinicalEncounter</object>
        <viewAllRecords>false</viewAllRecords>
    </objectPermissions>
</PermissionSet>
```

| Element | Requirement row it satisfies |
|---|---|
| `classAccesses` `PatientSummaryService` | An Apex action or data source the card calls; the class must exist before this permission set deploys |
| `fieldPermissions` `Account.Phone` | The card displays the patient's phone number; read-only |
| `objectPermissions` `ClinicalEncounter` | The New Encounter action creates encounter records; no delete |

UNVERIFIED (2026-10-03): `PatientSummaryService` is an illustrative class name for whatever Apex the card's data source or action calls; replace it with the real class or remove the block if the card uses only Data Mappers and Integration Procedures. UNVERIFIED (2026-10-03): the OmniStudio user permission set or licence each audience needs in addition to this permission set is help-only.

## 2. package.xml

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Patient_Summary_Card_Coordinator</members>
        <name>PermissionSet</name>
    </types>
    <version>67.0</version>
</Package>
```

## 3. Guest audience (Setup procedure, not this permission set)

For a public Experience Cloud placement, record access comes from guest user sharing rules, which "can only grant Read Only access", because guest org-wide defaults are Private for all objects and cannot be changed.

1. Setup, then Sharing Settings, then the object's sharing rules, then New.
2. Choose the guest user sharing rule type, set criteria that select only the records the public card may show, and share with the site's guest user with Read Only access.
3. Remove every edit action from the card state shown to guests.

## Deploy order

1. Apex classes and Integration Procedures the card depends on.
2. This permission set, then assignment to care coordinators.
3. The FlexCard, through OmniStudio deployment tooling (never by editing `OmniUiCard` records).

## Verification

- A care coordinator with only this permission set (plus the org's OmniStudio access) sees the phone number and can launch New Encounter.
- A coordinator without it sees the card fields blank or gets an access error on the action, which confirms the permission set is the gate.
- A guest visitor sees only records matched by the guest sharing rule and no edit actions.
