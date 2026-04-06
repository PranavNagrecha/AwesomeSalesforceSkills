---
name: territory-api-and-assignment
description: "Territory2 API in Apex: programmatic territory member management (UserTerritory2Association, ObjectTerritory2Association), bulk assignment DML, and SOAP-based rule evaluation. NOT for ETM admin setup, territory model design, declarative assignment rules, or Opportunity territory configuration (use admin/enterprise-territory-management)."
category: apex
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Performance
  - Reliability
  - Security
triggers:
  - "how do I assign users to a territory in Apex"
  - "programmatically add accounts to a territory using ObjectTerritory2Association"
  - "bulk territory assignment rule evaluation from Apex"
  - "UserTerritory2Association DML insert not working in async context"
  - "how to remove a user from a territory via code without manual setup"
tags:
  - territory2
  - etm
  - UserTerritory2Association
  - ObjectTerritory2Association
  - territory-assignment
  - apex-dml
inputs:
  - Salesforce org with Enterprise Territory Management enabled and at least one active Territory2Model
  - Territory2 record IDs (territory members or accounts to assign)
  - User IDs or Account IDs to associate with territories
  - Whether bulk assignment rule evaluation is needed (requires SOAP API callout)
outputs:
  - Apex DML patterns for inserting/deleting UserTerritory2Association and ObjectTerritory2Association records
  - Guidance on when and how to invoke assignment rule evaluation via SOAP callout
  - Checker report flagging territory API anti-patterns in existing Apex classes
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-06
---

# Territory API and Assignment

This skill activates when a practitioner needs to manage Enterprise Territory Management (ETM) memberships or account territory associations programmatically in Apex — by inserting or deleting `UserTerritory2Association` or `ObjectTerritory2Association` records — or when bulk territory assignment rule evaluation must be triggered from code via a SOAP API callout. Use it for automated onboarding/offboarding of territory reps, data-migration-driven bulk account assignments, and any scenario where territory membership must be driven by code rather than manual setup.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm Enterprise Territory Management (ETM) is enabled in the org and that at least one Territory2Model is in Active state. ETM-related objects are not queryable until the feature is on and a model is active.
- Identify the `Territory2` record IDs you need to work with. You cannot use Territory2 names directly in DML; you must resolve IDs first.
- Determine whether you need to evaluate assignment rules after inserting `ObjectTerritory2Association` rows. Assignment rules do **not** run automatically on DML to `ObjectTerritory2Association` — rule evaluation requires a separate SOAP API callout.
- Know the session ID constraints: `UserInfo.getSessionId()` returns `null` in asynchronous contexts (Batch Apex, Queueable, Scheduled Apex, future methods). Any SOAP callout for rule evaluation must be made in a synchronous user context or from a Platform Event subscriber running in a synchronous context.
- Know the 200-record-per-SOAP-call limit for bulk assignment rule evaluation requests.

---

## Core Concepts

### UserTerritory2Association

`UserTerritory2Association` is the junction object that places a user into a `Territory2`. It supports standard Apex DML (`insert`, `delete`) and can be queried with SOQL. Key fields:

| Field | Type | Description |
|---|---|---|
| `Territory2Id` | ID | The territory the user belongs to |
| `UserId` | ID | The user being assigned |
| `RoleInTerritory2` | String | Picklist value (e.g., `Account Executive`, empty string for no role) |
| `IsActive` | Boolean | Read-only; controlled by the territory model state |

Inserting a `UserTerritory2Association` record is the programmatic equivalent of clicking "Add Users" in Setup > Territories. The insert fires standard field-level security checks but **does not fire Apex triggers** — there is no trigger support on `UserTerritory2Association`.

Duplicate inserts (same `Territory2Id` + `UserId` combination) produce a `DUPLICATE_VALUE` DML error. Use `Database.insert(list, false)` and inspect `SaveResult` errors to handle gracefully.

### ObjectTerritory2Association

`ObjectTerritory2Association` places an Account (the only supported object type) into a `Territory2`. Key fields:

| Field | Type | Description |
|---|---|---|
| `ObjectId` | ID | The Account ID being assigned |
| `Territory2Id` | ID | The territory the account belongs to |
| `AssociationCause` | String | `Territory` (manual/API) or `Territory2RuleAssociation` (rule-based; platform-controlled) |

