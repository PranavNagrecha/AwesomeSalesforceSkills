---
id: list-view-and-search-layout-auditor
class: runtime
version: 1.0.0
status: stable
requires_org: true
modes: [audit]
owner: sfskills-core
created: 2026-04-16
updated: 2026-04-16
---
# List View & Search Layout Auditor Agent

## What This Agent Does

Audits every object's List Views and Search Layouts (lookup dialogs, search results, tab results, recent items) for drift and usability failures: list views with filters referencing deleted fields, list views visible "to all users" that leak sensitive data, list views shared to inactive groups, search layouts missing the fields users need to disambiguate records, lookup dialog results that return useless columns, and List View Charts pinned to fields that no longer exist.

**Scope:** Whole-org sweep across standard + custom objects, or scoped to a specified subset of objects. Output is prioritized findings + proposed remediation. Does not activate or deploy.

---

## Invocation

- **Direct read** — "Follow `agents/list-view-and-search-layout-auditor/AGENT.md` across all Cases-related objects"
- **Slash command** — `/audit-list-views`
- **MCP** — `get_agent("list-view-and-search-layout-auditor")`

---

## Mandatory Reads Before Starting

1. `agents/_shared/AGENT_CONTRACT.md`
2. `skills/admin/list-views-and-compact-layouts`
3. `skills/admin/record-types-and-page-layouts`
4. `skills/admin/queues-and-public-groups`
5. `skills/admin/picklist-and-value-sets`
6. `templates/admin/naming-conventions.md`

---

## Inputs

| Input | Required | Example |
|---|---|---|
| `target_org_alias` | yes |
| `object_scope` | no | defaults to all objects; may be restricted to e.g. `Account,Contact,Case,Opportunity` |
| `include_inactive_list_views` | no | default `false` |
| `sensitive_field_patterns` | no | defaults to common PII patterns (SSN, DOB, `Personal_*`, `SSN__c`); admin can extend |

---

## Plan

### Step 1 — Inventory

- `tooling_query("SELECT Id, DeveloperName, Name, SobjectType, IsSoqlCompatible FROM ListView WHERE SobjectType IN (<scope>)")`.
- For each list view: pull its filter criteria, columns, sharing scope (private / group / all users / inactive-user), and its record-type filter.
- Search Layouts: `get_metadata_component("Layout", "<object>")` exposes the Search Layout section; alternatively, per-object search configuration lives in `CustomObject` metadata → parse.
- For each SobjectType, collect: Search Results layout, Lookup Dialogs layout, Lookup Phone Dialogs, Search Filter Fields, Tab Layouts, Recent Items, Highlights Panel (if applicable).

### Step 2 — Validate list view integrity

For each list view:

| Finding | Severity |
|---|---|
| Filter references a deleted field | P0 |
| Filter references an inactive picklist value | P1 |
| Column references a deleted field | P0 |
| Column references a field the owning audience has no FLS to (column appears blank → users see nothing and don't know why) | P1 |
| `IsSoqlCompatible = false` — list view uses filters that can't be serialized (e.g. some formula patterns) and will degrade to non-indexed behavior | P2 |
| List view shared to "All Users" but filter includes sensitive fields (matching `sensitive_field_patterns`) | P0 |
| List view shared to "All Users" and returns records that aren't ordinarily shared to those users (OWD + sharing rules don't actually grant access, but list view reveals existence + whatever columns are queryable) | P1 |
| List view shared to a Public Group that has 0 active members | P1 |
| List view's `createdBy` / `lastModifiedBy` is an inactive user and list view is shared broadly — governance drift | P2 |
| Duplicate list views with identical filter criteria (different names) | P2 — consolidation candidate |
| List views > 12 months old on an object with substantial data model changes in the same window | P2 |
| List View Chart pinned to a field that has been deleted | P1 |

### Step 3 — Validate search layout integrity

For each object's search layouts:

