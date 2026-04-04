# Well-Architected Notes — Dynamic Forms and Dynamic Actions

## Relevant Pillars

- **User Experience** — Dynamic Forms is directly a UX tool. The core goal is to reduce cognitive load on record pages by surfacing only the fields and actions relevant to the current record context and user. Well-architected UX in Salesforce means users see what they need, when they need it, without clutter. Dynamic Forms is the primary no-code mechanism for achieving this on Lightning record pages.

- **Operational Excellence** — A single Dynamic Forms-enabled page replaces multiple page layout variants, reducing the number of artifacts to maintain. Fewer layouts means fewer sync failures when new fields are added. Operational Excellence demands that configuration drift be minimized — Dynamic Forms directly reduces one of the most common sources of admin drift in maturing orgs.

- **Security** — Dynamic Forms visibility rules must never be treated as a security control. The Well-Architected security principle of "least privilege" must be enforced at the FLS and sharing layer. Dynamic Forms can complement a secure design by hiding sensitive fields from the UI for users who should not see them, but this must be in addition to — not instead of — FLS restrictions.

## Architectural Tradeoffs

**Consolidation vs. Compatibility**

Dynamic Forms consolidates multiple page layouts into a single record page with conditional field visibility. The tradeoff is object support: not all standard objects support Dynamic Forms. Orgs with a mix of supported and unsupported objects must maintain two parallel configuration patterns — Dynamic Forms for some objects, page layouts for others. This dual-pattern state adds cognitive overhead for admins.

**Declarative Flexibility vs. Edge Case Coverage**

Dynamic Forms visibility filters cover the most common conditions (field value, profile, permission, record type, device). Complex multi-condition logic or conditions that depend on related records or aggregated values cannot be expressed in Dynamic Forms filters without a workaround (e.g., a helper formula field). When the logic is sufficiently complex, a custom LWC component may be a better architectural fit than a heavily filtered Dynamic Forms page.

**No-Code Speed vs. Performance on Large Pages**

Dynamic Forms pages with many individually-placed field components and numerous visibility filter conditions can be slower to render than page-layout-backed pages, particularly on older devices or slow connections. For objects with very large record pages (100+ fields), profile the rendered performance before rolling out broadly.

## Anti-Patterns

1. **Using Dynamic Forms visibility filters as a substitute for FLS** — Hiding a field using a Dynamic Forms filter while leaving FLS open to the profile means the field is still accessible via API, reports, and list views. This is not security; it is cosmetic. Always enforce FLS at the permission level for sensitive fields.

2. **Enabling Dynamic Forms in production without a sandbox migration rehearsal** — The "Upgrade Now" wizard behavior depends on the page layout currently assigned to the page. Running it in production without first validating in a sandbox risks wiping all fields from the record page for users assigned to that activation. Validate the migration sequence end-to-end in a sandbox first.

3. **Mixing Dynamic Actions and page layout action overrides on the same page** — When Dynamic Actions is enabled, the action source should be exclusively the Lightning record page (Dynamic Actions components). Leaving actions on both the page layout and the Dynamic Actions canvas causes duplicate entries and unpredictable visibility behavior. Commit fully to Dynamic Actions for the object or do not enable it.

4. **Building separate Lightning record pages per record type instead of using visibility filters** — Some orgs create a distinct Lightning record page for each record type to show different fields. This is the page-layout problem reproduced at the page level. One Dynamic Forms-enabled page with per-record-type visibility filters is the correct pattern.

## Official Sources Used

- Dynamic Forms (Lightning App Builder) — https://help.salesforce.com/s/articleView?id=sf.lightning_app_builder_dynamic_forms.htm
- Dynamic Actions (Lightning App Builder) — https://help.salesforce.com/s/articleView?id=sf.lightning_app_builder_dynamic_actions.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Field-Level Security — https://help.salesforce.com/s/articleView?id=sf.admin_fls.htm