Critical constraints:
- Standard DML (`insert`, `delete`) is supported.
- **Apex triggers do not fire on `ObjectTerritory2Association`** — not before-insert, not after-insert, nothing. You cannot use triggers to react to territory-account associations.
- Inserting with `AssociationCause = 'Territory'` creates a manual/API-driven association. Associations created by assignment rules use `Territory2RuleAssociation` (read-only from DML; set by the platform after rule evaluation).
- Only Account records can be the `ObjectId`. Associating Contacts, Opportunities, or other objects directly is not supported.

### Assignment Rule Evaluation

ETM assignment rules evaluate which territories an Account belongs to based on account field values (e.g., BillingState, Industry). Rule evaluation is **not triggered automatically** when you insert `ObjectTerritory2Association` rows or update Account fields — you must explicitly request evaluation.

From Apex, rule evaluation requires a SOAP API callout to the Territory2 evaluation service endpoint. The pattern is:

1. Obtain a valid session ID via `UserInfo.getSessionId()` — available only in synchronous user-context Apex.
2. Build an HTTP callout to `/services/Soap/s/<api-version>/` with the correct SOAP envelope.
3. Pass up to 200 Account IDs per request.
4. Parse the SOAP response to determine success or fault.

Because `UserInfo.getSessionId()` returns `null` in async Apex, bulk rule evaluation for large datasets is typically orchestrated via a Platform Event published from a batch `finish` method, consumed by a synchronous trigger or flow that performs the callout.

---

## Common Patterns

### Pattern 1: Bulk User Territory Assignment from Apex

**When to use:** A territory assignment change (e.g., sales rep territory realignment, new hire onboarding) must be applied to many users at once from a migration script, process automation, or an admin tool.

**How it works:**

1. Collect `(Territory2Id, UserId)` pairs to add.
2. Query `UserTerritory2Association` to find which pairs already exist (avoid `DUPLICATE_VALUE`).
3. Build `UserTerritory2Association` sObjects for net-new pairs.
4. Insert with `Database.insert(newAssociations, false)` and inspect `SaveResult` for any errors beyond `DUPLICATE_VALUE`.
5. For removals, query by `Territory2Id IN :ids AND UserId IN :userIds`, then delete.

```apex
public static void assignUsersToTerritory(Id territory2Id, List<Id> userIds) {
    Set<Id> existingUserIds = new Set<Id>();
    for (UserTerritory2Association uta :
             [SELECT UserId FROM UserTerritory2Association
              WHERE Territory2Id = :territory2Id AND UserId IN :userIds]) {
        existingUserIds.add(uta.UserId);
    }

    List<UserTerritory2Association> toInsert = new List<UserTerritory2Association>();
    for (Id uid : userIds) {
        if (!existingUserIds.contains(uid)) {
            toInsert.add(new UserTerritory2Association(
                Territory2Id = territory2Id,
                UserId = uid,
                RoleInTerritory2 = ''
            ));
        }
    }

    if (!toInsert.isEmpty()) {
        List<Database.SaveResult> results = Database.insert(toInsert, false);
        for (Database.SaveResult sr : results) {
            if (!sr.isSuccess()) {
                for (Database.Error err : sr.getErrors()) {
                    if (err.getStatusCode() != StatusCode.DUPLICATE_VALUE) {
                        throw new DmlException('Territory user assignment failed: ' + err.getMessage());
                    }
                }
            }
        }
    }
}
```

**Why not the alternative:** Using `insert` without `Database.insert(list, false)` rolls back the entire transaction on the first duplicate, which is common in realignment scenarios where some users are already assigned.

### Pattern 2: Manual Account-Territory Association via ObjectTerritory2Association

**When to use:** Accounts must be pinned to specific territories independent of assignment rules — for example, a data migration that preserves legacy territory assignments, or a key account that must always appear in an executive territory regardless of field values.

**How it works:**

1. Resolve the `Territory2Id` values for the target territories.
2. For each account, build an `ObjectTerritory2Association` with `AssociationCause = 'Territory'`.
3. Insert with `Database.insert(list, false)` to handle duplicates.
4. Query `ObjectTerritory2Association` to verify the associations are in place.

