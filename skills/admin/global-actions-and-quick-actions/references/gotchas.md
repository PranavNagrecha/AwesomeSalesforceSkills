# Gotchas — Global Actions and Quick Actions

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Action Layout Is Separate from Page Layout

**What happens:** An admin adds a field to an object's page layout, expecting it to appear in the quick action dialog. The field does not appear. Users cannot enter the field when using the action.

**When it occurs:** Any time an admin who is unfamiliar with the two-layout model edits a page layout and assumes the change flows into the action form. Very common with onboarding admins and new quick action configuration.

**How to avoid:** Always edit the action layout directly: Setup → Object Manager → [Object] → Buttons, Links, and Actions → [Action Name] → Edit Layout. The action layout and the page layout are completely independent. A field must be added to both if you want it visible on the record page AND in the quick action form.

---

## Gotcha 2: LWC Global Quick Actions Only Work in Field Service Mobile

**What happens:** A developer creates a Lightning Web Component, exposes it with `lightning__GlobalAction` as the target in the component metadata, adds it to the Global Publisher Layout, and expects it to appear in Lightning Experience. It does not appear for standard Lightning users.

**When it occurs:** When teams build custom global quick actions using LWC and test in a developer org or sandbox that happens to have FSL installed, the action appears — giving a false positive. Production users without Field Service see nothing.

**How to avoid:** Per the Salesforce LWC Developer Guide, LWC components with `lightning__GlobalAction` target are supported only in the Field Service mobile app. For standard Lightning Experience global actions using custom UI, use a Visualforce page with `<apex:page docType="html-5.0" applyBodyTag="false">` or an Aura component with the `force:lightningQuickAction` interface. For object-specific custom quick actions, LWC works as expected.

---

## Gotcha 3: Action Must Be Added to a Page Layout to Be Visible

**What happens:** An admin creates a quick action, edits the action layout, sets predefined values — but the action never appears on any record page.

**When it occurs:** The admin skips the final step of adding the action to the page layout. The action exists in Setup but is not surfaced to any user because it has not been placed in the "Salesforce Mobile and Lightning Experience Actions" section of any page layout. Common with less experienced admins and with automated scripting that creates actions via Metadata API without updating page layouts.

**How to avoid:** After creating and configuring an action, always open the relevant page layout (or Global Publisher Layout for global actions) and drag the action into the actions section. Then confirm the page layout is assigned to the correct profiles.

---

## Gotcha 4: Merge Field Predefined Values Fail on Global Actions

**What happens:** An admin tries to use `{!ObjectName.FieldName}` merge-field syntax in a predefined value on a global action. Salesforce throws a validation error and will not save the predefined value.

**When it occurs:** When an admin copies predefined value configuration from an object-specific action to a global action without adjusting for the lack of source-record context.

**How to avoid:** Global actions do not have a source record, so merge field formulas that reference record fields are not valid. Predefined values on global actions must be static literal values or formulas that do not reference `{!ObjectName.Field}` syntax. If you need to pre-fill from a record, use an object-specific action instead.

---

## Gotcha 5: Actions Beyond Position 5 Are Hidden in the "More" Menu

**What happens:** An admin adds 8 actions to the "Salesforce Mobile and Lightning Experience Actions" section of a page layout. Users report they cannot find 3 of the actions. The admin confirms the actions are in the layout.

**When it occurs:** In Lightning Experience, the highlights panel displays the first ~5 actions directly in the action bar. Actions beyond the 5th position collapse into a "More" overflow menu that many users do not discover. On mobile, the action bar also has limited visible slots.

**How to avoid:** Limit the total number of actions in the section to the 5–7 most frequently used. Audit action usage to identify low-use actions and remove or move them to a less prominent position. Place the highest-frequency actions first in the list. Consider whether all actions truly belong on the record page vs being accessible from other surfaces.
