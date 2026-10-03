# Metadata Examples: Care Coordination Requirements

Two deployable pieces that a care coordination design usually needs: the org settings that switch on the referral and Slack capabilities, and an Action Plan template that generates SDOH intervention tasks on a barrier's Case.

Grounding: Metadata API Developer Guide, IndustriesSettings Health Cloud fields (`api_meta L119538-119560`, sample and package manifest `L120228-120240`) and ActionPlanTemplate (`api_meta L15080-15365`); Object Reference, ActionPlanTemplateItem `ItemEntityType` values (`object_reference L22217-22300`); Health Cloud developer guide, org pref table (`health_cloud_dev_guide L8345-8368`). Element names not found in those guides are marked UNVERIFIED.

Licence gate: `IndustriesSettings` fields "are only available to customers with org editions where the vertical is enabled". `ActionPlanTemplate` requires the Customize Application permission and the IndustriesActionPlans license.

## 1. Industries settings

`force-app/main/default/settings/Industries.settings-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<IndustriesSettings xmlns="http://soap.sforce.com/2006/04/metadata">
    <enableCareMgmtSlackAccess>false</enableCareMgmtSlackAccess>
    <enableClinicalDataModel>true</enableClinicalDataModel>
</IndustriesSettings>
```

| Field | Value | Why |
|---|---|---|
| `enableClinicalDataModel` | `true` | Clinical Data Model on (API 51.0, default false). Referrals (`ClinicalServiceRequest`) are listed among objects that need the FHIR-Aligned Clinical Data Model org pref. UNVERIFIED (2026-10-03): that this field is that org pref is inferred from its description |
| `enableCareMgmtSlackAccess` | `false` | Care Coordination for Slack app off until the Slack decision is made (API 56.0) |

UNVERIFIED (2026-10-03): the Enhanced Care Plans setting on the Integrated Care Management Settings page has no `IndustriesSettings` field in the Summer '26 Metadata API guide (the only care plan field, `enableCarePlansPreference`, is documented for Public Sector Solutions). Enable it in Setup: Setup, then Integrated Care Management Settings, then Enhanced Care Plans.

## 2. Action Plan template for SDOH interventions on a Case

