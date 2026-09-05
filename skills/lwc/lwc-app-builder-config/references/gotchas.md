# Gotchas — LWC App Builder Config

Non-obvious `js-meta.xml` behaviours that cause real production support tickets. Line citations point at the crawled Lightning Web Components Developer Guide (`lwc_guide <page-slug> L<n>`) and the Apex Reference Guide (`apexrefguide L<n>`).

---

## 1. The form-factor child tag is `supportedFormFactor`, and its attribute is `type`

**What happens:** A meta file written as `<supported formFactor="Small"/>` — an easy analogy from `<supported…>`-shaped XML elsewhere — does not declare a form factor. The bundle either fails to deploy against the metadata schema or deploys with no form-factor declaration at all, and the component then inherits whatever the page type supports.

**When it occurs:** Any time the element is written from memory rather than from the reference. The plural wrapper `<supportedFormFactors>` is right; the child is the singular `<supportedFormFactor>` and it carries a required `type` attribute whose valid values are `Large` (desktop) and `Small` (phone).

**How to avoid:** Write `<supportedFormFactors><supportedFormFactor type="Large"/></supportedFormFactors>`, always inside a `targetConfig`. Grounded at `lwc_guide targets-lightning-app-page` L18993–L18999 and repeated per target at `targets-lightning-home-page` L19209–L19215, `targets-lightning-record-page` L19369–L19375, `targets-lightning-inbox` L19258–L19264.

---

## 2. `Color` is not a documented App Builder property type

**What happens:** A `<property type="Color">` inside a `lightning__RecordPage`, `lightning__AppPage` or `lightning__HomePage` `targetConfig` is outside the documented type set for those targets. The guide's per-target attribute tables for App Builder surfaces list exactly three: `Boolean`, `Integer`, `String`.

**When it occurs:** Most often when a snippet is lifted from an Experience Cloud example, where `Color` really is supported and renders a colour selector. The same paste into a record-page block is a different contract.

**How to avoid:** Treat the type set as per-target, not global. `Color` is documented for `lightningCommunity__Default` (L18775–L18778) and for `lightningStatic__Email` alongside `HorizontalAlignment` and `VerticalAlignment` (L18870–L18876). App Builder targets: L18972–L18975 (App Page), L19197–L19199 (Home Page), L19351–L19353 (Record Page), L19246–L19248 (Inbox), L19428–L19430 (Utility Bar). Separately, Lightning App Builder does not support the `Map`, `Object`, or `java://` complex types (`use-config-for-app-builder-tips` L9908).

---

## 3. Omitting `<objects>` is not a neutral default

**What happens:** A record-page `targetConfig` with no `<objects>` block does not mean "no restriction pending a decision" — it means the component supports every object the Lightning platform supports for record pages. Admins can drop an Account-shaped component onto Lead, Case, or a custom object, where it either errors or shows misleading data.

**When it occurs:** On the first deploy of any record-page component, because omission is the path of least resistance and nothing complains.

**How to avoid:** Name the objects. The guide is explicit: "Limits the component to a set of one or more objects. If you don't use this tag set, the component supports all supported objects" (`targets-lightning-record-page` L19363). Note also that the `<object>` tag does not support external objects (L19367), and the tag set may be specified only once per `targetConfig` (L19364).

---

## 4. `<objects>` outside a record-page `targetConfig` scopes nothing

**What happens:** Adding `<objects>` inside a `lightning__AppPage` or `lightning__HomePage` block has no effect. The component remains available on every app page and home page, and the author believes it is scoped.

**When it occurs:** When one `targetConfig` is copy-pasted to seed another, or when a `targetConfig targets="lightning__RecordPage,lightning__AppPage"` merges two surfaces into one block — the objects list then applies only to the record-page half.

**How to avoid:** The guide states the tag set "works only inside a parent `targetConfig` that's configured for `lightning__RecordPage`" (L19363). Give the record page its own `targetConfig` when it needs object scoping.

---

## 5. Once the component is placed, four things freeze

