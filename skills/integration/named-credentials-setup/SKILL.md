---
name: named-credentials-setup
description: "Named Credentials and External Credentials configuration for secure outbound callouts: per-user vs per-org authentication, legacy vs enhanced Named Credentials, external credential principal types (Named Principal, Per User, Anonymous), OAuth 2.0 and JWT flows, and credential deployment. NOT for callout code patterns, Apex HTTP implementation, or OAuth server-side flow debugging."
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
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-04
---

# Named Credentials Setup

This skill activates when a practitioner needs to configure Named Credentials or External Credentials for secure Salesforce outbound callouts — covering the full setup lifecycle from choosing principal type through deployment. It does not cover the Apex callout code that uses the credential once it exists.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Enhanced vs Legacy:** Determine which model the org is using. Winter '23 introduced Enhanced Named Credentials (split into Named Credential + External Credential). Legacy Named Credentials are still supported but deprecated in favor of the enhanced model. New orgs default to enhanced.
- **Auth type:** Confirm whether the external service requires OAuth 2.0 (Authorization Code or Client Credentials), basic auth (username + password), JWT, AWS Signature V4, or a custom header formula. This determines the External Credential protocol.
- **Scope:** Confirm whether all users share one set of credentials (Named Principal) or each user authenticates individually (Per User). Per-user requires each user to complete an OAuth flow and adds user education overhead.
- **Deployment:** Named Credential and External Credential metadata structures (endpoint URL, protocol, principal type) are deployable via Metadata API. The actual credentials (passwords, tokens, secrets) are stored in Salesforce's encrypted vault and are NOT exported or deployed — they must be re-entered in each org.
- **Limits:** Legacy Named Credentials: 200 per org. Enhanced Named Credentials and External Credentials have separate limits; check current release notes for exact counts. Per-org limit enforcement is real and should be factored into multi-integration architectures.

---

## Core Concepts

### Enhanced Named Credentials: Endpoint + Auth Are Separated

Since Winter '23, Salesforce splits the configuration into two records:

- **Named Credential** — holds the endpoint URL and a reference to an External Credential. This is what Apex references with `callout:NamedCredentialName`.
- **External Credential** — holds the authentication configuration: protocol, principal type, OAuth settings, custom headers, or JWT configuration.

One External Credential can back multiple Named Credentials pointing to different paths on the same service. This is a significant architecture win over legacy credentials where each endpoint-auth pair was one record.

**Legacy Named Credentials** combined URL + auth in a single record. They still work in existing orgs but Salesforce strongly recommends migrating to enhanced. In Apex, both models use the same `callout:Name` syntax.

### External Credential Principal Types

The principal type controls which identity is used for the callout:

| Principal Type | Who authenticates | Credential storage |
|---|---|---|
| **Named Principal** | The org (all users share one credential) | One secret stored org-wide |
| **Per User** | Each Salesforce user authenticates individually | One credential per user, stored against their user record |
| **Anonymous** | No authentication sent | No credentials required |

**Named Principal** is the right default for server-to-server integrations (e.g., background jobs calling an external API with a service account). **Per User** is correct when the external service enforces user-level access control and needs to act on behalf of the individual (e.g., a user accessing their own Google Drive data).

**Permission Sets control access to principals.** Assign a Permission Set to an External Credential principal to restrict which users can make callouts through it. Without a permission set assignment, users cannot execute callouts even if the credential is correctly configured.

### OAuth 2.0 Flows in External Credentials

Salesforce supports several OAuth 2.0 grant types:

- **Authorization Code** — used for Per User principals where Salesforce redirects the user to the external identity provider. The callback URL must be `https://{yourDomain}/services/authcallback/{ExternalCredentialDeveloperName}`. Users complete the flow under User Settings > Authentication Settings for External Systems.
- **Client Credentials** — used for Named Principal (org-wide) where Salesforce exchanges a client ID + secret for a bearer token. No user interaction required.
- **JWT Bearer** — Salesforce signs a JWT using a stored certificate (configured under Certificate and Key Management) and presents it to the token endpoint. No user secret needed if the external IdP trusts the certificate.

