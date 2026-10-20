# Gotchas — Named Credentials Setup

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: A Principal No Permission Set Enables Blocks Callouts

**What happens:** Callouts through an Enhanced Named Credential fail even though the External Credential is correctly configured with valid OAuth tokens. UNVERIFIED (2026-10-20): the HTTP 401 / `System.CalloutException: Unauthorized` outcome and that the message omits Permission Sets are observed, not in the corpus. The documented rule is that users assigned to a permission set that enables the principal "can make callouts" (meta 264 L97687-97690).

**When it occurs:** Any time an External Credential principal exists that no permission set enables through `externalCredentialPrincipalAccesses` (API 59.0+, meta 264 L97495-97497). UNVERIFIED (2026-10-20): that this was not required for legacy credentials; legacy Per User identity uses `PermissionSetExternalDataSourceAccess` for external data sources (meta 264 L97708-97716). Also occurs when a new integration user or permission set is added to the org after initial setup.

**How to avoid:** After creating each principal under an External Credential, enable it on the Permission Sets whose users will make callouts (`ExternalCredential-Principal` in `externalCredentialPrincipalAccesses`). Add this as a mandatory item on the setup review checklist. The check script (`check_named_credentials.py`) flags External Credential principals that no permission-set file in the inspected metadata enables.

---

## Gotcha 2: Credential Secrets Are Not Deployed — They Must Be Re-Entered in Every Org

**What happens:** A Named Credential and External Credential are deployed from sandbox to production via Metadata API (or Salesforce CLI). The deployment succeeds. The integration then fails immediately in production because the stored values (OAuth client secret, password, access token) were not carried over.

**When it occurs:** Packaged credentials "don't include the access tokens or certificates" and need post-install steps (pkg2 264 L9543-9567). The reason given covers any Metadata API deploy, including sandbox-to-production: "the standard Metadata API can't fully expose the definition of a credential and render sensitive information like tokens in plain text" (pkg2 264 L9543-9544). UNVERIFIED (2026-10-20): scratch-org spin-up and sandbox copy are not addressed.

**How to avoid:** Every deployment runbook for integrations using Named Credentials must include a mandatory post-deployment step: "Log into target org > Setup > Named Credentials > External Credentials > re-enter credential secrets for each principal." Treat this the same as rotating a password. Document in the runbook which specific principals need re-entry and who is authorized to perform the step.

---

## Gotcha 3: Authorization Code Callback URL Must Match What the IdP Registered

**What happens:** Users attempting to authorize a Per User External Credential via the per-user authentication page ("My Personal Information > External Credential", pkg2 264 L9567) are redirected to the external IdP, complete login, and then receive an error from the external system ("redirect_uri_mismatch" or equivalent). The OAuth flow never completes and the user's token is never stored.

**When it occurs:** Whenever the External Credential Developer Name is changed after the callback URL has already been registered in the external IdP, or when the initial registration used the wrong casing or an older name. UNVERIFIED (2026-10-20): the callback URL shape `https://{myDomain}.my.salesforce.com/services/authcallback/{ExternalCredentialDeveloperName}`, its case sensitivity and the "redirect_uri_mismatch" symptom are not in the corpus (the only `authcallback` example is an auth provider, apexdev 264 L21292).

**How to avoid:** Lock in the External Credential Developer Name before registering the callback URL in the external IdP. Treat the developer name as immutable once the IdP registration is complete. If the developer name must change, update the registered redirect URI in the external system first, then rename the credential in Salesforce, and notify Per User principals to re-authorize.

---

## Gotcha 4: Header Formulas Copied From Legacy Credentials Need Re-Testing in Enhanced Ones

**What happens:** Custom header formulas copied from legacy Named Credentials can send an empty or wrong header in Enhanced credentials, which is hard to trace. UNVERIFIED (2026-10-20): the earlier claim that legacy used `{!$Credential.LegacyNCName.UserName}` and enhanced used `{!$Credential.ExternalCredentialDeveloperName.FieldName}`, and that the value "resolves silently to empty", are not in the corpus. The documented Apex callout merge fields carry no credential name: `{!$Credential.Username}`, `{!$Credential.Password}`, `{!$Credential.OAuthToken}` (apexdev 264 L34926-34960), so the legacy form shown here is CONTRADICTED.

**When it occurs:** During migration from legacy to enhanced Named Credentials when custom header formulas are copy-pasted. Enhanced credentials add `AuthHeader` (on the External Credential) and `HttpHeader` (on the Named Credential) parameters whose value is "a formula of a header value that is evaluated at run time" (meta 264 L66299-66304, L93060-93073).

**How to avoid:** After migrating any Named Credential that uses formula headers, audit every header formula against the parameter definition. Test with a live callout and confirm the header value is populated by checking the external service's request logs.

---

## Gotcha 5: Per-User Callouts Fail in Async Apex (Batch, Queueable, Scheduled) Without the Correct Running User (UNVERIFIED 2026-10-20)

**What happens:** A Per User External Credential works correctly in a synchronous Apex context (e.g., triggered from a screen flow or button) but throws an auth exception when the same callout code runs in a batch job, scheduled Apex, or a future method.

**When it occurs:** UNVERIFIED (2026-10-20): this whole gotcha is not in the corpus. Async Apex running as the user who enqueued the job, with an integration user or admin who has never completed the Per User OAuth authorization flow, is the suspected cause; Salesforce then cannot find a stored per-user token.

**How to avoid:** Per User External Credential principals are architecturally incompatible with headless async Apex. For batch or scheduled callouts, use a Named Principal (org-wide) instead. If the callout genuinely must act as a specific user in an async context, the pattern is: capture the user context synchronously (e.g., in a trigger or flow), make the callout in the synchronous context or chain a queueable that can identify the user's stored token through a different mechanism.
