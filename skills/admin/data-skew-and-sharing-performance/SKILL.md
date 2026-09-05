---
name: data-skew-and-sharing-performance
description: "Diagnose and mitigate Salesforce data skew — ownership skew (single user owns >10,000 records) and parent-child skew (>10,000 children under one parent) — that cause sharing recalculation slowness, group membership lock errors, and record-level locking failures. Covers lookup skew and UNABLE_TO_LOCK_ROW, Defer Sharing Calculation (deferGroupMembership / deferSharingRules in Sharing.settings), ownership bucket groups, Controlled by Parent OWD, Bulk API serial vs parallel concurrency for skewed loads, and the documented load ordering for roles, groups and sharing rules. NOT for planning and batching a recalculation job — use data/sharing-recalculation-performance. NOT for designing the sharing model itself — use admin/sharing-and-visibility."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Scalability
triggers:
  - "sharing recalculation is taking too long or never finishing"
  - "group membership operation already in progress error when changing user roles"
  - "org performance degrades when reassigning account ownership"
  - "could not acquire lock error during large data load or user provisioning"
  - "page load is slow when opening an account with thousands of child records"
  - "how do I fix data skew in Salesforce"
  - "data skew hits the timeout"
  - "unable to lock row error when loading child records under one parent"
  - "bulk api job fails with too many lock failures"
  - "defer sharing calculation before a large data load"
  - "what order do I load users roles groups and sharing rules"
  - "integration user owns every record should I give them a role"
  - "one account has 400,000 contacts and record pages are slow"
  - "split a catch-all queue into ownership buckets"
  - "sharing rule on a lookup field is not selective"
  - "lookup skew lock contention during bulk load"
tags:
  - data-skew
  - sharing-recalculation
  - ownership-skew
  - performance
  - large-data-volumes
inputs:
  - "Object(s) suspected of data skew: name and rough record count"
  - "Ownership distribution: which users or queues own most records"
  - "Parent-child relationship details: which child objects and counts per parent"
  - "Current OWD (org-wide defaults) and sharing rule configuration"
outputs:
  - "Data skew diagnosis report identifying skew type (ownership vs parent-child)"
  - "Mitigation recommendations per skew type with trade-off notes"
  - "Review checklist for ongoing data health"
dependencies: []
version: 1.1.0
author: Pranav Nagrecha
updated: 2026-09-05
---

# Data Skew and Sharing Performance

Use this skill when users report slow sharing recalculations, group membership lock errors, or degraded performance when updating records owned by a small number of users or parented under a single account. This skill diagnoses ownership skew and parent-child skew and recommends targeted mitigations.

---

## Before Starting

Gather this context before working on anything in this domain:

- Identify which objects are suspected: note API names and approximate record counts.
- Find the ownership distribution: run a report grouped by Record Owner on the suspect object, sorted descending. Flag any user or queue owning more than 10,000 records of a single object.
- For parent-child skew: run a report on the child object grouped by parent (Account, Case, etc.). Flag any parent that has more than 10,000 children.
- For lookup skew: group the object by each custom lookup field's value, not just by parent. Flag any single target record that most records point at, and record whether that object takes concurrent high-volume inserts or updates — concurrency is what turns lookup skew into lock failures.
- Know the current OWD for affected objects: Private OWD combined with a role hierarchy amplifies recalculation cost.
- Know whether the org uses sharing rules sourced from roles or public groups — these are the triggers for recalculation fan-out.

---

## Questions to Ask Before Configuring

Ask these before the change window is booked. Every one of them has a documented behaviour behind it, and skipping any one produces a remediation that deploys cleanly and still takes the org down.

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "What is the top owner's record count, and does that user hold a role today?" | Removal from a role costs the same recalculation as addition; the LDV guide's ceiling is "Avoid having any user own more than 10,000 records" (`ldv.txt` L1033) | The ownership row of the skew plan, and whether the fix is buckets or role removal |
| "Is the write volume against the skewed parent or lookup concurrent, or does one job own the window?" | Lookup skew with low concurrency causes no locking at all — concurrency is the diagnosis, the count is only the symptom | A remediate/monitor decision, so effort goes to the skew that is actually failing |
| "What manual shares, sharing rules, and Apex-managed shares exist on the child object today?" | "Controlled by Parent" removes every independent child grant, and manual shares can't be retrieved or deployed (`api_meta.txt` L129249) | The access-loss inventory that has to be re-granted, and whether the OWD change is viable at all |
| "Has Support enabled Defer Sharing Calculation in this org, and who holds the permission?" | The feature is off by default and needs a Support case (`api_meta.txt` L127000) — a deploy of `deferGroupMembership` into an unprovisioned org is a no-op | A booked lead time, or a plan that does not depend on deferral |
| "Which API is the load using — Bulk API 2.0 or Bulk API v1?" | Bulk API 2.0's `concurrencyMode` is "Reserved for future use… only parallel mode is supported" (`api_asynch.txt` L3050) so serial is unavailable there | The right API chosen before the runbook is written, not after the first lock failure |
| "Can the load file be sorted by parent id before submission?" | "group records by the field `ParentId` in the same batch to minimize locking conflicts" (`ldv.txt` L894) is cheaper than serial mode and costs no throughput | A sort step in the ETL that removes most contention without slowing the job |
| "Is this a first load into an empty org, or remediation of a live one?" | Public Read/Write during initial load to skip sharing computation (`ldv.txt` L852) is only available to the first case; live orgs get deferral and sequencing instead | The correct branch of the load-ordering plan in `references/metadata-examples.md` § 7 |

