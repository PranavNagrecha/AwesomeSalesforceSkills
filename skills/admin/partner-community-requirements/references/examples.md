# Examples — Partner Community Requirements

## Example 1: Multi-Tier Partner Portal with Deal Registration

**Context:** A mid-market software vendor has three partner tiers (Gold, Silver, Bronze). Gold partners are authorized resellers with a dedicated channel manager. Silver partners have limited reseller rights. Bronze partners are referral-only and do not register deals. The vendor needs a portal where Gold and Silver partners can register deals, claims are reviewed by the channel manager, and approved deals convert to tracked Opportunities.

**Problem:** Without a defined tier hierarchy and approval routing model, the configuration team builds a single approval step for all partners. Gold partners (highest volume) queue behind Silver partners' manual reviews, creating channel conflict and partner dissatisfaction. Additionally, the team discovers mid-build that there is no Lead duplicate rule, so the same prospect is registered twice by two different partners at the same tier.

**Solution:**

Tier-gated deal registration with auto-approval for Gold:

```
Tier Hierarchy:
  Gold  → Deal registration: YES | Auto-approve if Amount < $25,000 | Lead pool: YES
  Silver → Deal registration: YES | Manual approval always           | Lead pool: YES
  Bronze → Deal registration: NO  | Lead pool: NO                   | Co-marketing: YES

Approval Process on Lead (entry criteria: Status = "Submitted for Registration"):
  Step 1: IF Partner_Tier__c = "Gold" AND Amount__c < 25000 → Auto Approve
  Step 2: ALL others → Route to Channel_Manager_Queue

On Approval:
  Flow: Convert Lead to Opportunity, stamp Partner_Account__c on Opportunity

Duplicate Rule on Lead:
  Match on: Company (exact) + Email (exact) OR Company (fuzzy) + Phone (exact)
  Action: Block with alert "A deal for this company is already registered"
```

**Why it works:** The auto-approval threshold eliminates channel manager bottlenecks for routine Gold deals while preserving governance on large or anomalous registrations. The duplicate rule prevents channel conflict before it reaches the approval queue rather than after conversion.

**What the design still has to add:** auto-approval alone does not attribute the deal. `Opportunity.PartnerAccountId` is read-only and derives from the owning partner user, so an auto-approved registration that stays owned by the channel manager converts with an empty partner account. The rule below is what turns "approved" into "attributed", and belongs in the requirements as a numbered step rather than in the build as an implementation detail:

| Registration outcome | Owner immediately after | `PartnerAccountId` on conversion | Design action required |
|---|---|---|---|
| Gold, auto-approved under $25K | Submitting partner user | Populated | None — the submitter already owns it |
| Silver, manually approved | Channel manager (the approver) | **Empty** | Transfer ownership to the accepting partner user before conversion |
| Sourced by Acme, offered to a partner | Acme AE | **Empty** | Transfer on acceptance; the partner must own it to be credited |
| Rejected, resubmitted, then approved | Submitting partner user | Populated | None |

Two of those four rows lose attribution without an explicit transfer step, which is why the design artefact in `references/worked-examples.md` §3 requires a step of `type: acceptance` before it will pass the checker.

---

## Example 2: Push Lead Distribution Model for Regional Partners

**Context:** A hardware distributor has 40 partners across four US regions. Partners are either Gold (receive leads automatically) or Silver (access a shared regional pool). Inbound leads come from web-to-lead and marketing automation. The business wants high-quality leads routed to Gold partners automatically; Silver partners can claim remaining leads from their regional pool.

**Problem:** The initial design assigns leads directly to partner user records. When a partner user is on leave or their Salesforce seat is deactivated, leads pile up in an inaccessible queue and are not reassigned. The team also discovers that Silver partner users can see leads outside their region because the list view filter is on lead source, not partner territory.

**Solution:**

Queue-based push for Gold, regional pool pull for Silver:

```
Queue Structure:
  Gold_West_Queue   (members: Gold partners, West territory)
  Gold_East_Queue   (members: Gold partners, East territory)
  Gold_Central_Queue
  Gold_South_Queue
  Silver_West_Pool
  Silver_East_Pool
  Silver_Central_Pool
  Silver_South_Pool

Lead Assignment Rules (evaluated in order):
  1. IF Partner_Tier__c = "Gold" AND Lead.State IN (West states)   → Gold_West_Queue
  2. IF Partner_Tier__c = "Gold" AND Lead.State IN (East states)   → Gold_East_Queue
  ... (repeat per region/tier)
  5. IF Lead.State IN (West states)  → Silver_West_Pool
  6. IF Lead.State IN (East states)  → Silver_East_Pool
  ... (repeat per region)
  Default: → Unassigned_Channel_Lead_Queue (for channel manager review)

Portal List View for Silver partners:
  Filter: Owner = {partner's regional pool queue}  (not a profile filter)
  Sharing: Public group per Silver regional tier → Read/Write on pool leads
```

**Why it works:** Queue-based assignment decouples the lead from individual user availability. Gold partners see their assigned leads immediately via queue-scoped list views. Silver partners see only their regional pool via sharing rules scoped to a regional public group — not a broad profile filter. Orphaned leads fall to the channel manager queue rather than disappearing.

**One caveat the queue design must absorb:** a sharing set cannot carry Lead. The Metadata API Guide's `SharingSet` `AccessMapping.object` list is Account, Campaign, Contact, Case, custom objects, Opportunity, Order, ServiceContract, User and WorkOrder. Lead visibility for the Silver pool therefore has to come from queue membership, a sharing rule shared to a portal role group, or `AccountRelationshipShareRule` — never from a sharing set, however naturally the requirement is phrased.

These two queries are the ones to run in the sandbox after the queues are built. The first proves distribution is landing where the rules say; the second proves the pool has not silently become invisible:

```sql
-- Where are partner-eligible leads actually sitting, and which are stuck unowned by a partner?
SELECT Owner.Name, Owner.Type, Status, COUNT(Id) leads
FROM   Lead
WHERE  IsConverted = false
AND    CreatedDate = LAST_N_DAYS:30
GROUP BY Owner.Name, Owner.Type, Status
ORDER BY COUNT(Id) DESC

-- Queue-owned leads with no active partner user in the queue: a pool nobody can claim.
SELECT Id, Company, State, OwnerId, Owner.Name
FROM   Lead
WHERE  IsConverted = false
AND    Owner.Type = 'Queue'
AND    OwnerId NOT IN (
         SELECT Queue.Id FROM QueueSobject WHERE SobjectType = 'Lead'
       )
```

The second query is deliberately conservative — it finds leads owned by something that is not a Lead-enabled queue at all, which is the failure that produces a permanently unreachable pool. Membership emptiness itself is checked in Setup, since `Group` and `GroupMember` do not expose partner queue membership in a single query.

---

## Anti-Pattern: Using Customer Community License for a PRM Portal

**What practitioners do:** An admin selects Customer Community Plus as the license type when provisioning Experience Cloud users for a channel partner portal because it is less expensive than Partner Community.

**What goes wrong:** The Partner Central Experience Cloud template's deal registration component, lead inbox, and MDF widgets do not render for Customer Community license users. Partners see blank pages or permission errors. The PRM-specific features (deal registration, lead distribution assignment rules, partner-specific dashboards) are gated to Partner Community and Partner Community Plus licenses. Discovering this post-build requires a license swap and re-provisioning of all existing partner users.

**Correct approach:** Use Partner Community license as the baseline. Evaluate whether Partner Community Plus is needed based on the partner user's need for pipeline reports, dashboards, and broader record access. Document the license selection decision in the requirements phase with an explicit note that Customer Community is out of scope.
