---
name: named-credentials-setup
description: "Named Credentials and External Credentials configuration for secure outbound callouts: per-user vs per-org authentication, legacy vs enhanced Named Credentials, external credential principal types (Named Principal, Per User, Anonymous), OAuth 2.0 and JWT flows, and credential deployment. NOT for the Apex callout code — use apex/apex-named-credentials-patterns. NOT for connected app setup — use admin/connected-apps-and-auth."
category: integration
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Operational Excellence
triggers:
  - "how to configure named credential for REST callout"
  - "set up OAuth 2.0 authentication for external service in Salesforce"
  - "per-user vs org-wide callout authentication"
  - "external credential principal types named principal per user anonymous"
  - "named credential deployment metadata api scratch org"
  - "legacy named credential vs enhanced named credential difference"
tags:
  - named-credentials
  - external-credentials
  - callout-auth
  - oauth
  - integration-security
  - metadata-deployment
inputs:
  - "Target external service endpoint URL and authentication type (OAuth 2.0, basic auth, JWT, AWS, custom)"
  - "Authentication scope: org-wide (Named Principal) vs individual user (Per User)"
  - "OAuth app credentials (client ID, client secret, token endpoint) if OAuth 2.0"
  - "Certificate alias if JWT authentication"
  - "List of users or permission sets that need callout access"
outputs:
  - "Enhanced Named Credential record (endpoint) linked to External Credential record (auth)"
  - "External Credential principal with permission set assignment controlling who can call out"
  - "Checklist of post-setup validation steps"
  - "Deployment-safe metadata structure for Named Credential and External Credential"
dependencies: []
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-10-20
---

# Named Credentials Setup

This skill activates when a practitioner needs to configure Named Credentials or External Credentials for secure Salesforce outbound callouts — covering the full setup lifecycle from choosing principal type through deployment. It does not cover the Apex callout code that uses the credential once it exists.

Metadata shape (grounded, Metadata API 264): an enhanced Named Credential has `namedCredentialType` `SecuredEndpoint` (or `PrivateEndpoint`), its URL is a `namedCredentialParameters` entry of type `Url`, and an `Authentication` entry points at an External Credential (meta 264 L92874-92884, L93044-93087, example L93120-93145). An External Credential has `authenticationProtocol` and `externalCredentialParameters`; its principals are parameters of type `NamedPrincipal` or `PerUserPrincipal` (meta 264 L66182-66202, L66348-66350, example L66398-66416). OAuth endpoints and the grant type live in an `ExternalAuthIdentityProvider` (API 62.0+, `authenticationFlow` AuthorizationCode, ClientCredentials or SalesforceDefined; meta 264 L65793-65831) or an auth provider. Access is granted from the permission set side, `PermissionSet.externalCredentialPrincipalAccesses` (API 59.0+, value `ExternalCredential-Principal`; meta 264 L97495-97497, L97687-97704).

---

## Before Starting

Gather this context before working on anything in this domain:

