# OAuth Redirect / Domain Plan

## Connected Apps

| App | Env | Login Host | Callback URL | Owner |
|---|---|---|---|---|

## My Domain

- Production name:
- Naming convention for sandboxes:
- Hardcoded-URL audit completed? Y/N

## Enhanced Domains Cutover

- Target date:
- Inventory scan complete? Y/N
- Email templates reviewed? Y/N
- External systems notified? Y/N

## Monitoring

- [ ] `redirect_uri_mismatch` dashboard in place.
- [ ] Alert on post-release spike.
- [ ] Runbook for sandbox-refresh Connected App reconfigure.

## Sign-Off

- [ ] All callback URLs are exact (no wildcards, no prefixes).
- [ ] All clients point at the correct login host per env.
- [ ] All hardcoded URLs in Apex / LWC / templates audited.
