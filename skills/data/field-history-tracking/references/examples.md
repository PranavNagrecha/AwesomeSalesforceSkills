# Examples — Field History Tracking

## Example 1: Querying Who Changed Opportunity Stage and When

**Context:** A sales operations manager needs to audit which sales reps changed `StageName` on Opportunities during the previous quarter. The org has had Field History Tracking enabled on `StageName` for over a year.

**Problem:** The manager wants to produce a list of all stage changes during Q1 2025, including the previous stage value, the new stage value, the user who made the change, and the timestamp — but the built-in Opportunity History report type only shows up to 2,000 rows and lacks the field-level filtering the manager needs.

**Solution:**

Run a bounded SOQL query directly against `OpportunityFieldHistory` (the Opportunity *field*-history sObject — **not** `OpportunityHistory`, which is the separate stage-history object and has no `Field` column):

```soql
SELECT OpportunityId, OldValue, NewValue, CreatedById, CreatedDate
FROM OpportunityFieldHistory
WHERE Field = 'StageName'
  AND CreatedDate >= 2025-01-01T00:00:00Z
  AND CreatedDate <= 2025-03-31T23:59:59Z
ORDER BY CreatedDate ASC
```

To join user names, wrap in Apex or use a relationship query:

```soql
SELECT OpportunityId, OldValue, NewValue, CreatedBy.Name, CreatedBy.Username, CreatedDate
FROM OpportunityFieldHistory
WHERE Field = 'StageName'
  AND CreatedDate >= 2025-01-01T00:00:00Z
  AND CreatedDate <= 2025-03-31T23:59:59Z
ORDER BY CreatedDate ASC
LIMIT 10000
```

Export results via Data Loader or Workbench for analysis in Excel or BI tools.

**Why it works:** `OpportunityFieldHistory` stores one row per tracked field change. Filtering on `Field = 'StageName'` isolates only stage transitions. `CreatedBy.Name` provides the user's full name via a relationship traversal. The `CreatedDate` bounds scope the result to the desired quarter and avoid full-table scans.

---

## Example 2: Diagnosing Missing Field History on a Custom Object

**Context:** A compliance team reports that changes to the `Approval_Status__c` field on a custom object `Contract__c` are not appearing in the History related list, even though a user visibly changed the value last week.

**Problem:** The team enabled history tracking on `Contract__c` six months ago but cannot see the change made last week. SOQL against `Contract__History` returns no rows for the expected change.

**Solution:**

Work through the troubleshooting checklist in sequence:

1. Confirm history is still enabled on the object:

```bash
# Check metadata for the object
sfdx force:source:retrieve -m "CustomObject:Contract__c" && grep -i "enableHistory" force-app/main/default/objects/Contract__c/Contract__c.object-meta.xml
```

Expected output: `<enableHistory>true</enableHistory>`

2. Confirm `Approval_Status__c` is selected for tracking:

```bash
grep -i "trackHistory" force-app/main/default/objects/Contract__c/fields/Approval_Status__c.field-meta.xml
```

Expected output: `<trackHistory>true</trackHistory>`

3. If both are confirmed, check field type — if `Approval_Status__c` is a formula field or roll-up summary, it cannot be tracked. Check the field metadata for `<type>`:

```bash
grep -i "<type>" force-app/main/default/objects/Contract__c/fields/Approval_Status__c.field-meta.xml
```

4. If the field type is eligible and history is enabled, run a SOQL probe:

```soql
SELECT Id, Field, OldValue, NewValue, CreatedById, CreatedDate
FROM Contract__History
WHERE ParentId = 'a01XXXXXXXXXXXX'
ORDER BY CreatedDate DESC
LIMIT 50
```

5. If no rows are returned for the expected change date, verify the change was made via the UI or API — history tracking does not capture changes made directly via Data Loader in `--no-trigger` mode or via certain metadata-level bulk operations.

**Why it works:** Metadata retrieval confirms whether `trackHistory` is set at the field level, which is the most common root cause of missing history. The SOQL probe confirms whether rows exist at all for the record. Separating object-level enablement from field-level selection is critical — both must be true for history to be captured.

---

## Example 3: One Query for a Record and Its Full Change Log

**Context:** A developer building an LWC change-log panel for `Project__c` needs, for a single project, the record's name and status alongside every tracked change — without issuing two separate queries (one for the record, one for `Project__History`).

**Problem:** The naive approach runs `SELECT Name, Status__c FROM Project__c WHERE Id = :id` and then a second `SELECT OldValue, NewValue FROM Project__History WHERE ParentId = :id`. That is two SOQL statements, two governor-limit hits, and manual stitching of the results in Apex.

**Solution:**

A history object is the child of its tracked parent, so a single parent-to-child query returns both — the record fields plus its history rows nested as a subquery:

```soql
SELECT Name, Status__c,
       (SELECT Field, OldValue, NewValue, CreatedBy.Name, CreatedDate
        FROM Project__History
        ORDER BY CreatedDate DESC)
FROM Project__c
WHERE Id = 'a01XXXXXXXXXXXX'
```

**Why it works:** Salesforce auto-generates the parent-child relationship between an object and its `__History` sObject when tracking is enabled. The subquery names the history object directly, collapsing two round-trips into one and keeping each change row grouped with the record it describes. To go the other way — from a change up to parent context — use the child-to-parent form in Concept 2, noting the relationship name is `Parent` on custom history but the object name (`Account`) on standard history (Gotcha 5). Neither form works against Shield's `FieldHistoryArchive` (Gotcha 6).

---

## Anti-Pattern: Relying on Field History Tracking for Long-Term Compliance Audit

**What practitioners do:** An admin enables Field History Tracking on `AnnualRevenue` on Account to satisfy a compliance requirement that financial field changes be retained for 5 years. The admin marks the task complete and informs the compliance team that audit history is captured.

**What goes wrong:** Salesforce automatically purges Field History records older than 18 months on a rolling basis. After 18 months, all history rows for `AnnualRevenue` changes that occurred before the rolling window are silently deleted. When auditors request a 5-year history record three years later, the data no longer exists. This is not a bug — it is documented platform behavior. The compliance gap creates regulatory exposure.

**Correct approach:** For retention requirements exceeding 18 months, use Shield Field Audit Trail (see `field-audit-trail` skill). Alternatively, implement a custom logging pattern at write time using an Apex before-update trigger that writes changes into a custom `FieldChangeLog__c` object. This custom log is not subject to the platform retention purge and can be retained indefinitely. Document which approach is in use and communicate the limitation proactively during requirements gathering — not after a compliance incident.
