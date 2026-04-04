---
name: queues-and-public-groups
description: "Use this skill when creating or managing queues, configuring queue membership, setting up case or lead queues, creating public groups, or using groups in sharing rules and manual sharing. Trigger keywords: queue, public group, queue membership, queue email, group sharing, case queue, lead queue. NOT for assignment rules that route records to queues automatically (use assignment-rules). NOT for Omni-Channel routing configuration (separate routing engine)."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Scalability
triggers:
  - "how to create a support queue for my team in Salesforce"
  - "set up a public group for use in sharing rules"
  - "assign cases to a queue instead of a specific person"
  - "how do I add users to a Salesforce queue"
  - "configure queue email notification when a case is added to the queue"
  - "create a regional public group for opportunity sharing in EMEA"
  - "difference between a queue and a public group in Salesforce"
tags:
  - queues
  - public-groups
  - case-management
  - lead-management
  - sharing
  - routing
  - access-control
inputs:
  - "Object type: whether queues are needed for Case, Lead, Orders, or a custom object with queues enabled"
  - "Team structure: which users, roles, or role hierarchies should be queue or group members"
  - "Sharing intent: whether the group is for sharing rules, manual sharing, list view visibility, or email alerts"
  - "Queue email address to notify the team when records enter the queue"
outputs:
  - "Configured queue with supported objects, membership, and optional queue email"
  - "Configured public group with correct member composition"
  - "Sharing rule or manual share configuration using the group"
  - "Decision guidance on queue vs public group for a given use case"
  - "SOQL pattern for finding queue-owned records"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-04
---

# Queues and Public Groups

This skill activates when an admin needs to create or manage queues (which own records and route work to teams) or public groups (which aggregate members for access sharing, sharing rules, and list view visibility). Use it alongside the assignment-rules skill when records must be routed to queues automatically.

---

## Before Starting

Gather this context before working in this domain:

- **Which objects are involved?** Queues only work with objects that have queue support enabled: Case, Lead, Order, and custom objects explicitly configured for queues. Standard objects like Account, Contact, and Opportunity do not support queue ownership.
- **What is the goal — routing work or sharing access?** Queues are for routing records to a pool of workers. Public groups are for granting shared access via sharing rules or manual sharing. The two mechanisms are distinct and should not be substituted for each other.
- **Understand org sharing model first.** Public group utility depends on the org-wide default (OWD) setting. If OWD is Public Read/Write for an object, groups add no incremental access. Groups are most valuable in Private or Public Read Only OWDs.
- **Platform limit on sharing recalculation.** Deeply nested public groups (groups containing groups containing groups) trigger expensive sharing recalculation jobs when membership changes. Prefer flat group structures in high-volume orgs.

---

## Core Concepts

### Queues

A queue is a special type of record owner that represents a pool of users, rather than a single individual. Records assigned to a queue are visible to all queue members through the queue's list view. Any queue member can claim ownership by changing the record's Owner field to themselves.

**Supported objects for queues:** Case, Lead, Order, and custom objects where "Allow Queues" is checked on the object definition. Account, Contact, Opportunity, and most other standard objects do not support queue ownership.

**Queue membership types:** A queue can include individual Users, Roles, Roles and Subordinates, and Public Groups. Adding a Role automatically includes all users in that role; Roles and Subordinates also includes users in roles below it in the hierarchy.

**Queue email:** Each queue can have a single email address (individual address or distribution list). When a record is assigned to the queue, Salesforce sends a notification to that address. Individual queue members do not receive individual email notifications — only the queue email is triggered. Configure this address to reach the whole team, not a single person.

**Accepting work from a queue:** Queue-owned records are in a shared pool. A team member claims a record by changing the Owner field to themselves. Until claimed, the owner remains the queue. Records owned by a queue appear in list views scoped to that queue, not in any individual's "My Open Cases" or "My Leads" view.

**SOQL for queue-owned records:** Use `WHERE Owner.Type = 'Queue'` to filter records owned by any queue. To filter by a specific queue name: `WHERE Owner.Name = 'Tier 1 Support Queue'`. Note that `OwnerId` alone does not distinguish user-owned from queue-owned records — `Owner.Type` is required.

### Public Groups

