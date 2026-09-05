---
name: list-views-and-compact-layouts
description: "Use when designing or reviewing list views, compact layouts, highlights panels, and search-result presentation so users can scan, find, and act on records quickly across desktop and mobile. Covers the deployable ListView, CompactLayout, SearchLayouts and ProfileSearchLayouts metadata: filterScope, booleanFilter, sharedTo, compactLayoutAssignment, and the package.xml shapes for each. Triggers: 'too many list views', 'compact layout not showing the right fields', 'search layouts vs list views', 'mobile highlights panel', 'list view missing after sandbox refresh', 'deploy a list view between orgs', 'list view column deployed blank', 'compact layout deploy failed'. NOT for page layouts or record types — use admin/record-types-and-page-layouts. NOT for Dynamic Forms — use admin/dynamic-forms-and-actions."
category: admin
salesforce-version: "Spring '25+'"
well-architected-pillars:
  - User Experience
  - Operational Excellence
  - Reliability
tags:
  - list-views
  - compact-layouts
  - search-layouts
  - highlights-panel
  - mobile-ux
triggers:
  - "users cannot find the right records in list views"
  - "compact layout is missing key fields on mobile"
  - "should i use search layouts or list views"
  - "too many public list views are creating clutter"
  - "record highlights panel is not useful"
  - "list views did not come across in the sandbox refresh"
  - "how do I deploy a list view from sandbox to production"
  - "compact layout deploy fails on a long text area field"
  - "a list view column deployed but renders blank"
  - "search layout keeps re-adding the name field on every deploy"
  - "the compact layout I created is not showing on the record"
inputs:
  - "target objects, personas, and primary browse or search workflows"
  - "whether the experience is Lightning desktop, mobile, console, or Experience Cloud"
  - "which fields users must scan quickly before opening a full record"
outputs:
  - "deployable ListView, CompactLayout and SearchLayouts metadata plus the package.xml for it"
  - "ux recommendation for list views, compact layouts, and search-result presentation"
  - "review findings for list-view sprawl, weak filters, and poor highlights design"
  - "configuration worksheet for object-level browse and scan paths"
dependencies: []
version: 1.1.0
author: Pranav Nagrecha
updated: 2026-09-04
---

Use this skill when users are losing time before they even open a record. List views, compact layouts, and search layouts all shape how quickly a user can browse, triage, and select the next record, but they solve different problems and should not be treated as interchangeable UI settings.

---

## Before Starting

Gather this context before working on anything in this domain:

- Are users browsing a working queue, opening a record from mobile, or searching globally for a known record?
- Which fields must be visible in the first five seconds, and which fields only matter after the record is open?
- Is the pain caused by information density, ownership of shared views, or confusion between search results and list-based work queues?
- Are the views that matter already in source control, or do they live only in the org? Metadata API cannot see a **Visible only to me** view at all, so an org comparison that reports no drift may still be missing what users rely on.

## Questions to Ask Before Configuring

Ask these before opening Setup. Each one maps to a behaviour in `references/gotchas.md` that turns a reasonable-looking configuration into a broken one.

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "Who is the audience for this view, and did anyone decide it should be public?" | A list view with no `sharedTo` element is public; the broadest audience is encoded as an absence, so nobody reviews it | An explicit sharing target (`group`, `role`, `roleAndSubordinates`, `queue`) or a written decision that public is intended |
| "Is this view meant to follow a queue?" | `filterScope` = `Queue` plus a `queue` developer name is a different object from a filtered view, and every queue already auto-creates one | Either a queue name that must deploy first, or a decision to use the auto-created view instead of authoring a rival |
| "What are the exact column tokens on this object?" | Standard-field columns are legacy tokens, not API names (`PC_Email` for `PersonEmail`), so hand-written columns render blank | A retrieved list view to harvest tokens from, instead of guesses |
| "Which record types exist, and which compact layout does each one get?" | `compactLayoutAssignment` sits on the object **and** on every record type; an unassigned layout renders nowhere | An assignment map: object default plus one line per record type |
| "Does any field we want in the highlights panel hold free text?" | Text area, long text area, rich text area, and multi-select picklist cannot go in a compact layout — the deploy fails | A short formula or text field to carry the summary, with the long field left on the record page |
| "Are these views migrating between orgs, and by what mechanism?" | `ListView` and `SearchLayouts` reject the package.xml wildcard and `ListView` members need `Object.ViewUniqueName` | A manifest that retrieves the encompassing object rather than a wildcard that silently returns nothing |
| "Who owns list-view creation on this object after go-live?" | Sprawl is a permission decision: "Manage Public List Views" also lets a user edit or delete every public view in the org | A named owner and the narrower "Manage Shared List Views" permission where it fits |

