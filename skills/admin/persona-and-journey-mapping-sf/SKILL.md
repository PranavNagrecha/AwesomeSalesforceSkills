---
name: persona-and-journey-mapping-sf
description: "Build Salesforce-anchored personas and journey maps where every persona ties to a Permission Set Group, primary record types, list views, dashboards, automation, and a measured mobile/desktop posture, and journeys walk each task end-to-end with friction tags that drive UX decisions. NOT for stakeholder authority / RACI (use admin/stakeholder-raci-for-sf-projects), NOT for system-side process flows (use admin/process-flow-as-is-to-be), NOT for Lightning page design itself (use admin/lightning-app-builder-advanced or the lightning-record-page-auditor agent), NOT for pure design / UX research disconnected from org artifacts."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - User Experience
  - Operational Excellence
  - Performance
triggers:
  - "persona journey map salesforce"
  - "user persona salesforce features"
  - "salesforce mobile vs desktop persona"
  - "map sales rep journey to record page friction"
  - "service agent persona dashboard list view PSG"
  - "tie persona to permission set group and record type"
  - "find friction points in user journey for dynamic forms quick actions"
tags:
  - persona-and-journey-mapping-sf
  - persona-design
  - journey-map
  - user-experience
  - permission-set-group
  - mobile-vs-desktop
  - friction-analysis
inputs:
  - "list of user roles and counts in scope (target Permission Set Groups, profiles, record types)"
  - "primary tasks each role performs and rough frequency (daily / weekly / monthly)"
  - "available org artifacts to anchor against: PSGs, record types, list views, dashboards, automation"
  - "measured (not assumed) mobile vs desktop usage split per role"
outputs:
  - "persona records (canonical schema) anchored to PSG + record types + list views + dashboards + automation + mobile/desktop posture"
  - "per-task journey maps with steps, frequency, friction points tagged from a fixed taxonomy, and desired outcome"
  - "a friction-to-fix backlog: which friction points need UI work (Dynamic Forms, Quick Actions, page redesign, list view tuning) vs automation (Flow, validation rule, assignment rule)"
  - "handoff JSON consumed by lightning-record-page-auditor, list-view-and-search-layout-auditor, path-designer, and UAT test design"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-28
---

# Persona And Journey Mapping (Salesforce-Anchored)

This skill activates when an admin, BA, or architect needs to define **who actually
uses the org and how**, in a way that drives concrete Salesforce configuration
decisions rather than abstract UX deliverables. Every persona must anchor to org
artifacts the platform exposes — Permission Set Groups, record types, list views,
dashboards, automation — and every journey must walk a real task with measured
friction so the output feeds downstream auditing and design agents.

---

## Before Starting

Gather this context before producing any persona artifact:

- The **list of in-scope roles** and their headcount. Roles without users are noise.
- The **target Permission Set Group(s)** for each role — if the PSG does not yet
  exist, flag it; do not invent one. Personas without a PSG anchor become opinion
  pieces.
- The **primary record types** each role touches and the **list views** they live
  in. These are observable, not invented.
- **Mobile vs desktop usage**, ideally measured (Lightning Usage app, login
  history, EventLogFile UriEvent / LightningPerformance) — never assumed.
- **Dashboards** the role consumes daily/weekly. If a dashboard is named in a
  persona but does not exist in the org, it is a hallucination — flag it.
- The **automation** that fires for the role (record-triggered Flow, validation
  rules, assignment rules, approval processes, Agentforce topics) — captured by
  metadata, not memory.

---

## Core Concepts

### Persona = User × Org Artifacts

A Salesforce-anchored persona is the join between a *user population* and the
*concrete artifacts* the platform uses to constrain and serve them. The five
anchors are non-negotiable: PSG (what they can do), record types (what they
work on), list views (what they see), dashboards (how they measure success),
automation (what fires for them). A persona missing any anchor cannot drive a
configuration decision.

### Mobile vs Desktop Posture

Salesforce mobile (the Salesforce app) and Lightning Experience desktop are
different products with different UX rules: mobile favors Compact Layouts,
mobile-only Quick Actions, and brief related-list summaries; desktop favors
Dynamic Forms, multi-tab record pages, and dense related lists. The
mobile_pct / desktop_pct split — **measured, not guessed** — is what tells you
which surface to optimize. A 70% mobile field rep persona and a 95% desktop
SDR persona need very different record pages even on the same object.

### Journey Map vs Process Flow

