---
name: soql-for-view-and-for-reference
description: "Use when a SOQL query that serves a custom record-viewing surface (custom LWC/Aura/Visualforce page, mobile app, or API client) must make the retrieved records show up in the user's Recent Items and global-search auto-complete by writing LastViewedDate / LastReferencedDate and a RecentlyViewed row via the optional FOR VIEW / FOR REFERENCE clauses. Covers which clause to pick, correct grammar placement, the misuse warning, the RecentlyViewed 90-day / 200-per-object lifecycle, and the custom-object custom-tab prerequisite. Standard Lightning record pages already write recency for you. NOT for FOR UPDATE row locking — use apex/record-locking-and-contention. NOT for scoping a query to Mine / Team / Territory — use apex/soql-using-scope-clause."
category: apex
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Performance
triggers:
  - "mark a record as recently viewed from my custom LWC so it appears in Recent Items"
  - "populate LastViewedDate or LastReferencedDate when a user opens a record on a custom page"
  - "make records show in global-search auto-complete after a user views them in my mobile app"
  - "deciding whether to use FOR VIEW or FOR REFERENCE on a SOQL query and which one is correct"
  - "why is my Recently Viewed list showing records nobody actually opened"
tags:
  - soql-for-view-and-for-reference
  - for-view
  - for-reference
  - recently-viewed
  - last-viewed-date
inputs:
  - "The SOQL query (or selector method) that fetches records for a custom record-viewing surface"
  - "The execution context: is a logged-in user actually viewing the retrieved records in this request, or is this batch/trigger/async/integration code?"
  - "Whether the surface is a full record view (FOR VIEW) or a lighter reference such as a mobile card or custom page (FOR REFERENCE)"
outputs:
  - "A correctly placed FOR VIEW / FOR REFERENCE clause on a bounded, user-facing query"
  - "Guidance on which recency field (LastViewedDate / LastReferencedDate) is written and how it surfaces in Recent Items and search auto-complete"
  - "A misuse audit that flags the clause in bulk / async / system-context code where the records will not actually be viewed"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-07-08
---

# SOQL FOR VIEW and FOR REFERENCE

This skill activates when a custom record-viewing surface — a Lightning web component, Aura component, Visualforce page, mobile app, or API client — must make the records it fetches behave like records the user "opened": appear in **Recent Items** and in the **global-search auto-complete** list. Standard Lightning record pages get this for free; a custom surface that runs its own SOQL does not, and must opt in with the optional `FOR VIEW` or `FOR REFERENCE` clause. These clauses turn a read into a read-plus-write: they update `LastViewedDate` / `LastReferencedDate` and add a `RecentlyViewed` row for each retrieved record. Misused, they silently pollute the user's recency data — Salesforce documents an explicit warning against that.

