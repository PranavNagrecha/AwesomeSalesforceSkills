# Examples — Flow Loop Element Patterns

Concrete before/after refactors for the most common Loop-element anti-patterns. Each example uses Flow element pseudo-syntax (the literal element list a designer would build), not Flow XML — the goal is reviewability, not deployability.

---

## Example 1: DML-in-loop refactored with Collect-Then-DML

**Context:** Record-triggered flow on `Opportunity` (After Save). When an Opp closes, mark all related `Quote` records as `Status = 'Won'` and stamp `Won_Date__c = TODAY()`.

**Problem (BAD — DML inside the loop):**

```
Get Records: Quotes_for_Opp
  Object: Quote
  Filter: OpportunityId = {!$Record.Id}
  Store all fields, all records
  → outputs: vQuotes (collection)

Loop: LoopQuotes
  Collection: vQuotes
  Iteration order: Asc
  Current item: vCurrentQuote

  Assignment: SetWonFields
    vCurrentQuote.Status = 'Won'
    vCurrentQuote.Won_Date__c = {!$Flow.CurrentDate}

  Update Records: UpdateThisQuote          <-- ANTI-PATTERN
    Record(s): vCurrentQuote               <-- one DML per iteration
End Loop
```

At a 200-Quote opportunity (or one record-triggered flow processing 200 Opps in a Bulk API insert with related-quote load), this issues 200 DML statements and busts the 150-DML cap.

**Solution (GOOD — Collect-Then-DML):**

```
Get Records: Quotes_for_Opp        (unchanged)
  → outputs: vQuotes

Assignment: InitOutputCollection
  vQuotesToUpdate (SObject Collection of Quote) = (empty)

Loop: LoopQuotes
  Collection: vQuotes
  Current item: vCurrentQuote

  Assignment: SetAndCollect
    vCurrentQuote.Status      = 'Won'
    vCurrentQuote.Won_Date__c = {!$Flow.CurrentDate}
    vQuotesToUpdate Add vCurrentQuote
End Loop

Update Records: UpdateAllQuotes              <-- single DML, post-loop
  Record(s): vQuotesToUpdate
```

**Why it works:** One DML statement regardless of input volume. The iteration variable for an SObject collection is a reference into `vQuotes`, so the field assignments mutate the same instance you Add to `vQuotesToUpdate` — no copy required.

---

## Example 2: SOQL-in-loop refactored with Map-Lookup pre-load

**Context:** Autolaunched flow processing a passed-in collection of `Case` records. For each Case, look up the `Account.Customer_Tier__c` and copy it into `Case.Cached_Tier__c`.

**Problem (BAD — Get Records inside the loop):**

```
Loop: LoopCases
  Collection: vInputCases
  Current item: vCase

  Get Records: GetAccountForCase           <-- ANTI-PATTERN
    Object: Account                        <-- one SOQL per iteration
    Filter: Id = {!vCase.AccountId}
    → vAccount

  Assignment: CopyTier
    vCase.Cached_Tier__c = {!vAccount.Customer_Tier__c}
End Loop
```

200 Cases means 200 SOQL queries against the 100-sync-SOQL limit. Fails on the 101st iteration.

**Solution (GOOD — pre-load all relevant Accounts once):**

```
Assignment: BuildAccountIdSet
  vAccountIds (Text Collection) = (empty)

Loop: CollectAccountIds          (pure assignment loop, no DML/SOQL)
  Collection: vInputCases
  Current item: vCase
  Assignment: AddId
    vAccountIds Add {!vCase.AccountId}
End Loop

Get Records: GetAllAccountsOnce               <-- one SOQL total
  Object: Account
  Filter: Id IN {!vAccountIds}
  Store: Id, Customer_Tier__c
  → vAccounts (collection)

Assignment: InitOutput
  vCasesToUpdate (SObject Collection of Case) = (empty)

Loop: LoopCases
  Collection: vInputCases
  Current item: vCase

  Loop: FindMatchingAccount       (small inner loop OK — bounded by vAccounts size)
    Collection: vAccounts
    Current item: vAcct
    Decision: IsMatch
      {!vAcct.Id} = {!vCase.AccountId} → MATCH
    MATCH path:
      Assignment: SetTier
        vCase.Cached_Tier__c = {!vAcct.Customer_Tier__c}
        vCasesToUpdate Add vCase
      (no break — flow has no break, but Decision can short-circuit on next iteration via guard)
  End Loop
End Loop

Update Records: WriteCases
  Record(s): vCasesToUpdate
```

