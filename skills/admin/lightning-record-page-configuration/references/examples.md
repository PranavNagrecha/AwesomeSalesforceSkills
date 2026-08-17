# Examples — Lightning Record Page Configuration

## Example 1: Promote a Record Page and Its Assignment from a Full Sandbox to Production

**Context:** A 400-user org runs two Lightning apps over Opportunity — `Sales_Console` (console navigation, used by inside sales) and `Sales_Standard` (used by field reps and management). A rebuilt Opportunity record page has been signed off in a Full sandbox. It must be the default for the whole org, except inside `Sales_Console`, where the existing dense page stays.

**Problem:** The team's first attempt deployed `force-app/main/default/flexipages/` only. The deploy went green and production changed nothing. There was no error to investigate, because the page arrived correctly and simply had nothing pointing at it.

**Solution:**

Step 1 — the page itself. Truncated to the parts that matter; the full file carries every region:

```xml
<!-- force-app/main/default/flexipages/Opportunity_Record_Page.flexipage-meta.xml -->
<?xml version="1.0" encoding="UTF-8" ?>
<FlexiPage xmlns="http://soap.sforce.com/2006/04/metadata">
    <flexiPageRegions>
        <itemInstances>
            <componentInstance>
                <componentInstanceProperties>
                    <name>collapsed</name><value>false</value>
                </componentInstanceProperties>
                <componentName>force:highlightsPanel</componentName>
                <identifier>force_highlightsPanel</identifier>
            </componentInstance>
        </itemInstances>
        <mode>Replace</mode>
        <name>header</name>
        <type>Region</type>
    </flexiPageRegions>
    <masterLabel>Opportunity Record Page</masterLabel>
    <parentFlexiPage>flexipage__default_rec_L</parentFlexiPage>
    <sobjectType>Opportunity</sobjectType>
    <template>
        <name>flexipage:recordHomeTemplateDesktop</name>
    </template>
    <type>RecordPage</type>
</FlexiPage>
```

Step 2 — the org default, which lives on the object, not the page:

```xml
<!-- force-app/main/default/objects/Opportunity/Opportunity.object-meta.xml -->
<actionOverrides>
    <actionName>View</actionName>
    <content>Opportunity_Record_Page</content>
    <formFactor>Large</formFactor>
    <type>Flexipage</type>
</actionOverrides>
```

Step 3 — the console app keeps its own page, as an app default. Note that desktop and mobile are two separate overrides, and that the App Builder stamps its own `comment` on anything it writes:

```xml
<!-- force-app/main/default/applications/Sales_Console.app-meta.xml -->
<actionOverrides>
    <actionName>View</actionName>
    <comment>Action override created by Lightning App Builder during activation.</comment>
    <content>Opportunity_Console_Page</content>
    <formFactor>Large</formFactor>
    <skipRecordTypeSelect>false</skipRecordTypeSelect>
    <type>Flexipage</type>
    <pageOrSobjectType>Opportunity</pageOrSobjectType>
</actionOverrides>
<actionOverrides>
    <actionName>View</actionName>
    <comment>Action override created by Lightning App Builder during activation.</comment>
    <content>Opportunity_Console_Page</content>
    <formFactor>Small</formFactor>
    <skipRecordTypeSelect>false</skipRecordTypeSelect>
    <type>Flexipage</type>
    <pageOrSobjectType>Opportunity</pageOrSobjectType>
</actionOverrides>
```

Drop the `Small` block and console agents on phones fall back to whatever the next rung supplies. Salesforce's own `Dreamhouse` sample app carries exactly this pair of overrides per object for the same reason.

Step 4 — one manifest carrying all three:

```xml
<!-- manifest/package.xml -->
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types><members>Opportunity_Record_Page</members><name>FlexiPage</name></types>
    <types><members>Opportunity_Console_Page</members><name>FlexiPage</name></types>
    <types><members>Opportunity</members><name>CustomObject</name></types>
    <types><members>Sales_Console</members><name>CustomApplication</name></types>
    <version>64.0</version>
</Package>
```

```bash
sf project deploy start --manifest manifest/package.xml --target-org prod --test-level RunLocalTests
```

Step 5 — verify the result rather than the deploy. Log in as one inside-sales user and one field rep, open the same Opportunity in each app, and confirm the two pages differ as designed.

**Why it works:** Deploying `CustomObject` carries the org default; deploying `CustomApplication` carries the console app's override, which by documented precedence beats the org default for anyone working inside that app. The `FlexiPage` members carry only page contents, which is why they cannot do this job alone.

**Source:** Metadata API Developer Guide — FlexiPage, ActionOverride, CustomApplication; `trailheadapps/dreamhouse-lwc` `Dreamhouse.app-meta.xml` for the app-override shape.

---

## Example 2: Replace Three Record-Type Page Layouts with One Dynamic Forms Record Page

**Context:** A Case object has three record types — `Support`, `Billing`, and `Field_Service`. Historically each had its own page layout, and each layout drifted independently. A field added for compliance reached two of the three, and nobody noticed for a quarter.

**Problem:** The differentiation is genuinely field-level, not structural: all three record types want the same header, the same tabs, and the same related lists, and differ only in which fields appear in the detail section. Three pages is three times the maintenance for a difference that fits in a filter.

