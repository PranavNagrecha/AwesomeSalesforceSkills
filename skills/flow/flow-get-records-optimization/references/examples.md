# Examples — Get Records Optimization

## Example 1: Lift Query Out Of Loop

**Before:**

```
For each case in cases:
    Get Records Account where Id = case.AccountId, limit 1
    Assign case.AccountName = Account.Name
```

For 200 cases, this is 200 SOQL. Blows the limit fast.

**After:**

```
Build collection accountIds from cases.
Get Records Account where Id IN accountIds, limit 200
For each case in cases:
    Find matching account in collection
    Assign case.AccountName
```

One SOQL.

## Example 2: Filter Sharpness

**Before:** Get Records Opportunity where `Name LIKE '%Smith%'`. Full
scan. 50k default limit. Slow.

**After:** Get Records Opportunity where
`AccountId = {!recordId}` then filter in-memory on Name.
Indexed filter, bounded result.

## Example 3: Field Trim

**Before:** "All fields" on Contact (80 fields × 500 records = 40k
attribute reads).

**After:** explicit fields `Id, FirstName, LastName, Email, AccountId`.
80% smaller heap.

## Example 4: Top N

**Before:** Get Records Case, sort by CreatedDate desc, no limit; then
Decision "first = top."

**After:** Get Records with sort + limit 1. Engine uses the sort+limit
to stop early.

## Example 5: Cross-Flow Reuse

Screen Flow visits two screens both needing the same user's Manager.

**Before:** Get Records Manager on each screen.

**After:** Get Records once at flow start; pass into both screens as a
variable.
