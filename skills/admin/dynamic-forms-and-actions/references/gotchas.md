# Gotchas — Dynamic Forms and Dynamic Actions

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Fields Disappear When Dynamic Forms Is Enabled Without the Upgrade Wizard

**What happens:** When a practitioner removes the monolithic "Fields" component from a Lightning record page and saves (which is the effect of enabling Dynamic Forms without migrating), all fields that were controlled by the page layout disappear from the record page for every user assigned to that page.

**When it occurs:** Any time a Lightning record page transitions from a page-layout-backed "Fields" component to Dynamic Forms without first running the "Upgrade Now" migration wizard. The wizard is accessible via the Page Properties panel in Lightning App Builder when a "Fields" section component is selected.

**How to avoid:** Always use the "Upgrade Now" wizard before removing the page layout "Fields" component. The wizard reads the currently assigned page layout and scaffolds individual field components on the page canvas. Test in a sandbox before activating in production. If the issue has already occurred in production, re-add the "Fields" component temporarily, re-activate the page, and then run the proper migration.

---

## Gotcha 2: Dynamic Forms Visibility Filters Are Not a Security Control

**What happens:** A field hidden via a Dynamic Forms visibility filter is not visible on the Lightning UI, but it remains accessible via the REST API, SOQL queries, reports, and list views — provided the user has FLS read access. Some practitioners configure Dynamic Forms filters instead of FLS to "hide" sensitive data, leaving it unintentionally exposed.

**When it occurs:** Whenever an admin uses Dynamic Forms visibility rules to restrict access to sensitive fields (e.g., salary, social security number, confidential notes) without also setting appropriate FLS restrictions. This is a data governance risk.

**How to avoid:** Field-Level Security (FLS) is the authoritative access control for field data. This is the same failure page layouts have — `admin/record-types-and-page-layouts` gotcha 5 ("Page Layouts Are Not Security Controls") documents the layout side and is worth reading once; moving from a layout to a Dynamic Form does not change the conclusion, it just moves where the cosmetic hiding is configured. Dynamic Forms filters control rendering only. For any field that must be restricted from certain users, set FLS to "Read Only: No" or "Edit: No" for the relevant profiles/permission sets. Dynamic Forms filters can then additionally refine the UI experience, but FLS should be the primary control.

---

## Gotcha 3: Standard Objects Have Limited Dynamic Forms Support

**What happens:** Dynamic Forms is not available for all standard objects. If you open Lightning App Builder for a standard object that is not supported, the "Upgrade Now" option does not appear, and field components cannot be individually placed. Practitioners sometimes spend significant time trying to enable Dynamic Forms before discovering the object is not supported.

**When it occurs:** When an admin attempts to enable Dynamic Forms on standard objects such as Task, Event, User, Product (Product2), or Contract. The supported list has expanded incrementally with each Salesforce release but is not exhaustive.

**UNVERIFIED (2026-09-04):** the specific objects named above (Task, Event, User, Product2, Contract) are not confirmed as unsupported by any source available offline. The Metadata API Developer Guide documents that `fieldInstance` exists only on Dynamic Forms-enabled pages but publishes no object support matrix, and help.salesforce.com cannot be fetched. Treat this list as a prompt to check, not as fact: open Lightning App Builder for the object and look for the field-placement affordance.

**How to avoid:** Before beginning any Dynamic Forms implementation, verify the object is on the current supported list at https://help.salesforce.com/s/articleView?id=sf.lightning_app_builder_dynamic_forms.htm. If the object is not supported, evaluate whether record types + page layout assignments can achieve the required field visibility, or whether a custom LWC component is needed. Check release notes each major release for newly added standard objects.

---

## Gotcha 4: Dynamic Actions Can Conflict With Page Layout Action Overrides

**What happens:** When Dynamic Actions is enabled on a Lightning record page, actions can appear from two sources: the Lightning record page (Dynamic Actions components) and the page layout (action overrides). This can cause the same action to appear twice in the action bar, or visibility rules to be ignored because the page layout's static action list overrides the Dynamic Actions configuration.

**When it occurs:** After enabling Dynamic Actions on a Lightning record page without removing corresponding actions from the page layout's action section. Most commonly seen when teams enable Dynamic Actions incrementally — adding one action as a Dynamic Action component while leaving others on the page layout.

