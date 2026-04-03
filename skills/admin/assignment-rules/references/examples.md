# Examples — Assignment Rules

## Example 1: Regional Lead Routing to Territory Queues

**Context:** A B2B SaaS company has three regional sales teams: AMER, EMEA, and APAC. All leads from Web-to-Lead forms must route to the correct regional queue based on the lead's country. Leads from partner referrals always go to the AMER Strategic Accounts Queue regardless of country.

**Problem:** Without an assignment rule, every Web-to-Lead record defaults to the org's Default Lead Owner (usually a catch-all system user). The rep team has no visibility into new leads, and response time is suffering.

**Solution:**

1. Create three queues in Setup → Queues: `AMER Sales Queue`, `EMEA Sales Queue`, `APAC Sales Queue`. For each, set Supported Objects to Lead and add the appropriate sales reps as members.
2. Create a fourth queue: `AMER Strategic Accounts Queue` for partner-sourced leads.
3. Navigate to Setup → Lead Assignment Rules → New → name it "Global Lead Routing" → check Active → Save.
4. Add rule entries in this order:

   | Order | Criteria | Assign To |
   |-------|----------|-----------|
   | 1 | Lead Source = Partner Referral | AMER Strategic Accounts Queue |
   | 2 | Country IN (United Kingdom, Germany, France, Netherlands, Spain) | EMEA Sales Queue |
   | 3 | Country IN (Australia, Japan, Singapore, India) | APAC Sales Queue |
   | 4 | (no criteria — catch-all) | AMER Sales Queue |

5. Test by creating a Web-to-Lead submission from a German IP and confirming the record appears in EMEA Sales Queue.

**Why it works:** Rule entries are evaluated top-to-bottom. Partner leads are caught by Entry 1 before the geographic entries apply. The catch-all Entry 4 ensures no lead lands with the API user as owner.

---

## Example 2: Case Priority Routing for a Multi-Tier Support Org

**Context:** A software support org has three case tiers: Tier 1 (general issues), Tier 2 (technical escalations), and a P0 Emergency Queue for production-down cases. Cases come in via Email-to-Case, Web-to-Case, and manual creation. Priority is set to "Critical" for production-down cases.

**Problem:** All cases land in a single support queue. Tier 2 engineers miss production-critical cases mixed among routine requests. SLA compliance is degraded.

**Solution:**

1. Create three queues in Setup: `Tier 1 Support Queue`, `Tier 2 Technical Queue`, `P0 Emergency Queue`. Each queue has its email address configured to notify the team.
2. Navigate to Setup → Case Assignment Rules → New → "Support Case Routing" → Active.
3. Rule entries:

   | Order | Criteria | Assign To |
   |-------|----------|-----------|
   | 1 | Priority = Critical | P0 Emergency Queue |
   | 2 | Priority = High AND Type = Technical Question | Tier 2 Technical Queue |
   | 3 | (no criteria) | Tier 1 Support Queue |

4. Email-to-Case and Web-to-Case run this rule automatically. For manually created cases by internal support agents, confirm "Run assignment rules" is checked.
5. Add an email notification template to the P0 queue entry so the on-call team is immediately alerted.

**Why it works:** Critical cases always reach the P0 queue regardless of origin channel. The catch-all ensures all other cases have a home. Email notifications on the P0 entry trigger page-style alerts to the emergency team.

---

## Example 3: Apex Round-Robin Across a Fixed Rep List

**Context:** A fintech company has six inbound sales reps who should receive leads in equal rotation. A queue is not appropriate because leads must have an individual owner immediately (CRM reporting is built on OwnerId = User). Omni-Channel is not licensed.

**Problem:** Assignment rules can only target one user per entry. Configuring six entries with the same criteria (one per rep) would send all leads to Entry 1's rep, not rotate them.

**Solution:** Use a Custom Setting to store the current rotation index and a comma-separated list of rep user IDs.

```apex
// Custom Setting: Lead_Round_Robin_Config__c (List type)
// Fields: Rep_User_Ids__c (Text 1000), Current_Index__c (Number)

trigger LeadRoundRobin on Lead (before insert) {
    Lead_Round_Robin_Config__c config =
        Lead_Round_Robin_Config__c.getInstance('Default');
    if (config == null || String.isBlank(config.Rep_User_Ids__c)) return;

    List<String> repIds = config.Rep_User_Ids__c.split(',');
    Integer startIdx = config.Current_Index__c != null
        ? (Integer) config.Current_Index__c : 0;
    Integer idx = startIdx;

    for (Lead l : Trigger.new) {
        // Only override if not already assigned to a real user
        if (l.OwnerId == null || l.OwnerId == UserInfo.getUserId()) {
            l.OwnerId = repIds[Math.mod(idx, repIds.size())].trim();
            idx++;
        }
    }

    // Persist updated index via a platform event or queueable to avoid mixed DML
    System.enqueueJob(new UpdateRoundRobinIndex(idx));
}

public class UpdateRoundRobinIndex implements Queueable {
    private Integer newIdx;
    public UpdateRoundRobinIndex(Integer idx) { this.newIdx = idx; }
    public void execute(QueueableContext ctx) {
        Lead_Round_Robin_Config__c config =
            Lead_Round_Robin_Config__c.getInstance('Default');
        config.Current_Index__c = newIdx;
        upsert config;
    }
}
```

Configure the assignment rule to point to a holding user (the "unassigned" sentinel). The trigger overrides the OwnerId before insert, so the assignment rule fires first and the trigger corrects it in the same transaction.

**Why it works:** The trigger runs in the same transaction as insert, so the OwnerId is set before the record is committed. The queueable handles the counter update asynchronously to avoid mixed DML with the Lead insert.

---

## Anti-Pattern: Multiple Active Rules for Different Scenarios

**What practitioners do:** Create separate assignment rules for "Business Hours" and "After Hours" routing, expecting both to be active simultaneously.

**What goes wrong:** Only one assignment rule can be active per object. Activating the After Hours rule immediately deactivates the Business Hours rule. All records then route to after-hours targets around the clock. This is a silent failure — no error is shown when a rule is deactivated.

**Correct approach:** Maintain a single assignment rule with entries that use criteria to detect the scenario (e.g., a custom field "Received After Hours" populated by Flow before the case is created). Alternatively, use Omni-Channel with time-based routing queues for true time-aware distribution.
