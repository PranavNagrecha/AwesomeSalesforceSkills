# Gotchas — Dynamic Forms Migration

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Required + Hidden = Save Failure with No User Feedback Loop

**What happens:** A field is marked `required` on its Dynamic Forms component AND has a visibility rule that hides it for some users / record types. A user in the hidden cohort attempts to save the record. The save fails with `REQUIRED_FIELD_MISSING` — referencing a field the user can't see.

**Why:** Required-ness is a server-side validation that runs regardless of UI visibility. Visibility rules are UI-only. The two layers don't coordinate.

**Mitigation:** Never combine `required=true` with a visibility rule on the same component. Choose one: if the field must be populated, it must be visible to the user filling the record. Use validation rules with explicit conditions if you need conditional requirement based on other field values — and surface a clear error message.

## Gotcha 2: Component Visibility Doesn't Re-evaluate on Inline Edit

**What happens:** A user inline-edits the `RecordType` on the page. The save succeeds. The user expects the field set to update to match the new record type. It doesn't — the page still shows the previous record type's visible fields.

**Why:** Visibility rules are evaluated on full page render. Inline edits commit data without triggering a render. The UI presents stale visibility until the user refreshes the page.

**Mitigation:** Document this behavior in the user runbook. For workflows that change `RecordType` frequently, consider a custom LWC button that performs the change and forces a page reload. Salesforce may improve this; track release notes.

## Gotcha 3: Hidden Fields Are NOT Removed from Reports, Formulas, or API

**What happens:** A field has Dynamic Forms visibility "Show only to managers." A non-manager user can't see the field on the page. The same user runs a report that includes the field — and sees the value clearly.

**Why:** Dynamic Forms visibility is a UI-only filter. Field-Level Security (FLS) is the data-layer security control. Hiding via visibility rules without restricting FLS leaves the data fully accessible via reports, list views, formulas, and API.

**Mitigation:** If a field must be truly inaccessible to a user, restrict via FLS — Profile or Permission Set field permissions. Use Dynamic Forms visibility for UX simplification (declutter the page), not for security. The two layers serve different purposes.

## Gotcha 4: Quick Action Inputs Still Use the Page Layout

**What happens:** A team migrates the Account record page to Dynamic Forms. They later add a new Quick Action for "Edit Address." They configure the action; the input field list is empty. They add fields to the Dynamic Forms page expecting the Quick Action to inherit. It doesn't.

**Why:** Quick Actions reference the *Quick Action layout* on the Page Layout, NOT the Dynamic Forms record page. The Page Layout's Quick Action section is independent of the record page's field configuration.

**Mitigation:** When adding or modifying Quick Actions, edit the Quick Action layout on the relevant Page Layout. Document this dual-management explicitly. Some orgs maintain a dedicated "Actions" Page Layout per object specifically for Quick Action configuration.

## Gotcha 5: Mobile Renders the Same Page — But Some Components Behave Differently

**What happens:** Migration completes successfully on desktop. Users on the Salesforce mobile app report missing fields, awkward layouts, or "the section is empty."

**Why:** Some Dynamic Forms components (custom LWCs, certain visibility rule combinations) render differently or not at all on mobile. The same Lightning Record Page is used for both surfaces; mobile-specific issues only appear on actual mobile rendering.

**Mitigation:** Test on real mobile devices (iOS and Android Salesforce app) before declaring migration complete. Use the App Builder's "Form Factor" filter (`$Browser.FormFactor equals 'Phone'`) to provide mobile-specific component variants where needed.

## Gotcha 6: Page Layouts Cannot Be Fully Deleted — At Least One Per Record Type Is Required

**What happens:** Migration is complete. Admins decide to "clean up by deleting all old Page Layouts." Some delete attempts fail; others succeed but break Quick Actions and Print View.

**Why:** Salesforce requires at least one Page Layout per record type for Quick Action assignment, Print View rendering, and Salesforce Classic display. Deleting all Page Layouts is not a supported state.

**Mitigation:** Retain at least one minimal Page Layout per object (or per record type if Quick Actions vary). Reduce content to standard fields only; the Dynamic Forms record page handles the rich layout. Don't try to eliminate Page Layouts entirely.

## Gotcha 7: Compact Layout Still Drives the Highlights Panel

**What happens:** A team migrates the record page to Dynamic Forms; they configure a beautiful new field layout. The Highlights Panel (the top of the record page showing key fields) doesn't update.

**Why:** Compact Layouts (configured in Object Manager → Compact Layouts) drive the Highlights Panel. Dynamic Forms covers the Record Detail component below the Highlights Panel — not the Highlights Panel itself.

**Mitigation:** Review and update the Compact Layout for each record type alongside the Dynamic Forms migration. Treat them as two separate but coordinated changes.

## Gotcha 8: Profile Name in Visibility Rules Is a Brittle String Reference

**What happens:** A visibility rule uses `$User.Profile.Name equals 'Sales Rep'`. Six months later, the org renames the profile to "Inside Sales Rep" for clarity. The visibility rule silently stops matching; the field becomes visible to (or hidden from) the wrong users.

**Why:** Profile name is a freeform string. Renaming a profile breaks any reference that pinned the old name. Visibility rules don't fail at rename time — they just stop matching, and the symptom is a wrong field-visibility outcome.

**Mitigation:** Prefer Custom Permissions (`$Permission.X equals true`) over profile name strings. Custom Permissions are stable identifiers; they survive Permission Set / Profile renaming and can be assigned more granularly.

## Gotcha 9: Managed-Package Lightning Record Pages Cannot Be Migrated In-Place

**What happens:** An org installed a managed package that includes a Lightning Record Page for a custom object. The team wants to migrate that page to Dynamic Forms. App Builder shows the page as read-only.

**Why:** Pages owned by a managed package cannot be edited by the subscriber org. The "Upgrade Now" button is disabled because edit access is restricted.

**Mitigation:** Clone the managed-package page to your namespace via "Clone" in App Builder. Migrate the clone to Dynamic Forms. Reassign the cloned page to the relevant apps / profiles / record types. The original managed-package page remains untouched (and irrelevant once the clone is the active assignment).
