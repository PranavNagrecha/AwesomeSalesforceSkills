---
name: report-type-strategy
description: "Custom Report Type design — when to create a CRT vs use the standard, A-with-B-without and A-without-B joins, primary/secondary/related-via-lookup objects, the 60-field display limit, and field-set vs cross-join layouts. NOT for building the report or dashboard itself once the report type exists — use admin/reports-and-dashboards-fundamentals. Keywords: reportType metadata, baseObject, outerJoin, ObjectRelationship, ReportLayoutSection, checkedByDefault, displayNameOverride, deployed false, custom report type sprawl, report type inventory."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Performance
triggers:
  - "custom report type isn't in the report builder list"
  - "accounts with no cases missing from my report"
  - "choose the base object for a custom report type"
  - "add a fourth object to a custom report type"
  - "reportType deploy fails inner join after outer join"
  - "count how many reports use a custom report type"
  - "show lookup parent fields on a custom report type"
  - "clean up duplicate custom report types"
  - "custom report type vs standard report type"
  - "report type a with b without related"
  - "report type primary secondary tertiary object"
  - "salesforce report type 60 field display limit"
  - "report type which fields are reportable"
  - "joined report custom report type"
  - "custom report type in development not deployed"
  - "accounts without contacts child field filter contradiction"
tags:
  - reports
  - custom-report-type
  - data-access
  - field-availability
  - performance
inputs:
  - "Primary object and the join shape (with/without related, lookup vs master-detail)"
  - "Field set users actually need (vs everything on the object)"
  - "Whether the report type will be packaged or org-only"
outputs:
  - "Decision: create CRT, reuse standard, or build a joined report"
  - "Object hierarchy (primary, secondary, optional tertiary, related-via-lookup) with join semantics"
  - "Field layout grouped by section, within the 1,000-field cap and 60-display limit"
dependencies: []
version: 1.1.0
author: Pranav Nagrecha
updated: 2026-09-04
---

# Report Type Strategy

Custom Report Types (CRTs) determine which objects can be reported
on together, with what join semantics, and which fields appear in
the report builder. They are the substrate every report sits on
top of. Standard report types ship with the platform for the
common shapes ("Accounts and Contacts", "Opportunities"). CRTs
exist for everything else: custom-object joins, with-without
queries, and curated field sets.

The decision matrix is small. Use a standard report type when one
exists for your shape and the field set is acceptable. Create a
CRT when (a) the join you need does not exist as a standard, (b)
you need an A-with-B-without (or A-without-B) join semantic
unavailable on the standard, (c) you need to expose a custom
object as the primary, or (d) you need to curate the field list
because the standard exposes too many fields and overwhelms the
admin. Build a *joined report* (a report that combines multiple
report types) only when one CRT cannot model the shape — joined
reports have their own constraints (no cross-block formulas
across all blocks, no cross-block filters in some cases).

The hard parts are the join semantics and the 60-field display
limit. A primary-with-secondary CRT inner-joins by default; a
"with or without" CRT outer-joins (rows from primary that have
no secondary still appear). Once a CRT is created, the join
shape cannot be edited — only the field layout can. The
60-field limit is a *display* cap (the field-picker UI shows 60);
the underlying CRT supports up to 1,000 fields, but anything past
60 is reachable only through search.

## Questions to Ask Before Configuring

Ask these before opening Setup or writing `reportType` XML. A report type is a substrate: `baseObject`
cannot be edited after creation, and every report built on the type inherits whatever the join
sequence decided. An LLM that skips these produces a type that deploys cleanly and answers the wrong
question.

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "Which object's records must appear on **every** row, even when nothing related exists?" | That object is `baseObject`, and the guide states it can't be edited after initial creation | The primary object, settled once, and the name of the type |
| "For each related object: should a parent with zero of them still show up?" | This is `outerJoin` per level, and it is the difference between a silent 80% undercount and a correct report | One `true`/`false` per join, decided by the requirement rather than by the default |
| "In what order are the relationships mandatory vs optional?" | The guide forbids an inner join later in a sequence that already contains an outer join — the ordering is a hard constraint, not a preference | A join order that is legal, or the discovery that this needs two report types |
| "Which of the wanted fields live on a **lookup parent** rather than a child?" | Lookup parents are dotted `field` paths on an existing `table` and cost no join slot; only children consume the four-object budget | A join chain that fits, and columns that would otherwise have been impossible |
| "Does a standard report type already answer this, and can this org's users see it?" | `SharingSettings.enableStandardReportVisibility` defaults to `false`, which can hide standard types that expose other users' data | Either reuse of a standard type, or a documented reason the org setting forces a custom one |
| "Who will own this type in a year, and what happens to the reports on it?" | New fields are never added to a custom type automatically, and reports-per-type is not queryable via SOQL | A named owner and a retrieve-based inventory routine instead of drift |
| "Is the answer actually 'A without B'?" | There is no negation join in `ObjectRelationship`; negation belongs on the report as a `without` cross filter | A superset report type plus a report-level filter, not a second type that can't work |

What a proper report-type strategy adds over just clicking through the CRT wizard: the join sequence
is legal and directional on purpose, lookup parents are read as columns instead of burning join
slots, the standard-vs-custom decision accounts for the org's sharing setting, and the org ends up
with a small inventory of named topologies rather than a drawer of near-identical types nobody dares
delete.

