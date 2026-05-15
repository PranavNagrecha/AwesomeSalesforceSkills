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
Accounts (e.g., a quarterly cleanup) the Flow hits the 100 SOQL
limit before processing the 11th Account's children. The
transaction fails for ALL 200 Accounts — including the first 10
that "almost succeeded" before the rollback.

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
operations in one transaction — Flow hits the 150-DML limit at
operation 151 and the entire transaction rolls back. Every record
in the bulk batch fails; users see a wall of error toasts.

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
