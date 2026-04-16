# Decision Tree — Sharing Selection

Which sharing mechanism should I use?
**Organization-Wide Defaults (OWD) · Role Hierarchy · Sharing Rules (criteria-based / ownership-based) · Manual Sharing · Account Teams / Opportunity Teams / Case Teams · Implicit Sharing · Apex Managed Sharing · Restriction Rules · Scoping Rules · Permission Sets · Public Groups · Experience Cloud Sharing Sets / Sharing Groups · User Sharing**

Use this tree BEFORE granting any access. Stacking too many mechanisms is
the most common cause of unauditable orgs.

---

## Strategic defaults

1. **Start with OWD as restrictive as the business allows.** Public Read/Write
   is a last resort, not a starting point. You cannot easily tighten later.
2. **Use declarative sharing first** (sharing rules, teams, roles). Reserve
   Apex Managed Sharing for cases where no declarative path exists.
3. **Prefer Permission Sets / Permission Set Groups over Profiles** for
   CRUD/FLS/system permissions. Profile-based access is frozen and Salesforce
   is evolving away from it.
4. **Never grant "View All" / "Modify All" on standard objects** just to
   solve a sharing problem — they bypass sharing entirely and hide bugs.
5. **Audit access, not intent.** Whoever can answer "who can see record X
   and why" in under 2 minutes owns the sharing model.

---

## The 7-step sharing design sequence (do it in this order)

```
1. OWD              (baseline — default is NO access beyond owner)
      ↓
2. Role Hierarchy   (managers see reports' records unless "Grant access
                     using hierarchies" is disabled on the object)
      ↓
3. Sharing Rules    (broaden: owner-based or criteria-based)
      ↓
4. Teams            (Account / Opportunity / Case team membership)
      ↓
5. Manual / Apex    (case-by-case — manual from UI, Apex Managed for programmatic)
      ↓
6. Restriction /    (narrow back down — Restriction Rules trump sharing;
   Scoping Rules     Scoping Rules affect default UI filters only)
      ↓
7. Implicit         (parent-child automatic sharing you cannot disable for
                     standard parent-child relationships)
```

Every layer after OWD **broadens** access (except Restriction Rules, which
narrow). If a user can see something they shouldn't, walk the sequence top
to bottom and find which layer added the access.

---

## Decision tree

```
START: I need user U to be able to see/edit record R of type T.

Q1. What is T's current Organization-Wide Default?
    ├── Private                                 → Q2
    ├── Public Read-Only / Public Read-Write    → Tighten OWD before adding anything → Q2
    └── Controlled by Parent                    → Access is inherited; go fix the parent object's model

Q2. Is U in the same role or above the record owner's role in the hierarchy?
    ├── Yes, and "Grant access using hierarchies" is ON  → Access already granted; done
    ├── Yes, but hierarchy is disabled on T              → Q3
    └── No                                               → Q3

Q3. Can the access be described by "anyone who matches criteria X should see records matching criteria Y"?
    ├── Yes, criteria are on the record itself          → Criteria-Based Sharing Rule
    ├── Yes, criteria are on related user/manager       → Hierarchy/role-based Sharing Rule
    └── No                                              → Q4

Q4. Is it per-record, ad hoc, initiated by the owner or an admin?
    ├── Yes, small volume, stable                       → Manual Sharing (UI)
    ├── Yes, volatile, programmatic                     → Apex Managed Sharing  → Q5
    └── No                                              → Q6

Q5. Apex Managed Sharing prerequisites
    - OWD of T must be Private or Public Read-Only.
    - You understand the required `RowCause__c` (Custom Apex sharing reason).
    - You will store the `__Share` record as the source of truth.
    - You will re-run sharing calculations on owner change.
    See skills/apex/apex-managed-sharing.

Q6. Is this for a Salesforce sales/service team context?
    ├── Sales → use Account / Opportunity Teams
    ├── Service → use Case Team with Predefined Case Team
    └── Other → continue

Q7. Does U need access to read only, and only when looking at the record
    (not in list views or reports)?
    ├── Yes → Scoping Rules (UI-level filter; NOT a security boundary)
    └── No  → Continue

Q8. Do we need to REMOVE access that some other layer is granting?
    ├── Yes → Restriction Rule (trumps sharing; evaluated per-query)
    └── No  → Done

Q9. External users (Experience Cloud)?
    ├── Yes → Use Sharing Sets (simple relationships) or Sharing Groups (complex) — NOT role hierarchy
    └── No  → Done
```

---

## Criteria-Based Sharing vs Apex Managed Sharing

| Dimension | Criteria-Based Sharing Rule | Apex Managed Sharing |
|---|---|---|
| Maintained by | Admin (declarative) | Developer (code) |
| Evaluated on | Criteria match at DML time | Whatever code you write |
| Limit | Total sharing rules per object (~300 by edition) | None from sharing count; bounded by `__Share` row count |
| Recalculation on owner change | Automatic | You must handle it |
| Audit story | Clear in setup | Requires reading Apex |
| Cost to change | Admin edits a rule | Deploy code |
| Use when | Criteria are stable, admin-managed | Criteria depend on runtime state unavailable declaratively |

