# Well-Architected Notes — LWC App Builder Config

## Relevant Pillars

- **Operational Excellence** — meta.xml is how admins (not developers) interact with the component over time. Clear `masterLabel`, helpful `description` tooltips, sane defaults, and surface-scoped `targetConfig` blocks reduce admin error, shorten enablement, and cut "why isn't this component doing what I expected" tickets.
- **Reliability** — `<objects>` on record-page targets prevents admins from dropping the component on incompatible sObjects, which would otherwise produce runtime errors or silently broken UI. Correct `<supportedFormFactors>` prevents a desktop-only layout from rendering on phones. Required-flagging forces admins to supply the inputs the component needs to function.
- **Security** — design attributes exposed to admins can drive which records, fields, or Apex callables the component touches. Datasource Apex classes run in user context when the admin opens the property panel, and they must apply CRUD/FLS checks when enumerating schema. Leaking admin-only options (debug toggles, internal mode strings) to Experience Cloud admins is a real attack surface.

## Architectural Tradeoffs

- **One bundle, many surfaces vs. one bundle per surface.** A single bundle with per-target `targetConfig` blocks is efficient, but only when the component's JS is genuinely generic. As soon as surface-specific branching fills the JS, split the bundle. See the "Swiss-Army-Knife" anti-pattern in `examples.md`.
- **Static CSV datasource vs. Apex `DynamicPickList`.** Static is zero-runtime-cost and fine for truly stable lists (severity levels, T-shirt sizes). Dynamic Apex lists cost an Apex invocation each time the property panel opens, but they reflect schema changes without a deploy.
- **Permissive exposure vs. strict scoping.** Leaving off `<objects>` is faster to ship but invites misplacement. Scoping up front is cheaper than un-scoping a misused component later.

## Anti-Patterns

1. **Shipping a record-page component with no `<objects>` scope.** Admins drop it on Case, Lead, or Contact and it fails at runtime or shows the wrong data. The fix ("add an `<objects>` element") is trivial, but once the component is placed on 30 pages, removing it from the wrong ones is a cleanup project.

2. **Using design attributes to hide debug or feature-flag toggles.** A `<property name="enableRawLogging" type="Boolean" default="false"/>` visible to every admin is both a support risk (admins flip it and flood logs) and a security concern in Experience Cloud contexts. Use custom metadata or permission-gated logic instead of admin-facing toggles.

3. **Relying on `default` values instead of handling unset props in JS.** Defaults arrive as strings and only apply when the admin leaves the field blank. Components that assume `this.maxRows === 5` will break when admins set `"5 "` (with a trailing space) or when a future meta.xml change renames the property. Always validate and cast design-attribute values on read.

## Official Sources Used

- LWC Configuration Tags Reference — https://developer.salesforce.com/docs/platform/lwc/guide/reference-configuration-tags.html
- LWC `targets` Reference — https://developer.salesforce.com/docs/platform/lwc/guide/reference-targets.html
- LWC `targetConfig` Reference — https://developer.salesforce.com/docs/platform/lwc/guide/reference-target-config.html
- LWC `objects` Reference — https://developer.salesforce.com/docs/platform/lwc/guide/reference-objects.html
- LWC `supportedFormFactors` Reference — https://developer.salesforce.com/docs/platform/lwc/guide/reference-supportedformfactors.html
- LWC `js-meta.xml` Reference — https://developer.salesforce.com/docs/platform/lwc/guide/js-meta-xml.html
- LWC Best Practices — https://developer.salesforce.com/docs/platform/lwc/guide/get-started-best-practices.html
