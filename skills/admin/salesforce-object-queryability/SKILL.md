---
name: salesforce-object-queryability
description: "Distinguish the six real reasons a Salesforce query can 'fail', and the protocol for diagnosing before declaring. Covers: object doesn't exist, not queryable in edition, permission-denied, field-level errors, namespace prefix missing, API version mismatch. NOT for SOQL performance tuning (use soql-optimization-patterns). NOT for Bulk API payload issues (use bulk-api-2-patterns)."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
  - Security
tags:
  - soql
  - sobject
  - tooling-api
  - edition-limits
  - api-version
  - diagnostics
  - agent-discipline
triggers:
  - "soql query failed but i do not know why"
  - "sobject not queryable in this org"
  - "tooling api 400 error"
  - "permission set group assignment not queryable"
  - "what is the difference between empty rows and a failed query"
  - "agent hallucinated sobject name"
inputs:
  - The exact query that failed
  - The API response (error code, message, full body if available)
  - Org edition (Developer, Enterprise, Unlimited, Professional, etc.)
  - Whether query was issued via Tooling API vs Data API
  - Running user's profile or permission set
outputs:
  - A classification — which of the six failure modes the query hit
  - Next step per classification (retry, escalate, skip, abort)
  - A diagnostic log line the agent can emit in its output envelope
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-17
---

# Salesforce Object Queryability

## When to use this skill

Activate when:

- A SOQL or Tooling-API query returned an error and you need to know why.
- An agent or script is about to declare "object not queryable in this org" — and you need to verify the claim before trusting it.
- A multi-dimension agent (`user-access-diff`, `org-drift-detector`) is deciding whether to skip a dimension OR retry with a corrected query.
- A reviewer is auditing an agent's output envelope for silently-dropped dimensions.

Do NOT use this skill for:
- SOQL performance / selectivity tuning (use `skills/apex/soql-optimization-patterns`).
- Bulk API 2.0 payload issues (use `skills/data/bulk-api-2-patterns`).
- Authentication / session issues (use `skills/integration/authentication-patterns`).

## Why this skill exists

A documented real-world incident: an AI agent diffing two users in a customer org tried to query `PermissionSetGroupAssignment` — an object that **does not exist in any Salesforce edition**. The query returned a 400 error. The agent collapsed this into "PSG not queryable in this org" and silently dropped the PSG dimension from the comparison. The resulting report was incomplete but looked complete.

The fix is disciplined failure classification. "Not queryable in this org" is a real category — but it's one of **six** possible reasons a query can fail, and the remediation is different for each.

## The six failure modes

| # | Classification | Cause | HTTP status | Error code (typical) | Correct response |
|---|---|---|---|---|---|
| 1 | **Object doesn't exist** | API name typo; wrong case; missing namespace prefix; misremembered object | 400 | `INVALID_TYPE` / `INVALID_TABLE` | **Fix the query.** Do not report "not queryable." |
| 2 | **Not queryable in this edition** | Feature-gated object (e.g., Territory2 requires Enterprise Territory Management enabled) | 400 | `INVALID_TYPE` | **Check edition / feature flag.** Report as edition-limited, not "not queryable." |
| 3 | **Permission denied** | Running user lacks access to the sObject / fields | 403 | `INSUFFICIENT_ACCESS_OR_READONLY` | **Retry as a user with access, OR report permission gap.** Not a query bug. |
| 4 | **Field-level error** | Querying a field that doesn't exist / is inaccessible; bad filter clause | 400 | `INVALID_FIELD` | **Fix the field list.** Agent should retry with corrected projection. |
| 5 | **Namespace prefix missing** | Managed-package object/field queried without `namespace__` prefix | 400 | `INVALID_TYPE` or `INVALID_FIELD` | **Add the namespace prefix.** Introspect via `sObject Describe` to find it. |
| 6 | **API version too old** | Object was introduced in a newer API version than the client is using | 400 | `INVALID_TYPE` | **Bump API version** and retry. |

**`INVALID_TYPE` is the most ambiguous code** — it covers modes 1, 2, 5, and 6. The agent must do follow-up checks before declaring which.

## Diagnostic protocol

When a query fails, run these checks in order:

### Step 1 — Capture the full error payload

Don't collapse to "not queryable." Capture the HTTP status + `errorCode` + `message`. Salesforce error payloads are structured:

```json
{
  "errorCode": "INVALID_TYPE",
  "message": "sObject type 'PermissionSetGroupAssignment' is not supported."
}
```

The `message` field disambiguates in most cases ("not supported" vs "insufficient access" vs "field does not exist").

### Step 2 — Verify the object name exists

Run `GET /services/data/vXX.0/sobjects/` to get the full list of accessible sObjects. If the name isn't in the list:

- If it's close to a real name → typo (Mode 1). Fix and retry.
- If it's a managed-package object → probably missing namespace prefix (Mode 5).
- If it's a feature-gated object → edition limit (Mode 2).

### Step 3 — Check Tooling API vs Data API

Some objects (`PermissionSet`, `FlowDefinition`, `ApexClass`) are queryable via Tooling API but NOT the Data API, and vice versa. If the query hit the wrong endpoint, `INVALID_TYPE` fires.

Quick reference:
- Data API: `User`, `Account`, `Case`, `Contact`, `PermissionSetAssignment`, `ObjectPermissions`, `FieldPermissions`, `GroupMember`, `PermissionSetGroupComponent`.
- Tooling API only: `ApexClass`, `ApexTrigger`, `FlowDefinition`, `ValidationRule`, `RoutingConfiguration`, most metadata-describe objects.

