# LLM Anti-Patterns — LWC App Builder Config

Common mistakes AI coding assistants make when generating or advising on LWC `js-meta.xml` files. These help the consuming agent self-check its own output. Every "correct pattern" below is grounded in the crawled Lightning Web Components Developer Guide (`lwc_guide <page-slug> L<n>`).

---

## Anti-Pattern 1: Setting `isExposed=false` (or omitting it) and then expecting the component to appear

**What the LLM generates:**

```xml
<LightningComponentBundle xmlns="http://soap.sforce.com/2006/04/metadata">
  <apiVersion>63.0</apiVersion>
  <isExposed>false</isExposed>
  <targets>
    <target>lightning__RecordPage</target>
  </targets>
</LightningComponentBundle>
```

**Why it happens:** The default scaffold emits `<isExposed>false</isExposed>` — the guide's own "simplest configuration file" does (`create-components-meta-file` L719–L721). LLMs copy the scaffold verbatim and append `<targets>` without flipping the boolean.

**Correct pattern:**

```xml
<isExposed>true</isExposed>
```

Both halves are required: "To allow the component to be used in a builder, set `isExposed` to `true` and define at least one `<target>`" (`reference-configuration-tags` L18712).

**Detection hint:** `<targets>` is non-empty and `<isExposed>` is `false` or missing.

---

## Anti-Pattern 2: Writing `<supported formFactor="Small"/>` instead of `<supportedFormFactor type="Small"/>`

**What the LLM generates:**

```xml
<supportedFormFactors>
  <supported formFactor="Small"/>
  <supported formFactor="Large"/>
</supportedFormFactors>
```

**Why it happens:** The plural wrapper suggests a singular `<supported>` child, and `formFactor` reads like the obvious attribute name. The wrapper is right and both inner names are wrong, so the mistake survives a quick skim.

**Correct pattern:**

```xml
<supportedFormFactors>
  <supportedFormFactor type="Large"/>
  <supportedFormFactor type="Small"/>
</supportedFormFactors>
```

The child tag is `supportedFormFactor`, its required attribute is `type`, and the valid values are `Large` (desktop) and `Small` (phone) — `targets-lightning-app-page` L18994–L18999.

**Detection hint:** any `<supported ` element, or any `formFactor=` attribute, inside a `supportedFormFactors` block.

---

## Anti-Pattern 3: Putting `<supportedFormFactors>` at the root of the bundle

**What the LLM generates:**

```xml
<LightningComponentBundle xmlns="http://soap.sforce.com/2006/04/metadata">
  <isExposed>true</isExposed>
  <supportedFormFactors>
    <supportedFormFactor type="Small"/>
  </supportedFormFactors>
  <targets>
    <target>lightning__AppPage</target>
  </targets>
</LightningComponentBundle>
```

**Why it happens:** `<supportedFormFactors>` reads like a bundle-level setting, so LLMs place it next to `<isExposed>` by analogy with `<apiVersion>` and `<masterLabel>`.

**Correct pattern:**

```xml
<targetConfig targets="lightning__AppPage">
  <supportedFormFactors>
    <supportedFormFactor type="Small"/>
  </supportedFormFactors>
</targetConfig>
```

The guide places it precisely: "Specify the `supportedFormFactors` tag set one time inside a `targetConfig` set" (L18993), and "In the `<targetConfigs>` section of the component's configuration file, use the `<supportedFormFactors>` tag set" (`use-config-form-factors` L9793).

**Detection hint:** `<supportedFormFactors>` as a direct child of `<LightningComponentBundle>`.

---

## Anti-Pattern 4: Using a property `type` that does not exist for that target

**What the LLM generates:**

```xml
<property name="severity" type="Picklist" label="Severity">
  <option>low</option>
  <option>medium</option>
  <option>high</option>
</property>
```

or, more subtly, a `Color` picker on a record page:

```xml
<targetConfig targets="lightning__RecordPage">
  <property name="accentColor" type="Color" label="Accent Colour" default="rgba(0, 112, 210, 1)"/>
</targetConfig>
```

**Why it happens:** "Picklist" is a core Salesforce concept, so LLMs assume the design-attribute layer has a matching type. `Color` is worse, because it *is* real — just not on App Builder targets. A snippet copied from an Experience Cloud example carries it across a contract boundary.

**Correct pattern:**

```xml
<property name="severity" type="String" label="Severity" datasource="low,medium,high" default="medium"/>
```

App Builder targets document exactly three types — `Boolean`, `Integer`, `String` (`targets-lightning-record-page` L19351–L19353, `targets-lightning-app-page` L18972–L18975, `targets-lightning-home-page` L19197–L19199). `Color` and `ContentReference` are documented for `lightningCommunity__Default` (L18775–L18779); `Color`, `HorizontalAlignment` and `VerticalAlignment` for `lightningStatic__Email` (L18870–L18876). App Builder does not support the `Map`, `Object`, or `java://` complex types at all (`use-config-for-app-builder-tips` L9908).

