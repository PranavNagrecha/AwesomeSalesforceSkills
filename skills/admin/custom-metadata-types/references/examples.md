# Examples - Custom Metadata Types

## Example 1: Deployable Case Routing Rules

**Context:** A support org routes Cases by region and priority. The first implementation hardcodes queue IDs in Apex and uses different values in each sandbox.

**Problem:** Deployments break because queue IDs differ by org. Admins are afraid to touch the routing logic because every environment needs manual code edits or post-deploy fixes.

**Solution:**

Create a `Case_Routing__mdt` type with fields such as `Region__c`, `Priority__c`, `Queue_Developer_Name__c`, `Active__c`, and `Sort_Order__c`.

```apex
public with sharing class CaseRoutingService {
    public static String queueDeveloperNameFor(String region, String priority) {
        for (Case_Routing__mdt rule : [
            SELECT DeveloperName, Region__c, Priority__c, Queue_Developer_Name__c, Active__c
            FROM Case_Routing__mdt
            WHERE Active__c = true
            ORDER BY Sort_Order__c ASC
        ]) {
            if (rule.Region__c == region && rule.Priority__c == priority) {
                return rule.Queue_Developer_Name__c;
            }
        }
        return null;
    }
}
```

In Flow, the same type can be queried with `Get Records` and used in a Decision path instead of copying the routing matrix into multiple flow versions.

**Why it works:** The rules become deployable metadata rather than environment-specific code. Sandboxes and production can promote the same design safely because the lookup uses stable metadata keys.

---

## Example 2: Package Defaults Without Storing Secrets In Metadata

**Context:** A product team ships a managed package that calls an external fraud-check service. The endpoint path and timeout are stable defaults, but the subscriber's credentials are unique per org.

**Problem:** The first draft stores the full URL, username, and API token inside a public CMT so support teams can "see everything in one place."

**Solution:**

Split responsibilities:

- `Fraud_Service_Config__mdt`
  - `Service_Path__c`
  - `Timeout_Millis__c`
  - `Feature_Enabled__c`
- Named Credential `FraudService`
  - base URL
  - auth configuration
  - secret material

```apex
Fraud_Service_Config__mdt config = [
    SELECT Service_Path__c, Timeout_Millis__c, Feature_Enabled__c
    FROM Fraud_Service_Config__mdt
    WHERE DeveloperName = 'Default'
    LIMIT 1
];

HttpRequest req = new HttpRequest();
req.setEndpoint('callout:FraudService' + config.Service_Path__c);
req.setTimeout(Integer.valueOf(config.Timeout_Millis__c));
```

**Why it works:** Deployable behavior stays in metadata, while credentials remain in the supported secret-handling mechanism. The package can ship safe defaults without teaching subscribers to store secrets in metadata.

---

## Anti-Pattern: Using CMT As A User-Maintained Transaction Table

**What practitioners do:** They create a metadata type for data that operations changes throughout the day and expect it to behave like a Custom Object with ad hoc UI maintenance, reporting, and frequent production edits.

**What goes wrong:** Release management and runtime behavior become awkward. The team either bypasses source control to make emergency edits or builds unsupported mutation workflows around something that should have been modeled as data, not metadata.

**Correct approach:** Use CMT for relatively stable configuration that should move with releases. Use Custom Objects when the records are business-owned, reportable, and frequently edited in production.