```apex
public static void pinAccountsToTerritory(Id territory2Id, List<Id> accountIds) {
    Set<Id> existingAccounts = new Set<Id>();
    for (ObjectTerritory2Association ota :
             [SELECT ObjectId FROM ObjectTerritory2Association
              WHERE Territory2Id = :territory2Id AND ObjectId IN :accountIds
              AND AssociationCause = 'Territory']) {
        existingAccounts.add(ota.ObjectId);
    }

    List<ObjectTerritory2Association> toInsert = new List<ObjectTerritory2Association>();
    for (Id acctId : accountIds) {
        if (!existingAccounts.contains(acctId)) {
            toInsert.add(new ObjectTerritory2Association(
                ObjectId = acctId,
                Territory2Id = territory2Id,
                AssociationCause = 'Territory'
            ));
        }
    }

    if (!toInsert.isEmpty()) {
        Database.insert(toInsert, false);
    }
}
```

**Why not the alternative:** Using assignment rules to pin accounts requires crafting a rule that matches a specific field value, which is fragile. Manual API associations via `AssociationCause = 'Territory'` are explicit and survive rule re-evaluation without being overwritten.

### Pattern 3: SOAP-Based Assignment Rule Evaluation

**When to use:** After updating Account fields that affect territory rule criteria, you need to re-evaluate which territories those accounts belong to — from a synchronous user context where a session ID is available.

**How it works:**

1. Collect Account IDs in chunks of at most 200.
2. Build the SOAP envelope with the session ID from `UserInfo.getSessionId()`.
3. Make an HTTP callout to the Territory2 evaluation endpoint.
4. Parse the SOAP response for success or fault elements.

```apex
public static void evaluateRulesForAccounts(List<Id> allAccountIds) {
    String sessionId = UserInfo.getSessionId();
    if (sessionId == null) {
        throw new IllegalStateException(
            'evaluateRules requires a synchronous user context; '
            + 'UserInfo.getSessionId() returned null.'
        );
    }

    String baseEndpoint = URL.getOrgDomainUrl().toExternalForm()
        + '/services/Soap/s/' + System.requestVersion().major + '.0';

    Integer batchSize = 200;
    for (Integer i = 0; i < allAccountIds.size(); i += batchSize) {
        List<Id> chunk = allAccountIds.subList(i, Math.min(i + batchSize, allAccountIds.size()));
        String body = buildSoapEnvelope(chunk);

        HttpRequest req = new HttpRequest();
        req.setEndpoint(baseEndpoint);
        req.setMethod('POST');
        req.setHeader('Content-Type', 'text/xml; charset=UTF-8');
        req.setHeader('SOAPAction', '""');
        req.setHeader('Authorization', 'Bearer ' + sessionId);
        req.setBody(body);

        HttpResponse resp = new Http().send(req);
        if (resp.getStatusCode() != 200) {
            throw new CalloutException('SOAP rule eval failed: ' + resp.getBody());
        }
    }
}
```

