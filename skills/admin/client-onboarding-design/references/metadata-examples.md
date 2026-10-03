# Metadata Examples: Client Onboarding Design

The deployable form of the wealth onboarding design in `examples.md` Example 1: an Action Plan template whose compliance gate is an item dependency, the document types the onboarding collects, and the document checklist settings.

Grounding: Metadata API Developer Guide, ActionPlanTemplate fields, dependencies, and sample (`api_meta L15080-15365`), DocumentChecklistSettings (`api_meta L55674-55735`), DocumentType (`api_meta L55744-55800`); Object Reference, ActionPlan, ActionPlanTemplateItem, and ActionPlanTemplateVersion (`object_reference L21594-22765`); FSC Developer Guide, DocumentChecklistItem (`fsc_dev_guide L14520-14740`). Element names not found in those guides are marked UNVERIFIED.

Licence gate: creating or accessing Action Plan templates needs the Customize Application permission and the IndustriesActionPlans license.

## 1. Action Plan template with dependency gates

The KYC check releases the compliance review, and the compliance review releases the funding instructions. Every item is required; the dependencies create the order.

`force-app/main/default/actionPlanTemplates/Wealth_Onboarding_v1.apt-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ActionPlanTemplate xmlns="http://soap.sforce.com/2006/04/metadata">
    <actionPlanTemplateItem>
        <actionPlanTemplateItemValue>
            <name>Subject</name>
            <valueLiteral>Run KYC and AML identity check</valueLiteral>
            <itemEntityType>Task</itemEntityType>
        </actionPlanTemplateItemValue>
        <actionPlanTemplateItemValue>
            <name>Priority</name>
            <valueLiteral>High</valueLiteral>
            <itemEntityType>Task</itemEntityType>
        </actionPlanTemplateItemValue>
        <actionPlanTemplateItemValue>
            <name>ActivityDate</name>
            <valueFormula>StartDate + 2</valueFormula>
            <itemEntityType>Task</itemEntityType>
        </actionPlanTemplateItemValue>
        <displayOrder>1</displayOrder>
        <isRequired>true</isRequired>
        <itemEntityType>Task</itemEntityType>
        <name>Run KYC check</name>
        <uniqueName>WOB_Run_KYC_Check</uniqueName>
    </actionPlanTemplateItem>
    <actionPlanTemplateItem>
        <actionPlanTemplateItemValue>
            <name>Subject</name>
            <valueLiteral>Capture beneficial ownership disclosure</valueLiteral>
            <itemEntityType>Task</itemEntityType>
        </actionPlanTemplateItemValue>
        <actionPlanTemplateItemValue>
            <name>Priority</name>
            <valueLiteral>High</valueLiteral>
            <itemEntityType>Task</itemEntityType>
        </actionPlanTemplateItemValue>
        <actionPlanTemplateItemValue>
            <name>ActivityDate</name>
            <valueFormula>StartDate + 2</valueFormula>
            <itemEntityType>Task</itemEntityType>
        </actionPlanTemplateItemValue>
        <displayOrder>2</displayOrder>
        <isRequired>true</isRequired>
        <itemEntityType>Task</itemEntityType>
        <name>Capture beneficial ownership</name>
        <uniqueName>WOB_Beneficial_Ownership</uniqueName>
    </actionPlanTemplateItem>
    <actionPlanTemplateItem>
        <actionPlanTemplateItemValue>
            <name>Subject</name>
            <valueLiteral>Compliance officer review</valueLiteral>
            <itemEntityType>Task</itemEntityType>
        </actionPlanTemplateItemValue>
        <actionPlanTemplateItemValue>
            <name>Priority</name>
            <valueLiteral>High</valueLiteral>
            <itemEntityType>Task</itemEntityType>
        </actionPlanTemplateItemValue>
        <actionPlanTemplateItemValue>
            <name>ActivityDate</name>
            <valueFormula>StartDate + 4</valueFormula>
            <itemEntityType>Task</itemEntityType>
        </actionPlanTemplateItemValue>
        <displayOrder>3</displayOrder>
        <isRequired>true</isRequired>
        <itemEntityType>Task</itemEntityType>
        <name>Compliance officer review</name>
        <uniqueName>WOB_Compliance_Review</uniqueName>
    </actionPlanTemplateItem>
    <actionPlanTemplateItem>
        <actionPlanTemplateItemValue>
            <name>Subject</name>
            <valueLiteral>Send account funding instructions</valueLiteral>
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
        <displayOrder>4</displayOrder>
        <isRequired>true</isRequired>
        <itemEntityType>Task</itemEntityType>
        <name>Send funding instructions</name>
        <uniqueName>WOB_Send_Funding_Instructions</uniqueName>
    </actionPlanTemplateItem>
    <actionPlanTemplateItemDependencies>
        <name>Review after KYC</name>
        <creationType>OnPreviousItemCompleted</creationType>
        <previousTemplateItem>
            <actionPlanTemplateItemValue>
                <name>Subject</name>
                <valueLiteral>Run KYC and AML identity check</valueLiteral>
                <itemEntityType>Task</itemEntityType>
            </actionPlanTemplateItemValue>
            <actionPlanTemplateItemValue>
                <name>Priority</name>
                <valueLiteral>High</valueLiteral>
                <itemEntityType>Task</itemEntityType>
            </actionPlanTemplateItemValue>
            <actionPlanTemplateItemValue>
                <name>ActivityDate</name>
                <valueFormula>StartDate + 2</valueFormula>
                <itemEntityType>Task</itemEntityType>
            </actionPlanTemplateItemValue>
            <displayOrder>1</displayOrder>
            <isRequired>true</isRequired>
            <itemEntityType>Task</itemEntityType>
            <name>Run KYC check</name>
            <uniqueName>WOB_Run_KYC_Check</uniqueName>
        </previousTemplateItem>
        <templateItem>
            <actionPlanTemplateItemValue>
                <name>Subject</name>
                <valueLiteral>Compliance officer review</valueLiteral>
                <itemEntityType>Task</itemEntityType>
            </actionPlanTemplateItemValue>
            <actionPlanTemplateItemValue>
                <name>Priority</name>
                <valueLiteral>High</valueLiteral>
                <itemEntityType>Task</itemEntityType>
            </actionPlanTemplateItemValue>
            <actionPlanTemplateItemValue>
                <name>ActivityDate</name>
                <valueFormula>StartDate + 4</valueFormula>
                <itemEntityType>Task</itemEntityType>
            </actionPlanTemplateItemValue>
            <displayOrder>3</displayOrder>
            <isRequired>true</isRequired>
            <itemEntityType>Task</itemEntityType>
            <name>Compliance officer review</name>
            <uniqueName>WOB_Compliance_Review</uniqueName>
        </templateItem>
    </actionPlanTemplateItemDependencies>
    <actionPlanTemplateItemDependencies>
        <name>Funding after compliance review</name>
        <creationType>OnPreviousItemCompleted</creationType>
        <previousTemplateItem>
            <actionPlanTemplateItemValue>
                <name>Subject</name>
                <valueLiteral>Compliance officer review</valueLiteral>
                <itemEntityType>Task</itemEntityType>
            </actionPlanTemplateItemValue>
            <actionPlanTemplateItemValue>
                <name>Priority</name>
                <valueLiteral>High</valueLiteral>
                <itemEntityType>Task</itemEntityType>
            </actionPlanTemplateItemValue>
            <actionPlanTemplateItemValue>
                <name>ActivityDate</name>
                <valueFormula>StartDate + 4</valueFormula>
                <itemEntityType>Task</itemEntityType>
            </actionPlanTemplateItemValue>
            <displayOrder>3</displayOrder>
            <isRequired>true</isRequired>
            <itemEntityType>Task</itemEntityType>
            <name>Compliance officer review</name>
            <uniqueName>WOB_Compliance_Review</uniqueName>
        </previousTemplateItem>
        <templateItem>
            <actionPlanTemplateItemValue>
                <name>Subject</name>
                <valueLiteral>Send account funding instructions</valueLiteral>
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
            <displayOrder>4</displayOrder>
            <isRequired>true</isRequired>
            <itemEntityType>Task</itemEntityType>
            <name>Send funding instructions</name>
            <uniqueName>WOB_Send_Funding_Instructions</uniqueName>
        </templateItem>
    </actionPlanTemplateItemDependencies>
    <actionPlanType>Industries</actionPlanType>
    <category>Onboarding</category>
    <description>Wealth client onboarding v1: KYC, beneficial ownership, compliance review, funding</description>
    <isAdHocItemCreationEnabled>false</isAdHocItemCreationEnabled>
    <name>Wealth Onboarding v1</name>
    <targetEntityType>Account</targetEntityType>
    <uniqueName>Wealth_Onboarding_v1</uniqueName>
</ActionPlanTemplate>
```

