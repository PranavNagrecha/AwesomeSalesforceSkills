---
name: apex-named-credentials-patterns
description: "Use when writing Apex that calls out to external endpoints via Named Credentials, working with custom header formula tokens ({!$Credential.OAuthToken}), querying per-user auth state through the UserExternalCredential SObject, or diagnosing why Named Credential callouts fail. Trigger keywords: 'callout: prefix', 'named credential header formula', 'UserExternalCredential', 'External Credential per-user principal', 'Named Credential oauth token apex'. NOT for Named Credential setup in the Salesforce Setup UI — use integration/named-credentials-setup. NOT for general HTTP callout mechanics (HttpRequest, HttpResponse, mock patterns) — use integration/callouts-and-http-integrations."
category: apex
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
triggers:
  - named credential custom header formula apex how to pass oauth token
  - per-user oauth named credential apex token inspection
  - UserExternalCredential query apex check if user has authenticated
  - callout colon prefix named credential apex syntax
  - enhanced model external credential vs named credential apex confusion
  - named credential not working with continuation async callout
tags:
  - named-credentials
  - callouts
  - oauth
  - apex-callout
  - external-credential
inputs:
  - "Named Credential API name and model (legacy vs. enhanced)"
  - "Auth type in use: OAuth, Basic, or Custom Headers"
  - "Whether per-user (Named Principal) or org-wide (Per-User Principal) auth is needed"
  - "Any custom header formula tokens required in the callout"
outputs:
  - "Apex callout implementation using Named Credential with correct syntax"
  - "Custom header formula token usage for injecting OAuth tokens or credentials"
  - "UserExternalCredential SOQL query for per-user token status checks"
  - "Guidance on Enhanced vs. Legacy model differences affecting Apex code"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-19
---

# Apex Named Credentials Patterns

Use this skill when writing Apex that makes authenticated outbound callouts through Named Credentials — covering the `callout:` URL prefix, custom header formula tokens for injecting OAuth or Basic auth values, the `UserExternalCredential` SObject API for per-user token inspection, and the behavioral differences between the legacy and enhanced Named Credential models that affect Apex code.

---

## Before Starting

