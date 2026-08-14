# Gotchas — Salesforce ERD and Diagramming

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Polymorphic fields have no ERD edge, and drawing one is a lie

**What happens:** Several standard relationship fields do not point at one object. The Apex Developer Guide defines the
case plainly: "A polymorphic relationship is a relationship between objects where a referenced object can be one of
several different types. For example, the `Who` relationship field of a `Task` can be a `Contact` or a `Lead`." The
same applies to `What` on `Task` and `Event`, and to `Owner` on many objects, which can be a `User` or a `Group`.

An ERD generated from metadata either invents a single edge (wrong), draws every possible edge (unreadable), or drops
the field (silently incomplete). All three ship regularly.

**When it occurs:** In every generated ERD that includes activities, and in every integration design that treats
`WhatId` as a foreign key to one table. The downstream cost lands on the data-migration team, who discover that a
single column holds ids from four objects.

**How to avoid:** Model polymorphic fields as an annotated edge to a labelled set, not as a relationship line, and put
the discriminator in the note. In the accompanying design, show how consumers narrow the type — the platform gives two
mechanisms: a `Type` qualifier in the `WHERE` clause (`WHERE What.Type IN ('Account', 'Opportunity')`) and a `TYPEOF`
clause in the `SELECT` list (`SELECT TYPEOF What WHEN Account THEN Phone WHEN Opportunity THEN Amount END FROM Event`).
A reader who sees `TYPEOF` in the diagram's companion query understands the relationship in a way no arrow conveys.

---

## Gotcha 2: A diagram generated from `package.xml` inherits that manifest's blind spots

**What happens:** Diagram-as-code pipelines read the retrieved metadata and emit ER syntax from it. The retrieval is
therefore the diagram's real source, and it has documented gaps. "Some Salesforce features have metadata types that
aren't available in Metadata API. These metadata types can't be retrieved or deployed with Metadata API." The Metadata
API Developer Guide names the authority for checking: the Metadata Coverage report is "the ultimate source of truth for
metadata coverage across several channels."

The subtler gap is in what the manifest asked for rather than what the API supports. Profiles are the canonical
example: their retrieved content "depends on the content requested in the `RetrieveRequest` message", so a partial
manifest yields partial metadata that looks complete on disk.

**When it occurs:** When the ERD is used as the input to a data migration or an access review. Objects from managed
packages, and anything the manifest did not name, are simply absent — and absence in a diagram reads as "does not
exist", not as "was not retrieved".

**How to avoid:** Emit the manifest's scope into the diagram itself — a header comment listing the types and members
retrieved, the API version, and the retrieval date. A diagram that states what it excludes is usable; one that does not
is a claim about the whole org that nobody verified.

---

## Gotcha 3: The API version in the manifest silently changes what a regenerated diagram contains

**What happens:** "The API version that the deployment uses is the API version that's specified in `package.xml`."
Retrieval behaves the same way — the manifest's `<version>` decides which fields and which types come back. A
regeneration pipeline whose manifest is pinned to an old version produces a diagram of the org as that version sees it,
and the diff against last quarter looks like schema stability when it is actually a frozen lens.

**When it occurs:** On repositories where `package.xml` was written once and the CI job has run unattended since. The
symptom is a field that exists in Setup, exists in the org, and does not appear in the ERD — with no error anywhere.

**How to avoid:** Print the manifest's API version in the rendered diagram, and fail the regeneration job when the
manifest version trails the org's release by more than one. A diagram nobody can date is a diagram nobody should trust.

---

## Gotcha 4: Junction and system objects carry the relationships stakeholders ask about

**What happens:** The relationships that generate the most questions in a review — how a contact relates to more than
one account, which contacts are on an opportunity, who is on a case team — live on objects that a "core objects" ERD
usually omits because they were not on the whiteboard: `AccountContactRelation`, `OpportunityContactRole`,
`CaseTeamMember`, and the sharing objects (`<Object>__Share`, `AccountShare`).

**When it occurs:** In the review meeting, when someone asks how a contact can belong to two accounts and the diagram
has no answer. The follow-up cost is worse: an integration designed from the incomplete diagram writes to
`Contact.AccountId` and cannot represent the relationship the business actually has.

**How to avoid:** Decide logical-versus-physical explicitly and say which one the diagram is. For any ERD that will
inform integration or migration work, include the junction objects and the `__Share` objects for any object whose
access model matters — sharing is part of the data model, not a footnote to it, and for custom objects the share table
is where Apex managed sharing writes.

## Official Sources Used

- Apex Developer Guide, Version 67.0 (Summer '26) — *Working with Polymorphic Relationships in SOQL Queries*: the
  definition of a polymorphic relationship, the `Task.Who` Contact-or-Lead example, the `What.Type` filter form, and
  the `TYPEOF … WHEN … THEN … END` clause.
  https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/langCon_apex_SOQL_polymorphic_relationships.htm (verified 2026-08-14)
- Metadata API Developer Guide, Version 67.0 — *Metadata Types*: the Metadata Coverage report as "the ultimate source
  of truth for metadata coverage across several channels".
  https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_types_list.htm (verified 2026-08-14)
- Metadata API Developer Guide, Version 67.0 — *Unsupported Metadata Types*: the consequence of unsupported types.
  https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_unsupported_types.htm (verified 2026-08-14)
- Metadata API Developer Guide, Version 67.0 — *Profile*: retrieved content depends on the `RetrieveRequest`, the
  example of the diagram-relevant partial-retrieve behaviour.
  https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_profile.htm (verified 2026-08-14)
- Metadata API Developer Guide, Version 67.0 — *Deleting Components from an Organization*: "The API
  version that the deployment uses is the API version that's specified in `package.xml`."
  https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_deploy_deleting_files.htm (verified 2026-08-14)
