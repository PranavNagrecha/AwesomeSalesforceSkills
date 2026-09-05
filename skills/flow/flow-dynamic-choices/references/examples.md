# Examples — Flow Dynamic Choices

Narrative walk-throughs. The complete deployable flow lives in `references/metadata-examples.md`;
the fragments here are the shapes those examples turn on.

## Example 1: Active Account picker

**Context:** Case creation flow

**Problem:** Hard-coded account names

**Solution:**

Record Choice Set: Account WHERE IsActive__c=true LIMIT 50 ORDER BY Name

**Why it works:** Always current

**The `limit` is not optional decoration.** `FlowDynamicChoiceSet.limit` is documented "Maximum
**and default**: 200" (`api_meta.txt` L70319–L70321) — leaving it out sets 200, it does not remove
the ceiling. And `sortField` + `sortOrder` matter for the same reason: "the records are sorted
before the limit takes effect" (L70321–L70322), so an unsorted `limit` gives an arbitrary 50, not
the first 50 by name.


---

## Example 2: Country → State dependent

**Context:** Address capture

**Problem:** All states shown regardless of country

**Solution:**

Two Record Choice Sets; State_Choice filtered by {!SelectedCountry}

**Why it works:** Reactive filter on selection

The dependency is a single `filters` entry whose `value` is an `elementReference` rather than a
literal — `FlowRecordFilter.value` is a `FlowElementReferenceOrValue` (`api_meta.txt` L71069–L71090),
so it can name the earlier screen field directly:

```xml
<dynamicChoiceSets>
    <name>State_Choices</name>
    <dataType>String</dataType>
    <displayField>Name</displayField>
    <filters>
        <field>Country__c</field>
        <operator>EqualTo</operator>
        <value>
            <elementReference>Select_Country</elementReference>
        </value>
    </filters>
    <limit>60</limit>
    <object>State_Region__c</object>
    <outputAssignments>
        <assignToReference>varStateCode</assignToReference>
        <field>ISO_Code__c</field>
    </outputAssignments>
    <sortField>Name</sortField>
    <sortOrder>Asc</sortOrder>
    <valueField>Id</valueField>
</dynamicChoiceSets>
```

`Select_Country` is the *name of the screen field* on the earlier screen, not a variable. If the two
choice sets sit on the **same** screen, the second one does not re-evaluate on selection unless the
component is reactive — put them on separate screens, or move to a reactive component
(`flow/flow-reactive-screen-components`).

Two things this shape cannot do: combine the country filter with an OR clause (there is no
`filterLogic` on this type — see `references/gotchas.md` Gotcha 5), and survive a Back-then-Forward
navigation cleanly (Gotcha 3).


---

## Example 3: Icon tile picker

**Context:** Case-reason selection on a support screen flow

**Problem:** A plain dropdown of reason codes is slow to scan and gives no visual cue.

**Solution:**