| Element | Notes |
|---|---|
| `targetEntityType` | `Account`. Test Financial Account anchoring separately; it is in the plan parent list from API 48.0 but not in the Metadata API's template parent list (gotcha 3) |
| `actionPlanTemplateItemDependencies` | API 59.0. `previousTemplateItem` is the prerequisite, `templateItem` the dependent. `OnPreviousItemCompleted` is the value in the guide's sample |
| `valueFormula` | `StartDate + N` is the due date; no `DaysFromStart` field exists |
| `isRequired` | Records that the task must be done; does not by itself create order |
| `category` | `Onboarding` (API 64.0); object reference picklist values are `Onboarding` and `Application` |
| `isAdHocItemCreationEnabled` | Required from API 59.0; `false` keeps the regulated sequence closed to ad hoc tasks |
| `uniqueName` | Required on the template and every item; keep stable across versions |

UNVERIFIED (2026-10-03): as in the guide's sample, each dependency repeats the full item definition; the guide does not say whether a shorter reference is accepted. UNVERIFIED (2026-10-03): a document checklist item can be a template item (`ItemEntityType` includes Document Checklist Item; the plan item API value is `DocumentChecklistItem`), but the item-value names for a document item are not in the Metadata API sample, so documents are kept out of this template and tracked as document checklist items on the account.

