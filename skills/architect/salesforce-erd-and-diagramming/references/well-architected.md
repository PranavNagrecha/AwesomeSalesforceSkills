# Well-Architected Notes — Salesforce ERD and Diagramming

## Relevant Pillars

- **Automated (primary)** — a diagram is a projection of metadata, and metadata is machine-readable. Anything
  hand-maintained decays at the rate the org changes while continuing to look authoritative, which is the worst
  combination available. The pillar's test applies literally: if it can be generated, generating it is not an
  optimisation.
- **Adaptable** — the diagram's value is measured at the moment someone plans a change against it. A stale ERD does not
  merely fail to help; it actively misinforms migration and integration planning, and the cost lands on the team least
  able to detect the error.
- **Secure** — audience determines content. An ERD produced for a vendor or an executive deck that carries field names
  revealing regulated data, or a share-table topology revealing the access model, has disclosed more than intended.
  Redaction is a design input, not a post-processing step.
- **Resilient** — provenance is what makes a diagram falsifiable. Manifest, API version, retrieval date, and stated
  exclusions turn "is this right?" from a debate into a check.

## Architectural Tradeoffs

**Generated vs hand-drawn.** Generation guarantees fidelity and produces layouts that are frequently unreadable at the
scale a real org reaches. Hand-drawing produces the clear picture an executive needs and disagrees with the org within
two releases. The workable split is to generate the developer-and-migration artifact, hand-curate the executive one,
and generate both from the same committed source so the curated version has a traceable parent.

**Logical vs physical.** A logical ERD is what stakeholders can read; a physical one is what a migration needs. The
temptation is one diagram serving both, which produces a logical diagram that quietly omits junction objects
(`AccountContactRelation`, `OpportunityContactRole`) and share tables — precisely the objects the migration depends on.
Produce two, label each, and never let a logical diagram be the input to technical work.

**Completeness vs readability for polymorphic fields.** Drawing every possible target of `Task.WhatId` is complete and
unreadable. Drawing one is readable and false. The annotated-node compromise is neither, and it is the only option that
keeps the diagram honest: the set of possible types goes in the note, and the narrowing mechanism (`WHERE What.Type` or
`SELECT TYPEOF`) goes in the companion query.

**Fail the build on drift vs regenerate silently.** Auto-committing a regenerated diagram keeps it current with no
human effort and lets a schema change land without anyone reviewing its effect on the model. Failing the PR forces the
review and adds friction to every object change. Prefer failing, because the point of the diagram is the conversation
it triggers, not the file.

## Anti-Patterns

1. **The undated diagram.** No manifest, no API version, no retrieval date, no statement of what was excluded. A reader
   cannot distinguish "this object does not exist" from "this object was not retrieved", and both look identical on the
   page.
2. **The pinned manifest.** A regeneration job running green for a year against a `package.xml` fixed at an old
   `<version>`. Retrieval honours the manifest's API version, so the pipeline faithfully reproduces an obsolete view of
   the org and reports success every time.
3. **The invented polymorphic edge.** A single arrow from `Task` to `Account` because the generator picked the first
   candidate. It reads as a foreign key, gets designed against as a foreign key, and is discovered not to be one during
   data migration.
4. **The core-objects ERD used for integration design.** Six standard objects, no junctions, no share tables. It
   answers the questions nobody asked and omits the ones that decide the integration's data model.

## Official Sources Used

- Apex Developer Guide, Version 67.0 (Summer '26) — *Working with Polymorphic Relationships in SOQL Queries*: the
  definition, the `Task.Who` Contact-or-Lead example, and the `What.Type` / `TYPEOF` narrowing forms cited in
  `examples.md`.
  https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/langCon_apex_SOQL_polymorphic_relationships.htm (verified 2026-08-14)
- Metadata API Developer Guide, Version 67.0 — *Unsupported Metadata Types*: why an
  absent object may be a retrieval gap rather than a schema fact.
  https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_unsupported_types.htm (verified 2026-08-14)
- Metadata API Developer Guide, Version 67.0 — *Profile*: retrieved content depends on the `RetrieveRequest`, the
  clearest documented case of partial metadata that looks complete on disk.
  https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_profile.htm (verified 2026-08-14)
- Metadata API Developer Guide, Version 67.0 — *Deleting Components from an Organization*: the
  `package.xml`-sourced API version behind the stale-manifest failure.
  https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_deploy_deleting_files.htm (verified 2026-08-14)
