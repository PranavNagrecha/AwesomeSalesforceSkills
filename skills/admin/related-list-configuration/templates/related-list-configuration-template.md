# Related List Configuration — Work Template

Use this template when configuring or auditing related lists on a record page.

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
- **Org has Enhanced Related Lists enabled?** (yes/no — Spring '24+ feature)

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

1. Edit Page Layout `<name>`: columns → [list, ≤10 for classic], sort field → `<field>` (`Asc`/`Desc`).
2. (If per-record-type divergence) Edit Page Layout `<name>`: ...
3. Update Page Layout description to document any intentional divergence.
4. (If component change) Update Lightning record page in App Builder: swap to `<component>`.
5. Verify: impersonate user from each affected (Profile × Record Type) combination.
6. Verify mobile: first 4 columns are the customer-facing ones.

## Review Checklist

- [ ] Edited the Page Layout that the affected (Profile × Record Type) resolves to (not Lightning App Builder)
- [ ] No classic related list exceeds 10 columns
- [ ] Sort field is a sortable, directly stored scalar (not a cross-object formula, long text, base64, encrypted text)
- [ ] If Enhanced Related Lists, the filter / mass-action features are actually used
- [ ] Per-record-type divergence is documented in the layout description
- [ ] Mobile column order verified (top 4 are user-critical)
- [ ] FLS for each column is consistent with intent (no surprise blank cells)
- [ ] Search Filter Fields on the parent object include the columns users will type into the lookup dialog
- [ ] Affected users notified if the component swap reset per-user column-width preferences

## Notes / Deviations

(Record any deviations from the standard pattern and why — e.g., "kept 11-column related list because the org accepts the silent drop for the seasonal-promo field that admins remove each quarter").
