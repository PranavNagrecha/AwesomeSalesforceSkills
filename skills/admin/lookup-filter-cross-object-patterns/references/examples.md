# Examples — Lookup Filter Cross Object Patterns

Worked requirements, sized against what a `lookupFilter` can and cannot express. The deployable XML
for each shape lives in `references/metadata-examples.md`; this file is about deciding which shape
the requirement is.

## Example 1: Contact-on-Case constrained to the case's account

**Context:** Support reps add contacts to cases. The picker lists every contact in the org.

**Problem:** Reps pick the wrong contact, then a downstream sharing rule grants the wrong customer access to the case.

**Solution:**

```text
Object:       Case
Field:        ContactId
filterItems:  Contact.AccountId  equals  $Source.AccountId
isOptional:   false
errorMessage: "Choose a contact who belongs to the account on this case."
Exemption:    none
```

**Why it works:** The picker narrows to contacts under the case's already-selected account, and the
`isOptional` `false` setting turns the same condition into a save-time rejection carrying that
message. Full XML: `references/metadata-examples.md` §1.

**What it does not do:** It cannot require that `AccountId` is filled in *first*. A blank
`$Source.AccountId` makes the comparison meaningless, not the save invalid. That part is a validation
rule — `admin/validation-rules`.

---

## Example 2: Account Manager restricted to same region

**Context:** `Opportunity.Account_Manager__c` is a User lookup. Sales ops wants the picker to show
only users whose `User.Region__c` matches the opportunity's region.

**Problem:** Wrong-region account managers were being assigned because the lookup showed every user.

**Solution:** Deploy `isOptional` `true` with an `infoMessage`, measure, then flip. The measuring
step is the one teams skip:

```sql
-- Run BEFORE setting isOptional to false. Every row here is a record whose
-- next save would be rejected by the new filter.
SELECT COUNT()
FROM Opportunity
WHERE Account_Manager__c != NULL
  AND Region__c != NULL
  AND Account_Manager__r.Region__c != Region__c
```

```sql
-- The same rows with enough columns to build the fix file.
SELECT Id, Name, StageName, Region__c,
       Account_Manager__c, Account_Manager__r.Name, Account_Manager__r.Region__c
FROM Opportunity
WHERE Account_Manager__c != NULL
  AND Region__c != NULL
  AND Account_Manager__r.Region__c != Region__c
ORDER BY Id
```

A non-zero count is the whole decision. Zero means flip to `isOptional` `false` today; anything else
means backfill first, or ship an OR'd exemption item and a date to remove it.

**Why it works:** Optional → measure → required is the only order that does not turn a data-quality
improvement into a save outage on records nobody was touching.

---

## Example 3: A requirement a lookup filter cannot express

**Context:** "A Contract's billing contact must be a contact on the account, **and** must have been
active in the last 90 days."

**Problem:** The recency half has no field to point at. `FilterOperation` is a closed enum of
comparisons (api_meta.txt:43903–43916) — there is no date arithmetic, no `TODAY()`, no function of
any kind on either side of an item.

**Solution:** Split it. The account half is a filter item; the recency half becomes a formula
checkbox on the target object that the filter can then compare against.

```text
Contact.Recently_Active__c  (Formula, Checkbox, on Contact)
  LastActivityDate > TODAY() - 90

lookupFilter on Contract__c.Billing_Contact__c
  1: Contact.AccountId          equals  $Source.Account__c
  2: Contact.Recently_Active__c equals  true
  booleanFilter: 1 AND 2
```

**Why it works:** Every transformation happens in a place that supports transformations — a formula
field — and the filter stays a list of field/operator/value comparisons, which is all it ever was.
`admin/formula-fields` covers what this costs at query time on a large object.

**Watch for:** A formula field like this is evaluated at read time, so the filter is always current,
but it also cannot be indexed. On a multi-million-row target the picker gets slower, not wrong.

---

## Anti-Pattern: hand-coding the filter logic in a validation rule instead

**What practitioners do:** Skip the lookup filter and write only a validation rule:

```text
AND(
  NOT(ISBLANK(ContactId)),
  NOT(ISBLANK(AccountId)),
  Contact.AccountId <> AccountId
)
```

**What goes wrong:** The lookup picker still shows every contact in the org. Users keep choosing
wrong ones, hit the error on save, and lose the rest of the form. The rule is correct and the
experience is terrible.

**Correct approach:** Both, deliberately. The filter narrows the picker so the wrong choice is hard
to make; the validation rule catches the writes that never opened a picker. They are complementary,
not redundant — and the validation rule is also the only half whose enforcement surface is documented
for API and Data Loader writes.

**Watch for:** The two drifting apart. When the filter gains a third condition and the rule does not,
you now have two different definitions of the same constraint. Put the filter's `description` and the
rule's `description` in agreement, and change them in the same commit.