What a proper configuration adds over just reassigning the records: the ownership buckets, sharing rules, OWD and indexed load keys deploy as reviewed metadata with a suspend-and-resume pair around them, the load runs in an API and concurrency mode that can actually honour the lock constraints, and the post-change queries prove that group membership landed and implicit parent shares went away — instead of a green deploy over four empty groups.

---

## Core Concepts

### Ownership Data Skew

Ownership data skew occurs when a single user or queue owns more than 10,000 records of a single object. This is the most common performance trap for orgs that park records under a catch-all user (e.g., an "Unassigned Leads" queue or a single integration user that owns all migrated records).

**Why it causes problems:** When a user moves in the role hierarchy — or is added to or removed from a public group that is the source of a sharing rule — Salesforce must update the sharing table entries for every record that user owns. With 50,000 records owned by one user, a single role change triggers 50,000 sharing table recalculations. This can produce long-running background jobs, "Group membership operation already in progress" errors, and lock contention that blocks other sharing operations.

**The 10,000-record threshold:** Salesforce documents this explicitly in the *Designing Record Access for Enterprise Scale* guide, and the *Best Practices for Deployments with Large Data Volumes* guide states the same ceiling as a general best practice: under the goal "Avoiding sharing computations", the practice is "Avoid having any user own more than 10,000 records." (`ldv.txt` L1033). Below 10,000 records per owner, most sharing operations complete quickly. Above this threshold, any change that triggers recalculation for that owner becomes a risk. Treat it as a guideline, not an enforced cap — the platform does not block ownership above it.

### Parent-Child Data Skew

Parent-child data skew occurs when a single parent record (typically an Account) has more than 10,000 child records (Contacts, Cases, Opportunities, or other related objects). This is often seen in "catch-all" accounts created to park unassociated contacts from marketing imports.

**Why it causes problems:** Salesforce maintains *implicit sharing* — when a user gains access to a child record (e.g., a Contact), the system automatically grants that user read access to the parent Account. When that user later loses access to the child, Salesforce must scan all other children of that parent to determine whether the implicit parent share should be retained or removed. With 300,000 contacts under one account, this scan becomes expensive and can cause lock contention and performance degradation on every access change operation.

**The implicit sharing chain:** This is not just a bulk data load problem — even a single-record update that changes ownership of a child record will trigger this scan if the parent is highly skewed. The implicit share is visible in the share table: `AccountShare.RowCause` value `ImplicitParent` means "The User or Group has access because they're the owner of or have sharing access to records related to the account, such as opportunities, cases, contacts, contracts, or orders." (`object_reference.txt` L17743). Note that `ImplicitParent`, `Manual`, and `Owner` shares "are compressed into one record with the highest level of access" (`object_reference.txt` L17816), so counting share rows understates how many grants were evaluated.

**The documented mitigation is arithmetic, not architecture:** "Distribute child records so that no parent has more than 10,000 child records. For example, in a deployment that has many contacts but does not use accounts, set up several dummy accounts and distribute the contacts among them." (`ldv.txt` L1052–L1056). The related-list rendering symptom is a documented case study of the same cause, and the interim relief there was the **Enable Separate Loading of Related Lists** setting, which lets the account detail render while the related list query is still running (`ldv.txt` L1173–L1177) — relief, not a fix.

### Lookup Skew

Salesforce's *Large Data Volumes* module defines data skew as "more than 10,000 child records are associated with the same parent record within an org" and names three variants — account data skew, ownership skew, and **lookup skew**: "a very large number of records are associated with a single record in the lookup object." Lookup skew is the variant most often left out of a skew audit.

