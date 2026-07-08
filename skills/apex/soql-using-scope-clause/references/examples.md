# Examples — SOQL USING SCOPE Clause

All SOQL/Apex below is illustrative scaffolding authored from the official SOQL and
SOSL Reference and the Scoping Rules guide. Replace object and field names with your own.
`USING SCOPE` is "Available in API version 32.0 and later"; the docs give no GA/Beta/Pilot
label for the clause itself.

## Example 1: "My open cases" without a hardcoded OwnerId

**Context:** an LWC controller must list the running user's own open cases.

**Problem:** `WHERE OwnerId = :UserInfo.getUserId()` only matches direct ownership and has to
be re-derived everywhere; it also does nothing for security on its own.

**Solution:**

```apex
public with sharing class CaseSelector {
    // Cases owned by the running user. USING SCOPE goes after FROM, before WHERE.
    // WITH USER_MODE (Summer '23+) is what actually enforces CRUD/FLS/sharing.
    public List<Case> selectMyOpenCases() {
        return [
            SELECT Id, CaseNumber, Subject, Status
            FROM Case
            USING SCOPE mine
            WHERE IsClosed = false
            WITH USER_MODE
            ORDER BY CreatedDate DESC
        ];
    }
}
```

**Why it works:** `mine` resolves to the running user's owned records at query time, and the
clause is positioned correctly (after `FROM`, before `WHERE`). Security is added separately
because scope is a filter, not enforcement.

---

## Example 2: Dynamic, describe-guarded scoped query in a selector

**Context:** a selector chooses the scope at runtime and must not blow up on objects that
don't support it. This selector extends the canonical base class in
`templates/apex/BaseSelector.cls`.

**Problem:** hardcoding a scope an object doesn't support throws; and building the string in
the wrong clause order is a common runtime failure.

**Solution:**

```apex
public with sharing class ScopedAccountSelector extends BaseSelector {

    private static final Set<String> ALLOWED_SCOPES = new Set<String>{
        'delegated', 'everything', 'mine', 'mine_and_my_groups',
        'my_territory', 'my_team_territory', 'scopingRule', 'team'
    };

    public List<Account> selectByScope(String scope) {
        if (!ALLOWED_SCOPES.contains(scope)) {
            throw new SelectorException('Unsupported USING SCOPE value: ' + scope);
        }
        // scope is validated against a fixed allow-list, so it is safe to concatenate.
        // Clause order is enforced by construction: FROM ... USING SCOPE ... WHERE ...
        String soql =
            'SELECT Id, Name, OwnerId ' +
            'FROM Account ' +
            'USING SCOPE ' + scope + ' ' +
            'WHERE CreatedDate = THIS_YEAR';
        return (List<Account>) Database.query(soql, userMode());
    }
}
```

**Why it works:** the scope token is validated against a closed allow-list before
concatenation (never bind user input directly into `USING SCOPE`), `Database.query(..., userMode())`
runs the query in user mode, and the string is assembled in the mandated clause order. In
production, confirm the object supports the requested scope via `sObject Describe` rather than
relying only on the allow-list.

---

## Example 3: Approval work items awaiting me or my queues

**Context:** a "My Approvals" component needs pending approval work items for the running user
*and* their queues.

**Problem:** joining `ProcessInstanceWorkItem` to queue membership by hand is verbose and easy
to get wrong.

**Solution:**

```apex
List<ProcessInstanceWorkItem> pending = [
    SELECT Id, ActorId, ProcessInstance.TargetObjectId, ProcessInstance.Status
    FROM ProcessInstanceWorkItem
    USING SCOPE mine_and_my_groups
    WITH USER_MODE
];
```

**Why it works:** `mine_and_my_groups` is documented to include "records assigned to the user
running the query and the user's queues." Note the hard constraint: this scope "applies only to
the `ProcessInstanceWorkItem` object" — using it elsewhere is invalid.

---

## Example 4: Scoping-rule SOQL operator (EVERYTHING everywhere)

**Context:** a scoping rule filters which records a user can see, using the SOQL operator in its
record criteria. This feature is "Available in: Lightning Experience in Performance and Unlimited
Editions."

**Problem:** the SOQL operator has a strict rule — "The SELECT statement, including nested SELECT
statements, must include USING SCOPE EVERYTHING. USING SCOPE EVERYTHING is the only valid scope
clause syntax for scoping rules." Omitting it (or using `mine`) fails.

**Solution:** apply `USING SCOPE EVERYTHING` to the outer *and* every nested `SELECT`:

```
SOQL(Id, SELECT AccountId
         FROM BranchUnitCustomer
         USING SCOPE EVERYTHING
         WHERE BranchUnitId IN (
             SELECT CurrentBranchId
             FROM Banker
             USING SCOPE EVERYTHING
             WHERE UserOrContactId = $User.Id
         ))
```

**Why it works:** every `SELECT` carries the mandated `USING SCOPE EVERYTHING`, satisfying the
scoping-rule requirement. The operator supports `$User.Id` (but not other `$User` fields) and does
not support dynamic queries.

---

## Anti-Pattern: treating USING SCOPE mine as record-level security

**What practitioners do:** ship `SELECT ... FROM Opportunity USING SCOPE mine` from a `without
sharing` class and call it "users only see their own opportunities."

**What goes wrong:** `mine` filters by ownership but enforces no FLS/CRUD/sharing. A field the
user shouldn't read still returns, and the pattern breaks the moment the requirement is "records
shared with me," which ownership scope does not cover.

**Correct approach:** keep `USING SCOPE mine` for the *audience* filter and add `WITH USER_MODE`
(or `with sharing` + `SecurityUtils` CRUD/FLS checks) for the *security* boundary — they are
orthogonal and you usually want both.
