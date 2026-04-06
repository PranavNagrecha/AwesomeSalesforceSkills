# Gotchas — Lightning App Builder Advanced

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Visibility Filters Are Cosmetic — FLS Is the Security Gate

**What happens:** Components and fields hidden by visibility filters do not enforce field-level security. A user whose profile has FLS read on a field can still retrieve that field's value via API, Developer Console SOQL, or a connected app even when the LAB visibility filter hides the component on the record page.

**When it occurs:** Any time a practitioner uses visibility filters to restrict sensitive data instead of using FLS + object permissions.

**How to avoid:** Use visibility filters for UX simplification only. Always enforce data access through FLS, object permissions, and sharing rules. Never rely on a hidden component as a security boundary.

---

## Gotcha 2: Dynamic Actions + Page-Layout Actions = Duplicate Buttons

**What happens:** When Dynamic Actions is enabled on a record page, the action bar component on the canvas takes over rendering of actions. However, if the page layout assigned to the user still has a populated "Salesforce Mobile and Lightning Experience Actions" section, those actions render in addition to the Dynamic Actions bar — showing duplicate buttons.

**When it occurs:** Immediately after enabling Dynamic Actions on a page, before removing the page-layout action assignments from the relevant profiles and record types.

**How to avoid:** Before enabling Dynamic Actions, audit which page layouts are assigned to the profiles/record types using the target page. Either clear the action section in those layouts or switch the profile/record type assignment to a layout with an empty action section. Activate Dynamic Actions only after this cleanup is confirmed.

---

## Gotcha 3: Dynamic Forms Migration Silently Drops Fields Not on the Layout

**What happens:** The "Upgrade Now" wizard in LAB migrates only the fields currently present in the page layout's field section at the time of migration. Fields added to the page layout after migration, fields that exist on the object but were never added to the layout, and related-list components are not migrated automatically.

**When it occurs:** After running the Dynamic Forms migration wizard on a record page that has fields managed outside the layout (e.g., added via a later deployment) or where the layout had optional fields that were removed before migration.

**How to avoid:** Before running the wizard, take a screenshot or export of the full page layout field list. After migration, compare the LAB canvas field list against the pre-migration list. Manually add any fields that are missing. Test with multiple profiles to ensure field visibility is correct.

---

## Gotcha 4: LWC targetConfig Cannot Declare recordId as a Design Property

**What happens:** An LWC component intended for Lightning record pages includes `<property name="recordId" ...>` in its `targetConfig` block inside `.js-meta.xml`. When deploying or syncing the metadata, Salesforce returns a validation error indicating that `recordId` is a reserved property injected automatically by the platform.

**When it occurs:** When developers port patterns from older Aura components (where exposing attributes in the design resource was common) to LWC.

**How to avoid:** Do not declare `recordId` or `objectApiName` in the LWC component's `<targetConfig>` design section. These are injected automatically by the Lightning framework when the component is placed on a record page. Declare them only in the component's JavaScript class using the `@api` decorator — not in the metadata config.

---

## Gotcha 5: Per-Tab Visibility in Tabs Component Requires Summer '24 or Later

**What happens:** Practitioners on pre-Summer '24 orgs (or older sandbox releases) do not see the per-tab visibility option when editing the Tabs component in LAB. The option simply does not appear in the component properties panel.

**When it occurs:** When using the Tabs component on a record page in a sandbox or scratch org whose release has not yet been updated to Summer '24.

**How to avoid:** Confirm the org's Salesforce release version before designing a solution that depends on per-tab visibility. For orgs on Winter '24 or Spring '24, the fallback is to use separate page variants (one per record type or profile) or to place multiple standalone Tab components with page-level visibility filters.
