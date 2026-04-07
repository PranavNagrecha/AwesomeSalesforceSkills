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

---

## Anti-Pattern: Using Customer Community License for a PRM Portal

**What practitioners do:** An admin selects Customer Community Plus as the license type when provisioning Experience Cloud users for a channel partner portal because it is less expensive than Partner Community.

**What goes wrong:** The Partner Central Experience Cloud template's deal registration component, lead inbox, and MDF widgets do not render for Customer Community license users. Partners see blank pages or permission errors. The PRM-specific features (deal registration, lead distribution assignment rules, partner-specific dashboards) are gated to Partner Community and Partner Community Plus licenses. Discovering this post-build requires a license swap and re-provisioning of all existing partner users.

**Correct approach:** Use Partner Community license as the baseline. Evaluate whether Partner Community Plus is needed based on the partner user's need for pipeline reports, dashboards, and broader record access. Document the license selection decision in the requirements phase with an explicit note that Customer Community is out of scope.
