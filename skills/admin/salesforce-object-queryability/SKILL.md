---
name: salesforce-object-queryability
description: "Distinguish the six real reasons a Salesforce query can 'fail', and the protocol for diagnosing before declaring: object doesn't exist, not queryable in edition, permission-denied, field-level errors, namespace prefix missing, API version mismatch. NOT for one object's own query restrictions, required filters or row caps - use apex/soql-object-limits-and-restrictions. NOT for a query that works but is slow - use data/soql-query-optimization."
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
  - "invalid_type error on a soql query"
  - "object appears in describe but the query returns 400"
  - "which permission do i need to query oauthtoken"
  - "select from openactivity fails with a 400"
  - "query works as admin but fails as the integration user"
  - "api_disabled_for_org when calling the rest api"
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
version: 1.1.0
author: Pranav Nagrecha
updated: 2026-09-04
---

# Salesforce Object Queryability

## Why this skill exists

A documented real-world incident: an AI agent diffing two users in a customer org tried to query `PermissionSetGroupAssignment` — an object that **does not exist in any Salesforce edition**. The query returned a 400 error. The agent collapsed this into "PSG not queryable in this org" and silently dropped the PSG dimension from the comparison. The resulting report was incomplete but looked complete.

The fix is disciplined failure classification. "Not queryable in this org" is a real category — but it's one of **six** possible reasons a query can fail, and the remediation is different for each.

## Questions to Ask Before Configuring

Ask these before writing a verdict. Each one collapses at least one of the six modes, and each one traces to a gotcha in `references/gotchas.md`.

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "Which surface issued the call — Data REST, Tooling, SOAP, Apex, Bulk — and does that surface own the object?" | An object on the wrong endpoint fails identically to an object that does not exist | The `surface` field of the verdict, and whether a retry on the other endpoint is even worth issuing (gotcha 2) |
| "Does the org's `/services/data/` listing report a newer version than the client is pinned to?" | An object introduced after your pinned version is invisible, not missing | Rules Mode 6 in or out in one unauthenticated call, before any per-object work (gotcha 6) |
| "Is the name present in Describe Global, and what does its `queryable` flag say?" | Presence and queryability are two different facts; the listing carries both | Splits `object-does-not-exist` from `not-queryable-on-this-surface` without a second call (gotcha 11) |
| "Which user ran it, and does the same query return rows for an admin?" | A 403 is a security control working, not a broken query | Turns a dead end into a named permission and a deployable grant (gotcha 16) |
| "Which managed-package namespaces are installed in this org?" | A bare name misses a prefixed object, and `getGlobalDescribe` keys carry the namespace | Separates `namespace-prefix-missing` from a genuine miss (gotchas 5, 13) |
| "Did the query return zero rows, or did it fail?" | These are opposite outcomes that read the same to a `if not results` branch | Stops the most common false verdict in the set (gotcha 3) |
| "Does the caller need the rows, or only to know whether rows exist?" | Decides whether a skipped dimension is fatal or merely noted | The `confidence_impact` value in the output envelope, instead of a blanket MEDIUM |

What a proper diagnosis adds over just reporting "the query failed": the caller gets one of eight closed verdicts with the probe evidence behind it, a named remediation they can act on, and an honest confidence — instead of a reason string that hides six different root causes and six different fixes.

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

Run `GET /services/data/vXX.0/sobjects/` to get the full list of accessible sObjects. Each entry carries a `queryable` boolean alongside `name` and `keyPrefix` — read it here rather than paying for a per-object describe. If the name **is** in the list but `queryable` is `false`, the object exists and has no `query()` call: that is `not-queryable-on-this-surface`, and no permission grant will change it (see `references/gotchas.md` gotcha 11). If the name isn't in the list:

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

Describe does **not** report a minimum API version. Get it from two places instead: `GET /services/data/` (unauthenticated) for the newest version the org serves, and the Object Reference's per-object sentence — "This object is available in API version N.0 and later" — for the object's floor. If the object appears in Describe Global at the org's newest version but not at yours, the verdict is `api-version-too-old`; bump and retry. The server says the same thing on a 409: "Check that the API version is compatible with the resource you're requesting."

### Step 6 — Verify the field projection

If the error is `INVALID_FIELD`, the object exists but the field list has a bad entry. Retry with `SELECT Id FROM <Object> LIMIT 1` to confirm the object works, then narrow down the bad field via binary search on the projection.

## Recommended Workflow

1. **Open the worksheet and capture the failure verbatim.** Start
   `templates/salesforce-object-queryability-template.md` § 1: object name as
   written, full query string, surface, client API version, running user, HTTP
   status, `errorCode`, `message`. A blank row here is a re-run, not a guess.
2. **Answer the seven questions above** into § 2 of the worksheet. Several modes
   fall out before any probe runs — a pinned version below the org's newest, or a
   namespace you had not accounted for.