**Why it causes problems:** This is a write-time problem, not a query-time one. "Every time a record is inserted or updated, Salesforce must lock the target records that are selected for each lookup field; this practice ensures that, when the data is committed to the database, its integrity is maintained." Concurrent DML against records sharing one lookup target therefore serialises on that target row and fails with `UNABLE_TO_LOCK_ROW`, the API status code for "A deadlock or timeout condition has been detected." If one record in a batch can't be locked, the entire batch fails, and the error message carries the IDs of the records that could not be locked, when available.

**Lock duration is your own code:** "Locks are held the entire time your custom code is executing," so triggers, flows, and roll-ups firing on the child object widen the window in which a competing transaction collides.

**Skew alone is not the diagnosis:** "Lookup skew under certain usage patterns may not cause any problem at all." A concentrated lookup with low concurrent write volume is fine. Confirm concurrency before remediating.

### Group Membership Locking

Salesforce uses table-level locks to protect the integrity of group membership data during updates. When a role change, sharing rule recalculation, or user provisioning operation holds these locks for a long time (driven by data skew), other concurrent operations — such as admins updating user roles or integration processes provisioning new users — will fail with "could not obtain lock" or "Group membership operation already in progress."

**Granular locking (enabled by default):** Salesforce enables granular locking by default, which allows some concurrent group operations when there is no hierarchical relationship between the affected roles or groups. However, operations like role reparenting still block most other group updates, regardless of granular locking.

**Peak-risk windows:** These errors are most likely during organizational realignments (end-of-quarter, end-of-year) when many account assignments and role changes happen simultaneously.

---

## Common Patterns

### Pattern 1 — Distribute Ownership to Reduce Skew

**When to use:** You have identified a user or queue that owns more than 10,000 records. You cannot redesign the data model but can re-distribute ownership.

**How it works:**
1. Identify the top-skewed owners using a record count report grouped by owner.
2. Reassign records in batches — avoid bulk-reassigning all records at once, which itself triggers recalculation. Use Apex batch jobs or Data Loader scheduled in off-peak hours.
3. For "parking lot" users (integration users, unassigned queues), create multiple queues and distribute records across them to keep each under 10,000.
4. If the parking-lot user must retain ownership (business requirement), remove them from all roles. A user with no role cannot trigger role-hierarchy-based sharing recalculations. As documented in the *Designing Record Access for Enterprise Scale* guide: place these users in a role at the very top of the hierarchy and never move them, or remove them from the role hierarchy entirely.

**Why not a single catch-all user:** Every time that user is added to or removed from a public group, or their role changes, the entire set of owned records must be recalculated.

### Pattern 2 — Break Up Skewed Parent Accounts

**When to use:** A single Account has more than 10,000 child records (Contacts, Cases, etc.) — typically from a marketing import or a "catch-all" account pattern.

**How it works:**
1. Identify skewed accounts using a SOQL count query: `SELECT AccountId, COUNT(Id) FROM Contact GROUP BY AccountId HAVING COUNT(Id) > 10000`
2. Create segmentation accounts (e.g., by region, import batch, or lifecycle stage) to split the children.
3. Re-parent children in batches to keep each account below 10,000 children.
4. Where possible, configure child object OWD as "Controlled by Parent" — this disables implicit parent sharing and eliminates the scan-on-access-change entirely. Only use this when the child's sharing model can truly follow the parent.

**Why not keep one large parent:** Every access change to any of the children forces Salesforce to scan all sibling records to maintain implicit sharing integrity.

### Pattern 3 — Sequence Maintenance Operations to Avoid Lock Contention

**When to use:** You have ongoing integrations or batch processes that update role/group structure concurrently, causing lock errors.

