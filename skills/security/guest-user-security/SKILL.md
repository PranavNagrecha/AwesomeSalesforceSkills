---
name: guest-user-security
description: "Use when hardening the Experience Cloud guest user profile, controlling unauthenticated access to records and Apex, or investigating data exposure through guest SOQL. Covers object permissions, sharing model enforcement for unauthenticated users, and Apex execution context. NOT for Experience Cloud site creation (use Experience Cloud skills) or for authenticated external user security (use security/experience-cloud-security)."
category: security
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
triggers:
  - "guest user is exposing records they should not see on our Experience Cloud site"
  - "how do I harden the guest user profile for a public-facing Salesforce site"
  - "unauthenticated users can access sensitive data through our Apex controller"
  - "what permissions should the guest user profile have on my Experience Cloud site"
  - "guest sharing rules stopped working after a Salesforce upgrade"
tags:
  - guest-user
  - experience-cloud
  - unauthenticated-access
  - sharing
  - security-hardening
inputs:
  - "Experience Cloud site name and guest user profile"
  - "List of Apex classes accessible via guest context (Apex REST, @AuraEnabled, invocable)"
  - "Object and field permissions granted to the guest profile"
  - "OWD settings for objects exposed to guest users"
outputs:
  - "Guest user hardening checklist with specific remediation steps"
  - "Apex class review findings: classes that expose data to guest context"
  - "Sharing model assessment for objects accessible unauthenticated"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-04
---

# Guest User Security

