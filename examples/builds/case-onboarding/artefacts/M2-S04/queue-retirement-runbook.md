# Queue retirement and ownership-skew runbook — M2-S04

Built by `agents/metadata-builder` under `agents/build-step-runner`. Nothing here was deployed
and nothing here is executed by an agent. It is the operating note that travels with the three
Case queues this step creates: `Tier_1_General`, `Tier_2_Engineering` and `Billing`.

Two things are recorded here because the metadata cannot carry them:

1. **Retirement** — Q89. A deleted queue does not hand its records to anyone.
2. **Ownership skew** — S4 on the step note. `Tier_1_General` is the catch-all owner for
   roughly 480 cases a day, and a single queue owning more than 10,000 records of one object is
   the documented ownership-skew threshold.

---

## 1. Why this queue set carries a skew risk at all

| Input | Value | Source |
|---|---|---|
| Case volume | ~400 by email + ~60 by web form + ~20 logged by hand = **~480 a day** | `requirement.md` |
| Catch-all owner | `Tier_1_General` — Q26 routes every unmatched case there | Q26 |
| Ownership-skew threshold | **10,000 records of one object owned by a single user or queue** | `skills/admin/data-skew-and-sharing-performance` SKILL.md:88, quoting the LDV guide's "Avoid having any user own more than 10,000 records" (`ldv.txt` L1033) |

Derived, not measured: at 480 cases a day, `Tier_1_General` crosses 10,000 owned Cases in about
**21 days** *if nothing leaves queue ownership in that window*. That "if" is the whole point —
Omni-Channel push (M3-S05) is what moves ownership from the queue to an agent, and until it is
live every case that arrives simply accumulates under the queue. The threshold is therefore a
go-live risk for the intake milestone, not a year-three problem.

What crossing it costs, per the same skill: every change to a role or to a public group that
feeds a sharing rule forces Salesforce to recompute the sharing rows for every record that owner
holds. At 10,000+ cases under one queue that shows up as long-running sharing recalculation
jobs, `Group membership operation already in progress` errors, and lock contention against other
sharing work. The platform does not block ownership above the threshold — it is a guideline that
degrades, not a cap that fails loudly.

## 2. Monitor — who, what, how often

**Owner: the CRM admin lead.** That is the recorded `owner_role` on Q29 (queue membership) and on
Q87 (post-deploy access verification); no separate monitoring owner was answered, so the same
role carries this.

**Cadence:** weekly through the first release, then monthly. Weekly is chosen because the derived
crossing point above is ~3 weeks, so a monthly-only check can miss the threshold entirely.

**The count query.** Shape taken from
`skills/admin/data-skew-and-sharing-performance/references/metadata-examples.md` § 6 (ownership
skew), retargeted from `Loan__c` to `Case`:

```sql
SELECT OwnerId, COUNT(Id) cnt
FROM Case
GROUP BY OwnerId
HAVING COUNT(Id) > 10000
ORDER BY COUNT(Id) DESC
```

An empty result is the pass condition. Because that query returns ids rather than names, pair it
with the queue-scoped count — `Owner.Type` is required, since `OwnerId` alone does not
distinguish a queue from a user (`admin/queues-and-public-groups` SKILL.md, SOQL section):

```sql
SELECT Owner.Name, COUNT(Id) cnt
FROM Case
WHERE Owner.Type = 'Queue' AND IsClosed = false
GROUP BY Owner.Name
ORDER BY COUNT(Id) DESC
```

**Also watch:** Setup -> Background Jobs after any role or public-group membership change, per
`admin/data-skew-and-sharing-performance` gotcha guidance. A sharing recalculation that is still
running when the next membership change lands is how the "operation already in progress" error
arrives.

## 3. Remedy if the threshold is approached — split into ownership buckets

The documented remedy is more owners, not a bigger queue. From
`skills/admin/data-skew-and-sharing-performance` § "Ownership Data Skew" and
`references/metadata-examples.md` § 2:

1. **Confirm the diagnosis first.** Run the query in § 2. Skew is a count against one owner, not
   a general "the queue feels big".
2. **Create bucket owners.** Split `Tier_1_General` into `Tier_1_General_Bucket_01..NN`, each
   sized to stay under the 10,000 ceiling. The skill's bucket example is a `Group`; here the
   owning entity is a Queue, so the buckets are queues and the public group behind each one is
   the membership source.
3. **Set `doesIncludeBosses` deliberately on bucket groups.** The skill says set it `false` on a
   bucket group on purpose: "every `true` adds hierarchy fan-out to a structure whose entire
   point is to *reduce* fan-out". That is a departure from the `true` this step writes on the
   three ordinary membership groups, and it is deliberate on both sides.
4. **Give every bucket a membership step.** Group membership is `GroupMember` data and does not
   travel with the metadata — "Members of the public group aren't migrated when you deploy the
   group type." A bucket group deployed with no members grants nothing at all.