- **Enhanced vs Legacy:** Determine which model the org is using. `namedCredentialType` is `Legacy` ("doesn't use the schema introduced in the Winter '23 release"), `SecuredEndpoint` (uses external credentials) or `PrivateEndpoint` (API 56.0+, meta 264 L92874-92884); the legacy-only fields (`endpoint`, `principalType`, `protocol`, `username`, `password` and others) are deprecated in API 56.0 (meta 264 L92756-92771, L92927-92975). UNVERIFIED (2026-10-20): "new orgs default to enhanced" and "Salesforce strongly recommends migrating" are not in the corpus.
- **Auth type:** Confirm whether the external service requires OAuth (Authorization Code or Client Credentials flow), Basic (username + password), AWS Signature V4 or a Custom scheme. `ExternalCredential.authenticationProtocol` accepts AwsSv4, Basic, Custom and Oauth; Jwt, JwtExchange, NoAuthentication and Password are "Reserved for future use" there (meta 264 L66186-66197), yet the same description also says "For connections using a direct token system, select Jwt" (L66199) and "For on-premises systems, select Password" (L66201-66202, Files Connect); the two pull different ways, so confirm in the org before choosing Jwt or Password. JWT bearer is configured as OAuth with a `SigningCertificate` parameter plus `JwtBodyClaim`/`JwtHeaderClaim` parameters (meta 264 L66314-66316, L66340-66355).
- **Scope:** Confirm whether all users share one set of credentials (Named Principal) or each user authenticates individually (Per User). Per-user requires each user to complete an OAuth flow and adds user education overhead.
- **Deployment:** Named Credential and External Credential metadata structures (endpoint URL, protocol, principal type) are deployable via Metadata API. Credentials are encrypted (meta 264 L92625-92627, L66152-66154); packaged named credentials "don't include the access tokens or certificates that are needed to perform authenticated callouts", so after install you create the principal or populate tokens in the UI or Connect API, grant permission sets access to the principals, and reauthenticate (pkg2 264 L9543-9567). The same guide gives the reason, which covers a plain Metadata API deploy too: "the standard Metadata API can't fully expose the definition of a credential and render sensitive information like tokens in plain text" (pkg2 264 L9543-9544), so re-enter secrets after every deploy. UNVERIFIED (2026-10-20): scratch-org spin-up and sandbox copy are not addressed.
- **Limits:** UNVERIFIED (2026-10-20): the "200 legacy Named Credentials per org" figure and any enhanced-model limit are not in the corpus (grep of the app-limits cheat sheet and all 13 other files); read the current limits page before designing a many-integration org.

---

## Questions to Ask Before Configuring

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| Does the org use legacy or enhanced Named Credentials, and is migration in scope? | `namedCredentialType` decides which fields and which permission model apply (Before Starting). | Legacy/enhanced inventory and a migration backlog. |
| Which protocol does the external service need? | Jwt, JwtExchange, NoAuthentication and Password are marked reserved on External Credential, though the same row says to select Jwt for a direct token system and Password for on-premises Files Connect (Before Starting). | Oauth, Basic, AwsSv4 or Custom, and the OAuth flow. |
| One shared identity or one per user? | Principal type drives who authenticates and what async Apex can use (SKILL gotcha 1, gotchas.md Gotcha 5). | Named Principal or Per User, with the reason. |
| Which permission sets will enable the principal? | Access is granted from the permission set side (SKILL gotcha 1, gotchas.md Gotcha 1). | A permission-set list and an integration-user owner. |
| How will secrets reach each org after deployment? | Packaged credentials exclude tokens and certificates (SKILL gotcha 2, gotchas.md Gotcha 2). | A runbook step with a named admin. |
| Are there custom header or merge-field requirements? | Merge fields and header formulas differ by model (SKILL gotcha 3, gotchas.md Gotcha 4). | The exact header or merge field and a test callout. |
| Which callback URL and certificate does the IdP register? | Authorization Code and JWT depend on exact callback and certificate values (gotchas.md Gotcha 3). | Registered redirect URI and certificate alias. |

A proper configuration adds an enhanced credential with a documented principal and permission-set model, a secrets runbook and a tested callout, which "just pasting an endpoint and key" skips.

---

## Core Concepts

### Enhanced Named Credentials: Endpoint + Auth Are Separated

Since Winter '23, Salesforce splits the configuration into two records:

- **Named Credential** — holds the endpoint URL and a reference to an External Credential. This is what Apex references with `callout:NamedCredentialName`.
- **External Credential** — holds the authentication configuration: protocol, principals, custom authentication headers (`AuthHeader`) and JWT claims; the OAuth endpoints and grant type come from the referenced external auth identity provider.

One External Credential can back multiple Named Credentials pointing to different paths on the same service (UNVERIFIED 2026-10-20: the corpus says only that "each named credential must be mapped to at least one external credential", pkg2 264 L9573-9574). This is a significant architecture win over legacy credentials where each endpoint-auth pair was one record.

