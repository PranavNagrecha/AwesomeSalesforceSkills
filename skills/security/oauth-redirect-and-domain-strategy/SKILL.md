---
name: oauth-redirect-and-domain-strategy
description: "Design Connected App OAuth callback URLs, My Domain naming, Enhanced Domains cutover, and cross-environment redirect handling. Trigger keywords: oauth redirect uri, connected app callback, my domain, enhanced domains, sandbox url change. NOT for end-user login flow UX, Experience Cloud branding, or SAML-only SSO configuration — use admin/connected-app-troubleshooting."
category: security
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
  - Operational Excellence
triggers:
  - "configure oauth callback url"
  - "connected app redirect uri"
  - "enhanced domains cutover"
  - "my domain strategy"
  - "sandbox oauth endpoint"
tags:
  - security
  - oauth
  - my-domain
  - connected-app
inputs:
  - List of Connected Apps and their client redirect URIs
  - Environment inventory (prod, UAT, dev sandboxes)
  - Current My Domain / Enhanced Domains state
outputs:
  - Redirect URI matrix per Connected App per environment
  - Enhanced Domains cutover plan
  - Login host strategy (login.salesforce.com vs My Domain)
dependencies: []
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-08-14
---

# OAuth Redirect And Domain Strategy

Every OAuth failure in Salesforce that is not a permission problem is a **string
matching** problem. Three strings have to line up, and they are owned by three
different parties:

| String | Owned by | Where it lives |
|---|---|---|
| **Login host** | The org | `https://<mydomain>.my.salesforce.com`, or `https://<mydomain>--<sandbox>.sandbox.my.salesforce.com` |
| **`redirect_uri`** | The client | Sent on the authorize request and again on the token request |
| **Callback URL** | The connected app | `ConnectedAppOauthConfig.callbackUrl` — "It's the OAuth `redirect_uri`" |

The failure mode is binary and leaves almost no Salesforce-side evidence: a browser
redirect carrying an error parameter, no debug log, and often nothing in Login
History because no login occurred. Client-side logging is the primary diagnostic and
has to exist before you need it.

---

## Before Starting

1. **Enumerate the applications, not the orgs.** One logical application deployed to
   four environments is one connected app with four callback lines — not four
   connected apps.

2. **Know that the consumer key is immutable.** "In API version 32.0 and later, you
   can set this field's value only during creation. After you define and save the
   value, it can't be edited." It must also be globally unique.

3. **Establish whether clients can send PKCE** before requiring it. Turning it on is
   a hard cut: "any authorization code flow variations that don't implement it fail."

4. **Inventory what lives outside the org** if a domain change is coming — IdP
   configuration, webhook registrations, partner allow-lists. Their owners' lead time
   is the cutover's real critical path.

---

## Core Concepts

### `callbackUrl` is a newline-separated list

A Connected App accepts multiple callback URLs, newline-separated (`\r`
programmatically), and matches the app's requested URL against the list at run time —
quoted in full in [`references/gotchas.md`](references/gotchas.md).

```xml
<callbackUrl>https://orders.example.com/oauth/callback
https://uat.orders.example.com/oauth/callback
https://dev1.orders.example.com/oauth/callback</callbackUrl>
```

A comma makes the whole field one malformed string and breaks **every** environment
on the app at once.

### Matching is exact

There is no documented wildcard, prefix, or normalisation behaviour. Treat the match
as byte-identical. All of these are different strings from
`https://orders.example.com/oauth/callback`:

```text
https://orders.example.com/oauth/callback/        trailing slash
https://Orders.example.com/oauth/callback         host or path case
http://orders.example.com/oauth/callback          scheme
https://orders.example.com:443/oauth/callback     explicit default port
https://orders.example.com/oauth/callback?src=a   library-appended query parameter
```

Use the protocol's `state` parameter for anything that needs round-tripping — it is
carried separately and is not part of the redirect URI.

### PKCE defaults are opposites

| Type | `isPkceRequired` default |
|---|---|
| `ConnectedApp` | **`false`** — "The default value is `false`." (API 59.0 and later) |
| `ExternalClientApplication` | **`true`** — "If set to `true` (default) Proof Key for Code for Exchange (PKCE) is required for OAuth integration." |

A client that worked against a connected app can fail immediately against an
External Client App, having changed nothing. Write the field explicitly on both.

Platform guidance: "we always recommend implementing PKCE for public clients. We
also strongly recommend that you implement PKCE for private clients."

### Login host formats

| Environment | Host |
|---|---|
| Production | `https://<mydomain>.my.salesforce.com` |
| Sandbox | `https://<mydomain>--<sandboxname>.sandbox.my.salesforce.com` |

`login.salesforce.com` and `test.salesforce.com` still work but redirect to My
Domain, and client libraries differ in how cleanly they follow that redirect. Point
clients directly at My Domain, from an environment variable — never a build-time
constant, because the sandbox name is part of the host.

---

## Common Patterns

### Pattern A — one app, every environment

One connected app definition deployed to every org, with every environment's
callback as a line in `callbackUrl`. One consumer key, one rotation, and the client
varies only `SF_LOGIN_URL`. Full metadata in
[`references/examples.md`](references/examples.md), Example 1.

### Pattern B — separate apps where token isolation matters