A public group is a named collection of members used to grant access and control visibility. Unlike a queue, a public group does not own records — it only aggregates membership for sharing purposes.

**Member types a public group can include:** Users, Roles, Roles and Subordinates, other Public Groups, and Portal Users (Customer Portal or Partner Portal users when Communities/Experience Cloud is enabled). This composition flexibility allows a single group to span organizational boundaries.

**Uses of public groups:**
- **Sharing rules:** Both criteria-based and ownership-based sharing rules can target a public group as the "share with" recipient.
- **Manual sharing:** Users with the Share button on a record can manually share to a public group.
- **Queue membership:** A queue can include a public group as one of its member types, inheriting all the group's members.
- **List view visibility:** List views can be shared with a public group, controlling which users see which views.
- **Email alerts in Flow/Process Builder:** Email alerts can address a public group, sending the alert to all group members.

**Nested groups:** Public groups can contain other public groups. Nesting allows hierarchical structures but increases the cost of sharing recalculation. Every membership change triggers Salesforce to recompute all sharing rows for all objects with sharing rules that reference the group. In orgs with millions of records and complex group nesting, this recalculation can lock objects for extended periods. Flat group membership (direct users and roles) is preferred in high-volume orgs.

### Queues vs Public Groups

These two constructs serve different purposes and should not be substituted for each other:

| Aspect | Queue | Public Group |
|---|---|---|
| Can own records | Yes — record OwnerId can be a Queue Id | No — groups cannot own records |
| Supported objects | Case, Lead, Order, queue-enabled custom objects | Any object (for sharing, not ownership) |
| Used for sharing rules | No (indirectly — as queue member) | Yes — primary use case |
| Used for routing work | Yes — primary use case | No |
| Sends queue email notification | Yes — single address per queue | No |
| Member types | Users, Roles, Roles + Subordinates, Groups | Users, Roles, Roles + Subordinates, Groups, Portal Users |

---

## Common Patterns

### Pattern: Tiered Support Queues with Escalation

**When to use:** A support team handles cases at multiple levels of complexity. Tier 1 agents handle general inquiries; Tier 2 specialists handle complex or escalated cases. Records should enter Tier 1 first and escalate to Tier 2 when needed.

**How it works:**
1. Create a queue named `Tier 1 Support` for the Case object. Add Tier 1 agents as members. Configure a queue email (e.g., `support-t1@company.com`).
2. Create a queue named `Tier 2 Support` for the Case object. Add Tier 2 specialists as members. Configure a separate queue email.
3. Configure a Case Assignment Rule (see assignment-rules skill) to route new cases to Tier 1 Support.
4. Use an Escalation Rule or a Flow to detect when a case has been open in Tier 1 too long, then change the Owner to Tier 2 Support.
5. Tier 2 agents see the escalated case in their queue list view and claim ownership.

**Why not assign directly to a user:** Queue-based routing allows any available team member to claim work, preventing bottlenecks when a specific agent is unavailable.

### Pattern: Regional Public Group for Sharing Rules

**When to use:** Sales reps in EMEA need read access to Opportunities owned by other EMEA reps, but the org-wide default for Opportunity is Private. Assignment-rules would not solve this — the reps still need cross-user read access without changing ownership.

**How it works:**
1. Create a public group named `EMEA Sales Team`. Add all EMEA sales users directly, or add the EMEA Sales Role to include all role members automatically.
2. Navigate to Setup → Sharing Settings → Opportunity Sharing Rules → New.
3. Select rule type: Ownership-based. "Owned by members of" → EMEA Sales Team. "Share with" → EMEA Sales Team. Access: Read Only.
4. Salesforce recalculates sharing and grants all EMEA reps read access to each other's Opportunities.
5. When a new rep joins EMEA, add them to the group (or the role) and sharing is automatically extended.