**What happens:** A change that is legal on day one is refused on day two. You cannot remove an `<object>` tag while the component is in use on a record page for that object; you cannot remove page-type support while it is in use on that page type; you cannot change `min` or `max` while it is in use on a Lightning page; and you can only ever *increase* the supported form factors, never decrease them.

**When it occurs:** The first time someone tries to narrow an over-broad initial configuration — exactly the correction that an unscoped first deploy invites.

**How to avoid:** Get the scope right before the component reaches an admin, and treat widening as the only cheap direction. Grounded at `use-config-for-app-builder-tips` L9904–L9909, with the form-factor rule repeated at `use-config-form-factors` L9806.

---

## 6. Experience Cloud sites and managed packages apply a stricter, different set of freezes

**What happens:** In a site or managed package the rules are property-level and tighter than App Builder's. You cannot add a new `<property>` with `required=true`; you cannot remove an existing `<property>`; you cannot flip an existing property to `required=true`; you cannot remove a `default` from a property that is `required=true` and has one; you cannot add a `min` or `max` where none existed, raise an existing `min`, or lower an existing `max`.

**When it occurs:** On the second release of any packaged component, and on any component already dropped onto a page in a published site.

**How to avoid:** Land the property contract before the first package version or the first site placement. If the component is used in a site but *not* in a managed package there is an escape hatch: remove the component from the site, make the change, redeploy, and add it back. Grounded at `use-config-for-community-builder` L8126–L8139.

---

## 7. `isExposed` is a one-way door inside a released package

**What happens:** After a managed package is released, `isExposed` can change only from `false` to `true` — never back. Worse, once it is `true` in a published package, the developer can no longer remove a configuration target or a public `@api` property from the component, and that restriction applies even to targets and properties added after the most recent publication.

**When it occurs:** When a component is exposed "just to test it in App Builder" in a package that then ships.

**How to avoid:** Expose deliberately. Grounded at `use-packaging-add` L7809–L7818. The same page notes that after release the developer can still edit `apiVersion`, `description`, `masterLabel`, `targetConfigs` and `targets` (L7810–L7815) — "edit" within the constraints above, not "remove".

---

## 8. Experience Builder does not auto-bind `recordId` or `objectApiName`

**What happens:** The same bundle that receives a record ID automatically on a Lightning record page receives nothing on an Experience Cloud page. The component renders, the guard clause fires, and the page looks broken for reasons that are invisible in the meta file.

**When it occurs:** Whenever a record-page component is reused on a community page, which is precisely what a multi-target bundle invites.

**How to avoid:** The admin must enter `{!recordId}` in the component's Record ID property field in Experience Builder; the framework then resolves it to the 18-character ID (`use-record-context` L7894–L7902; the same is true of `objectApiName`, `use-object-context` L7914–L7916). Document that step in the component's `description`, and never let the component throw when the value is absent — `recordId` is set only in an explicit record context and cannot be depended on anywhere else (L7893).

---

## 9. `lightning__Tab` and `lightning__RecordAction` accept far less than the other targets

**What happens:** Design attributes and form factors written for a Tab target are silently pointless: the `lightning__Tab` target supports neither the `property` nor the `supportedFormFactor` tags. `lightning__RecordAction` supports form factors but no component properties at all, and its `Small` value is explicitly unsupported because LWC quick actions do not appear in the Salesforce mobile app.

**When it occurs:** When a multi-target bundle adds Tab or RecordAction to `<targets>` and reuses the App Page `targetConfig` for them.

**How to avoid:** Check the per-target table before writing a `targetConfig`. Grounded at `use-config-custom-tab` L7987 and `targets-lightning-record-action` L19307, L19311–L19313. `actionType` is also a one-way door: it cannot change between `Action` and `ScreenAction` after deploy (L19323). Component design for quick actions belongs to `lwc/lwc-quick-actions`.

---

## 10. A dynamic picklist shows only its first 200 values, and type-ahead may search only those

**What happens:** An `apex://` datasource over a wide object returns a long list; the property panel displays the first 200. If the `DynamicPickListRows` was built without `containsAllRows` set to true, a type-ahead search in the panel searches only those first 200 displayed values, not the complete set — so an admin typing the exact API name of the 300th field gets no result.

