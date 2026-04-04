# Examples — Queues and Public Groups

## Example 1: Tier 1 and Tier 2 Support Queues with Escalation Flow

**Context:** A B2B SaaS company has a support team with two tiers. Tier 1 handles all incoming cases first. Cases unresolved after 4 hours escalate to Tier 2 specialists. Work should be visible to the whole tier at once, not locked to individual agents.

**Problem:** Without queues, cases are assigned to individual agents. If an agent is unavailable, their cases stagnate. There is no shared pool for the team to pick from. Escalation has no formal mechanism — it relies on agents manually reassigning cases.

**Solution:**

Step 1 — Create Tier 1 and Tier 2 queues in Setup:

```
Setup → Queues → New

Queue 1:
  Label: Tier 1 Support
  Queue Email: support-tier1@company.com
  Supported Objects: Case
  Members: Role "Tier 1 Support Agents" (or Roles and Subordinates if there are sub-teams)

Queue 2:
  Label: Tier 2 Support
  Queue Email: support-tier2@company.com
  Supported Objects: Case
  Members: Role "Tier 2 Specialists"
```

Step 2 — Route new cases to Tier 1 via Case Assignment Rule:

```
Setup → Case Assignment Rules → New (or edit active rule)
Rule Entry 1 (catch-all, last entry): Assign to "Tier 1 Support" queue
```

Step 3 — Escalate to Tier 2 via a Flow (Record-Triggered, scheduled path):

```
Object: Case
Trigger: Record created or updated
Scheduled path: 4 hours after Case.CreatedDate
Condition: Owner is Tier 1 Support (OwnerId = [Tier 1 Queue Id]) AND Status != 'Closed'
Action: Update Record — set OwnerId = [Tier 2 Queue Id]
```

Step 4 — SOQL to audit escalated cases still in Tier 2:

```soql
SELECT Id, CaseNumber, Subject, CreatedDate, Owner.Name
FROM Case
WHERE Owner.Name = 'Tier 2 Support'
  AND Status != 'Closed'
ORDER BY CreatedDate ASC
```

**Why it works:** Queue ownership keeps work visible to the whole tier. Any available agent claims a case by changing the Owner to themselves. The scheduled Flow path handles escalation declaratively without custom code. The `Owner.Name` SOQL filter targets the queue specifically rather than relying on `OwnerId`, which would require the queue's record ID.

---

## Example 2: EMEA Sales Team Public Group for Opportunity Sharing Rule

**Context:** A global sales org has org-wide default Private for Opportunity. EMEA sales reps need read access to each other's Opportunities for account planning and deal coordination, but must not see opportunities owned by APAC or Americas reps. The EMEA team is defined by a Salesforce Role.

**Problem:** Role hierarchy grants upward visibility (EMEA managers see their reps' records), but reps at the same level cannot see each other's Opportunities. Changing OWD to Public Read Only would expose all Opportunities globally. Assignment rules do not help — they control ownership, not read access.

**Solution:**

Step 1 — Create the public group:

```
Setup → Public Groups → New
  Label: EMEA Sales Team
  Members: Add Role "EMEA Account Executive"
            Add Role "EMEA Sales Development"
            (Use "Roles and Subordinates" if sub-roles exist under these)
```

Step 2 — Create an Opportunity sharing rule:

```
Setup → Sharing Settings → Opportunity Sharing Rules → New
  Rule Name: EMEA Peer Sharing
  Rule Type: Based on record owner
  "Owned by members of": Public Group — EMEA Sales Team
  "Share with": Public Group — EMEA Sales Team
  Opportunity Access: Read Only
```

Step 3 — Verify sharing:

```
Setup → User → [Pick an EMEA rep] → View Sharing → Opportunity
Confirm they have read access to another EMEA rep's Opportunity record
```

Step 4 — SOQL to confirm EMEA-owned opportunities (for admin audit):

```soql
SELECT Id, Name, Owner.Name, Owner.UserRole.Name
FROM Opportunity
WHERE Owner.UserRole.Name IN ('EMEA Account Executive', 'EMEA Sales Development')
  AND IsClosed = false
ORDER BY Owner.Name
```

**Why it works:** The public group aggregates EMEA members by Role, so when a new rep joins and is assigned the EMEA role, they automatically inherit the sharing rule access without any manual group maintenance. The ownership-based sharing rule grants horizontal peer access — something the role hierarchy alone cannot provide.

---

## Anti-Pattern: Using a Queue to Share Read Access on Opportunity

**What practitioners do:** An admin wants EMEA reps to see each other's Opportunities. They create a queue for Opportunity and add EMEA reps as members, thinking queue membership grants access.

**What goes wrong:** Opportunity does not support queue ownership — Salesforce does not allow queue members to receive Opportunity records via queue ownership. Even if the queue is created successfully (it may appear to save), assigning an Opportunity to a queue is not a supported operation. The intended sharing access never materializes.

**Correct approach:** Create a public group for EMEA reps and configure an Opportunity sharing rule that targets the group. Queues route work through record ownership; public groups share access through sharing rules. These mechanisms are distinct and not interchangeable for unsupported objects.
