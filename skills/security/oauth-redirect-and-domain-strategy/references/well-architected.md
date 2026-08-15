# Well-Architected Notes — OAuth Redirect and Domain Strategy

## Relevant Pillars

- **Security** — Primary pillar. The callback allow-list is the control that stops
  an authorization code being delivered somewhere an attacker chose. Its strength is
  entirely a function of how narrow the list is: every extra line — a `localhost`
  entry left in production, a callback for a decommissioned environment, a partner's
  URL nobody re-verified — is another place a code can legitimately land. PKCE is
  the complementary control that stops an intercepted code being exchanged, and the
  platform's guidance is to apply it beyond public clients: "we always recommend
  implementing PKCE for public clients. We also strongly recommend that you implement
  PKCE for private clients."

- **Reliability** — This domain fails by string mismatch, and string mismatches are
  binary: the flow works or it does not, with no degraded mode. The failure also
  leaves almost no Salesforce-side evidence — it surfaces as a browser redirect
  carrying an error parameter, with no debug log and often nothing in Login History
  because no login occurred. Reliability here means client-side logging built before
  it is needed, and a configuration model where the only thing that varies per
  environment is one environment variable.

- **Operational Excellence** — Consumer keys are immutable after save and globally
  unique. Sandbox refreshes replace or destroy connected apps. Domain changes touch
  systems outside the org entirely. The artifact that makes all of this governable is
  a redirect matrix with an owner and a verification date per row — without it, a
  cutover is executed by discovery.

- **Performance** — Not a factor in configuration, but pointing clients at the org's
  My Domain rather than `login.salesforce.com` removes a redirect hop from every
  authentication, and removes an entire class of library-specific redirect bugs.

## Architectural Trade-offs

**One connected app for all environments vs one per environment.** A single
definition deployed everywhere, with every environment's callback as a line in
`callbackUrl`, gives one consumer key, one rotation operation, and a client whose
only per-environment variable is the login host. The cost is that a compromised
production secret is the same secret the sandboxes use, and any environment's
callback is technically valid for any org holding that app. Separate apps make
production and sandbox tokens non-interchangeable and blast-radius them apart, at
the cost of N keys, N rotations, and N reconfigurations after every sandbox refresh —
and the keys can never be reconciled afterwards, because they are immutable. Pick
deliberately; the failure mode of picking by accident is the second one.

**My Domain host vs `login.salesforce.com`.** The generic hosts still work and are
one fewer thing to configure. They also redirect, and library behaviour across that
redirect varies — some cache the pre-redirect host for the token request, some drop
`state`. Pointing at My Domain directly costs an environment variable and removes
the variance. For anything beyond a single first-party client, take the variable.

**PKCE required vs optional.** Requiring it is the right default and the platform
recommends it for private clients too. The trade is that enabling it is a hard cut:
"any authorization code flow variations that don't implement it fail." An older
library that does not send `code_challenge` breaks the moment the flag flips, with no
warning period. The sequencing is therefore: verify on the wire that the client sends
both `code_challenge` and `code_verifier`, then require it — never the reverse.

**`localhost` in the callback list.** It is genuinely useful and it grants that
anyone able to run a listener on a developer's machine can complete an authorization
for the org. Keeping it in non-production apps only is the clean answer. Keeping it
in production is sometimes operationally necessary and should then carry a written
reason and a removal date, so it is a decision rather than a residue.

**Where the login host lives.** A build-time constant is simpler and makes the
sandbox name part of a build artifact — so a refresh under a different name is a code
change. An environment variable is one more deployment concern and makes the same
refresh a configuration change. Given how routinely sandboxes are refreshed and
renamed, the variable pays for itself immediately.

## Anti-Patterns

1. **One connected app per environment by default.** Multiplies immutable consumer
   keys, multiplies rotation, diverges the client's configuration per environment,
   and breaks on every sandbox refresh.

2. **Expecting wildcard or prefix callback matching.** Salesforce matches against
   stored values; treat it as byte-identical. Trailing slashes, case, scheme, an
   explicit `:443`, and library-appended query parameters are all mismatches.

