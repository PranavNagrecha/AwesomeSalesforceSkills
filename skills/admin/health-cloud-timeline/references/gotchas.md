# Gotchas — Health Cloud Timeline

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Category Name Mismatch Silently Drops Timeline Entries

**What happens:** When a `TimelineObjectDefinition` references a `timelineCategory` value that does not exactly match an active category configured in Setup > Timeline > Categories, the records from that object silently disappear from the timeline. No error is raised at deployment time, no warning appears in the component, and no debug log surfaces the mismatch. From the end user's perspective, the object simply "does not appear on the timeline."

**When it occurs:** Most commonly after a deployment where someone updated category labels in Setup without updating the corresponding `TimelineObjectDefinition` metadata (or vice versa). Also occurs after org refreshes where categories are manually recreated in the destination org with slightly different capitalization or spacing.

**How to avoid:** Treat timeline category names as a contract between Setup and metadata. Keep a canonical list of category values in source control alongside the `TimelineObjectDefinition` files. After any deployment, open Setup > Timeline > Categories and visually compare against the `timelineCategory` values in all `TimelineObjectDefinition` files. Automate this check using `scripts/check_health_cloud_timeline.py`.

---

## Gotcha 2: Legacy Component Deprecation Has No Org-Level Warning

**What happens:** The legacy `HealthCloud.Timeline` managed-package component continues to function in orgs that have it installed even after Salesforce deprecated it. Salesforce does not inject an admin warning, a deprecation notice on the component, or any automated migration prompt. Orgs only discover the deprecation when they encounter a bug that support will not fix, when a new seasonal Health Cloud release breaks the component behavior, or when consulting with a Salesforce TAM.

**When it occurs:** Any org provisioned with Health Cloud prior to Health Cloud v236 (Summer '22) and that has not proactively migrated. The risk is highest for orgs on multi-year implementation timelines that have not revisited the timeline configuration since initial go-live.

**How to avoid:** Audit all patient and member page layouts for the presence of the `HealthCloud.Timeline` component. If found, schedule a migration sprint to replace it with the Industries Timeline + `TimelineObjectDefinition` metadata. The migration guide in `references/examples.md` covers the standard objects. Do not add new configuration to the legacy component; invest only in the Industries Timeline path.

---

## Gotcha 3: Objects Without an Account Lookup Cannot Appear — No Partial Workaround Exists

**What happens:** The Industries Enhanced Timeline anchors exclusively to the patient's Account record. If a custom or standard object has only a Contact lookup (or a lookup to Case, Opportunity, or any other non-Account object), it cannot be surfaced on the timeline regardless of any workaround. Attempts to use formula fields, custom metadata, or flow-based cross-object references to simulate an Account relationship do not satisfy the component's query requirement.

**When it occurs:** When implementing Health Cloud on an org that previously had a Contact-centric data model (e.g., a B2C CRM org converted to Health Cloud). Clinical objects designed before Person Account enablement often have `ContactId` lookups rather than `AccountId` lookups. Custom objects built by third-party ISV packages may also lack Account lookups.

**How to avoid:** Before writing any `TimelineObjectDefinition`, trace the relationship from the target object to Account. If no direct path exists, evaluate adding an Account lookup field to the object. For objects with existing data, this requires a data migration to populate the new Account field. Plan this schema change early — retrofitting Account lookups onto production objects with millions of records requires careful planning and a maintenance window.

---

## Gotcha 4: API Version Below v55.0 Causes Silent Metadata Deployment Failure

**What happens:** `TimelineObjectDefinition` is a metadata type introduced at Salesforce API v55.0. If a project's `sfdx-project.json` specifies `"sourceApiVersion": "54.0"` or earlier, SFDX will either throw an unrecognized metadata type error or silently skip the files during deployment. The component renders an empty timeline with no error message.

**When it occurs:** In orgs migrating from older SFDX project configurations, orgs running tooling generated before Spring '22, or scratch org definitions copied from an older template.

**How to avoid:** Verify `"sourceApiVersion"` in `sfdx-project.json` is `"55.0"` or higher before deploying `TimelineObjectDefinition` metadata. Use `sf project deploy start --dry-run` to catch metadata type recognition errors before a production deployment.

---

## Gotcha 5: TimelineObjectDefinition Is Org-Wide — No Record Type Scoping

**What happens:** Once a `TimelineObjectDefinition` is active, its object's records appear on every instance of the Industries Timeline component in the org, across all page layouts that include it. There is no mechanism to scope a definition to a specific record type, page layout, or user profile at the `TimelineObjectDefinition` level. An object configured for the "Pediatric Encounter" timeline will also appear on the "Adult Member" timeline if both pages use the same component.

**When it occurs:** In multi-LOB orgs where different business units share one Health Cloud org but need different timeline views for their patient populations (e.g., a payer org with both clinical and member service use cases on different record types).

**How to avoid:** Use the timeline category filter to separate entries by type and train users to apply the appropriate filters. For strict separation, create separate page layouts with Industries Timeline components configured with different default category filters. If the requirement is truly disjoint (object X should never appear for patient type Y), reconsider the data model — the object may need to be scoped at the record level with appropriate sharing rules rather than hidden at the component level.
