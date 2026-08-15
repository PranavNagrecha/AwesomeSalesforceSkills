# Well-Architected Notes — Webhook Signature Verification

## Relevant Pillars

- **Security** — Primary pillar. For a webhook exposed through a public Salesforce
  Site, the HMAC check *is* the authentication boundary; there is no session, no
  user, and no network control in front of it. Three properties must hold together
  and each fails independently: **authenticity** (the sender holds the shared
  secret), **integrity** (the bytes were not altered — which is why the raw body
  must be hashed, never a re-serialised copy), and **freshness** (the request is
  not a replay of an earlier valid one, which the signature alone never
  establishes). A verifier that satisfies the first two and skips the third is the
  most common shape of a broken webhook endpoint.

- **Reliability** — Webhook delivery is at-least-once with retries on any non-2xx
  and on timeout. The handler therefore has to be idempotent by construction — an
  upsert against the provider's event id on an External Id, Unique field — and has
  to return quickly enough that the provider never classifies a success as a
  timeout. Doing real work inline converts a slow dependency into duplicated
  processing and an endpoint the provider marks unhealthy.

- **Operational Excellence** — The secret has a lifecycle. Rotation without dual
  acceptance is a silent outage measured in 401s; the design must accept both the
  current and previous secret across a cutover and drop the old one as a separate,
  deliberate change. Observability should record the decision (event id, type,
  verified yes/no, processing status) and never the material (raw body, signature
  header, secret).

- **Performance** — The synchronous request/response size ceiling is 6 MB (12 MB
  for asynchronous Apex). A provider posting near that ceiling has outgrown the
  webhook shape and should be moved to a notification-plus-pull design where the
  event carries an identifier and Salesforce fetches the payload on its own
  schedule.

## Architectural Trade-offs

**Public Site vs provider-authenticated endpoint.** A Salesforce Site makes the
endpoint reachable by anyone on the internet, which is the only option when the
provider cannot attach a bearer token to outbound webhooks. It concentrates all
risk on the HMAC check and on guest-user permissions. A Connected App with the
OAuth 2.0 client credentials flow bound to a dedicated integration user gives you a
second, independent gate — the token proves *who* is calling — and lets you revoke
access without changing the signing secret. Prefer the authenticated shape when the
provider supports it, and keep the signature check in both cases: they answer
different questions.

**Verify-then-stage vs verify-and-process.** Staging (write the raw event, return
200, process asynchronously) decouples your processing time from the provider's
timeout and makes redelivery cheap. It costs a staging object, a retention policy
for what is often sensitive payload data, and an extra hop before the business
effect is visible. Processing inline is simpler and is defensible only when the
work is a single small DML and the volume is low. The moment a callout, an email,
or a Flow enters the handler, staging is the only correct answer.

**Storing the payload vs storing only the decision.** Retaining raw payloads makes
reprocessing after a bug trivial and is often what turns a bad afternoon into a
replay. It also means payment and PII data now lives in a Salesforce object with
its own sharing model, its own report exposure, and its own retention obligation.
If you retain, restrict the object to the integration's permission set and give it
an explicit deletion policy; if you do not, accept that a processing bug is
unrecoverable without asking the provider to redeliver.

**Symmetric (HMAC) vs asymmetric (RSA/ECDSA) verification.** HMAC requires both
sides to hold the same secret, which means Salesforce holds a key capable of
*forging* requests. Asymmetric schemes give Salesforce only a public key, so a
compromise of the org cannot be used to forge webhooks to anyone else. You do not
usually get to choose — the provider does — but when a provider offers both, the
asymmetric option is materially better and Apex supports it through
`Crypto.verify(algorithmName, data, signature, certDevName)` with the certificate
held in Certificate and Key Management rather than in a metadata field.