**How it works:**
1. Schedule role hierarchy and public group maintenance processes in non-overlapping time windows.
2. Add retry logic to integrations: if a "lock" error is returned, wait and retry — do not surface it immediately as a hard failure.
3. Reorganise the batches before reaching for serial mode: "group records by the field `ParentId` in the same batch to minimize locking conflicts" (`ldv.txt` L894–L896). The Bulk API guide's own preference is to "Avoid processing data in serial mode unless you know that parallel mode would otherwise result in lock timeouts and you can't reorganize your batches to avoid locks" (`api_asynch.txt` L4993–L4995).
4. If serial concurrency is genuinely needed, use **Bulk API v1** and set `JobInfo.concurrencyMode` to `Serial`. Bulk API 2.0 cannot do this — its `concurrencyMode` is "Reserved for future use… Currently only parallel mode is supported… The mode isn't user configurable." (`api_asynch.txt` L3050–L3054). Salesforce names four operations as likely to need it: creating users, updating ownership for records with private sharing, updating user roles, and updating territory hierarchies (`api_asynch.txt` L5010–L5015) — a skew remediation is mostly the middle two.
5. Avoid running user provisioning at the same time as deployments that update group membership or include Apex tests that modify sharing structures.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Single user owns >10,000 records, user has a role | Distribute ownership across multiple users/queues | Role presence makes any role change trigger fan-out recalculation |
| Single user owns >10,000 records, business requires single owner | Remove user from role hierarchy | No role = no role-based sharing recalculation triggered |
| Account has >10,000 child records, child sharing can follow parent | Set child OWD to "Controlled by Parent" | Disables implicit sharing scan entirely |
| Account has >10,000 child records, child needs independent sharing | Split children across multiple parent accounts | Keeps implicit sharing scan bounded per parent |
| Concurrent inserts/updates fail with `UNABLE_TO_LOCK_ROW` on a low-cardinality custom lookup | Distribute across more lookup values first; leave the field blank where it does not apply rather than pointing records at a catchall | The lookup target row is locked per DML — fewer records per target means less contention, and distribution is reversible |
| Lookup values are few, static, and the target object holds no other data anyone reads | Replace the lookup with a picklist | Removes the target-record lock entirely; generally not available if the lookup records carry additional fields and other data |
| Lock errors during end-of-quarter role updates | Sequence operations in non-overlapping windows + add retry logic | Locks are held briefly but amplified by concurrent volume |
| New data import would create skew | Distribute across multiple owners/parents during import | Prevention is cheaper than remediation |

---


## Recommended Workflow

1. **Measure all three skews before naming one.** Run the three `GROUP BY` diagnostics and the `GROUP BY ROLLUP` distribution query in `references/metadata-examples.md` § 6 — by `OwnerId`, by parent id, and by *each* custom lookup field. Record the counts in `templates/data-skew-and-sharing-performance-template.md` and save the same numbers as `skew-plan.json` for the checker.

2. **Weight each hit by write concurrency, then classify.** A lookup target holding 900,000 rows on an object nobody writes concurrently is a finding, not an incident. Use the Decision Guidance table below to pick the pattern per hit, and check the count against the optimizer's selectivity thresholds in `references/metadata-examples.md` § 6 to see whether reads are affected too or only writes.

3. **Answer the Questions to Ask above before designing.** In particular, confirm whether Defer Sharing Calculation exists in the org and which Bulk API the load uses — both change the shape of the plan, and both have weeks-long lead times if the answer is no.

4. **Write the metadata, not just the advice.** Build the `Sharing.settings` suspend/resume pair, bucket `Group` files, per-bucket `SharingRules`, `sharingModel` changes and External Id load keys from `references/metadata-examples.md` §§ 1–5. Every bucket group needs a paired `GroupMember` load step — group membership does not travel with the metadata.

5. **Lint the package and the plans.** Run `python3 scripts/check_data_skew_and_sharing_performance.py --manifest-dir <dir> --skew-plan skew-plan.json --job-plan bulk-job-plan.json`. It flags parents and owners over the guide's ceiling, bucket groups with no membership step, criteria rules filtering on fields that carry no index, and Bulk jobs set to parallel against a skewed target.

6. **Sequence the execution in the documented order.** Follow the load-ordering table in `references/metadata-examples.md` § 7 — roles, then record data, then groups and queues, then sharing rules one at a time — with deferral suspended around it and the resume as its own deploy.

7. **Verify with the post-change queries, then walk the Review Checklist.** `EntityDefinition` for the OWD, `GroupMember` counts per bucket, and `AccountShare` grouped by `RowCause` to confirm `ImplicitParent` shares actually went away. Record deviations and their business reason in the template.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] No single user or queue owns more than 10,000 records of any single object.
- [ ] No single Account (or other parent) has more than 10,000 child records in any child object.
- [ ] No custom lookup field concentrates the bulk of an object's records on one or two target records where concurrent write volume is high.
- [ ] "Parking lot" users that must hold large record counts are placed outside the role hierarchy (no role assigned) or at the top of the hierarchy and never moved.
- [ ] Child objects where sharing can follow the parent are configured as "Controlled by Parent" OWD.
- [ ] Integration processes that update role/group structure include retry logic for lock errors.
- [ ] Bulk reassignment operations are batched in off-peak windows, not run in one large transaction.
- [ ] Sharing recalculation background jobs are monitored after any large role or ownership change.
- [ ] Defer Sharing Calculation is confirmed provisioned in this org (it needs a Support case) before any runbook step depends on it, and the resume is a deployable `Sharing.settings` file rather than a Setup click.
- [ ] Every bucket `Group` deployed has a paired `GroupMember` load step, and the post-deploy membership count query returns non-zero for each bucket.
- [ ] `includeRecordsOwnedByAll` is set explicitly on every new criteria-based sharing rule — it cannot be edited after creation.
- [ ] Any load needing serial concurrency is a Bulk API v1 job; the file is sorted by parent id; and no Bulk API 2.0 job in the plan claims `concurrencyMode: Serial`.
- [ ] `python3 scripts/check_data_skew_and_sharing_performance.py --manifest-dir <dir> --skew-plan skew-plan.json --job-plan bulk-job-plan.json` has been run and every finding is either fixed or recorded with a reason.

