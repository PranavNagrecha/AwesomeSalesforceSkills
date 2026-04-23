# Examples — LWC App Builder Config

## Example 1: Multi-Surface Bundle (Record Page + App Page + Experience Cloud)

**Context:** A pipeline-summary LWC needs to appear on Account and Opportunity record pages, on a custom App Page ("Pipeline Dashboard"), and on an Experience Cloud page. Each surface needs slightly different admin configuration, and the App Page version must also support phone.

**Problem:** Without per-target `targetConfig` blocks, admins see either no configuration or the same generic panel on every surface. Without `<objects>`, admins can drop the component on Case or Contact pages where its data model does not apply.

**Solution:**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<LightningComponentBundle xmlns="http://soap.sforce.com/2006/04/metadata">
  <apiVersion>62.0</apiVersion>
  <isExposed>true</isExposed>
  <masterLabel>Pipeline Summary</masterLabel>
  <description>Shows pipeline totals filtered by owner and stage.</description>

  <targets>
    <target>lightning__RecordPage</target>
    <target>lightning__AppPage</target>
    <target>lightningCommunity__Default</target>
  </targets>

  <targetConfigs>
    <targetConfig targets="lightning__RecordPage">
      <objects>
        <object>Account</object>
        <object>Opportunity</object>
      </objects>
      <property
        name="title"
        type="String"
        label="Card Title"
        description="Heading shown above the summary."
        default="Pipeline Summary"/>
      <property
        name="stageField"
        type="String"
        label="Stage Field"
        datasource="apex://OpportunityFieldPickList"
        description="Field to group totals by."/>
    </targetConfig>

    <targetConfig targets="lightning__AppPage">
      <supportedFormFactors>
        <supported formFactor="Large"/>
        <supported formFactor="Small"/>
      </supportedFormFactors>
      <property
        name="title"
        type="String"
        label="Card Title"
        default="Team Pipeline"/>
      <property
        name="ownerRoleId"
        type="String"
        label="Role ID"
        required="true"/>
    </targetConfig>

    <targetConfig targets="lightningCommunity__Default">
      <property
        name="title"
        type="String"
        label="Card Title"
        default="My Pipeline"/>
      <property
        name="showTotals"
        type="Boolean"
        label="Show Totals"
        default="true"/>
    </targetConfig>
  </targetConfigs>
</LightningComponentBundle>
```

**Why it works:** `isExposed=true` lets every builder see the bundle. The three targets each get a dedicated `targetConfig` so admins only see the knobs that make sense on that surface. `<objects>` scopes the record-page exposure to Account and Opportunity. `<supportedFormFactors>` lives inside the App Page config so the Small form factor applies only there. `recordId` and `objectApiName` are auto-injected on the record-page target and only need to be declared in the JS (`@api recordId; @api objectApiName;`).

---

## Example 2: Apex-Backed Dynamic Picklist for a Design Attribute

**Context:** Admins configuring the component on an Opportunity record page need to pick which currency-typed field to summarize. The list of valid fields depends on org schema and cannot be hardcoded.

**Problem:** A static CSV datasource cannot reflect custom fields added after the component ships. Using `type="Picklist"` fails because it is not a valid design-attribute type.

**Solution:**

```apex
global class OpportunityCurrencyFieldPickList extends VisualEditor.DynamicPickList {

    global override VisualEditor.DataRow getDefaultValue() {
        return new VisualEditor.DataRow('Amount', 'Amount');
    }

    global override VisualEditor.DynamicPickListRows getValues() {
        VisualEditor.DynamicPickListRows rows = new VisualEditor.DynamicPickListRows();
        for (Schema.SObjectField f : Opportunity.SObjectType.getDescribe().fields.getMap().values()) {
            Schema.DescribeFieldResult d = f.getDescribe();
            if (d.getType() == Schema.DisplayType.Currency) {
                rows.addRow(new VisualEditor.DataRow(d.getLabel(), d.getName()));
            }
        }
        return rows;
    }
}
```

```xml
<targetConfig targets="lightning__RecordPage">
  <objects>
    <object>Opportunity</object>
  </objects>
  <property
    name="currencyField"
    type="String"
    label="Currency Field"
    description="Which currency field to total."
    datasource="apex://OpportunityCurrencyFieldPickList"/>
</targetConfig>
```

**Why it works:** The design attribute uses the supported `type="String"` plus a `datasource="apex://…"` pointing at a class that implements `VisualEditor.DynamicPickList`. App Builder calls the class whenever an admin opens the property panel, so new custom currency fields show up automatically without a code change.

---

## Anti-Pattern: The Swiss-Army-Knife Bundle

**What practitioners do:** A single LWC bundle exposes itself on every target — Record Page, App Page, Home Page, Experience Cloud, Utility Bar, Flow Screen — with 15 design attributes covering all the surface-specific options in one shared `targetConfig`-less list. The component then branches internally based on `objectApiName`, feature flags, and "mode" properties.

**What goes wrong:** Admins see irrelevant properties on every surface (for example, a "Utility Bar Badge Color" knob on a record-page placement). The JS carries every surface's logic, inflating bundle size. Changing one property's type breaks placements on surfaces that never used it. Test plans balloon because every deploy has to re-verify every surface.

**Correct approach:** Split by surface. Either create separate bundles for genuinely different use cases, or keep one bundle but define a dedicated `<targetConfig>` per target with only the properties that surface actually uses. Keep each `targetConfig`'s property list short — if it exceeds five or six knobs, the component is probably doing too many things.
