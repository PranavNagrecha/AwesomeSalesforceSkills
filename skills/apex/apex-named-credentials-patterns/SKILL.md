---
name: apex-named-credentials-patterns
description: "Use when writing Apex that calls out to external endpoints via Named Credentials, working with custom header formula tokens ({!$Credential.OAuthToken}), querying per-user auth state through the UserExternalCredential SObject, or diagnosing why Named Credential callouts fail. Trigger keywords: 'callout: prefix', 'named credential header formula', 'UserExternalCredential', 'External Credential per-user principal', 'Named Credential oauth token apex', 'namedCredentialType SecuredEndpoint', 'externalCredentialPrincipalAccesses', 'generateAuthorizationHeader', 'allowMergeFieldsInHeader', 'migrate legacy named credential', 'Remote Site Setting vs Named Credential'. NOT for Named Credential setup in the Salesforce Setup UI — use integration/named-credentials-setup. NOT for general HTTP callout mechanics (HttpRequest, HttpResponse, mock patterns) — use apex/callouts-and-http-integrations."
category: apex
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
triggers:
  - "named credential custom header formula apex how to pass oauth token"
  - "per-user oauth named credential apex token inspection"
  - "UserExternalCredential query apex check if user has authenticated"
  - "callout colon prefix named credential apex syntax"
  - "enhanced model external credential vs named credential apex confusion"
  - "named credential not working with continuation async callout"
  - "write the externalCredential and namedCredential xml for a SecuredEndpoint callout"
  - "migrate a legacy named credential to external credential without breaking apex"
  - "grant a permission set access to an external credential principal"
  - "named credential callout returns 401 but the credential is configured"
  - "replace remote site setting and hardcoded api token with a named credential"
  - "deploy named credential and apex to sandbox without changing the endpoint in code"
  - "test an apex callout that goes through a named credential"
  - "stop apex from setting the authorization header twice on a named credential callout"
  - "the parameter type AuthHeader requires these fields ParameterValue deploy error"
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
  - "Which permission set grants the External Credential principal, and who the callout runs as"
outputs:
  - "Apex callout implementation using Named Credential with correct syntax"
  - "Custom header formula token usage for injecting OAuth tokens or credentials"
  - "UserExternalCredential SOQL query for per-user token status checks"
  - "Guidance on Enhanced vs. Legacy model differences affecting Apex code"
  - "Deployable ExternalCredential + NamedCredential + PermissionSet metadata with deploy order"
dependencies: []
version: 1.2.0
author: Pranav Nagrecha
updated: 2026-09-12
---

# Apex Named Credentials Patterns

Use this skill when writing Apex that makes authenticated outbound callouts through Named Credentials — covering the `callout:` URL prefix, the `{!$Credential.*}` merge fields for injecting credential values into headers and bodies, the `ExternalCredential` / `NamedCredential` / `PermissionSet` metadata a developer actually deploys, and the behavioral differences between the legacy and `SecuredEndpoint` models that affect Apex code.

Boundary: `integration/named-credentials-setup` owns the declarative security design. This skill owns how Apex consumes it and the metadata shapes a developer deploys alongside the code.

---

## Before Starting

