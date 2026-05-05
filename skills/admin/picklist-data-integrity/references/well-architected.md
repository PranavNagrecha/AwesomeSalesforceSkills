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

- Picklist Field Restrictions — https://help.salesforce.com/s/articleView?id=sf.fields_restricted_picklist.htm&type=5
- Picklist Value Sets (Global) — https://help.salesforce.com/s/articleView?id=sf.fields_global_picklist_overview.htm&type=5
- Manage Picklist Values — https://help.salesforce.com/s/articleView?id=sf.picklist_values_manage.htm&type=5
- Dependent Picklists — https://help.salesforce.com/s/articleView?id=sf.fields_dependent_picklists.htm&type=5
- Replace Picklist Values — https://help.salesforce.com/s/articleView?id=sf.fields_replace_picklist_values.htm&type=5
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
