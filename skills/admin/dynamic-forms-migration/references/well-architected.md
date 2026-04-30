# Well-Architected Notes — Dynamic Forms Migration

## Relevant Pillars

- **User Experience** — Dynamic Forms enables fine-grained, context-aware record pages: fields appear or hide based on record type, field values, user attributes, or device. The traditional model required separate Page Layouts per record type (and per profile in some cases), which fragmented the user experience and made the page feel different across personas. Dynamic Forms unifies the canvas while still differentiating content — users see the same layout structure with the right content for their context. This consistency improves discoverability and reduces training overhead.

- **Operational Excellence** — Dynamic Forms collapses N page layouts (one per record type, sometimes per profile) into one Lightning Record Page with N visibility rules. For an org with 5 record types each with their own layout, that's 5 layouts to maintain → 1 page with 5 visibility rules. Adding a new field requires placing one component instead of editing 5 layouts. The administrative surface shrinks substantially, and changes propagate consistently because there's a single source of truth for the record page.

- **Security** — Dynamic Forms cleanly separates UI organization (what's on the page) from data security (Field-Level Security). Done correctly, this clarifies the security model: FLS controls access; Dynamic Forms controls layout. Done incorrectly, it conflates the two — admins use Dynamic Forms visibility as a security control and leave FLS misconfigured. The migration is the moment to audit FLS independently and use Dynamic Forms purely as a UX layer. This separation of concerns improves auditability and makes the security model legible.

## Architectural Tradeoffs

**One page with visibility rules vs multiple pages per record type:** Single page is the default — it captures the consolidation benefit of Dynamic Forms. Multiple pages become necessary when the unique-field count per record type exceeds ~30 fields, or when entire components (related lists, custom LWCs) differ. The tradeoff: single page concentrates the visibility logic in one place (auditable, but complex); multiple pages distribute the logic across page assignments (simpler per-page, but harder to maintain consistency across pages). Choose single until complexity justifies the split.

**Custom Permissions vs profile-name strings for visibility:** Custom Permissions are stable identifiers, assignable via Permission Sets, and decouple visibility from profile naming. Profile name strings are more direct but brittle — a profile rename silently breaks the rule. Custom Permissions add upfront definition cost (one metadata file per permission) but pay back the first time a profile is renamed or a permission needs to apply across profiles. Default to Custom Permissions for any non-trivial visibility logic.

**Aggressive Page Layout decommissioning vs retention:** Page Layouts remain authoritative for Quick Action input fields, Print View, and Salesforce Classic users. Aggressive decommissioning ("delete all old layouts!") breaks these surfaces. The well-architected outcome is: retain at least one minimal Page Layout per record type, reduce its content to standard fields only, accept that dual-management of Compact Layout / Page Layout / Dynamic Forms is the steady state. Don't force the org to a "Dynamic Forms only" state that Salesforce doesn't support.

**FLS audit timing — pre vs post migration:** Pre-migration FLS audit means migration starts from a known good state and Dynamic Forms visibility cleanly layers on top. Post-migration audit conflates FLS issues with visibility-rule issues and complicates debugging. Pre-migration audit is the right answer; the migration is also a good moment to consolidate FLS via Permission Sets / Permission Set Groups if the org still relies on Profile-level FLS.

## Anti-Patterns

1. **Treating Dynamic Forms visibility as a security control.** Visibility rules are UI-only. The field is still accessible via API, reports, list views, and formulas. Using visibility rules to "hide sensitive data" creates false confidence and a real data exposure surface. Always pair visibility rules with appropriate FLS for any field that must be inaccessible to a user.

2. **Combining `required=true` with visibility rules on the same component.** This produces save failures with confusing error messages — the user can't see the field but is told it's required. Either always show required fields or use validation rules with explicit conditional logic.

3. **One Lightning Record Page per Record Type as the default architecture.** Re-creates the proliferation Dynamic Forms was designed to eliminate. Default to ONE page with visibility rules; split only when complexity exceeds rule manageability.

4. **Skipping the Compact Layout review.** Compact Layouts drive the Highlights Panel, which is visually part of the record page but architecturally separate. Migration plans that omit Compact Layout review leave the Highlights Panel showing stale or wrong fields.

5. **Forgetting Quick Action layouts are still page-layout-driven.** Quick Action input fields reference the Quick Action section of the Page Layout, NOT the Dynamic Forms record page. Adding a Quick Action after migration requires editing the Page Layout's Quick Action section. Document this dual-management.

6. **Profile-name string visibility rules.** Brittle and break silently on profile rename. Use Custom Permissions for stable identification.

7. **Production-first migration without user-preview window.** Auto-conversion is reliable for layout structure; it cannot validate UX. Run a 1–2 week sandbox preview with real users from each affected profile before production cutover.

## Official Sources Used

- Dynamic Forms Help — https://help.salesforce.com/s/articleView?id=sf.dynamic_forms_overview.htm
- Migrate to Dynamic Forms — https://help.salesforce.com/s/articleView?id=sf.dynamic_forms_migrate.htm
- Lightning App Builder Help — https://help.salesforce.com/s/articleView?id=sf.lightning_app_builder_overview.htm
- Component Visibility Rules — https://help.salesforce.com/s/articleView?id=sf.lightning_app_builder_filters.htm
- Custom Permissions — https://help.salesforce.com/s/articleView?id=sf.custom_perms_overview.htm
- Page Layouts and Field-Level Security — https://help.salesforce.com/s/articleView?id=sf.fls_about_field_level_security.htm
- Compact Layouts — https://help.salesforce.com/s/articleView?id=sf.compact_layout_overview.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
