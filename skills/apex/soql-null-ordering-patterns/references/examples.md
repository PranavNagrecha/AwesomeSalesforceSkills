# Examples — SOQL NULL Ordering Patterns

## Example 1: ASC sort with explicit NULLS LAST

**Context:** Account list view sorted by `LastActivityDate ASC`. About 30% of accounts have never had activity (null).

**Problem:** Default `ORDER BY LastActivityDate ASC` places null records at the *top* of the list — precisely the accounts the sales team is *least* interested in.

**Solution:**

```apex
List<Account> accounts = [
    SELECT Id, Name, LastActivityDate
    FROM Account
    ORDER BY LastActivityDate ASC NULLS LAST, Id ASC
    LIMIT 200
];
```

**Why it works:** `NULLS LAST` overrides the SOQL default. The `Id ASC` tiebreaker keeps ties (multiple accounts with the same activity date) in a deterministic order across reruns.

---

## Example 2: Cursor-paginated batch over a nullable sort field

**Context:** Nightly batch syncs 200,000 accounts to a warehouse, sorted by `Last_Sync__c DESC`.

**Problem:** OFFSET/LIMIT can't reach beyond 2,000 records, and even within that range, records added during the run skew page boundaries — some accounts are exported twice, some not at all.

**Solution:**

```apex
public class AccountSyncIterator {
    private DateTime cursorTs;
    private Id cursorId;

    public List<Account> nextPage() {
        List<Account> rows;
        if (cursorTs == null) {
            // First page — no WHERE on the cursor
            rows = [
                SELECT Id, Name, Last_Sync__c
                FROM Account
                ORDER BY Last_Sync__c DESC NULLS LAST, Id ASC
                LIMIT 200
            ];
        } else {
            rows = [
                SELECT Id, Name, Last_Sync__c
                FROM Account
                WHERE (Last_Sync__c < :cursorTs
                       OR (Last_Sync__c = :cursorTs AND Id > :cursorId))
                ORDER BY Last_Sync__c DESC NULLS LAST, Id ASC
                LIMIT 200
            ];
        }
        if (!rows.isEmpty()) {
            Account last = rows[rows.size() - 1];
            cursorTs = last.Last_Sync__c;
            cursorId = last.Id;
        }
        return rows;
    }
}
```

**Why it works:** The cursor `(Last_Sync__c, Id)` is stable: even if records are inserted mid-export, every record is visited exactly once. The compound WHERE clause handles the within-tie case (`Last_Sync__c = :cursorTs AND Id > :cursorId`).

The cursor's null transition deserves attention: when crossing from non-null `Last_Sync__c` records into null records, the cursorTs would be null on the next iteration. Either treat null records as a separate final pass, or use a sentinel datetime older than any real record.

---

## Anti-Pattern: relying on default null position for "consistent" ordering

**What practitioners do:**

```apex
ORDER BY Last_Activity_Date__c ASC LIMIT 200
```

**What goes wrong:** Today's run returns null-activity records at the top of the result. Tomorrow's pagination breaks because someone touched a previously-null record. The "missing records" ticket lands on Monday.

**Correct approach:** Always specify NULLS clause and always include a tiebreaker. The query is not slower; it's just correct.

```apex
ORDER BY Last_Activity_Date__c ASC NULLS LAST, Id ASC LIMIT 200
```
