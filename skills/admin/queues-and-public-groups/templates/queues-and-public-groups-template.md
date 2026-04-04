# Queues and Public Groups — Design Template

Use this template when designing or documenting queue and public group configuration for a Salesforce org.

---

## Scope

**Request summary:** (describe what the user or stakeholder asked for)

**Goal type:** (check one)
- [ ] Record routing — queue to pool work for a team
- [ ] Access sharing — public group for sharing rules or manual sharing
- [ ] Both

---

## Queue Inventory

List all queues to be created or modified.

| Queue Name | Supported Objects | Queue Email | Members (Users / Roles / Groups) | Notes |
|------------|-------------------|-------------|----------------------------------|-------|
| [Queue 1]  | Case              | support@co.com | Role: Support Tier 1           | Primary inbound queue |
| [Queue 2]  | Case              | support-t2@co.com | Role: Support Tier 2        | Escalation queue |
| [Queue 3]  | Lead              | leads@co.com  | Public Group: EMEA Sales Team  |       |

### Queue Acceptance Workflow

**How will agents claim records?**
- [ ] Manually change Owner field from the queue list view
- [ ] Omni-Channel routing (routes from queue to agents automatically)
- [ ] Other: ___________________

---

## Public Group Inventory

List all public groups to be created or modified.

| Group Name | Member Types | Intended Use | Notes |
|------------|-------------|--------------|-------|
| [Group 1]  | Role: EMEA Account Exec | Opportunity sharing rule | Peer read access |
| [Group 2]  | Users: Jane Doe, John Smith | List view visibility | Admin team view |

### Nesting Review

**Does any group contain another group?**
- [ ] No nesting — all members are direct users or roles (preferred)
- [ ] One level of nesting — sub-group: _______________ (review performance impact)
- [ ] Multiple levels of nesting — document and review with platform team before deploying

---

## Sharing Rules Using Public Groups

| Rule Name | Object | Rule Type | Owned By | Share With | Access Level |
|-----------|--------|-----------|----------|------------|--------------|
| [Rule 1]  | Opportunity | Ownership-based | EMEA Sales Team | EMEA Sales Team | Read Only |
| [Rule 2]  | Case | Criteria-based | (field criteria) | Support Managers | Read/Write |

---

## SOQL Validation Queries

Use these queries to verify queue-owned records after configuration.

```soql
-- All open Cases owned by any queue
SELECT Id, CaseNumber, Subject, Owner.Name, CreatedDate
FROM Case
WHERE Owner.Type = 'Queue'
  AND IsClosed = false
ORDER BY CreatedDate ASC

-- Cases owned by a specific queue
SELECT Id, CaseNumber, Subject, CreatedDate
FROM Case
WHERE Owner.Name = 'Tier 1 Support'
  AND Owner.Type = 'Queue'

-- Leads owned by any queue
SELECT Id, LastName, Company, Owner.Name
FROM Lead
WHERE Owner.Type = 'Queue'
  AND IsConverted = false

-- GroupMember records for a given user (for deactivation audit)
SELECT Group.Name, Group.Type
FROM GroupMember
WHERE UserOrGroupId = '<user_id>'
```

---

## Checklist

Run through these before marking configuration complete:

- [ ] All queues are associated with the correct supported objects
- [ ] Queue email is a monitored team alias, not an individual inbox
- [ ] All queue members are active users; deactivated users are not present
- [ ] Public group membership reviewed — correct roles vs. roles+subordinates selected
- [ ] Group nesting depth reviewed — flat preferred for high-volume objects
- [ ] Sharing rules referencing groups have been tested by logging in as a group member
- [ ] SOQL queries for queue-owned records use `Owner.Type = 'Queue'`
- [ ] Reports and dashboards validated for queue-name rows in Owner-grouped views
- [ ] Checker script run: `python3 skills/admin/queues-and-public-groups/scripts/check_queues.py --manifest-dir <path>`

---

## Notes and Deviations

(Record any decisions that deviate from standard patterns documented in SKILL.md, and the reason why.)
