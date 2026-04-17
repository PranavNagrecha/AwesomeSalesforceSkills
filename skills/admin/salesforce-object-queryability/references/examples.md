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

**Context:** Agent queries `User` as a restricted portal user; gets 403.

**Classification:** Mode 3 — permission denied.

**Remediation:** This is signal, not noise. Record the permission gap in the output (this is itself useful info about the running user). Don't silently continue.

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
