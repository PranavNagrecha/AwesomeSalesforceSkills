# Examples — LWC App Builder Config

Scenario-shaped walkthroughs. The complete deployable bundle — html, js, js-meta.xml, Apex, Jest, `package.xml` — is in `references/code-examples.md`; these examples isolate one decision each.

---

## Example 1: Multi-Surface Bundle (Record Page + App Page + Experience Cloud)

**Context:** A pipeline-summary LWC needs to appear on Account and Opportunity record pages, on a custom App Page ("Pipeline Dashboard"), and on an Experience Cloud page. Each surface needs slightly different admin configuration, and the App Page version must also support phone.

**Problem:** Without per-target `targetConfig` blocks, admins see either no configuration or the same generic panel on every surface. Without `<objects>`, admins can drop the component on Case or Contact pages where its data model does not apply — the guide is explicit that with no `<objects>` tag set the component supports all supported objects (`lwc_guide targets-lightning-record-page` L19363).

**Solution:**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<LightningComponentBundle xmlns="http://soap.sforce.com/2006/04/metadata">
  <apiVersion>63.0</apiVersion>
  <isExposed>true</isExposed>
  <masterLabel>Pipeline Summary</masterLabel>
  <description>Shows pipeline totals filtered by owner and stage.</description>

  <targets>
    <target>lightning__RecordPage</target>
    <target>lightning__AppPage</target>
    <target>lightningCommunity__Page</target>
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
        <supportedFormFactor type="Large"/>
        <supportedFormFactor type="Small"/>
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
        required="true"
        default="00E000000000000"/>
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

**Why it works:**

- `isExposed=true` plus a non-empty `<targets>` is what makes the bundle reachable from any builder (L18712).
- Each surface gets a dedicated `targetConfig`, so admins only see the knobs that make sense there. Every `targets` attribute value matches a page type listed under `<targets>`, which the guide requires (L18769).
- `<objects>` scopes the record-page exposure to Account and Opportunity, and appears only in the record-page block because that is the only place it works (L19363).
- The form-factor block uses `<supportedFormFactor type="…"/>`, sits inside the App Page `targetConfig`, and therefore applies only there (L18993–L18999).
- Experience Cloud takes two targets: `lightningCommunity__Page` puts the component in the Components panel, and `lightningCommunity__Default` is what carries the editable properties (L18811–L18812, `use-config-for-community-builder` L8106–L8110).
- `ownerRoleId` is `required="true"` **and** has a `default`, because a required property with no default makes the component appear invalid the moment it is added in App Builder (`use-config-for-app-builder-tips` L9899).
- `recordId` and `objectApiName` are auto-populated on the record-page target and declared only in the JS (`@api recordId; @api objectApiName;`). On the Experience Cloud target they are not auto-bound — an admin enters `{!recordId}` (L7894, L7900).

---

## Example 2: Apex-Backed Dynamic Picklist for a Design Attribute

**Context:** Admins configuring the component on an Opportunity record page need to pick which currency-typed field to summarize. The list of valid fields depends on org schema and cannot be hardcoded.

**Problem:** A static CSV datasource cannot reflect custom fields added after the component ships. Using `type="Picklist"` fails because it is not a documented design-attribute type — the App Builder targets document `Boolean`, `Integer`, and `String` only (L19351–L19353).

**Solution:**

