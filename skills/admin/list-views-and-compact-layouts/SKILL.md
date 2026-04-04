---
name: list-views-and-compact-layouts
description: "Use when designing or reviewing list views, compact layouts, highlights panels, and search-result presentation so users can scan, find, and act on records quickly across desktop and mobile. Triggers: 'too many list views', 'compact layout not showing the right fields', 'search layouts vs list views', 'mobile highlights panel'. NOT for page layout design, Dynamic Forms strategy, or record-type architecture."
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
inputs:
  - "target objects, personas, and primary browse or search workflows"
  - "whether the experience is Lightning desktop, mobile, console, or Experience Cloud"
  - "which fields users must scan quickly before opening a full record"
outputs:
  - "ux recommendation for list views, compact layouts, and search-result presentation"
  - "review findings for list-view sprawl, weak filters, and poor highlights design"
  - "configuration worksheet for object-level browse and scan paths"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-03-13
---

Use this skill when users are losing time before they even open a record. List views, compact layouts, and search layouts all shape how quickly a user can browse, triage, and select the next record, but they solve different problems and should not be treated as interchangeable UI settings.

---

## Before Starting

Gather this context before working on anything in this domain:

- Are users browsing a working queue, opening a record from mobile, or searching globally for a known record?
- Which fields must be visible in the first five seconds, and which fields only matter after the record is open?
- Is the pain caused by information density, ownership of shared views, or confusion between search results and list-based work queues?

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

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. Gather context — confirm the org edition, relevant objects, and current configuration state
2. Review official sources — check the references in this skill's well-architected.md before making changes
3. Implement or advise — apply the patterns from Core Concepts and Common Patterns sections above
4. Validate — run the skill's checker script and verify against the Review Checklist below
5. Document — record any deviations from standard patterns and update the template if needed

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Each list view has a named audience and clear purpose.
- [ ] Columns are optimized for triage rather than "everything useful."
- [ ] Broad public views are limited and intentional.
- [ ] Compact layout fields support record recognition in highlights and mobile contexts.
- [ ] Search-result tuning is treated separately from list-view tuning.
- [ ] The design is validated with a real persona and container, not only with admin assumptions.

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Compact layouts do not replace page layouts** - they support recognition and highlights, not full editing or detailed field placement.
2. **Search layout fixes do not change list views** - teams often edit the wrong metadata because both features display columns.
3. **List-view sprawl is a governance problem, not just a UX problem** - once everyone can create broad public views freely, the object becomes harder to navigate and harder to support.
4. **Field visibility in the UI is still bounded by security** - if a user cannot access a field, layout design alone will not make it usable.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Browse-and-scan UX recommendation | Guidance on which surfaces should use list views, compact layouts, or search-result tuning |
| Configuration review findings | Issues such as over-wide columns, weak filters, and missing high-signal highlight fields |
| Object worksheet | Persona-specific inventory of list views, compact layouts, and search-result intent |

---

## Related Skills

- `admin/record-types-and-page-layouts` - use when the real design issue is record type separation, page layouts, or Dynamic Forms.
- `admin/reports-and-dashboards` - use when the team needs analytics, summarization, or scheduled reporting rather than operational list navigation.
- `lwc/lwc-data-table` - use when a custom component is replacing standard list experiences and needs deliberate column and action design.
