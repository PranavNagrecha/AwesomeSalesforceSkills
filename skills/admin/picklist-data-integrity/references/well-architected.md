# Well-Architected Notes — Picklist Data Integrity

## Relevant Pillars

- **Reliability** — Restricted picklists are a data-quality control
  worth the integration friction they impose. Unrestricted plus
  periodic reconciliation is acceptable; Unrestricted with no
  reconciliation produces phantom values that distort reports for
  months before anyone notices.
- **Operational Excellence** — Pattern C (migrate before
  deactivate) is the highest-leverage operational discipline in
  picklist hygiene. The runbook surfaces records using the
  retiring value before they become orphaned data.

## Architectural Tradeoffs

- **Restricted vs Unrestricted.** Restricted = data quality at the
  cost of integration brittleness (every new source value requires
  picklist update). Unrestricted = integration flexibility at the
  cost of phantom-value drift. Default Restricted; relax only when
  the integration needs justify it.
- **Global Value Set vs local picklist.** Global = one place to
  manage, ripple changes hit every consumer. Local = duplication,
  but per-consumer evolution. Use global when the value list is
  semantically the same domain across consumers.
- **API name vs label rename.** Label rename ripples to UI without
  Apex impact. API name rename is a value migration. Pick label
  rename whenever possible; API name rename when the original was
  a typo / misspelling / outdated identifier.
- **Picklist vs lookup vs custom metadata.** Picklist for small,
  stable, admin-managed lists. Lookup for relational data with
  attributes. Custom metadata for shared configuration values
  with attributes that admins edit but Apex consumes. Don't
  default to picklist for everything.

## Anti-Patterns

1. **Deactivating a value without first migrating records.**
   Records keep the value; reports filter it out; orphaned data.
2. **Unrestricted picklist with integration writes and no
   reconciliation.** Phantom values accumulate silently.
3. **Validation rule duplicating restricted-picklist enforcement.**
   Two layers maintain the same constraint; out-of-sync over time.
4. **Deactivating dependent picklist controller before migrating
   dependents.** Records' dependent values become unreachable.
5. **Treating "rename label" as equivalent to "rename API name".**
   Different ripple semantics; different impact on Apex / formulas.
6. **Global Value Set rename as a single-team decision.** Ripples
   to every consuming field; coordinate across stakeholders.

## Official Sources Used

- Metadata API Developer Guide, `CustomValue` — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf (api_meta.txt:47478–47483 supplies the two documented ways to deactivate a value and the rule that omission from a deployed file deactivates; api_meta.txt:47521–47526 supplies the retrieve asymmetry that makes a retrieved unrestricted local picklist a partial file; api_meta.txt:47513–47520 and 47527–47528 supply `default`, `description` and `label`-defaults-to-API-name, used in `references/metadata-examples.md` §3)
- Metadata API Developer Guide, `ValueSet` — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf (api_meta.txt:45847–45849 defines `restricted` as "whether the picklist's values are limited to only the values defined by a Salesforce admin", the claim under the Restricted-vs-Unrestricted tradeoff below and the §5 conversion checklist; api_meta.txt:45853 defines `valueSetName`, which the checker uses to tell a GVS-backed field from a local one)
- Object Reference for the Salesforce Platform, "Picklist Fields" — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf (object_reference.txt:2363–2367 is the grounding for `references/gotchas.md` § 10: the API does not enforce values on unrestricted picklists, an unmatched write *creates an inactive picklist value*, and the match is case-insensitive; object_reference.txt:2372–2374 — "Always use the value when inserting or updating a field. The `query()` call always returns the value, not the label" — grounds § 14 and the label-vs-API-name tradeoff)
- Object Reference, Glossary entry "Restricted picklist" — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf (object_reference.txt:2463–2464, "Users can't load unapproved values through the API", is the only sourced statement of the restricted-picklist rejection behaviour; the specific error code is marked UNVERIFIED in `references/gotchas.md` § 12 because no extracted guide names it)
- Object Reference, `PicklistValueInfo` standard object — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf (object_reference.txt:219760–219836 documents the object, its `query()` support and its `Value` / `Label` / `IsActive` / `IsDefaultValue` / `ValidFor` fields — the non-Apex half of the stored-vs-defined audit in `references/metadata-examples.md` §2)
- Apex Reference Guide, `DescribeFieldResult.getPicklistValues()` — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf (apexrefguide.txt:190848–190849, "Only active picklist values are returned", is the whole reason the audit must be a set difference and the grounding for `references/gotchas.md` § 11)
- Apex Reference Guide, `PicklistEntry` class — same PDF (apexrefguide.txt:193677–193686 supplies `getValue()`, `getLabel()`, `isActive()` and `isDefaultValue()`, used in the audit script's label-drift detection; apexrefguide.txt:191375–191380 supplies `isRestrictedPicklist()`)
- Apex Developer Guide, "Working with SOQL Aggregate Functions" — same PDF (apexdev.txt:9556–9566: `COUNT()` with a `GROUP BY` "consumes one query row per grouping" rather than one per record — why the audit query is affordable on a large object)
- Data Loader Guide, "Allow field truncation" / `sfdc.truncateFields` — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_data_loader.pdf (salesforce_data_loader.txt:437–452 and 1863–1877: the setting covers Picklist and Multi-select Picklist, and version 15.0+ fails the row rather than truncating — `references/gotchas.md` § 13)
- Salesforce App Limits Cheat Sheet — **no picklist limits found.** A search of the extracted cheat sheet for "picklist" returns nothing, so no numeric picklist limit in this package is sourced from it. The 1,000-values-per-global-value-set figure lives in `admin/picklist-and-value-sets` (api_meta.txt:79363–79367) and is not restated here.
- Salesforce Well-Architected — Trusted / Easy — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html (pillar framing for the Reliability and Operational Excellence notes above)

Sibling skills relied on rather than re-derived, cited inline throughout: `admin/picklist-and-value-sets` (`references/metadata-examples.md` §§1–2, 7–9; `references/gotchas.md` §§3–5, 7, 9–10, 14), `admin/record-types-and-page-layouts` (`references/gotchas.md` § 4, report filters on unstable labels), `admin/data-import-and-management` (`references/gotchas.md`, failed-vs-unprocessed rows and the bulk-load caveats behind `references/metadata-examples.md` §4).