Create a set of standalone **Choice** resources (text data type) — one per reason code — and attach an SLDS icon to each, then place a **Visual Picker** screen input component on the screen and point it at those choices. At run time each choice renders as an icon-and-text tile the user taps instead of opening a dropdown. Visual Picker is a standard component (Summer '25), so no custom LWC is needed. The Visual Picker is configured using standalone Choice resources and doesn't support Record Choice Sets or Picklist Choice Sets, so if the reason codes come from a picklist field or a query, map them into standalone Choice resources first.

**Why it works:** Icon-tagged choices render as tiles; users pick faster from visual cues without leaving Flow Builder for a custom component.

**In metadata**, the icon is `FlowChoice.choiceIcon`, a `FlowIcon` whose only field is `iconName` —
"the name of the selected Salesforce Lightning Design System icon" — available in API version 64.0
and later (`api_meta.txt` L69880–L69882, L70631–L70637). `UNVERIFIED (2026-09-05)`: "Visual Picker"
is a Flow Builder / help.salesforce.com name and is not a `FlowScreenFieldType` value
(L71677–L71713), so the component is a `ComponentInstance` field in the XML — which is also why it
takes `inputParameters` rather than `choiceReferences`.


---

## Example 4: Searchable record picker (Choice Lookup)

**Context:** Service screen flow where an agent picks the right Contact on an Account that has thousands of them.

**Problem:** A dropdown or radio list of thousands of contacts is unusable, and a plain Lookup component lets the agent search *any* record with no guardrails.

**Solution:**

Build a **filtered Record Choice Set** (or a filtered Collection Choice Set) that narrows Contacts to the selected Account, then place a **Choice Lookup** screen input component pointed at it. The user types to filter and the component returns a typeahead list. Leave it single-select for one Contact, or set **Let Users Select Multiple Options = Yes** to allow up to 25 selections — and, for multi-select, store the output in a collection variable. Choice Lookup accepts any Choice resource (Record, Collection, or Picklist Choice Set), so the same component also works for long picklist-backed lists.

**Why it works:** Search/typeahead scales past the point where dropdowns and radio lists fail, while the filtered Choice resource keeps the selectable set constrained — unlike the standard Lookup, which surfaces recent and global-search records with no author-defined filter.

**Load-behavior note:** Choice Lookup displays 20 options first, then loads 100 more each time the user scrolls, up to 1,020 displayed, and resets to 20 when a filter is reapplied. Keep the underlying Choice resource filtered enough that the target is reachable rather than relying on the scroll cap. `UNVERIFIED (2026-09-05)`: those load numbers are help.salesforce.com claims. The grounded ceiling that caps the whole problem is `limit`'s "Maximum and default: 200" on a single `FlowDynamicChoiceSet` (`api_meta.txt` L70319–L70321) — a 1,020-option list cannot come from one choice set.


---

## Example 5: Multi-select checkboxes, and what the flow actually receives

**Context:** An enrolment screen collecting accessibility accommodations.

**Problem:** The author expects a collection of selected values and writes downstream logic against
one. The flow receives a single string.

**Solution:**

`MultiSelectCheckboxes` "stores its field value as a concatenation of the user-selected choice
values, separated by semicolons. Any semicolons in the selected choice values are removed when added
to the multi-select field value" (`api_meta.txt` L71714–L71720). So a user selecting all three
choices leaves the flow holding one `String`:

| What the user checked | What `{!Select_Accommodations}` holds |
|---|---|
| Sign-language interpreter | `Interpreter` |
| Interpreter + step-free | `Interpreter;Step Free` |
| all three | `Interpreter;Step Free;Large Print` |
| a choice whose value was `Level 1; advanced` | `Level 1 advanced` — the semicolon is stripped |

Test membership rather than iterating:

```xml
<formulas>
    <name>fxNeedsInterpreter</name>
    <dataType>Boolean</dataType>
    <expression>CONTAINS({!Select_Accommodations}, &quot;Interpreter&quot;)</expression>
</formulas>
```

**Why it works:** It matches what the platform stores instead of what the author wanted it to store.
There is no split — `FlowAssignmentOperator`'s fifteen values contain nothing that decomposes a
string (L69767–L69865), and `FlowFormula` returns one scalar (L70596–L70612). Building a real text
collection costs one Decision plus one `Add` Assignment per value; `references/metadata-examples.md`
§3 shows both routes and the Metadata-API-only trap on the shortcut.


---

## Example 6: Reaching for a collection choice set instead of a second query

**Context:** A screen needs choices that a Get Records already fetched for a different reason — an
empty-state check, a count, a related-list display.

**Problem:** A second record choice set re-queries the same rows when the screen renders.

**Solution:**

Point a choice set at the collection with `collectionReference` — "the collection that's used to
generate choices", available in API version 54.0 and later (`api_meta.txt` L70278–L70280) — instead
of giving it its own `object` + `filters`:

```xml
<dynamicChoiceSets>
    <name>Region_Choices</name>
    <collectionReference>varEligibleRegions</collectionReference>
    <dataType>String</dataType>
    <displayField>Region_Name__c</displayField>
    <valueField>Region_Code__c</valueField>
</dynamicChoiceSets>
```

`varEligibleRegions` is the record collection a Get Records already filled — and note `valueField`
here is a business key (`Region_Code__c`), not `Id`, because "the stored value for the choice … can
differ from what is displayed to the user" (L70383–L70389).

**Why it works:** The Get Records is a `FlowNode` with a `faultConnector` (L71120) and a `connector`,
so the zero-row case gets a Decision and a routed failure — neither of which a record choice set can
have. The choice set then renders from memory. `UNVERIFIED (2026-09-05)`: the guide documents
`collectionReference` and the `Record` `dataType` (API 54.0+) but never states which of `dataType` /
`displayField` / `valueField` a *collection* choice set requires; the field table qualifies them only
as "Required for record choices". Retrieve after the first save in Flow Builder and diff.

This is also the escape hatch for OR logic: `FlowRecordLookup` has `filterLogic`
(L71124–L71131) and `FlowDynamicChoiceSet` does not.
