# LLM Anti-Patterns — LWC App Builder Config

Common mistakes AI coding assistants make when generating or advising on LWC js-meta.xml files. These help the consuming agent self-check its own output.

## Anti-Pattern 1: Setting `isExposed=false` (or omitting it) and then expecting the component to appear

**What the LLM generates:**

```xml
<LightningComponentBundle xmlns="http://soap.sforce.com/2006/04/metadata">
  <apiVersion>62.0</apiVersion>
  <isExposed>false</isExposed>
  <targets>
    <target>lightning__RecordPage</target>
  </targets>
</LightningComponentBundle>
```

**Why it happens:** The default scaffold from `sfdx force:lightning:component:create` emits `<isExposed>false</isExposed>`. LLMs often copy the scaffold verbatim and append `<targets>` without flipping the boolean.

**Correct pattern:**

```xml
<isExposed>true</isExposed>
```

**Detection hint:** If `<targets>` is non-empty and `<isExposed>` is `false` or missing, flag it.

---

## Anti-Pattern 2: Listing `<targets>` but omitting `<targetConfigs>` when per-target design attributes are needed

**What the LLM generates:**

```xml
<targets>
  <target>lightning__RecordPage</target>
  <target>lightning__AppPage</target>
</targets>
<!-- no targetConfigs -->
```

...while separately telling the user "admins can configure a title and an object filter in App Builder."

**Why it happens:** The LLM conflates "exposed to a target" with "configurable on a target." Without a `<targetConfig>`, admins see the component but no properties.

**Correct pattern:** Wrap each target that needs configuration in a `<targetConfig targets="…">` block with `<property>` children.

**Detection hint:** Description mentions admin-configurable knobs but `<targetConfigs>` is missing or empty.

---

## Anti-Pattern 3: Putting `<supportedFormFactors>` at the root of the bundle

**What the LLM generates:**

```xml
<LightningComponentBundle ...>
  <isExposed>true</isExposed>
  <supportedFormFactors>
    <supported formFactor="Small"/>
  </supportedFormFactors>
  <targets>
    <target>lightning__AppPage</target>
  </targets>
</LightningComponentBundle>
```

**Why it happens:** `<supportedFormFactors>` reads like a bundle-level setting. LLMs place it next to `<isExposed>` by analogy.

**Correct pattern:** Place it inside the relevant `<targetConfig>`:

```xml
<targetConfig targets="lightning__AppPage">
  <supportedFormFactors>
    <supported formFactor="Small"/>
  </supportedFormFactors>
</targetConfig>
```

**Detection hint:** `<supportedFormFactors>` appears as a child of `<LightningComponentBundle>` instead of `<targetConfig>`.

---

## Anti-Pattern 4: Using `type="Picklist"` for a design attribute

**What the LLM generates:**

```xml
<property name="severity" type="Picklist" label="Severity">
  <option>low</option>
  <option>medium</option>
  <option>high</option>
</property>
```

**Why it happens:** "Picklist" is a core Salesforce concept, so LLMs assume the design-attribute layer has a matching type. It does not — valid types are `String`, `Integer`, `Boolean`, `Color` (plus a handful of community-specific types such as `ContentReference`).

**Correct pattern:**

```xml
<property name="severity" type="String" label="Severity"
          datasource="low,medium,high" default="medium"/>
```

or, for a dynamic list:

```xml
<property name="severity" type="String" label="Severity"
          datasource="apex://SeverityPickList"/>
```

**Detection hint:** `type="Picklist"`, `type="Reference"`, or `type="sObject"` anywhere in a non-community `<property>`.

---

## Anti-Pattern 5: Trusting a `default` string as its declared type on read

**What the LLM generates:**

Meta:
```xml
<property name="maxRows" type="Integer" default="25" label="Max Rows"/>
```

JS:
```javascript
@api maxRows;
get rowsToShow() {
    return this.records.slice(0, this.maxRows); // maxRows is "25" (string)
}
```

**Why it happens:** LLMs assume `type="Integer"` means the JS property is a JavaScript `Number`. In practice App Builder hands design-attribute values to LWC as strings; `slice(0, "25")` happens to work, but `this.maxRows + 1 === "251"` does not.

**Correct pattern:**

```javascript
@api maxRows;
get rowsToShow() {
    const n = Number(this.maxRows) || 0;
    return this.records.slice(0, n);
}
```

**Detection hint:** A `@api` property bound to a numeric design attribute is used in arithmetic or strict-equality comparisons without a `Number(...)` / `parseInt(...)` cast.