3. **Run the six probes in order** using `references/metadata-examples.md` block 1
   (curl: Versions → Describe Global → sObject Describe → query) or block 2 (the
   Apex anonymous script, when you have no API session but do have a dev console).
   Record all six results in § 3, including `skip` with its reason.
4. **Pick one verdict from the closed vocabulary** in § 4 and write the evidence
   lines in § 5. Check it against the mode-specific traps in
   `references/gotchas.md` — especially 11 (`queryable: false` on an object that
   is present), 15 (an un-filterable field on a queryable object) and 16
   (`API_DISABLED_FOR_ORG` masquerading as a per-object result).
5. **Convert the worksheet into the verdict record** — the YAML shape in
   `references/metadata-examples.md` block 6 — and lint it:
   `python3 scripts/check_salesforce_object_queryability.py verdicts/<object>.verdict.yaml`.
   The checker rejects a free-text verdict, a missing probe, and a verdict that
   contradicts its own checks.
6. **If the verdict is `permission-denied`, produce the grant, not just the
   finding.** Deploy the permission-set fragment in block 3 (only the permissions
   the object's *Special Access Rules* actually name), then confirm coverage with
   `python3 scripts/check_salesforce_object_queryability.py --manifest-dir force-app/main/default`
   before the deploy.
7. **Emit the classification into the caller's output envelope** under
   `dimensions_compared` or `dimensions_skipped`, carrying the verdict, the
   evidence, and a `retry_hint`. Never silent-skip; never ship the bare string
   "not queryable in this org".

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

- REST API Developer Guide — *Describe Global* (`/services/data/vXX.X/sobjects/`), whose per-object entry carries `queryable`, `keyPrefix` and the describe URLs: https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/resources_describeGlobal.htm
- REST API Developer Guide — *Status Codes and Error Responses*, for the 400/403/404/409/500/503 split and the `NOT_FOUND` / `INSUFFICIENT_ACCESS` / `INVALID_FIELD` payload shapes quoted in this skill: https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/errorcodes.htm
- REST API Developer Guide — *sObject Describe* (`/services/data/vXX.X/sobjects/sObject/describe/`): https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/resources_sobject_describe.htm
- Object Reference for the Salesforce Platform — the *Supported Calls*, *Special Access Rules* and "available in API version N.0 and later" conventions that decide whether an object can be queried at all and by whom: https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf
- Apex Developer Guide — *Accessing All sObjects* (`Schema.getGlobalDescribe` namespace-prefixed keys from API 28.0) and *Dynamic SOQL* (`AccessLevel.USER_MODE` from API 55.0): https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf
- Metadata API Developer Guide — `PermissionSet` and `PermissionSetUserPermission`, for the deployable grant in `references/metadata-examples.md`: https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf
- Salesforce Developer Limits and Allocations Quick Reference — Apex governor limits and the SOAP `describeSObjects()` 100-object cap that bound a probe run.

Fuller grounding, with the claim each source supports, is in `references/well-architected.md`.

---

## Reference Files

| File | Read it when |
|---|---|
| `references/metadata-examples.md` | Running the probes: the curl sequence and its per-mode error payloads, the Apex six-check script, the deployable permission-set grant plus `package.xml` and `sf` commands, the licence/edition and API-version probes, and the verdict-record shape |
| `references/gotchas.md` | The failure looks like one mode and is another — an object present in the listing that has no `query()`, a field that is un-filterable on a queryable object, a namespaced describe key, or an org-level API gap reported once per object |
| `references/examples.md` | Sizing a real incident against the six modes, including the hallucinated-object case this skill was written from |
| `references/llm-anti-patterns.md` | Reviewing AI-generated diagnosis before acting on it — especially any output containing the string "not queryable in this org" |
| `references/well-architected.md` | Justifying classify-then-remediate over retry-and-hope, or locating the official source behind a claim here |
| `templates/salesforce-object-queryability-template.md` | Workflow steps 1–5 — the worksheet that becomes the verdict record |
| `scripts/check_salesforce_object_queryability.py` | Workflow step 5 (lint the verdict) and step 6 (`--manifest-dir` setup-object coverage before a permission deploy) |

---

## Related Skills

- `admin/data-model-documentation` — owns describe-based object and field inventories; come here only when one of its queries fails
- `admin/permission-set-architecture` — designs the CRUD/FLS grant this skill's `permission-denied` verdict asks for
- `security/record-access-troubleshooting` — a query that succeeds and returns fewer rows than expected is sharing, not queryability
- `data/soql-query-optimization` — a query that works but is slow, or times out on an LDV object
- `apex/soql-object-limits-and-restrictions` — one object's own required filters, row caps and query restrictions once it is confirmed queryable
- `apex/soql-security` — enforcing user mode and field access inside the query rather than diagnosing after the fact
- `apex/apex-dynamic-soql-binding-safety` — building the probe query string without opening an injection path
- `data/sosl-search-patterns` — when the right answer is search rather than a `FROM` clause on an object that has no `query()`