---

## Recommended Workflow

1. **Inventory before you add.** Retrieve every report type with the wildcard manifest in
   `references/metadata-examples.md` (`ReportType` is one of the few analytics types that accepts
   `<members>*</members>`). Read `baseObject`, the `join` chain and `label` on each. If a type
   already has your base object and your join topology, extend its `sections` instead of creating a
   sibling — that is how sprawl starts.
2. **Settle `baseObject` against the question, not the use case.** Pick the object whose records
   must appear even when nothing related exists. The guide states all objects, including custom and
   external objects, are supported, so there is no "reportable object" list to route around. Name
   the type after the base object and its join shape ("Accounts with or without Cases"), never after
   the team that asked for it — see `references/gotchas.md`.
3. **Draw the join sequence and check it is legal.** Maximum four objects. Once an outer join
   appears in the sequence, no later join may be inner. Sort every wanted relationship into
   mandatory vs optional, order mandatory first, and if the requirement demands otherwise, split
   into two report types now rather than discovering it at deploy time.
4. **Move every lookup parent out of the join chain.** Anything reachable by a dotted path from an
   already-joined table is a column, not a join — example 3 in `references/metadata-examples.md`
   shows `Contact.Account.Industry` on `<table>Case</table>`. Do this before step 3's budget is
   spent; it frequently turns a five-object requirement into a legal two-object type.
5. **Write the `sections`.** One section per table in the chain, plus one per lookup-parent cluster.
   `masterLabel` is required on every section; `checkedByDefault` pre-selects a column for new
   reports only; `displayNameOverride` disambiguates the three `Name` columns a three-object chain
   produces. Write the `description` for the report-builder picker — say what the type excludes.
6. **Lint, then deploy.** Run
   `python3 scripts/check_report_type_strategy.py --manifest-dir force-app/main/default`. It fails
   on more than four joined objects and on an inner join after an outer join, and reports sections
   with no columns, `deployed=false`, duplicate labels, and two types sharing a base object and
   topology. Fix ERRORs before `sf project deploy start --dry-run`.
7. **Verify and record ownership.** Confirm `deployed` is `true` for anything non-admins must see,
   then run the reports-per-type count in `references/metadata-examples.md` § Verification — it is a
   grep over retrieved `Report` metadata, because the `Report` object exposes no report-type field.
   Zero-count types are deletion candidates; record the owner of every type you keep.

## When To Reach For Joined Reports

Joined reports stitch results from multiple report types into one
output, side by side. Use when a single CRT cannot model the
shape: cross-object summary alongside detail, "this quarter vs
prior" comparisons, A-without-B as a subtraction. They are more
fragile (cross-block formulas have limits, some filters apply
per-block) but they are the only single-report answer for
multi-shape data.

## What This Skill Does Not Cover

- **Designing individual reports** (filters, summaries, charts)
  — see `admin/reports-and-dashboards-fundamentals`.
- **Dashboard composition** — see `admin/reports-and-dashboards`.
- **Reports API / Reporting Snapshot** — not covered here; the
  closest guidance is async report execution via the Analytics API
  in `admin/report-performance-tuning`.
- **Big Object reporting** — see `data/external-data-and-big-objects`.

---

## Reference Files

| File | Read it when |
|---|---|
| `references/metadata-examples.md` | Writing or reviewing `reportType` XML — the three join topologies, lookup-path columns, `package.xml` with the wildcard, retrieve/deploy commands, and the reports-per-type verification |
| `references/gotchas.md` | A report type deploys but the rows are wrong, the type is invisible, a new field never showed up, or the org has more types than anyone can account for |
| `references/examples.md` | Sizing a requirement: which shapes a single type can model, which need a cross filter, and which genuinely need a joined report |
| `references/llm-anti-patterns.md` | Reviewing AI-generated report-type guidance before acting on it — especially join-shape and depth claims |
| `references/well-architected.md` | Justifying standard-vs-custom against the pillars, or chasing the official source behind a claim here |
| `templates/report-type-strategy-template.md` | Capturing the topology decisions before any XML is written — especially the irreversible `baseObject` choice |
| `scripts/check_report_type_strategy.py` | Linting `reportTypes/` in a DX tree before deploying |

---

## Related Skills

- **admin/reports-and-dashboards**: Use for the `Report`, `Dashboard`, `ReportFolder` and `FolderShare` XML that sits on top of a report type — including the `crossFilters` block that expresses "A without B". It owns the wildcard and folder-sharing rules this skill cites. NOT for choosing the base object or the join chain.
- **admin/reports-and-dashboards-fundamentals**: Use once the report type exists and the work is the report itself — groupings, summaries, formulas, charts. NOT for deciding whether the type can express the shape.
- **admin/report-performance-tuning**: Use when a report on a correct type is slow — deep joins, large row counts, async execution via the Analytics API. NOT for join correctness.
- **admin/analytics-permission-and-sharing**: Use when the question is who can see a report type, a folder or the rows inside — including the org-level standard-report-visibility setting this skill flags as a standard-vs-custom input.
- **data/external-data-and-big-objects**: Use when the base object is an external object or a Big Object, where reportability is constrained by the storage model rather than by the report type.
