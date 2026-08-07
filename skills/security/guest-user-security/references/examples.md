# Examples — Guest User Security

## Example 1: Fixing an Apex Data Leak on a Public Knowledge Portal

**Scenario:** A technology company has an Experience Cloud knowledge portal where unauthenticated visitors can search for articles. An internal audit discovers that unauthenticated visitors can query Account records by passing an account ID in a URL parameter to an @AuraEnabled controller method.

**Problem:** The Apex class `KnowledgeController` is marked `without sharing` and contains:
```apex
@AuraEnabled(cacheable=true)
public static Account getAccount(Id accountId) {
  return [SELECT Id, Name, AnnualRevenue, Industry FROM Account WHERE Id = :accountId];
}
```
Any guest user who knows or guesses an Account ID can retrieve sensitive fields including AnnualRevenue.

**Solution:**
1. Change the class to `with sharing`.
2. Replace the SOQL with `WITH USER_MODE`.
3. Return a DTO instead of a raw Account.

```apex
public with sharing class KnowledgeController {
  @AuraEnabled(cacheable=true)
  public static AccountDTO getAccount(Id accountId) {
    List<Account> accts = [SELECT Id, Name FROM Account WHERE Id = :accountId WITH USER_MODE];
    if (accts.isEmpty()) return null;
    return new AccountDTO(accts[0].Id, accts[0].Name);
  }
}
```

**Why it works:** `with sharing` restricts the result to records the guest user can see — for a guest, only the records matched by a guest user sharing rule, since guest org-wide defaults are Private on every object. `WITH USER_MODE` enforces FLS, blocking access to fields not on the guest profile. The DTO explicitly whitelists returned fields.

---

## Example 2: Guest User Creating Support Cases on a Service Portal

**Scenario:** A manufacturer's public service portal allows unauthenticated visitors to submit warranty claims (create Case records), then shows a read-only confirmation. The site was built before Winter '21.

**Problem:** After enforcement, the visitors' post-submission confirmation stopped rendering — the old grant was a queue membership / manual share that no longer reaches guest users. The site team panics and grants "Modify All" on Case to the guest profile to make it work.

**Solution:** Modify All is never appropriate for guest users, and (since Spring '21) can no longer be granted to them anyway. The correct fix:
1. Leave Case OWD alone. Guest org-wide defaults are Private on every object and can't be changed, so raising the Case OWD would not restore guest access — it would only widen access for authenticated internal users.
2. On the guest profile, grant only Create permission on Case. No Edit, Delete, or View All.
3. In the Case creation Apex, immediately set `OwnerId` to a dedicated Case Queue. Guests can't own records regardless, and queue ownership keeps the record out of any guest-facing sharing rule's criteria.
4. If the confirmation screen genuinely must read the Case back, return the field values from the same Apex transaction that created it, or add a **guest user sharing rule** whose criteria match only that submission class (for example `Is_Public_Submission__c = true`) — Read Only is all a guest sharing rule can grant, which is exactly right here.
5. Remove "Modify All" from the guest profile immediately, and remove the guest user from the queue/public group left over from the pre-Winter '21 design.

**Why it works:** Create-only profile permission gives guests exactly the access needed for form submission — no more. Read-back is granted narrowly and explicitly through the one mechanism that still reaches guests, instead of by loosening a setting that guests are not evaluated against.