3. **Comma-separating multiple callbacks.** The documented separator is a line
   break (`\r` programmatically). A comma makes the whole field one malformed string
   and breaks every environment on the app at once.

4. **Omitting `isPkceRequired`.** The defaults differ between `ConnectedApp` and
   `ExternalClientApplication`, so silence means different behaviour on each — a live
   migration hazard.

5. **Hardcoding the login host.** Embeds the sandbox name in a build artifact and
   inherits whatever redirect behaviour the client library has when pointed at
   `login.salesforce.com`.

6. **Leaving `localhost` in production.** A permanent grant to anything that can
   listen on a developer's machine, and nothing ever fails to draw attention to it.

7. **Scoping a domain change to the org.** IdP configuration, webhook
   registrations, and partner allow-lists are outside your change control and their
   owners' lead time is the cutover's real critical path.

8. **Refreshing a sandbox without an OAuth step.** The connected app and its
   consumer key are replaced or destroyed, and the login host may change with the
   sandbox name.

9. **Diagnosing a redirect mismatch without client-side logs.** There is no
   Salesforce-side evidence to find. The authorize and token requests, logged at the
   client, are the only artifacts that answer the question.

## Official Sources Used

- Metadata API Developer Guide — ConnectedApp / ConnectedAppOauthConfig: `callbackUrl` ("It's the OAuth `redirect_uri`"), the multiple-callback newline rule and the `\r` separator, `consumerKey` immutability from API 32.0 with its length/format/global-uniqueness constraints, `isPkceRequired` and its behaviour, `scopes`, `sessionTimeout` — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_connectedapp.htm
- Metadata API Developer Guide — ExternalClientApplication and its OAuth settings (`isPkceRequired` defaulting to `true`, `isSecretRequiredForRefreshToken`, `isRefreshTokenRotationEnabled`) — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_externalclientapplication.htm
- Salesforce Help — My Domain Login and Application URL Formats — https://help.salesforce.com/s/articleView?id=xcloud.domain_name_url_formats.htm&type=5
- Salesforce Help — My Domain URL Format Changes with Enhanced Domains Deployment — https://help.salesforce.com/s/articleView?id=platform.domain_name_url_format_changes_enable_enhanced.htm&type=5
- Salesforce Help — Considerations for Enhanced Domains — https://help.salesforce.com/s/articleView?id=platform.domain_name_enhanced_considerations.htm&type=5
- Salesforce Help — Salesforce Enhanced Domains FAQ (KB 000393816) — https://help.salesforce.com/s/articleView?id=000393816&type=1
- Salesforce Help — Sandbox Login Link Does Not Reflect the My Domain URL (KB 000383649; the `--<sandbox>.sandbox.my.salesforce.com` format) — https://help.salesforce.com/s/articleView?id=000383649&type=1
- Salesforce Help — OAuth 2.0 Web Server Flow for Web App Integration — https://help.salesforce.com/s/articleView?id=platform.remoteaccess_oauth_web_server_flow.htm&type=5
- Salesforce Well-Architected — Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html

<!-- UNVERIFIED: the specific list of near-miss mismatches (trailing slash, host
     case, explicit :443, appended query parameter) is derived from the general
     OAuth 2.0 redirect-URI matching rules in RFC 6749 §3.1.2 and from the
     documented statement that Salesforce "validates the callback URL specified
     by the app by matching it with one of the values". Salesforce does not
     publish a per-character normalisation table, so treat these as the safe
     operating assumption rather than as a quoted platform rule. -->
<!-- UNVERIFIED: the claim that some OAuth client libraries mishandle the
     login.salesforce.com -> My Domain redirect (caching the pre-redirect host,
     or dropping `state`) is practitioner experience, not documented Salesforce
     behaviour. The redirect itself is documented; the library-side
     consequences are not. -->
<!-- UNVERIFIED: "a sandbox refresh replaces or destroys the connected app and
     changes its consumer key" was not verified against the sandbox refresh
     documentation in this pass. The recommendation to deploy connected apps
     from source as part of post-refresh is sound regardless, but confirm the
     exact refresh behaviour before writing it into a runbook as fact. -->