---

## Salesforce-Specific Gotchas

The three that catch practitioners most often. `references/gotchas.md` carries eleven, including the ones that only surface at deploy time — deferral that was never provisioned, "serial mode" that ran in parallel, and bucket groups that deploy empty.

1. **Removing a user from a role can be as expensive as adding them** — The recalculation runs in both directions. If a user with 80,000 records is removed from a sharing-rule source group, all 80,000 records must be evaluated. Many admins are surprised that "un-assigning" a role is not a fast operation.

2. **Implicit sharing scans happen on child-record access loss, not just batch loads** — A single record update that changes the owner of one Contact under a 500,000-contact Account will trigger a full implicit-sharing scan on that account. This is not a bulk-only problem.

3. **"Controlled by Parent" removes implicit sharing — but also all independent access grants** — Setting a child object to "Controlled by Parent" eliminates the implicit sharing scan, but it also means you can no longer share individual child records directly. All access to children is inherited from the parent. Admins who switch to this OWD mid-implementation often break existing manual shares or sharing rules on the child object.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Data Skew Diagnosis Report | Summary of skewed objects, owners, and parent accounts with record counts and risk classification |
| Mitigation Plan | Prioritized list of actions: ownership redistribution, parent splitting, OWD changes, and sequencing guidance |
| Ongoing Health Checklist | Repeatable checklist to catch new skew before it causes production problems |

---

## Reference Files

| File | Read it when |
|---|---|
| `references/metadata-examples.md` | Writing the deployable artifacts — the `Sharing.settings` suspend/resume pair, bucket `Group` files, per-bucket `SharingRules`, `sharingModel` and External Id field XML, the `package.xml` and `sf` deploy sequence, the diagnostic and post-change queries with the optimizer's selectivity thresholds, and the Bulk API load-ordering plan |
| `references/gotchas.md` | Something deployed green and behaved wrong — deferral that never engaged, "serial mode" that ran in parallel, bucket groups that grant nothing, an index Support says already exists, a sharing-rule setting that will not edit, or a failed batch that half-committed |
| `references/examples.md` | Sizing a remediation end to end — the integration-user ownership skew and the catch-all account, each with the numbers, the fix, and why it works |
| `references/well-architected.md` | Justifying a tradeoff (ownership distribution vs integration simplicity, Controlled by Parent vs independent child sharing) or locating the official source behind a claim in this skill |
| `references/llm-anti-patterns.md` | Reviewing skew advice an AI assistant produced, especially "just reassign the records" or a diagnosis that names only two skew types |
| `templates/data-skew-and-sharing-performance-template.md` | Running workflow steps 1–2 — the ownership, parent, and lookup measurement tables and the mitigation plan |
| `scripts/check_data_skew_and_sharing_performance.py` | Workflow step 5, before every deploy and before every skewed load |

---

## Related Skills

- `admin/sharing-and-visibility` — Use for designing the overall sharing model (OWD, roles, sharing rules). This skill handles performance problems that arise from an existing sharing model, not model design.
- `data/soql-query-optimization` — Use when query performance is the problem. Data skew affects sharing maintenance, not SOQL query plans directly.
- `data/sharing-recalculation-performance` — Use when the recalculation job itself has to be planned and batched. This skill diagnoses the skew that makes the job expensive; that skill runs the job.
- `architect/large-data-volume-architecture` — Use for the wider LDV design question (skinny tables, divisions, archival, data tiering) when skew is one symptom of a data-volume problem rather than the whole problem.
- `data/bulk-api-and-large-data-loads` — Use when the load mechanics themselves are the work: batch sizing, PK chunking, job monitoring, and error reconciliation.