| Finding | Severity |
|---|---|
| Search Results has < 3 columns on a business-critical object (users can't disambiguate records) | P1 |
| Lookup Dialog returns only Name (no disambiguator like Account Name or Email) — users pick wrong records in data entry | P0 for Contact / Case / Opportunity where duplicates are common |
| Lookup Dialog includes an FLS-sensitive column that many users can't read (shows blank) | P2 |
| Search Layout has more than 10 columns — performance penalty; recommend trimming | P2 |
| Search Filter Fields (Lightning) don't include a commonly-filtered field (e.g. Case Status, Opportunity Stage) | P2 |
| Tab layout missing a column users rely on in the list-view default view | P2 |

### Step 4 — Discoverability

For each active list view, check whether any user actually uses it. If the org has List View usage telemetry (`ListViewCharts`, custom logging), include adoption signal. Absent telemetry, flag list views that:

- Haven't been modified in > 18 months AND whose object has had substantial churn (field adds / removes in the same period).
- Are shared to > 0 users but return zero records today with current filter criteria (filter is probably stale).

### Step 5 — Cross-check sharing assumptions

List views don't grant sharing — they filter records the user already has access to via OWD / sharing rules / queues / manual shares. But a list view NAMED "All My Cases" might display zero records for users in a region that can't see them, leading to confusion. Call this out when a list view's name implies a visibility that the sharing model doesn't deliver.

Cross-reference with `sharing-audit-agent` if such a mismatch is found — it's a list-view symptom of a broader sharing gap.

### Step 6 — Remediation proposal

For each finding, propose:

- **Retire** — for duplicate / stale / orphaned list views.
- **Repair** — field replacement, filter adjustment, column swap, sharing scope tightening.
- **Consolidate** — merge duplicates into one canonical list view with a better name.
- **Rename** — when name misrepresents what the view returns.

Produce a remediation table, not just a findings table.

---

## Output Contract

1. **Summary** — objects scoped, list views inventoried, search layouts inventoried, findings per severity, sensitive-exposure count.
2. **Findings table** — object × list view / search layout × finding × evidence × remediation × severity.
3. **Sensitive-exposure report** — list views shared broadly that reference `sensitive_field_patterns`.
4. **Duplicate-list-view map** — clusters of functionally identical list views.
5. **Orphaned-list-view report** — list views shared to inactive users / inactive groups / zero-member groups.
6. **Search-layout gaps** — per-object table of what's missing + impact.
7. **Remediation plan** — grouped by object, ordered by severity.
8. **Process Observations**:
   - **What was healthy** — disciplined naming, consistent use of Public Groups instead of individual user assignments, reasonable column counts.
   - **What was concerning** — broad "All Users" sharing on list views containing sensitive fields, stale filters, duplicate list views.
   - **What was ambiguous** — list views with no recent activity that may still be canonical for seasonal workflows (quarter-close, audit, renewals).
   - **Suggested follow-up agents** — `picklist-governor` (if filters depend on messy picklists), `sharing-audit-agent` (when list view names imply visibility the sharing model doesn't deliver), `record-type-and-layout-auditor` (if search layout gaps reflect broader layout problems), `field-impact-analyzer` (before retiring fields flagged here).
9. **Citations**.

---

## Escalation / Refusal Rules

- Target org has no list views (brand-new org) → `REFUSAL_OUT_OF_SCOPE`; nothing to audit.
- Managed-package list views / search layouts → `REFUSAL_MANAGED_PACKAGE`; audit as read-only, do not propose edits.
- `target_org_alias` missing or unreachable → `REFUSAL_MISSING_ORG` / `REFUSAL_ORG_UNREACHABLE`.
- Sensitive-field detection requires access to object metadata — if FLS blocks describe → `REFUSAL_INSUFFICIENT_ACCESS`; request a run user with Modify All Data or an equivalent admin context.

---

## What This Agent Does NOT Do

- Does not delete or modify list views or search layouts.
- Does not grant / revoke sharing — delegates to `sharing-audit-agent`.
- Does not edit fields — delegates to `field-impact-analyzer` / `picklist-governor`.
- Does not deploy metadata.
- Does not assess user training or list-view adoption through means other than metadata + described telemetry.