A journey map is **persona-first**: one persona, one task, every step
they take, with friction tagged. A process flow is **system-first**: the
sequence of system events regardless of who triggers them. Journey maps drive
UX decisions (Dynamic Forms, Quick Actions, page redesign, path); process
flows drive automation decisions (Flow vs Apex, callouts, approvals). Do not
conflate them. If you find yourself describing a callout, you are writing a
process flow — stop and switch artifacts (`admin/process-flow-as-is-to-be`).

### Friction Taxonomy (Fixed Enum)

Every friction point must be tagged from this enum so downstream agents can
route work:

| Friction Tag | Meaning | Typical Fix |
|---|---|---|
| `cognitive_load` | Too many fields, sections, or related lists in view at once | Dynamic Forms, conditional visibility, page redesign |
| `click_count` | Task takes more navigation clicks than necessary | Quick Action, Path step, list view inline edit, related list tuning |
| `mode_switch` | Forces user from mobile→desktop or app→browser mid-task | Mobile-friendly Quick Action, mobile-aware Lightning page, offline-capable LWC |
| `data_input` | Repeated typing, no defaults, no picklist where appropriate | Default field values, validation rule with a useful message, picklist conversion |
| `search` | User cannot find a record, list view, or related item | List view tuning, search layout, pinned list views, Einstein Search config |

---

## Common Patterns

### Pattern: PSG-First Persona Sketch

**When to use:** brand-new persona work, or when an existing persona doc has
drifted from org reality.

**How it works:** start from the PSG (or planned PSG) — extract assigned
object permissions, record types, layouts, and tabs. Bind that to a named
persona. Every claim in the persona profile must trace back to a PSG, a
record type, a list view, a dashboard, or an automation in the org.

**Why not the alternative:** title-based personas ("Sales Rep") describe a
stereotype, not a user. They drift, they collide, and they cannot be audited.

### Pattern: One Task Per Journey Map

**When to use:** every primary persona task — captured one task per journey
artifact, not bundled.