**When it occurs:** On objects with many fields, or on a datasource that enumerates records rather than schema.

**How to avoid:** Filter server-side so the list is genuinely short, and call `setContainsAllRows(true)` (or use the `DynamicPickListRows(rows, containsAllRows)` constructor) when it is not. Grounded at `apexrefguide` L248019–L248025.

---

## 11. `default` is a builder-side value, not a JavaScript initializer

**What happens:** `<property type="Integer" default="10"/>` sets what App Builder pre-fills in the property panel. It is not a runtime guarantee: a Jest test instantiates the class directly and never sees it, and any code path that constructs the component outside a builder placement sees only the JS field initializer.

**When it occurs:** Whenever the meta file's default and the JS initializer drift apart, which no tool catches — Jest tests are local and run independently of Salesforce (`unit-testing-using-jest-create-tests` L12326).

**How to avoid:** Initialize every design attribute in the JS class to the same value the meta file declares, and pin the JS side with a Jest test. Two related rules make this cheap: give required properties a default, because a required property with no default makes the component show as invalid the moment it is added in App Builder (`use-config-for-app-builder-tips` L9899); and when the JS type and the config type disagree, the configuration file's type takes precedence (L18972, `use-config-for-app-builder` L9840, L9901). UNVERIFIED (2026-09-05): the guide does not document the JavaScript runtime type of a design-attribute value delivered from App Builder, so coerce at the setter rather than assuming either a string or a number.

---

## 12. `targets` and `targetConfigs` are separate lists, and the mismatch is silent in one direction

**What happens:** A `targetConfig` whose `targets` attribute names a page type that is absent from `<targets>` configures nothing. In the other direction, a target with no `targetConfig` still enumerates the surface — it simply offers no admin-configurable properties there.

**When it occurs:** After a surface is dropped from `<targets>` and its `targetConfig` is left behind, or after a new target is added and no one adds the matching block.

**How to avoid:** The guide requires that "the `targets` attribute value must match one or more of the page types that you listed under `<targets>`" (L18769, L18966, L19103). Keep the two lists in sync mechanically — `scripts/check_lwc_app_builder_config.py` reports both directions. UNVERIFIED (2026-09-05): the guide does not state what the builder does with a `targetConfig` naming an undeclared target; treat it as unconfigured rather than as an error.

---

## 13. The event schema for Dynamic Interactions is never checked against the JavaScript

**What happens:** An `<event>` block on a `lightning__AppPage` `targetConfig` advertises an event and its payload shape to admins. The event tag metadata is not validated against the `.js` file, so a component can offer an event it never fires, or a payload key it never sets, and App Builder will happily let an admin wire an interaction to it.

**When it occurs:** After a refactor renames the `CustomEvent` or changes its `detail` keys without touching the meta file.

**How to avoid:** Treat the schema as a published contract with a test behind it. Only `type` and `properties` are read from the schema, only `type`/`title`/`description` are supported property attributes, and the only valid property types in the schema are String, Integer, and Boolean (`use-config-for-app-builder-dynamic-interactions` L9878–L9881). Payload design belongs to `lwc/component-communication`.

---

## 14. `masterLabel` and `description` are user-facing in two different places

**What happens:** `description` is not a code comment. It appears in list views such as the Lightning Components list in Setup, and as a tooltip in App Builder and Experience Builder. `masterLabel` is the component's title in those same lists and builders. A blank or engineer-facing value is what admins read while deciding whether to place the component.

**When it occurs:** On any bundle scaffolded and then extended without revisiting the two header tags.

**How to avoid:** Write both for an admin audience, and use property-level `description` for the per-knob i-bubble. Grounded at `reference-configuration-tags` L18710 (`description`) and L18714 (`masterLabel`); the tips page adds that property descriptions should explain expected data, format, and range (`use-config-for-app-builder-tips` L9894–L9898). UNVERIFIED (2026-09-05): the guide does not document whether `masterLabel` resolves a Custom Label reference such as `{!$Label.c.MyLabel}`; earlier revisions of this skill asserted it does not. Treat the literal string as the safe assumption and verify in a scratch org before promising localization.
