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

---

## Example 3: The Rows Behind Example 2

**Context:** Example 2 resolves a routing rule in Apex. The rules themselves are files, and reviewers keep asking "what does a row actually look like?"

**Problem:** A `__mdt` type with no deployed records reads as configurable and behaves as broken — `getInstance()` returns null and `getAll()` returns an empty map (Apex Reference Guide L204569, L204588).

**Solution:** ship the rows as source, in `customMetadata/`, one file per rule.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomMetadata xmlns="http://soap.sforce.com/2006/04/metadata"
                xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                xmlns:xsd="http://www.w3.org/2001/XMLSchema">
    <label>Web DE High</label>
    <protected>false</protected>
    <values>
        <field>Channel__c</field>
        <value xsi:type="xsd:string">Web</value>
    </values>
    <values>
        <field>Country__c</field>
        <value xsi:type="xsd:string">DE</value>
    </values>
    <values>
        <field>Priority__c</field>
        <value xsi:type="xsd:int">10</value>
    </values>
    <values>
        <field>Queue_Developer_Name__c</field>
        <value xsi:type="xsd:string">DACH_Inbound</value>
    </values>
</CustomMetadata>
```

Saved as `force-app/main/default/customMetadata/Lead_Routing_Rule.Web_DE_High.md-meta.xml` — the record name is `<TypeNameWithoutMdt>.<DeveloperName>` and the file suffix is `.md` in Metadata API format (Metadata API Developer Guide L41456–41459). The `xsi:type` per field type comes from the guide's own table (L41716–41749).

**Why it works:** the rule is reviewable in a pull request, promotes through environments with the code that reads it, and cannot drift between sandbox and production without someone deploying a file.

**Verification.** After deploying, confirm the resolution order Apex will actually see:

```soql
SELECT DeveloperName, Channel__c, Country__c, Priority__c, Queue_Developer_Name__c
FROM Lead_Routing_Rule__mdt
WHERE Channel__c = 'Web'
ORDER BY Priority__c ASC, DeveloperName ASC
```

Two rows sharing a `Priority__c` for the same `Channel__c` + `Country__c` is the silent
defect this query exists to surface: Apex will pick one of them, deterministically but
arbitrarily, and the routing looks correct until someone adds a third row.