**Legacy Named Credentials** combined URL + auth in a single record. They still work in existing orgs (the type is kept "for backward compatibility", meta 264 L92875-92876); "Salesforce strongly recommends migrating" is UNVERIFIED (2026-10-20), as in Before Starting. In Apex, both models use the same `callout:Name` syntax.

### External Credential Principal Types

The principal type controls which identity is used for the callout:

| Principal Type | Who authenticates | Credential storage |
|---|---|---|
| **Named Principal** | The org (all users share one credential) | One secret stored org-wide |
| **Per User** | Each Salesforce user authenticates individually | One credential per user, stored against their user record |
| **Anonymous** (legacy only) | No authentication sent | No credentials required |

Anonymous is a value of the legacy `principalType` (Anonymous, NamedUser, PerUser; meta 264 L92936-92945). An enhanced External Credential has principal parameter types `NamedPrincipal` ("same set of user credentials for all users") and `PerUserPrincipal` ("access control at the individual user level"), and `NoAuthentication` is "Reserved for future use" (meta 264 L66195, L66348-66350). Legacy credentials do support Per User (`principalType` PerUser).

**Named Principal** is the right default for server-to-server integrations (e.g., background jobs calling an external API with a service account). **Per User** is correct when the external service enforces user-level access control and needs to act on behalf of the individual (e.g., a user accessing their own Google Drive data).

**Permission Sets control access to principals.** Users assigned to a permission set whose `externalCredentialPrincipalAccesses` enables the principal "can make callouts using a named credential that references the external credential" (meta 264 L97687-97690). The `principal` field on the External Credential parameter, which pointed at a permission set, is described as "removed in API version 58.0 and later" (meta 264 L66364-66371 and the description continuing across the page break at L66381-66383). Without the permission-set entry, users cannot execute callouts even if the credential is correctly configured.

### OAuth 2.0 Flows in External Credentials

Salesforce supports several OAuth 2.0 grant types:

- **Authorization Code** — used for Per User principals where Salesforce redirects the user to the external identity provider. UNVERIFIED (2026-10-20): the callback URL `https://{yourDomain}/services/authcallback/{ExternalCredentialDeveloperName}` is not in the corpus (the only `authcallback` example is for an auth provider, apexdev 264 L21292). The corpus names the per-user step "My Personal Information > External Credential" (pkg2 264 L9567) and a Named Principal step "Setup > Named Credential > External Credential" (pkg2 264 L9566); "User Settings > Authentication Settings for External Systems" appears only as the Help topic "Store Authentication Settings for External Systems" (obj 264 L134284-134285).
- **Client Credentials** — used for Named Principal (org-wide) where Salesforce exchanges a client ID + secret for a bearer token. No user interaction required. `authenticationFlow` ClientCredentials exists on the external auth identity provider (meta 264 L65828-65831).
- **JWT Bearer** — Salesforce signs a JWT using a certificate named in a `SigningCertificate` parameter ("OAuth with JWT Bearer Flow", meta 264 L66353-66355) and presents it to the token endpoint (`AuthProviderUrl`, meta 264 L66314-66316). "Certificate and Key Management" is UNVERIFIED (2026-10-20).

Token refresh: Salesforce refreshes expired or invalid access tokens on the standard 401 response, and an `AdditionalRefreshStatusCode` parameter adds 4xx, 6xx, 7xx, 8xx and 9xx codes (meta 264 L66295-66298).

### Credential Vault and Deployment Boundaries

Salesforce stores all credential secrets (passwords, client secrets, access tokens) in an encrypted vault. This has two important consequences:

