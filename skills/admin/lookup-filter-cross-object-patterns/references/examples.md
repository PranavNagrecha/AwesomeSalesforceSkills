# Examples — Lookup Filter Cross Object Patterns

## Example 1: Contact-on-Case constrained to the case's account

**Context:** Support reps add contacts to cases. The picker lists every contact in the org.

**Problem:** Reps pick the wrong contact, then a downstream sharing rule grants the wrong customer access to the case.

**Solution:**

```text
Object:   Case
Field:    ContactId
Filter:   Contact.AccountId  equals  $Source.AccountId
Required: Yes
Admin bypass: No
```

**Why it works:** The picker dialog short-circuits to contacts under the case's already-selected account, and the required flag rejects API saves that come in via integrations or Apex.

---

## Example 2: Account Manager restricted to same region

**Context:** Opportunity.Account_Manager__c is a User lookup. Sales ops wants the picker to only show users whose `User.Region__c` matches the opportunity's owner's region.

**Problem:** Wrong-region account managers were getting added because the lookup showed every user.

**Solution:**

```text
Object:   Opportunity
Field:    Account_Manager__c
Filter:   User.Region__c  equals  $Source.Owner.Region__c
Required: No (during 60-day rollout)
Admin bypass: Yes (Data Migration profile only)
```

After 60 days of running optional, run a report counting Opportunity records where the manager's region != the owner's region. If zero, flip to required.

**Why it works:** Optional → measure → required is the only safe path when the org has historical data that may violate the new rule.

---

## Anti-Pattern: hand-coding the filter logic in a validation rule instead

**What practitioners do:** Skip the lookup filter and just write a validation rule `AND(NOT(ISBLANK(ContactId)), Contact.AccountId <> AccountId)`.

**What goes wrong:** The lookup picker still shows every contact; users keep picking wrong, hit the validation error on save, and lose typed work. UX collapses.

**Correct approach:** Use the lookup filter (narrows the picker) AND a validation rule (catches API/Apex paths) together. The two are complementary, not redundant — the filter shapes UX, the validation rule shapes enforcement on writes that bypass the picker.
