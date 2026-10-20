# Named Credentials Setup — Work Template

Use this template when setting up or reviewing Named Credentials and External Credentials for an outbound integration.

---

## Scope

**Skill:** `named-credentials-setup`

**Request summary:** (fill in what is being configured or reviewed)

**Org:** (sandbox / production / scratch org name)

**Target environment:** (URL of external service)

---

## Context Gathered

Answer these before starting configuration:

| Question | Answer |
|---|---|
| Enhanced or legacy Named Credentials model? | |
| Auth type required by external service? | Oauth / Basic / AwsSv4 / Custom (Jwt, JwtExchange, NoAuthentication, Password are marked reserved on External Credential, api_meta 264 L66193-66197; the same row says select Jwt for a direct token system, L66199, and Password for on-premises Files Connect, L66201-66202) |
| OAuth grant type (if OAuth)? | Authorization Code / Client Credentials / JWT Bearer |
| Org-wide or per-user authentication? | Named Principal / Per User (Anonymous is legacy-only) |
| Which users or permission sets need callout access? | |
| Will this credential be deployed across environments? | Yes / No |
| External IdP callback URL registration needed? | Yes / No |
| Certificate needed (JWT)? | Yes / No — alias if yes: |

---

## External Credential Configuration

| Field | Value |
|---|---|
| Label | |
| Developer Name | |
| Protocol | |
| Flow Type (OAuth 2.0) | |
| Authorization Endpoint URL | |
| Token Endpoint URL | |
| Client ID | |
| Scope | |
| Principal Type | Named Principal / Per User |
| Principal Name | |
| Permission Sets enabling the principal | |

**OAuth Callback URL (Per User only):**
`https://<myDomain>.my.salesforce.com/services/authcallback/<ExternalCredentialDeveloperName>`

Confirm this URL is registered in external IdP: [ ]

---

## Named Credential Configuration

| Field | Value |
|---|---|
| Label | |
| Developer Name | |
| URL (base endpoint; the guide's own example ends with `/`, meta 264 L93128, so a trailing slash is a convention, UNVERIFIED 2026-10-20) | |
| External Credential | |
| Allow Merge Fields in HTTP Header | Yes / No |
| Allow Merge Fields in HTTP Body | Yes / No |

---

## Apex Reference String

```
callout:<NamedCredentialDeveloperName>/<relative-path>
```

Example: `callout:My_Service_NC/api/v1/resources`

---

## Checklist

Work through this list before closing the task:

- [ ] External Credential created with correct protocol and flow type
- [ ] Principal added with correct type (Named Principal / Per User)
- [ ] Permission Set(s) enable the principal (`externalCredentialPrincipalAccesses`)
- [ ] For OAuth Authorization Code: callback URL registered in external IdP
- [ ] For Client Credentials: token endpoint tested and client secret entered in vault
- [ ] For JWT: certificate alias confirmed in Certificate and Key Management
- [ ] Named Credential created and linked to External Credential
- [ ] Named Credential URL and Apex path joined without `//` (convention, UNVERIFIED 2026-10-20)
- [ ] Merge fields in header/body enabled only if actively used
- [ ] For Per User: affected users notified to authenticate (My Personal Information > External Credential, pkg2 264 L9567)
- [ ] Deployment runbook updated to include post-deploy credential re-entry step
- [ ] Test callout executed from Apex (anonymous window or test class) — HTTP 200 confirmed
- [ ] No Remote Site Setting needed for the named credential endpoint (apexdev 264 L34761-34763); hard-coded endpoints still need one

---

## Post-Deployment Runbook Note

> Named Credential and External Credential metadata structure is deployable.
> Credential secrets (passwords, client secrets, tokens) are NOT deployed.
> After every deployment to a new org, an admin must:
> 1. Log into the target org.
> 2. Navigate to Setup > Named Credentials > External Credentials.
> 3. Edit each principal and re-enter vault-stored credential values.
> 4. For Per User: notify each user to re-authenticate via their personal External Credential page.

Responsible admin in target org: ___________________

---

## Notes

(Record any deviations from the standard pattern, non-standard scopes, custom header formulas used, or future migration work for any legacy Named Credentials encountered.)