The official SOQL and SOSL Reference documents both clauses as current (Summer '26 / API 67.0) and does **not** stamp them Beta, Pilot, or deprecated. Do not assert a maturity level the docs do not state.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Confirm a real user is viewing these records in *this* request.** The single controlling rule from the docs: use the clauses "only when you are sure that the retrieved records will definitely be viewed by the logged-in user, else the clause incorrectly updates the usage information for the records." Code that runs in a batch, trigger, `@future`, Queueable, scheduled job, or integration-user context almost never satisfies this.
- **Know that this is a write, not just a read.** A `SELECT ... FOR VIEW` mutates data (`LastViewedDate` and a `RecentlyViewed` insert). That has cost and context implications a plain query does not.
- **Confirm the object exposes the recency fields.** Standard objects that track recency (Account, Contact, custom-tab-backed objects, etc.) have `LastViewedDate` / `LastReferencedDate`. A **custom object has these fields only after a custom tab is created for it** — otherwise the query fails with `No such column 'LastViewedDate'`.
- **Decide FOR VIEW vs FOR REFERENCE.** `FOR VIEW` = the user is *viewing* the record (full view). `FOR REFERENCE` = the record is *referenced* from a custom interface without a full page view (mobile app, custom page).

---

## Core Concepts

### The two clauses and what each one writes

Both clauses are optional trailing SOQL clauses. Each performs two writes per retrieved record:

- **`FOR VIEW`** — "Use the optional FOR VIEW clause in a SOQL query to update objects with information about when they were last viewed." It updates `LastViewedDate` for the retrieved record and adds an entry to the `RecentlyViewed` object.
- **`FOR REFERENCE`** — "Use the optional FOR REFERENCE in a SOQL query to notify Salesforce when a record is referenced from a custom interface, such as in a mobile application or from a custom page." It updates `LastReferencedDate` and, like `FOR VIEW`, inserts a `RecentlyViewed` row.

`LastViewedDate` drives the **Recent Items** list; `LastReferencedDate` reflects a lighter "the user saw a reference to this" signal. Both feed the global-search auto-complete / most-recently-used surface.

### Where the clauses sit in SOQL grammar

The clauses are near the end of the `SELECT` statement, after `ORDER BY`, `LIMIT`, and `OFFSET`, and before the `UPDATE {TRACKING | VIEWSTAT}` and `FOR UPDATE` clauses:

```
[ORDER BY ...]
[LIMIT n]
[OFFSET n]
[{FOR VIEW | FOR REFERENCE}]
[UPDATE {TRACKING | VIEWSTAT}]
[FOR UPDATE]
```

Minimal working syntax (straight from the docs):

```sql
SELECT Name, Id FROM Contact LIMIT 1 FOR VIEW
SELECT Name, Id FROM Contact LIMIT 1 FOR REFERENCE
```

### Updating both recency fields ("in conjunction with")

To refresh both recency fields, the docs say: "To update recent usage data for retrieved objects, use the FOR VIEW clause in conjunction with the FOR REFERENCE clause." Note the nuance: the reference shows the two clauses **only individually** and gives **no combined single-query example**, and the `SELECT` grammar presents them as an alternation `{FOR VIEW | FOR REFERENCE}`. In practice, pick the one clause that matches the surface (a real view → `FOR VIEW`; a reference → `FOR REFERENCE`); treat "update both fields from one query" as under-specified rather than asserting a combined syntax the reference does not print.

### The RecentlyViewed lifecycle

`RecentlyViewed` is ephemeral, not an audit log:

- "RecentlyViewed data is retained for 90 days, after which it is removed on a periodic basis."
- "RecentlyViewed data is periodically truncated down to 200 records per object."

So a record can silently drop out of Recent Items after 90 days, or once it falls outside the newest 200 rows for its object. Never build reporting or compliance logic on top of `RecentlyViewed`.

---

## Common Patterns

### Custom record viewer marks the record viewed (FOR VIEW)

**When to use:** a custom LWC/Aura/Visualforce page loads a single record for the user to read, replacing what a standard record page would have done, and you want that record to land in Recent Items.

**How it works:** in the selector layer, fetch the specific record by Id with a `LIMIT` and append `FOR VIEW`. The controller passes the opened record's Id; the query touches exactly that record.

```sql
SELECT Id, Name, StageName FROM Opportunity WHERE Id = :recordId LIMIT 1 FOR VIEW
```

**Why not the alternative:** without the clause the record never enters Recent Items from your custom surface (the platform only writes recency for standard pages). Writing `LastViewedDate` yourself via a `Database.update` is both unnecessary and, for `RecentlyViewed`, impossible — the clause is the supported mechanism.

### Lightweight reference from a mobile app or custom page (FOR REFERENCE)

**When to use:** a mobile client or custom page surfaces a record as a reference — a card, a preview, a lookup result — without a full page view, and you want a "recently referenced" signal.

**How it works:** same shape, `FOR REFERENCE` instead, writing `LastReferencedDate`:

```sql
SELECT Id, Name FROM Account WHERE Id = :accountId LIMIT 1 FOR REFERENCE
```

**Why not the alternative:** using `FOR VIEW` here overstates the interaction (the user did not open the record), inflating the Recent Items list with things the user only glanced at a reference to.

### Keep it bounded and user-scoped (misuse guard)

**When to use:** always, whenever either clause is present.

**How it works:** constrain the query to the specific record(s) the user is looking at (a `WHERE Id = :id` / `WHERE Id IN :ids`), add a `LIMIT`, and run it in user mode (`WITH USER_MODE` / `AccessLevel.USER_MODE`). This guarantees the clause only writes usage data for records the user can actually see and is actually viewing.

**Why not the alternative:** an unbounded `SELECT ... FOR VIEW` (no `WHERE`, no `LIMIT`) stamps `LastViewedDate` on up to the query's whole result set, flooding the user's Recent Items with records they never opened — exactly the misuse the docs warn against.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Custom UI shows a full view of a record | `FOR VIEW` on a bounded, by-Id query | Writes `LastViewedDate`; record enters Recent Items |
| Mobile app / custom page references a record without a full view | `FOR REFERENCE` | Writes `LastReferencedDate`; "recently referenced" signal |
| You believe you need both recency fields updated | Pick the clause matching the actual interaction; treat "both from one query" as under-documented | Reference shows the clauses only individually, no combined example |
| Batch / trigger / `@future` / Queueable / scheduled / integration user | Neither clause | No logged-in user is viewing the records — the docs' misuse condition |
| Standard Lightning record page | Neither clause | The platform already writes recency for standard views |
| Aggregate query (`COUNT()`, `GROUP BY`) | Neither clause | There are no individual records for the user to "view" |
| Custom object with no tab | Create a custom tab first (need not be visible), then use the clause | Fields do not exist until a tab is defined |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Verify the context.** Confirm a logged-in user is about to view (or reference) the retrieved records in this exact request. If the code path is batch, trigger, `@future`, Queueable, scheduled, or runs as an integration user, stop — do not add the clause.
2. **Pick the clause.** `FOR VIEW` for a full record view; `FOR REFERENCE` for a lighter reference from a custom interface. If you think you need both recency fields, choose the one that matches the real interaction rather than inventing a combined form.
3. **Bound the query.** Add a specific `WHERE` (the record Id / Ids the user opened) and a `LIMIT`, and keep the query in user mode so it can only touch records the user can see.
4. **Check field availability.** Confirm the target object exposes `LastViewedDate` / `LastReferencedDate`. For a custom object, ensure a custom tab exists (visibility not required) or the query throws `No such column`.
5. **Place and locate the clause.** Put it after `ORDER BY` / `LIMIT` / `OFFSET` and before `FOR UPDATE`, and keep the query in the selector layer (see `templates/apex/BaseSelector.cls`), not duplicated across controllers or inside loops.
6. **Run the checker and verify.** Run `scripts/check_soql_for_view_and_for_reference.py` over the Apex source, then open the surface as a test user and confirm the viewed record appears in Recent Items / search auto-complete — and that unrelated records were not polluted.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] A real, logged-in user is viewing the retrieved records in this request (not batch / async / trigger / integration code)
- [ ] The correct clause is used: `FOR VIEW` for a full view, `FOR REFERENCE` for a lighter reference — no invented combined syntax
- [ ] The query is bounded (specific `WHERE` + `LIMIT`) and runs in user mode, so only records the user can see get their usage data updated
- [ ] The target object exposes `LastViewedDate` / `LastReferencedDate` (custom objects have a custom tab)
- [ ] The clause is positioned correctly in the grammar and lives in the selector layer, not scattered across controllers or inside loops
- [ ] No `FOR VIEW` / `FOR REFERENCE` on aggregate (`COUNT()` / `GROUP BY`) queries
- [ ] Manually verified Recent Items / search auto-complete updates for the viewed record and only that record

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **A "read" that writes** — `SELECT ... FOR VIEW` performs DML side-effects (updates `LastViewedDate` and inserts `RecentlyViewed` rows). It looks like a query in code review but mutates data, which is why it must not run where no user is actually viewing the records.
2. **Misuse silently corrupts the user's experience** — the docs warn to use the clauses "only when you are sure that the retrieved records will definitely be viewed by the logged-in user, else the clause incorrectly updates the usage information for the records." A single unbounded query can flood Recent Items and search auto-complete with noise.
3. **Custom objects fail until they have a tab** — querying `LastViewedDate` / `LastReferencedDate` (or using these clauses) on a custom object without a custom tab throws `No such column`. Creating the tab — even one hidden from the navigation bar — enables the fields.
4. **`RecentlyViewed` is not permanent** — data is retained 90 days then removed periodically, and is truncated to 200 records per object. Do not treat it as an audit trail or build compliance logic on it.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| `FOR VIEW` / `FOR REFERENCE` clause | Appended to a bounded, user-facing selector query at the correct grammar position |
| `scripts/check_soql_for_view_and_for_reference.py` report | Flags the clauses in bulk / async / system-context code, on unbounded or aggregate queries |
| `templates/soql-for-view-and-for-reference-template.md` | Decision worksheet + canonical safe selector snippet for a custom record viewer |

---

## Related Skills

- `apex/soql-fundamentals` — the base `SELECT` statement grammar these clauses attach to; read it for clause ordering and query structure.
- `apex/soql-using-scope-clause` — the **read** side of the same recency data: `USING SCOPE mru` / `USING SCOPE mine` filters by what the user recently used, which is what `FOR VIEW` / `FOR REFERENCE` populate.
- `lwc/lwc-imperative-apex` — the controller pattern a custom record viewer uses to call the selector that carries the `FOR VIEW` clause.
