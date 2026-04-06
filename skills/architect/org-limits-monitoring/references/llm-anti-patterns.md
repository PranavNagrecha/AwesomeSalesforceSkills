# LLM Anti-Patterns -- Org Limits Monitoring

Common mistakes AI coding assistants make when generating or advising on org-level limit monitoring in Salesforce.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Using the REST Limits Endpoint From Scheduled Apex Without Acknowledging API Cost

**What the LLM generates:** A Scheduled Apex class that makes an HTTP callout to `GET /services/data/vXX.0/limits` every hour to check org limits, without mentioning that this consumes an API call or offering the zero-cost `OrgLimits.getAll()` alternative.

**Why it happens:** Training data includes many REST API examples for limit checking. The LLM defaults to the REST pattern because it appears more frequently in documentation and blog posts than the Apex-native `OrgLimits` class.

**Correct pattern:**

```apex
// Use OrgLimits.getAll() for zero API cost monitoring
Map<String, System.OrgLimit> limitsMap = OrgLimits.getAll();
System.OrgLimit apiLimit = limitsMap.get('DailyApiRequests');
Integer consumed = apiLimit.getValue();
Integer total = apiLimit.getLimit();
Decimal pctUsed = (Decimal.valueOf(consumed) / Decimal.valueOf(total)) * 100;
```

**Detection hint:** Look for `HttpRequest` or `/services/data/` in a Scheduled Apex monitoring class. If the class is checking limits that are available via `OrgLimits.getAll()`, it should use the Apex-native approach instead.

---

## Anti-Pattern 2: Hard-Coding Threshold Values in Apex

**What the LLM generates:** Threshold checks with magic numbers directly in the Apex class:

```apex
if (pctUsed > 80) {
    sendAlert('WARNING: API usage at ' + pctUsed + '%');
}
```

**Why it happens:** LLMs favor concise, self-contained code snippets. Adding Custom Metadata configuration adds complexity that the model avoids in short-form answers.

**Correct pattern:**

```apex
// Read thresholds from Custom Metadata
Limit_Monitor_Config__mdt config = Limit_Monitor_Config__mdt.getInstance('DailyApiRequests');
if (pctUsed >= config.Critical_Threshold__c) {
    sendAlert('CRITICAL', limitName, pctUsed);
} else if (pctUsed >= config.Warning_Threshold__c) {
    sendAlert('WARNING', limitName, pctUsed);
}
```

**Detection hint:** Search for numeric literals (70, 75, 80, 85, 90) used in comparison operators inside a limit monitoring class. These should be replaced with configurable metadata values.

---

## Anti-Pattern 3: Assuming OrgLimits.getAll() Returns All Limits

**What the LLM generates:** Code that calls `OrgLimits.getAll()` and assumes the returned map contains every limit available through the REST Limits resource, then fails silently when a limit key like `DailyBulkV2QueryJobs` returns null.

**Why it happens:** The LLM conflates the two monitoring surfaces. Documentation for the REST Limits resource is more extensive, and the model projects that coverage onto the Apex class.

**Correct pattern:**

```apex
Map<String, System.OrgLimit> limitsMap = OrgLimits.getAll();
System.OrgLimit lim = limitsMap.get('DailyBulkV2QueryJobs');
if (lim != null) {
    // Process the limit
} else {
    // This limit is not available via OrgLimits — use REST /limits instead
    System.debug('Limit DailyBulkV2QueryJobs not available via OrgLimits.getAll()');
}
```

**Detection hint:** Look for `.get('LimitName')` calls on the OrgLimits map that are not followed by a null check. Every limit key access should handle the case where the key is not present.

---

## Anti-Pattern 4: Generating Platform Event Monitoring Without Addressing Silent Drops

**What the LLM generates:** A monitoring solution for `HourlyPublishedPlatformEvents` that only checks the consumption percentage, without mentioning that events published beyond the limit are silently dropped (no exception thrown, no error logged).

**Why it happens:** Most governor limit violations throw exceptions, so the LLM assumes the same failure behavior for platform event limits. The silent-drop behavior is a Salesforce-specific nuance not well-represented in general training data.

**Correct pattern:**

```
Monitoring alone is insufficient for platform event limits.
In addition to threshold-based alerting on HourlyPublishedPlatformEvents:
1. Implement subscriber-side reconciliation to detect dropped events.
2. Design event publishers to check EventBus.publish() SaveResult for errors.
3. Consider event replay (ReplayId) for subscribers to recover from gaps.
```

**Detection hint:** If the monitoring solution mentions `HourlyPublishedPlatformEvents` but does not mention "silent drop," "reconciliation," or "replay," the guidance is incomplete.

---

## Anti-Pattern 5: Recommending a Separate Scheduled Job Per Limit Category

**What the LLM generates:** Multiple Scheduled Apex classes -- one for API limits, one for storage limits, one for event limits -- each scheduled independently.

**Why it happens:** LLMs favor separation of concerns and generate modular, single-responsibility classes. In most frameworks this is correct, but Salesforce has a hard cap of 100 scheduled Apex jobs per org.

**Correct pattern:**

```apex
// Single monitoring job handles all limit categories
global class OrgLimitMonitorJob implements Schedulable {
    global void execute(SchedulableContext sc) {
        Map<String, System.OrgLimit> limits = OrgLimits.getAll();
        List<Limit_Monitor_Config__mdt> configs =
            Limit_Monitor_Config__mdt.getAll().values();
        for (Limit_Monitor_Config__mdt config : configs) {
            if (!config.Enabled__c) continue;
            System.OrgLimit lim = limits.get(config.Limit_Name__c);
            if (lim == null) continue;
            evaluateAndAlert(config, lim);
        }
    }
}
```

**Detection hint:** Multiple classes implementing `Schedulable` in the same monitoring solution, or multiple `System.schedule()` calls for different limit categories.

---

## Anti-Pattern 6: Computing Percentage With Integer Division

**What the LLM generates:**

```apex
Integer pctUsed = (consumed / total) * 100; // Always returns 0 when consumed < total
```

**Why it happens:** Integer division truncation is a common bug in Apex that LLMs reproduce from training data. When `consumed` is less than `total`, the integer division `consumed / total` evaluates to 0 before the multiplication by 100.

**Correct pattern:**

```apex
Decimal pctUsed = (Decimal.valueOf(consumed) / Decimal.valueOf(total)) * 100;
```

**Detection hint:** Look for `Integer` type on the percentage variable, or division of two Integer values without a cast to `Decimal` first.