**How it works:** the journey artifact has a single `task` (e.g. "Log a
visit", "Triage an inbound case", "Update opportunity stage to Negotiation"),
the frequency (daily / weekly / monthly / quarterly), the steps in order,
the friction tag on each problematic step, and the **next task** the persona
moves to (so the journey doesn't end at "saves record").

**Why not the alternative:** combining tasks into a single map produces a
deliverable nobody reads and a friction list nobody can route.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Asked for personas with no PSG roadmap yet | Flag the gap. Do not write personas; write a PSG sketch first. | Personas without PSG anchors cannot be audited or kept current. |
| Asked to map mobile vs desktop and no measurement exists | Flag the gap. Pull from Lightning Usage app or EventLogFile, then resume. | Inventing mobile_pct corrupts every downstream UX decision. |
| Persona task ends at "record saved" | Extend it — what task does the persona do next, on what surface? | A journey that ends at save misses the most common friction (mode switch to next task). |
| 9+ personas in a single phase | Reduce to ≤7 by merging adjacent personas. | More than 7 personas is noise; signal-to-decision ratio collapses. |
| Persona references a dashboard nobody can find in the org | Remove or replace with a real dashboard | Hallucinated artifacts make the persona untrustworthy. |
| Friction tag does not fit the taxonomy | Either re-frame to fit the enum or capture as `notes` | Free-text tags break the routing handoff. |

---

## Recommended Workflow

1. **Identify personas from PSG roadmap.** Pull the planned (or current) Permission
   Set Groups; one persona per distinct user population the PSGs serve. If a
   PSG covers two distinct populations with different journeys, split it.
2. **Anchor each persona to org artifacts.** Fill the canonical schema:
   `psg_assigned`, `primary_record_types[]`, `primary_list_views[]`,
   `dashboards[]`, `automation_touched[]`, and the measured `mobile_pct` /
   `desktop_pct`. No anchor → not a persona.
3. **Build a journey map per primary task.** One task per artifact. Record
   frequency, every step in order, friction points tagged from the fixed
   taxonomy, and the next task the persona transitions to.
4. **Flag friction that needs UI work.** `cognitive_load`, `click_count`, and
   `mode_switch` typically route to record-page redesign, Quick Actions, Path,
   or Dynamic Forms — handed off to `lightning-record-page-auditor`.
5. **Flag friction that needs automation.** `data_input` and some `click_count`
   friction routes to Flow, defaults, validation rules, or assignment rules —
   handed off to the automation agents.
6. **Hand off to downstream agents.** Emit the handoff JSON: persona id, anchor
   artifacts, friction backlog, and target agents
   (`lightning-record-page-auditor`, `list-view-and-search-layout-auditor`,
   `path-designer`, plus UAT test design which runs each case as a persona).
7. **Revisit per release.** Personas drift as PSGs and record types change;
   re-run the anchor check every release train.

---

## Canonical Persona Schema

```json
{
  "persona_id": "outside_sales_rep",
  "name": "Outside Sales Rep",
  "headcount": 42,
  "psg_assigned": "PSG_Sales_Field",
  "primary_record_types": ["Account.Customer", "Opportunity.Field_Deal", "Visit__c.Standard"],
  "primary_list_views": ["My_Open_Opps_This_Week", "Visits_Due_Today"],
  "dashboards": ["Field_Sales_Daily"],
  "mobile_pct": 70,
  "desktop_pct": 30,
  "automation_touched": [
    "Flow:Visit_After_Save",
    "ValidationRule:Opp.Field_Stage_Required_Fields",
    "AssignmentRule:Lead_Field_Territory"
  ]
}
```

## Canonical Journey Schema

```json
{
  "persona_id": "outside_sales_rep",
  "task": "Log a customer visit between meetings",
  "frequency": "daily",
  "steps": [
    {"step": "Open Salesforce mobile app", "surface": "mobile"},
    {"step": "Tap Visits Due Today list view", "surface": "mobile"},
    {"step": "Open visit, tap Log Visit Quick Action", "surface": "mobile"},
    {"step": "Enter notes, attendees, next step", "surface": "mobile", "friction": "data_input"},
    {"step": "Save", "surface": "mobile"},
    {"step": "Move to next visit on list", "surface": "mobile"}
  ],
  "friction_points": [
    {"step_index": 3, "tag": "data_input", "note": "No default for Visit Type; user retypes territory each time"}
  ],
  "desired_outcome": "Visit logged in <60s without leaving the mobile app",
  "next_task": "Drive to next account and repeat"
}
```

## Handoff JSON Shape

```json
{
  "personas": [ /* persona records */ ],
  "journeys": [ /* journey records */ ],
  "friction_backlog": [
    {
      "persona_id": "outside_sales_rep",
      "task": "Log a customer visit between meetings",
      "friction_tag": "data_input",
      "recommended_target": "lightning-record-page-auditor",
      "recommended_intervention": "Default Visit Type from territory; review mobile compact layout"
    }
  ]
}
```

---

## Review Checklist

- [ ] Every persona is anchored to a real PSG (planned or existing).
- [ ] Every persona lists ≥1 record type, ≥1 list view, and ≥1 dashboard from the org.
- [ ] `mobile_pct + desktop_pct ≈ 100` (within ±2 for rounding) and the source of the measurement is named.
- [ ] Every primary task has its own journey artifact with ≥3 steps.
- [ ] Every friction point uses a tag from the fixed enum.
- [ ] Every journey names the `next_task`; none end at "save".
- [ ] Persona count for the phase is ≤ 7.
- [ ] Friction backlog routes each item to a downstream agent.

---

## Salesforce-Specific Gotchas

1. **PSG drift after release.** PSGs change between releases as new objects ship; re-run anchor checks every release train or personas go stale silently.
2. **Mobile usage measurement gaps.** Lightning Usage app shows desktop-only by default; you must enable Mobile App usage and EventLogFile UriEvent to get the real split.
3. **List view personalization invisible to admins.** Users create personal list views the admin never sees; persona list-view anchors should bias to shared list views or you misread the journey.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| `personas.json` | Array of persona records following the canonical schema. |
| `journeys.json` | Array of journey records, one per persona-task pair. |
| `friction_backlog.json` | Routed friction items with target agent and recommended intervention. |
| `handoff.json` | Combined handoff envelope consumed by downstream auditing agents. |

---

## Related Skills

- `admin/stakeholder-raci-for-sf-projects` — Use for stakeholder authority and decision rights, not user-facing persona work.
- `admin/process-flow-as-is-to-be` — Use for system-side process flows; this skill stays user-facing.
- `admin/lightning-app-builder-advanced` — Use for the actual record page build once friction is identified.
- `agents/lightning-record-page-auditor` — Downstream audit agent that consumes per-persona record page friction.
- `agents/list-view-and-search-layout-auditor` — Downstream agent for `search` and list-view friction.
- `agents/path-designer` — Downstream agent for per-record-type path design driven by journey stages.
