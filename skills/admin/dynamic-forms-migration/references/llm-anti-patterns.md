# LLM Anti-Patterns — Dynamic Forms Migration

Common mistakes AI coding assistants make when generating or advising on Dynamic Forms migrations.

## Anti-Pattern 1: Treating Dynamic Forms Visibility as Field-Level Security

**What the LLM generates:** Migration plan that says "Use Dynamic Forms component visibility to hide commission fields from non-managers." Implies this is a security control.

**Why it happens:** Hiding the field from the page feels like access restriction.

**Correct pattern:** Dynamic Forms visibility is UI-only. The field remains accessible via reports, list views, formulas, and the API. For genuine access restriction, set Field-Level Security via Profile or Permission Set field permissions. Use Dynamic Forms visibility for UX simplification, not security. Always state this distinction explicitly to the user.

## Anti-Pattern 2: Combining `required=true` with a Visibility Rule

**What the LLM generates:** Component configuration with both `Required: true` and `Visibility: RecordType equals 'X'`. Looks consistent — "this field is required for this record type."

**Why it happens:** Conflating "required when visible" with "required when applicable."

**Correct pattern:** Required-ness validates server-side regardless of UI visibility. Hidden + required means the user can't see the field but the save fails with "REQUIRED_FIELD_MISSING." Either: (a) make the field always visible if it must be required; or (b) use a validation rule with explicit conditional logic and a clear error message that doesn't blame the missing field.

## Anti-Pattern 3: Recommending Profile Name Strings for Visibility Rules

**What the LLM generates:**

```
Visibility filter: $User.Profile.Name equals 'Sales Rep'
```

**Why it happens:** Profile name is the obvious user attribute.

**Correct pattern:** Use Custom Permissions: `$Permission.View_Commission_Fields equals true`. Profile name strings break when profiles are renamed, and renames are common as orgs evolve. Custom Permissions are stable identifiers and can be assigned via Permission Sets — more flexible than profile-bound logic.

## Anti-Pattern 4: Recommending "Delete All Old Page Layouts" Post-Migration

**What the LLM generates:** Migration plan that ends with "After Dynamic Forms is active, delete all Page Layouts to clean up."

**Why it happens:** Mental model of "Page Layouts replaced by Dynamic Forms — therefore Page Layouts are obsolete."

**Correct pattern:** Page Layouts remain authoritative for: Quick Action input fields, Print View, Salesforce Classic users. At least one Page Layout per record type must remain. Migration plan should specify which Page Layouts can be retired and which must be kept (typically: keep one minimal Page Layout per record type, retire the variants that exist only for layout differentiation).

## Anti-Pattern 5: Forgetting Compact Layout Configuration

**What the LLM generates:** Migration plan that addresses Record Detail (Dynamic Forms scope) but doesn't mention Compact Layouts.

**Why it happens:** The Highlights Panel is visually part of the record page; the model assumes it's covered by the same migration.

**Correct pattern:** Compact Layouts drive the Highlights Panel separately. Migration plan must include "review and update Compact Layout for each record type" as an explicit step. Otherwise, the Highlights Panel may show stale or wrong fields after the Dynamic Forms migration.

## Anti-Pattern 6: Suggesting Direct FlexiPage XML Edit Instead of "Upgrade Now"

**What the LLM generates:** A code-first migration plan that involves editing `FlexiPage` XML to add field components and visibility rules.

**Why it happens:** XML feels like the canonical, version-controllable path.

**Correct pattern:** Use App Builder's "Upgrade Now" feature first — it auto-generates correct XML. Then export the resulting `FlexiPage` to source control for ongoing management. Direct XML editing is error-prone (visibility-rule structure is easy to malform) and "Upgrade Now" gets you 90% of the way faster.

## Anti-Pattern 7: Skipping Mobile Verification

**What the LLM generates:** Test plan that focuses on desktop browser verification, mentions mobile only as "should also work on mobile."

**Why it happens:** Mobile is a forgotten surface.

**Correct pattern:** Salesforce mobile app uses the same Lightning Record Page; some Dynamic Forms components and visibility rule combinations behave differently on mobile. Test on real devices (iOS and Android Salesforce app) for at least one record per record type. Use the App Builder's `$Browser.FormFactor equals 'Phone'` filter to provide mobile-specific component variants if needed.

## Anti-Pattern 8: Migrating One Big Change Without User Preview

**What the LLM generates:** Migration plan that goes "Sandbox migrate → production migrate" with no user preview phase.

**Why it happens:** Pressure to move quickly; "the auto-conversion handles everything."

**Correct pattern:** Run a 1–2 week sandbox preview with a sample of real users from each affected profile. Capture feedback, adjust visibility rules, fix any FLS gaps that surface. Production cutover comes only after sandbox sign-off. The auto-conversion is reliable for the layout structure; it cannot validate that the UX makes sense for the people using it.

## Anti-Pattern 9: Recommending One Lightning Record Page Per Record Type as the Default

**What the LLM generates:** "For each record type, create a separate Lightning Record Page with Dynamic Forms."

**Why it happens:** 1:1 mental mapping from Page Layout → Lightning Record Page.

**Correct pattern:** Default to ONE Lightning Record Page per object with per-component visibility rules. Switch to multiple pages only when the field-set difference between record types is large (>30 fields) and visibility rules become unmanageable. The whole point of Dynamic Forms is to consolidate; per-record-type pages re-fragment what was just consolidated.

## Anti-Pattern 10: Skipping the FLS Audit Step

**What the LLM generates:** Migration plan that adds Dynamic Forms visibility rules without an FLS audit first.

**Why it happens:** Visibility rules feel like the new control mechanism; FLS feels like background plumbing.

**Correct pattern:** Audit FLS first. Many orgs have FLS that's been incrementally configured over years and may not match current expectations. Adding Dynamic Forms visibility rules on top of misconfigured FLS produces two layers of access controls and makes "why can't user X see field Y" debugging unnecessarily complex. Fix the data layer first; layer Dynamic Forms on top with confidence.