**Why not use a Role hierarchy:** Role hierarchy grants upward visibility (managers see subordinates' records) but not peer visibility. A sharing rule with a public group grants horizontal access among peers in the group.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Route Cases or Leads to a team pool | Queue on Case or Lead object | Queues own records; team members claim from shared pool |
| Grant read/write access to a group of users | Public Group + Sharing Rule | Groups aggregate membership; sharing rules grant access |
| Custom object needs team-based ownership | Enable queues on object, then create queue | Custom objects require explicit queue enablement in Setup |
| Need to share a Salesforce list view with a team | Public Group (assign list view to group) | List view visibility is controlled by public group membership |
| Email a team when a record is assigned | Queue email on the queue | Single address notified on queue assignment |
| Email an entire team from a Flow email alert | Public Group as alert recipient | Email alerts can target public groups, reaching all members |
| Object is Account, Contact, or Opportunity | Public Group (for sharing rules) only | These objects do not support queue ownership |
| Member changes cause slow sharing recalculation | Flatten group structure, reduce nesting depth | Each nested group multiplies recalculation scope |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working in this domain:

1. **Clarify the goal** — determine whether the need is record routing (queue) or access sharing (public group). Confirm which object is involved and whether it supports queues.
2. **Create the queue or public group in Setup** — for queues: Setup → Queues → New; configure supported objects, queue email, and members. For groups: Setup → Public Groups → New; add members by type (user, role, group).
3. **Configure downstream use** — for queues: set up an assignment rule or Flow to route records to the queue. For public groups: create a sharing rule that references the group, or assign list views to the group.
4. **Validate membership** — confirm all intended users are reachable through the membership chain (direct, via role, or via nested group). Deactivated users should be removed from queue membership to avoid stale ownership pools.
5. **Test the queue email** — assign a test record to the queue and confirm the queue email receives a notification.
6. **Run the checker script** — `python3 skills/admin/queues-and-public-groups/scripts/check_queues.py --manifest-dir <metadata-dir>` to surface any Group metadata references for review.
7. **Confirm SOQL uses Owner.Type** — any report or query on queue-owned records must use `Owner.Type = 'Queue'`; plain `OwnerId` checks will not distinguish queues from users.

---

## Review Checklist

Run through these before marking queue or public group configuration complete:

- [ ] Queue is associated with the correct supported objects (Case, Lead, Order, or queue-enabled custom object)
- [ ] Queue email is a team alias or distribution list — not an individual's inbox
- [ ] All queue members are active users; deactivated users have been removed
- [ ] Public group member composition is intentional — roles vs roles+subordinates distinction reviewed
- [ ] Sharing rules referencing the public group have been tested by logging in as an intended member
- [ ] Nested group depth is reviewed — prefer flat membership in orgs with more than 1M records per shared object
- [ ] SOQL queries on queue-owned records use `Owner.Type = 'Queue'` filter
- [ ] Reports and dashboards that count queue-owned records are validated — owner-grouped reports must account for queue ownership

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Queue-owned records show queue name as Owner in reports** — Owner Name, Owner Email, and Owner Role fields reflect the queue, not a user. Reports grouped by Owner or dashboards using Owner-based filters will show the queue name as a row, separate from any user's data. Rollup summaries and assignment-based reports may undercount or misattribute records until ownership is accepted by a user.
2. **Deleting a queue does not reassign records** — If a queue is deleted while it still owns records, those records become unowned or orphaned in some report contexts. Reassign all queue-owned records to a user or another queue before deleting a queue. Use a SOQL query (`WHERE Owner.Name = 'Queue Name'`) to find affected records first.
3. **Deactivated users remain in queue membership until removed** — Salesforce does not auto-remove deactivated users from queues. The queue still accepts assignments, still shows the deactivated user in its membership list, and still sends queue email to the configured address. This causes confusion when teams assume the membership is clean. Audit queue membership during every user deactivation.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Configured queue | Queue with supported objects, queue email, and verified membership |
| Configured public group | Named group with correct member composition for its intended sharing or visibility use |
| Sharing rule | Criteria-based or ownership-based rule referencing the public group |
| SOQL pattern | `WHERE Owner.Type = 'Queue'` filter for queue-owned record queries |
| Checker script output | List of Group metadata references found in the project metadata for review |

---

## Related Skills

- assignment-rules — use to route records automatically to queues based on criteria; queues must exist before assignment rules can target them
- sharing-and-visibility — broader sharing model design, including OWD settings, role hierarchy, and criteria-based sharing rules that use public groups
- escalation-rules — time-based re-routing of cases between queues when SLA is breached
- user-management — queue membership requires active users; deactivation workflows should include queue membership cleanup
