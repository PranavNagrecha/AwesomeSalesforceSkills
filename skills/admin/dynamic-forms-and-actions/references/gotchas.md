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

**How to avoid:** Field-Level Security (FLS) is the authoritative access control for field data. Dynamic Forms filters control rendering only. For any field that must be restricted from certain users, set FLS to "Read Only: No" or "Edit: No" for the relevant profiles/permission sets. Dynamic Forms filters can then additionally refine the UI experience, but FLS should be the primary control.

---

## Gotcha 3: Standard Objects Have Limited Dynamic Forms Support

**What happens:** Dynamic Forms is not available for all standard objects. If you open Lightning App Builder for a standard object that is not supported, the "Upgrade Now" option does not appear, and field components cannot be individually placed. Practitioners sometimes spend significant time trying to enable Dynamic Forms before discovering the object is not supported.

**When it occurs:** When an admin attempts to enable Dynamic Forms on standard objects such as Task, Event, User, Product (Product2), or Contract. The supported list has expanded incrementally with each Salesforce release but is not exhaustive.

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
