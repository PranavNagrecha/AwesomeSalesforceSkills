# OAuth Redirect / Domain — Examples

## Example 1: Redirect URI Matrix (Multi-Env App)

Connected App `CustomerPortal`:

```text
Callback URLs (one per line, exact match):
https://portal.acme.com/callback
https://uat.portal.acme.com/callback
https://dev.portal.acme.com/callback
https://staging.portal.acme.com/callback
```

Client config:

```text
APP_ENV        SF_LOGIN_HOST                         CLIENT_REDIRECT
prod           acme.my.salesforce.com                https://portal.acme.com/callback
uat            acme--uat.sandbox.my.salesforce.com   https://uat.portal.acme.com/callback
dev            acme--dev.sandbox.my.salesforce.com   https://dev.portal.acme.com/callback
```

## Example 2: Enhanced Domains Inventory

```bash
grep -r "visual.force.com" apex/ lwc/ emailTemplates/
grep -r "\.lightning\.force\.com" apex/ lwc/
grep -r "na[0-9]+\.salesforce\.com" .
```

Any hits are candidates to rewrite to My Domain + stable path.

## Example 3: Sandbox Refresh Checklist

On refresh, the sandbox name may change (e.g., `dev3` → `dev4`). Impact:

- Sandbox My Domain host changes → client env vars update.
- Connected App callback URL in the refreshed sandbox resets to prod's
  values. Reconfigure UAT callbacks.
- Named Credentials pointing to the sandbox by host need update.

## Example 4: Mobile App Callback

Mobile app registered with callback `com.acme.app://callback`. Connected
App callback list must include that custom-scheme URI exactly.

## Example 5: OAuth Error Dashboard

Track in a report:

- Event: `LoginHistory` where `Status` = `Failed: redirect_uri_mismatch`.
- Trend by app, by env, by day. Spike after any release = regression
  in redirect config.