### Step 4 — Check running-user access

`GET /services/data/vXX.0/sobjects/<SObjectName>/describe` — if it returns but the query still fails with `INSUFFICIENT_ACCESS_OR_READONLY`, the user's profile/PS lacks access (Mode 3).

### Step 5 — Check API version

The object's `urls.sobject` + `keyPrefix` fields in describe tell you the minimum API version. If the client is older, bump to the version that introduced the object.

### Step 6 — Verify the field projection

If the error is `INVALID_FIELD`, the object exists but the field list has a bad entry. Retry with `SELECT Id FROM <Object> LIMIT 1` to confirm the object works, then narrow down the bad field via binary search on the projection.

## Recommended Workflow

1. **Capture the full error** — don't discard the response body.
2. **Classify against the six modes** using the decision table.
3. **Act per mode** — retry, remediate, or escalate. Never silent-skip.
4. **Record the classification** in the agent's output envelope under `dimensions_skipped` with a clear `reason` string.
5. **Document the reasoning** — "not queryable" alone is insufficient; explain WHY and what the caller could do to unblock.

## Key patterns

### Pattern 1 — Agent output-envelope discipline

Agents comparing multi-dimension surfaces (user access, org state, deployment history) MUST declare which dimensions were compared vs skipped, with reason codes:

```json
{
  "dimensions_compared": ["profile", "permission-sets", "object-crud", "system-perms"],
  "dimensions_skipped": [
    {
      "dimension": "psg-components",
      "reason": "PermissionSetGroupComponent query returned INVALID_TYPE via the /services/data endpoint; retried via /services/data/v62.0/query and succeeded",
      "confidence_impact": "NONE",
      "retry_hint": "Bump sf CLI to 2.38+"
    }
  ]
}
```

Compare to the bad pattern:

```json
{
  "dimensions_skipped": [
    {"dimension": "psg-components", "reason": "not queryable in this org"}
  ]
}
```

The bad version hides six possible root causes behind one string. The good version names the cause and gives the caller a remediation.

### Pattern 2 — The `INVALID_TYPE` diagnostic ladder

When the error code is `INVALID_TYPE`:

```
Step 1: Is the name in /sobjects/ listing?
  Yes  → Mode 3 (permission) or Mode 6 (API version)
  No   → continue

Step 2: Is the name a managed-package object in this org?
  Yes  → Mode 5 (namespace missing)
  No   → continue

Step 3: Is the name gated by an edition/feature?
  Yes  → Mode 2 (edition limit)
  No   → continue

Step 4: Is the name close to a real sObject name (Levenshtein ≤ 2)?
  Yes  → Mode 1 (typo — suggest the real name)
  No   → Mode 1 (hallucinated; the object does not exist)
```

### Pattern 3 — Non-existent objects agents commonly hallucinate

AI agents pattern-match on naming conventions and occasionally produce plausible-looking sObject names that don't exist. Known hallucinations seen in the wild:

| Hallucinated name | Real object |
|---|---|
| `PermissionSetGroupAssignment` | `PermissionSetAssignment` (with `PermissionSetGroupId != null`) |
| `UserPermissionSetGroup` | `PermissionSetAssignment` (PSG linkage on this object) |
| `SharingRuleHierarchy` | `SharingRules` + separate hierarchy calculation via describe |
| `CustomPermissionAssignment` | `SetupEntityAccess` where `SetupEntityType='CustomPermission'` |
| `FlowInterviewHistory` | `FlowInterviewLog` |

Agents should validate any sObject name against `/sobjects/` describe before executing a query, especially when the name looks like a reasonable extrapolation from another name.

## Bulk safety

This skill is about diagnosis, not bulk writes. Only bulk-relevant note: when a query fails mid-iteration, do NOT continue looping with the same broken query 200 times. Break out, classify, and either retry once with the fix or propagate the failure.

## Error handling

Every query-fail branch in agent code should log:
- The query string
- The endpoint (Data API vs Tooling API)
- The full error response
- The classification (one of the six modes)
- The retry/remediation action taken

Silent `try/except: pass` is the root cause of the "looks complete but isn't" failure mode. Banning it in agent code is the single most valuable hygiene rule.

## Well-Architected mapping

- **Reliability** — distinguishing "query failed" from "query returned zero rows" from "object doesn't exist" is load-bearing for any agent that operates on live-org data. Collapsing them produces silently-incomplete reports.
- **Operational Excellence** — runbooks for query failures save hours of debugging. A classified error tells the next engineer exactly which of the six remediation paths to take.
- **Security** — a `permission-denied` error is meaningful signal (the agent is running as a user who shouldn't see something). Swallowing it masks a security control working correctly.

## Gotchas

See `references/gotchas.md`.

## Official Sources Used

- Salesforce Developer — REST API Error Codes: https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/errorcodes.htm
- Salesforce Developer — Tooling API Guide: https://developer.salesforce.com/docs/atlas.en-us.api_tooling.meta/api_tooling/
- Salesforce Developer — sObject Describe: https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/resources_sobject_describe.htm
- Salesforce Architects — API Versioning Strategy: https://architect.salesforce.com/
- Salesforce Developer — SOAP API Status Codes: https://developer.salesforce.com/docs/atlas.en-us.api.meta/api/sforce_api_calls_concepts_core_data_objects.htm