Token refresh is handled automatically by Salesforce once the initial token is obtained.

### Credential Vault and Deployment Boundaries

Salesforce stores all credential secrets (passwords, client secrets, access tokens) in an encrypted vault. This has two important consequences:

1. **Secrets are not readable via SOQL, REST API, or Apex.** You can write to the vault (by entering the credential in Setup) but you cannot read back the stored value. This is by design.
2. **Metadata API deployment does NOT carry secrets.** Deploying Named Credential metadata to a sandbox or production moves the structural configuration only. An admin must re-enter actual credential values post-deployment. Document this in runbooks.

---

## Common Patterns

### Mode 1: Create a New Named Credential (Enhanced Model)

**When to use:** Any new integration in an org on Winter '23+ (or any org being migrated from legacy).

**How it works:**

1. **Setup > Named Credentials > External Credentials > New**
   - Developer Name: use kebab-case or snake_case consistently (e.g., `MyServiceExtCred`)
   - Label: human-readable name for Setup UI
   - Protocol: select the auth type (OAuth 2.0, Password, JWT, AWS Signature V4, Custom)
   - If OAuth 2.0: enter Authorization Endpoint URL, Token Endpoint URL, Client ID, Client Secret, Scope, and select the grant type
   - Add a Principal: set principal type (Named Principal / Per User / Anonymous), give it a name

2. **Assign Permission Sets to the Principal**
   - Under the principal, add the Permission Sets whose users should be allowed to call out
   - Without this, callouts fail silently with an authentication error

3. **Setup > Named Credentials > Named Credentials > New**
   - URL: the base URL of the external service (e.g., `https://api.example.com/v1`)
   - External Credential: select the External Credential created above
   - Allow Formulas in HTTP Header / Body: enable only if the credential uses formula-based merge fields

4. **In Apex:** `req.setEndpoint('callout:MyNamedCredential/resource');`

5. **Validate:** Make a test callout from Apex (Developer Console or test class) and confirm HTTP 200 response. Check Setup > Named Credentials for the OAuth token status if using OAuth flows.

**Why not hard-coded URLs with stored credentials:** Hard-coded endpoints bypass Salesforce's allowed callout endpoint enforcement, expose credentials in Apex or Custom Settings readable by any user with SOQL access, and require code deployments to rotate credentials.

---

### Mode 2: Audit or Review Existing Named Credentials

**When to use:** Pre-release review, security audit, or assessing org credential hygiene.

**How it works:**

1. Run the bundled checker: `python3 scripts/check_named_credentials.py --manifest-dir path/to/metadata`
2. In Setup, navigate to Named Credentials and note which are legacy (no linked External Credential) vs enhanced.
3. For each Enhanced credential, verify:
   - Principal type matches the integration pattern (Named Principal for service-to-service, Per User for user-delegated)
   - Permission Sets are assigned to each principal (empty principal = credential accessible to nobody or everybody depending on version)
   - OAuth callback URL is registered in the external IdP's allowed redirect URIs
   - Custom header formulas do not embed literal secrets (use merge field syntax instead)
4. For legacy credentials: assess migration priority. Legacy credentials cannot use Per User principals or formula-based custom headers.

---

### Mode 3: Troubleshoot Authentication Failures

**When to use:** Callouts returning 401 Unauthorized or generic "System.CalloutException: Unauthorized".

**How it works:**