Where production and sandbox tokens must be non-interchangeable, keep separate apps
— and write down the extra cost: N immutable keys, N rotations, N reconfigurations
after every sandbox refresh. Make it a decision, not an accident of the Setup UI.

### Pattern C — the redirect matrix

One row per connected app per environment: login host, `redirect_uri` the client
sends, the stored callback line it matches, the owner, and the date it was last
verified. This is the artifact that turns a domain change from discovery into
review.

### Pattern D — PKCE rollout in the safe order

Verify on the wire that the client sends `code_challenge` on authorize and
`code_verifier` on token exchange, *then* set `isPkceRequired` to `true`. Never the
reverse — there is no warning period.

---

## Decision Guidance

| Situation | Approach |
|---|---|
| One application, several environments | One connected app, several `callbackUrl` lines |
| Production and sandbox tokens must not be interchangeable | Separate apps, with the rotation cost documented |
| Client is a mobile or single-page app | `isPkceRequired` `true`; the client cannot hold a secret |
| Client library is old and unverified | Verify PKCE on the wire before requiring it |
| Redirect mismatch, configuration looks correct | Log the client's `redirect_uri` on both requests and diff against the stored line |
| Several callback paths needed | One line each — no wildcard, no prefix |
| Developers need local flow | `localhost` in non-production apps only; if production, record why and a removal date |
| Enhanced domains cutover | Redirect matrix + repo sweep + external-system owner list |
| Sandbox refresh scheduled | Redeploy connected apps from source; reissue secrets; confirm `SF_LOGIN_URL` |

---

## Recommended Workflow

1. **Build the redirect matrix**: one row per connected app per environment, with
   login host, client `redirect_uri`, stored callback line, owner, and verification
   date. Include integrations with no redirect (client credentials) so the inventory
   is complete.
2. **Consolidate to one connected app per application** where token isolation is not
   required, moving every environment's callback into `callbackUrl` as its own line.
3. **Set `isPkceRequired` explicitly** on every app of both types, after verifying
   on the wire that clients send `code_challenge` and `code_verifier`.
4. **Move the login host into an environment variable** in every client, pointing at
   the org's My Domain rather than `login.salesforce.com`.
5. **Sweep for hardcoded hosts** across Apex, LWC, metadata, email templates, and
   then across systems outside the org — IdP configuration, webhook registrations,
   partner allow-lists — assigning an owner and a confirmation date to each external
   item.
6. **Rehearse any domain change in a full sandbox**, exercising every row of the
   matrix rather than one representative flow.
7. **Add connected app redeployment and secret reissue** to the sandbox post-refresh
   runbook, and add "no `localhost` callbacks in production" to the release
   checklist.

---

## Review Checklist

- [ ] One connected app per application, unless token isolation is a written decision
- [ ] Every environment's callback present as its own newline-separated line
- [ ] No commas, no wildcards, no prefixes in `callbackUrl`
- [ ] No trailing whitespace on any stored callback value
- [ ] `isPkceRequired` written explicitly on every connected app and External Client App
- [ ] PKCE verified on the wire before being required
- [ ] Client login host is an environment variable pointing at My Domain
- [ ] No `salesforce.com` string literals in client code
- [ ] No `localhost` callbacks in production apps, or a recorded reason and removal date
- [ ] Client-side logging of the authorize and token requests exists before it is needed
- [ ] Redirect matrix has an owner and a verification date for every row
- [ ] External systems (IdP, webhooks, partner allow-lists) enumerated with owners
- [ ] Sandbox post-refresh runbook includes connected app redeploy and secret reissue

---

## Salesforce-Specific Gotchas

Full detail with quotes in [`references/gotchas.md`](references/gotchas.md).

1. **The consumer key is immutable after save** and must be globally unique.
2. **Callback matching is exact**, and the near-misses are invisible on screen.
3. **Multiple callbacks are newline-separated**, not comma-separated — a comma
   breaks every environment at once.
4. **`isPkceRequired` defaults are opposites** between `ConnectedApp` (`false`) and
   `ExternalClientApplication` (`true`).
5. **`login.salesforce.com` works, then redirects**, and libraries differ in how they
   handle it.
6. **A sandbox refresh changes the host and can destroy the app.**
7. **`localhost` callbacks outlive development** and nothing ever fails to flag them.
8. **The domain change is only partly inside Salesforce.**
9. **The failure leaves no Salesforce-side evidence.**
10. **One app per environment multiplies rotation and breaks on refresh.**

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Redirect matrix | App × environment, with login host, client `redirect_uri`, stored callback line, owner, and verification date |
| Consolidated connected app metadata | One definition per application with newline-separated callbacks and explicit `isPkceRequired` |
| Client configuration standard | `SF_LOGIN_URL` as an environment variable, with the per-environment values and who sets them |
| Hardcoded-host sweep results | Repo grep output plus the external-system inventory with owners and confirmation dates |
| Cutover rehearsal record | Which matrix rows were exercised in the sandbox, and the result of each |

---

## Related Skills

- `security/connected-app-security-policies` — the session, refresh token, and IP
  policies that sit alongside the OAuth configuration on the same app
- `security/oauth-token-management` — token lifetime, refresh rotation, and
  revocation once the flow works
- `security/api-only-user-hardening` — the identity a client-credentials app binds
  to, which has no redirect at all
- `devops/sandbox-refresh-and-templates` — the refresh event that invalidates
  connected apps and login hosts
