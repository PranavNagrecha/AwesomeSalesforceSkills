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

Dynamic Forms pages with many individually-placed field components and numerous visibility filter conditions can be slower to render than page-layout-backed pages, particularly on older devices or slow connections. There is also a hard structural ceiling: the Metadata API Developer Guide states that a Lightning page region can contain up to 100 components, and converting a page layout turns one detail component into one item per field. Split wide objects across sections, columns, and tab facets rather than one region, and hand the render-cost question to `admin/lightning-page-performance-tuning` — its measurement discipline (EPT at P75, tab-deferred components, related-list variants) is the right instrument, and its gotcha 5 is the load-bearing point here: Dynamic Forms improves performance only when fields are conditionally hidden.

## Anti-Patterns

1. **Using Dynamic Forms visibility filters as a substitute for FLS** — Hiding a field using a Dynamic Forms filter while leaving FLS open to the profile means the field is still accessible via API, reports, and list views. This is not security; it is cosmetic. Always enforce FLS at the permission level for sensitive fields.

2. **Enabling Dynamic Forms in production without a sandbox migration rehearsal** — The "Upgrade Now" wizard behavior depends on the page layout currently assigned to the page. Running it in production without first validating in a sandbox risks wiping all fields from the record page for users assigned to that activation. Validate the migration sequence end-to-end in a sandbox first.

3. **Mixing Dynamic Actions and page layout action overrides on the same page** — When Dynamic Actions is enabled, the action source should be exclusively the Lightning record page (Dynamic Actions components). Leaving actions on both the page layout and the Dynamic Actions canvas causes duplicate entries and unpredictable visibility behavior. Commit fully to Dynamic Actions for the object or do not enable it.

4. **Building separate Lightning record pages per record type instead of using visibility filters** — Some orgs create a distinct Lightning record page for each record type to show different fields. This is the page-layout problem reproduced at the page level. One Dynamic Forms-enabled page with per-record-type visibility filters is the correct pattern.

## Official Sources Used

- Metadata API Developer Guide — **FlexiPage** and its subtypes (https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf) — supplies the whole page structure quoted in `references/metadata-examples.md`: `flexiPageRegions` / `itemInstances` / `componentInstance` / `fieldInstance`, the `type` enumeration containing `RecordPage`, `sobjectType` being unchangeable once set, `identifier` (required from API 53.0, 120-character cap), and the *"available only on Lightning Pages that have enabled Dynamic Forms"* qualifier on `FieldInstance` (Core Concepts; metadata-examples §1).
- Metadata API Developer Guide — **FieldInstanceProperty**, **UiFormulaRule**, **UiFormulaCriterion** (same PDF) — the two valid property names `uiBehavior` (API 49.0+) and `conditionalFormatRuleset` (API 62.0+), the `uiBehavior` values `None` / `Readonly` / `Required`, the closed operator set `CONTAINS` / `EQUAL` / `NE` / `GT` / `GE` / `LE` / `LT`, `booleanFilter`, the five `leftValue` expression contexts including `{!$Client.FormFactor}` and `{!$Permission.CustomPermission.<name>}`, and the *"no more than five fields"* expression span limit (Visibility Filters table; gotcha 7; the checker's span and operator checks).
- Metadata API Developer Guide — **FlexiPageRegion** and **ComponentInstanceProperty** (same PDF) — *"A Lightning page region can contain up to 100 components"*, the 10,000-character `ComponentInstanceProperty` cap, and the `Region` / `Facet` / `Background` region types (gotcha 10; the checker's region-size check).
- Metadata API Developer Guide — **ActionOverride** and **ActionOverrideType** (same PDF) — `type` = `flexipage` being *"only valid for the View action in Lightning Experience"*, the `formFactor` semantics where `Large` is Lightning Experience desktop, `Small` is the mobile app, and no value means Salesforce Classic, and the instruction that *"You can't delete ActionOverrides by deploying with destructiveChange.xml"* (metadata-examples §2 and §6; gotcha 8).
- Metadata API Developer Guide — **CustomApplication**, **AppProfileActionOverride**, and the **ProfileActionOverride** summary (same PDF) — the precedence statement *"a matching ProfileActionOverride assignment takes precedence over existing overrides"*, `recordType` being required when `actionName` is `View`, `profile` being the only identity qualifier, and the sample app definition the §3 excerpt is shaped from (metadata-examples §3; Decision Guidance).
- Metadata API Developer Guide — **DynamicFormsSettings** and **RecordPageSettings** (same PDF) — `enableFormsOnMobile` (API 58.0+, marked a Beta Service) and `RecordPageSettings.enableDynamicForms` being *"Removed in API version 50.0 and later"* (gotchas 6 and 9; metadata-examples §4).
- Object Reference for the Salesforce Platform (https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf) — searched for a `FlexiPage` standard object and found none, which is what the UNVERIFIED marker on the Tooling API query in metadata-examples §7 rests on.
- `trailheadapps/dreamhouse-lwc` sample record page, as verified and cited by `admin/lightning-record-page-configuration` — the source for the component names `flexipage:fieldSection` (with `columns`), `flexipage:column` (with `body`), `force:highlightsPanel`, and the template `flexipage:recordHomeTemplateDesktop` used in metadata-examples §1.
- Dynamic Forms (Lightning App Builder) — https://help.salesforce.com/s/articleView?id=sf.lightning_app_builder_dynamic_forms.htm (the object-support list referenced in gotcha 3, which is why that gotcha carries an UNVERIFIED marker — this page cannot be fetched offline).
- Dynamic Actions (Lightning App Builder) — https://help.salesforce.com/s/articleView?id=sf.lightning_app_builder_dynamic_actions.htm (the field-section-versus-field rule evaluation timing quoted in Core Concepts).
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html (the pillar framing in this file).
- Field-Level Security — https://help.salesforce.com/s/articleView?id=sf.admin_fls.htm (gotcha 2 and the Security pillar note: visibility rules render, FLS authorises).
- Enhancing Dynamic Pages with Visibility Rules (Trailhead, Lightning App Builder module) — https://trailhead.salesforce.com/content/learn/modules/lightning_app_builder/add-visibility-rules-for-dynamic-pages-lab (the Common Patterns walkthroughs).
