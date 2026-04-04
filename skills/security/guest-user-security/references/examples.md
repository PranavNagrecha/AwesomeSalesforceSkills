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

**Why it works:** `with sharing` restricts the result to records the guest user can see (only Public OWD records). `WITH USER_MODE` enforces FLS, blocking access to fields not on the guest profile. The DTO explicitly whitelists returned fields.

---

## Example 2: Guest User Creating Support Cases on a Service Portal

**Scenario:** A manufacturer's public service portal allows unauthenticated visitors to submit warranty claims (create Case records). The site was built before Spring '21.

**Problem:** After the Spring '21 upgrade, the original guest sharing rules that allowed guests to create Cases stopped working because the org had Cases on Private OWD. The site team panics and grants "Modify All" on Case to the guest profile to make it work.

**Solution:** Modify All is never appropriate for guest users. The correct fix:
1. Set Case OWD to Public Read/Write (acceptable since guests should only see their own submissions — enforce this via Apex after creation).
2. On the guest profile, grant only Create permission on Case. No Edit, Delete, or View All.
3. In the Case creation Apex, immediately set `OwnerId` to a dedicated Case Queue so guests cannot re-access their submitted case after navigation.
4. Remove "Modify All" from the guest profile immediately.

**Why it works:** Public OWD with Create-only profile permission gives guests exactly the access needed for form submission — no more. The queue ownership prevents guests from later reading all cases.
