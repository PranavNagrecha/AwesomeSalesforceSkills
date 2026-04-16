# Eval: integration/named-credentials-setup

- **Skill under test:** `skills/integration/named-credentials-setup/SKILL.md`
- **Priority:** P0
- **Cases:** 3
- **Last verified:** 2026-04-16
- **Related templates:** `templates/apex/HttpClient.cls`
- **Related decision trees:** `standards/decision-trees/integration-pattern-selection.md`

## Pass criteria

The AI must always use Named Credential + External Credential (the modern
split), never inline endpoints or secrets, and match the right auth
protocol to the external system. Any response that hardcodes an endpoint
or stores a secret in Apex/CMDT fails.

## Case 1 — First-time Named Credential for an OAuth 2.0 client-credentials API

**Priority:** P0

**User prompt:**

> "I need Apex to call `https://api.vendor.com/v2/` using OAuth 2.0 client
> credentials. The vendor gave me a Client Id and Client Secret. Walk me
> through the setup."

**Expected output MUST include:**

- Split components: External Credential (holds secrets + protocol),
  Named Credential (holds URL + references External Credential),
  Permission Set (grants users access to the credential).
- Protocol: OAuth 2.0 — Client Credentials Grant. Configure token endpoint
  and scopes in the External Credential.
- Named Credential callout URL becomes `callout:My_Vendor/v2/...` — Apex
  never sees the real hostname.
- Principal: Named Principal with secret fields populated from the vendor.
- Permission Set grants `External Credential Principal Access`.
- Rotation plan: rotate Client Secret by editing the External Credential
  Principal — no redeployment.

**Expected output MUST NOT include:**

- Storing Client Secret in Custom Metadata or Custom Setting.
- Legacy "Named Credential with authentication protocol" (the pre-External-Credentials
  model) for new work.
- Hardcoding the hostname in Apex and "just adding a header".

**Rubric (0–5):**

- **Correctness:** External Credential + Named Credential split.
- **Completeness:** All four Setup pieces + permission set + rotation addressed.
- **Bulk safety:** N/A — score 5.
- **Security:** Lead criterion — zero secrets in metadata/source.
- **Citation of official docs:** Links to External Credentials setup doc.

**Reference answer (gold):**

"Setup in four parts:

1. **External Credential** (`My_Vendor_EC`): Authentication Protocol =
   OAuth 2.0, Grant Type = Client Credentials, Authentication URL =
   `https://api.vendor.com/oauth/token`, Scopes = what the vendor documents.
   Save.
2. **Named Principal** on the External Credential: Principal Type =
   Named Principal (single shared set of creds for server-to-server).
   Configure Client Id + Client Secret here — they're stored encrypted.
3. **Permission Set** (`My_Vendor_Access`): Enable `External Credential
   Principal Access` for the principal you just created. Assign to the
   integration user or to the profiles that will run the Apex callout.
4. **Named Credential** (`My_Vendor`): Label + Name, URL =
   `https://api.vendor.com/v2`, Authentication = select the External
   Credential from step 1. Allow Merge Fields in HTTP Header = off for now.

Apex:

```apex
HttpClient.Response res = new HttpClient()
    .namedCredential('My_Vendor')
    .path('/accounts/' + extId)
    .method('GET')
    .header('Accept', 'application/json')
    .send();
```

No hostname, no secret, no token-exchange code in Apex. Token acquisition is handled by the platform. Rotation: edit the Principal's secret, save — no deploy. Audit: `NamedCredential` + `ExternalCredential` metadata are version-controlled, but secrets are not."

## Case 2 — Migrating a legacy "Remote Site Setting + stored API key" pattern

**Priority:** P0

**User prompt:**

> "Our org has `Remote Site Settings` for 3 external APIs and the API keys
> are stored in a `Integration_Config__c` Custom Setting. Management wants
> this 'cleaned up'. What's the migration plan?"

**Expected output MUST include:**

- This is a P0 security debt — API keys in Custom Setting are plaintext
  in the org schema and exported on every full sandbox refresh.
- Migration plan per endpoint:
  - Create External Credential (API Key protocol).
  - Create Named Credential pointing at the endpoint.
  - Create Permission Set granting access.
  - Update Apex: replace `http.setEndpoint(Config.Endpoint__c)` +
    `http.setHeader('X-API-Key', Config.ApiKey__c)` with
    `callout:<NamedCredential>/path` and rely on EC to inject the header.
  - Delete the `Integration_Config__c` record AND the Custom Setting if
    unused.
  - Remove the Remote Site Setting (Named Credentials register the
    hostname automatically).
- Testing: `MockHttpResponseGenerator` in unit tests continues to work
  because the mock intercepts at the Apex layer.
