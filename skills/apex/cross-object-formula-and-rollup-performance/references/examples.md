# Examples — Cross-Object Formula and Rollup Performance

## Example 1: Spanning Relationship Audit via Tooling API

**Context:** A developer tries to add a cross-object formula field on the Opportunity object but receives "Maximum 15 object references in one object" at save time. The team does not know which formulas consume the existing references.

**Problem:** Without an inventory, the team guesses which formula to remove, sometimes breaking dependent reports or validation rules.

**Solution:**

```bash
# Query all formula fields on Opportunity via Tooling API
sf data query --query "SELECT DeveloperName, Formula FROM CustomField WHERE TableEnumOrId = 'Opportunity' AND Formula != null" --use-tooling-api --json | \
  jq -r '.result.records[] | "\(.DeveloperName): \(.Formula)"'
```

Then parse each formula for unique relationship hops:

```python
import re

def extract_spanning(formula: str) -> set[str]:
    """Return unique relationship names from cross-object refs."""
    refs = re.findall(r'([A-Z]\w+(?:__r)?)\.\w+', formula)
    return set(refs)

# Example: "Account.Owner.Profile.Name" -> {'Account', 'Owner', 'Profile'}
```

**Why it works:** The Tooling API returns the raw formula text, allowing automated counting. Each unique relationship name (not each field reference) counts toward the 15-reference limit.

---

## Example 2: Deferred Rollup Read with Queueable

**Context:** An after-update trigger on OpportunityLineItem needs to check whether the parent Opportunity's rollup field `Total_Revenue__c` has crossed a threshold and then create a Task for the owner.

**Problem:** Reading `Total_Revenue__c` inside the trigger returns the pre-recalculation value because rollups fire at step 13, after all triggers complete.

**Solution:**

```apex
// In OpportunityLineItemTriggerHandler
public static void afterUpdate(List<OpportunityLineItem> newItems) {
    Set<Id> oppIds = new Set<Id>();
    for (OpportunityLineItem oli : newItems) {
        oppIds.add(oli.OpportunityId);
    }
    // Do NOT query Opportunity.Total_Revenue__c here — it is stale.
    System.enqueueJob(new RevenueThresholdCheck(oppIds));
}

public class RevenueThresholdCheck implements Queueable {
    private Set<Id> oppIds;
    public RevenueThresholdCheck(Set<Id> oppIds) {
        this.oppIds = oppIds;
    }
    public void execute(QueueableContext ctx) {
        List<Opportunity> opps = [
            SELECT Id, OwnerId, Total_Revenue__c
            FROM Opportunity
            WHERE Id IN :oppIds AND Total_Revenue__c > 1000000
        ];
        List<Task> tasks = new List<Task>();
        for (Opportunity o : opps) {
            tasks.add(new Task(
                WhatId = o.Id,
                OwnerId = o.OwnerId,
                Subject = 'Revenue milestone reached',
                Status = 'Open',
                Priority = 'High'
            ));
        }
        if (!tasks.isEmpty()) insert tasks;
    }
}
```

**Why it works:** The Queueable runs in a separate transaction, after the platform has committed the rollup recalculation. The SOQL query inside the Queueable returns the correct, updated value.

---

## Example 3: Incremental Apex Rollup Replacing Native Rollup on LDV Object

**Context:** A custom object `Sensor_Reading__c` has 500k+ records per parent `Device__c`. The native rollup `Avg_Temperature__c` on `Device__c` times out with REQUEST_RUNNING_TOO_LONG because the rollup filter excludes readings where `Status__c != 'Valid'` and `Status__c` is not indexed.

**Solution:**

```apex
public class SensorReadingRollupHandler {
    public static void handleAfterInsert(List<Sensor_Reading__c> newReadings) {
        Map<Id, List<Sensor_Reading__c>> byDevice = new Map<Id, List<Sensor_Reading__c>>();
        for (Sensor_Reading__c r : newReadings) {
            if (r.Status__c != 'Valid') continue; // Apply filter in code
            if (!byDevice.containsKey(r.Device__c))
                byDevice.put(r.Device__c, new List<Sensor_Reading__c>());
            byDevice.get(r.Device__c).add(r);
        }
        if (byDevice.isEmpty()) return;

        List<Device__c> devices = [
            SELECT Id, Reading_Count__c, Reading_Sum__c
            FROM Device__c
            WHERE Id IN :byDevice.keySet()
            FOR UPDATE
        ];
        for (Device__c d : devices) {
            List<Sensor_Reading__c> readings = byDevice.get(d.Id);
            Decimal count = d.Reading_Count__c == null ? 0 : d.Reading_Count__c;
            Decimal total = d.Reading_Sum__c == null ? 0 : d.Reading_Sum__c;
            for (Sensor_Reading__c r : readings) {
                count++;
                total += r.Temperature__c;
            }
            d.Reading_Count__c = count;
            d.Reading_Sum__c = total;
            // Avg computed via formula: Reading_Sum__c / Reading_Count__c
        }
        update devices;
    }
}
```

**Why it works:** The Apex trigger performs an incremental delta update rather than a full recalculation. It only processes the newly inserted records, avoiding the full scan of 500k children. The FOR UPDATE clause prevents concurrent inserts from creating inconsistent totals.

---

## Anti-Pattern: Reading Rollup in Same-Transaction Trigger

**What practitioners do:** Write an after-update trigger on the child that queries the parent rollup field and branches logic based on the value.

**What goes wrong:** The rollup has not recalculated yet (step 13 has not run). The trigger reads the previous value and makes incorrect decisions — such as skipping a threshold notification or applying the wrong discount tier.

**Correct approach:** Enqueue a Queueable or publish a Platform Event from the trigger. Handle the rollup-dependent logic in the asynchronous handler where the recalculated value is available.
