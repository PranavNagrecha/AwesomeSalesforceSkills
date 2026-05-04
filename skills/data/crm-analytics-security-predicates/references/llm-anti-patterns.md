# LLM Anti-Patterns — CRM Analytics Security Predicates

Mistakes AI coding assistants commonly make when advising on CRM
Analytics row-level security. The consuming agent should self-check
against this list before recommending a predicate or its test plan.

---

## Anti-Pattern 1: Recommending predicate setup at the dashboard level

**What the LLM generates.** "To restrict who sees what in this
dashboard, add a filter step that uses `$User.Id`."

**Why it happens.** "Filter the dashboard" sounds like row-level
security; the LLM doesn't surface that dashboard filters are UI
controls, not data-access controls.

**Correct pattern.** Predicates go on the **dataset**, not the
dashboard. Dashboard filters can be bypassed via SAQL Studio,
explorations, or API access — they're not security.

**Detection hint.** Any "row-level security" recommendation that
mentions dashboard filters or step-level filters as the
implementation is wrong.

---

## Anti-Pattern 2: Testing only with admin accounts

**What the LLM generates.** Test plans that say "log in and verify
the predicate works" without specifying the user's permission level.

**Why it happens.** "Test it" is the standard verification step; the
LLM doesn't surface that admins bypass predicates.

**Correct pattern.** Test matrix must include:
- A non-admin user who SHOULD see rows.
- A non-admin user who SHOULD NOT see rows.
- An admin (confirms bypass behavior; not a security test).

**Detection hint.** Any predicate test plan that doesn't explicitly
call out non-admin testing is incomplete.

---

## Anti-Pattern 3: Treating predicates as a replacement for sharing rules

**What the LLM generates.** "You don't need sharing rules for this —
the predicate handles it."

**Why it happens.** Both control row visibility; the LLM conflates
the layers.

**Correct pattern.** Two independent layers:
- Salesforce Core sharing controls record-page and report access.
- CRM Analytics predicates control dataset-query access in CRM
  Analytics.

The dataflow / recipe ran as a privileged user, so the dataset has
all the rows — the predicate is the only filter inside CRM
Analytics. Both layers may be required.

**Detection hint.** Any "predicates replace sharing rules" or "you
can drop your sharing rules now that you have predicates" advice is
wrong.

---

## Anti-Pattern 4: Role-hierarchy predicate without dataflow support

**What the LLM generates.**

```
'OwnerId' == "$User.Id" ||
'OwnerRole' in ($User.UserRoleId.descendants)
```

**Why it happens.** The LLM imagines a SAQL traversal that doesn't
exist. SAQL has no role-hierarchy walk function.

**Correct pattern.** Role-hierarchy access requires the **dataflow /
recipe** to compute, per row, the chain of role Ids from the owner
up to the org top, stored as a multi-value column. The predicate
then matches against that column:

```
'OwnerRoleHierarchy' matches "$User.UserRoleId"
```

**Detection hint.** Any predicate that claims to "walk the role
hierarchy" or references a `.descendants` / `.ancestors` /
`.hierarchy` method on `$User.UserRoleId` is wrong by construction.

---

## Anti-Pattern 5: Hardcoding service-account User Ids

**What the LLM generates.**

```
'OwnerId' == "$User.Id" || 'OwnerId' == "0051A000007SVCACCT"
```

**Why it happens.** "Just OR in the service account" is the visible
fix; the LLM doesn't surface that User Ids are unstable across
recreation.

**Correct pattern.** Grant `Manage Analytics` permission to the
service user via a dedicated permission set. The predicate stays
clean; bypass is auditable.

**Detection hint.** Any predicate with a literal 15- or 18-character
User Id in it is wrong. User Ids are not stable identifiers in this
context.

---

## Anti-Pattern 6: Single-test verification

**What the LLM generates.** "Log in as a sales rep, verify they see
only their rows. Predicate works."

**Why it happens.** One-positive-case verification is the simplest
test; the LLM doesn't surface the over-permissive failure mode.

**Correct pattern.** Multi-user test plan:
- Owner A → sees A's rows only.
- Owner B → sees B's rows only.
- Non-owner with no access → sees nothing.
- Non-owner with team access (if Pattern B) → sees expected subset.
- Admin → sees everything.

The non-owner-with-no-access test is the most security-critical —
it catches over-permissive predicates that grant unintended access.

**Detection hint.** Test plans with only one or two users are
incomplete for security-critical predicates.

---

## Anti-Pattern 7: `$User.<CustomField>` without addressing null handling

**What the LLM generates.**

```
'Region__c' == "$User.Region__c"
```

**Why it happens.** The LLM emits the obvious form without
considering what happens when the User has no `Region__c` populated.

**Correct pattern.** Either:
- Populate `Region__c` for every User who needs visibility (clean).
- Wrap the predicate to handle null with a documented intent:
  ```
  'Region__c' == "$User.Region__c" || "$User.Region__c" == null
  ```
  …knowing that this grants null-region users full visibility,
  which may be intentional (admin proxy) or a security gap.

**Detection hint.** Any `$User.<CustomField>`-based predicate that
doesn't document null handling is going to produce surprising
behavior for users with the field unpopulated.

---

## Anti-Pattern 8: `matches` regex against unbounded user-supplied input

**What the LLM generates.**

```
'TeamMembers' matches "$User.UserName"
```

**Why it happens.** `UserName` looks like a stable identifier; the
LLM doesn't surface that it can contain regex-special characters.

**Correct pattern.** Use `$User.Id` (always safe — only hex digits
in Salesforce Ids). If you need a username-based match, escape regex
metacharacters in the dataflow at column-build time, or use `==` /
`in` against a pre-normalized list.

**Detection hint.** Any `matches` predicate against `$User.UserName`
or `$User.Email` is risking regex-injection from the username
itself.
