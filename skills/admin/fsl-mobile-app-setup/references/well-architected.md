# Well-Architected Notes — FSL Mobile App Setup

## Relevant Pillars

- **Reliability** — The core challenge of FSL Mobile is ensuring technicians have access to the right data when they are offline and that data written offline is durably synced back to the org. Offline priming strategy, page reference budgets, and conflict resolution policies are all reliability concerns. A misconfigured priming setup results in technicians missing records mid-job with no recovery path until they regain connectivity.

- **Performance** — Priming sync time and device storage are constrained resources. Priming configurations that pull too many related lists or too wide a scheduling window increase sync time and device storage consumption. Poor performance in priming directly delays technician readiness, especially in environments with weak cellular coverage.

- **Security** — FSL Mobile downloads Salesforce records onto physical devices held by field workers. Devices can be lost or stolen. Security considerations include: ensuring mobile device management (MDM) policies are applied, confirming the FSL Mobile connected app enforces IP restrictions or MFA where required, and validating that offline data does not persist beyond the authorized session. Apex REST endpoints used by HTML5 extensions must enforce standard FLS and sharing rules — they do not inherit any mobile-specific security shortcut.

- **Operational Excellence** — FSL Mobile deployments require ongoing monitoring of priming health as data volumes grow. Teams should document the priming design, the page reference budget, and the extension architecture so future admins do not inadvertently add related lists that push the configuration over the silent 1,000-reference limit.

## Architectural Tradeoffs

**Priming window width vs. data completeness:** A wider scheduling window (e.g., 7 days) gives technicians more forward visibility but increases page reference counts and sync time. A narrow window (e.g., 1 day) keeps priming lean but means a technician who works early in the morning may not have afternoon appointments if the sync hasn't run yet. Choose the window based on technician work patterns and page reference budget.

**LWC Quick Action vs. HTML5 Extension Toolkit:** LWC actions are simpler, use LDS for offline data queuing, and are the strategic direction. HTML5 extensions offer lower-level DOM control and may be necessary for complex multi-step UI patterns or existing investments. New extensions should always start with LWC. Migrating existing HTML5 extensions carries risk unless there is budget and test coverage for the replacement.

**Custom branding vs. standard branding:** Custom branding through Mobile App Plus improves technician trust and app recognition, especially in white-label or partner scenarios. However, it requires an add-on license and republishing the connected app. Do not commit to custom branding in a project timeline without confirming the license is provisioned.

## Anti-Patterns

1. **Over-priming related lists without counting page references** — Adding every possible related list to the priming config in the name of "complete offline coverage" without tracking the total page reference count. This predictably exceeds the 1,000-reference limit in high-volume territories, producing silent record loss. Instead, audit page reference budgets before each new related list is added and enforce the 1,000 limit as a hard project constraint.

2. **Using the HTML5 Mobile Extension Toolkit for all new extensions** — Defaulting to the HTML5 toolkit because it was the only option in older FSL implementations, even for new development where LWC quick actions are fully capable. HTML5 extensions require Apex REST boilerplate, cannot use LDS, and do not benefit from platform offline data queuing. All new extensions should evaluate LWC quick actions first.

3. **Configuring FSL Mobile through the standard Salesforce Mobile surface** — Spending time building App Manager configurations, Briefcase rules, or standard mobile navigation expecting them to affect FSL Mobile. This produces no effect on FSL Mobile and delays actual delivery.

## Official Sources Used

- Field Service Mobile App — Field Service Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.field_service_dev.meta/field_service_dev/fsl_mobile_intro.htm
- Create App Extensions — Salesforce Help — https://help.salesforce.com/s/articleView?id=sf.fs_mobile_app_extensions.htm
- Configure Deep Linking — Field Service Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.field_service_dev.meta/field_service_dev/fsl_mobile_deep_links.htm
- Offline Priming — Salesforce Help — https://help.salesforce.com/s/articleView?id=sf.fs_mobile_offline_priming.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Object Reference — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_concepts.htm
- Metadata API Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_intro.htm