5. **Suspend and resume around the move.** `Sharing.settings` carries `deferGroupMembership` and
   `deferSharingRules`. **Check before relying on it:** the defer-sharing-calculation feature is
   off until Salesforce Customer Support enables it for the org — deploying `true` into an org
   that never filed that case does nothing. Resume order matters: set `deferSharingRules` to
   `true` first if the two recalculations must be separated in time, because flipping
   `deferGroupMembership` back to `false` recalculates both.
6. **Prove it landed.** Re-run § 2's query, and count members per bucket group
   (`SELECT GroupId, Group.DeveloperName, COUNT(Id) members FROM GroupMember GROUP BY GroupId, Group.DeveloperName`).
   Non-zero per bucket, and no owner over the ceiling.

**Cheaper mitigation to consider first, before building buckets:** the skew here is driven by
cases *sitting* in the catch-all queue. Getting M3-S05's Omni-Channel push live, or closing the
loop on stale unaccepted cases, reduces the owned-record count without any new metadata. Buckets
are the remedy when the arrival rate alone exceeds what the pool clears.

## 4. Retirement — what to do before any of these queues is deleted

Q89's answer: **reassign open Cases to the surviving queue before the queue is deleted.**

The platform behaviour that makes this mandatory (`admin/queues-and-public-groups`
`references/gotchas.md` gotcha 2): deleting a queue does **not** reassign the records it owns.
Their `OwnerId` still points at the deleted queue, they disappear from every queue list view,
and they remain reachable only by SOQL. There is no undo that restores the queue's list view.

Order of operations:

1. **Count what the queue owns.** Adapted from gotcha 2's query:

   ```sql
   SELECT Id, CaseNumber, Subject, Status, Owner.Name
   FROM Case
   WHERE Owner.Name = '<queue label>' AND Owner.Type = 'Queue'
   ```

   Use the label as it appears in `<name>` — `Tier 1 General`, `Tier 2 Engineering`, `Billing` —
   not the developer name.
2. **Name the surviving queue.** For this build the fall-through owner is `Tier_1_General`
   (Q26: unmatched cases go to the Tier 1 General queue), so a retired `Tier_2_Engineering` or
   `Billing` reassigns to it. **If `Tier_1_General` itself is ever retired there is no
   fall-through target on file** — that decision is not answered by any clarification and must be
   taken by the process owner before the queue is touched.
3. **Reassign, then re-count.** Bulk-update `OwnerId` to the surviving queue, then re-run the
   query in step 1 and confirm it returns zero rows. Delete only on zero.
4. **Sweep the references before deleting.** A queue is named by developer name from several
   places this build creates, and a dangling reference breaks the referring component, not the
   queue: the Case assignment rules (M3-S04), the Omni-Channel routing configuration (M3-S05),
   and the escalation rules that reassign to Tier 2 after 8 business hours (M4). Each must be
   repointed or removed in the same change.
5. **Retire the paired public group too, or deliberately keep it.** `Support_Tier_1`,
   `Support_Tier_2` and `Billing_Team` exist to feed these queues. A group left behind after its
   queue is gone is a membership list nobody maintains.

## 5. Membership hygiene (ongoing, not only at retirement)

- **Deactivated users are not removed from queue or group membership automatically**
  (`queues-and-public-groups` gotcha 4). The queue keeps listing them and keeps accepting
  assignments; the effective capacity is silently lower than the roster. Add a group-membership
  check to the user-deactivation checklist:

  ```sql
  SELECT Group.Name, Group.Type
  FROM GroupMember
  WHERE UserOrGroupId = '<deactivated_user_id>'
  ```

- **Reporting reads queue-owned cases as owned by the queue** (gotcha 1). "My Open Cases" and any
  owner-grouped report or roll-up will exclude or mis-attribute everything sitting in these three
  queues until an agent accepts it. Any intake dashboard built for this release has to filter on
  `Owner.Type = 'Queue'` explicitly rather than assume a user owner.
- **Keep the groups flat.** None of the three groups contains another group, and it should stay
  that way: nesting multiplies the scope of every sharing recalculation
  (`queues-and-public-groups` gotcha 3).

## 6. Post-deploy actions this metadata cannot perform

| Action | Why it is not metadata |
|---|---|
| Populate `Support_Tier_1`, `Support_Tier_2`, `Billing_Team` with the 12 / 4 / 2 users (Q8) | Group membership is `GroupMember` data; the guide states members are not migrated when the group type is deployed |
| Confirm the three rosters against the current team lists | Manual, and the plan's own W02 (2 of 3) acceptance test asks a support manager to do exactly this at the M2 gate |
| Verify queue email delivery for `Billing` | Requires sending a test case into the queue in a sandbox (Q68's sandbox test) |