```apex
global with sharing class OpportunityCurrencyFieldPickList extends VisualEditor.DynamicPickList {

    global override VisualEditor.DataRow getDefaultValue() {
        return new VisualEditor.DataRow('Amount', 'Amount');
    }

    global override VisualEditor.DynamicPickListRows getValues() {
        VisualEditor.DynamicPickListRows rows = new VisualEditor.DynamicPickListRows();
        for (Schema.SObjectField f : Opportunity.SObjectType.getDescribe().fields.getMap().values()) {
            Schema.DescribeFieldResult d = f.getDescribe();
            if (d.getType() == Schema.DisplayType.CURRENCY && d.isAccessible()) {
                rows.addRow(new VisualEditor.DataRow(d.getLabel(), d.getName()));
            }
        }
        rows.setContainsAllRows(true);
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

**Why it works:** The design attribute uses the supported `type="String"` plus a `datasource="apex://…"` — the guide's documented shape for setting picklist values dynamically from an Apex class (L18976). The class extends `VisualEditor.DynamicPickList` and overrides `getValues()` and `getDefaultValue()` (`apexrefguide` L247820–L247834, L247876–L247884). `VisualEditor.DataRow` takes label first, value second (`apexrefguide` L247586–L247594). `setContainsAllRows(true)` matters because a picklist in a Lightning component displays only the first 200 values, and with `containsAllRows` false a type-ahead search searches only those (`apexrefguide` L248021–L248025).

**Scaling it to more than one object:** give the class a `VisualEditor.DesignTimePageContext` constructor parameter and branch on `context.entityName` / `context.pageType` instead of hardcoding `Opportunity` — see `references/code-examples.md` §4.

---

## Example 3: The Surface × Property Matrix, Before Any XML

**Context:** A component is requested for "record pages, the home page, and the community." The temptation is to open the meta file and start typing.

**Problem:** The meta file is where irreversible decisions get made by accident — object scope, form factors, `min`/`max`, and required flags all freeze once the component is in use (L9904–L9909, L8128–L8137). A matrix makes each of those a deliberate cell.

**Solution:** fill this in first; the XML then writes itself.

| Property | Type | Record Page | App Page | Home Page | Community Default | Notes |
|---|---|---|---|---|---|---|
| `cardTitle` | String | free text, default "Pipeline Summary" | fixed 3-value `datasource` | free text | free text | Static list is safe only if the three values are genuinely stable |
| `amountField` | String | `apex://PipelineFieldPickList` | — | — | — | Needs the Apex class in the same deploy |
| `maxRows` | Integer | `min=1 max=50 default=10` | same | `default=5` | — | `min`/`max` freeze once placed (L9907) |
| `showTotals` | Boolean | `default=true` | `default=true` | — | `default=false` | — |
| `accentColor` | Color | **invalid here** | **invalid here** | **invalid here** | `default=rgba(0,112,210,1)` | `Color` is documented only for community and email targets (L18778, L18873) |
| — | — | `<objects>`: Case, Account | — | — | — | Only record pages accept `<objects>` (L19363) |
| — | — | Form factors: Large + Small | Large + Small | **Large only** | — | Home pages support only `Large` (L9795) |

**Why it works:** Every cell that says "invalid here" or "Large only" is a deploy failure or a support ticket avoided before a line of XML exists, and every freeze-once-placed cell gets a decision from someone who knows the business rule rather than a default from whoever typed fastest.

---

## Anti-Pattern: The Swiss-Army-Knife Bundle

**What practitioners do:** A single LWC bundle exposes itself on every target — Record Page, App Page, Home Page, Experience Cloud, Utility Bar, Flow Screen — with 15 design attributes covering all the surface-specific options in one shared `targetConfig`-less list. The component then branches internally based on `objectApiName`, feature flags, and "mode" properties.

**What goes wrong:** Admins see irrelevant properties on every surface (for example, a "Utility Bar Badge Color" knob on a record-page placement — which is doubly wrong, since `Color` is not a documented App Builder type). The JS carries every surface's logic, inflating bundle size. Changing one property's type breaks placements on surfaces that never used it. Some of those targets do not even accept the properties: `lightning__Tab` supports neither `property` nor `supportedFormFactor` (`use-config-custom-tab` L7987), and `lightning__RecordAction` supports no component properties at all (L19307). Test plans balloon because every deploy has to re-verify every surface — and once placed, the over-broad target list can no longer be narrowed (L9906).

**Correct approach:** Split by surface. Either create separate bundles for genuinely different use cases, or keep one bundle but define a dedicated `<targetConfig>` per target with only the properties that surface actually uses. Keep each `targetConfig`'s property list short — if it exceeds five or six knobs, the component is probably doing too many things.
