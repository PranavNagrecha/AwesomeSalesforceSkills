# Examples — User Access Policies

## Example 1: Auto-Assign Permission Set Group on User Create by Profile

**Context:** A company onboards 50+ new sales reps per quarter. Each rep needs the `Sales_Rep_PSG` permission set group assigned immediately upon account creation. Previously this was handled by an Apex trigger on the User object.

**Problem:** The Apex trigger required developer maintenance, occasionally failed silently in bulk loads, and was not included in change sets by the admin team.

**Solution:**

```text
Policy Type: Grant
Filter Criteria:
  Profile = Sales Rep Profile

Assignments:
  - Permission Set Group: Sales_Rep_PSG

Status: Active
```

Navigate to Setup > User Access Policies > New. Set type to Grant. Add filter: Profile equals "Sales Rep Profile". Add `Sales_Rep_PSG` to the Assignments section. Save and activate. Deactivate the legacy Apex trigger.

**Why it works:** The platform evaluates all active Grant policies when a new User record is created. Any user created with the "Sales Rep Profile" profile will have `Sales_Rep_PSG` assigned automatically without any code execution.

---

## Example 2: Revoke Permission Set When User Moves Out of Department

**Context:** Users in the Finance department have access to `Finance_Data_Access_PS`. When users transfer to other departments, that permission set should be removed automatically to enforce least-privilege access.

**Problem:** Manual permission cleanup after department transfers is frequently missed during offboarding checklists, leaving stale access in place.

**Solution:**

```text
Policy Type: Revoke
Filter Criteria:
  Department = Finance

Assignments (to revoke when filter NO LONGER matches):
  - Permission Set: Finance_Data_Access_PS

Status: Active
```

Create a Revoke policy with filter `Department = Finance` and assign `Finance_Data_Access_PS` to the revoke list. When a user's Department field is updated away from "Finance", the platform re-evaluates the Revoke policy and removes the permission set.

**Why it works:** UAP re-evaluates policies whenever a field referenced in any policy's filter criteria is updated. Changing Department triggers re-evaluation. The Revoke policy no longer matches the user, so the platform removes the listed permission set.

---

## Example 3: PSL and PSG Co-Assignment for Agentforce Feature Access

**Context:** Users in the `Customer Success` department need both the Agentforce PSL and the `Agentforce_User_PSG` permission set group to access an Agentforce-gated feature. Both must be provisioned together.

**Problem:** Admins were assigning the PSL and the PSG separately, leading to tickets where one was assigned but not the other — causing broken feature access.

**Solution:**

```text
Policy Type: Grant
Filter Criteria:
  Department = Customer Success

Assignments:
  - Permission Set License: Agentforce PSL
  - Permission Set Group: Agentforce_User_PSG

Status: Active
```

A single Grant policy can include both PSL and PSG in the same assignment list. Both are provisioned in a single evaluation pass, eliminating the split-assignment problem.

**Why it works:** UAP processes all assignment items in a single policy atomically. Adding both the PSL and PSG to the same policy ensures they are always provisioned together.

---

## Anti-Pattern: Creating a Grant and Revoke Policy Targeting the Same Permission Set for the Same User Segment

**What practitioners do:** A practitioner creates a Grant policy with filter `Department = Engineering` assigning `Eng_Tools_PS`, then later creates a Revoke policy with the same filter `Department = Engineering` also targeting `Eng_Tools_PS`, intending to use the Revoke policy to "clean up" in certain edge cases.

**What goes wrong:** Both policies evaluate on every qualifying update. The platform runs Grant first, assigns `Eng_Tools_PS`, then runs Revoke, removes `Eng_Tools_PS`. The net result is that users in Engineering never retain `Eng_Tools_PS` — it is granted and immediately revoked in the same pass.

**Correct approach:** Grant and Revoke policies should target complementary filter criteria, not the same criteria. Use the Revoke policy with the opposite or excluding filter (e.g., Revoke when `Department != Engineering`) or use separate policies with mutually exclusive filter conditions.