**Solution:**

Step 1 — place the fields individually as `fieldInstance` items and attach a visibility rule to the ones that are record-type-specific:

```xml
<!-- force-app/main/default/flexipages/Case_Record_Page.flexipage-meta.xml -->
<flexiPageRegions>
    <itemInstances>
        <fieldInstance>
            <fieldInstanceProperties>
                <name>uiBehavior</name><value>required</value>
            </fieldInstanceProperties>
            <fieldItem>Record.Subject</fieldItem>
            <identifier>RecordSubjectField</identifier>
        </fieldInstance>
    </itemInstances>
    <itemInstances>
        <fieldInstance>
            <fieldInstanceProperties>
                <name>uiBehavior</name><value>none</value>
            </fieldInstanceProperties>
            <fieldItem>Record.Invoice_Number__c</fieldItem>
            <identifier>RecordInvoice_Number__cField</identifier>
            <visibilityRule>
                <criteria>
                    <leftValue>{!Record.RecordType.DeveloperName}</leftValue>
                    <operator>EQUAL</operator>
                    <rightValue>Billing</rightValue>
                </criteria>
            </visibilityRule>
        </fieldInstance>
    </itemInstances>
    <name>Facet-case-detail-col1</name>
    <type>Facet</type>
</flexiPageRegions>
```

Step 2 — a field that two of the three record types need uses a `booleanFilter` rather than two components:

```xml
<visibilityRule>
    <criteria>
        <leftValue>{!Record.RecordType.DeveloperName}</leftValue>
        <operator>EQUAL</operator>
        <rightValue>Support</rightValue>
    </criteria>
    <criteria>
        <leftValue>{!Record.RecordType.DeveloperName}</leftValue>
        <operator>EQUAL</operator>
        <rightValue>Field_Service</rightValue>
    </criteria>
    <booleanFilter>1 OR 2</booleanFilter>
</visibilityRule>
```

Step 3 — a component that only compliance officers should see rides a custom permission, not a profile-scoped page:

```xml
<visibilityRule>
    <criteria>
        <leftValue>{!$Permission.CustomPermission.View_Case_Compliance_Panel}</leftValue>
        <operator>EQUAL</operator>
        <rightValue>true</rightValue>
    </criteria>
</visibilityRule>
```

Step 4 — assign once, at Rung 3, and delete the two now-redundant app-scoped overrides that used to point at the retired pages.

Step 5 — verify by opening one record of each record type as a user of each affected profile, and confirm that hiding a field did not also make it unreachable to automation that requires it.

**Why it works:** A visibility rule on `{!Record.RecordType.DeveloperName}` reads the record in context, which only a `RecordPage` can do. `uiBehavior` on a field instance replaces the layout's Required checkbox, and `booleanFilter` combines criteria by 1-based index so one component covers two record types. The compliance panel moves its differentiation onto a custom permission, which is assignable from a permission set — unlike page assignment, which only understands profiles.

**Source:** Metadata API Developer Guide — FlexiPage (FieldInstance, FieldInstanceProperty, UiFormulaRule, UiFormulaCriterion).

---

## Example 3 (Failure): "I Set the Org Default and Half the Org Still Sees the Old Page"

**Context:** A 900-user org. The admin builds a replacement Account record page, opens Activation, sets it as Org Default, and announces the change. Management and operations see the new page. The entire 300-person service organisation does not.

**What goes wrong:** The admin re-activates the page three times, clears browser cache, asks users to log out, and files a support case. None of it works, because none of it addresses the actual resolution path. Two years earlier, someone fixed a service-specific complaint by assigning a page under App, Record Type, and Profile inside the `Service_Console` app. That override still exists, still matches, and by documented precedence still wins. It is stored in the app's metadata, so it never appears when the admin looks at the object.

**Diagnosis:**

```bash
sf project retrieve start --metadata "CustomApplication" --target-org prod
grep -A 8 "profileActionOverrides" force-app/main/default/applications/Service_Console.app-meta.xml
```

```soql
-- Confirm which pages exist for the object before deciding what to keep
SELECT Id, DeveloperName, MasterLabel, Type
FROM FlexiPage
WHERE Type = 'RecordPage' AND EntityDefinitionId = 'Account'
```

**Recovery:**

1. Enumerate every `profileActionOverrides` and `actionOverrides` entry across every app that exposes Account. Record which profile, record type, and form factor each one names.
2. For each stale entry, decide: delete it so the org default takes over, or repoint `content` at the new page. Repointing is safer when the assignment was deliberate; deleting is right when nobody can say why it exists.
3. Deploy the `CustomApplication` change — not the page, which never needed to move.
4. Re-verify by logging in as a service user, not by re-opening the Activation dialog. The dialog shows what you set, not what resolves.

**The general rule:** an org default is the *lowest* rung. Setting it can only change behaviour for populations that have nothing more specific already pointing somewhere else. Before changing an org default, enumerate the app-scoped overrides — see `gotchas.md` Gotcha 2.

**Source:** Metadata API Developer Guide — CustomApplication (`profileActionOverrides`); Tooling API — FlexiPage.
