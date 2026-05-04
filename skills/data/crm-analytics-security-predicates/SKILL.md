---
name: crm-analytics-security-predicates
description: "Row-level security in CRM Analytics datasets via security predicates — SAQL filter expressions stored on the dataset that apply at query time per running user. Covers the syntax (`'DatasetColumn' operator value`), the `$User.*` context variables, multi-level predicates (role hierarchy + team + region), the performance cost of complex predicates, and the testing discipline (admins bypass predicates by default). NOT for Salesforce Core sharing rules (different runtime), NOT for App / Dashboard / Lens-level access (that's CRM Analytics App sharing, not predicates), NOT for field-level masking inside a dataset (use Encryption + dataset transformations)."
category: data
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
  - Operational Excellence
triggers:
  - "crm analytics security predicate dataset row level security"
  - "saql filter user role hierarchy predicate"
  - "predicate user.id owner-only access"
  - "crm analytics predicate team membership account team"
  - "predicate performance cost slow dashboard"
  - "test predicate admin bypass non-admin user"
tags:
  - crm-analytics
  - security-predicate
  - row-level-security
  - saql
  - dataset
  - user-context
inputs:
  - "Dataset(s) the predicate will protect — name and field schema"
  - "Access model: owner-only / role-hierarchy / team-membership / region / multi-dimensional"
  - "Whether the running user has access to the source SObject (predicate doesn't replace SObject sharing — both apply)"
  - "Performance budget for the dashboards that consume this dataset"
outputs:
  - "Predicate expression string for the dataset"
  - "`$User.*` context variables required (and any custom User fields the predicate references)"
  - "Test plan covering owner / non-owner / admin / cross-team users"
  - "Performance baseline for predicate-protected vs unprotected query"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-05-04
---

# CRM Analytics Security Predicates

Row-level security in CRM Analytics. A **security predicate** is a SAQL
filter expression stored at the **dataset** level. Every query that
reads the dataset has the predicate applied automatically, scoped to
the running user's context (Id, role, profile, custom User fields).
The dataset's owner / admin doesn't see it; the running user does.

What this skill is NOT. Salesforce Core SObject sharing rules (Org-Wide
Defaults, role hierarchy, sharing rules, manual sharing, Apex managed
sharing) operate on the source records — predicates operate on the
dataset's *copy* of those records. Both can apply; they're independent.
App / Dashboard / Lens sharing is different — that's CRM Analytics
*Asset* sharing (who can open the dashboard at all), not row-level
filtering inside it. Field-level masking is a different control (use
Shield Platform Encryption or transform the dataset to omit / hash the
field).

---

## Before Starting

- **Confirm the dataset, not the dashboard, is the right level.**
  Predicates apply to the dataset, not to individual dashboards or
  lenses. A predicate set on a dataset filters every dashboard /
  lens / SAQL query that reads that dataset. If different audiences
  need different filtering, you may need separate datasets — or a
  predicate that varies per running user via `$User.*` rather than
  per-dashboard.
- **Verify SObject-level sharing is also in place.** Predicates do
  not replace sharing rules on the source records. If a user can't
  see an Account in Salesforce Core, the dataflow / recipe that
  built the dataset already had access (it ran as the dataflow
  user) — the predicate is the only thing keeping the user from
  seeing the row in CRM Analytics. That asymmetry is correct, but
  surprising.
