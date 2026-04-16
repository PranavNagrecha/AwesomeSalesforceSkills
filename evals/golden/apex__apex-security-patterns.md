# Eval: apex/apex-security-patterns

- **Skill under test:** `skills/apex/apex-security-patterns/SKILL.md`
- **Priority:** P0
- **Cases:** 3
- **Last verified:** 2026-04-16
- **Related templates:** `templates/apex/SecurityUtils.cls`, `templates/apex/BaseSelector.cls`
- **Related decision trees:** `standards/decision-trees/sharing-selection.md`

## Pass criteria

The AI must apply `with sharing`, CRUD/FLS enforcement (preferring `WITH USER_MODE`
or `Security.stripInaccessible`), and SOQL-injection-safe queries. Any
response that grants access beyond the running user without documented
justification, or uses string concatenation for SOQL binds, fails.

## Case 1 — `@AuraEnabled` method for an LWC — writing to Cases

**Priority:** P0

**User prompt:**

> "I need an `@AuraEnabled(cacheable=false)` method that lets a service rep
> close a Case from an LWC. Here's what I have — review for security."

**Context provided:**

```apex
public class CaseCloser {
    @AuraEnabled
    public static void closeCase(Id caseId, String reason) {
        Case c = [SELECT Id FROM Case WHERE Id = :caseId];
        c.Status = 'Closed';
        c.Reason = reason;
        update c;
    }
}
```

**Expected output MUST include:**

- Class missing `with sharing`.
- Query needs `WITH USER_MODE` (preferred) or CRUD/FLS check.
- `update` needs FLS enforcement (`Security.stripInaccessible` or
  `WITH USER_MODE` via `Database.update` overload).
- Input validation — `caseId` must be non-null and of SObject type `Case`.
- Use `AuraHandledException` with a safe message — never leak `e.getMessage()`.
- Audit that the Reason field's picklist value exists (or validate against
  a whitelist).
- Test that includes `System.runAs()` of a low-privilege user to prove
  enforcement works.

**Expected output MUST NOT include:**

- `without sharing` as the fix.
- `Security.stripInaccessible` with no check on the returned record.
- Using `DescribeSObjectResult.isUpdateable()` in a loop without caching.

**Rubric (0–5):**

- **Correctness:** All four gaps (sharing, query enforce, update enforce, input validate) identified.
- **Completeness:** Fixed code compiles and tests pass for non-admin user.
- **Bulk safety:** Not strictly bulk here — score 5 if a single input is handled correctly.
- **Security:** Core criterion — full marks only if every gap closed.
- **Citation of official docs:** Links to `WITH USER_MODE` + `stripInaccessible` docs.

**Reference answer (gold):**

```apex
public with sharing class CaseCloser {

    private static final Set<String> ALLOWED_REASONS = new Set<String>{
        'Resolved', 'Duplicate', 'Customer Withdrew'
    };

    @AuraEnabled(cacheable=false)
    public static void closeCase(Id caseId, String reason) {
        if (caseId == null) {
            throw new AuraHandledException('Case Id is required.');
        }
        if (caseId.getSObjectType() != Case.SObjectType) {
            throw new AuraHandledException('Invalid record type.');
        }
        if (!ALLOWED_REASONS.contains(reason)) {
            throw new AuraHandledException('Reason is not allowed.');
        }

        List<Case> rows = [
            SELECT Id
            FROM Case
            WHERE Id = :caseId
            WITH USER_MODE
            LIMIT 1
        ];
        if (rows.isEmpty()) {
            throw new AuraHandledException('Case not accessible.');
        }

        Case toUpdate = new Case(Id = caseId, Status = 'Closed', Reason = reason);
        Database.update(toUpdate, AccessLevel.USER_MODE);
    }
}
```

"`WITH USER_MODE` on both the SOQL and the `Database.update` enforces CRUD + FLS against the running user. `with sharing` enforces row-level sharing. `ALLOWED_REASONS` is a whitelist — never let the client dictate picklist values. `AuraHandledException` with a safe message prevents stack-trace leaks."

## Case 2 — Dynamic SOQL with user-supplied filter

**Priority:** P0

**User prompt:**

> "I need to let an LWC pass in a search string for Account name. Right now
> I'm building the SOQL string from the input — is this safe?"

**Context provided:**

```apex
String q = 'SELECT Id, Name FROM Account WHERE Name LIKE \'%' + searchTerm + '%\'';
return Database.query(q);
```

**Expected output MUST include:**