**How to avoid:** When enabling Dynamic Actions, audit the page layout's action configuration and remove any actions that will be managed via Dynamic Actions components. Treat the page layout action list and the Dynamic Actions canvas as mutually exclusive for the actions you are migrating. Remove the action from the page layout action section before adding it as a Dynamic Actions component on the record page.

---

## Gotcha 5: Visibility Filter Conditions Using Picklist Fields Require Exact API Values

**What happens:** When a visibility filter condition references a picklist field, the value entered must match the picklist field's API value exactly — not the label displayed in the UI. If the picklist field has a label of "In Review" but an API value of "In_Review", entering "In Review" in the filter condition causes the filter to never match, and the field or action remains permanently hidden or visible.

**When it occurs:** When admins type picklist values directly into the filter condition value field instead of selecting from the dropdown. The picklist value dropdown in Lightning App Builder shows labels, but behind the scenes the comparison uses API values. Custom picklists and standard picklists with labels that differ from API values are both affected.

**How to avoid:** Always use the picklist dropdown selector in the visibility filter dialog rather than typing values manually. If the field is not showing the dropdown (e.g., for certain standard picklists), verify the exact API value via Setup > Object Manager > the object > Fields > the picklist field > Values.


---

## Gotcha 6: There Is No Org-Level Dynamic Forms Switch to Deploy Any More

**What happens:** A team scripts an environment build that turns Dynamic Forms on for the org — a `RecordPageSettings` entry, a scratch-org definition feature, a settings file — and the setting either silently does nothing or the deploy fails on an unknown field. The team then spends the pipeline debugging session looking for the switch instead of at the page.

**When it occurs:** Any time an org-provisioning script written against an older API version is replayed at a current version, and any time an agent reasons "feature X must have an enablement setting". The Metadata API Developer Guide lists `enableDynamicForms` under `RecordPageSettings` with a single qualifier: *"Removed in API version 50.0 and later."* The only Dynamic Forms setting that still exists is `DynamicFormsSettings.enableFormsOnMobile` (API 58.0+, Beta), and that governs mobile rendering, not the feature.

**How to avoid:** Stop looking for an org switch. Dynamic Forms is a property of an individual `FlexiPage` — a page has it because it contains `fieldInstance` items, which the guide describes as *"available only on Lightning Pages that have enabled Dynamic Forms."* Enablement and configuration are the same act. In a scratch-org definition, provision nothing; in source control, the evidence that a page is Dynamic Forms-enabled is the presence of `<fieldInstance>` in its `.flexipage-meta.xml`, and that is what a build check should assert.

---

## Gotcha 7: `Required` Is a Property of the Field Instance, Not of the Field

**What happens:** A field is marked required on a Dynamic Forms page, everyone signs off, and rows keep arriving with it blank — from Data Loader, from a Flow, from the API, from a quick action, and from any other Lightning page that places the same field.

**When it occurs:** Whenever "make it required" is interpreted as a data-quality control. `uiBehavior` is a `fieldInstanceProperty` — it hangs off one `fieldInstance`, on one page, identified by one `identifier`. Place the same field on a second page without it and that page saves happily. Nothing about `uiBehavior` reaches the record-save path, so no API caller is affected at all. The same is true of layout-level required, which `admin/record-types-and-page-layouts` gotcha 11 covers for the layout side.

**How to avoid:** Decide which of the two problems you have. If the field must never be null in the database, that is a validation rule or `<required>true</required>` on the `CustomField`, and the Dynamic Forms `Required` is decoration on top. If you only want to prompt the user on this one screen, `uiBehavior` is correct and the field must stay nullable — because a genuinely required field combined with a visibility rule that hides it produces an unsaveable record, which `admin/dynamic-forms-migration` gotcha 1 covers in detail.

---

## Gotcha 8: You Cannot Remove a Page Assignment With `destructiveChanges.xml`

**What happens:** A team retires a record page, adds the `FlexiPage` to `destructiveChanges.xml`, and the deploy fails — or worse, succeeds against a stale assignment and leaves users on a page that no longer exists. The instinct is then to add the `actionOverrides` entry to the destructive manifest, which does nothing.