What a proper configuration adds over just doing it: views that survive a sandbox refresh because they are in source, a highlights panel that actually deploys and renders on every record type, and a public-view inventory small enough that the next admin can tell which queue is authoritative.

---

## Core Concepts

List views, compact layouts, and search layouts each own a different stage of user navigation. List views are for browsing and filtering record sets. Compact layouts are for fast record recognition in highlights and mobile contexts. Search layouts shape how search results present records. When teams blur those responsibilities, they keep editing the wrong metadata and users still cannot find what they need.

### List Views Are Working Surfaces

List views help users answer "what should I work on next?" They need a clear audience, strong filters, and only the columns required for triage. The best list view is not the one with the most data. It is the one that lets the intended persona decide quickly whether to open the record or move on.

### Compact Layouts Are Scan Layers

Compact layouts are not mini page layouts. They should expose the few fields that identify the record and its current state, especially in highlights panels and mobile-first experiences. If a compact layout tries to summarize everything, it stops helping anyone.

### Search Layouts And List Views Are Separate Concerns

Search results answer "which record is this?" while list views answer "which set of records should I process?" Changing search result columns does not fix a weak list view, and adding more list view columns does not improve global search behavior.

### None Of These Features Are Security Controls

Fields appearing or not appearing in a compact layout or list view do not change object, field, or record access. Good UX configuration depends on security, but it does not replace it.

### All Three Live Inside The Object

None of these is a standalone folder in Metadata API terms. Everything below is nested in the object's own definition, which is why "retrieve the object" is usually the right move and a wildcard usually is not.

| Metadata type | package.xml `<name>` | `<members>` | Wildcard `*` | Key elements |
|---|---|---|---|---|
| `ListView` | `ListView` | `Object.ViewUniqueName` | No | `filterScope` (required), `columns`, `filters`, `booleanFilter`, `queue`, `sharedTo`, `label`, `language`, `division` |
| `CompactLayout` | `CompactLayout` | layout name | Yes | `fields` (ordered by priority), `label` |
| `SearchLayouts` | via `CustomObject` | object name | No | `listViewButtons`, `searchResultsAdditionalFields`, `lookupDialogsAdditionalFields`, `customTabListAdditionalFields`, `searchFilterFields`, `massQuickActions`, `excludedStandardButtons` |
| `ProfileSearchLayouts` | via `CustomObject` | object name | — | `profileName`, `fields` |

`filterScope` is the one required element on a list view. Its enumeration is `Everything`, `Mine`, `MineAndMyGroups`, `AssignedToMe` (ServiceAppointment only), `Queue`, `Delegated`, `MyTerritory`, `MyTeamTerritory`, `Team`, `SalesTeam`, and `ScopingRule` — and a `ScopingRule` view only applies its rule when the user selects **Filter by scope** in Lightning Experience (`admin/scoping-rules`). Deployable XML for all four types is in `references/metadata-examples.md`.

### Assignment Is Separate From Definition

A compact layout is inert until something names it. `compactLayoutAssignment` appears twice: once on the `CustomObject` as the object default, and once inside each `RecordType`. A record type with no assignment does not inherit visibly in the metadata, so the assignment map has to be written down per record type rather than inferred from the layout list.

---

## Common Patterns

### Persona-Specific Working Lists

**When to use:** Sales, service, or operations teams repeatedly work a filtered subset of records.

**How it works:** Create a small set of role-oriented list views with meaningful ownership, narrow filters, and only the columns needed for triage. Reserve broad "all records" views for admins or specialized troubleshooting.

**Why not the alternative:** A long list of near-duplicate public list views creates clutter and weakens trust in every queue.