## 2. Document types

`force-app/main/default/documentTypes/Signed_Account_Agreement.documentType-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<DocumentType xmlns="http://soap.sforce.com/2006/04/metadata">
    <description>Client-signed account agreement collected before funding</description>
    <isActive>true</isActive>
    <masterLabel>Signed Account Agreement</masterLabel>
</DocumentType>
```

`force-app/main/default/documentTypes/Investment_Policy_Statement.documentType-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<DocumentType xmlns="http://soap.sforce.com/2006/04/metadata">
    <description>Investment policy statement agreed with the advisor</description>
    <isActive>true</isActive>
    <masterLabel>Investment Policy Statement</masterLabel>
</DocumentType>
```

## 3. Document checklist settings

`force-app/main/default/settings/DocumentChecklist.settings-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<DocumentChecklistSettings xmlns="http://soap.sforce.com/2006/04/metadata">
    <dciCustomSharing>false</dciCustomSharing>
    <deleteDCIWithFiles>false</deleteDCIWithFiles>
</DocumentChecklistSettings>
```

`deleteDCIWithFiles` stays `false` so compliance evidence is not deleted with an uploaded file. `dciCustomSharing` enables custom sharing rules for document checklist items when set to `true`; leave it off unless the sharing model needs it.

## 4. package.xml

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Wealth_Onboarding_v1</members>
        <name>ActionPlanTemplate</name>
    </types>
    <types>
        <members>Investment_Policy_Statement</members>
        <members>Signed_Account_Agreement</members>
        <name>DocumentType</name>
    </types>
    <types>
        <members>DocumentChecklist</members>
        <name>Settings</name>
    </types>
    <version>67.0</version>
</Package>
```

## Deploy order

1. `Settings: DocumentChecklist` and `DocumentType`.
2. `ActionPlanTemplate`, deployed by a user with the IndustriesActionPlans license.
3. Publish the template version in Setup if the deploy leaves it in `Draft` (the guide's sample deploys `status` `Draft`), so plans can be created from it.

## Verification

- Launch a plan on a test Account: only "Run KYC check" and "Capture beneficial ownership" tasks exist at launch.
- Complete the KYC task: "Compliance officer review" appears. Complete it: "Send funding instructions" appears.
- `SELECT Status, Version FROM ActionPlanTemplateVersion WHERE ActionPlanTemplate.UniqueName = 'Wealth_Onboarding_v1'` shows the published version. UNVERIFIED (2026-10-03): `UniqueName` as a queryable field on `ActionPlanTemplate` is inferred from the metadata field `uniqueName`.
