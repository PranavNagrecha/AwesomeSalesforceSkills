# Examples — Salesforce Object Queryability

## Example 1: The ExampleOrg incident — hallucinated object name

**Context:** An AI agent running `user-access-diff` against an ExampleOrg sandbox tried to query `PermissionSetGroupAssignment`.

**What happened:**
```
Query: SELECT Id, AssigneeId FROM PermissionSetGroupAssignment WHERE AssigneeId = '005...'
Response: 400 — INVALID_TYPE: "sObject type 'PermissionSetGroupAssignment' is not supported."
```

The agent collapsed this to *"PermissionSetGroupAssignment is not queryable in this org"* and dropped the PSG dimension from the comparison. Report looked complete; wasn't.

**Classification:** Mode 1 — object doesn't exist. The hallucinated name is a compound of `PermissionSetAssignment` + `PermissionSetGroup`.

**Correct remediation:**
1. Call `GET /services/data/v62.0/sobjects/` → scan list → confirm no object by that name exists.
2. Recognize that the real query for PSG membership is:
   ```sql
   SELECT PermissionSetId, PermissionSetGroupId, PermissionSet.Name
   FROM PermissionSetAssignment
   WHERE AssigneeId = '005...'
     AND PermissionSetGroupId != null
   ```
3. Flatten PSG components separately via `PermissionSetGroupComponent` (queryable, exists in every org with PSGs enabled).

**Agent output should have been:**
```json
{
  "dimensions_skipped": [],
  "dimensions_compared": ["...", "psg-components"],
  "confidence": "HIGH"
}
```

NOT:
```json
{
  "dimensions_skipped": [{"dimension": "psg", "reason": "not queryable"}],
  "confidence": "MEDIUM"
}
```

---

## Example 2: Feature-gated — Territory2

**Context:** Agent queries `UserTerritory2Association` on an org without Enterprise Territory Management enabled.

**Response:** `400 INVALID_TYPE: "sObject type 'UserTerritory2Association' is not supported."`

**Classification:** Mode 2 — not queryable in this edition (feature-gated).

**Remediation:** Record in `dimensions_skipped` with `confidence_impact: NONE` (territory is optional for most comparisons) and `retry_hint: "Enable Enterprise Territory Management to include this dimension."` Do NOT lump with Mode 1.

---

## Example 3: Managed-package namespace

**Context:** Agent queries `fin__Payment__c` in an ExampleOrg HED org but uses `Payment__c` (bare name).

**Response:** `400 INVALID_TYPE`.

**Classification:** Mode 5 — namespace prefix missing.

**Remediation:** Check `/sobjects/` listing. Find `fin__Payment__c`. Retry query with correct prefix.

---

## Example 4: Tooling API vs Data API

**Context:** Agent queries `FlowDefinition` via the Data API (`/services/data/v62.0/query`).

**Response:** `400 INVALID_TYPE`.

**Classification:** Mode 1 (wrong endpoint — Data API doesn't expose this).

**Remediation:** Retry via Tooling API: `/services/data/v62.0/tooling/query`. Same query, different endpoint.

---

## Example 5: Permission-denied (not a query bug)

**Context:** Agent queries `OauthToken` as a probe user whose profile has API
Enabled but not Customize Application. The object *is* in the org's listing.

**What the two calls return.** The describe succeeds and the query does not —
that gap is the whole diagnosis:

```http
GET /services/data/v67.0/sobjects/          -> 200; entry {"name":"OauthToken","queryable":true}
GET /services/data/v67.0/query/?q=SELECT+Id+FROM+OauthToken+LIMIT+1
                                            -> 403
{ "message": "You do not have permission to view this record.",
  "errorCode": "INSUFFICIENT_ACCESS" }
```

**Classification:** Mode 3 — permission denied. `queryable: true` in the listing
rules out Modes 1, 2, 5 and 6 in a single call; the 403 rules out Mode 4.

**Why this user and not another.** The Object Reference states the rule on the
object itself: "Users with the Customize Application permission see all tokens for
all users in the org. Otherwise, you see only your own tokens"
(`object_reference.txt` L189605–L189606). So the same query run by an admin
returns rows, and run by the probe user returns 403 — the object never moved.

**Remediation:** This is signal, not noise. Record the permission gap in the
output (it is itself useful information about the running user), name the
permission the Object Reference demands, and don't silently continue. The
deployable grant is in `references/metadata-examples.md` block 3.

---

## Anti-Pattern: Generic "not queryable" reason string

Agent output:
```json
{"dimensions_skipped": [{"dimension": "x", "reason": "not queryable in this org"}]}
```

What it hides: typo, edition gap, permission gap, namespace gap, API version, wrong endpoint — six different things, six different remediations. Fix: classify, then report.

---

## Anti-Pattern: Retry loop without classification

Agent loops the same broken query 200 times (once per record). Every iteration produces the same 400. Nothing resolves.

Fix: first failure → classify → either retry ONCE with the fix OR break out.
