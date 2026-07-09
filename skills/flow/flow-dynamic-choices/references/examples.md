# Examples — Flow Dynamic Choices

## Example 1: Active Account picker

**Context:** Case creation flow

**Problem:** Hard-coded account names

**Solution:**

Record Choice Set: Account WHERE IsActive__c=true LIMIT 50 ORDER BY Name

**Why it works:** Always current


---

## Example 2: Country → State dependent

**Context:** Address capture

**Problem:** All states shown regardless of country

**Solution:**

Two Record Choice Sets; State_Choice filtered by {!SelectedCountry}

**Why it works:** Reactive filter on selection


---

## Example 3: Icon tile picker

**Context:** Case-reason selection on a support screen flow

**Problem:** A plain dropdown of reason codes is slow to scan and gives no visual cue.

**Solution:**

Create a set of standalone **Choice** resources (text data type) — one per reason code — and attach an SLDS icon to each, then place a **Visual Picker** screen input component on the screen and point it at those choices. At run time each choice renders as an icon-and-text tile the user taps instead of opening a dropdown. Visual Picker is a standard component (Summer '25), so no custom LWC is needed. The Visual Picker is configured using standalone Choice resources and doesn't support Record Choice Sets or Picklist Choice Sets, so if the reason codes come from a picklist field or a query, map them into standalone Choice resources first.

**Why it works:** Icon-tagged choices render as tiles; users pick faster from visual cues without leaving Flow Builder for a custom component.


---

## Example 4: Searchable record picker (Choice Lookup)

**Context:** Service screen flow where an agent picks the right Contact on an Account that has thousands of them.

**Problem:** A dropdown or radio list of thousands of contacts is unusable, and a plain Lookup component lets the agent search *any* record with no guardrails.

**Solution:**

Build a **filtered Record Choice Set** (or a filtered Collection Choice Set) that narrows Contacts to the selected Account, then place a **Choice Lookup** screen input component pointed at it. The user types to filter and the component returns a typeahead list. Leave it single-select for one Contact, or set **Let Users Select Multiple Options = Yes** to allow up to 25 selections — and, for multi-select, store the output in a collection variable. Choice Lookup accepts any Choice resource (Record, Collection, or Picklist Choice Set), so the same component also works for long picklist-backed lists.

**Why it works:** Search/typeahead scales past the point where dropdowns and radio lists fail, while the filtered Choice resource keeps the selectable set constrained — unlike the standard Lookup, which surfaces recent and global-search records with no author-defined filter.

**Load-behavior note:** Choice Lookup displays 20 options first, then loads 100 more each time the user scrolls, up to 1,020 displayed, and resets to 20 when a filter is reapplied. Keep the underlying Choice resource filtered enough that the target is reachable rather than relying on the scroll cap.