- **Plan the test set.** At minimum: a row owner, a non-owner with
  legitimate access, a non-owner without access, an admin (who
  bypasses predicates by default — that's the most common mistake).
- **Budget for predicate cost.** Predicates run on every query.
  Complex multi-condition predicates with `IN` against a large list,
  or predicates that reference computed `$User.*` values, can slow
  every dashboard that reads the dataset.

---

## Core Concepts

### Predicate syntax

```
'<DatasetColumn>' <operator> <value> [<logical-op> '<DatasetColumn>' <operator> <value>] ...
```

Components:

- **DatasetColumn** — the API name of a column in the dataset, in
  single quotes. Case-sensitive.
- **Comparison operators** — `==`, `!=`, `<`, `<=`, `>`, `>=`,
  `in`, `matches` (regex).
- **Logical operators** — `&&` (AND), `||` (OR), parentheses for
  grouping.
- **Values** — string literal `"..."`, numeric, list `[...]`, or
  a `$User.*` context variable.

### `$User.*` context variables

Available inside any predicate value position. They resolve at query
time to the running user:

| Variable | Resolves to |
|---|---|
| `"$User.Id"` | The 18-character Id of the running user |
| `"$User.UserRoleId"` | The role Id (or null if no role) |
| `"$User.ProfileId"` | The profile Id |
| `"$User.UserName"` | The Username |
| `"$User.Email"` | Email |
| `"$User.<CustomField__c>"` | Any standard or custom User field |

The custom-field form is the most useful — define a `Region__c` on
User, populate per user, then write `'Region' == "$User.Region__c"`
to filter the dataset by the running user's region.

### The five access patterns and their predicate shapes

| Access pattern | Predicate |
|---|---|
| Owner-only | `'OwnerId' == "$User.Id"` |
| Owner OR my team | `'OwnerId' == "$User.Id" \|\| 'TeamMembers' matches "$User.Id"` |
| Role hierarchy (my role and below) | `'UserRoleId' in [matches "$User.UserRoleId"]` (predicate refers to a precomputed role-hierarchy column in the dataset) |
| Region-scoped (custom User field) | `'Region' == "$User.Region__c"` |
| Multi-condition: region AND own team | `('Region' == "$User.Region__c") && ('TeamMembers' matches "$User.Id")` |

### Admins bypass predicates by default

CRM Analytics admins (users with the `Manage Analytics` permission)
see all rows regardless of the predicate. This is intentional — it
prevents admins from being locked out of their own datasets — but
it's the source of the most common testing failure: the team writes
the predicate, the admin tests it, sees all the rows, declares it
working, and discovers in production that non-admin users see what
they expected.

**Always test with a non-admin user.**

### Predicate cost

Predicates run on every query against the dataset. The cost is:

- **Per-row evaluation** of the predicate expression.
- **Variable substitution** — `$User.Email` requires looking up the
  running user's email at query time.
- **Regex matches** — `matches` is more expensive than `==` /
  `in`.
- **Long `IN` lists** — `IN ['a', 'b', 'c', ..., 'zzz']` evaluates
  each comparison.

For most predicates, the cost is negligible (sub-100ms added). For
predicates with regex matches against role-hierarchy columns over
millions of rows, the cost can be a noticeable fraction of dashboard
load time. Profile in CRM Analytics's query inspector if a
predicate-protected dashboard is slow.

---

## Common Patterns

### Pattern A — Owner-only access

**When to use.** Every user sees only the rows they own. Standard
"my pipeline" / "my cases" semantics.

```
'OwnerId' == "$User.Id"
```

**Test plan.**
- User A owns rows 1-10 → sees rows 1-10.
- User B owns rows 11-20 → sees rows 11-20.
- Admin → sees all rows (bypasses predicate; expected).

**Trade.** Doesn't surface team-shared visibility. If the user has
been granted access via a sharing rule, they still don't see the row
in the dataset because the predicate is per-dataset, not per-source-row.
For team visibility, use Pattern B.

### Pattern B — Owner OR team-member

**When to use.** Standard sharing-rule equivalent for opportunities
or accounts where team members get visibility.

```
'OwnerId' == "$User.Id" || 'AccountTeamMembers' matches "$User.Id"
```

**Prerequisite.** The dataset must include a column listing
team-member Ids per row — typically a multi-value column populated by
the dataflow / recipe joining `AccountTeamMember` against `Account`.

**Test plan.**
- Owner → sees their owned rows.
- Team member → sees rows where they're listed in `AccountTeamMembers`.
- Non-owner / non-team-member → no rows.

### Pattern C — Role hierarchy (my role and below)

**When to use.** Sales managers see rows owned by their reports.

```
'UserRoleHierarchyIds' matches "$User.UserRoleId"
```

**Prerequisite.** `UserRoleHierarchyIds` is a dataset column that
contains, for each row, the chain of role Ids from the row owner up
to the org top — populated by the dataflow / recipe.

**Implementation note.** Computing the role chain per row is a
dataflow / recipe responsibility. The predicate is straightforward;
the *data preparation* is where the cost lives.

### Pattern D — Multi-dimensional (region AND team)

**When to use.** A regional manager sees rows in their region AND on
their team — but not other regions, even if they're on the team.

```
('Region' == "$User.Region__c") && ('AccountTeamMembers' matches "$User.Id")
```

**Trade.** Adding dimensions multiplies the test matrix. Each new
condition adds a new dimension of test users.

### Pattern E — Service-account bypass for system queries

**When to use.** A scheduled SAQL query runs as a service user that
must see all rows (export to a warehouse, daily aggregate). The
predicate would block it.

**Approach.** Grant the service user the `Manage Analytics`
permission so the predicate is bypassed. Document the bypass: a
service-account-only role + permission set, audit-logged, scope
limited to the relevant dataset(s).

**Anti-pattern.** Writing `('OwnerId' == "$User.Id" || 'OwnerId' ==
'service-user-id')` — works but ties the predicate to a specific
user record. If the service user is recreated, the predicate
silently breaks.

---

## Decision Guidance

| Situation | Predicate | Reason |
|---|---|---|
| Standard "my pipeline" semantics | `'OwnerId' == "$User.Id"` (Pattern A) | Cleanest; no extra dataset prep |
| Sharing-rule equivalent (owner or team) | Pattern B with team-member column | Mirrors Salesforce sharing semantics in the dataset |
| Manager sees their reports | Pattern C with role-hierarchy column | Standard hierarchical access |
| Region-scoped reporting | `'Region' == "$User.Region__c"` (custom User field) | Use custom User fields for non-standard dimensions |
| Multi-dimensional access | Pattern D — combine with `&&` | Each new dimension multiplies test users |
| Need different access per dashboard | **Either** separate datasets **or** predicate that varies via `$User.*` | Predicates are per-dataset, not per-dashboard |
| Service account that needs full access | `Manage Analytics` permission on the service user | Don't hardcode user Ids in the predicate |
| Test passes for admin only | **Test with a non-admin user** | Admins bypass predicates by default |
| Predicate is slowing dashboards | Profile in CRM Analytics query inspector; consider precomputing fields in the dataset | Per-row evaluation cost adds up |

---

## Recommended Workflow

1. **Decide access pattern.** Pick from owner-only, owner+team, role-hierarchy, region, multi-dimensional. Start simple; add dimensions only when justified.
2. **Identify the columns the predicate needs.** Owner Id is usually present; team-members and role-hierarchy chains are dataflow / recipe-computed columns.
3. **Write the predicate** following the syntax in Core Concepts.
4. **Define the test matrix.** Owner / non-owner / admin / cross-team — one user per axis. Include a non-admin user; admins bypass predicates.
5. **Apply via the dataset's `Security Predicate` field** (Setup or via the dataset XMD JSON).
6. **Test.** Run the same SAQL query as each test user; confirm the row sets match expectations.
7. **Profile.** If the dataset feeds latency-sensitive dashboards, run a representative query in the inspector and confirm predicate cost is acceptable.

---

## Review Checklist

- [ ] Predicate syntax is valid (column names quoted, operators spelled correctly).
- [ ] Every `$User.*` reference resolves to a real User field.
- [ ] If using regex `matches`, regex is verified against sample data.
- [ ] Test matrix includes a non-admin user.
- [ ] Test matrix includes a user with NO access (verifies the predicate actually blocks).
- [ ] Service-account bypass strategy is documented (if any).
- [ ] Performance baseline measured (especially if `matches` is used).
- [ ] Predicate is stored on the dataset, not duplicated across dashboards.

---

## Salesforce-Specific Gotchas

1. **Admins bypass predicates by default.** Test with a non-admin user, always. (See `references/gotchas.md` § 1.)
2. **Predicates apply to the dataset, not the dashboard.** A predicate set on dataset X filters every dashboard that reads dataset X. (See `references/gotchas.md` § 2.)
3. **Predicates do NOT replace SObject-level sharing on source records.** Both layers apply. The dataflow / recipe ran as a privileged user, so the *dataset* has the data; the predicate is the only filter the running user sees through. (See `references/gotchas.md` § 3.)
4. **`$User.<CustomField__c>` resolves at query time** — if the custom field is null on the running user, the predicate's right-hand side is null, and `'Column' == null` returns no rows for that user. (See `references/gotchas.md` § 4.)
5. **Role-hierarchy access requires a precomputed column in the dataset.** SAQL can't traverse the role hierarchy at query time; the dataflow / recipe must produce a `UserRoleHierarchyIds` chain per row. (See `references/gotchas.md` § 5.)
6. **`matches` regex is more expensive than `==` and `in`.** Profile if the dashboard is slow. (See `references/gotchas.md` § 6.)
7. **Hard-coding a service-account user Id in the predicate breaks when the user is recreated.** Use the `Manage Analytics` permission to bypass instead. (See `references/gotchas.md` § 7.)

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Security predicate expression | The actual string applied to the dataset's `Security Predicate` field |
| Dataflow / recipe additions | Any precomputed columns the predicate depends on (team membership, role-hierarchy chain) |
| Custom User fields used | Per-user values referenced via `$User.<CustomField>` |
| Test matrix | Owner / non-owner / admin / cross-team users with expected row sets per user |
| Performance baseline | Query inspector output before/after predicate; documented overhead |

---

## Related Skills

- `data/crm-analytics-dataflow-design` — building the dataset that the predicate protects; predicate-required columns (team membership, role chain) are dataflow concerns.
- `data/crm-analytics-app-sharing` — different layer: who can open the dashboard / app at all (Asset sharing), not row-level filtering inside it.
- `security/sharing-architecture` — Salesforce Core sharing on the source SObjects; both layers apply when CRM Analytics queries Salesforce data.
- `security/byok-key-rotation` — when the dataset contains Shield-encrypted fields, key rotation interacts with predicate-protected reads.
