# Gotchas — CRM Analytics Security Predicates

Non-obvious behaviors of CRM Analytics row-level security that cause
real production problems.

---

## Gotcha 1: Admins bypass predicates by default

**What happens.** A predicate is set on a dataset. The admin who
configured it tests by viewing the dashboard — sees all rows, declares
it working. A non-admin user reports "I see everything I shouldn't"
or "I see nothing". The bypass behavior was undisclosed.

**When it occurs.** Always — `Manage Analytics` permission grants
predicate bypass. Most admins have it implicitly via their profile or
permission sets.

**How to avoid.** Test plan must include a non-admin user explicitly.
Audit which permission sets grant `Manage Analytics`; tighten if the
assignment is broader than security policy intends.

---

## Gotcha 2: Predicates apply at dataset level, not dashboard level

**What happens.** Team writes a predicate, applies it to a specific
dashboard, expects it to filter the dashboard. It doesn't — predicates
don't exist at the dashboard level. The dashboard's results are
unfiltered.

**When it occurs.** Anyone treating predicates as a UI-control rather
than a data-access control. Or anyone confusing CRM Analytics security
with Salesforce Core sharing.

**How to avoid.** Predicates go on the dataset (`SecurityPredicate`
field on the dataset metadata). Every query that reads the dataset
inherits the predicate. If different dashboards need different
filtering, either (a) use multiple datasets, or (b) write a predicate
that varies per running user via `$User.*` context.

---

## Gotcha 3: Predicates do NOT replace SObject-level sharing

**What happens.** Team assumes that a CRM Analytics predicate is
equivalent to setting up Salesforce sharing rules. They omit the
sharing-rule work, deploy. Salesforce Core users who shouldn't see
records still see them in record pages and reports — only the CRM
Analytics dataset is protected.

**When it occurs.** Confusion about what predicates protect.

**How to avoid.** Two layers, both required:
- Salesforce Core sharing (Org-Wide Defaults, role hierarchy, sharing
  rules, manual sharing) protects record-page / report access.
- CRM Analytics predicates protect the **dataset's copy** of the
  data inside CRM Analytics.

The dataflow / recipe ran as a privileged user, so the dataset
itself contains all the rows — the predicate is the only thing
filtering what the running user sees in CRM Analytics. If you want
parity with sharing, the predicate must encode the sharing rules.

---

## Gotcha 4: `$User.<CustomField>` resolves to null when the field is null

**What happens.** Predicate is `'Region__c' == "$User.Region__c"`. A
User has `Region__c` unpopulated (null). The predicate evaluates to
`'Region__c' == null` for that user — which matches no rows. The
user sees an empty dashboard.

**When it occurs.** New User provisioning that didn't populate the
custom field; existing Users who never had it set.

**How to avoid.** Either:
- Populate the custom field for every User who needs visibility (the
  cleanest answer; surface in user provisioning).
- Wrap the predicate to handle null: `'Region__c' == "$User.Region__c"
  || "$User.Region__c" == null` — be careful with this; it grants
  full visibility to null-region users, which may not be the intent.

---

## Gotcha 5: Role hierarchy access requires a precomputed column

**What happens.** Team writes a predicate like
`'OwnerId' == "$User.Id" || <some role hierarchy traversal>`.
The role traversal can't be expressed in a predicate — SAQL can't
walk the role hierarchy at query time. The predicate evaluates only
the owner-Id branch; users see only their own rows, not their
reports' rows.

**When it occurs.** Manager-sees-reports patterns implemented
without dataflow / recipe support.

**How to avoid.** The dataflow / recipe must compute, per opportunity
row, the chain of role Ids from the owner up to the top. Store as a
multi-value column (e.g. `OwnerRoleHierarchy`). The predicate then
matches:

```
'OwnerRoleHierarchy' matches "$User.UserRoleId"
```

This is the most common "the predicate doesn't seem to work" pattern
— the data prep step was missing.

---

## Gotcha 6: `matches` regex is more expensive than `==` and `in`

**What happens.** Dashboard performance degrades after a predicate
with `matches` is applied to a high-volume dataset. The query
inspector shows predicate evaluation as the dominant cost.

**When it occurs.** `matches` against multi-value columns
(team-member lists, role-hierarchy chains). Per-row regex evaluation
adds up.

**How to avoid.**
- Use `in` for exact-match lists where possible.
- Pre-filter at dataflow time so the dataset has fewer rows that the
  predicate must evaluate.
- Profile in the query inspector and confirm predicate is actually
  the bottleneck before optimizing.

---

## Gotcha 7: Hardcoding a service-account User Id in the predicate

**What happens.** Predicate includes `'OwnerId' == "0051A000007SVCACCT"`
as a bypass clause for a service user. The service user is later
recreated (deactivated, replaced); the new User has a different Id.
The predicate now silently excludes the new service user — every
scheduled job that depended on the bypass starts returning empty
result sets.

**When it occurs.** Service-account rotation; sandbox refresh that
restored a deactivated service user.

**How to avoid.** Grant the `Manage Analytics` permission to service
users that need bypass, via a dedicated permission set. The predicate
stays clean; the bypass is auditable via the permission set's
assignments.

---

## Gotcha 8: Predicate set in the dataset XMD JSON is shadowed by a Setup-edited predicate

**What happens.** Team commits an updated `SecurityPredicate` to the
dataset XMD via the dataflow / metadata deploy. An admin had
previously edited the predicate via Setup. The Setup-edited version
is the active one; the deploy looks like it succeeded, but the
predicate behavior didn't change.

**When it occurs.** Admin-managed predicates that drift from
source-controlled metadata.

**How to avoid.** Decide who owns the predicate — source control or
Setup — and stick to that ownership. If source control, audit any
Setup edits and ensure they're reflected upstream. If Setup, document
that the dataset's source-controlled XMD shouldn't carry a
SecurityPredicate value.

---

## Gotcha 9: Predicate testing should include the "no access" user

**What happens.** Predicate is tested with one user who should see
some rows. The predicate works for that user. Production reveals
that ANOTHER user — who should see zero rows — sees them all because
of an unintended OR branch in the predicate.

**When it occurs.** Test plans that cover only the positive cases.

**How to avoid.** Test matrix includes:
- A user who should see rows (verifies the predicate isn't
  over-restrictive).
- A user who should NOT see rows (verifies the predicate isn't
  over-permissive).
- An admin (confirms bypass behavior; expected to see everything).

The "no access" test is the one that catches over-permissive
predicates — the most security-critical class of error.
