# LLM Anti-Patterns — OAuth Redirect and Domain Strategy

Mistakes AI assistants reliably make when asked about Salesforce OAuth callbacks,
My Domain, or a `redirect_uri` mismatch.

## Anti-Pattern 1: One Connected App Per Environment

**What the LLM generates:** "Create a connected app in each org — production, UAT,
and each sandbox — with that environment's callback URL."

**Why it happens:** Connected apps are org-scoped objects, so per-org creation is
the shape the model expects. Nothing in the prompt signals that the callback field
holds a list.

**Correct pattern:**

```
callbackUrl holds MULTIPLE values:

  "You can enter multiple callback URL values. At run time, Salesforce
   validates the callback URL specified by the app by matching it with one of
   the values. You must separate each callback URL with line breaks. To enter
   a new line programmatically, use the \r line break character."

  <callbackUrl>https://orders.example.com/oauth/callback
https://uat.orders.example.com/oauth/callback
https://dev1.orders.example.com/oauth/callback</callbackUrl>

One app definition, deployed to every org. The client then varies only its
login host, from an environment variable.

Why this matters: the consumer key is immutable after save ("In API version
32.0 and later, you can set this field's value only during creation") and must
be globally unique. Per-environment apps give every environment a different,
unchangeable client id - so rotation is N operations and a sandbox refresh
silently invalidates one of them.
```

**Detection hint:** an answer that creates more than one connected app for a single
logical application, or a `callbackUrl` element containing exactly one URL for an
application that clearly has several deployments.

---

## Anti-Pattern 2: Suggesting a Wildcard or Prefix Callback

**What the LLM generates:** "Use `https://orders.example.com/*` to cover all your
callback paths," or "the callback acts as a prefix, so sub-paths are allowed."

**Why it happens:** Other allow-list features in Salesforce (Trusted URLs) do
support wildcards, and some OAuth providers do prefix matching. The model
generalises.

**Correct pattern:**

```
Salesforce matches the incoming redirect_uri against one of the STORED VALUES.
There is no documented wildcard, prefix, or normalisation behaviour. Treat the
match as byte-identical.

These are all DIFFERENT strings and each fails:
  trailing slash          .../callback/
  host or path case       .../Callback
  scheme                  http:// vs https://
  explicit default port   :443
  appended query param    ?src=email

If you need extra values round-tripped, use the protocol's `state` parameter -
it is carried separately and is NOT part of the redirect URI.

If you genuinely need several paths, list each one as its own line.
```

**Detection hint:** `*` in a `callbackUrl`, or an explanation containing "prefix,"
"starts with," or "sub-path" for callback matching.

---

## Anti-Pattern 3: Hardcoding the Login Host

**What the LLM generates:**

```javascript
const LOGIN_URL = 'https://test.salesforce.com';
// or
const LOGIN_URL = 'https://acme--uat.sandbox.my.salesforce.com';
```

**Why it happens:** The model needs a concrete value to produce working code, and
`test.salesforce.com` is the most-documented sandbox host.

**Correct pattern:**

```
Two problems with a literal.

1. login.salesforce.com and test.salesforce.com still work but REDIRECT to the
   org's My Domain. Some OAuth libraries follow that cleanly; others cache the
   pre-redirect host for the token request or drop `state` across it, producing
   failures that look intermittent. Point clients at My Domain directly:

     production  https://<mydomain>.my.salesforce.com
     sandbox     https://<mydomain>--<sandboxname>.sandbox.my.salesforce.com

2. A literal embeds the sandbox NAME in a build artifact. A refresh under a
   different name, or a new sandbox, then needs a code change.

  const LOGIN_URL = process.env.SF_LOGIN_URL;
  if (!LOGIN_URL) { throw new Error('SF_LOGIN_URL is required'); }
```

**Detection hint:** any string literal containing `salesforce.com` in generated
client code, especially `test.salesforce.com`.

---

## Anti-Pattern 4: Omitting `isPkceRequired`

**What the LLM generates:** a complete `ConnectedApp` with `callbackUrl`,
`consumerKey`, and `scopes`, and no PKCE element.

**Why it happens:** PKCE is optional in the metadata schema, so omitting it produces
valid XML. It is also a newer concern than most of the training corpus.

**Correct pattern:**

```
Write it explicitly on BOTH app types, because the defaults differ:

  ConnectedApp                  default FALSE  ("The default value is false.",
                                 API 59.0 and later)
  ExternalClientApplication     default TRUE   ("If set to true (default) Proof
                                 Key for Code for Exchange (PKCE) is required")

The defaults are OPPOSITES.

That difference is a live migration hazard: a client that worked against a
connected app fails immediately against an External Client App, having changed
nothing.

  <isPkceRequired>true</isPkceRequired>

And note the consequence of enabling it: "any authorization code flow
variations that don't implement it fail." Verify the client sends
code_challenge on authorize and code_verifier on token exchange BEFORE
flipping it on.

Salesforce's recommendation: "we always recommend implementing PKCE for public
clients. We also strongly recommend that you implement PKCE for private
clients."
```

