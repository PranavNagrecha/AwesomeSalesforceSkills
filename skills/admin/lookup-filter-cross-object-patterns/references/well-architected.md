# Well-Architected Notes — Lookup Filter Cross Object Patterns

## Relevant Pillars

- **Reliability** — A required cross-object lookup filter is the cheapest, most consistent way to enforce relational integrity at write time. Validation rules cover the same ground but only fire on save; lookup filters also reshape the picker, preventing the wrong choice from being made in the first place.
- **User Experience** — A filter that narrows a 50,000-row picker to the 12 contextually relevant rows turns a 30-second hunt into a one-click selection. Optional filters trade enforcement for guidance and are appropriate when the goal is decluttering rather than restriction.

## Architectural Tradeoffs

- **Required vs. optional:** Required is enforced for API/Apex/Flow; optional is UI-only. Required filters lock you into backfill discipline.
- **Filter vs. validation rule:** A lookup filter is what users see; a validation rule is what the system permits. They are not interchangeable — they are complementary. Use the filter to shape selection, the validation rule to enforce semantics that span more than one field.
- **Filter vs. sharing model:** Never use a filter as a security boundary. Sharing model and OWD govern access; filters govern only what the picker shows.

## Anti-Patterns

1. **Filter-as-ACL** — Hiding sensitive records by filtering the lookup. Users can still bypass via API or paste a record ID. Use sharing.
2. **Required filter without backfill** — Deploying a required filter with no plan for legacy records, then discovering blocked saves weeks later when stale records are touched.
3. **Replicating filter logic in three places** — A filter, a validation rule, AND a Flow decision all enforcing the same constraint, drifting independently. Pick one canonical enforcement point and link the others to it.

## Official Sources Used

- Object Reference — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_concepts.htm
- Metadata API Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_intro.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Lookup Filters help — https://help.salesforce.com/s/articleView?id=sf.fields_about_lookup_filters.htm&type=5