### Five-Second Compact Layout Design

**When to use:** Users need to recognize status, priority, owner, and key identifiers before opening the record.

**How it works:** Put the fields that answer "what is this and what state is it in?" into the compact layout. Keep the set short and stable. Use the full page or record page for deep context.

**Why not the alternative:** Stuffing the highlights area with every useful field makes the scan layer unreadable, especially on mobile.

### Search Versus Browse Deliberately Split

**When to use:** Teams are trying to solve both search discovery and queue processing on the same object.

**How it works:** Tune search-result presentation for recognition, and tune list views for workflow. Review both with the same persona, but do not assume one setting replaces the other.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Users need a filtered queue or worklist | List View | The primary need is browsing a record set and taking action on the next item |
| Users need to identify a record quickly after opening or in mobile | Compact Layout | The need is high-signal recognition, not detailed editing |
| Users are finding the wrong records from search | Search Layout or search-result configuration | Search result presentation is a separate surface from list views |
| Users need to edit or rearrange many fields on the record itself | Page Layout or Lightning Record Page | That is full-record design, not browse-and-scan configuration |
| The team wants to hide data from unauthorized users | Fix security model instead | These features do not enforce access controls |

---

## Recommended Workflow

1. **Inventory what exists, from two directions.** Retrieve the encompassing object (`sf project retrieve start --metadata CustomObject:<Object>`) to get every list view, compact layout, and the `searchLayouts` block in one pull, then query `SELECT DeveloperName, Name, SobjectType, IsSoqlCompatible FROM ListView WHERE SobjectType = '<Object>'` in the org. The query returns views the retrieve cannot — private and auto-created queue views — and the difference between the two lists is the real inventory.
2. **Fill in `templates/list-views-and-compact-layouts-template.md`.** One row per existing view with audience, filters, columns, share scope, and a keep / merge / retire call; then the compact-layout field set and the assignment per record type. This is the artefact the rest of the workflow edits.
3. **Harvest tokens before writing any XML.** Copy standard-field `columns` and `searchResultsAdditionalFields` values from the retrieved files. Custom fields use their API name; standard fields do not, and guessing produces a blank column or a failed deploy.
4. **Author the metadata from `references/metadata-examples.md`.** Take the queue-scoped view, the `booleanFilter` + `sharedTo` view, the compact layout, and the object-level `compactLayoutAssignment` / `recordTypes` / `searchLayouts` block as the starting shapes, and follow the "How to read it" notes rather than editing them by analogy.
5. **Run the checker on the source tree**: `python3 skills/admin/list-views-and-compact-layouts/scripts/check_list_views_and_compact_layouts.py --manifest-dir force-app/main/default`. It flags unfiltered public views, dangling `booleanFilter` indices, `filterScope` / `queue` mismatches, compact layouts holding an unsupported field type, and compact layouts that no `compactLayoutAssignment` names.
6. **Deploy with `--dry-run` first, then confirm on a phone-width viewport.** Open one record of each record type and one list view per persona; re-run the `ListView` query to confirm `DeveloperName` and `IsSoqlCompatible` match what was authored. Re-check `references/gotchas.md` if the retrieved file differs from what you sent — the search layout's Name field is added back by design.
7. **Record the governance decision.** Who may create public views on this object, which auto-created queue views are authoritative, and when the inventory is reviewed again.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Each list view has a named audience and clear purpose.
- [ ] Columns are optimized for triage rather than "everything useful."
- [ ] Broad public views are limited and intentional.
- [ ] Compact layout fields support record recognition in highlights and mobile contexts.
- [ ] Search-result tuning is treated separately from list-view tuning.
- [ ] The design is validated with a real persona and container, not only with admin assumptions.
- [ ] Every list view file either carries a deliberate `sharedTo` target or is a public view somebody signed off on.
- [ ] Every compact layout is named by a `compactLayoutAssignment` on the object or on a record type.
- [ ] `filterScope` = `Queue` views name a queue that deploys before them, and duplicate auto-created queue views are accounted for.
- [ ] `booleanFilter` indices resolve to filter line items that exist, in document order.
- [ ] `scripts/check_list_views_and_compact_layouts.py --manifest-dir <source>` reports no ERROR lines.

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Compact layouts do not replace page layouts** - they support recognition and highlights, not full editing or detailed field placement.
2. **Search layout fixes do not change list views** - teams often edit the wrong metadata because both features display columns.
3. **List-view sprawl is a governance problem, not just a UX problem** - once everyone can create broad public views freely, the object becomes harder to navigate and harder to support.
4. **Field visibility in the UI is still bounded by security** - if a user cannot access a field, layout design alone will not make it usable.
5. **"Manage Public List Views" is no longer the only permission for sharing a view** - since Summer '26, grant "Manage Shared List Views" so a user can share their own list views with the roles, groups, and territories they belong to; "Manage Public List Views" still works, but it also lets them edit or delete every public list view in the org.
6. **A missing `sharedTo` element means public, not unshared** - the guide states `SharedTo` is present for shared and private views and absent for public ones, so the widest audience is the one with no markup to review.
7. **"Visible only to me" views are outside Metadata API entirely** - they never appear in a retrieve, so a clean org diff is not evidence that users kept their views.
8. **Compact layouts reject four field types at deploy** - text area, long text area, rich text area, and multi-select picklist, which is exactly the shortlist an admin reaches for when asked to show "what this record is about".
9. **`ListView` and `SearchLayouts` reject the package.xml wildcard while `CompactLayout` accepts it** - the same manifest can therefore ship half the design.