- Is the org using the **legacy model** (single Named Credential with embedded auth config) or the **enhanced model** (External Credential for auth + Named Credential for endpoint, introduced Spring '22)?  The two models have different metadata shapes but the same `callout:` URL syntax in Apex.
- Does the use case require **per-user auth** (each user authenticates individually with OAuth) or **org-wide auth** (all users share one credential set)? Per-user auth requires querying `UserExternalCredential` to check whether a given user has an active token before making the callout.
- Are there **custom header fields** defined on the Named Credential that inject OAuth tokens or credentials? These use the `{!$Credential.*}` formula syntax and only resolve at callout time — they are not available inside Apex code at compile or run time.
- Named Credentials automatically exempt the endpoint host from Remote Site Settings. In **managed packages**, the subscriber org may still need Remote Site Settings if the Named Credential is not part of the package. Confirm the distribution model before relying on this exemption.

---

## Core Concepts

### Legacy vs. Enhanced Named Credential Model

The **legacy model** combines the endpoint URL and authentication configuration in a single Named Credential metadata record. The **enhanced model** (Spring '22+) separates them:

- **External Credential** — holds the authentication protocol, OAuth flow configuration, principals, and per-user identity mapping.
- **Named Credential** — holds the endpoint URL and references an External Credential.

From **Apex code, both models use exactly the same `callout:` URL syntax**. The difference is invisible to the Apex developer in normal callout code. The split matters when you need to inspect or manage per-user auth state via the `UserExternalCredential` SObject (enhanced model only) or when configuring multiple Named Credentials that share the same auth config.

### The `callout:` URL Prefix

Named Credentials are referenced in Apex via the `callout:` URL prefix. The syntax is:

```
callout:<Named_Credential_API_Name>[/path][?query_string]
```

The Named Credential API name is case-sensitive. The trailing path is optional; the Named Credential endpoint URL and the Apex-supplied path are concatenated at runtime by the platform.

```apex
HttpRequest req = new HttpRequest();
req.setEndpoint('callout:MyServiceNC/api/v2/customers');
req.setMethod('GET');
HttpResponse res = new Http().send(req);
```

The platform injects authentication headers, resolves formula tokens in custom headers, and validates Remote Site Settings on the endpoint automatically. **You must never construct the full endpoint URL with credentials hard-coded.**

### Custom Header Formula Tokens

Named Credential records (both models) support **custom header fields** that can embed runtime-resolved formula tokens. These are set in the Named Credential setup UI, not in Apex. At callout time, the platform evaluates these formulas and injects the resulting values as HTTP headers.

Available formula tokens (Apex Developer Guide — Named Credentials):

| Token | Resolves to |
|---|---|
| `{!$Credential.OAuthToken}` | The active OAuth access token for the current user or org-wide principal |
| `{!$Credential.Username}` | The username stored in the credential |
| `{!$Credential.Password}` | The password stored in the credential |

**Key constraint:** Formula tokens are evaluated by the platform at callout time on the server side. They **cannot be read back in Apex code** — you cannot call `System.Label` or any getter to obtain the resolved token value in your Apex logic. They are write-only from the Apex developer's perspective.

**Formula tokens are only valid inside Named Credential custom header fields.** Attempting to use `{!$Credential.OAuthToken}` inside an Apex string literal, a request body, or a URL path does not resolve — the literal string is sent verbatim.

### UserExternalCredential SObject (Enhanced Model)

The `UserExternalCredential` SObject exists only in orgs using the enhanced model. It records the per-user auth association between a Salesforce User and an External Credential Principal. Querying it lets Apex determine whether a specific user has an active (or any) token before initiating a callout on their behalf.

Key fields:

| Field | Description |
|---|---|
| `ExternalCredentialId` | 18-char ID of the External Credential record |
| `UserId` | 18-char ID of the Salesforce User |
| `PrincipalType` | `NamedPrincipal` or `PerUserPrincipal` |

A `UserExternalCredential` record existing for a user indicates the user has completed the OAuth flow. Absence means the user has not authenticated and the callout will fail with an auth error. Use this SObject to gate callouts or present the user with a re-authentication prompt.

### Callout Limits and Constraints

Named Credential callouts are subject to the same Apex callout limits as all other callouts (Apex Developer Guide — Callout Limits):

- Maximum callout timeout: **120 seconds** (10 seconds default if not explicitly set via `req.setTimeout()`).
- Maximum callouts per transaction: **100**.
- Named Credentials are **not compatible with the Continuation framework** (async Visualforce/Aura callouts). Continuation requires a full URL endpoint with Remote Site Settings; the `callout:` prefix is not supported.

---

## Common Patterns

### Callout With Named Credential and Custom OAuth Header Injection

**When to use:** The external API requires the OAuth access token in a custom header (e.g., `X-API-Token`) rather than the standard `Authorization` header, and the Named Credential has a custom header field with `{!$Credential.OAuthToken}` configured.

**How it works:** The Named Credential admin configures a custom header (e.g., `X-API-Token`) with the formula `{!$Credential.OAuthToken}` in the Setup UI. In Apex, the developer references the Named Credential with the standard `callout:` prefix. The platform evaluates the formula and injects the header automatically.

```apex
public class CustomerServiceCallout {
    public static HttpResponse fetchCustomer(String customerId) {
        HttpRequest req = new HttpRequest();
        req.setEndpoint('callout:CustomerServiceNC/api/v1/customers/' + customerId);
        req.setMethod('GET');
        req.setTimeout(30000); // 30 seconds; max is 120000

        // No explicit auth header needed here.
        // The Named Credential's custom header formula {!$Credential.OAuthToken}
        // injects the OAuth token at callout time.

        HttpResponse res = new Http().send(req);
        return res;
    }
}
```

**Why not the alternative:** Do not manually retrieve the token from a Custom Setting or Custom Metadata and set `req.setHeader('Authorization', 'Bearer ' + token)`. This stores credentials in the Salesforce database outside the Protected credential vault, bypasses token refresh handling, and is an anti-pattern per the Salesforce Well-Architected Security pillar.

### Per-User Token Status Check via UserExternalCredential

**When to use:** The integration uses per-user OAuth and the UX should prompt the user to authenticate if they have not yet completed the OAuth flow, rather than letting a callout fail with a cryptic auth error.

**How it works:** Query `UserExternalCredential` for the current user and the target External Credential ID before making the callout. If no record exists, surface a re-auth URL or a friendly error.

```apex
public class AuthStatusChecker {
    /**
     * Returns true if the current user has an active UserExternalCredential
     * for the given External Credential API name.
     *
     * @param externalCredentialApiName  e.g. 'CustomerService_EC'
     */
    public static Boolean isUserAuthenticated(String externalCredentialApiName) {
        // Resolve the External Credential ID from the API name.
        // ExternalCredential is a setup object — use SOQL on it.
        List<ExternalCredential> ecs = [
            SELECT Id
            FROM ExternalCredential
            WHERE DeveloperName = :externalCredentialApiName
            LIMIT 1
        ];
        if (ecs.isEmpty()) {
            return false;
        }
        Id ecId = ecs[0].Id;

        // Check if the current user has a UserExternalCredential record
        // with PerUserPrincipal type.
        List<UserExternalCredential> uecs = [
            SELECT Id, PrincipalType
            FROM UserExternalCredential
            WHERE UserId = :UserInfo.getUserId()
              AND ExternalCredentialId = :ecId
              AND PrincipalType = 'PerUserPrincipal'
            LIMIT 1
        ];
        return !uecs.isEmpty();
    }
}
```

**Why not the alternative:** Do not attempt the callout and inspect the HTTP 401 response status as a proxy for "user not authenticated." That approach wastes a callout, can confuse application-level 401s (the API rejecting the request) with auth-layer 401s (no token available), and counts against the 100-callout-per-transaction limit.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Standard REST callout to authenticated endpoint | `callout:NCName/path` in `setEndpoint()` | Platform injects auth, handles Remote Site Settings |
| OAuth token must appear in a custom header, not Authorization | Configure formula `{!$Credential.OAuthToken}` in Named Credential custom header field | Formula is evaluated at callout time; no Apex token handling needed |
| Need to check if current user has authenticated (per-user OAuth) | Query `UserExternalCredential` for UserId + ExternalCredentialId before callout | Avoids callout failure; enables proactive re-auth prompt |
| Async Visualforce or Aura page needing callout | Use standard synchronous callout with `callout:` prefix; Continuation framework is NOT supported | Continuation does not support the `callout:` prefix |
| Legacy model org, single Named Credential | Same `callout:` syntax; no `UserExternalCredential` SObject available | Behavioral model differs; `UserExternalCredential` is enhanced model only |
| Managed package distribution | Verify subscriber org Remote Site Settings if Named Credential not included in package | Named Credentials in packages do not automatically provision RSSettings in subscriber |
| Token formula in request body or URL path | Not supported — use an alternative approach (custom header field only) | `{!$Credential.*}` tokens only resolve in Named Credential custom header fields |

---

## Recommended Workflow

1. **Confirm the Named Credential model** — check Setup > Named Credentials and determine whether the org uses the legacy model (single record) or the enhanced model (External Credential + Named Credential pair). This determines whether `UserExternalCredential` is available and whether custom header formulas are configured on the Named Credential or External Credential.
2. **Identify auth requirements** — determine whether the callout uses OAuth (Bearer token), Basic auth (username/password), or custom headers. For per-user OAuth, note which External Credential principal type is configured (`PerUserPrincipal`).
3. **Write the Apex callout** — use `callout:<NCApiName>/path` in `setEndpoint()`. Set an explicit timeout. Do not manually construct auth headers; rely on the Named Credential custom header formulas.
4. **Add a pre-callout auth gate if needed** — for per-user OAuth flows, query `UserExternalCredential` before the callout and return a graceful error or redirect if no record exists.
5. **Write unit tests with mock** — Named Credential callouts require `HttpCalloutMock` in test context. Verify status codes, mock response bodies, and test both authenticated and unauthenticated paths.
6. **Validate** — run `python3 check_apex_named_credentials_patterns.py --manifest-dir <project_root>` and confirm no hardcoded endpoint or credential anti-patterns are present.

---

## Review Checklist

- [ ] All callout endpoints use `callout:<NCApiName>` prefix — no hardcoded base URLs with credentials.
- [ ] No credentials (tokens, passwords) set via `req.setHeader()` directly in Apex code.
- [ ] `req.setTimeout()` is set explicitly; default 10-second timeout is almost always too short.
- [ ] Per-user OAuth flows check `UserExternalCredential` before attempting the callout.
- [ ] Tests use `HttpCalloutMock` and cover non-200 response codes.
- [ ] Named Credentials are not used with the Continuation framework.
- [ ] Formula tokens (`{!$Credential.OAuthToken}`) are only configured in Named Credential custom header fields, not in Apex string literals or request bodies.
- [ ] Managed package distribution scenarios account for Remote Site Settings in subscriber orgs.

---

## Salesforce-Specific Gotchas

1. **Named Credentials cannot be used with the Continuation framework** — the `callout:` prefix is incompatible with Visualforce/Aura Continuation async callouts. Attempting to use `callout:NCName` as the Continuation endpoint URL results in a runtime error. Use synchronous callouts from Queueable instead if async behavior is needed.
2. **Formula tokens only resolve in Named Credential custom header fields, not in Apex** — `{!$Credential.OAuthToken}` in an Apex string literal or request body is sent as the literal text `{!$Credential.OAuthToken}` to the external system. Developers expecting it to be replaced at runtime are surprised when the API rejects the malformed token.
3. **Remote Site Settings exemption does not automatically apply in managed packages** — when a Named Credential is in a managed package, the subscriber org does not automatically receive a Remote Site Settings entry for the endpoint. If any code path in the package makes a direct URL callout (bypassing the Named Credential), it will fail. Always use the `callout:` prefix consistently.
4. **UserExternalCredential is only available in the enhanced model** — querying this SObject in a legacy-model org throws a compile error or runtime exception. Guard with a feature check or document the org model requirement clearly.
5. **Per-user token expiry is not reflected in UserExternalCredential** — a `UserExternalCredential` record existing does not guarantee the token is valid; it only means the user completed the OAuth flow at some point. A 401 from the external API is the only signal that the token has expired and the user must re-authenticate.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Apex callout class | `Http().send()` call using `callout:NCName/path` with explicit timeout and no hardcoded auth |
| Pre-callout auth gate | SOQL-based `UserExternalCredential` check returning boolean auth status for current user |
| Named Credential review findings | List of anti-patterns found (hardcoded endpoints, inline tokens, missing timeout, Continuation misuse) |

---

## Related Skills

- `integration/named-credentials-setup` — use for creating or configuring Named Credentials and External Credentials in the Setup UI. This skill covers only the Apex consumption patterns.
- `integration/callouts-and-http-integrations` — use for general HTTP callout mechanics (HttpRequest, HttpResponse, mock patterns, error handling) that apply regardless of Named Credentials.
- `apex/apex-queueable-patterns` — use when Named Credential callouts need to run asynchronously outside a synchronous transaction.
- `apex/callout-limits-and-async-patterns` — use when hitting the 100 callout per transaction limit or designing retry/backoff for callout failures.