1. **Secrets are encrypted.** "All credentials stored within this entity are encrypted" under org-specific keys (meta 264 L92625-92627). UNVERIFIED (2026-10-20): that secrets cannot be read via SOQL, REST API or Apex is not stated in the corpus.
2. **Neither packaging nor a Metadata API deploy carries secrets** — "the standard Metadata API can't fully expose the definition of a credential and render sensitive information like tokens in plain text" (pkg2 264 L9543-9546): an admin re-enters credential values post-deployment. Document this in runbooks.

---

## Common Patterns

### Mode 1: Create a New Named Credential (Enhanced Model)

**When to use:** Any new integration in an org on Winter '23+ (or any org being migrated from legacy).

**How it works:**

1. **Setup > Named Credentials > External Credentials > New**
   - Developer Name: use snake_case consistently (e.g., `My_Service_Ext_Cred`)
   - Label: human-readable name for Setup UI
   - Protocol: Oauth, Basic, AwsSv4 or Custom (the other `authenticationProtocol` values are marked "Reserved for future use", meta 264 L66186-66197, although L66199 and L66201-66202 say to select Jwt for a direct token system and Password for on-premises Files Connect)
   - If OAuth: the Authorization and Token URLs and the grant type are `AuthorizeUrl`/`TokenUrl` parameters and `authenticationFlow` of the external auth identity provider (meta 264 L65828-65831, L65894, L65916); UNVERIFIED (2026-10-20): the Setup UI field labels for Client ID, Client Secret and Scope are not in the corpus
   - Add a Principal: set principal type (Named Principal / Per User), give it a name (the parameter name)

2. **Enable the Principal on Permission Sets**
   - On each Permission Set whose users should call out, enable the External Credential principal (`externalCredentialPrincipalAccesses`, value `ExternalCredential-Principal`, meta 264 L97687-97704)
   - Without this the users cannot call out (UNVERIFIED 2026-10-20: the failure mode, "silently" or a specific error text, is not in the corpus)

3. **Setup > Named Credentials > Named Credentials > New**
   - URL: the base URL of the external service (e.g., `https://api.example.com/v1`)
   - External Credential: select the External Credential created above
   - Allow Merge Fields in HTTP Header / Body (both default false) and Generate Authorization Header (default true): enable the merge-field options only when Apex builds the header or body with merge fields (meta 264 L92648-92673, L92773-92779; apexdev 264 L34911-34916)

4. **In Apex:** `req.setEndpoint('callout:MyNamedCredential/resource');`

5. **Validate:** Make a test callout from Apex (Developer Console or test class) and confirm HTTP 200 response. Check Setup > Named Credentials for the OAuth token status if using OAuth flows.

**Why not hard-coded URLs with stored credentials:** A hard-coded endpoint must be registered in Remote Site Settings or "the callout fails"; a named credential endpoint needs no remote site setting (apexdev 264 L34727-34731, L34761-34763), and with a named credential "Salesforce manages all authentication" so code does not carry credentials (apexdev 264 L34744-34747). Credentials kept in Apex or Custom Settings are UNVERIFIED (2026-10-20) as "readable by any user with SOQL access" in the corpus, and need code or data changes to rotate.

---

### Mode 2: Audit or Review Existing Named Credentials

**When to use:** Pre-release review, security audit, or assessing org credential hygiene.

**How it works:**

1. Run the bundled checker: `python3 scripts/check_named_credentials.py --manifest-dir path/to/metadata`
2. In Setup, navigate to Named Credentials and note which are legacy (no linked External Credential) vs enhanced.
3. For each Enhanced credential, verify:
   - Principal type matches the integration pattern (Named Principal for service-to-service, Per User for user-delegated)
   - Permission Sets enable each principal (UNVERIFIED 2026-10-20: what an un-enabled principal does by version is not in the corpus)
   - OAuth callback URL is registered in the external IdP's allowed redirect URIs
   - Custom header formulas (`AuthHeader` and `HttpHeader` parameters, meta 264 L66299-66304, L93060-93073) do not embed literal secrets
