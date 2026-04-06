# Well-Architected Notes — Lightning App Builder Advanced

## Relevant Pillars

- **Security** — Visibility filters are cosmetic display controls, not security enforcement. FLS, object permissions, and sharing rules must enforce all data access independently of what the LAB canvas shows or hides. Treating visibility rules as security gates creates a false sense of protection that does not survive API access.
- **Performance Efficiency** — Salesforce documents a guideline of 8 or fewer visible components per region on mobile form factors. Exceeding this causes cascade-loading delays on Phone form factor. Use formula fields for complex conditions rather than stacking 10 visibility conditions per component — formula evaluation is batched server-side and more efficient than multiple client-side filter evaluations.
- **Operational Excellence** — Custom page templates (Aura `lightning:template`) and Dynamic Forms configurations are stored as FlexiPage metadata. These should be version-controlled, deployed through change sets or SFDX, and tested in sandbox before production activation. LAB page changes remain in draft until explicitly activated, which gives a safe staging window.

## Architectural Tradeoffs

**Visibility filters vs. multiple page layouts:** Visibility filters on a single page are easier to maintain than managing multiple page layout assignments across profiles and record types. However, they are limited to 10 conditions per component and cannot reference related-object fields. The break-even point is roughly 3+ page variants driven by the same object — at that point a single Dynamic Forms page with formula-field proxies is usually cleaner than maintaining 3 layouts.

**Dynamic Actions vs. code-driven action visibility:** Dynamic Actions covers the most common conditional action cases declaratively. Custom Lightning actions with Apex controllers that check conditions programmatically can handle more complex logic but require code maintenance. Prefer Dynamic Actions unless the condition cannot be expressed as a field value, profile, permission, or record type filter.

**Custom page templates vs. standard templates:** Custom Aura templates give full control over region layout (columns, widths, maxComponents per region) but require code deployment and cannot be edited in LAB itself. Standard templates cover the majority of use cases. Use custom templates only when a genuinely unsupported layout configuration is required by the business.

## Anti-Patterns

1. **Using visibility filters as security enforcement** — Hiding a component or field via a LAB filter does not prevent API access to that data. This anti-pattern creates compliance risk in regulated orgs. Always pair visibility decisions with proper FLS configuration.
2. **Enabling Dynamic Actions without cleaning up page-layout action assignments** — Results in duplicate action buttons visible to users, causing confusion and support tickets. The cleanup step (removing page-layout action sections from assigned layouts) must happen before or immediately after Dynamic Actions activation.
3. **Building complex cross-field visibility inline in LAB** — Stacking 8–10 visibility conditions with multiple field-value comparisons is brittle. The conditions are not testable in isolation, and a field rename or picklist change silently breaks them. Formula fields used as visibility proxies are testable, documented in the object schema, and maintainable without opening LAB.

## Official Sources Used

- Lightning App Builder — Limits and Considerations: https://help.salesforce.com/s/articleView?id=sf.lightning_app_builder_limits_considerations.htm
- Set Visibility Rules for a Lightning Page Component: https://help.salesforce.com/s/articleView?id=sf.lightning_app_builder_components_visibility.htm
- LWC Developer Guide — Configure a Component for Lightning App Builder: https://developer.salesforce.com/docs/component-library/documentation/en/lwc/use_config_for_app_builder
- Dynamic Forms — Considerations: https://help.salesforce.com/s/articleView?id=sf.dynamic_forms_considerations.htm
- Dynamic Actions — Considerations: https://help.salesforce.com/s/articleView?id=sf.lightning_app_builder_dynamic_actions_considerations.htm
- Create and Configure Custom Lightning Page Templates: https://help.salesforce.com/s/articleView?id=sf.lightning_app_builder_template_create.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