- Rotation: now a 5-second admin action instead of a code deploy.

**Expected output MUST NOT include:**

- "Just rotate the keys and keep Custom Setting" — doesn't solve the root issue.
- Recommending Platform Encryption on the Custom Setting field (the key
  still sits in metadata and is extractable by admins).
- Big-bang migration — recommend per-endpoint iterative moves.

**Rubric (0–5):**

- **Correctness:** Frames the migration per endpoint with NC + EC.
- **Completeness:** Covers Apex changes + cleanup of legacy config.
- **Bulk safety:** N/A — score 5.
- **Security:** Lead criterion — only 5 if cleanup of the old Custom Setting is explicit.
- **Citation of official docs:** Links to Named Credentials migration guide.

**Reference answer (gold):**

"This is a real security issue, not cosmetic — API keys in a Custom Setting
are plaintext metadata and leak on every sandbox refresh.

Migrate one endpoint at a time:

1. **Pick endpoint A**. Create External Credential `API_A_EC` — protocol
   = Custom (or OAuth if the vendor supports it). Add a Custom Header
   Principal with `X-API-Key` = <the value>. Rotation = 90 days.
2. Create Named Credential `API_A` pointing at the hostname. Callout URL
   = `callout:API_A/...`.
3. Create Permission Set `API_A_Access`. Assign to the running user(s).
4. In Apex, change:
   `http.setEndpoint(Config.API_A_Endpoint__c)` → `callout:API_A` prefix.
   `http.setHeader('X-API-Key', Config.API_A_Key__c)` → delete (EC
   injects it).
5. Run your test suite with `MockHttpResponseGenerator` — tests should
   still pass.
6. Deploy. Verify in a sandbox first. Remove Remote Site Setting for the
   hostname (NC registers it automatically).
7. Delete the `Integration_Config__c` record for API_A. Once all 3 are
   migrated, delete the Custom Setting definition.

Repeat for endpoints B and C. No big-bang — each migration is self-contained
and reversible.

Ongoing: rotation becomes a Setup task instead of a code deploy. Document the new rotation cadence in `standards/security/credential-rotation.md`."

## Case 3 — Per-user OAuth vs Named Principal

**Priority:** P0

**User prompt:**

> "I need to call the Google Calendar API on behalf of each user to sync
> their meetings. Should I use a Named Principal like I did for my vendor
> integration?"

**Expected output MUST include:**

- No — this is per-user delegation. Use External Credential with
  Authentication Protocol = OAuth 2.0, Principal Type = `Per User`.
- Each user completes the OAuth consent flow once to link their Google
  account; tokens stored per-user encrypted.
- `callout:Google_Calendar/...` in Apex runs under the running user's
  token automatically.
- If the user hasn't authenticated, the callout fails with a specific
  error; surface it in LWC with a button that invokes a connection flow.
- Permission Set enables `External Credential Principal Access` for the
  Per-User Principal.

**Expected output MUST NOT include:**

- Using a Named Principal (wrong model for per-user flows).
- Storing per-user tokens in a custom object (the platform does this for you).
- JWT bearer flow (wrong grant type for per-user UX flows).

**Rubric (0–5):**

- **Correctness:** Recommends Per-User principal type.
- **Completeness:** Covers consent flow + fallback UX for unauthenticated users.
- **Bulk safety:** N/A — score 5.
- **Security:** Tokens never stored in application data; revoked when user deactivated.
- **Citation of official docs:** Links to Per-User OAuth docs.

**Reference answer (gold):**

"No — a Named Principal is shared credentials for server-to-server. You
want **Per-User** so each user's Google token is stored separately.

Setup:

1. External Credential `Google_Calendar_EC`, Protocol = OAuth 2.0, Grant
   Type = Authorization Code, Principal Type = `Per User`. Scopes include
   `https://www.googleapis.com/auth/calendar.readonly`.
2. Named Credential `Google_Calendar` pointing at `https://www.googleapis.com/calendar/v3`.
3. Permission Set grants `External Credential Principal Access` for the
   Per-User principal.

User first-time UX:

- Attempt callout. If Salesforce has no token for this user, callout fails
  with `EXTERNAL_CREDENTIAL_NOT_AUTHORIZED` (or the configured error).
- In the LWC, catch this and show a `Connect to Google Calendar` button
  that opens the consent flow (built-in redirect from Salesforce).
- After consent, the token is stored encrypted in the platform; the same
  callout now succeeds.

Revocation:

- Deactivate the Salesforce user → their per-user token is no longer used.
- Users can disconnect in Setup → Authentication Settings for External
  Systems.

Never store tokens in a custom object — the platform does it for you encrypted, and auditing uses Setup."