- This is a SOQL injection vulnerability.
- Fix: use `String.escapeSingleQuotes()` at minimum, and preferably
  `Database.queryWithBinds` with a bind map (which the user's prompt
  doesn't leverage).
- Length + character whitelist on `searchTerm` — cap at 80 chars, reject
  newlines and backslashes.
- Use `WITH USER_MODE` so CRUD/FLS still enforced.
- Note that even LIKE with wildcards should be rate-limited or require
  `LIMIT` to avoid heap blow-up.

**Expected output MUST NOT include:**

- "It's fine if the user is authenticated" (wrong — SOQL injection is
  input-domain, not auth-domain).
- Using static SOQL (it can't accept dynamic filters the way the user wants).

**Rubric (0–5):**

- **Correctness:** Identifies injection.
- **Completeness:** Escaping + binds + length + LIMIT + user_mode.
- **Bulk safety:** LIMIT present in fixed query.
- **Security:** Lead criterion — full marks only with binds AND length cap.
- **Citation of official docs:** Links to Secure Coding Guide (SOQL Injection).

**Reference answer (gold):**

"Yes, that's classic SOQL injection — the user can close the quote and append
`OR Id != null` or similar. Fix:

```apex
@AuraEnabled(cacheable=true)
public static List<Account> searchAccounts(String searchTerm) {
    if (String.isBlank(searchTerm)) {
        throw new AuraHandledException('Search term required.');
    }
    if (searchTerm.length() > 80) {
        throw new AuraHandledException('Search term too long.');
    }
    if (!Pattern.matches('^[\\w\\s\\-\\.\']+$', searchTerm)) {
        throw new AuraHandledException('Invalid characters.');
    }

    String clean = '%' + String.escapeSingleQuotes(searchTerm) + '%';
    return Database.queryWithBinds(
        'SELECT Id, Name FROM Account WHERE Name LIKE :clean WITH USER_MODE LIMIT 100',
        new Map<String, Object>{ 'clean' => clean },
        AccessLevel.USER_MODE
    );
}
```

Binds (not string concat) are the right primary defense. `escapeSingleQuotes` is belt-and-braces. The whitelist regex rejects `%` and `_` wildcards the user shouldn't be setting themselves (prevents an attacker from crafting `%` to get all rows). LIMIT prevents heap blow-up on accidental broad matches."

## Case 3 — `without sharing` request for "admin bypass"

**Priority:** P0

**User prompt:**

> "An admin reported that a scheduled Apex class is not seeing records
> a specific user can't see. The admin wants me to add `without sharing`.
> Is that OK?"

**Expected output MUST include:**

- Challenge the requirement — "without sharing" is rarely the right answer.
- Ask: is this class run by a specific integration user whose sharing
  should apply? Elevate the user's access via permission sets or sharing
  rules instead.
- If truly system-level (data export, privacy fulfilment), document with
  an ADR and name the class to surface the elevation (e.g.
  `DataExport_WithoutSharing`).
- Ensure the method surface is minimal — never combine `without sharing`
  with `@AuraEnabled` or `@RestResource`.
- Require a reviewer sign-off on the PR for the elevation.
- Tests must still run `System.runAs()` with a normal user to verify
  normal-user paths are untouched.

**Expected output MUST NOT include:**

- Agreeing and switching to `without sharing` with no discussion.
- Recommending `WITH SYSTEM_MODE` in the query without also addressing
  class-level sharing.

**Rubric (0–5):**

- **Correctness:** Pushes back on the default ask.
- **Completeness:** Covers alternative access grants + ADR + naming + surface.
- **Bulk safety:** N/A — score 5 by default.
- **Security:** Lead criterion — must explain the blast radius of the elevation.
- **Citation of official docs:** Links to `with sharing` / `without sharing` docs.

**Reference answer (gold):**

"Push back before flipping the switch.

Questions first:

- Is this a scheduled job run as a named Integration user? If yes, the fix
  is to grant that user the necessary permission sets or criteria-based
  sharing rules — not to bypass sharing entirely.
- Does the job need to see ALL records of type X, including ones no human
  has access to (privacy fulfilment, anonymisation, global aggregation)?
  That's the one case where `without sharing` is defensible.

If it IS that case:

- Put it in a class named to surface the elevation —
  `DataExport_WithoutSharing` or similar. Anyone reading `git grep 'WithoutSharing'`
  should land on it.
- Add a top-of-file comment with a link to an ADR explaining why, and which
  business requirement it satisfies.
- Expose the minimum-viable entry point. Never `@AuraEnabled` or
  `@RestResource` a `without sharing` class.
- Require a second reviewer on the PR.

Tests: one scenario that proves the sharing bypass works (admin user), and
one that proves normal users still can't reach the data through their usual
LWCs/REST endpoints.

If the push-back answer is 'just do it', put in writing that the class
bypasses sharing by design and get product sign-off before merging."
