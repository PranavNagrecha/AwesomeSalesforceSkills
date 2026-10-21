# Related List Configuration — Work Template

Use this template when configuring or auditing related lists on a record page.

UNVERIFIED (2026-10-21), applies to this file: whether "Enhanced Related Lists" is a separate Lightning App Builder component or a list-type setting on `Related Lists` / `Related List - Single`, the 10-column cap, the mobile column count, and that column choice cannot be made in Lightning App Builder (the "not Lightning App Builder" checklist line) — Salesforce Help only.

## Scope

**Skill:** `related-list-configuration`

**Request summary:** (one sentence — e.g., "reduce Contacts related list on Account Sales page from 12 columns to 10 and re-sort by LastModifiedDate descending")

## Context Gathered

- **Object + relationship:** (e.g., Account → Contacts)
- **Affected Page Layout(s):** (list each layout name and its assigned Profile × Record Type)
- **Lightning record page hosting the related list:** (name + which component is used: Related Lists / Related List - Single / Enhanced Related Lists / Related Lists - Quick Links)
- **User populations affected:** (which Profiles and record types — mobile + desktop)
- **Current column set + count (per related list):**
  - Layout A:
  - Layout B:
- **Current sort field + direction:**
- **FLS notes for the affected fields:**
- **Org uses the Enhanced list type?** (yes/no — release date UNVERIFIED)

## Approach

**Pattern from SKILL.md:**
- [ ] Pattern 1 — Classic Related Lists block (small page, no per-list filter need)
- [ ] Pattern 2 — Enhanced Related Lists for the one list that needs filtering / mass actions
- [ ] Pattern 3 — Per-record-type Page Layout divergence

**Component choice on the Lightning record page:**
- [ ] All-in-one `Related Lists` block
- [ ] `Related List - Single` per list
- [ ] `Enhanced Related Lists`
- [ ] `Related Lists - Quick Links` as anchor bar (paired with one of the above)

**Rationale (why this component, not the alternative):**

## Plan

1. Edit Page Layout `<name>`: columns → [list, ≤10 per Help (UNVERIFIED cap)], sort field → `<field>` (`Asc`/`Desc`).
2. (If per-record-type divergence) Edit Page Layout `<name>`: ...
3. Record any intentional divergence in the change record (Layout metadata has no description field).
4. (If component change) Update Lightning record page in App Builder: swap to `<component>`.
5. Run `check_related_list_configuration.py --manifest-dir force-app/main/default`; impersonate a user from each affected (Profile × Record Type) combination.
6. Verify mobile: the first columns are the customer-facing ones (mobile column count UNVERIFIED).

## Review Checklist

- [ ] Edited the Page Layout that the affected (Profile × Record Type) resolves to (not Lightning App Builder)
- [ ] No classic related list exceeds 10 columns (Help-only cap, UNVERIFIED)
- [ ] Sort field is a directly stored scalar on the child (unsortable-type list UNVERIFIED)
- [ ] If Enhanced Related Lists, the filter / mass-action features are actually used
- [ ] Per-record-type divergence is recorded in the change record (no Layout description field)
- [ ] Mobile column order verified (most user-critical first)
- [ ] FLS for each column is consistent with intent (field permissions govern related lists, secguide 262 L621)
- [ ] `lookupDialogsAdditionalFields` / `lookupFilterFields` / `searchFilterFields` on the parent's search layouts cover what users need
- [ ] Affected users warned that a component swap may reset per-user column widths (UNVERIFIED)

## Notes / Deviations

(Record any deviations from the standard pattern and why — e.g., "kept an 11-column related list because the org accepts that the seasonal-promo field may not render inline").
