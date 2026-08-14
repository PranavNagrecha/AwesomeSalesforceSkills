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
  - "we're having issues with guest user"
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
  - "Guest user sharing rules granting record access on the site"
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

This skill activates when a practitioner needs to audit, configure, or remediate security for Salesforce Experience Cloud guest users — the unauthenticated profile that backs every public-facing site. Guest users have a unique execution context: permanent system-mode Apex access, org-wide defaults locked to Private on every object (since Winter '21), record access granted only through guest user sharing rules, and a profile that cannot be deleted or duplicated.

---

## Before Starting

Gather this context before working on anything in this domain:

- Identify which Experience Cloud sites use guest access (Setup > Digital Experiences > All Sites). Each site has its own guest user profile with independent object permissions.
- Confirm how "Secure guest user record access" is configured. Since Winter '21 it is enabled in every org with Experience Cloud sites and **cannot be disabled** — there is no toggle to leave off. What legacy orgs *do* carry forward is stale configuration: public groups and queues that still list the guest user, orphaned manual/Apex managed shares, and grandfathered profile permissions.
- List all Apex classes referenced by guest pages: @AuraEnabled classes, Apex REST endpoints on Force.com Sites, and invocable actions exposed via guest Flow.
- Inventory the **guest user sharing rules**, not the OWD. Guest org-wide defaults are Private for every object and that access level can't be changed, so an object's OWD tells you nothing about guest visibility. Every record a guest can read arrives through a criteria-based guest user sharing rule.

---

## Core Concepts

### Guest User Runs in System Mode — Always

Every guest user executes Apex in system mode regardless of the `with sharing` or `without sharing` keyword on the class. Unlike authenticated users, guest users have no system-enforced FLS or CRUD in Apex — the `with sharing` keyword only enforces the sharing model (which records are visible), not field-level security.

Practical impact: An Apex class marked `with sharing` will correctly hide records the guest cannot see via sharing, but it will still expose every field on the records that ARE visible. Combine `with sharing` for record filtering with explicit FLS checks or `WITH USER_MODE` in SOQL for field filtering.

### Secure Guest User Record Access — Guest OWD Is Private, Permanently

This is the fact most guidance gets backwards. Since Winter '21, "Secure guest user record access" is enabled in every org with Experience Cloud sites and can't be disabled. Under it:

- **Guest org-wide defaults are Private for every object**, including objects not listed on the Sharing Settings page, and **that access level can't be changed.** Child objects in a master-detail relationship inherit the parent's Private setting.
- Setting an object's OWD to Public Read Only does **not** expose its records to guests. Guest sharing is a separate, always-Private model — the internal/external OWD you see in Sharing Settings is not what the guest user is evaluated against.
- **Guest user sharing rules are the only way to grant record access** to unauthenticated guests. They are a special type of criteria-based sharing rule, grant **Read Only** and nothing more, and count against the 50-criteria-based-rules-per-object limit.
- Guest users **can't** be added to public groups or queues, **can't** receive access through manual sharing or Apex managed sharing, and **can't** own records (guest-created records are reassigned to a default org user).
- Spring '21 additionally removed View All Records, Modify All Records, edit, and delete from guest users permanently.

The remediation direction therefore inverts too: a site whose guests lost access is fixed by **writing a guest user sharing rule**, never by loosening OWD. Loosening OWD widens exposure for authenticated users while doing nothing for guests — the worst possible trade.

Legacy orgs do not auto-migrate their *stale* configuration: guest users previously added to public groups or queues are not removed automatically and must be removed by hand, and grandfathered profile permissions persist until an admin strips them. That, not a disabled toggle, is what an audit is looking for.

### Object and Field Permissions on the Guest Profile

Guest users have a dedicated profile per site. Permissions must be explicitly granted on this profile:
- Grant only the minimum required object permissions (typically Read only on specific objects).
- "The only object permissions allowed for guest users are read and create." View All Records, Modify All Records, edit and delete are blocked at the platform, not merely discouraged; Create belongs on the guest profile only where a documented submission path needs it.
- **View All Fields**, the per-object permission added in Spring '25 and enabled on the Object Settings page of a permission set, is on the same block list — "View All Data, Modify All Data, and View All Records, Modify All Records, or View All Fields for a given object can't be assigned to external users." Never design guest field access around it: it auto-grants read on every field added to the object later, so guest FLS has to stay enumerated field by field.
- Check field permissions: even Read access to sensitive fields (SSN, birthdate, email) on public-facing records is a data exposure risk.
- Permission sets can be assigned to guest users, and always could — this predates Spring '22. The Spring '21 / Spring '22 / Winter '23 releases each *narrowed* what those assignments may carry, they did not create the capability. Audit permission set assignments to the guest user regardless: the residual risk is a permission set that grants read or create on an object nobody intended to expose.

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

**Why not without sharing:** `without sharing` ignores the sharing model entirely — any guest user who knows a record ID can read it via SOQL, even though the guest org-wide default is Private. This is the one thing that defeats the platform's guest lockdown, which is why it is the single highest-value finding in a guest audit.

### Granting Record Access to Guest Users

**When to use:** An unauthenticated visitor legitimately needs to read specific records (a public event listing, a published article, an order-status lookup).

**How it works:**
1. Leave the guest sharing model alone — guest OWD is Private on every object and can't be changed. Do not touch the object's OWD hoping to reach guests; it will not.
2. Create a **guest user sharing rule** on that object (Setup → Sharing Settings → the object → Guest user sharing rules). It is criteria-based, so write criteria that match *only* the records that are genuinely public — `Is_Public__c = true`, not `Id != null`.
3. Accept the ceiling: guest user sharing rules grant Read Only. If the requirement is guest writes, that is Create permission on the guest profile plus a submission-only Apex/Flow path — not a sharing rule.
4. Budget the limit: guest user sharing rules count toward the 50 criteria-based sharing rules per object.
5. Use `WITH USER_MODE` in all Apex touching the object so sharing *and* FLS are enforced consistently.
6. Never rely on Apex `WHERE` clauses alone to hide records — an Apex bug bypasses conditional filters. The sharing-rule criteria are the backstop.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Apex class used by both guests and authenticated users | Split into guest-specific class with `with sharing` + `WITH USER_MODE`, delegate to shared service layer | Mixing contexts in one class is error-prone |
| Object with sensitive fields but publicly queryable records | Narrow guest user sharing rule on the public records, remove sensitive fields from guest profile FLS | The sharing rule controls which rows; FLS controls which fields |
| Guest user needs to create records (e.g., form submission) | Grant Create permission on guest profile for that object only, never Edit/Delete | Minimum privilege; form submissions are Create-only |
| Guest site was built pre-Winter '21 and guest access is failing | Replace the old grant (public group, queue, manual share, Apex managed share, ordinary sharing rule) with a criteria-based **guest user sharing rule**; remove the guest user from any group or queue | Those mechanisms no longer reach guests; loosening OWD would not help and would widen internal exposure |
| Permission set must be assigned to guest user | Audit carefully — list all PSets assigned, verify no elevated object permissions or system permissions are included | PS assignment to guest user is a new vector since Spring '22 |

---

## Recommended Workflow

1. Enumerate all Experience Cloud sites in the org and identify which use guest access. For each site, open the guest user profile.
2. Audit object permissions on the guest profile: remove any Create/Edit/Delete/View All/Modify All that is not strictly required.
3. Audit field permissions on the guest profile for every Read-accessible object: remove access to sensitive fields (PII, financial, health data).
4. Review every **guest user sharing rule** in the org. Each one should map to a documented business justification and to criteria narrow enough that only genuinely public records match. Never change an object's OWD to reach guests — guest OWD is Private and unchangeable. Also remove the guest user from any public group or queue it was added to before Winter '21.
5. Review all Apex classes reachable from guest sessions. Add `with sharing` and replace SOQL with `WITH USER_MODE` queries.
6. Run the Salesforce Security Health Check to identify open guest user permission gaps.
7. Test the site as a guest user (incognito browser, no session) and confirm that no unexpected records or fields are exposed.

---

## Review Checklist

- [ ] Guest profile has no Edit, Delete, View All, or Modify All on any object, and Create only where a documented submission path requires it
- [ ] Sensitive fields are removed from guest profile field permissions
- [ ] All Apex reachable from guest sessions uses `with sharing` AND `WITH USER_MODE`
- [ ] Every guest user sharing rule has a documented justification and criteria that match only public records
- [ ] Guest user is not a member of any public group or queue, and holds no leftover manual or Apex managed shares
- [ ] No remediation in the plan proposes loosening an object's OWD to grant guest access
- [ ] Permission sets assigned to the guest user have been reviewed and minimized
- [ ] Site tested in incognito/unauthenticated state — no unexpected record or field exposure

---

## Salesforce-Specific Gotchas

1. **`with sharing` alone does not prevent field exposure** — it controls which RECORDS a guest sees, not which FIELDS. A `with sharing` class can still return all fields on every accessible record. Always combine with `WITH USER_MODE` or explicit FLS checks.
2. **Apex without sharing executed by a guest is a full-org data read** — a single `without sharing` class called from a guest LWC component will return any record matching the SOQL filter, regardless of OWD. This is the most common guest data leak pattern.
3. **Guest user sharing rules grant Read Only, full stop** — since Winter '21 no sharing mechanism can give a guest write access to an existing record, and guests can no longer be reached through public groups, queues, manual sharing, or Apex managed sharing at all. Orgs that depended on any of those broke on upgrade, and the fix is a guest user sharing rule (for reads) or Create-only profile permission (for submissions) — not an OWD change.
4. **Guest users can be assigned permission sets — and always could** — so elevated permissions can reach the guest user indirectly. Note the release history runs the opposite way to how it is usually reported: Spring '21 removed Edit, Delete, View All Records and Modify All Records for guests even via permission set or permission set group; Spring '22 began restricting assignment to permission sets tied to permission set *licences* carrying those restricted object permissions; Winter '23 enforced that update and auto-removed the offending assignments. Only read and create standard-object permissions survive for guests. Always audit the full effective permission set of the guest user, not just the profile.
5. **Each site has its own guest user** — changing the guest profile on Site A does not affect Site B. If you have 3 sites, you must audit 3 guest profiles independently.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Guest user hardening checklist | Ordered remediation items for each site: profile permissions, FLS, guest sharing rule review, Apex review |
| Apex exposure report | List of @AuraEnabled/@RestResource classes reachable from guest sessions with `with sharing` and `WITH USER_MODE` status |
| Guest sharing rule inventory | Rule-by-rule table showing object, criteria, records matched, business justification, and required change (guest OWD is Private everywhere and is not a variable) |

---

## Related Skills

- security/experience-cloud-security — authenticated external user security, sharing sets, external OWD
- security/security-health-check — org-wide security posture assessment
- security/api-security-and-rate-limiting — controlling Apex REST exposure for unauthenticated endpoints