**Why it works:** Total SOQL = 1 regardless of input size. The inner loop iterates `vAccounts` (bounded), not the database. Element count is `O(cases × accounts)` — acceptable for low-hundreds; at higher volume escalate to invocable Apex with `Map<Id, Account>` for true O(n) lookup.

---

## Example 3: Pure-filter loop replaced with Collection Filter element

**Context:** Screen flow displaying a list of `Contact` records. Filter to only contacts where `Email_Opt_In__c = TRUE` before showing the data table.

**Problem (BAD — Loop + Decision + Assignment):**

```
Loop: FilterOptIns
  Collection: vAllContacts
  Current item: vC
  Decision: IsOptedIn
    {!vC.Email_Opt_In__c} = TRUE → KEEP
  KEEP path:
    Assignment: AddToOutput
      vOptedInContacts Add vC
End Loop
```

Three elements per iteration counted against the 2,000-element ceiling, plus the design intent ("filter") is hidden in three nested elements.

**Solution (GOOD — Collection Filter element):**

```
Collection Filter: KeepOptIns
  Input collection: vAllContacts
  Condition:        Email_Opt_In__c Equals TRUE
  → vOptedInContacts (auto-typed Contact collection)
```

**Why it works:** One declarative element, intent is obvious, element count drops from `3n + 1` to `1`.

---

## Example 4: Subflow-in-loop hiding DML

**Context:** Reviewer sees a record-triggered flow on `Account` whose body looks clean — just a Loop over related Contacts and a Subflow call. Looks fine on the surface.

```
Loop: LoopContacts
  Collection: vRelatedContacts
  Current item: vContact

  Subflow: Subflow_RefreshContactScore       <-- LOOKS INNOCENT
    Input: vContact
End Loop
```

Open `Subflow_RefreshContactScore`:

```
Get Records: GetLatestActivity              <-- SOQL inside the subflow
  Object: Task
  Filter: WhoId = {!input_Contact.Id}, ORDER BY ActivityDate DESC, LIMIT 1
  → vTask

Assignment: ScoreCalc
  input_Contact.Engagement_Score__c = ...

Update Records: SaveScore                   <-- DML inside the subflow
  Record: input_Contact
```

**Anti-pattern:** The parent flow's Loop runs N iterations × (1 SOQL + 1 DML) inside the subflow. Bulkification fails at iteration 76 (DML cap) or 101 (SOQL cap).

**Correct approach:** Refactor the subflow to accept a `List<Contact>` input, do ONE Get Records `WHERE WhoId IN :inputContactIds`, build a map in-memory, write back with one Update Records. Then the parent loop disappears entirely — pass `vRelatedContacts` straight to the bulkified subflow.

---

## Anti-Pattern: Wrapping the in-loop DML in a Decision to "fix" it

**What practitioners do:** They see the DML-in-loop warning and add a Decision so the Update Records only fires on iterations where some condition is true.

```
Loop: LoopAccounts
  Decision: NeedsUpdate
    {!vAcct.Tier__c} != 'Platinum' → DO_UPDATE
  DO_UPDATE path:
    Update Records: UpdateOne     <-- STILL ANTI-PATTERN
End Loop
```

**What goes wrong:** The DML is still inside the loop. If 80 of 200 accounts need the update, you issue 80 DML statements — fewer than 200 but still N-bounded, and the next automation in the same transaction can easily push the total past 150. The fix is structural (collect-then-DML), not gating.

**Correct approach:** Use the Decision to gate the Assignment-with-Add only — the DML stays outside the loop, operating on whatever ended up in the collection (zero rows is fine — Update Records on an empty collection is a no-op, not an error).

---

## Anti-Pattern: Nested loops to "join" two collections

**What practitioners do:** Given a list of Cases and a list of Owners, they nest a loop:

```
Loop: LoopCases
  Loop: LoopOwners                    <-- O(n*m)
    Decision: Match { vCase.OwnerId = vOwner.Id }
```

**What goes wrong:** 200 cases × 200 owners = 40,000 element-executions before any work happens; far above the 2,000-element interview limit. Flow halts with `Number of executed elements has exceeded the maximum`.

**Correct approach:** Pre-load owners once, then the inner loop iterates a small bounded collection — or better, escalate to invocable Apex with a `Map<Id, User>` for true O(n).