- Is the org using the **legacy model** (single Named Credential with embedded auth config) or the **enhanced model** (External Credential for auth + Named Credential for endpoint, introduced Spring '22)?  The two models have different metadata shapes but the same `callout:` URL syntax in Apex.
- Does the use case require **per-user auth** (each user authenticates individually with OAuth) or **org-wide auth** (all users share one credential set)? The choice determines which principal type the External Credential declares and how failures surface to the user.
- Are there **credential values** the endpoint needs in a header or body that the platform will not supply on its own? Those use `{!$Credential.*}` merge fields, which are written in Apex but gated by two flags on the Named Credential.
- Which **permission set** grants the External Credential principal, and does the user the callout runs as hold it? Batch, Queueable, Scheduled and `@future` Apex do not necessarily run as the person who started the work.
- Named Credentials automatically exempt the endpoint host from Remote Site Settings. In **managed packages**, the credential also needs an `AllowedManagedPackageNamespaces` parameter naming the package. Confirm the distribution model before relying on the exemption.

---

## Questions to Ask Before Configuring

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| What is the Named Credential's API name, and does a credential with that exact name exist in every org you will deploy to? | `callout:` resolves by API name. Same-name credentials with different URL parameters are the platform's own portability mechanism (`apexdev` L34327–34331) — the reason callout code never needs an environment check. | You get one Apex class that deploys unchanged to scratch, sandbox and production, and a deploy-time check the checker can enforce (`NC-APEX-003`). |
| Is the credential `Legacy` or `SecuredEndpoint`? | Every field the legacy shape relies on is deprecated at API 56.0 (`api_meta` L89950–90240). Building new Apex on it means building on a deprecated surface, and hand-authored files mix the two shapes silently. See gotchas 1 and 5. | You write the right XML the first time instead of deploying a `SecuredEndpoint` credential whose URL sits in a legacy-only `<endpoint>` element and is therefore ignored. |
| Named principal or per-user principal? | `NamedPrincipal` shares one identity; `PerUserPrincipal` gives per-user access control (`api_meta` L63806–63808). Only the named principal works for Batch, Queueable and Scheduled Apex. It also changes what admin edits cost — see gotcha 10. | The async design is settled before the code is written, and the external system's audit trail is a deliberate choice rather than a side effect. |
| Which permission set grants the principal, and is it assigned to the user the callout runs as? | A principal is inert until `externalCredentialPrincipalAccesses` grants it (`api_meta` L94794–94796). Nothing in the deploy fails without it. See gotcha 6 and anti-pattern 8. | The change set includes the grant and the assignment step, so the integration works on first run instead of returning 401 for every user. |
| Who owns the `Authorization` header — the platform or your Apex? | `generateAuthorizationHeader` defaults to `true` (`api_meta` L90039–90046). Apex adding its own on top is a collision that surfaces as a 401. See gotcha 4. | One owner, encoded in metadata that travels with the code, instead of an implicit default nobody deployed. |
| Does the endpoint need a credential value in a specific header name or in the body? | That is what `{!$Credential.*}` merge fields are for, and they need `allowMergeFieldsInHeader` / `allowMergeFieldsInBody`, both defaulting to `false` (`api_meta` L89914–89940). See gotchas 2 and 3. | The flags ship with the Apex that depends on them, so the endpoint receives the credential rather than the literal merge-field text. |
| What is the endpoint URL — host and path — and do sandbox and production share a host? | A `SecuredEndpoint` credential's `Url` parameter needs a real value before deploy, and it is one of the two facts an `AuthHeader` formula depends on. Proven live in a dry-run (`sf project deploy start --dry-run`, API 67.0), not stated in the guide. See gotcha 14. | The `NamedCredential` deploys with a real endpoint on the first attempt, and sandbox-vs-production drift is a decision instead of a placeholder left behind. |
| What is the name of the authentication parameter the header formula will merge in (e.g. `ApiKey`, `ApiToken`), and who enters its value in Setup after deploy? | An `AuthHeader` parameter needs a non-empty `parameterValue`, or the deploy fails with `The parameter type "AuthHeader" requires these fields: ParameterValue.` — and a `PermissionSet` naming that credential's principal fails in the same request. Proven live in a dry-run, not stated in the guide. See gotcha 14. | The `ExternalCredential` deploys with the `{!$Credential.<EC>.<ParameterName>}` formula in place, and the post-deploy Setup step that creates the actual parameter is scheduled instead of discovered at deploy time. |
| What kind of transaction makes the callout — synchronous, Queueable, Batch, or a Continuation? | Timeout budget, principal choice and framework support all follow from this. Continuations do accept `callout:` endpoints; the documented exclusion is Private Connect (`apexdev` L36006–36070). See gotcha 11. | The right timeout and the right mocking API (`Test.setMock` vs `Test.setContinuationResponse`) are chosen up front rather than discovered in a failing test. |

**What a proper configuration adds over just doing it:** a hardcoded endpoint and a concatenated `Authorization` header will call the API successfully today — what the credential model buys is that the secret is never in source or in an export, the endpoint changes per org without a code change, and access is granted and revoked with the same permission sets that govern everything else.

---

## Core Concepts

### Legacy vs. `SecuredEndpoint` Named Credential Model

The **legacy model** combines the endpoint URL and authentication configuration in a single Named Credential metadata record. The **enhanced model** (`namedCredentialType` `SecuredEndpoint`, Spring '22+) separates them:

- **External Credential** — holds the authentication protocol, principals, and auth parameters.
- **Named Credential** — holds the endpoint URL and references an External Credential.

From **Apex code, both models use exactly the same `callout:` URL syntax**. The difference is invisible in ordinary callout code and highly visible in the metadata you deploy. `namedCredentialType` valid values are `Legacy`, `PrivateEndpoint`, `SecuredEndpoint`, and `Standard` (reserved for internal use), available in API version 56.0 and later (`api_meta` L90140–90152).

| Concern | Legacy | `SecuredEndpoint` |
|---|---|---|
| Endpoint URL | `<endpoint>` (deprecated at 56.0) | `namedCredentialParameters` with `parameterType` `Url` |
| Auth protocol | `<protocol>` (deprecated at 56.0) | `ExternalCredential.authenticationProtocol` |
| Identity | `<principalType>` (deprecated at 56.0) | `ExternalCredentialParameter` `NamedPrincipal` / `PerUserPrincipal` |
| Who may use it | Profile / user-level credential entry | `PermissionSet.externalCredentialPrincipalAccesses` (API 59.0+) |
| Files to deploy | 1 | 3 (EC, NC, permission set) |

### The `callout:` URL Prefix

"A named credential URL contains the scheme `callout:`, the name of the named credential, and an optional path. For example: `callout:My_Named_Credential/some_path`" (`apexdev` L34332–34334). A query string is appended with `?`: `callout:My_Named_Credential/some_path?format=json` (`apexdev` L34335–34337).

```apex
HttpRequest req = new HttpRequest();
req.setEndpoint('callout:MyServiceNC/api/v2/customers');
req.setMethod('GET');
HttpResponse res = new Http().send(req);
```

The name is the **Named Credential's** API name, never the External Credential's. The platform resolves the endpoint, applies authentication, and skips the Remote Site Settings requirement for that host (`apexdev` L34319–34322).

### `{!$Credential.*}` Merge Fields — an Apex-Side Feature

The Apex Developer Guide's section is titled "Merge Fields for Apex Callouts That Use Named Credentials", and its examples are Apex, not Setup (`apexdev` L34456–34513):

```apex
req.setHeader('X-Username', '{!$Credential.Username}');
req.setHeader('Authorization', '{!$Credential.OAuthToken}');
req.setBody('Password:{!HTMLENCODE($Credential.Password)}');
```

| Merge field | Resolves to | Available when |
|---|---|---|
| `{!$Credential.Username}` / `{!$Credential.Password}` | Username / password of the running user | Password authentication |
| `{!$Credential.OAuthToken}` | OAuth token of the running user | OAuth authentication |
| `{!$Credential.AuthorizationMethod}` | `Basic`, `Bearer`, or `null` | Depends on protocol |
| `{!$Credential.AuthorizationHeaderValue}` | Base-64 `user:pass`, OAuth token, or `null` | Depends on protocol |
| `{!$Credential.OAuthConsumerKey}` | Consumer key | OAuth authentication |

Two flags gate them, both defaulting to `false`: `allowMergeFieldsInHeader` and `allowMergeFieldsInBody` (`api_meta` L89914–89940). `HTMLENCODE` is the only formula function permitted around a merge field, and only in bodies (`apexdev` L34508–34513). Apex never sees the resolved value — the substitution happens on the platform side at callout time.

### Principals and Who May Use Them

`ExternalCredentialParameter.parameterType` `NamedPrincipal` means "the parameter uses the same set of user credentials for all users who access the external system"; `PerUserPrincipal` "provides access control at the individual user level" (`api_meta` L63806–63808). Access is granted from the permission set side:

```xml
<externalCredentialPrincipalAccesses>
    <enabled>true</enabled>
    <externalCredentialPrincipal>Partner_Orders_EC-PartnerOrdersNamedPrincipal</externalCredentialPrincipal>
</externalCredentialPrincipalAccesses>
```

The value is the External Credential name and the principal name joined by a **dash** (`api_meta` L94995–94999), available in API version 59.0 and later. Before 58.0 the link ran the other way, from `ExternalCredentialParameter.principal` to a permission set — that field "is removed in API version 58.0 and later" (`api_meta` L63830–63831).

For a **per-user** principal, Apex may want to know whether the running user has authenticated before it calls. Treat that gate as an optimisation, not a contract: the `UserExternalCredential` and `ExternalCredential` **objects** are not documented in the Object Reference used to ground this skill, so run `sf sobject describe` against the target org before coding against a field list (gotcha 12). Handle 401 and 403 in the callout path regardless.

### Callout Limits That Bite Named Credential Code

- Default timeout **10 seconds**; per-callout maximum **120,000 ms**; **120-second** cumulative budget across all callouts in one transaction (`apexdev` L35844–35857).
- Maximum **100** callouts per transaction (`apexdev` L35844).
- Continuations accept a named credential URL (`apexdev` L36006–36018). The documented exclusion is Private Connect (`apexdev` L36069–36070). Limits there: three parallel callouts, 120-second maximum (`apexdev` L36299, L36303).
- Running a `callout:` in Execute Anonymous requires **Customize Application** (`apexdev` L14761–14762).

Deeper coverage of the limits themselves belongs to `integration/callout-limits-and-async-patterns`.

---

## Common Patterns

### Environment-Portable Callout Through a `SecuredEndpoint` Credential

**When to use:** the default. One Apex class deploys unchanged everywhere; each org's credential carries its own URL parameter under the same API name.

**How it works:** the Apex names the credential and a path; the platform supplies the base URL, the authentication, and the Remote Site exemption. Build on `templates/apex/HttpClient.cls`, which composes `'callout:' + namedCredential + path` for you.

```apex
HttpClient.Response res = new HttpClient()
    .namedCredential('Partner_Orders_NC')
    .path('/v2/orders/' + EncodingUtil.urlEncode(externalId, 'UTF-8'))
    .method('GET')
    .timeoutMs(20000)
    .retryOnTransient(false)   // HttpClient's backoff is a busy-wait; retry from a Queueable
    .send();
```

**Why not the alternative:** an `if (isSandbox)` branch or a Custom Setting holding the base URL reimplements, worse, the portability the platform already provides — and gives you a second place for production and sandbox to drift apart.

### Endpoint That Needs the Credential in a Non-Standard Header

**When to use:** the API wants the token in `X-Api-Key`, or wants `Authorization` in a shape the platform's generated header does not match.

**How it works:** turn off the platform's header, turn on header merge fields, and write the header in Apex.

```apex
// Named Credential: generateAuthorizationHeader = false, allowMergeFieldsInHeader = true
HttpRequest req = new HttpRequest();
req.setEndpoint('callout:Partner_Orders_NC/v2/orders');
req.setHeader('Authorization', 'Bearer {!$Credential.Password}');
req.setHeader('Accept', 'application/json');
```

**Why not the alternative:** reading a token from a Custom Setting or Custom Label to build the same header puts the secret in the database, outside the credential vault, deployable to any sandbox without rotation, and visible in an export.

### Replacing a Remote Site Setting Plus a Hardcoded Secret

**When to use:** an inherited integration that calls a literal URL with a concatenated `Authorization` header.

**How it works:** deploy External Credential → Named Credential → permission set, change one line of Apex, delete the Remote Site Setting last.

```apex
// Before
req.setEndpoint('https://api.acme-corp.com/v2/orders/' + id);
req.setHeader('Authorization', 'Bearer ' + System.Label.Acme_Token);

// After — endpoint and auth both move out of source
req.setEndpoint('callout:Acme_Orders_NC/v2/orders/' + id);
```

**Why not the alternative:** leaving the Remote Site Setting in place after the migration hides the fact that some other code path still calls the host directly — the checker's `NC-RSS-001` advisory exists to surface exactly that.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Standard REST callout to an authenticated endpoint | `callout:NCName/path` in `setEndpoint()` | Platform resolves endpoint, applies auth, skips Remote Site Settings |
| Token must appear in a custom header name | `generateAuthorizationHeader` false + `allowMergeFieldsInHeader` true + `setHeader` with `{!$Credential.*}` | The merge field resolves platform-side; the secret never enters Apex |
| Credential value needed inside the request body | `allowMergeFieldsInBody` true + `{!HTMLENCODE($Credential.Password)}` | `HTMLENCODE` is the only supported wrapper, and only in bodies |
| Long-running callout from a Visualforce page | Continuation with a `callout:` endpoint | Named credential URLs are supported there (`apexdev` L36006–36018) |
| Same callout must traverse a private connection | `namedCredentialType` `PrivateEndpoint` + Queueable | Async callouts are not supported over Private Connect |
| Async job (Batch / Queueable / Scheduled) | `NamedPrincipal` | The running user is not the person who queued the work |
| External system must attribute actions to individuals | `PerUserPrincipal` + 401/403 re-auth path | Per-user access control at the cost of an onboarding flow |
| Managed package calling a subscriber's credential | Add `AllowedManagedPackageNamespaces` to the credential | Namespaced packages are named explicitly on the credential |
| Inherited legacy credential still working | Leave it, plan the migration | Every legacy field is deprecated at 56.0 — new work goes on `SecuredEndpoint` |

---

## Recommended Workflow

1. **Identify the credential and its model.** Get the Named Credential API name from the requester, then confirm the shape: `sf data query --query "SELECT DeveloperName, CalloutOptionsGenerateAuthorizationHeader, CalloutOptionsAllowMergeFieldsInHeader FROM NamedCredential"`. A populated `Endpoint` or `PrincipalType` means legacy (both are legacy-only and deprecated at 56.0). Work through the **Questions to Ask** table before writing anything.
2. **Author or amend the metadata.** Follow `references/code-examples.md` sections 1–3 for the `ExternalCredential`, `NamedCredential` and `PermissionSet` XML. Settle the two decisions the Apex depends on here, not later: who owns the `Authorization` header (`generateAuthorizationHeader`), and whether merge fields are needed (`allowMergeFieldsInHeader` / `allowMergeFieldsInBody`).
3. **Write the Apex against `templates/apex/HttpClient.cls`.** Name the credential, set an explicit timeout, and branch on 401/403 separately from other non-2xx codes so an access failure reads as an access failure. Section 4 of `references/code-examples.md` is the reference implementation.
4. **Write the test with `templates/apex/tests/MockHttpResponseGenerator.cls`.** Cover the success shape, the endpoint's not-found code, and the 401 path. Do not assert on `req.getEndpoint()` inside the mock — route on the path substring instead (section 6 explains why).
5. **Run the checker.** `python3 scripts/check_apex_named_credentials_patterns.py --manifest-dir force-app --strict`. It resolves every `callout:` name against the credentials in the tree, flags a legacy `namedCredentialType`, catches a `SecuredEndpoint` credential with no `externalCredential` link, and reports an Authorization header that collides with the platform's.
6. **Deploy in dependency order and verify.** External Credential (with its principal) deploys first, then Named Credential, then the permission set, then Apex. Only after the External Credential deploys does a human enter the API key against the principal in Setup — never in metadata — and only then does `sf org assign permset` run. A validate-only deploy (`--dry-run` / `checkOnly`) of the credential can pass with the `AuthHeader` formula in place while that Setup value is still empty; the deploy checks the formula's shape, not the secret behind it, so the runtime 401 on a live callout is the real UAT check, not the green deploy (gotcha 14). Verify with the `NamedCredential` SOQL in section 8 and `sf apex run test`.
7. **Retire what the credential replaced.** Delete the Remote Site Setting and the Custom Label or Custom Setting that held the old secret, and rotate the secret — it was in source control, so it is compromised.

---

## Review Checklist

- [ ] All callout endpoints use the `callout:<NCApiName>` prefix — no literal base URLs.
- [ ] Every `callout:` name resolves to a Named Credential that exists in the target org.
- [ ] `generateAuthorizationHeader` is deployed explicitly, and exactly one side sets `Authorization`.
- [ ] Any `{!$Credential.*}` merge field is paired with the matching `allowMergeFields*` flag in the same change.
- [ ] `HTMLENCODE` appears only around body merge fields, never header ones.
- [ ] The External Credential declares a principal, and a permission set grants it.
- [ ] The permission set is assigned to the user the callout actually runs as, including in async contexts.
- [ ] `req.setTimeout()` is set explicitly; the 10-second default is almost always too short.
- [ ] Tests use `HttpCalloutMock` (or `Test.setContinuationResponse` for Continuations) and cover 401.
- [ ] No secret remains in a Custom Label, Custom Setting, or Custom Metadata record after migration.
- [ ] `check_apex_named_credentials_patterns.py --strict` is clean.

---

## Salesforce-Specific Gotchas

Full detail, with line citations, in `references/gotchas.md`. The six that most often break a first deployment:

1. **A `SecuredEndpoint` credential's URL belongs in a `Url` parameter.** `<endpoint>` is legacy-only and deprecated at API 56.0, so a copied file can carry a URL the modern type ignores.
2. **`generateAuthorizationHeader` is `true` unless you deploy `false`.** Apex that adds its own `Authorization` on top collides with the platform's.
3. **Merge fields are Apex-side, but inert until the flags are on.** Both `allowMergeFields*` fields default to `false`; the literal text reaches the endpoint instead of the credential value.
4. **The principal grant lives on the permission set from API 59.0.** `ExternalCredentialParameter.principal` was removed at 58.0; without `externalCredentialPrincipalAccesses` every callout is unauthorized.
5. **Continuations do support `callout:`.** The widely repeated incompatibility is not in the guide; the documented exclusion is Private Connect.
6. **An `AuthHeader` parameter with no `parameterValue` fails deploy validation.** Proven live in a dry-run, not stated in the guide — and a permission set naming that credential's principal fails in the same deploy as a cascade. See gotcha 14.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| `ExternalCredential` XML | `authenticationProtocol`, a `NamedPrincipal` or `PerUserPrincipal` parameter, and any `AuthHeader` / `AuthParameter` entries |
| `NamedCredential` XML | `SecuredEndpoint` with `Url` and `Authentication` parameters, plus explicit `generateAuthorizationHeader` and `allowMergeFields*` flags |
| `PermissionSet` fragment | `externalCredentialPrincipalAccesses` granting `<EC>-<principal>` |
| Apex client class + `-meta.xml` | `callout:` endpoint via `templates/apex/HttpClient.cls`, explicit timeout, 401/403 branch |
| Apex test class | `MockHttpResponseGenerator` covering success, not-found and 401 |
| `package.xml` + deploy order | EC → NC → PermissionSet → Apex, with the manual credential-entry and assignment steps called out |
| Checker report | `NC-APEX-*`, `NC-META-*`, `NC-XREF-*`, `NC-PERM-*`, `NC-RSS-*`, `NC-AUTH-*`, `NC-PS-*` findings by severity |

---

## Reference Files

| File | Read it when |
|---|---|
| `references/code-examples.md` | You are writing the deployable artifacts: External Credential, Named Credential, permission set, Apex client, test, `package.xml`, deploy order, and verification queries |
| `references/gotchas.md` | A callout fails for a reason the code does not explain, or you are hand-authoring credential XML |
| `references/llm-anti-patterns.md` | Reviewing generated Apex or credential XML, or self-checking your own output |
| `references/examples.md` | You want a worked scenario end to end, including the before/after of a migration |
| `references/well-architected.md` | Choosing between the legacy and `SecuredEndpoint` models, or between principal types, and needing the tradeoff written down |

---

## Related Skills

- `integration/named-credentials-setup` — the declarative security design: choosing an auth protocol, configuring OAuth and JWT flows, and the Setup-side work. This skill covers the Apex consumption and the metadata a developer deploys.
- `apex/callouts-and-http-integrations` — general HTTP callout mechanics (`HttpRequest`, `HttpResponse`, uncommitted-work errors, error handling) that apply regardless of Named Credentials.
- `apex/apex-http-callout-mocking` — multi-response and per-endpoint mock design when one canned response is not enough.
- `apex/apex-queueable-patterns` — moving a Named Credential callout out of a synchronous transaction.
- `integration/callout-limits-and-async-patterns` — the 100-callout ceiling, the cumulative timeout budget, and retry design.
- `security/oauth-token-management` — token issuance, refresh, rotation and revocation for the Connected App behind an OAuth External Credential.
- `integration/private-connect-setup` — when `namedCredentialType` must be `PrivateEndpoint` and async callouts are therefore off the table.
