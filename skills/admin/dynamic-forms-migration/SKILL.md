---
name: dynamic-forms-migration
description: "Migrating standard Lightning Record Page layouts (Page Layouts on the Record Detail component) to Dynamic Forms — converting fields and sections to component-level placement, replacing record-type-driven layouts with field-visibility filters, retaining or replacing Quick Action layouts, planning custom-object vs standard-object rollout, and verifying field-level security and Reading View parity. NOT for Dynamic Forms initial setup (use admin/dynamic-forms-and-actions) or Lightning Record Page design from scratch (use admin/lightning-app-builder-advanced)."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - User Experience
  - Operational Excellence
  - Security
triggers:
  - "How do I migrate from Page Layouts to Dynamic Forms?"
  - "Convert record-type-driven page layouts to a single Dynamic Forms record page"
  - "Dynamic Forms is generally available on standard objects — should I migrate Account / Contact / Opportunity?"
  - "What about Quick Action layouts — do they migrate too?"
  - "Field-level security audit before turning on Dynamic Forms"
tags:
  - dynamic-forms
  - page-layouts
  - record-pages
  - lightning-app-builder
  - field-visibility
  - migration
inputs:
  - "Object scope (standard vs custom; some standard objects have unique constraints)"
  - "Inventory of existing page layouts per object, per record type, per profile"
  - "Whether record types currently drive layout differentiation (and how)"
  - "Whether the record page is shared across multiple apps / profiles"
  - "Quick Action coverage and any layout dependencies on Compact Layouts"
outputs:
  - "Dynamic Forms-enabled Lightning Record Page replacing the Record Detail component"
  - "Field-visibility rules replacing record-type page-layout differentiation"
  - "Documentation of fields no longer visible (or newly visible) per profile, per record type"
  - "Updated list of Compact Layouts (still required for highlights panel) and Quick Action layouts (still page-layout-driven)"
  - "Pre/post audit comparing field visibility for representative user / record-type combinations"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-30
---

# Dynamic Forms Migration

This skill activates when a practitioner needs to migrate from traditional page-layout-driven record pages to Dynamic Forms — placing fields and sections as components in the Lightning App Builder with per-component visibility rules instead of record-type-driven full-layout switching.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm Dynamic Forms availability for your target object. Generally available on standard objects (Account, Contact, Opportunity, Lead, Case, custom objects, and most platform objects) since the Spring '24 wave; confirm for the specific object — Tasks, Events, and a small number of system objects still have constraints.
- Inventory page layouts per object: `SELECT Id, Name, EntityDefinition.QualifiedApiName, RecordTypeId FROM LayoutAssignment` (queryable via Tooling API). Identify how many distinct layouts exist and whether they vary by record type, profile, or both.
- Identify the current Lightning Record Page assignments: per-app, per-profile, per-record-type. The migration changes the Record Detail component on these pages — every assigned page must be touched.
- Confirm Compact Layouts and Quick Action layouts are inventoried separately. Dynamic Forms covers the Record Detail component; the Highlights Panel still uses Compact Layouts, and Quick Actions still reference Page Layouts. These are NOT migrated in scope.
- Check Field-Level Security per profile. Dynamic Forms respects FLS, but the field-visibility filters layered on top can confuse the "why can't I see this field?" debugging. Audit FLS first; layer Dynamic Forms visibility on top.

---

## Core Concepts

### 1. What Dynamic Forms Replaces — and What It Doesn't

| Currently driven by Page Layout | Migrated to Dynamic Forms? | Migrated to what? |
|---|---|---|
| Field placement on the Record Detail component | YES | Field components in the App Builder canvas |
| Field-level required, read-only on layout | YES | Component-level required / read-only properties |
| Section organization | YES | Field Section components |
| Conditional field visibility (was: separate layouts per record type) | YES | Per-component visibility filters using `RecordType.DeveloperName`, field values, user properties |
| Highlights Panel field selection | NO — still Compact Layout | Compact Layouts remain authoritative |
| Quick Action input fields | NO — still Page Layout (Quick Action layout) | Quick Action layouts remain unchanged |
| Related Lists | NO — still configured on the Lightning Record Page (or on the Page Layout for non-Dynamic-Forms objects) | Dynamic Related Lists are a separate feature |
| Print View | NO — still Page Layout-driven for print | Print View limitation persists |
| Salesforce Mobile App field rendering | YES (with caveats) | Same Dynamic Forms render in mobile if using the LEX page; verify on mobile |
| Salesforce Classic | NO — Classic users continue to see Page Layouts | Page Layouts remain in effect for Classic users |

### 2. The Record Page Migration Path in App Builder

