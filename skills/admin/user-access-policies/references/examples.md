# Examples — User Access Policies

Worked scenarios. For the full deployable file shape, package.xml, deploy order, and verification queries, see `references/metadata-examples.md`.

## Example 1: Auto-Assign a Permission Set Group on User Create by Profile

**Context:** A company onboards 50+ new sales reps per quarter. Each rep needs the `SalesRepPSG` permission set group assigned immediately on user creation. Previously this was handled by an Apex trigger on the User object.

**Problem:** The Apex trigger required developer maintenance, occasionally failed silently in bulk loads, and was not included in change sets by the admin team.

**Solution:** One policy, one filter row, one action.

```text
masterLabel:   Sales Rep Onboarding
booleanFilter: 1                       <- required even for a single row
order:         100
status:        Design                  <- activated in Setup after deploy
triggerType:   Create

filter  1: type=Profile  operation=equals  target=SalesRepCustomProfile
action  1: action=Grant  type=PermissionSetGroup  target=SalesRepPSG
```

Deploy the `.useraccesspolicy` file, then set the policy to `Active` in **Setup → User Access Policies** — a policy deployed with status `Active` arrives as `Design`. Deactivate the legacy Apex trigger in the same release.

**Why it works:** `triggerType` `Create` runs the policy when a user matching the criteria is created. `booleanFilter` `1` selects the single declared filter row. No Apex executes.

---

## Example 2: Revoke a Permission Set When a User Leaves a Department

**Context:** Users in the Finance department hold `Finance_Data_Access_PS`. When users transfer out, that permission set should be removed to enforce least privilege.

**Problem:** Manual cleanup after department transfers is frequently missed, leaving stale access in place.

**Solution:** Filter on the *destination* state and revoke, rather than trying to express "no longer Finance" as a policy that stops matching. A policy that stops matching a user simply does not run for them; it does not undo its previous actions.

```text
masterLabel:   Move Out Of Finance
booleanFilter: 1 AND 2
order:         200
status:        Design
triggerType:   Update

filter  1: type=User  columnName=Department  operation=notEquals  target=User  value=Finance
filter  2: type=User  columnName=IsActive    operation=equals     target=User  value=true
action  1: action=Revoke  type=PermissionSet  target=Finance_Data_Access_PS
```

Verify against a real transferred user afterwards. `IsRevoked` distinguishes a policy revocation from a deleted assignment row, and `LastDeletedByChange.Source` names what caused it:

```sql
SELECT AssigneeId, PermissionSet.Name, IsActive, IsRevoked,
       LastDeletedByChange.Source
FROM PermissionSetAssignment
WHERE PermissionSet.Name = 'Finance_Data_Access_PS'
  AND IsRevoked = true
ORDER BY AssigneeId
```

Those three UAP-gated fields exist only when `userAccessPoliciesEnabled` is true in the org — the query will not compile elsewhere.

**Why it works:** `type` `User` with `columnName` and `value` is how a raw user field is filtered; `target` is the literal string `User`. `notEquals` matches the population that has already moved out, and `triggerType` `Update` runs the policy on the transfer.

---

## Example 3: Licence Plus Permission Set Group for a Gated Feature

**Context:** Users in Customer Success need both a permission set licence and the `Agentforce_User_PSG` permission set group to reach a licence-gated feature.

**Problem:** Admins were assigning the licence and the group separately, producing tickets where one landed and the other did not — a seat that looks provisioned and does not work.

**Solution:** Both actions in one policy, so the winning policy grants both or neither.

```text
masterLabel:   CS Agentforce Seat
booleanFilter: 1
order:         150
status:        Design
triggerType:   CreateAndUpdate

filter  1: type=User  columnName=Department  operation=equals  target=User  value=Customer Success
action  1: action=Grant  type=PermissionSetLicense  target=<PSL developer name>
action  2: action=Grant  type=PermissionSetGroup    target=Agentforce_User_PSG
```

**Why it works:** Every element of `userAccessPolicyActions` is an independent `{action, target, type}` triple, and all of them run when that policy is the one applied. Splitting them across two policies would make the two compete on `order` instead — see the anti-pattern below.

---

## Anti-Pattern: A Narrower Policy That Silently Suppresses a Broader One

**What practitioners do:** An org has a working baseline policy — `order` 100, filter `Profile = SalesRepCustomProfile`, granting `SalesRepPSG` **and** the console permission set licence. Later, EMEA needs a regional public group as well, so a second policy is added: `order` 50, filter `Profile = SalesRepCustomProfile AND Country in (Germany, France, United Kingdom)`, granting `SalesRepPSG` and `EMEASalesPublicGroup`. It is written to *add* the group, and it is given a low `order` "so it takes priority".

**What goes wrong:** A German rep matches both policies. Only the active policy with the lowest `order` is applied, so the EMEA policy runs and the baseline policy does not run at all. The rep gets the permission set group and the regional public group — and never gets the console permission set licence, because that action lives only in the suppressed policy. The licence is not deferred or merged in afterwards; it simply never executes for anyone the EMEA policy matches. Nothing fails, nothing logs, and the gap surfaces as a support ticket about a feature that will not open.

**Correct approach:** Treat overlapping policies as a ranked list where the winner must be self-sufficient. Either repeat every action the outranked policy contributed:

```text
Sales Rep Onboarding EMEA   order 50
  Grant PermissionSetGroup    SalesRepPSG
  Grant PermissionSetLicense  SalesConsoleUser      <- repeated from the baseline
  Grant Group                 EMEASalesPublicGroup
```

or keep one policy and express the regional difference inside it, so nothing competes. Before adding any policy, list which existing policies it will outrank and what each of them was granting. `scripts/check_user_access_policies.py` reports overlapping criteria with differing `order` values and conflicting action sets.
