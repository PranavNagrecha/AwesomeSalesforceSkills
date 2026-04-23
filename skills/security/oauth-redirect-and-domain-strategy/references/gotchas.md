# OAuth Redirect / Domain — Gotchas

## 1. Exact Match, Not Prefix

`https://app/cb` does not match `https://app/cb?token=...`.
`redirect_uri_mismatch` at runtime. Register the exact URL.

## 2. HTTP vs HTTPS Matters

`http://...` and `https://...` are different URIs. Register HTTPS; HTTP
is rejected.

## 3. Trailing Slash Counts

`https://app/cb/` and `https://app/cb` are different. Match the client's
sent value exactly.

## 4. Sandbox Refresh Resets Connected App

A sandbox refresh can reset Connected App configuration to the prod
version. Re-apply sandbox-specific callback URLs after refresh.

## 5. test.salesforce.com Redirects Are Sometimes Rejected

Some OAuth client libraries do not follow the 302 from
`test.salesforce.com` to the sandbox My Domain. Point clients directly
at the sandbox My Domain.

## 6. Mobile Custom Schemes Are Case-Sensitive

`com.acme.app://callback` is case-sensitive in some client libs and
environments. Keep consistent.

## 7. Enhanced Domains Breaks Hardcoded Links In Email Templates

Absolute URLs in email templates pointing to old instance URLs stop
working. Audit templates as part of cutover.

## 8. Redirect URL On External System Registrations

Some external webhook registrations use the Salesforce instance URL.
If My Domain changes or Enhanced Domains changes patterns, update the
external registrations too.