| Step | What you do |
|---|---|
| 1 | Open the Lightning Record Page in App Builder |
| 2 | Locate the Record Detail component on the canvas |
| 3 | Choose "Upgrade Now" (or "Migrate to Dynamic Forms" depending on UI version) — App Builder generates Field Section components from the existing Page Layout's sections |
| 4 | The generated components mirror the current Page Layout's section structure and field order |
| 5 | Customize: add visibility filters, regroup sections, add new components (related lists, custom LWCs) interleaved with field sections |
| 6 | Activate the page (assign to apps / profiles / record types as before) |

The "Upgrade Now" auto-conversion is the most important migration mechanic. It generates working Dynamic Forms components from the existing Page Layout in seconds — you don't rebuild the layout by hand.

### 3. Replacing Record-Type-Driven Differentiation

| Pre-Migration: Layout-Per-Record-Type | Post-Migration: Visibility Rules |
|---|---|
| One Page Layout per record type | One Lightning Record Page (or fewer pages) with field-visibility rules per record type |
| `Sales_Layout` for Sales record type, `Service_Layout` for Service record type | Field components have visibility rule: show if `RecordType.DeveloperName = 'Sales'` |
| Layout assignment via Profile + Record Type | Page assignment can stay record-type-aware OR collapse to one page with visibility rules — choose based on complexity |
| Reordering required adding/removing fields per layout | Single component placement; visibility rules toggle per-record-type display |

The simplification is meaningful for orgs with 5+ record types per object — managing 5 page layouts becomes managing one page with 5 visibility rules.

### 4. Field-Visibility Rule Semantics

Dynamic Forms component visibility supports filters on:

| Filter source | Examples |
|---|---|
| Record fields | `Account.Industry equals 'Healthcare'`, `Opportunity.StageName equals 'Closed Won'` |
| Record type | `RecordType.DeveloperName equals 'Sales'` |
| User properties | `$User.Profile.Name equals 'Sales Manager'`, `$User.Department equals 'EMEA'` |
| Permission | `$Permission.Custom_Permission_Name equals true` |
| Device form factor | `$Browser.FormFactor equals 'Desktop'` |
| Combined (AND/OR) | Up to 5 filter criteria with AND/OR logic per component |

These rules are evaluated per component on render. Hidden fields are not present in the DOM at all — security implications below.

### 5. Field-Level Security vs Dynamic Forms Visibility

| Layer | What it controls | Who enforces |
|---|---|---|
| Field-Level Security (FLS) | Whether the user has access to read/edit the field at the data layer | Salesforce platform — applies to API, reports, formulas, every access path |
| Dynamic Forms component visibility | Whether the field is rendered in the App Builder page for this user/record | Lightning App Builder — UI-only |

FLS is the security layer. Dynamic Forms visibility is a UX layer on top. Hiding a field via Dynamic Forms visibility while granting FLS read access means the user CAN see the value via API, reports, and other surfaces — just not on this Lightning page. Conversely, granting Dynamic Forms visibility while denying FLS results in a "this field is not accessible" placeholder. Always set FLS correctly first; use Dynamic Forms for UX layering.

---

## Common Patterns

### Pattern 1: Single Page Layout → Dynamic Forms (Simplest Migration)

**When to use:** The object has one or two page layouts, no record-type-driven differentiation, simple field visibility needs.

**How it works:**
1. Open the Lightning Record Page assigned to the object.
2. Click the Record Detail component → "Upgrade Now".
3. Verify the auto-generated Field Section components reproduce the original layout exactly.
4. Save and activate.

**Why not the alternative:** Building Dynamic Forms by hand is slower and more error-prone than the auto-conversion, even for simple cases.

### Pattern 2: Record-Type-Driven Layouts → Single Page with Visibility Rules

**When to use:** The object has multiple page layouts differentiated by record type. E.g., 3 Account record types each with their own page layout.

**How it works:**
1. Choose a "primary" Record Type's page layout to convert first via "Upgrade Now."
2. For each additional Record Type's layout, identify the unique fields/sections.
3. Add those unique fields/sections as additional Dynamic Forms components on the same page.
4. Apply visibility rules: `RecordType.DeveloperName equals 'X'` per component.
5. Test by switching record types on a sample record; verify each record type sees its expected field set.
6. Decommission the per-record-type Page Layouts after sign-off.

**Why not the alternative:** Maintaining multiple Lightning Record Pages (one per record type) is a valid alternative, but loses the simplification benefit of Dynamic Forms. One page with rules is better when the unique-field count per record type is small (<10 fields).

### Pattern 3: Profile-Driven Layouts → Visibility Rules with `$User.Profile.Name`

**When to use:** The object has different page layouts assigned to different profiles. E.g., "Sales Rep Layout" hides commission fields shown on "Sales Manager Layout."

