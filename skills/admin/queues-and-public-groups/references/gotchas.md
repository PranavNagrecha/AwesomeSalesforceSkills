# Gotchas — Queues and Public Groups

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Queue-Owned Records Show the Queue as Owner — Reports and Rollups Break

**What happens:** When a Case or Lead is owned by a queue, the `OwnerId` field contains the queue's Group Id (not a User Id). Report columns like "Owner Name," "Owner Email," and "Owner Role" display the queue name, not any individual user. Reports grouped by Owner produce a separate row for the queue. Rollup Summary fields, dashboards with "Current User" filters, and "My Cases" list views exclude queue-owned records entirely — they only count user-owned records.

**When it occurs:** Any time cases or leads sit in a queue unaccepted. In orgs where work stays in queues for extended periods before agents claim records, a significant portion of the data becomes invisible in user-scoped views and reports.

**How to avoid:** Design reports that explicitly include queue-owned records by adding a filter for `Owner Type = Queue` or by building a report type that surfaces both queue-owned and user-owned records. Brief agents that "My Open Cases" does not show queue work — they must check the queue list view. Consider using a field like `Date/Time Accepted` (custom field) to track when ownership transfers from queue to user.

---

## Gotcha 2: Deleting a Queue Does Not Reassign Owned Records

**What happens:** If you delete a queue that still owns records, Salesforce does not automatically reassign those records to any user. The records remain with the deleted queue's Id as OwnerId. These records become unreachable through the normal queue list view (the queue no longer exists) and are effectively orphaned in queue-based views. They still exist in the database and are queryable via SOQL, but they are invisible to agents browsing queue lists.

**When it occurs:** Queue cleanup exercises, team reorganizations, or support team restructuring where old queues are retired without first migrating the owned records.

**How to avoid:** Before deleting any queue, run a SOQL query to find all records owned by it:

```soql
SELECT Id, CaseNumber, Subject, Owner.Name
FROM Case
WHERE Owner.Name = 'Queue To Delete'
```

Bulk-reassign those records to a new queue or a default user before deleting the queue. Only delete the queue after confirming `COUNT()` returns zero.

---

## Gotcha 3: Nested Public Groups Slow Sharing Recalculation Significantly

**What happens:** When a public group contains other public groups (nesting), Salesforce must traverse the full membership graph every time sharing recalculation runs. Each membership change — adding a user, removing a role, changing a role hierarchy — triggers a sharing recalculation for all objects with sharing rules that reference the group. In orgs with millions of records and deeply nested groups, this recalculation can lock the affected object's sharing table for hours, causing timeouts and deferred access grants.

**When it occurs:** Orgs that model complex organizational hierarchies using nested groups, or that use a single "mega-group" containing many sub-groups for convenience. Becomes critical during active user provisioning periods (onboarding batches, reorgs) when multiple membership changes occur in short succession.

**How to avoid:** Keep public group membership as flat as possible. Add Roles or Roles and Subordinates directly to the group instead of wrapping them in nested groups. If nesting is unavoidable, limit to one level of nesting and avoid changing membership during business hours. Monitor the Sharing Recalculation job in Setup → Background Jobs when membership changes are made.

---

## Gotcha 4: Deactivated Users Are Not Auto-Removed from Queue Membership

**What happens:** When a user is deactivated, Salesforce does not remove them from queue membership. The queue continues to list them as a member. The queue email still receives notifications for assignments. However, the deactivated user cannot log in and claim any queue-owned records, leaving those records visible in the queue but with reduced effective capacity.

**When it occurs:** Any org without a formal offboarding checklist that includes queue membership cleanup. Common in orgs with high turnover or seasonal contractors.

**How to avoid:** Include queue membership review in the user deactivation checklist. Query `GroupMember` records where `UserOrGroupId` matches the deactivated user to find all group and queue memberships:

```soql
SELECT Group.Name, Group.Type
FROM GroupMember
WHERE UserOrGroupId = '<deactivated_user_id>'
```

Remove the user from each queue and group before or immediately after deactivation.

---

## Gotcha 5: Queue Email Notifies the Queue Address, Not Individual Members

**What happens:** Many admins expect that assigning a record to a queue sends an individual email to every queue member. This is incorrect. Salesforce sends one notification to the queue's configured email address only. If the queue email field is blank, no notification is sent at all. Individual members receive no email unless they have their own notification rules or Omni-Channel presence.

**When it occurs:** When a team expects to be notified individually about new queue assignments but the queue email is either not configured, points to an unmonitored alias, or is assumed to fan out to all members.

**How to avoid:** Set the queue email to a monitored team distribution list (not an individual's mailbox). Communicate to the team that queue email is a team-level notification, not a per-member alert. If per-member notification is required, configure a Flow that runs on record assignment and sends individual emails, or use Omni-Channel which has its own presence and routing notifications.
