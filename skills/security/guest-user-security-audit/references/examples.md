# Examples — Guest User Security Audit

## Example 1 — `without sharing` Apex callable from guest

**Context.** Audit finds an `@AuraEnabled` Apex method on a class
declared `without sharing`:

```apex
public without sharing class PublicAccountController {
    @AuraEnabled(cacheable=true)
    public static List<Account> getAllAccounts() {
        return [SELECT Id, Name, Industry, AnnualRevenue FROM Account];
    }
}
```

**Why it's a finding.** Any LWC or Aura component on the public
Experience Cloud site can call this method. The class is
`without sharing`, so the guest user receives every Account in the
org, not just records shared to guest.

**Remediation.**

```apex
public with sharing class PublicAccountController {
    @AuraEnabled(cacheable=true)
    public static List<Account> getPublicAccounts() {
        return [
            SELECT Id, Name, Industry FROM Account
            WHERE Public_Accounts__c = true
            WITH SECURITY_ENFORCED
        ];
    }
}
```

`with sharing` enforces the guest user's sharing; explicit filter
restricts to a public flag; `WITH SECURITY_ENFORCED` enforces FLS.

**OWASP mapping.** A01 Broken Access Control.

---

## Example 2 — Sharing rule granting all Cases to guest

**Context.** Setup -> Sharing Settings shows a sharing rule on
Case: "Type = Guest user, owned by criteria All Cases, access
Read-Only".

**Why it's a finding.** Every Case in the org is readable by the
guest user. Any custom component or REST endpoint that queries Case
will return all Cases, including private / sensitive ones.

**Remediation.** Replace the all-Cases rule with a criteria-based
rule that limits to a `Public_FAQ_Case__c = true` flag (or a
record type, or a queue).

**OWASP mapping.** A01 Broken Access Control.

---

## Example 3 — REST endpoint exposed publicly without auth

**Context.**

```apex
@RestResource(urlMapping='/PublicData/*')
global without sharing class PublicDataApi {
    @HttpGet
    global static List<Account> doGet() {
        return [SELECT Id, Name, AnnualRevenue FROM Account];
    }
}
```

**Why it's a finding.** Apex REST classes exposed via the public
site URL are callable by anyone. `without sharing` returns every
Account.

**Remediation.** Convert to `with sharing`, restrict the query, and
verify the public site's profile actually needs this endpoint at
all. Many such endpoints exist as leftovers from internal-only
proofs of concept.

**OWASP mapping.** A01 Broken Access Control + A05 Security
Misconfiguration.

---

## Example 4 — Run-As-Guest test reveals object enumeration

**Context.** Auditor runs the site as the Guest User. Network tab
shows a GET to `/services/data/v60.0/query?q=...` returning Contact
data.

**Why it's a finding.** Guest is hitting the standard REST API.
Even with secure-by-default, if the Guest profile has Read on
Contact and a sharing rule grants any Contacts, the API returns
them.

**Remediation.** Guest profile should not grant Read on Contact
unless absolutely required. Audit the matching sharing rule;
restrict the criteria; or remove guest's standard API access (Setup
-> Sites -> per-site -> Restrict guest user from accessing
standard Salesforce APIs).

**OWASP mapping.** A01 Broken Access Control.

---

## Example 5 — Audit query for `without sharing` classes

**Tooling SOQL.** Run via Tooling API or `sfdx force:data:soql`
against the Tooling endpoint:

```sql
SELECT Id, Name, Body
FROM ApexClass
WHERE Body LIKE '%without sharing%'
```

Then for each, manually check for `@AuraEnabled` or
`@RestResource` annotations to determine guest reachability.

**Caveat.** `Body` queries return source; pattern-matching can have
false positives (comments, strings). Use this as a triage list, not
a final verdict.

---

## Example 6 — Profile audit script

**Discovery checklist** for a Guest profile:

- Object Permissions: zero "Read" / "Create" / "Edit" / "Delete"
  unless explicit business need documented.
- System Permissions: no "View All Data", "Modify All Data",
  "Manage Users", "Author Apex", "Customize Application", "Schedule
  Reports".
- Field-level security: blanket-disabled by default; enable only
  fields needed by public components.
- Login IP ranges: not applicable to guest (no login).
- Session settings: short timeout if guest checkout / form-fill is
  the use case.

If any item fails, document with OWASP A01 / A05 mapping in the
audit report.