1. **Check Permission Set assignment:** The most common cause of 401 errors is a missing Permission Set on the External Credential principal. Navigate to External Credentials > [record] > Principals and confirm the calling user's Profile or Permission Set is listed.
2. **Per-user flow not completed:** If using Per User principal, the individual user must have authorized the external system via User Settings > Authentication Settings for External Systems. If the authorization is missing, Salesforce cannot attach a token to the callout.
3. **OAuth token expired and not refreshing:** Check if the external IdP requires offline_access scope (or equivalent) for refresh tokens. Without a refresh token, Salesforce cannot renew silently and users must re-authorize.
4. **Callback URL mismatch:** For Authorization Code flow, confirm the callback URL in the external IdP matches exactly: `https://{yourMyDomain}.my.salesforce.com/services/authcallback/{ExternalCredentialDeveloperName}`. Case sensitivity and trailing slashes can cause failures.
5. **JWT certificate not trusted:** If using JWT Bearer, confirm the certificate in Salesforce's Certificate and Key Management matches the public key registered with the external IdP.
6. **Named Credential URL path double-slash:** Appending a path to the Named Credential endpoint in Apex can produce `//` if the base URL ends with `/` and the path starts with `/`. Always strip the trailing slash from the Named Credential URL.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Server-to-server background integration (batch, platform events) | Named Principal + Client Credentials OAuth or Password | No user in context; org-wide credential is correct |
| User-delegated external service (user's own account on external system) | Per User + Authorization Code OAuth | Service acts on behalf of the individual user |
| Public API with no authentication required | Anonymous principal | No credential management overhead |
| Service-to-service with mTLS or signed JWT | Named Principal + JWT Bearer | Certificate-based auth with no shared secret |
| Multiple endpoints on same service with same auth | One External Credential, multiple Named Credentials | External Credential is reusable across Named Credentials |
| Legacy Named Credential migration | Create parallel Enhanced NC, test, deprecate legacy | Enhanced model required for Per User and formula headers |
| Credential rotation in production | Update credential value in Setup UI; no deployment needed | Vault is separate from metadata; no code change required |

---


## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. Gather context — confirm the org edition, relevant objects, and current configuration state
2. Review official sources — check the references in this skill's well-architected.md before making changes
3. Implement or advise — apply the patterns from Core Concepts and Common Patterns sections above
4. Validate — run the skill's checker script and verify against the Review Checklist below
5. Document — record any deviations from standard patterns and update the template if needed

---

## Review Checklist

Run through these before marking a Named Credential setup complete:

- [ ] External Credential record has a principal with the correct type (Named Principal / Per User / Anonymous)
- [ ] Permission Set(s) are assigned to the External Credential principal
- [ ] For OAuth 2.0 Authorization Code: callback URL registered in external IdP's allowed redirect list
- [ ] For OAuth 2.0 Client Credentials or JWT: token endpoint tested and credential values entered
- [ ] Named Credential URL does not end with a trailing slash
- [ ] Allow Formulas in HTTP Header/Body is only enabled when formula-based merge fields are actively used
- [ ] For Per User: affected users notified to complete authorization under User Settings
- [ ] Deployment runbook documents that credential secrets must be re-entered post-deployment
- [ ] Test callout executed and HTTP 200 confirmed
- [ ] Legacy Named Credentials in scope of this project flagged for migration backlog

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Permission Set assignment is mandatory, not optional** — Even if an External Credential principal is correctly configured, no user can make callouts through it until at least one Permission Set is explicitly assigned to that principal. The error thrown is a generic auth failure that does not mention Permission Sets. This is the single most common cause of "it was set up correctly but still fails" support tickets.

2. **Deployment does not carry credential secrets** — Metadata API moves the Named Credential and External Credential structure (URL, protocol, principal type, scope) but not the vault-stored values (passwords, client secrets, access tokens). Post-deployment steps in a runbook must instruct an admin to re-enter these values. Forgetting this causes integrations to silently fail in target orgs.

3. **Legacy Named Credential formula merge fields use a different namespace** — Legacy credentials use `{!$Credential.NamedCredentialName.UserName}` syntax. Enhanced External Credentials use `{!$Credential.ExternalCredentialName.FieldName}`. Mixing the two syntaxes when migrating is a source of callout formula failures that are hard to diagnose because the merge field silently resolves to empty rather than throwing an error.

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

- `callouts-and-http-integrations` (apex) — Apex code patterns for making HTTP callouts using Named Credentials, including error handling and retry logic
- `connected-apps-and-auth` (admin) — OAuth Connected App setup on the Salesforce side; often a prerequisite when Salesforce itself is the OAuth server
- `apex-managed-sharing` (apex) — Not directly related but referenced when integration user permission design intersects with record sharing rules