`force-app/main/default/actionPlanTemplates/SDOH_Transportation_Intervention.apt-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ActionPlanTemplate xmlns="http://soap.sforce.com/2006/04/metadata">
    <actionPlanTemplateItem>
        <actionPlanTemplateItemValue>
            <name>Subject</name>
            <valueLiteral>Confirm transportation need with patient</valueLiteral>
            <itemEntityType>Task</itemEntityType>
        </actionPlanTemplateItemValue>
        <actionPlanTemplateItemValue>
            <name>Priority</name>
            <valueLiteral>High</valueLiteral>
            <itemEntityType>Task</itemEntityType>
        </actionPlanTemplateItemValue>
        <actionPlanTemplateItemValue>
            <name>ActivityDate</name>
            <valueFormula>StartDate + 1</valueFormula>
            <itemEntityType>Task</itemEntityType>
        </actionPlanTemplateItemValue>
        <displayOrder>1</displayOrder>
        <isRequired>true</isRequired>
        <itemEntityType>Task</itemEntityType>
        <name>Confirm transportation need</name>
        <uniqueName>SDOH_Transport_Confirm_Need</uniqueName>
    </actionPlanTemplateItem>
    <actionPlanTemplateItem>
        <actionPlanTemplateItemValue>
            <name>Subject</name>
            <valueLiteral>Refer patient to community transport program</valueLiteral>
            <itemEntityType>Task</itemEntityType>
        </actionPlanTemplateItemValue>
        <actionPlanTemplateItemValue>
            <name>Priority</name>
            <valueLiteral>Normal</valueLiteral>
            <itemEntityType>Task</itemEntityType>
        </actionPlanTemplateItemValue>
        <actionPlanTemplateItemValue>
            <name>ActivityDate</name>
            <valueFormula>StartDate + 5</valueFormula>
            <itemEntityType>Task</itemEntityType>
        </actionPlanTemplateItemValue>
        <displayOrder>2</displayOrder>
        <isRequired>true</isRequired>
        <itemEntityType>Task</itemEntityType>
        <name>Refer to transport program</name>
        <uniqueName>SDOH_Transport_Refer_Program</uniqueName>
    </actionPlanTemplateItem>
    <actionPlanTemplateItemDependencies>
        <name>Refer after need confirmed</name>
        <creationType>OnPreviousItemCompleted</creationType>
        <previousTemplateItem>
            <actionPlanTemplateItemValue>
                <name>Subject</name>
                <valueLiteral>Confirm transportation need with patient</valueLiteral>
                <itemEntityType>Task</itemEntityType>
            </actionPlanTemplateItemValue>
            <displayOrder>1</displayOrder>
            <isRequired>true</isRequired>
            <itemEntityType>Task</itemEntityType>
            <name>Confirm transportation need</name>
            <uniqueName>SDOH_Transport_Confirm_Need</uniqueName>
        </previousTemplateItem>
        <templateItem>
            <actionPlanTemplateItemValue>
                <name>Subject</name>
                <valueLiteral>Refer patient to community transport program</valueLiteral>
                <itemEntityType>Task</itemEntityType>
            </actionPlanTemplateItemValue>
            <displayOrder>2</displayOrder>
            <isRequired>true</isRequired>
            <itemEntityType>Task</itemEntityType>
            <name>Refer to transport program</name>
            <uniqueName>SDOH_Transport_Refer_Program</uniqueName>
        </templateItem>
    </actionPlanTemplateItemDependencies>
    <actionPlanType>Industries</actionPlanType>
    <description>Intervention tasks for a transportation barrier tracked on a Case</description>
    <isAdHocItemCreationEnabled>true</isAdHocItemCreationEnabled>
    <name>SDOH Transportation Intervention</name>
    <targetEntityType>Case</targetEntityType>
    <uniqueName>SDOH_Transportation_Intervention</uniqueName>
</ActionPlanTemplate>
```

| Element | Notes |
|---|---|
| `targetEntityType` | `Case` is a supported parent. `CareBarrier` is not in the supported parent list, which is why the plan hangs off the barrier's Case |
| `isAdHocItemCreationEnabled` | Required (API 59.0); `true` lets a CHW add a task the template did not foresee |
| `actionPlanTemplateItemDependencies` | API 59.0. `creationType` `OnPreviousItemCompleted` is the value used in the guide's sample; the referral task is created only after the confirmation task completes |
| `valueFormula` | `StartDate + N` sets the task due date, as in the guide's sample |
| `actionPlanType` | `Industries`; other values (`Retail`, `ITSM`, `PrvdEngmtCompliance`, `KAM`) are documented from API 63.0 |

UNVERIFIED (2026-10-03): the guide's sample repeats the full item definition inside `previousTemplateItem` and `templateItem`, so this example does the same; the guide does not say whether a shorter reference by `uniqueName` is accepted.

## 3. package.xml

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>SDOH_Transportation_Intervention</members>
        <name>ActionPlanTemplate</name>
    </types>
    <types>
        <members>Industries</members>
        <name>Settings</name>
    </types>
    <version>67.0</version>
</Package>
```

## Deploy order

1. `Settings: Industries` (turns on the clinical data model before anything references referrals).
2. Enhanced Care Plans in Setup (no metadata field found).
3. `ActionPlanTemplate`.

## Verification

- `SELECT Id FROM ClinicalServiceRequest LIMIT 1` returns zero rows rather than an "object not supported" error.
- Launching the template on a test Case creates the confirmation task, and the referral task appears only after the first task is completed.
- Retrieve `Settings:Industries` after deploy and confirm both values; settings retrieve as one file per settings component.