**Detection hint:** a generated connected app or External Client App with no
`isPkceRequired` element.

---

## Anti-Pattern 5: Answering "redirect_uri_mismatch" with "Check Your Callback URL"

**What the LLM generates:** "This error means the callback URL doesn't match — check
the connected app configuration."

**Why it happens:** It is true, and it is the entire content of most search results
for the error.

**Correct pattern:**

```
Give the diagnosis procedure, not the restatement:

  1. Log the exact redirect_uri the CLIENT sends, from the wire, on BOTH the
     authorize and the token request. They must be identical to each other.
     Do not read it from a config file.
  2. Copy the stored callbackUrl out of the connected app into the same buffer
     and diff character by character. Trailing whitespace in the stored value
     is invisible in the UI and is a real cause.
  3. Confirm the environment. A UAT client pointing at the production connected
     app produces an identical error.
  4. Check for library-appended query parameters on the redirect.

Say why this procedure is necessary: the failure surfaces as a browser redirect
with an error parameter. There is usually NO Salesforce-side log, no Setup page
showing the rejected attempt, and often nothing in Login History because no
login occurred. The client's own logs are the only evidence.
```

**Detection hint:** an answer to a redirect mismatch that contains no logging or
comparison step.

---

## Anti-Pattern 6: Leaving `localhost` in a Production Connected App

**What the LLM generates:** a callback list including
`http://localhost:3000/oauth/callback`, with no caveat, for a production app.

**Why it happens:** Local development is a real need and the entry is genuinely
useful in a dev app. The production distinction is not in the prompt.

**Correct pattern:**

```
State what it grants: anyone who can run a listener on a developer's machine -
malware, another local process, a compromised dependency's postinstall script -
can complete an authorization flow for your org.

Keep localhost callbacks in NON-PRODUCTION connected apps. If a production
entry is genuinely required, record the reason and a removal date in the app's
description, and add "no localhost callbacks in production" to the release
checklist.

Note the scheme too: http:// on localhost is the one place it is conventional,
which makes it easy to leave a plain-HTTP entry in a list that is otherwise
all HTTPS.
```

**Detection hint:** `localhost` or `127.0.0.1` in a callback list presented for
production use, with no removal condition.

---

## Anti-Pattern 7: Scoping a Domain Change to the Salesforce Org

**What the LLM generates:** an enhanced-domains or My Domain change plan covering
Apex, LWC, and metadata.

**Why it happens:** Those are the artifacts the model can reason about and the ones
in the repository it was shown.

**Correct pattern:**

```
Half the affected configuration is outside your change control:

  Inside the org      Named Credentials, Remote Site Settings, Trusted URLs,
                      Apex string literals, LWC/Aura fetch targets, email
                      template absolute links
  Outside the org     IdP SAML/OIDC configuration, webhook registrations at
                      every provider, partner allow-lists, monitoring probes

Sweep the repo:
  grep -rEn '\.(na|eu|ap|cs|um)[0-9]+\.salesforce\.com' .
  grep -rn 'my.salesforce.com' --include='*.cls' --include='*.js' .

Then produce a matrix with an OWNER and a CONFIRMATION DATE per external item.
Those owners are outside your organisation and their lead time is the cutover's
real critical path - not the Salesforce change itself.
```

**Detection hint:** a domain cutover plan with no external-system inventory and no
named owners outside the team.

---

## Anti-Pattern 8: Treating a Sandbox Refresh as Unrelated to OAuth

**What the LLM generates:** a sandbox refresh checklist covering data masking, user
deactivation, and email deliverability — with nothing about connected apps.

**Why it happens:** Those are the canonical refresh concerns, and connected apps do
not appear in most refresh documentation.

**Correct pattern:**

```
A refresh can change both strings the client depends on:

  - the connected app in the sandbox is replaced by the copy from production,
    or disappears, and its consumer key changes
  - the login host changes if the sandbox is recreated under a different name

Add to the post-refresh runbook:
  - redeploy connected apps from source (never create them by hand in a
    sandbox)
  - reissue and redistribute consumer secrets to the clients that use them
  - confirm SF_LOGIN_URL for every client pointed at that sandbox

And make the login host an environment variable, so a name change is a
deployment setting rather than a code change.
```

**Detection hint:** a sandbox refresh or environment strategy answer that mentions
integrations but not connected apps or consumer keys.
