# Examples — Flow Cross-Object Updates

Two worked scenarios and one anti-pattern showing how to write
cross-object DML in Flow without burning SOQL/DML governor budget
under bulk load. Examples are written as Flow-element pseudocode
(Flow doesn't export to a hand-readable text format; the structure
here matches what you'd build in Flow Builder).

---

## Example 1: Stamp "Last Contact Made" date on parent Account from Contact insert

**Context:** Sales ops wants the Account record page to show "Last
Contact Made" — the most recent CreatedDate across all related
Contacts. When a Contact is created or its `LastContactDate__c` field
is updated, the parent Account should reflect the latest value.
Data Loader runs can create up to 200 Contacts per batch.

**Problem:** A naive implementation does a Get Records (Contact)
inside a loop or issues an Update Records per Contact. With 200
records in the batch, that's 200 SOQL or 200 DML — well past
the per-transaction governor limits for a Flow.

**Solution:** Single Update Records, no loop, no Get Records
needed.

```
Flow: Account_Last_Contact_Stamp
  Type: Record-Triggered Flow
  Object: Contact
  Trigger: A record is created or updated
  Condition Requirements:
    - $Record.AccountId IS NOT NULL
    - ISNEW() OR ISCHANGED({!$Record.LastContactDate__c})
  Optimize for: Actions and Related Records (after-save)

Decision: Use_Created_Or_Modified_Date
  When: ISNEW()  → Outcome A (use CreatedDate)
  When: ELSE     → Outcome B (use LastContactDate__c)

[Outcome A]
  Update Records: Account_Last_Contact
    Object: Account
    Filter: Id = {!$Record.AccountId}
    Fields:
      Last_Contact_Made__c = {!$Record.CreatedDate}

[Outcome B]
  Update Records: Account_Last_Contact_B
    Object: Account
    Filter: Id = {!$Record.AccountId}
    Fields:
      Last_Contact_Made__c = {!$Record.LastContactDate__c}
```

**Why it works:** Flow bulkifies the Update Records element
automatically — when 200 Contacts arrive in a single batch, the
Flow engine collapses the 200 individual update operations into
a single underlying DML (Salesforce groups by target object +
filter pattern). The result: 1 DML for the whole batch, regardless
of batch size. The two outcomes share the same target field but
read from different source fields because ISNEW() and ISCHANGED()
have different semantics on insert vs update.

The `Optimize for: Actions and Related Records` setting matters —
the alternative ("Fast Field Updates") doesn't support cross-object
DML at all. If the field were on the *current* record, you'd flip
to Fast Field Updates for the perf win, but cross-object writes
force the slower mode.

---

## Example 2: Cascade Account status change to all related Contacts

**Context:** When a sales rep changes Account `Status__c` to
"Inactive", all Contacts on that Account should have their
`MailingOptOut__c` field set to TRUE so they stop receiving
marketing emails. A Mass Email tool runs daily — getting this
wrong sends marketing to "inactive" accounts.

**Problem:** Practitioners build the cascade with an Update
Records *inside* a Loop. The first time someone bulk-updates 200
Accounts (e.g., a quarterly cleanup) the transaction dies and
fails for ALL 200 Accounts, including the ones that "almost
succeeded" before the rollback.

**Which limit, exactly.** An Update inside a Loop spends **DML
statements**, and the synchronous ceiling is 150 per transaction
(`apexdev.txt` L19550) — so an average of one child per Account
is already enough to blow it at the 151st write. A *Get Records*
inside a loop is the one that spends SOQL, ceiling 100
(L19542). A third ceiling catches the bulkified version too:
10,000 records processed by DML across the whole transaction
(L19556), which is why the Get in the corrected flow carries a
`<limit>`. Earlier revisions of this file named "100 SOQL" for
the DML-in-loop case; that was the wrong counter.

**Solution:** One Get Records (with a bulk filter), one Loop
(assign-only, no DML inside), one Update Records *outside* the
loop.

```
Flow: Account_Status_Inactive_Cascade
  Type: Record-Triggered Flow
  Object: Account
  Trigger: A record is updated
  Condition Requirements:
    - ISCHANGED({!$Record.Status__c})
    - {!$Record.Status__c} = "Inactive"
  Optimize for: Actions and Related Records

Get Records: Get_Related_Contacts
  Object: Contact
  Filter: AccountId = {!$Record.Id}
    AND MailingOptOut__c = FALSE      ← exclude already-opted-out
  Store: All records in `relatedContacts`

Loop: Opt_Out_Each
  Collection: relatedContacts
  Variable: currentContact

  Assignment: Set_Opt_Out
    currentContact.MailingOptOut__c = TRUE
    currentContact.OptOut_Source__c = "Account Status: Inactive"
    Add `currentContact` to collection `contactsToUpdate`

[Outside the loop]
Update Records: Update_Opted_Out_Contacts
  Input: contactsToUpdate
```

**Why it works:** When the trigger fires on 200 Accounts at once,
the Flow engine batches the Get Records across all 200 — internally
it issues one or two SOQLs to retrieve every related Contact,
not 200. The Loop runs in memory (no SOQL, no DML). The Update
Records at the end fires one DML per ~200 records (Salesforce
auto-chunks if the collection is large) for all changed Contacts
across all 200 source Accounts.

The `MailingOptOut__c = FALSE` filter on Get Records is critical
— without it, the flow re-updates already-opted-out Contacts on
every Account status change, wasting DML and re-firing any flow
that's listening for `MailingOptOut__c` changes.

---

## Anti-Pattern: Update Records inside a Loop element

**What practitioners do:**

```
Flow: Account_Cascade (WRONG)

Get Records: Get_Contacts
  Filter: AccountId = {!$Record.Id}
  Store: All records in `relatedContacts`

Loop: Each_Contact
  Collection: relatedContacts
  Variable: currentContact

  Update Records: Update_One           ← THE BUG
    Filter: Id = {!currentContact.Id}
    Fields: MailingOptOut__c = TRUE
```

**What goes wrong:** On a single Account with 50 Contacts, this
flow issues 50 DML operations. On a bulk update of 200 Accounts
(each with ~20 Contacts), that's 200 × 20 = 4,000 DML
operations in one transaction — the synchronous ceiling is 150
DML statements (`apexdev.txt` L19550), so the transaction dies
at operation 151 and rolls back. Every record in the bulk batch
fails; users see a wall of error toasts.

Worse, the failure is invisible at design time. Flow Builder's
"Run with Debug" feature against a single record runs the flow
50 times for a 50-Contact account and reports `50 DML, success`.
Only a 200-record bulk test in a sandbox surfaces the limit.
Production teams discover the issue when a quarterly bulk run
fires for the first time.

**Correct approach:** Move the DML out of the loop. Use the loop
ONLY to assign values to in-memory record variables and add them
to a collection. Issue ONE Update Records call after the loop
completes, with the entire collection as input. This matches the
canonical "Get → Loop assign → Update outside loop" pattern at the
top of `examples.md` Example 2.

In Flow Builder this is enforced by convention — the platform
permits Update Records inside a Loop because some legitimate uses
exist (e.g., conditional re-fetch from inside a complex loop), but
those uses are rare and should be flagged in code review. A blanket
rule that works for >95% of cases: "no DML inside Loop, ever."


---

## Reading the failure out of the org, before and after

Neither example above is provable from Flow Builder. Both are provable from a
debug log and two queries. This is the artifact to run when someone says "the
flow works, I tested it."

### Before: prove the anti-pattern scales with child count

```bash
# 1. one Account, many children -- the case the anti-pattern survives
sf data query --target-org uat --query \
  "SELECT AccountId, COUNT(Id) children FROM Contact GROUP BY AccountId ORDER BY COUNT(Id) DESC LIMIT 5"

# 2. turn on a Workflow-category log, then edit ONE of those Accounts in the UI.
#    Read the tail of the log:
#      LIMIT_USAGE_FOR_NS  -> "Number of DML statements: N out of 150"
#    N tracks the child count. That is the signature of DML inside the Loop.
sf apex log tail --target-org uat --color

# 3. now the bulk case, in a sandbox only. 200 parents through the same path
sf data update bulk --sobject Account --file data/accounts-200-status.csv --target-org uat
```

### After: prove the corrected flow is flat

Run the identical three steps against the corrected flow. The pass condition is
that the DML statement count in `LIMIT_USAGE_FOR_NS` is **the same number** for
step 2 and step 3. Rows processed will differ — that counter is supposed to
scale — but statements must not.

```sql
-- Did the cascade actually land, and did it stop where the filter said it would?
SELECT Account.Status__c, MailingOptOut__c, OptOut_Source__c, COUNT(Id)
FROM Contact
WHERE Account.Status__c = 'Inactive'
GROUP BY Account.Status__c, MailingOptOut__c, OptOut_Source__c
```

Any row with `MailingOptOut__c = false` under an Inactive Account is a Contact the
Get Records filter excluded or the Update never reached — the two failure modes
that look identical from the Flow Builder canvas.

The full deployable version of both flows, with the entry criteria that make the
counts flat, is in `references/metadata-examples.md`.
