# Gotchas — Named Credentials Setup

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Missing Permission Set Assignment Causes Silent Auth Failures

**What happens:** Callouts through an Enhanced Named Credential return HTTP 401 or throw `System.CalloutException: Unauthorized` even though the External Credential is correctly configured with valid OAuth tokens. The error message does not mention Permission Sets.

**When it occurs:** Any time an External Credential principal is created without at least one Permission Set assigned to it. This is required in the enhanced model but was not required for legacy Named Credentials, so practitioners migrating from legacy miss this step. Also occurs when a new integration user or permission set is added to the org after initial setup.

**How to avoid:** After creating each principal under an External Credential, immediately navigate to the Principals section and add the Permission Sets whose users will make callouts. Add this as a mandatory item on the setup review checklist. The check script (`check_named_credentials.py`) flags External Credential principals with no permission set assignments when inspecting metadata.

---

## Gotcha 2: Credential Secrets Are Not Deployed — They Must Be Re-Entered in Every Org

**What happens:** A Named Credential and External Credential are deployed from sandbox to production via Metadata API (or Salesforce CLI). The deployment succeeds. The integration then fails immediately in production because the vault-stored values (OAuth client secret, password, access token) were not carried over.

**When it occurs:** Every promotion from sandbox to production, every scratch org spin-up, and every org cloning scenario. Metadata API is intentionally designed to exclude vault secrets from the deploy payload.

**How to avoid:** Every deployment runbook for integrations using Named Credentials must include a mandatory post-deployment step: "Log into target org > Setup > Named Credentials > External Credentials > re-enter credential secrets for each principal." Treat this the same as rotating a password. Document in the runbook which specific principals need re-entry and who is authorized to perform the step.

---

## Gotcha 3: Authorization Code Callback URL Must Match the External Credential Developer Name Exactly (Case-Sensitive)

**What happens:** Users attempting to authorize a Per User External Credential via User Settings are redirected to the external IdP, complete login, and then receive an error from the external system ("redirect_uri_mismatch" or equivalent). The OAuth flow never completes and the user's token is never stored.

**When it occurs:** Whenever the External Credential Developer Name is changed after the callback URL has already been registered in the external IdP, or when the initial registration used the wrong casing or an older name. The Salesforce-generated callback URL is `https://{myDomain}.my.salesforce.com/services/authcallback/{ExternalCredentialDeveloperName}` — the developer name portion is case-sensitive.

**How to avoid:** Lock in the External Credential Developer Name before registering the callback URL in the external IdP. Treat the developer name as immutable once the IdP registration is complete. If the developer name must change, update the registered redirect URI in the external system first, then rename the credential in Salesforce, and notify Per User principals to re-authorize.

---

## Gotcha 4: Legacy Merge Field Namespace Does Not Work in Enhanced External Credentials

**What happens:** Custom header formulas copied from legacy Named Credentials (using `{!$Credential.LegacyNCName.UserName}` syntax) resolve silently to empty string in Enhanced External Credentials. The header is sent with no value, causing authentication failures that are hard to trace because no error is thrown on the Salesforce side.

**When it occurs:** During migration from legacy to enhanced Named Credentials when custom header formulas are copy-pasted. Enhanced External Credentials use `{!$Credential.ExternalCredentialDeveloperName.FieldName}` syntax, referencing the External Credential record (not the Named Credential record).

**How to avoid:** After migrating any Named Credential that uses formula headers, audit every header formula and update the record reference to point to the External Credential Developer Name. Test with a live callout and confirm the header value is populated by checking the external service's request logs.

---

## Gotcha 5: Per-User Callouts Fail in Async Apex (Batch, Queueable, Scheduled) Without the Correct Running User

**What happens:** A Per User External Credential works correctly in a synchronous Apex context (e.g., triggered from a screen flow or button) but throws an auth exception when the same callout code runs in a batch job, scheduled Apex, or a future method.

**When it occurs:** Async Apex runs as the user who enqueued the job, but in headless system contexts the "running user" may be an integration user or admin who has never completed the Per User OAuth authorization flow. Salesforce cannot find a stored per-user token and fails the callout.

**How to avoid:** Per User External Credential principals are architecturally incompatible with headless async Apex. For batch or scheduled callouts, use a Named Principal (org-wide) instead. If the callout genuinely must act as a specific user in an async context, the pattern is: capture the user context synchronously (e.g., in a trigger or flow), make the callout in the synchronous context or chain a queueable that can identify the user's stored token through a different mechanism.