**When it occurs:** On any page retirement or org cleanup. The guide is explicit for both carriers. For the object-level assignment: *"You can't delete ActionOverrides by deploying with destructiveChange.xml. To delete an ActionOverride, retrieve the CustomObject. In the definition file, find the `<ActionOverrides>` section, and remove the `<content>` row. Then, change the `<type>` value in that same section to Default."* For the app-level one: *"To delete a ProfileActionOverride, retrieve the app. In the app definition file, find the `<profileActionOverrides>` section, and remove the `<content>` row."*

**How to avoid:** Retirement is a two-step constructive deploy, not a destructive one. First deploy the edited `CustomObject` / `CustomApplication` that repoints or resets the override, confirm in App Builder → Activation that nothing still points at the page, then delete the `FlexiPage`. Two further traps in the same section: the guide recommends *"a fresh retrieve every time you want to delete a new override"* — a previously retrieved file will reintroduce the assignment you just removed — and *"Org default flexipage override assignment metadata can't be retrieved from a managed package,"* so a packaged page's org default is invisible to your diff.

---

## Gotcha 9: The Mobile Behaviour of a Dynamic Form Is an Org-Wide Beta Toggle, Not a Page Decision

**What happens:** A page is designed with per-field visibility, rolled out, and the field-service or sales users on phones report a different record page from the one in the design review. The team looks for a mobile setting on the page and finds none.

**When it occurs:** Whenever a Dynamic Forms page is reached from the Salesforce mobile app. Two independent switches decide what happens, and neither lives on the page. `DynamicFormsSettings.enableFormsOnMobile` is a *single settings file for the whole org* (API 58.0+, and the guide marks it a Beta Service subject to the Beta Services Terms) — so it cannot be piloted per page, per app, or per profile. Separately, the `formFactor` on the *assignment* decides which page a phone even loads: `Small` is the Salesforce mobile app, `Large` is Lightning Experience desktop, and a missing value means Salesforce Classic. Two form factors need two `actionOverrides` blocks.

**How to avoid:** Treat mobile as its own activation row from the start. Deploy the `Small` `actionOverrides` alongside the `Large` one in the same change, and get an explicit decision on the org-wide Beta setting before the design assumes phone parity — an org that has not enabled it cannot be fixed page-by-page.

**UNVERIFIED (2026-09-04):** what a phone actually renders when `enableFormsOnMobile` is false is not stated in the Metadata API Developer Guide, and the "Dynamic Forms does not render in Salesforce mobile offline mode" claim carried elsewhere in this skill is likewise unconfirmed offline. Test on a real device before promising either behaviour.

---

## Gotcha 10: A Region Holds 100 Components, and Dynamic Forms Is What Finally Reaches That Ceiling

**What happens:** A wide object — an insurance policy, a clinical record, a 200-field custom object — is converted field-by-field into one long column, and the page either refuses to save or starts behaving unpredictably at a size no page-layout-backed page ever reached.

**When it occurs:** On exactly the objects Dynamic Forms is most attractive for. The guide states the constraint under `FlexiPageRegion`: *"A Lightning page region can contain up to 100 components."* Under a page layout, a hundred fields were one component — the detail panel. Under Dynamic Forms every field is its own item, so the item count and the field count become the same number. Two neighbouring caps land in the same place: `ComponentInstanceProperty` has a maximum of 10,000 characters (a long rich-text or a large `valueList` can hit it), and `identifier` is capped at 120 characters.

**How to avoid:** Structure before you convert. Split fields across several `flexipage:fieldSection` components, each pointing at its own column facets, and across tabs or accordion facets rather than piling everything into `main` — a facet is a separate region and carries its own budget. Then trim: fields that only a minority of users read do not need to be on the page at all. Note also that page render cost rises with the number of components and rules evaluated, which is `admin/lightning-page-performance-tuning`'s subject; its gotcha 5 makes the sharper point that Dynamic Forms only *improves* performance when fields are conditionally hidden, so a conversion that hides nothing has added components for nothing.

**UNVERIFIED (2026-09-04):** the 100-component region cap is documented for "components". Whether a `fieldInstance` (an ItemInstance that is not a ComponentInstance) counts against that cap is not stated in the guide. Treat 100 items per region as the planning ceiling rather than assuming fields are exempt.
