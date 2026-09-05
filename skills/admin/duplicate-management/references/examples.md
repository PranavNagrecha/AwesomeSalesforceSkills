# Examples: Duplicate Management

---

## Example: Blocking Contact Duplicates by Email

**Scenario:** Internal users create Contacts manually, and duplicate Contacts with the same business email cause confusion for sales reps.

**Decision:** Use a blocking duplicate rule on Contact with strong email-based matching.

**Why:** The confidence level is high enough that allowing save would create avoidable cleanup work.

---

## Example: Alerting on Account Name + Domain Similarity

**Scenario:** Account names vary slightly (`Acme Inc.`, `Acme Incorporated`, `Acme, Inc.`) and users sometimes add the same company twice.

**Decision:** Use a fuzzy or composite matching approach with steward review rather than hard blocking all saves.

**Why:** Business-account matching often needs human judgment, especially when subsidiaries or regional entities exist.

**The matching rule:** extends the guide's own `AccountMatchingRule` sample (`Name` compared with `CompanyName`, `BillingCity` with `City`) by adding the website as a second, stronger signal. `booleanFilter` numbers the items in document order, so this reads "fuzzy company name, confirmed by either the website or the city".

```xml
<?xml version="1.0" encoding="UTF-8"?>
<MatchingRules xmlns="http://soap.sforce.com/2006/04/metadata">
    <matchingRules>
        <fullName>Account_Name_And_Domain</fullName>
        <label>Account: fuzzy name confirmed by domain or city</label>
        <description>Catches Acme Inc. / Acme Incorporated / Acme, Inc. without matching every company in one city.</description>
        <booleanFilter>1 AND (2 OR 3)</booleanFilter>
        <matchingRuleItems>
            <blankValueBehavior>NullNotAllowed</blankValueBehavior>
            <fieldName>Name</fieldName>
            <matchingMethod>CompanyName</matchingMethod>
        </matchingRuleItems>
        <matchingRuleItems>
            <blankValueBehavior>NullNotAllowed</blankValueBehavior>
            <fieldName>Website</fieldName>
            <matchingMethod>Exact</matchingMethod>
        </matchingRuleItems>
        <matchingRuleItems>
            <blankValueBehavior>NullNotAllowed</blankValueBehavior>
            <fieldName>BillingCity</fieldName>
            <matchingMethod>City</matchingMethod>
        </matchingRuleItems>
        <ruleStatus>Active</ruleStatus>
    </matchingRules>
</MatchingRules>
```

`CompanyName` and `City` are fuzzy methods from the documented `matchingMethod` enum; there is no fuzzy method for a URL, so the website uses `Exact`. `NullNotAllowed` on `Website` is what stops every Account without a website matching every other one. The duplicate rule that consumes this stays on `actionOnInsert` = `Allow` with `alert` and `report`, which is the "steward review rather than hard blocking" half of the decision — see `references/metadata-examples.md` for the duplicate-rule side.

---

## Example: Merge Governance for Historical Cleanup

**Scenario:** The org already has thousands of duplicate Contacts. The business wants cleanup without losing useful values.

**Approach:**
1. define survivorship rules per field
2. assign a steward queue
3. merge in controlled batches
4. track duplicates found versus duplicates resolved

**Measuring step 4:** the `report` operation writes a `DuplicateRecordSet` per group it finds, and stewards resolve a group by merging and deleting the set. Found-versus-resolved is therefore the gap between what each rule creates and what is left standing.

```sql
-- Found: sets each rule produced over the cleanup window.
SELECT DuplicateRuleId, COUNT(Id) setsCreated
FROM DuplicateRecordSet
WHERE CreatedDate = LAST_N_DAYS:30
GROUP BY DuplicateRuleId

-- Outstanding: the steward's actual backlog, oldest first.
SELECT Id, Name, RecordCount, CreatedDate
FROM DuplicateRecordSet
ORDER BY CreatedDate ASC
LIMIT 50
```

`DuplicateRecordSet` supports `delete()`, and nothing on the platform removes a set once its duplicates are merged — so a backlog that only grows means the rule is producing work faster than the queue absorbs it, which is the signal to retune matching rather than hire another steward.

**Why this works:** It treats merges as governed remediation, not as random record deletion.
