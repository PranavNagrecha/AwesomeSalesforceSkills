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
| Auth type required by external service? | OAuth 2.0 / Basic / JWT / AWS / Custom |
| OAuth grant type (if OAuth)? | Authorization Code / Client Credentials / JWT Bearer |
| Org-wide or per-user authentication? | Named Principal / Per User / Anonymous |
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
| Principal Type | Named Principal / Per User / Anonymous |
| Principal Name | |
| Permission Sets assigned to principal | |

**OAuth Callback URL (Per User only):**
`https://<myDomain>.my.salesforce.com/services/authcallback/<ExternalCredentialDeveloperName>`

Confirm this URL is registered in external IdP: [ ]

---

## Named Credential Configuration

| Field | Value |
|---|---|
| Label | |
| Developer Name | |
| URL (base endpoint, no trailing slash) | |
| External Credential | |
| Allow Formulas in HTTP Header | Yes / No |
| Allow Formulas in HTTP Body | Yes / No |

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
- [ ] Principal added with correct type (Named Principal / Per User / Anonymous)
- [ ] Permission Set(s) assigned to the principal
- [ ] For OAuth Authorization Code: callback URL registered in external IdP
- [ ] For Client Credentials: token endpoint tested and client secret entered in vault
- [ ] For JWT: certificate alias confirmed in Certificate and Key Management
- [ ] Named Credential created and linked to External Credential
- [ ] Named Credential URL has no trailing slash
- [ ] Formula headers enabled only if actively used
- [ ] For Per User: affected users notified to authorize at User Settings > Authentication Settings for External Systems
- [ ] Deployment runbook updated to include post-deploy credential re-entry step
- [ ] Test callout executed from Apex (anonymous window or test class) — HTTP 200 confirmed
- [ ] Remote Site Settings confirmed (Named Credentials auto-add the endpoint to the allowlist)

---

## Post-Deployment Runbook Note

> Named Credential and External Credential metadata structure is deployable.
> Credential secrets (passwords, client secrets, tokens) are NOT deployed.
> After every deployment to a new org, an admin must:
> 1. Log into the target org.
> 2. Navigate to Setup > Named Credentials > External Credentials.
> 3. Edit each principal and re-enter vault-stored credential values.
> 4. For Per User: notify each user to re-authorize via User Settings.

Responsible admin in target org: ___________________

---

## Notes

(Record any deviations from the standard pattern, non-standard scopes, custom header formulas used, or future migration work for any legacy Named Credentials encountered.)
