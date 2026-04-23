# Gotchas — LWC App Builder Config

Non-obvious meta.xml behaviors that cause real production support tickets.

1. **`isExposed=false` hides the component silently.** No deploy error, no lint warning — the bundle just never appears in App Builder, Experience Builder, Utility Bar, or Flow. Admins file a ticket saying the component is "missing," and the root cause is one boolean in the meta.xml.

2. **`targets` without matching `targetConfigs` is legal, but asymmetric.** Any target listed in `<targets>` shows up in the builder even if it has no `<targetConfig>` — the component simply offers no admin-configurable properties on that surface. The moment you need surface-specific design attributes, form factors, or object scoping, you must add a full `<targetConfig targets="…">` block for each target that needs config. Forgetting one surface means admins get zero knobs there.

3. **`<supportedFormFactors>` only works inside a `<targetConfig>`.** Putting it at the root of the meta.xml (as a sibling of `<targets>`) has no effect — the builder silently ignores it. To restrict a target to phone only, the element must live inside the `<targetConfig targets="lightning__AppPage">` (or equivalent) block.

4. **`<objects>` applies only to record-page targets.** Adding `<objects>` inside a `<targetConfig>` for `lightning__AppPage` or `lightning__HomePage` is meaningless — those surfaces are not scoped to a record. The element restricts where record-page admins can drop the component; everywhere else it is a no-op.

5. **`<masterLabel>` cannot be translated with Custom Labels.** Even if you write `{!$Label.c.MyLabel}`, it will not resolve — `masterLabel` takes a literal string. Use Translation Workbench (Setup → Translation Workbench → Translate) to localize the builder-side label. The same applies to `<description>`.

6. **Design-attribute `default` values always arrive as strings in JS.** A property declared `<property type="Integer" default="5"/>` hands `"5"` (a string) to the component. Cast on read (`Number(this.maxRows)` or `parseInt(...)`); comparing `this.maxRows === 5` will be false.

7. **Changing `targetConfigs` can break existing placements.** Adding a `required="true"` property, renaming a property, or changing a property `type` on a component already placed on many pages can force admins to re-open and re-save each page — and in some cases the old placement is marked invalid in Lightning App Builder until it is re-configured. Treat `targetConfigs` as a versioned public API for admins.

8. **Invalid `type` values on `<property>` cause cryptic deploy failures.** `Picklist`, `Reference`, or `sObject` are not valid design-attribute types outside specific community contexts. The deploy error is often a generic XML-schema complaint rather than a clear "type X is not supported," so the fix is easy to miss. Stick to `String`, `Integer`, `Boolean`, `Color`, and community-specific types like `ContentReference` only inside `lightningCommunity__*` targets.
