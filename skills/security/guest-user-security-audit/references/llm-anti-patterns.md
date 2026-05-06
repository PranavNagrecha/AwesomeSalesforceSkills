# LLM Anti-Patterns — Guest User Security Audit

Mistakes AI assistants commonly make when generating Apex / Aura /
LWC for guest-user-reachable surfaces.

---

## Anti-Pattern 1: `without sharing` on a public-site Apex class

**What the LLM generates.**

```apex
public without sharing class PublicAccountService {
    @AuraEnabled(cacheable=true)
    public static List<Account> findAccounts(String name) {
        return [SELECT Id, Name FROM Account WHERE Name LIKE :('%' + name + '%')];
    }
}
```

**Why it happens.** `without sharing` is a common copy-paste; the
LLM doesn't surface the guest exposure.

**Correct pattern.** `with sharing` for guest-reachable classes.
Restrict the SOQL by an explicit "public" flag. Use bind variables
to avoid SOQL injection. Apply `WITH SECURITY_ENFORCED`.

**Detection hint.** Any `@AuraEnabled` or `@RestResource` Apex
class declared `without sharing`.

---

## Anti-Pattern 2: `@RestResource(urlMapping=...)` without auth verification

**What the LLM generates.**

```apex
@RestResource(urlMapping='/PublicData/*')
global without sharing class PublicDataApi {
    @HttpGet
    global static List<Account> doGet() { return [SELECT Id, Name FROM Account]; }
}
```

**Why it happens.** Quick public-API pattern.

**Correct pattern.** REST endpoints exposed via the public site
URL must be `with sharing`, must restrict the query, and the
business case for a public unauthenticated endpoint must be
documented. Most "public APIs" should actually be authenticated.

**Detection hint.** Any `@RestResource` class with `without
sharing` or no sharing declaration.

---

## Anti-Pattern 3: Treating `WITH SECURITY_ENFORCED` as full coverage

**What the LLM generates.**

```apex
public without sharing class C {
    @AuraEnabled
    public static List<Contact> getContacts() {
        return [SELECT Id, Email FROM Contact WITH SECURITY_ENFORCED];
    }
}
```

> The query is secure because of `WITH SECURITY_ENFORCED`.

**Why it happens.** The clause sounds comprehensive.

**Correct pattern.** `WITH SECURITY_ENFORCED` enforces FLS and
CRUD; it does not enforce record-level sharing. A `without
sharing` class still returns records the guest user shouldn't see.
Combine `with sharing` + `WITH SECURITY_ENFORCED`.

**Detection hint.** Any code claim that `WITH SECURITY_ENFORCED`
is sufficient on its own.

---

## Anti-Pattern 4: Granting "View All Data" to the guest profile

**What the LLM generates.**

> Grant View All Data on the Guest profile so the public site can
> display Account information.

**Why it happens.** Generic "fix permission" thinking.

**Correct pattern.** Modern orgs cannot grant View All Data on
Guest. Even in older orgs the answer is never "give View All";
the answer is sharing rules scoped to a public flag, with `with
sharing` Apex enforcing it.

**Detection hint.** Any recommendation involving `View All Data` or
`Modify All Data` for a guest profile.

---

## Anti-Pattern 5: Suggesting `system.runAs(guestUser)` as test coverage

**What the LLM generates.**

```apex
@isTest
static void testGuest() {
    User g = [SELECT Id FROM User WHERE UserType = 'Guest' LIMIT 1];
    System.runAs(g) {
        // ...
    }
}
```

**Why it happens.** `runAs` mirrors a normal user-context test.

**Correct pattern.** `runAs` is a good unit-test technique but does
not exercise the full public-site stack. Couple it with a
manual / scripted Run-As-Guest browser test that walks the actual
site and inspects network responses. Apex tests miss the
component-rendering path.

**Detection hint.** Any guest-security test plan that relies on
`runAs` alone without a network-level public-site probe.

---

## Anti-Pattern 6: SOQL with concatenated guest input

**What the LLM generates.**

```apex
return Database.query('SELECT Id FROM Account WHERE Name LIKE \'' + userInput + '%\'');
```

**Why it happens.** Quick way to satisfy "search by name from a
public form".

**Correct pattern.** Use bind variables (`:userInput`) and
`String.escapeSingleQuotes` if dynamic SOQL is unavoidable. Public-
site SOQL injection is OWASP A03; combined with guest object access
it can dump entire tables.

**Detection hint.** Any concatenated user input in dynamic SOQL,
particularly in guest-reachable code paths.

---

## Anti-Pattern 7: Forgetting that each site has its own Guest User

**What the LLM generates.**

> Audit the Guest User profile.

**Why it happens.** Treating "Guest User" as singular.

**Correct pattern.** Each Experience Cloud site has its own Guest
User. Enumerate sites first; audit each.

**Detection hint.** Any audit checklist that does not enumerate
sites.
