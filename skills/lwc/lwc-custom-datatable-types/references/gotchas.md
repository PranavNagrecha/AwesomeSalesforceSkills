# Gotchas — LWC Custom Datatable Types

Non-obvious platform behaviors that cause real production problems when extending `lightning-datatable`.

## Gotcha 1: Templates Have No `this` And No Lifecycle Hooks

**What happens:** Developers port patterns from regular LWC components into a custom cell template — `this.recordId`, `connectedCallback`, `@wire` on the template, imperative handlers. None of it runs. The template renders whatever static markup is left once the broken expressions silently evaluate to `undefined`.

**When it occurs:** Anytime the author treats the `.html` file as a full LWC module instead of a fragment. Especially common when generating the template from an existing component.

**How to avoid:** Treat the template as pure data binding over `{value, typeAttributes, editable, context, keyField}`. If interactive state is required, render a child LWC from the template and put the logic there.

---

## Gotcha 2: `typeAttributes` Names Must Be Declared Or The Datatable Drops Them

**What happens:** The host column binds `typeAttributes: { iconName: { fieldName: 'iconName' } }`, the template reads `{typeAttributes.iconName}`, and the cell renders without the icon. No console warning, no error.

**When it occurs:** When a key is not present in the subclass's `customTypes.<type>.typeAttributes` array. The datatable strips unknown attributes as a safety measure.

**How to avoid:** Every key the template reads must appear in the `typeAttributes` array. When the checker script flags a binding in use with no matching array entry, fix the array first.

---

## Gotcha 3: Sorting Compares `value`, Not The Rendered DOM

**What happens:** A status pill column looks correct visually, but sorting scrambles the order or treats rows as equal.

**When it occurs:** When `value` is not a comparable scalar (e.g., the row stores the color/label objects in the column's bound field). The default sort comparator operates on the primitive `value`.

**How to avoid:** Keep `value` as the scalar you want to sort by (a numeric priority, an ISO status string). Put the display-only attributes (variant, icon, label) in `typeAttributes`. If the sort needs a different key than `value`, configure `sortBy` on the column.

---

## Gotcha 4: `editTemplate` Must Bind `value` For `draft-values` To Fire

**What happens:** The cell enters edit mode, the user changes the combobox, clicks outside, and the Save button never lights up.

**When it occurs:** When the `editTemplate`'s input control is bound to something other than `value` (for example, a local proxy, or `selected-value`). The datatable's save harness reads the edit control's `value` property to build the draft.

**How to avoid:** Wire the editable control's `value={value}` directly, and let the datatable's wrapper capture changes. If a computed value is required, compute on the host via `onsave`, not inside the template.

---

## Gotcha 5: Base Datatable CSS Overrides Are Brittle

**What happens:** A targeted style override on `.slds-table` or internal datatable shadow structure works in one release and breaks in the next.

**When it occurs:** When consumers use `:host` style hacks or `::part` on non-exposed parts to restyle the grid. Salesforce does not guarantee internal DOM stability across releases.

**How to avoid:** Prefer SLDS Styling Hooks (`--slds-c-*` CSS custom properties) where exposed. For cell-level look and feel, put the styling on the custom template itself, not on the datatable shell.

---

## Gotcha 6: Custom Types Are Per-Subclass

**What happens:** A team imports two independent datatable extensions (one from a managed package, one home-grown) and expects to use custom types from both in the same grid. Only one subclass can be instantiated per datatable, so only that subclass's types are available.

**When it occurs:** Anytime two sources of custom types need to coexist on a single grid.

**How to avoid:** Build one merged subclass that registers all required `customTypes`. Document the merged subclass in the project so future consumers know to extend it rather than creating parallel subclasses.

---

## Gotcha 7: Large `typeAttributes` Objects Cause Per-Cell Rerender Thrash

**What happens:** Every scroll, every edit, every data refresh feels heavier than it should, and Lightning Inspector shows the custom cell template rerendering rows that did not change.

**When it occurs:** When `typeAttributes` is populated with a large object (a full record, a deep options array shared by reference but re-created each parent render).

**How to avoid:** Keep `typeAttributes` values flat and primitive where possible. Memoize shared arrays (picklist options) on the host so the reference does not change on every render. Move heavy interactive logic into a child LWC that owns its own reactivity boundary.