**Rule:** Try criteria-based sharing first. If that fails, use Apex Managed
Sharing. Never layer Apex sharing on top of criteria-based sharing on the
same object — it creates duplicate grants that confuse audit.

---

## "Please just use `without sharing`" — when it's safe

Almost never. These are the narrow cases:

- A platform function (scheduled anonymisation, privacy-right fulfilment,
  global aggregation for a CEO-level dashboard) that must read every record
  regardless of the running user, AND the caller is system-level, AND the
  class is explicitly reviewed and documented.

Rules:

1. The class is named to make the elevation visible (e.g. `AccountAggregator_WithoutSharing`).
2. A comment at the top states *why* with a link to an ADR.
3. The class exposes only the minimum method needed.
4. Callers must be in the same repo — never expose `without sharing` classes
   as `@AuraEnabled` or `@RestResource`.
5. Review gate: a second reviewer must explicitly approve the `without sharing`
   declaration in PR.

Default in this repo is `with sharing`. Use `WITH USER_MODE` in SOQL
(Summer '23+) — see `templates/apex/BaseSelector.cls`.

---

## Permission sets vs sharing — different axis

| Purpose | Mechanism |
|---|---|
| "Can user see records of object T at all?" | OWD + sharing rules + hierarchy |
| "Can user perform CRUD on object T when they can see it?" | Permission sets (Profile is baseline) |
| "Can user see field F on a record they otherwise can see?" | FLS via permission sets |
| "Can user bypass sharing to do admin things?" | View/Modify All (object) — avoid; use for narrow admin permission sets |
| "Can user view all data in the org?" | View All Data (system) — never in normal roles |

**Rule:** CRUD/FLS is orthogonal to sharing. Don't solve a sharing problem
by giving "View All Data" — that hides the real access pattern and makes the
org unauditable.

---

## Experience Cloud sharing — a different world

Community / Experience Cloud users do NOT use role hierarchy by default.
Use:

- **Sharing Sets** — map a community user's contact/account to record access.
  Simple 1:1 or 1:many relationships.
- **Sharing Groups** — when sharing sets aren't enough; typically combined
  with account relationships and super-user access.
- **Guest User Profile** — strictly read-only best-effort access; treat any
  guest-exposed data as publishable.

Rules:

1. Always test the community user's access AS that user (`System.runAs`).
2. Default to "no record access" for the Guest User Profile on every object.
3. Audit quarterly — guest exposure is the #1 cause of public data leaks.

---

## Restriction Rules vs Scoping Rules — don't confuse them

| | Restriction Rule | Scoping Rule |
|---|---|---|
| Enforcement | Security boundary — user cannot see excluded records via any entry point | UI filter — user can still access excluded records via API or direct URL |
| Use case | "Compliance: sales users may not see Legal's records" | "Declutter: default list view hides inactive records" |
| Report impact | Excluded records not counted | Records still in reports if report filter allows |
| API impact | Excluded records not returned | No impact |

Choose Restriction Rules for compliance and data segregation. Choose Scoping
Rules for usability only.

---

## Anti-patterns

- **Public Read/Write OWD "to solve access problems."** Permanent data leak
  waiting to happen.
- **Grant access using hierarchies turned off without a Sharing Rule backfill.**
  Managers silently lose visibility.
- **Profile-based access for anything beyond baseline.** Profiles should be
  minimal; everything else goes to permission sets.
- **Apex Managed Sharing without handling owner change.** Stale `__Share`
  rows orphan access.
- **Layering Apex Managed Sharing ON TOP OF Criteria-Based Sharing on the
  same object.** Duplicates audits and multiplies compute on DML.
- **Manual Sharing as a substitute for modeling.** If the same manual share
  is happening 5+ times, it's a rule.
- **Calling `without sharing` "to make the test pass."** No. Fix the model.
- **Using View All Data / Modify All Data to "unblock" a scenario.** You
  just bypassed every control. Find the real answer.

---

## Auditability checklist

Every object's sharing model should be answerable in a 1-page ADR:

- [ ] OWD: Private / Public Read-Only / Public Read-Write / Controlled by Parent
- [ ] Role hierarchy on/off for this object
- [ ] Sharing rules (list with criteria + grantee group)
- [ ] Team memberships (sales/opportunity/case) if applicable
- [ ] Manual sharing policy (who can grant, when to revoke)
- [ ] Apex Managed Sharing classes + `RowCause` values
- [ ] Restriction rules
- [ ] Which profiles/permission sets grant View All / Modify All and why
- [ ] Community user access model (sharing set / sharing group)
- [ ] Guest user exposure (should be none on this object)

If you can't answer each of these in 30 seconds, the model is too complex.

---

## Related skills

- `admin/sharing-and-visibility`
- `admin/permission-sets`
- `admin/permission-set-groups`
- `apex/apex-managed-sharing`
- `apex/apex-security-patterns`
- `apex/soql-security`
- `security/org-hardening`
- `security/experience-cloud-security`
- `architect/security-architecture-review`

## Related templates

- `templates/apex/SecurityUtils.cls` — CRUD/FLS enforcement helpers
- `templates/apex/BaseSelector.cls` — defaults to `WITH USER_MODE` (respects sharing + FLS)
- `templates/apex/tests/TestUserFactory.cls` — run-as-user tests for sharing