**Why not the alternative:** There is no native Apex method to trigger ETM assignment rule evaluation. The SOAP callout is the only supported mechanism from Apex code.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Add a user to a territory programmatically | Insert `UserTerritory2Association` with `Database.insert(list, false)` | Standard DML; pre-query existing assignments to avoid `DUPLICATE_VALUE` |
| Remove a user from a territory | Query `UserTerritory2Association` by `Territory2Id + UserId`, then delete | Standard DML delete; no recalculation hook needed |
| Pin an account to a territory regardless of rules | Insert `ObjectTerritory2Association` with `AssociationCause = 'Territory'` | Manual associations survive rule re-evaluation |
| Re-evaluate which territories an account belongs to after field changes | SOAP API callout in synchronous context, chunked to ≤200 IDs per call | No native Apex method exists; rule evaluation is not automatic |
| React to a new territory-account association in code | Cannot use triggers on `ObjectTerritory2Association`; dispatch Platform Events from the service layer | Apex triggers never fire on `ObjectTerritory2Association` DML |
| Evaluate rules in async Apex (Batch, Queueable) | Publish a Platform Event in `finish`; consume in synchronous subscriber | Session ID unavailable in async context; SOAP callout must be synchronous |
| Bulk assignment for >200 accounts needing rule evaluation | Chunk into batches of 200, call SOAP sequentially in a loop | 200-record limit per SOAP call; 100 callout limit per transaction |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. Confirm ETM is enabled and the Territory2Model is in Active state — query `Territory2Model` and verify `State = 'Active'` before attempting any DML on territory association objects.
2. Resolve Territory2 IDs — query `Territory2` by name, external ID, or hierarchy criteria to obtain the IDs you will use in association records.
3. Check for existing associations — query `UserTerritory2Association` or `ObjectTerritory2Association` before inserting to build a net-new list and avoid `DUPLICATE_VALUE` errors.
4. Perform DML with `Database.insert(list, false)` — inspect `SaveResult` errors, ignore `DUPLICATE_VALUE`, and surface all others.
5. If assignment rule evaluation is needed, confirm you are in a synchronous user context, chunk account IDs into groups of ≤200, and make the SOAP callout using `UserInfo.getSessionId()`.
6. Validate the result — query `ObjectTerritory2Association` or `UserTerritory2Association` after DML to confirm the records were created and spot partial failures.
7. Run `check_territory_api_and_assignment.py` against the Apex source to catch anti-patterns before deploying.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] ETM is enabled and at least one Territory2Model is in Active state in the target org
- [ ] All DML on `UserTerritory2Association` and `ObjectTerritory2Association` uses `Database.insert(list, false)` and inspects `SaveResult`
- [ ] No Apex triggers are relied upon to fire on `ObjectTerritory2Association` DML
- [ ] SOAP callout for rule evaluation is not called from async Apex (Batch, Queueable, Scheduled, future)
- [ ] SOAP requests are chunked to ≤200 account IDs per call
- [ ] `AssociationCause` is explicitly set to `'Territory'` for managed associations (never `'Territory2RuleAssociation'`)
- [ ] Deletion paths exist to remove stale associations when users leave territories or accounts are reassigned
- [ ] Session ID availability is verified before the SOAP callout path is invoked

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Apex triggers do not fire on ObjectTerritory2Association** — A trigger declared on `ObjectTerritory2Association` deploys without error but its body never executes — not on DML from Apex, not from Setup, not from rule evaluation. Use Platform Events dispatched from the service layer that writes the association.

2. **UserInfo.getSessionId() returns null in all async Apex** — This is the primary cause of SOAP-based rule evaluation failures in Batch Apex `execute`, Queueable `execute`, `@future` methods, and Scheduled Apex `execute`. Any code path that depends on `getSessionId()` for a SOAP callout must run in a synchronous request context.

3. **Assignment rules do not re-evaluate automatically on Account field updates or ObjectTerritory2Association DML** — Updating `BillingState` or any other rule-relevant field on an Account does not trigger rule re-evaluation. You must explicitly call the SOAP evaluation endpoint.

4. **ObjectTerritory2Association DML with AssociationCause = 'Territory2RuleAssociation' throws a runtime error** — This value is platform-controlled and cannot be set via Apex DML. Attempting to insert with this cause throws `DmlException: FIELD_INTEGRITY_EXCEPTION`. Always set `AssociationCause = 'Territory'` explicitly.

5. **200-record-per-SOAP-call limit for rule evaluation** — The SOAP API for territory rule evaluation caps at 200 Account IDs per request. Callers that pass more than 200 IDs receive a SOAP fault. Chunk the list into batches of ≤200 and make sequential requests.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| `UserTerritory2Association` DML snippet | Apex pattern for bulk user-to-territory assignment with duplicate handling |
| `ObjectTerritory2Association` DML snippet | Apex pattern for pinning accounts to territories with `AssociationCause = 'Territory'` |
| SOAP rule evaluation wrapper | Apex HTTP callout pattern for triggering ETM assignment rule evaluation (synchronous context only) |
| `check_territory_api_and_assignment.py` report | Static analysis of Apex classes for territory API anti-patterns |

---

## Related Skills

- admin/enterprise-territory-management — Use for ETM admin setup, territory model design, territory types, assignment rule configuration, and Opportunity territory assignment; this skill handles only the programmatic Apex API layer
- apex-managed-sharing — Use when territory membership drives record sharing via `__Share` objects; the two patterns are often combined
- callout-and-dml-transaction-boundaries — Use when the SOAP callout for rule evaluation must be combined with DML in the same transaction
- async-apex — Use when territory assignment operations exceed synchronous DML limits and must be moved to batch or queueable context (excluding SOAP callout steps)