This skill activates when a practitioner needs to audit, configure, or remediate security for Salesforce Experience Cloud guest users — the unauthenticated profile that backs every public-facing site. Guest users have a unique execution context with permanent system-mode Apex access, OWD-enforced record visibility (since Spring '21), and a profile that cannot be deleted or duplicated.

---

## Before Starting

Gather this context before working on anything in this domain:

- Identify which Experience Cloud sites use guest access (Setup > Digital Experiences > All Sites). Each site has its own guest user profile with independent object permissions.
- Confirm the org is on API v51+ (Spring '21). The mandatory Secure Guest User Record Access toggle enforced org-wide-default-based record visibility for guests in Spring '21. If this toggle is OFF in older orgs, guests may be seeing all records.
- List all Apex classes referenced by guest pages: @AuraEnabled classes, Apex REST endpoints on Force.com Sites, and invocable actions exposed via guest Flow.
- Know the OWD for every object the site touches. Guest users see records only when OWD is Public Read Only or Public Read/Write — Private OWD hides all records unless sharing rules explicitly grant Read Only.

---

## Core Concepts

### Guest User Runs in System Mode — Always

Every guest user executes Apex in system mode regardless of the `with sharing` or `without sharing` keyword on the class. Unlike authenticated users, guest users have no system-enforced FLS or CRUD in Apex — the `with sharing` keyword only enforces the sharing model (which records are visible), not field-level security.

Practical impact: An Apex class marked `with sharing` will correctly hide records the guest cannot see via sharing, but it will still expose every field on the records that ARE visible. Combine `with sharing` for record filtering with explicit FLS checks or `WITH USER_MODE` in SOQL for field filtering.

### Spring '21 Mandatory Secure Guest User Record Access

Before Spring '21, guest users could use sharing rules to access Private OWD records. Spring '21 made the "Secure Guest User Record Access" toggle mandatory. After this change:
- Guest users can only access records where OWD is Public Read Only or Public Read/Write.
- Guest sharing rules can only grant Read Only access (not Read/Write).
- Guest users cannot see records owned by other guest users unless OWD is public.

Any site built before Spring '21 that relied on guest sharing rules for Private OWD records broke silently during the release upgrade. Orgs that had the toggle OFF and have not yet enforced it are running with weakened guest isolation.

### Object and Field Permissions on the Guest Profile

Guest users have a dedicated profile per site. Permissions must be explicitly granted on this profile:
- Grant only the minimum required object permissions (typically Read only on specific objects).
- Never grant Modify All, View All, Create, Edit, or Delete to the guest profile.
- Check field permissions: even Read access to sensitive fields (SSN, birthdate, email) on public-facing records is a data exposure risk.
- Permission sets CAN be assigned to guest users since Spring '22 — this is a new attack surface. Audit permission set assignments to the guest user.

### WITH USER_MODE in SOQL

Since Summer '22, Salesforce supports `WITH USER_MODE` in SOQL, which enforces both the sharing model AND field-level security in a single query modifier. For guest-facing Apex:

```apex
List<Account> results = [
  SELECT Id, Name FROM Account WITH USER_MODE WHERE IsActive__c = true
];
```

This is the preferred pattern over manual FLS checks with `Schema.SObjectType.Account.fields.Name.isAccessible()`. Both approaches prevent field exposure but `WITH USER_MODE` is declarative and harder to misconfigure.

---

## Common Patterns

### Hardening an Apex Class for Guest Context

**When to use:** Any @AuraEnabled, Apex REST, or @InvocableMethod class reachable from a guest user session.

**How it works:**
1. Add `with sharing` to the class declaration — this enforces the sharing model so private records are not leaked.
2. Replace all SOQL with `WITH USER_MODE` queries to enforce FLS.
3. Never return raw SObject lists to the client — use DTO/wrapper classes to explicitly whitelist returned fields.
4. Validate all inputs against an allowlist. Guest users can craft payloads with unexpected field names or IDs.

```apex
public with sharing class GuestCaseController {
  @AuraEnabled(cacheable=true)
  public static List<CaseDTO> getOpenCases(String accountId) {
    // WITH USER_MODE enforces sharing + FLS
    List<Case> cases = [
      SELECT Id, CaseNumber, Subject, Status
      FROM Case
      WHERE AccountId = :accountId AND Status != 'Closed'
      WITH USER_MODE
      LIMIT 50
    ];
    List<CaseDTO> result = new List<CaseDTO>();
    for (Case c : cases) {
      result.add(new CaseDTO(c.Id, c.CaseNumber, c.Subject, c.Status));
    }
    return result;
  }
}
```

**Why not without sharing:** `without sharing` ignores the sharing model entirely — any guest user who knows a record ID can access it via SOQL even if OWD is Private.

### Configuring OWD for Guest-Accessible Objects

**When to use:** Deciding whether an object's records should be accessible to unauthenticated users.

**How it works:**
1. If the object must be publicly readable, set OWD to Public Read Only. Guest users can then read all records.
2. If the object must NOT be publicly readable, set OWD to Private. Guest users will see zero records regardless of Apex sharing keywords.
3. Use `WITH USER_MODE` in all Apex touching this object so the OWD enforcement is consistent.
4. Never rely on Apex logic alone to hide records — an Apex bug can bypass conditional filters. The OWD is the backstop.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Apex class used by both guests and authenticated users | Split into guest-specific class with `with sharing` + `WITH USER_MODE`, delegate to shared service layer | Mixing contexts in one class is error-prone |
| Object with sensitive fields but publicly queryable records | OWD Public Read Only, remove sensitive fields from guest profile FLS | OWD controls visibility; FLS controls field access |
| Guest user needs to create records (e.g., form submission) | Grant Create permission on guest profile for that object only, never Edit/Delete | Minimum privilege; form submissions are Create-only |
| Guest site was built pre-Spring '21 and sharing rules are failing | Enable "Secure Guest User Record Access" toggle and switch affected objects to Public OWD | Old sharing rules for Private OWD no longer work; restructure required |
| Permission set must be assigned to guest user | Audit carefully — list all PSets assigned, verify no elevated object permissions or system permissions are included | PS assignment to guest user is a new vector since Spring '22 |

---

## Recommended Workflow

1. Enumerate all Experience Cloud sites in the org and identify which use guest access. For each site, open the guest user profile.
2. Audit object permissions on the guest profile: remove any Create/Edit/Delete/View All/Modify All that is not strictly required.
3. Audit field permissions on the guest profile for every Read-accessible object: remove access to sensitive fields (PII, financial, health data).
4. Review OWD for every object the site touches. Confirm Private objects are not accessible to guests. Set to Public Read Only only if unauthenticated access is genuinely required.
5. Review all Apex classes reachable from guest sessions. Add `with sharing` and replace SOQL with `WITH USER_MODE` queries.
6. Run the Salesforce Security Health Check to identify open guest user permission gaps.
7. Test the site as a guest user (incognito browser, no session) and confirm that no unexpected records or fields are exposed.

---

## Review Checklist

- [ ] Guest profile has no Create, Edit, Delete, View All, or Modify All on any object
- [ ] Sensitive fields are removed from guest profile field permissions
- [ ] All Apex reachable from guest sessions uses `with sharing` AND `WITH USER_MODE`
- [ ] Objects with Private OWD are not being accessed via guest SOQL
- [ ] "Secure Guest User Record Access" toggle is ON in all relevant orgs
- [ ] Permission sets assigned to the guest user have been reviewed and minimized
- [ ] Site tested in incognito/unauthenticated state — no unexpected record or field exposure

---

## Salesforce-Specific Gotchas

1. **`with sharing` alone does not prevent field exposure** — it controls which RECORDS a guest sees, not which FIELDS. A `with sharing` class can still return all fields on every accessible record. Always combine with `WITH USER_MODE` or explicit FLS checks.
2. **Apex without sharing executed by a guest is a full-org data read** — a single `without sharing` class called from a guest LWC component will return any record matching the SOQL filter, regardless of OWD. This is the most common guest data leak pattern.
3. **Guest sharing rules became Read Only only in Spring '21** — any guest sharing rule granting Read/Write that was created before Spring '21 was silently downgraded to Read Only. Orgs that depended on guest write access via sharing rules broke on upgrade.
4. **Guest users can be assigned permission sets since Spring '22** — this means elevated permissions can be granted to the guest user indirectly. Always audit the full effective permission set of the guest user, not just the profile.
5. **Each site has its own guest user** — changing the guest profile on Site A does not affect Site B. If you have 3 sites, you must audit 3 guest profiles independently.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Guest user hardening checklist | Ordered remediation items for each site: profile permissions, FLS, OWD alignment, Apex review |
| Apex exposure report | List of @AuraEnabled/@RestResource classes reachable from guest sessions with `with sharing` and `WITH USER_MODE` status |
| OWD alignment table | Object-by-object table showing current OWD, guest accessibility intent, and required change |

---

## Related Skills

- security/experience-cloud-security — authenticated external user security, sharing sets, external OWD
- security/security-health-check — org-wide security posture assessment
- security/api-security-and-rate-limiting — controlling Apex REST exposure for unauthenticated endpoints
