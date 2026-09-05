# Well-Architected Notes — Lookup Filter Cross Object Patterns

## Relevant Pillars

- **Reliability** — A required cross-object lookup filter is the cheapest, most consistent way to enforce relational integrity at write time. Validation rules cover the same ground but only fire on save; lookup filters also reshape the picker, preventing the wrong choice from being made in the first place.
- **User Experience** — A filter that narrows a 50,000-row picker to the 12 contextually relevant rows turns a 30-second hunt into a one-click selection. Optional filters trade enforcement for guidance and are appropriate when the goal is decluttering rather than restriction.

## Architectural Tradeoffs

- **Required vs. optional:** `isOptional` is a required boolean, so this is a decision you make on every filter whether or not you notice. Required buys enforcement and costs you a backfill; optional buys guidance and costs you nothing but an `infoMessage`.
- **Filter vs. validation rule:** A lookup filter is what users see; a validation rule is what the system permits. They are not interchangeable — they are complementary. Use the filter to shape selection, the validation rule to enforce semantics that span more than one field, and change both in the same commit.
- **Filter vs. sharing model:** Never use a filter as a security boundary. Sharing model and OWD govern access; filters govern only what the picker shows.
- **Conditions vs. fields:** The ten-item cap and the closed operation enum both push complexity out of the filter and into a formula or checkbox field on the target object. That is usually the better place for it anyway: a field is reportable, testable, and visible in a describe call, while a filter item is none of those.
- **Declarative reach vs. Setup editability:** A distance filter is deployable but not editable in Setup, so choosing it converts the filter into a source-controlled artefact permanently. That is a governance gain and an admin-autonomy loss; make it on purpose.

## Anti-Patterns

1. **Filter-as-ACL** — Hiding sensitive records by filtering the lookup. Users can still bypass via API or paste a record ID. Use sharing.
2. **Required filter without backfill** — Deploying a required filter with no plan for legacy records, then discovering blocked saves weeks later when stale records are touched.
3. **Replicating filter logic in three places** — A filter, a validation rule, AND a Flow decision all enforcing the same constraint, drifting independently. Pick one canonical enforcement point and link the others to it.
4. **Designing around a bypass that does not exist in the metadata** — `LookupFilter` has seven elements and none of them is an exemption switch. A rollout plan whose escape hatch is "admins can bypass" has no artefact behind it.
5. **A required filter with no `errorMessage`** — The user is rejected and told nothing useful. `errorMessage` exists for exactly this moment and costs one line.

## Official Sources Used

- Metadata API Developer Guide, `LookupFilter` / `FilterItem` / `FilterOperation` — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf (api_meta.txt:43860–43924; supports the seven-element shape, the "up to 10 FilterItems per lookup filter" cap, the `value`-or-`valueField` split, and the closed operation enum including `within` "(DISTANCE criteria only)")
- Metadata API Developer Guide, `CustomField` → `lookupFilter` — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf (api_meta.txt:43483–43501; supports "the filter is an element of the field, not its own component" and "LookupFilter isn't supported on the article type object", plus the no-wildcard rule for `CustomField` in `package.xml` at 43983–43985)
- Metadata API Developer Guide, `NamedFilter` (removed in API v30.0) — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf (api_meta.txt:44511–44530, 44580–44583; supports the migration statement in SKILL.md and the `sourceObject` evidence quoted beside the UNVERIFIED `$Source` marker in `references/metadata-examples.md`)
- Metadata API Developer Guide, `CustomObjectTranslation` → `LookupFilterTranslation` — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf (api_meta.txt:46011–46014, 46075–46087; supports Gotcha 9, including the `infoMessage` → `informationalMessage` rename)
- Object Reference, "Compound Field Considerations and Limitations" — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf (object_reference.txt:2934–2935, 2957–2961; supports Gotcha 6 — compound fields are unusable in lookup filters except distance ranges, and distance filters are Metadata-API-only)
- Object Reference, `ServiceResource.ResourceType` — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf (object_reference.txt:259736–259744; supports Gotcha 10 — a dependent lookup filter on a standard restricted picklist compares the stored code, not the label)
- Apex Developer Guide / Apex Reference Guide, `Schema.DescribeFieldResult` method list — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf (apexrefguide.txt:190542–190740; supports the grounded `getReferenceTo()` / `getRelationshipName()` half of `references/metadata-examples.md` §8, and is the source of the UNVERIFIED marker on `getFilteredLookupInfo()`, which does not appear in that list)
- Salesforce Well-Architected — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html (supports the Reliability and User Experience pillar framing above)
