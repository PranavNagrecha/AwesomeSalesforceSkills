# Examples — CRM Analytics Security Predicates

## Example 1 — Predicate works in dev, fails in QA: admin bypass

**Context.** Sales-Ops requested row-level security on the Pipeline
dataset: each rep should see only their owned opportunities. The
Analytics team writes the predicate, an admin tests it, all looks
good. QA (a non-admin tester) reports they see every opportunity in
the org.

**Wrong cause assumed.** "The predicate isn't being applied."

**Actual cause.** The admin tester saw all rows because admins
bypass predicates by default (`Manage Analytics` permission). The
QA tester saw all rows because they had `Manage Analytics`
inherited from a permission set that wasn't supposed to grant it.

**Right answer.**
1. Always test with a user who explicitly does NOT have `Manage Analytics`.
2. Audit which permission sets grant `Manage Analytics`; tighten if
   the assignment is broader than intended.
3. Document the admin-bypass behavior in the test plan so it isn't
   re-discovered the next time someone tests in QA.

**Predicate.**
```
'OwnerId' == "$User.Id"
```

---

## Example 2 — Owner-OR-team using a multi-value column

**Context.** Account Executives own Opportunities. Account Managers
collaborate via Account Teams and need read access to opportunities
on accounts they're on. The dataset must show: owned opportunities,
plus opportunities on accounts where the running user is a Team
Member.

**Dataflow / recipe step.** Join `AccountTeamMember` against the
opportunity's `AccountId` to produce a `TeamMembers` column on each
opportunity row — a multi-value string of User Ids:

```
TeamMembers = "0051A000007XYZ,0051A000007ABC,0051A000007DEF"
```

**Predicate.**
```
'OwnerId' == "$User.Id" || 'TeamMembers' matches "$User.Id"
```

`matches` here treats `TeamMembers` as a string and checks whether
`$User.Id` appears as a substring. This is correct for a comma-
separated multi-value column.

**Test plan.**
- Owner of opportunity 1, not on any team → sees opportunity 1, no others.
- Team member on opportunity 2's account, not the owner → sees opportunity 2.
- Owner of opportunity 1 AND team member on opportunity 2 → sees both.
- Non-owner, non-team-member → sees nothing.

---

## Example 3 — Region-scoped reporting via a custom User field

**Context.** A regional VP can only see opportunities in their
region. Each User has a `Region__c` custom field (`AMER`, `EMEA`,
`APAC`). The Opportunity has a `Region__c` field copied from the
Account.

**Predicate.**
```
'Region__c' == "$User.Region__c"
```

**Trade.** If a User's `Region__c` is null (e.g. a US-based
service-account that legitimately needs all regions), they see
nothing — `'Region__c' == null` matches no rows. Either:
- Populate `Region__c` for every User who needs visibility, OR
- Grant `Manage Analytics` to the bypass-needing service accounts.

**Test plan.**
- AMER VP → sees AMER rows only.
- EMEA VP → sees EMEA rows only.
- User with null `Region__c` → sees no rows.
- Admin → sees all rows.

---

## Example 4 — Role-hierarchy access (manager sees reports' rows)

**Context.** Sales managers should see opportunities owned by their
direct or indirect reports.

**Dataflow / recipe step.** For each opportunity, compute the chain
of role Ids from the owner's role up to the org top, store as a
multi-value `OwnerRoleHierarchy` column:

```
OwnerRoleHierarchy = "00E1A0000XYZ,00E1A0000ABC,00E1A0000DEF"
```

(The owner's role Id, plus every role Id above them in the hierarchy.)

**Predicate.**
```
'OwnerRoleHierarchy' matches "$User.UserRoleId"
```

A manager whose `UserRoleId` is `00E1A0000ABC` matches every row
where `00E1A0000ABC` appears in the chain — i.e. every row owned by
someone at or below their role.

**Why dataflow does the work.** SAQL can't traverse the role
hierarchy at query time; the dataflow / recipe must produce the
chain. This is the most common cause of "the predicate doesn't seem
to work" for role-hierarchy patterns — the column wasn't computed
correctly.

---

## Example 5 — Multi-dimensional: region AND team

**Context.** A regional sales manager sees opportunities in their
region AND on accounts where they're on the team — but not other
regions, even if they're a team member.

**Predicate.**
```
('Region__c' == "$User.Region__c") && ('TeamMembers' matches "$User.Id")
```

**Test matrix grows multiplicatively.** Two dimensions = four
combinations:

| Region match? | Team member? | Should see? |
|---|---|---|
| Yes | Yes | Yes |
| Yes | No | No |
| No | Yes | No |
| No | No | No |

Every dimension you add doubles the test matrix. Keep predicates as
narrow as the security requirement justifies; multi-dimensional
predicates are accurate but expensive to test and harder to debug.

---

## Anti-Pattern: Hardcoding service-account user Id in the predicate

```
'OwnerId' == "$User.Id" || 'OwnerId' == "0051A000007SVCACCT"
```

**What goes wrong.**
- The predicate now ties to a specific User record. If the service
  user is recreated (deactivated and a new one provisioned), the Id
  changes and the predicate silently fails.
- Auditors see a raw User Id in the dataset definition with no
  context.
- Maintenance: every change to which service accounts need bypass
  requires editing the predicate.

**Correct.** Grant `Manage Analytics` permission to the service user.
The predicate is bypassed for them by design. If multiple service
users need bypass, put them in a permission set; manage the set's
assignment as your audit-trail.

---

## Anti-Pattern: Setting the predicate at the dashboard level

A team thinks "we'll add a filter to the dashboard so reps only see
their own rows" — believing this is row-level security.

**What goes wrong.**
- A user with direct dataset access (via SAQL Studio, an
  exploration view, an API call) bypasses the dashboard filter
  entirely.
- The "security" is actually a UI affordance, not a control.

**Correct.** Predicates go on the **dataset**, not the dashboard.
Every query against the dataset gets the predicate, regardless of
how the user reached it. If a non-predicate version is needed for
admins, that's `Manage Analytics`, not a dashboard variant.
