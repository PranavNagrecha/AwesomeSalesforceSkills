# Worked Example — Proving the Archive Read Path Before the First Delete

The archive in this example is `Case_Archive__b` with the index `Account__c` (ASC), `Closed_Date__c` (DESC), `Case_Number__c` (ASC), as defined in SKILL.md. The data owner's three audit questions were written down before the index was designed:

| # | Question | Index prefix it uses |
|---|---|---|
| Q1 | All archived cases for one account | `Account__c` |
| Q2 | One account's cases closed in a date range | `Account__c`, `Closed_Date__c` |
| Q3 | One specific case | `Account__c`, `Closed_Date__c`, `Case_Number__c` |

A question such as "all cases closed in March 2019 across every account" does not start with `Account__c`, so this index cannot answer it. That is the moment to change the design, because the index cannot be edited after deployment.

## Step 1: Bounded reads with SOQL (Q1 to Q3)

```apex
Id acct = '001000000000001AAA';
DateTime fromDt = DateTime.newInstanceGmt(2019, 1, 1);
DateTime toDt = DateTime.newInstanceGmt(2019, 12, 31, 23, 59, 59);

List<Case_Archive__b> q1 = [
    SELECT Account__c, Closed_Date__c, Case_Number__c, Subject__c
    FROM Case_Archive__b
    WHERE Account__c = :acct
];
List<Case_Archive__b> q2 = [
    SELECT Account__c, Closed_Date__c, Case_Number__c, Subject__c
    FROM Case_Archive__b
    WHERE Account__c = :acct AND Closed_Date__c >= :fromDt AND Closed_Date__c <= :toDt
];
System.assert(!q1.isEmpty(), 'Archive returned nothing for a sampled account');
```

Filters follow the index order with no gaps: `Account__c` first, then `Closed_Date__c`.

## Step 2: Volume extraction with a Bulk API 2.0 query job

Bulk API 2.0 supports querying big objects (Bulk API guide, "Support for big objects: Ingest, Query").

```bash
curl -X POST "$INSTANCE_URL/services/data/v67.0/jobs/query" \
  -H "Authorization: Bearer $ACCESS_TOKEN" -H "Content-Type: application/json" \
  -d '{"operation":"query","query":"SELECT Account__c, Closed_Date__c, Case_Number__c, Subject__c FROM Case_Archive__b WHERE Account__c = '\''001000000000001AAA'\''"}'
# Poll GET /jobs/query/<jobId> until JobComplete, then GET /jobs/query/<jobId>/results
```

## Step 3: Field history, if it was in scope

If Field Audit Trail is on, history archived from the source is in `FieldHistoryArchive`. The Security guide's example query job:

```json
{
  "operation": "query",
  "query": "SELECT ParentId, FieldHistoryType, Field, Id, NewValue, OldValue FROM FieldHistoryArchive WHERE FieldHistoryType = 'Account' AND CreatedDate > LAST_MONTH"
}
```

## Step 4: Sign-off record

| Check | Result | Evidence |
|---|---|---|
| Q1 row count equals source count for 20 sampled accounts | Pass / Fail | Query output saved with the run |
| Q2 returns only rows in range | Pass / Fail | |
| Bulk API 2.0 job completes and the CSV opens | Pass / Fail | Job Id |
| Field history present for sampled cases (if required) | Pass / Fail / N/A | |
| Data owner approval to enable source deletion | Name, date | |

Only after every row passes does the archive job's delete step get enabled in production.
