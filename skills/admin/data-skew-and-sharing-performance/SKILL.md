---
name: data-skew-and-sharing-performance
description: "Diagnose and mitigate Salesforce data skew — ownership skew (single user owns >10,000 records) and parent-child skew (>10,000 children under one parent) — that cause sharing recalculation slowness, group membership lock errors, and record-level locking failures. NOT for sharing model design decisions (use sharing-and-visibility) or query optimization (use soql-query-optimization)."
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
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-03
---

# Data Skew and Sharing Performance

Use this skill when users report slow sharing recalculations, group membership lock errors, or degraded performance when updating records owned by a small number of users or parented under a single account. This skill diagnoses ownership skew and parent-child skew and recommends targeted mitigations.

---

## Before Starting

Gather this context before working on anything in this domain:

- Identify which objects are suspected: note API names and approximate record counts.
- Find the ownership distribution: run a report grouped by Record Owner on the suspect object, sorted descending. Flag any user or queue owning more than 10,000 records of a single object.
- For parent-child skew: run a report on the child object grouped by parent (Account, Case, etc.). Flag any parent that has more than 10,000 children.
- Know the current OWD for affected objects: Private OWD combined with a role hierarchy amplifies recalculation cost.
- Know whether the org uses sharing rules sourced from roles or public groups — these are the triggers for recalculation fan-out.

---

## Core Concepts

### Ownership Data Skew

Ownership data skew occurs when a single user or queue owns more than 10,000 records of a single object. This is the most common performance trap for orgs that park records under a catch-all user (e.g., an "Unassigned Leads" queue or a single integration user that owns all migrated records).

**Why it causes problems:** When a user moves in the role hierarchy — or is added to or removed from a public group that is the source of a sharing rule — Salesforce must update the sharing table entries for every record that user owns. With 50,000 records owned by one user, a single role change triggers 50,000 sharing table recalculations. This can produce long-running background jobs, "Group membership operation already in progress" errors, and lock contention that blocks other sharing operations.

**The 10,000-record threshold:** Salesforce documents this explicitly in the *Designing Record Access for Enterprise Scale* guide. Below 10,000 records per owner, most sharing operations complete quickly. Above this threshold, any change that triggers recalculation for that owner becomes a risk.

### Parent-Child Data Skew

Parent-child data skew occurs when a single parent record (typically an Account) has more than 10,000 child records (Contacts, Cases, Opportunities, or other related objects). This is often seen in "catch-all" accounts created to park unassociated contacts from marketing imports.

**Why it causes problems:** Salesforce maintains *implicit sharing* — when a user gains access to a child record (e.g., a Contact), the system automatically grants that user read access to the parent Account. When that user later loses access to the child, Salesforce must scan all other children of that parent to determine whether the implicit parent share should be retained or removed. With 300,000 contacts under one account, this scan becomes expensive and can cause lock contention and performance degradation on every access change operation.

**The implicit sharing chain:** This is not just a bulk data load problem — even a single-record update that changes ownership of a child record will trigger this scan if the parent is highly skewed.

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
3. Use serial processing mode for bulk operations that modify group membership if parallel mode produces lock errors.
4. Avoid running user provisioning at the same time as deployments that update group membership or include Apex tests that modify sharing structures.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Single user owns >10,000 records, user has a role | Distribute ownership across multiple users/queues | Role presence makes any role change trigger fan-out recalculation |
| Single user owns >10,000 records, business requires single owner | Remove user from role hierarchy | No role = no role-based sharing recalculation triggered |
| Account has >10,000 child records, child sharing can follow parent | Set child OWD to "Controlled by Parent" | Disables implicit sharing scan entirely |
| Account has >10,000 child records, child needs independent sharing | Split children across multiple parent accounts | Keeps implicit sharing scan bounded per parent |
| Lock errors during end-of-quarter role updates | Sequence operations in non-overlapping windows + add retry logic | Locks are held briefly but amplified by concurrent volume |
| New data import would create skew | Distribute across multiple owners/parents during import | Prevention is cheaper than remediation |

---


## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. Gather context — confirm the org edition, relevant objects, and current configuration state
2. Review official sources — check the references in this skill's well-architected.md before making changes
3. Implement or advise — apply the patterns from Core Concepts and Common Patterns sections above
4. Validate — run the skill's checker script and verify against the Review Checklist below
5. Document — record any deviations from standard patterns and update the template if needed

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] No single user or queue owns more than 10,000 records of any single object.
- [ ] No single Account (or other parent) has more than 10,000 child records in any child object.
- [ ] "Parking lot" users that must hold large record counts are placed outside the role hierarchy (no role assigned) or at the top of the hierarchy and never moved.
- [ ] Child objects where sharing can follow the parent are configured as "Controlled by Parent" OWD.
- [ ] Integration processes that update role/group structure include retry logic for lock errors.
- [ ] Bulk reassignment operations are batched in off-peak windows, not run in one large transaction.
- [ ] Sharing recalculation background jobs are monitored after any large role or ownership change.

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

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

## Related Skills

- sharing-and-visibility — Use for designing the overall sharing model (OWD, roles, sharing rules). This skill handles performance problems that arise from an existing sharing model, not model design.
- soql-query-optimization — Use when query performance is the problem. Data skew affects sharing maintenance, not SOQL query plans directly.
