# Gotchas — OAuth Redirect and Domain Strategy

Non-obvious behaviours in Salesforce OAuth callback and domain configuration.
Grounded in the Metadata API Developer Guide and Salesforce Help (Summer '26,
API 67.0).

## Gotcha 1: The Consumer Key Is Immutable After Save

**What happens:** A connected app is created with a placeholder consumer key, or the
team decides to standardise key naming later. The field is read-only and there is no
way to change it.

> "In API version 32.0 and later, you can set this field's value only during
> creation. After you define and save the value, it can't be edited. The value must
> be alphanumeric, can't contain special characters or spaces, and must be between
> 8–256 characters. Consumer keys must be globally unique."
> — Metadata API Developer Guide, `ConnectedAppOauthConfig.consumerKey`

**When it occurs:** On the first connected app anyone creates by hand, and again
when a naming convention is introduced after the fact.

**How to avoid:** Decide the consumer key at creation, and prefer one connected app
deployed to every org over one app per org — because the key is per app, a
per-environment app design gives every environment a different client id that can
never be reconciled. Note "globally unique": the value must be unique across
Salesforce, not just your org, so a generic string will be rejected.

---

## Gotcha 2: Callback URL Matching Is Exact, and the Near-Misses Are Invisible

**What happens:** Authorization fails with a redirect-mismatch error while the
stored callback and the client's configured callback look identical on screen.

Any of these is a different string from `https://orders.example.com/oauth/callback`:

```text
https://orders.example.com/oauth/callback/        trailing slash
https://Orders.example.com/oauth/callback         host or path case
http://orders.example.com/oauth/callback          scheme
https://orders.example.com:443/oauth/callback     explicit default port
https://orders.example.com/oauth/callback?src=a   appended query parameter
```

**When it occurs:** Most often when an OAuth library appends its own parameters to
the redirect it sends, and when a stored value has trailing whitespace that the UI
does not render.

**How to avoid:** Log the `redirect_uri` from the *client*, on the wire, for both
the authorize and the token request — they must be identical. Paste the stored value
and the sent value into the same buffer and diff them. For anything you need
round-tripped, use the protocol's `state` parameter, which is carried separately and
is not part of the redirect URI.

---

## Gotcha 3: Multiple Callback URLs Are Newline-Separated, Not Comma-Separated

**What happens:** A second callback is added after the first with a comma or a
space. The whole field is then one malformed string and *every* environment fails,
including the one that worked before.

> "You can enter multiple callback URL values. At run time, Salesforce validates the
> callback URL specified by the app by matching it with one of the values. You must
> separate each callback URL with line breaks. To enter a new line programmatically,
> use the `\r` line break character."

**When it occurs:** When adding an environment to an existing app, and whenever the
value is assembled by a script that joins with `,` because that is the usual
convention.

**How to avoid:** In metadata, put literal newlines inside the element:

```xml
<callbackUrl>https://orders.example.com/oauth/callback
https://uat.orders.example.com/oauth/callback</callbackUrl>
```

In code, join with `\r`. After any change, re-test *every* environment on the app,
not just the one you added — a malformed separator breaks all of them at once.

---

## Gotcha 4: `isPkceRequired` Defaults Differently for Connected Apps and External Client Apps

**What happens:** A working client is migrated from a `ConnectedApp` to an
`ExternalClientApplication` and immediately fails every authorization, having
changed nothing on the client.

| Type | Documented default |
|---|---|
| `ConnectedApp` | **`false`.** "If set to `false`, you can still implement PKCE but it isn't required. The default value is `false`." (API 59.0 and later) |
| `ExternalClientApplication` | **`true`.** "If set to `true` (default) Proof Key for Code for Exchange (PKCE) is required for OAuth integration. If set to `false`, PKCE is optional." |

The defaults are opposites. A connected app created without the field has PKCE
*optional*; an External Client App created without it has PKCE *required*.

And when it is required, the consequence is total: "If set to `true`, the PKCE
extension is required and any authorization code flow variations that don't
implement it fail."

**When it occurs:** During any migration to External Client Apps, and whenever a
connected app is recreated from a template that omits the field.

**How to avoid:** Write `isPkceRequired` explicitly in every generated app of either
type. Before enabling it, verify the client actually sends `code_challenge` on the
authorize request and `code_verifier` on the token exchange — many older libraries
do not, and "we upgraded the library" is not evidence.

The platform's own recommendation is unambiguous: "we always recommend implementing
PKCE for public clients. We also strongly recommend that you implement PKCE for
private clients."

---

## Gotcha 5: `login.salesforce.com` Works, Then Redirects

