# Examples — SOQL Outer-Join & Null Semantics

All queries below are illustrative and authored from the official SOQL and SOSL Reference.
Replace object, field, and namespace with your own. The behavior shown is standard query-
language behavior documented in the reference — no GA/Beta maturity level is implied.

## Example 1: A relationship query returns parent-less rows (the outer join)

**Context:** you query Cases with their Account name to build a report and are surprised that
Cases with no Account still appear, with blank Account columns.

**Problem:** you assumed the join filters those rows out.

**Behavior:**

```sql
SELECT Id, CaseNumber, Account.Id, Account.Name
FROM Case
ORDER BY Account.Name
```

This returns **every** Case. Per the reference, "Relationship SOQL queries return records, even
if the relevant foreign key field has a null value, as with an outer join," and in an `ORDER BY`
"the record is returned even if the foreign key value in a record is null." A custom-object
relationship behaves identically:

```sql
SELECT Id, Name, Parent__r.Id, Parent__r.Name
FROM Child__c
ORDER BY Parent__r.Name
```

**Why it matters:** if the report should exclude Cases with no Account, add an explicit
foreign-key filter — the join will not do it for you (see Example 3).

---

## Example 2: `WHERE Parent.Field = null` returns rows whose parent doesn't exist

**Context:** you want "Cases with no Contact" and write the intuitive filter on the parent
field.

**Problem:** the filter returns Cases with an empty `ContactId` *and* Cases whose Contact is
unresolvable, so the count is higher than "Cases with no Contact."

**Behavior:**

```sql
-- Over-selects: returns the Case even if the parent Contact does not exist
SELECT Id FROM Case WHERE Contact.LastName = null
```

The reference states: "In a WHERE clause that checks for a value in a parent field, the record
is returned even if the parent does not exist."

**Correct approach:** filter the foreign-key Id column, which is a scalar field on Case:

```sql
-- Cases whose Contact lookup is empty
SELECT Id FROM Case WHERE ContactId = null
```

**Why it works:** `ContactId` is a field on the Case itself; its null test means "unset"
precisely, independent of whether any parent record exists.

---

## Example 3: Select only rows with a populated (or empty) lookup

**Context:** you need two clean result sets — Contacts linked to an Account, and Contacts not
linked to one.

**Solution:**

```sql
-- Populated lookup
SELECT Id, Name FROM Contact WHERE AccountId != null

-- Empty lookup
SELECT Id, Name FROM Contact WHERE AccountId = null
```

**Why it works:** filtering the foreign-key field directly avoids the outer-join semantics of a
traversed parent field, so each query returns exactly the intended rows.

---

## Example 4: OR keeps null-foreign-key rows

**Context:** you filter Contacts by last name OR by their Account name and get Contacts with no
Account in the results.

**Behavior:**

```sql
SELECT Id FROM Contact WHERE LastName = 'Young' OR Account.Name = 'Quarry'
```

Per the reference, "In a WHERE clause that uses OR, records are returned even if the foreign key
value in a record is null." A Contact named 'Young' with a null `AccountId` is returned because
it satisfies the first branch — the relationship branch does not exclude parent-less rows.

**Why it matters:** if a branch must not apply to parent-less rows, add an explicit
`AccountId != null` condition rather than relying on the relationship traversal to filter.

---

## Example 5: Boolean fields treat null as false

**Context:** you write `WHERE Test__c = null` expecting "unset" rows and instead get every
`false` row.

**Behavior:**

```sql
-- Equivalent to WHERE Test__c = false — returns all "false" Accounts
SELECT Id, Name, Test__c FROM Account WHERE Test__c = null

-- Equivalent to WHERE Test__c = true
SELECT Id, Name, Test__c FROM Account WHERE Test__c != null
```

"Boolean fields never contain null values," and on an outer-joined object a Boolean is "treated
as false when no records match the query." So `= null` is evaluated as `= false` and `!= null`
as `= true`.

**Correct approach:** always compare Booleans to an explicit literal so the intent is clear:

```sql
SELECT Id, Name FROM Account WHERE Test__c = false
```

**Why it works:** the explicit comparison reads exactly as it evaluates and survives code review
without the reader having to recall the null-coercion rule.

---

## Example 6: Excluding non-null values with `!= null`

**Context:** you want only Events that have an `ActivityDate`.

**Solution:**

```sql
SELECT AccountId FROM Event WHERE ActivityDate != null
```

**Why it works:** `!= null` on a nullable scalar field returns rows where the field contains a
value. (Contrast with a Boolean field, where `!= null` means `= true`, per Example 5.)

---

## Anti-Pattern: dereferencing a parent field without a null guard in Apex

**What practitioners do:** iterate an outer-join result and read the parent field directly.

```apex
// Throws System.NullPointerException on any Case whose AccountId is null
for (Case c : [SELECT Id, Account.Name FROM Case]) {
    System.debug(c.Account.Name);
}
```

**What goes wrong:** the outer join returns rows with a null foreign key, and on those rows the
parent relationship object (`c.Account`) is `null`, so `c.Account.Name` throws.

**Correct approach:** guard the relationship object before dereferencing it.

```apex
for (Case c : [SELECT Id, Account.Name FROM Case]) {
    String acctName = (c.Account != null) ? c.Account.Name : '(no account)';
    System.debug(acctName);
}
```