4. For legacy credentials: assess migration priority. Legacy credentials do support Per User (`principalType` PerUser) and merge fields in headers (`allowMergeFieldsInHeader`, API 41.0+); what the enhanced model adds is the External Credential / parameter schema (`HttpHeader` and `AuthHeader` parameters, `SecuredEndpoint`/`PrivateEndpoint`), and the legacy fields are deprecated at API 56.0 (meta 264 L92680-92945).

---

### Mode 3: Troubleshoot Authentication Failures

**When to use:** Callouts returning 401 Unauthorized or generic "System.CalloutException: Unauthorized".

**How it works:**

1. **Check principal access:** A frequent cause (UNVERIFIED 2026-10-20: "most common" is not in the corpus) is a permission set that does not enable the External Credential principal. Confirm the calling user's Permission Set enables it (`externalCredentialPrincipalAccesses`).
2. **Per-user flow not completed:** If using a Per User principal, each user must authenticate ("My Personal Information > External Credential", pkg2 264 L9567). If the authorization is missing, Salesforce cannot attach a token to the callout (UNVERIFIED 2026-10-20: the exact failure is not in the corpus).
3. **OAuth token expired and not refreshing:** Salesforce refreshes on a 401, plus any `AdditionalRefreshStatusCode` values (meta 264 L66295-66298). UNVERIFIED (2026-10-20): whether the external IdP needs offline_access (or equivalent) for refresh tokens is IdP-specific and not in the corpus.
4. **Callback URL mismatch:** For Authorization Code flow, confirm the callback URL registered in the external IdP matches the one Salesforce shows for the credential. UNVERIFIED (2026-10-20): the URL shape `https://{yourMyDomain}.my.salesforce.com/services/authcallback/{ExternalCredentialDeveloperName}` and its case sensitivity are not in the corpus.
5. **JWT certificate not trusted:** If using JWT Bearer, confirm the certificate named in the `SigningCertificate` parameter matches the public key registered with the external IdP (meta 264 L66353-66355).
6. **Named Credential URL path double-slash:** Apex appends the path after the credential name, `callout:My_Named_Credential/some_path` (apexdev 264 L34798-34800). UNVERIFIED (2026-10-20): that a base URL ending in `/` produces `//` is not in the corpus; keeping the stored URL free of a trailing slash is a defensive convention.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Server-to-server background integration (batch, platform events) | Named Principal + Client Credentials OAuth or Basic | No user in context; org-wide credential is correct (the `Password` protocol is marked reserved, meta 264 L66197, and named only for on-premises Files Connect, L66201-66202) |
| User-delegated external service (user's own account on external system) | Per User + Authorization Code OAuth | Service acts on behalf of the individual user |
| Public API with no authentication required | Legacy `Anonymous` principal type, or a Custom protocol with no parameters ("For Simple URL data sources, select Custom with no parameters", meta 264 L66200) | `NoAuthentication` is reserved on External Credential |
| Service-to-service with a signed JWT | Named Principal + OAuth with JWT Bearer (`SigningCertificate`) | Certificate-based auth with no shared secret |
| Multiple endpoints on same service with same auth | One External Credential, multiple Named Credentials | External Credential is reusable across Named Credentials (UNVERIFIED 2026-10-20, see Core Concepts) |
| Legacy Named Credential migration | Create parallel Enhanced NC, test, deprecate legacy | Legacy fields are deprecated at API 56.0; the enhanced schema adds `HttpHeader`/`AuthHeader` parameters (legacy already supports Per User) |
| Credential rotation in production | Update credential value in Setup UI; no deployment needed (UNVERIFIED 2026-10-20) | Secrets are not carried in packages (pkg2 264 L9543-9546); no code change required |

---


## Recommended Workflow

1. Decide the model and principal: enhanced (`SecuredEndpoint`) unless a legacy credential must stay; Named Principal for service-to-service, Per User for user-delegated access.
2. Create the external auth identity provider (OAuth) or choose Basic/AwsSv4/Custom, then the External Credential with its principal parameter.
3. Create the Named Credential with the `Url` and `Authentication` parameters, then enable the principal on the permission sets that need it.
4. Call it from Apex with `callout:Name/path` and confirm the response; Per User principals need each user to authenticate first.
5. Run `python3 scripts/check_named_credentials.py --manifest-dir <metadata dir>` and walk the Review Checklist.
6. Record the post-deploy secret re-entry steps in the runbook (`templates/named-credentials-setup-template.md`).

---

## Review Checklist

Run through these before marking a Named Credential setup complete:

- [ ] External Credential record has a principal with the correct type (Named Principal / Per User)
- [ ] Permission Set(s) enable the External Credential principal (`externalCredentialPrincipalAccesses`)
- [ ] For OAuth 2.0 Authorization Code: callback URL registered in external IdP's allowed redirect list
- [ ] For OAuth 2.0 Client Credentials or JWT: token endpoint tested and credential values entered
- [ ] Named Credential URL and the Apex path joined without `//` (convention, UNVERIFIED 2026-10-20; the guide's example URL ends with `/`, meta 264 L93128)
- [ ] Allow Merge Fields in HTTP Header/Body is only enabled when Apex actively uses merge fields
- [ ] For Per User: affected users notified to authenticate (My Personal Information > External Credential)
- [ ] Deployment runbook documents that credential secrets must be re-entered post-deployment
- [ ] Test callout executed and HTTP 200 confirmed
- [ ] Legacy Named Credentials in scope of this project flagged for migration backlog

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Permission Set access is mandatory, not optional** — Even if an External Credential principal is correctly configured, users assigned to a permission set that enables it are the ones who "can make callouts" (meta 264 L97688-97690). UNVERIFIED (2026-10-20): the generic-auth-failure error text and "single most common cause" are not in the corpus.

2. **Packaging and Metadata API deploys do not carry credential secrets** (pkg2 264 L9543-9546: the Metadata API "can't ... render sensitive information like tokens") — the structure (URL, protocol, principal parameters) moves but not tokens or certificates; UNVERIFIED (2026-10-20): "silently fail". Post-deployment steps in a runbook must instruct an admin to re-enter these values.

3. **Callout merge fields and header formulas differ by model** — The documented Apex callout merge fields are `{!$Credential.Username}`, `{!$Credential.Password}`, `{!$Credential.OAuthToken}`, `{!$Credential.AuthorizationMethod}`, `{!$Credential.AuthorizationHeaderValue}` and `{!$Credential.OAuthConsumerKey}` (apexdev 264 L34926-34960); they take no credential name, so the earlier `{!$Credential.NamedCredentialName.UserName}` form is CONTRADICTED. Enhanced `AuthHeader` and `HttpHeader` parameters take a "formula of a header value that is evaluated at run time" (meta 264 L66299-66304, L93060-93073); the exact enhanced formula syntax and the "silently resolves to empty" behaviour are UNVERIFIED (2026-10-20).

---

## Output Artifacts

| Artifact | Description |
|---|---|
| External Credential record | Auth configuration: protocol, principal type, OAuth/JWT settings, permission set assignments |
| Named Credential record | Endpoint URL + reference to External Credential; the identifier used in Apex callout strings |
| Permission Set assignment | Links user population to External Credential principal, controlling callout access |
| Deployment runbook note | Documents that credential secrets must be re-entered manually post-deployment |
| Checker report | Output of `scripts/check_named_credentials.py` listing structural issues in metadata |

---

## Related Skills

- `apex/callouts-and-http-integrations` — Apex code patterns for making HTTP callouts using Named Credentials, including error handling and retry logic
- `apex/apex-named-credentials-patterns` — the Apex-side usage of the credential this skill creates
- `admin/connected-apps-and-auth` — OAuth Connected App setup on the Salesforce side; often a prerequisite when Salesforce itself is the OAuth server
- `security/service-account-credential-rotation` — rotation of the service-account secrets stored in the credential
