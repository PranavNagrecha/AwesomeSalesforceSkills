# Examples — Dynamic Forms and Dynamic Actions

## Example 1: Replacing Six Account Page Layouts With Field Visibility Rules

**Context:** A financial services org has six Account page layouts — one per Account record type (Prospect, Customer, Partner, Vendor, Competitor, Internal). The only meaningful difference between layouts is which fields appear. Whenever a new compliance field is added, an admin must update all six layouts. One layout was missed in the last release, causing a data quality issue.

**Problem:** Maintaining six separate page layouts creates drift. Admins must remember to update every layout when adding or renaming fields. The page layout assignment matrix (profile x record type) also grows as new profiles are added.

**Solution:**

1. Open Lightning App Builder for the Account record page assigned to these record types.
2. In the Page Properties panel, click "Upgrade Now" to convert the existing page layout fields to Dynamic Form components.
3. For fields that should only appear for specific record types, select the field component on the canvas, open "Set Component Visibility", and add a filter:
   - Filter type: Record Type
   - Operator: equals
   - Value: (select the applicable record types)
4. For fields that should appear across all record types, leave them without a visibility filter (they are always visible, subject to FLS).
5. Save the page. Activate it for all relevant profiles and record type combinations in a single page activation.

**Result:** One Lightning record page replaces six page layouts for field display purposes. Adding a new field now requires placing it once on the single page and setting a visibility filter if it is record-type-specific.

**Why it works:** Dynamic Forms visibility filters are evaluated at render time against the current record's record type. The page layout assignment matrix no longer drives field visibility — the Lightning record page does.

---

## Example 2: Hiding the "Approve Discount" Action Until Discount Exceeds Threshold

**Context:** A sales org has a custom "Approve Discount" quick action on the Opportunity object. The action should only be visible when the Discount_Percentage__c field exceeds 15 and the Opportunity Stage is not "Closed Won". Currently the action always appears, causing reps to accidentally click it on records that do not need approval.

**Problem:** The page layout action bar has no conditional visibility. The action is visible in all contexts, creating noise and user error.

**Solution:**

1. In Lightning App Builder, open the Opportunity record page.
2. In the Page Properties panel, enable Dynamic Actions.
3. Remove the "Approve Discount" action from the page layout action list (to avoid the action appearing from two sources).
4. On the page canvas, find the Actions area and drag the "Approve Discount" action component onto it.
5. Select the action component, click "Set Component Visibility", and add two filter conditions with AND logic:
   - Condition 1: Field Value — Discount_Percentage__c — Greater Than — 15
   - Condition 2: Field Value — StageName — Does Not Equal — Closed Won
6. Save and activate the page.

**Result:** The "Approve Discount" button only renders when the record meets both conditions. Reps no longer see it on records that do not require approval.

**Why it works:** Dynamic Actions component visibility is re-evaluated whenever the viewed record changes or when field values are updated. The AND logic ensures both conditions must be true simultaneously.

---

## Anti-Pattern: Enabling Dynamic Forms Without Running the Upgrade Wizard

**What practitioners do:** An admin enables Dynamic Forms on a Lightning record page by removing the existing "Fields" component and saving the page, assuming fields will still appear from the page layout.

**What goes wrong:** Removing the monolithic "Fields" component removes all page-layout-sourced fields from the page. Users see a record detail page with no fields — only the highlights panel and related lists. This happens immediately on page activation and affects all users assigned to that page.

**Correct approach:** Before removing or replacing the "Fields" component, use the "Upgrade Now" wizard in Lightning App Builder. The wizard inspects the assigned page layout and creates individual Dynamic Form field components for every field currently on the layout. Only after this conversion is the old "Fields" component replaced. Verify in a sandbox before activating in production.