Deeper treatment, with what happens / when it occurs / how to avoid, in `references/gotchas.md`.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Browse-and-scan UX recommendation | Guidance on which surfaces should use list views, compact layouts, or search-result tuning |
| Configuration review findings | Issues such as over-wide columns, weak filters, and missing high-signal highlight fields |
| Object worksheet | Persona-specific inventory of list views, compact layouts, and search-result intent |
| `objects/<Object>/listViews/*.listView-meta.xml` | Deployable list views with `filterScope`, `filters`, `booleanFilter`, and an explicit `sharedTo` |
| `objects/<Object>/compactLayouts/*.compactLayout-meta.xml` plus assignments | Compact layouts and the `compactLayoutAssignment` lines that make them render |
| Checker output | ERROR / WARN / INFO lines from `scripts/check_list_views_and_compact_layouts.py` on the source tree |

---

## Reference Files

| File | Read it when |
|---|---|
| `references/metadata-examples.md` | Writing deployable `ListView`, `CompactLayout`, and `searchLayouts` XML, the package.xml for them, and the post-deploy `ListView` query |
| `references/gotchas.md` | A view or layout deployed cleanly and still behaves wrong, or a retrieve keeps producing a diff nobody wrote |
| `references/examples.md` | Designing the working set for a persona before any XML exists — queue triage and a mobile compact layout, end to end |
| `references/well-architected.md` | Justifying the governance tradeoff between user freedom and view sprawl, and locating the official sources behind each claim |
| `references/llm-anti-patterns.md` | Reviewing output an AI assistant produced in this domain, especially "edit the page layout to change the highlights panel" |
| `templates/list-views-and-compact-layouts-template.md` | Running the inventory in workflow step 2 |

---

## Related Skills

- `admin/record-types-and-page-layouts` - use when the real design issue is record type separation, page layouts, or Dynamic Forms; record types are also where `compactLayoutAssignment` is set per type.
- `admin/queues-and-public-groups` - use when a `filterScope` = `Queue` view or a `sharedTo` group has to exist before the view deploys; its `references/queue-behaviour-matrix.md` covers the auto-created queue list view.
- `admin/scoping-rules` - use when the view uses `filterScope` = `ScopingRule` and the rule only applies once the user picks Filter by scope.
- `admin/dynamic-forms-and-actions` - use when the ask is really about the record detail region rather than the highlights panel above it.
- `admin/lightning-page-performance-tuning` - use when the record page is slow to render rather than hard to scan.
- `admin/reports-and-dashboards` - use when the team needs analytics, summarization, or scheduled reporting rather than operational list navigation.
- `lwc/lwc-data-table` - use when a custom component is replacing standard list experiences and needs deliberate column and action design.