**Detection hint:** any `type` value outside the documented set for the enclosing `targetConfig`'s target.

---

## Anti-Pattern 5: Listing `<targets>` but omitting `<targetConfigs>` while promising admin knobs

**What the LLM generates:**

```xml
<targets>
  <target>lightning__RecordPage</target>
  <target>lightning__AppPage</target>
</targets>
```

...while separately telling the user "admins can configure a title and an object filter in App Builder."

**Why it happens:** The LLM conflates "exposed to a target" with "configurable on a target." Without a `<targetConfig>` there are no properties, no `<objects>` scoping, and no form-factor declaration on that surface.

**Correct pattern:** wrap each target that needs configuration in a `<targetConfig targets="…">` block with `<property>` children, and make sure the attribute value matches a page type listed under `<targets>` (L18769).

```xml
<targetConfig targets="lightning__RecordPage">
  <objects>
    <object>Case</object>
  </objects>
  <property name="cardTitle" type="String" label="Card Title" default="Pipeline Summary"/>
</targetConfig>
```

**Detection hint:** the surrounding prose mentions admin-configurable knobs but `<targetConfigs>` is missing, empty, or does not cover the target being described.

---

## Anti-Pattern 6: Declaring a `property name` with no matching `@api` field

**What the LLM generates:**

Meta:
```xml
<targetConfig targets="lightning__RecordPage">
  <property name="maxRows" type="Integer" label="Max Rows" default="25"/>
  <property name="showTotals" type="Boolean" label="Show Total" default="true"/>
</targetConfig>
```

JS:
```javascript
import { LightningElement, api } from 'lwc';

export default class PipelineSummary extends LightningElement {
    @api maxRows = 25;
    // showTotals never declared — the knob renders and the value goes nowhere
    showTotals = true;
}
```

**Why it happens:** The two files are generated in separate turns, and nothing at deploy time cross-checks them. The component still deploys, the property still renders in the panel, and the admin's setting is silently discarded.

**Correct pattern:** one `@api` field per `property name`. "The component author defines the property in the component's JavaScript class using the `@api` decorator" and the `name` value "must match the property name in the component's JavaScript class" (L18968, L18971).

```javascript
@api maxRows = 25;
@api showTotals = true;
```

**Detection hint:** a `property name` in the meta file with no `@api <name>` — or `@api get <name>()` — in the bundle's `.js`. The reverse (an extra `@api` with no meta entry) is legitimate: `recordId`, `objectApiName`, `flexipageRegionWidth` and composition seams are all declared in JS only.

---

## Anti-Pattern 7: Assuming a record-page bundle behaves the same way on an Experience Cloud page

**What the LLM generates:**

```javascript
import { LightningElement, api, wire } from 'lwc';
import { getRecord } from 'lightning/uiRecordApi';

export default class PipelineSummary extends LightningElement {
    @api recordId;

    // Assumes recordId is always populated because the meta file lists
    // lightningCommunity__Default alongside lightning__RecordPage.
    @wire(getRecord, { recordId: '$recordId', fields: ['Case.Subject'] })
    record;
}
```

**Why it happens:** Adding `lightningCommunity__Default` to `<targets>` looks like it extends the same behaviour to a new surface. It extends the *placement*, not the context injection.

**Correct pattern:** guard on the value and document the admin step. Experience Builder sites do not automatically bind `recordId` — an admin enters `{!recordId}` in the component's Record ID property field (`use-record-context` L7894, L7900); the same holds for `objectApiName` (`use-object-context` L7914). And on any surface, `recordId` is set only in an explicit record context, so the component cannot depend on it (L7893).

```javascript
get hasContext() {
    return Boolean(this.recordId && this.objectApiName);
}
```

**Detection hint:** a `@wire` or `connectedCallback` that dereferences `recordId` without a guard in a bundle whose `<targets>` include a non-record surface.

---

## Anti-Pattern 8: Treating an irreversible change as a routine edit

**What the LLM generates:**

A confident "just remove `Small` from the supported form factors" or "drop `<object>Lead</object>` and redeploy" for a component that is already placed on pages.

**Why it happens:** The meta file is small and text-shaped, so every edit looks equally cheap. The platform disagrees for a specific list of edits.

**Correct pattern:** name the constraint before proposing the edit. Once a component is in use on a Lightning page you can only *increase* the supported form factors (`use-config-for-app-builder-tips` L9909, `use-config-form-factors` L9806); you cannot remove object tags for an object whose record page uses the component (L9905), remove page-type support that is in use (L9906), or change `min`/`max` (L9907). In a site or managed package the property rules are stricter still (`use-config-for-community-builder` L8128–L8137), and in a released managed package `isExposed` moves only from `false` to `true` (`use-packaging-add` L7812).

**Detection hint:** any proposed diff that removes a `<target>`, removes an `<object>`, removes a `<supportedFormFactor>`, adds `required="true"`, or tightens `min`/`max` — without a sentence about whether the component is already in use.
