# Well-Architected Notes — Picklist and Value Sets

## Relevant Pillars

- **Operational Excellence** — Picklist value sets are a governance surface. Choosing Global Value Sets where values must stay synchronized across objects reduces administrative overhead and risk of drift. Documenting the decision (local vs GVS) and the Replace/Deactivate/Delete process protects against data loss from hasty cleanup.
- **Reliability** — Dependent picklist dependencies are not enforced by the API. Adding a Validation Rule as a supplementary enforcement layer ensures the intended data model constraint holds regardless of how records are created or updated. Deactivating rather than deleting values preserves historical record integrity.

## Architectural Tradeoffs

**Global Value Set vs Object-Local**

Global Value Sets reduce maintenance cost when values must stay in sync across multiple objects. The tradeoff is reduced flexibility: deactivating a value immediately affects all fields sharing the GVS, and there is no per-field override. Object-local picklists are more flexible but require manual synchronization when values diverge.

**Recommendation:** Use Global Value Sets for organization-wide classification schemes (Region, Industry, Product Line, Status). Use object-local picklists when the field's values are specific to one object's lifecycle (e.g. Case Status has different valid values than Opportunity Stage — these should not share a GVS even though both are "status" concepts).

**Dependent Picklist vs Validation Rule**

Field Dependencies provide UI-level filtering without any custom code — low cost, good UX. They do not enforce at the API level. Validation Rules enforce at all write paths (UI, API, Apex, Flow) but require authoring and maintenance as the picklist values change.

**Recommendation:** Always use the field dependency for UX. Add a Validation Rule when the combination enforcement is a data integrity requirement (not just a UX nicety). Document the rule's picklist value assumptions so it gets updated when values are added or retired.

## Anti-Patterns

1. **Deleting picklist values without auditing record counts first** — Deleting a value immediately nulls all records carrying that value, with no undo. Always run a report to confirm zero records before deleting. Use Deactivate by default; only Delete when confirmed safe.

2. **Using a Global Value Set for object-specific lifecycle statuses** — Sharing a "Status" GVS across Case, Opportunity, and Lead seems to save time, but these objects have independent lifecycle requirements. Adding "In Review" for Cases automatically exposes it on Opportunities and Leads, confusing users. Model lifecycle statuses as object-local picklists; share only true org-wide classification schemes via GVS.

3. **Relying on the dependent picklist matrix as the sole data integrity control** — The dependency is UI-only. Any programmatic write bypasses it. Treating it as a sufficient guard without a companion Validation Rule leaves API-sourced data unconstrained.

## Official Sources Used

- Salesforce Help — Picklist Limitations: https://help.salesforce.com/s/articleView?id=platform.picklist_limitations.htm&language=en_US&type=5
- Salesforce Help (KB 000386685) — Increase Salesforce Multi-Select Picklist Values Limit: https://help.salesforce.com/s/articleView?id=000386685&type=1 — default and maximum are both 500 values; orgs below 500 can request an increase up to 500; "the maximum number of selectable values at one time is limited to 100 and cannot be increased"
- Salesforce Help — Create a Global Picklist Value Set: https://help.salesforce.com/s/articleView?id=platform.fields_creating_global_picklists.htm&language=en_US&type=5
- Salesforce Help — Dependent Picklist Considerations: https://help.salesforce.com/s/articleView?id=platform.fields_dependent_field_considerations.htm&language=en_US&type=5
- Salesforce Help — Define a Dependent Picklist (Field Dependencies): https://help.salesforce.com/s/articleView?id=platform.fields_defining_field_dependencies.htm&language=en_US&type=5
- Salesforce Help — Replace Picklist Values: https://help.salesforce.com/s/articleView?id=platform.customize_replace.htm&language=en_US&type=5
- Salesforce Help — Deactivate, Reactivate, or Remove a Picklist Value: https://help.salesforce.com/s/articleView?id=platform.fields_deactivate_reactivate_values.htm&language=en_US&type=5
- Salesforce Help — Edit Picklists for Record Types: https://help.salesforce.com/s/articleView?id=platform.editing_picklists_for_record_types_and_business_processes.htm&language=en_US&type=5
- Salesforce Help — Bulk Manage Picklist Values (GA): https://help.salesforce.com/s/articleView?id=release-notes.rn_forcecom_fields_bulk_manage_picklist_values.htm&language=en_US&release=238&type=5
- Salesforce Help — Increase multi-select picklist limit (KA 000386685): https://help.salesforce.com/s/articleView?id=000386685&language=en_US&type=1
- Salesforce Developer Limits & Allocations — Picklist: https://developer.salesforce.com/docs/atlas.en-us.salesforce_app_limits_cheatsheet.meta/salesforce_app_limits_cheatsheet/salesforce_app_limits_picklist.htm
- Metadata API Developer Guide — GlobalValueSet: https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_globalvalueset.htm
- Salesforce Well-Architected Overview: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html