**Replay tolerance width.** A narrow window (Stripe's default 300 seconds) bounds
replay tightly but makes the endpoint sensitive to clock skew between the provider
and the platform, and to genuine delivery delays during a provider incident. A wide
window is forgiving and lengthens the replay opportunity. Pair whatever window you
choose with idempotency so that a replay inside the window is still a no-op.

## Anti-Patterns

1. **Hashing anything other than the raw body.** Re-serialising through
   `JSON.serialize` reorders keys and normalises whitespace, so verification fails
   for every request — including genuine ones — and the usual "fix" is to delete
   the check.

2. **Comparing digests by hand.** `Crypto.verifyHMac` exists and takes the same
   effort to call as `generateMac` plus an equality test. Using the platform
   verifier removes an entire class of review argument.

3. **Treating a valid signature as a fresh request.** Without a timestamp
   tolerance and an idempotency key, one captured delivery is replayable
   indefinitely and every provider retry is a duplicate record.

4. **Doing the work inline.** Providers time out in single-digit seconds. A handler
   that creates records, runs a Flow, and makes a callout before responding turns
   one event into repeated deliveries of the same event.

5. **Keeping the secret in source or in a Custom Setting.** A literal is in every
   clone of the repo and every deployment log; a Custom Setting is readable by
   anyone with the object permission and surfaces in describes and reports.
   Protected Custom Metadata is the right home, read through `getAll()` so it costs
   no query.

6. **Verbose rejection responses.** Echoing the computed MAC, the expected format,
   or the reason for failure gives an attacker an oracle. Return the same terse
   4xx for every verification failure and log the detail internally.

7. **Rotating the secret without dual acceptance.** In-flight deliveries signed
   with the old value fail silently. Accept both across the cutover — Stripe hands
   you this for free by sending multiple `v1=` values — and remove the previous
   secret in a separate change.

## Official Sources Used

- Apex Reference Guide — Crypto Class, `verifyHMac(algorithmName, data, privateKey, macToVerify)` — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_classes_restful_crypto.htm
- Apex Reference Guide — Crypto Class, `generateMac(algorithmName, input, privateKey)` (4 KB key cap, Base64 symmetry rule) — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_classes_restful_crypto.htm
- Apex Reference Guide — Crypto Class, `verify(algorithmName, data, signature, certDevName)` — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_classes_restful_crypto.htm
- Apex Reference Guide — RestRequest Class (`requestBody` as Blob, `headers` as `Map<String, String>`, `remoteAddress`) — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_class_System_RestRequest.htm
- Apex Reference Guide — RestContext Class — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_class_System_RestContext.htm
- Apex Developer Guide — Exposing Apex Classes as REST Web Services (`@RestResource`, URL mapping rules, 6 MB / 12 MB request size) — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_rest_intro.htm
- Apex Developer Guide — Apex Governor Limits (heap and request size) — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_gov_limits.htm
- Apex Developer Guide — Custom Metadata Types in Apex (`getAll()` costs no SOQL) — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_metadata_types.htm
- Salesforce Help — Configure Public Access Settings for a Site — https://help.salesforce.com/s/articleView?id=platform.configuring_public_access_settings.htm&type=5
- Salesforce Help — OAuth 2.0 Client Credentials Flow for Server-to-Server Integration — https://help.salesforce.com/s/articleView?id=platform.remoteaccess_oauth_client_credentials_flow.htm&type=5
- Salesforce Well-Architected — Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html

## Third-Party Provider Contracts Referenced

These are provider behaviours, not Salesforce behaviours. They change on the
provider's schedule, so re-check them before relying on an exact string.

- Stripe — Receive Stripe events in your webhook endpoint (the `Stripe-Signature` `t=` / `v1=` grammar, `signed_payload = timestamp + "." + body`, "ignore all schemes that aren't `v1`" to prevent downgrade attacks, the 5-minute default tolerance, multiple active signatures for up to 24 hours during a secret roll, and the constant-time comparison recommendation) — https://docs.stripe.com/webhooks
- GitHub — Validating webhook deliveries (`X-Hub-Signature-256`, the `sha256=` prefix, and "Never use a plain `==` operator ... consider using a method like `secure_compare` ... which performs a 'constant time' string comparison") — https://docs.github.com/en/webhooks/using-webhooks/validating-webhook-deliveries
