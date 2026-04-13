# Examples — Analytics Security Architecture

## Example 1: Sharing Inheritance with Mandatory Backup Predicate

**Context:** A financial services org has a CRM Analytics opportunity pipeline app. The source Salesforce Opportunity object uses the standard role hierarchy for sharing — managers see their team's opportunities, individual reps see only their own. The team wants to mirror this in CRM Analytics without writing a custom predicate. However, regional VP users sit near the top of the hierarchy and could own visibility to tens of thousands of records.

**Problem:** If sharing inheritance is enabled without a backup predicate, the VP users exceed the 3,000-row threshold. Salesforce sharing inheritance cannot apply at that scale, and those users silently see all rows in the dataset — every deal in every region — rather than just their hierarchy's deals. This is a data-leakage failure that produces no error in the UI.

**Solution:**

Step 1 — Enable sharing inheritance on the `opportunities_ds` dataset in Analytics Studio (Dataset Settings > Security > Row-Level Security > Sharing Inheritance: On).

Step 2 — Set the backup predicate on the same dataset:

```
'false'
```

The backup predicate fires when sharing inheritance cannot be applied (i.e., when the user's row count exceeds 3,000). Returning `false` means those users see zero rows rather than all rows — a secure failure mode that surfaces as an empty dashboard for VP users, prompting a support ticket rather than a silent data leak.

Step 3 — Test with three user personas in a full sandbox:
- An individual rep (owns ~50 opportunities) — should see only their own records.
- A front-line manager (team of 10 reps, ~500 opportunities) — should see all team records.
- A regional VP (hierarchy spans ~8,000 opportunities) — backup predicate fires; VP sees zero rows; this is the expected behavior and should trigger a separate predicate design for VP-level users.

**Why it works:** The backup predicate of `'false'` closes the gap left by the 3,000-row limit. It does not interfere with users who are within the threshold — sharing inheritance takes precedence for them. The VP scenario is a known platform constraint, not a bug, and must be handled by a separate predicate or role-based design for high-volume users.

---

## Example 2: Cross-Dataset Security Using Embedded User Lookup via Augment Step

**Context:** A telecom org uses CRM Analytics to display support case analytics. Cases are not owned by individual agents — they are assigned to queues and then to agents via a custom junction object (`Case_Agent__c`) that maps `CaseId` to `AgentUserId`. The security requirement is: each agent sees only cases they are currently assigned to. There is no direct `OwnerId` on the case that maps to the running user.

**Problem:** A predicate on the `cases_ds` dataset cannot reference the `Case_Agent__c` junction object — predicates can only filter on columns present in the dataset at query time. Without embedding agent assignment data, the only option would be a predicate of `'OwnerId' == "$User.Id"`, which would exclude all queue-owned cases regardless of assignment.

**Solution:**

Step 1 — Build an agent entitlement dataset (`agent_entitlement_ds`) via a dataflow or recipe that reads `Case_Agent__c` and produces a flat table:

```
CaseId  |  Authorized_AgentUserId
00001   |  005abc123
00001   |  005xyz789   (if a case can have multiple agents)
00002   |  005abc123
```

Step 2 — In the main dataflow or recipe for `cases_ds`, add an augment step after loading the `Case` object:

```
Augment step:
  Left dataset:  cases_source (from Case object)
  Right dataset: agent_entitlement_ds
  Join key:      CaseId (left) = CaseId (right)
  Output column: Authorized_AgentUserId (from right dataset)
```

The resulting `cases_ds` dataset now has one row per (Case, Agent) combination, with the `Authorized_AgentUserId` column embedded.

Step 3 — Apply the security predicate on `cases_ds`:

```
'Authorized_AgentUserId' == "$User.Id"
```

Step 4 — Verify column name case: open Analytics Studio > cases_ds > Schema. Confirm the column appears as `Authorized_AgentUserId` (exact case). If the dataflow outputs it as `authorized_agentuserId`, the predicate must match that exactly.

Step 5 — Schedule the `cases_ds` dataflow to re-run at the same cadence as `Case_Agent__c` records change (e.g., every 4 hours if agents are reassigned frequently). Stale entitlement data means agents may see cases they are no longer assigned to, or miss newly assigned cases.

**Why it works:** The security boundary is enforced at dataflow run time, not query time — the entitlement join produces a dataset where each row is already pre-scoped to the authorized agent. The predicate then filters down to the running user's rows at query time. This is the only supported pattern for entitlement-based security in CRM Analytics; predicates have no cross-dataset join capability.

---

## Anti-Pattern: Relying on Salesforce OWD to Restrict Analytics Dataset Rows

**What practitioners do:** Configure Salesforce OWD to Private on the Account object, assume that CRM Analytics will respect those settings, and skip the security predicate configuration on the `accounts_ds` dataset.

**What goes wrong:** Every licensed CRM Analytics user with dataset access sees every Account row in the dataset, regardless of OWD, sharing rules, or role hierarchy. The Salesforce record-level security model is entirely separate from CRM Analytics dataset security. There is no automatic inheritance. A user who cannot see an Account record in Salesforce list views and record pages can still see that Account's data in CRM Analytics dashboards if no predicate is applied.

**Correct approach:** Always configure an explicit security predicate (or sharing inheritance with a backup predicate) on every CRM Analytics dataset that contains restricted data. Treat CRM Analytics security as a completely independent security layer that must be designed, implemented, and tested separately from the Salesforce sharing model. The assumption that "Salesforce security carries over" is the single most common and most dangerous mistake in CRM Analytics implementations.