**What happens:** Authentication works in one client library and fails, or behaves
intermittently, in another — with the same credentials and the same connected app.

`login.salesforce.com` and `test.salesforce.com` remain valid entry points but
redirect to the org's My Domain. Some OAuth libraries follow that redirect cleanly;
others cache the pre-redirect host for the token request, or drop the `state`
parameter across it.

**When it occurs:** With the second or third client library integrated against the
same org — the first one worked, so the host is assumed correct.

**How to avoid:** Point clients at the org's My Domain directly. Production is
`https://<mydomain>.my.salesforce.com`; a sandbox is
`https://<mydomain>--<sandboxname>.sandbox.my.salesforce.com`. No redirect, no
library-specific redirect behaviour to debug.

---

## Gotcha 6: A Sandbox Refresh Changes the Host and Can Destroy the App

**What happens:** After a refresh, every client pointed at the sandbox fails. The
connected app in the sandbox is gone, or its consumer key has changed, and the login
host may have changed too if the sandbox was recreated under a different name.

**When it occurs:** At every sandbox refresh, which is a routine event that rarely
carries an OAuth checklist.

**How to avoid:** Two habits.

1. **Deploy the connected app as metadata**, from the same source as production, as
   part of the post-refresh deployment. Never create it by hand in a sandbox.
2. **Make the login host an environment variable**, never a build-time constant, so
   a name change is a deployment setting rather than a code change.

Add "redeploy connected apps and reissue their secrets" to the sandbox post-refresh
runbook, alongside the usual data masking and user deactivation steps.

---

## Gotcha 7: `localhost` Callbacks Outlive Development

**What happens:** `http://localhost:3000/oauth/callback` is added so developers can
run the flow locally, and it is still on the production connected app three years
later.

**When it occurs:** Always, because nothing fails when it is left in place.

**How to avoid:** Understand what it grants: anyone who can run a listener on a
developer's machine — malware, another local process, a compromised dependency's
postinstall script — can complete an authorization flow for your org. Keep localhost
entries in non-production connected apps only. Where a production entry is genuinely
required, record the reason and a removal date in the app's `description`, and put
"no localhost callbacks in production" in the release checklist so the next reviewer
catches it.

---

## Gotcha 8: The Domain Change Is Only Partly Inside Salesforce

**What happens:** An enhanced-domains cutover is rehearsed in a sandbox, deployed to
production, and breaks integrations that were never part of the rehearsal — a
partner's IdP configuration, a webhook registration, an allow-list at a vendor.

**When it occurs:** Whenever the cutover plan covers only artifacts under the team's
change control.

**How to avoid:** Sweep for hardcoded hosts inside the repository:

```bash
grep -rEn '\.(na|eu|ap|cs|um)[0-9]+\.salesforce\.com' .
grep -rn 'my.salesforce.com' --include='*.cls' --include='*.js' \
                              --include='*.html' --include='*.xml' .
```

and then enumerate the places that are not the repository: Named Credentials, Remote
Site Settings, Trusted URLs, email template absolute links, IdP SAML/OIDC
configuration, webhook registrations at every provider, and partner allow-lists. For
each external item, name the owner and the date they confirmed the new value — those
owners are outside your change control and their lead time is the cutover's real
critical path.

---

## Gotcha 9: The Failure Leaves No Salesforce-Side Evidence

**What happens:** A redirect mismatch surfaces as a browser redirect carrying an
error parameter. There is no debug log to open, no Setup page showing a rejected
attempt, and often nothing in Login History because no login occurred.

**When it occurs:** On every redirect-mismatch failure, which is why these
investigations stall.

**How to avoid:** Instrument the client. Log, at the client, the full authorize URL
and the full token request body (with the secret redacted) before sending. Those two
requests are the evidence, and the `redirect_uri` in each must match the other and
match a stored line. Build this logging before you need it — retrofitting it during
an outage costs a deploy.

---

## Gotcha 10: One Connected App Per Environment Multiplies Rotation and Breaks on Refresh

**What happens:** Four environments, four connected apps, four consumer keys. Secret
rotation is four coordinated operations across four teams, the client's
configuration diverges per environment, and a sandbox refresh silently invalidates
one of them.

**When it occurs:** By default, because "create a connected app" is what you do in
each org and nothing signals that the callback field is a list.

**How to avoid:** One connected app definition, deployed everywhere, with every
environment's callback as a line in `callbackUrl`. The client then varies only its
login host. Where production and sandbox tokens genuinely must be
non-interchangeable, keeping separate apps is defensible — but make it an explicit
decision with the extra rotation cost written down, not an accident of the Setup UI.