**How it works:**
1. Convert the most-permissive profile's layout via "Upgrade Now."
2. For fields that should be hidden from less-permissive profiles, add visibility rules: `$User.Profile.Name not equals 'Sales Rep'` (or use a Custom Permission for cleaner abstraction).
3. Test by impersonating each profile; verify visibility matches expectations.

**Why not the alternative:** Profile-name string matching is brittle (renaming a profile breaks visibility). Prefer Custom Permissions: `$Permission.View_Commission_Fields equals true`. Custom Permissions are stable identifiers and can be assigned via permission sets, which is more flexible than profile-based matching.

### Pattern 4: Hybrid — Dynamic Forms for Detail, Compact Layout for Highlights

**When to use:** Always (this is the steady-state architecture for a Dynamic Forms record page).

**How it works:**
1. Highlights Panel still reads from Compact Layout. Configure the Compact Layout to show the right fields (typically 3–5 most-important).
2. Record Detail uses Dynamic Forms components.
3. Quick Actions still reference Page Layouts (the Quick Action layout, not the Page Layout for Record Detail).
4. Acknowledge the dual-management: Compact Layout and Page Layout are still in play even after the Record Detail is on Dynamic Forms.

**Why not the alternative:** Trying to "migrate everything to Dynamic Forms" leads to confusion when Highlights Panel and Quick Actions don't behave as expected. They are out of scope; document that explicitly.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Single page layout, no record-type variance | Pattern 1: direct "Upgrade Now" | Simplest path; auto-conversion handles everything |
| 3+ record types each with own layout | Pattern 2: collapse to one page with visibility rules | Reduces layout-management overhead |
| Profile-driven layout differentiation | Pattern 3: Custom Permissions in visibility rules | Profile-name strings are brittle; Custom Permissions are stable |
| <10 fields differ between record types | Single page with rules | Maintenance is simpler than multiple pages |
| >30 fields differ between record types | Separate Lightning Record Pages per record type, each with Dynamic Forms | Visibility rules at this volume become unmanageable |
| Object also has Salesforce Classic users | Migrate Lightning page only; Classic users continue with Page Layouts | Dynamic Forms doesn't apply in Classic |
| Mobile-heavy usage | Migrate but verify on mobile; some Dynamic Forms components have mobile-specific quirks | Same page renders on mobile; spot-check render fidelity |
| Object is Task, Event, or one of the late-GA standard objects | Verify Dynamic Forms availability before planning | Some standard objects have Dynamic Forms constraints |
| Many in-flight changes to the page layout | Freeze layout changes during migration sprint | Concurrent layout edits during migration risk inconsistent state |
| FLS not yet correctly set per profile | Audit and fix FLS BEFORE adding Dynamic Forms visibility rules | Two layers of visibility are hard to debug; fix the data-layer one first |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Inventory page layouts and assignments.** For the target object: list all Page Layouts, all Record Type assignments, all profile assignments, all Lightning Record Page assignments. Identify the dominant layout (most-assigned) — this becomes the conversion source.
2. **Audit Field-Level Security.** Pre-migration, run a per-profile FLS report. Note any fields where FLS doesn't match what users actually see (rare but exists). Fix FLS to match expected access BEFORE adding Dynamic Forms visibility rules.
3. **Convert via "Upgrade Now" in sandbox.** Open the Lightning Record Page; click Record Detail → "Upgrade Now." The auto-generated components mirror the source Page Layout's structure.
4. **Add visibility rules for record-type and profile differentiation.** Replace the per-record-type / per-profile page layouts with visibility filters. Prefer Custom Permissions over profile-name strings.
5. **Compose with non-field components.** Dynamic Forms is not just about fields — interleave related lists, custom LWCs, Quick Actions, and Path components in the same canvas to create a richer record page.
6. **Test exhaustively in sandbox.** Open sample records of each record type. Impersonate each affected profile (`Setup → Users → Login as User`). Verify field visibility matches expectations. Test on mobile.
7. **Activate in sandbox; collect user feedback.** Run a 1–2 week sandbox preview with selected users before production cutover.
8. **Production rollout.** Activate the Dynamic Forms record page in production. Keep the original Page Layouts in place initially (they govern Classic users and any record pages NOT using Dynamic Forms).
9. **Decommission original Page Layouts (selectively).** After sign-off, the original Page Layouts can be retired IF they're no longer assigned to any active surface. Keep at least one minimal layout per object — Salesforce requires it for Quick Actions, Print View, and Classic.
10. **Document the architecture.** Per-component visibility rules and the underlying field-permission model are not self-documenting. Maintain a runbook of "field X visible when Y" per object.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Field-Level Security has been audited per profile and matches expected access at the data layer
- [ ] Lightning Record Page has been converted via "Upgrade Now"; auto-generated components match the source Page Layout
- [ ] Record-type differentiation has been moved into per-component visibility rules (or split into separate pages if field counts justify it)
- [ ] Profile-based visibility uses Custom Permissions (preferred) or `$User.Profile.Name` (acceptable but brittle)
- [ ] Compact Layout has been reviewed; Highlights Panel still configured correctly
- [ ] Quick Action layouts have been reviewed; the Quick Action surface still uses Page Layouts
- [ ] Mobile rendering verified on real devices for at least one record per record type
- [ ] User-impersonation testing completed for each affected profile / record type combination
- [ ] Documentation captures per-component visibility rules and their business intent
- [ ] Original Page Layouts retained (at least minimally) for Quick Actions, Print View, and Classic users
- [ ] Activation rolled out via Lightning Record Page assignment (per-app, per-profile, per-record-type as needed)

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Page Layout still drives Quick Action input fields, Print View, and Salesforce Classic.** Migrating Record Detail to Dynamic Forms does NOT migrate Quick Action layouts (which still reference the Page Layout's Quick Action section), Print View (driven by Page Layout), or Salesforce Classic users (who don't see Lightning Record Pages at all). Plan to keep at least one minimal Page Layout per object permanently.