### Metadata and API sources used for `references/metadata-examples.md` and gotchas 9–14

Salesforce Metadata API Developer Guide (Summer '26 / v62 PDF):
https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf

- `GlobalValueSet` type — file suffix, folder, `masterLabel` / `customValue` / `sorted` / `description`, the 1,000-value ceiling, the sample definition, the `__gvs` developer-name suffix from API 57.0, and wildcard support in `package.xml` (metadata-examples §1, §7; Gotcha 14)
- `CustomValue` type — `fullName` / `label` / `default` / `isActive` / `color` / `description`, the "values missing from a component definition get deactivated when deployed" rule, and the retrieve asymmetry between global and non-global unrestricted picklists (metadata-examples §1; Gotchas 9 and 10)
- `StandardValue` type — the stage-specific `forecastCategory` enum and `probability`, plus `closed` for Case and Task Status, `converted` for Lead Status, `won` for Opportunity Stage (metadata-examples §3, §4; Gotcha 12)
- `StandardValueSet` type — file suffix and folder, "must contain at least one picklist value", the record-type visibility note for values loaded through the Metadata API, and the absence of wildcard support (metadata-examples §3, §7; Gotchas 5 and 11)
- `ValueSet` / `ValueSetValuesDefinition` / `ValueSettings` types — `restricted`, `valueSetName` vs `valueSetDefinition`, `controllingField`, and "you can add field dependency values via the Metadata API but not remove them" (metadata-examples §2, §6; Gotcha 13)
- `CustomField` → `valueSet` — "a custom picklist that uses a global value set is restricted" and "either a valueSetDefinition or a valueName specified, but never both" (metadata-examples §2; checker ERROR and WARN)
- `GlobalValueSetTranslation` / `ValueTranslation` — file naming, `masterLabel` as the pairing key, and the untranslated-value comment convention (metadata-examples §5)
- Appendix C, StandardValueSet Names and Standard Picklist Fields — the field-name-to-set-name mapping (`Opportunity.StageName` → `OpportunityStage`, `Case.Status` → `CaseStatus`, `Lead.Status` → `LeadStatus`, `Account.Industry` → `Industry`), case sensitivity, and footnotes 2 and 3 for sets that cannot be inserted/deleted or read at all (metadata-examples §7; Gotcha 11)

Salesforce Object Reference (Summer '26 / v62 PDF):
https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf

- Picklist Field Type — "the API doesn't enforce the list of values for advisory (unrestricted) picklist fields on `create()` or `update()`", the inactive-value-on-insert behaviour, and "always use the value when inserting or updating a field. The `query()` call always returns the value, not the label" (Questions to Ask; Gotcha 3; metadata-examples §1)
- Field property glossary, "Restricted picklist" — "a picklist whose values are restricted to those values defined by a Salesforce admin. Users can't load unapproved values through the API" (Core Concepts; checker WARN on unrestricted global-set-backed fields)

Salesforce Apex Reference Guide (Summer '26 / v62 PDF):
https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/apexrefguide.pdf

- `Schema.DescribeFieldResult` — `getPicklistValues()` ("only active picklist values are returned"), `isRestrictedPicklist()`, `isDependentPicklist()`, `getController()` (metadata-examples §9 verification)
- `Schema.PicklistEntry` — `getLabel()`, `getValue()`, `isActive()`, `isDefaultValue()` and "only one item in a picklist can be designated as the default" (metadata-examples §9; checker ERROR on multiple defaults)

Not used, and why: the Salesforce Developer Limits and Allocations Quick Reference
(`salesforce_app_limits_cheatsheet`) has no picklist section in the Summer '26 edition, so the
1,000-value and 500-value figures in `SKILL.md` continue to rest on the Salesforce Help articles
listed above rather than on the cheat sheet.
