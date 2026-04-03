# Examples - Custom Metadata In Apex

## Example 1: Centralized Feature Flag Reader

**Context:** A service must decide whether invoice retry logic is enabled for a business unit.

**Problem:** Raw `SELECT ... FROM Retry_Rule__mdt` queries are duplicated across several classes.

**Solution:**

```apex
public inherited sharing class RetryRuleConfig {
    public static Boolean isEnabled(String businessUnit) {
        Retry_Rule__mdt ruleRecord = Retry_Rule__mdt.getInstance(businessUnit);
        return ruleRecord != null && ruleRecord.Enabled__c;
    }
}
```

**Why it works:** The rest of the code depends on a small semantic API instead of repeated metadata queries and field names.

---

## Example 2: Strategy Table In Custom Metadata

**Context:** Lead routing depends on channel, country, and priority threshold.

**Problem:** Hardcoded branching in Apex keeps growing.

**Solution:**

```apex
List<Lead_Routing_Rule__mdt> rules = [
    SELECT DeveloperName, Channel__c, Country__c, Queue_Developer_Name__c, Priority__c
    FROM Lead_Routing_Rule__mdt
    WHERE Channel__c = :channel
];
```

Resolve the winning rule in Apex and hand back a queue developer name or handler key.

**Why it works:** Metadata owns variability while Apex owns resolution and enforcement.

---

## Anti-Pattern: Runtime DML Mental Model

**What practitioners do:** They design business services as if `insert My_Config__mdt` were normal runtime persistence.

**What goes wrong:** The write model conflicts with how metadata actually moves and is governed.

**Correct approach:** Keep runtime services read oriented and isolate metadata creation or update behind a deployment boundary.
