---
name: report-type-strategy
description: "Custom Report Type design — when to create a CRT vs use the standard, A-with-B-without and A-without-B joins, primary/secondary/related-via-lookup objects, the 60-field display limit, and field-set vs cross-join layouts. NOT for individual report definitions (use admin/report-design) or dashboards (use admin/dashboard-design)."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Performance
triggers:
  - "custom report type vs standard report type"
  - "report type a with b without related"
  - "report type primary secondary tertiary object"
  - "salesforce report type 60 field display limit"
  - "report type which fields are reportable"
  - "joined report custom report type"
  - "report builder cannot find object combination"
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
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-05-05
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

## Recommended Workflow

1. **Confirm a standard report type does not already cover this.**
   Setup → Report Types → Show All; filter by primary object.
   Most "Account" and "Opportunity" shapes are already there.
2. **Decide the join shape before creating the CRT.** A → B
   inner: "Accounts with Contacts" — Accounts that have ≥1
   Contact. A → B with-or-without: "Accounts with or without
   Contacts" — every Account; Contacts join when present. A →
   B without: cannot be modeled as a single CRT — needs a
   subtraction in a joined report or a Cross Filter.
3. **Pick the primary object as the one users always need on
   every row.** Secondary objects are optional rows. Tertiary
   ("related via lookup") joins go through a lookup field on the
   secondary.
4. **Curate the field list deliberately.** Add only the fields
   users will reference. Group by section ("Account Information",
   "Lead Source") so the field picker is scannable. Adding all
   1,000 fields produces an unusable picker.
5. **Set up the CRT layout in two passes.** First pass: bring in
   every field you might need. Second pass: hide the ones you
   don't, group the rest. The hidden fields can still be added by
   savvy users via search; they don't clutter default layouts.
6. **Document the report type's purpose.** The CRT description
   field is small but visible in the report-builder picker. "Use
   for renewals tracking. Excludes closed-lost." beats "Custom
   Account Reporting".
7. **Test access by running as a low-privilege user.** CRTs
   inherit object permissions; if Sales Reps can't see the
   tertiary object, the report row collapses to whatever they can
   see.

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
  — see `admin/report-design`.
- **Dashboard composition** — see `admin/dashboard-design`.
- **Reports API / Reporting Snapshot** — see `admin/reporting-api`.
- **Big Object reports** — see `architect/big-object-reporting`.