2. **Dynamic Forms component visibility is a UI-only filter, not security.** Hiding a field via component visibility does NOT prevent the user from accessing it via API, reports, or formulas. FLS is the security layer; Dynamic Forms visibility is for UX organization. Treating Dynamic Forms visibility as a security control creates false confidence in data protection.

3. **Hidden fields ARE in the page metadata — but not in the DOM.** When a visibility rule hides a field, the field component is excluded from the rendered DOM. This means scripted tests (Selenium, Playwright) that rely on element presence break unpredictably as visibility rules trigger or untrigger. Tests must be visibility-aware or operate via API rather than DOM.

4. **Highlights Panel uses Compact Layout, not Dynamic Forms.** Admins frequently expect that "the page is Dynamic Forms now" means the Highlights Panel is too. It isn't. The Highlights Panel field set comes from the Compact Layout for the record type. Ensure the Compact Layout has been reviewed alongside the Dynamic Forms migration.

5. **Reading View / Read-Only User View renders differently.** Reading View (the page rendered for users without edit access, or in some Communities contexts) may render Dynamic Forms differently than the standard edit view — typically simpler, with some component visibility rules behaving differently. Test the Reading View path explicitly for Communities users and read-only profiles.

6. **Record-type changes after page render don't re-evaluate visibility.** If a user changes a record's RecordType via inline edit on the page, visibility rules that depend on `RecordType.DeveloperName` re-evaluate only on full page reload — not on the inline-edit save. Users may see stale field visibility briefly. Workaround: refresh the page after record-type changes (Salesforce may improve this in future releases).

7. **Visibility rule on a required field can hide it but not relax the validation.** A field marked required on the Page Layout (or in Dynamic Forms component properties) remains required even when hidden by visibility rules. The save fails with "Required field missing" — and the user can't see the field to populate it. Fix: never combine "required" + "hidden by visibility" on the same component. Choose one or the other.

8. **Migrating an object on a managed-package Lightning Record Page may be blocked.** Dynamic Forms migration requires editing the page in App Builder. Pages owned by a managed package cannot be edited; you must clone them to your namespace, migrate the clone, and reassign. This is not a Dynamic Forms-specific limitation but is often discovered for the first time during migration.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Migrated Lightning Record Page | Record Detail component replaced with Field Section + Field components |
| Visibility-rule documentation | Per-component rule specification with business intent ("Hide commission fields from non-managers via Custom Permission View_Commission_Fields") |
| FLS audit report (pre/post) | Per-profile field access — confirms data-layer security matches expectations |
| Compact Layout review | Confirms Highlights Panel still surfaces the right fields for each record type |
| User-impersonation test log | Profile × Record Type matrix with verification of field visibility per combination |
| Decommissioning plan | Which original Page Layouts can be retired vs which must remain (Quick Actions, Print View, Classic) |

---

## Related Skills

- `admin/dynamic-forms-and-actions` — Use for new Dynamic Forms configuration (post-migration) and for Dynamic Actions
- `admin/lightning-app-builder-advanced` — Use for advanced Lightning Record Page composition patterns (custom LWCs, Path, Related Lists)
- `security/field-level-security-design` — Use to audit and re-architect FLS BEFORE applying Dynamic Forms visibility
- `admin/page-layout-assignment-strategy` — Use when planning which Page Layouts to retain for Quick Actions, Print View, and Classic
- `lwc/visualforce-to-lwc-migration` — Use if some record-page real estate also includes Visualforce components being modernized
