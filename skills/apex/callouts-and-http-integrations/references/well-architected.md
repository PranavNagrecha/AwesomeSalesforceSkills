# Well-Architected Notes — Callouts And HTTP Integrations

## Relevant Pillars

### Security

This skill directly affects secret management, endpoint governance, and remote-system identity. Named Credentials and External Credentials are security controls as much as convenience features.

Tag findings as Security when:
- tokens or endpoints are embedded in Apex
- org-wide versus per-user identity is unclear or misapplied
- outbound requests bypass the configured authentication boundary

### Reliability

Remote systems fail in ways Salesforce code cannot control. Timeout management, response classification, and post-commit boundaries are reliability concerns, not optional polish.

Tag findings as Reliability when:
- callout failures are silently swallowed
- triggers or save transactions perform fragile outbound work inline
- non-200 responses or malformed payloads are not classified explicitly

## Architectural Tradeoffs

- **Synchronous lookup vs async sync:** inline callouts can improve immediacy, but they increase user
  latency and transaction fragility. The platform makes the choice partly for you — a trigger cannot
  call out synchronously at all (apexdev L14900–14903), and any code path that has already done DML,
  enqueued a job, run a batch, or called a `@future` method is blocked from calling out for the rest
  of the transaction (apexdev L35379–35380).
- **Per-user identity vs org identity:** `PerUserPrincipal` "provides access control at the
  individual user level" (api_meta L63806–63808), which matches remote systems that audit by end
  user, but every user must authenticate individually before their first callout works.
  `NamedPrincipal` — one credential set for all users — is the lower-operations default.
- **Simple wrapper vs richer retry framework:** not every integration needs exponential backoff, but
  every integration needs explicit failure classification. Where the wrapper ends matters more than
  its sophistication: Apex has no `sleep`, so any in-transaction backoff burns CPU against the
  10,000 ms sync / 60,000 ms async ceiling (apexdev L19579). Backoff belongs on a job boundary.
- **Named Credential header parameters vs Apex-built headers:** headers that never vary per record
  (tenant id, API version, static auth) belong on the Named Credential as `HttpHeader` parameters
  (api_meta L90326–90331), which keeps them out of source control and out of the 100 KB per-header
  cap (apexrefguide L216680). Headers that vary per request must be built in Apex.
- **Continuation vs Queueable for slow remote systems:** a Continuation is the only mechanism for a
  long-running call that must return to a user-facing page, but it costs a separate limit set — at
  most 3 parallel and 3 chained callouts, a 1 MB response cap, and `HttpRequest.setTimeout` is
  ignored in favour of the continuation's own 120 s (apexdev L36301–36315). Batch-shaped work belongs
  in a Queueable instead. See apex/continuation-callouts.

## Anti-Patterns

1. **Hardcoded endpoint and token management** — breaks environment portability and secret hygiene,
   and drags in a Remote Site Setting the code does not mention (apexdev L34293–34299).
2. **Trigger-based direct callouts** — fragile and difficult to operate under transaction
   constraints; the guide requires async from a trigger (apexdev L14900–14903).
3. **Happy-path-only integration code** — assumes success and treats non-200 or malformed responses
   as impossible. A 200 carrying an HTML maintenance page is the case that reaches production.
4. **Retry loops without an idempotency key** — a 5xx or a transport failure means *unknown*, not
   *failed*. Retrying a bare POST can double-write on the remote side.
5. **One mock, one status code** — a test suite that only registers a 200 mock proves parsing, not
   integration behaviour, and never exercises the retry ladder.

## Official Sources Used

- Apex Developer Guide v67.0, Summer '26 — "Invoking Callouts Using Apex" L34251+, "Named
  Credentials as Callout Endpoints" L34318+ (the `callout:` scheme and why Named Credentials replace
  Remote Site Settings), "HTTP Classes" L35288+ (Http / HttpRequest / HttpResponse element list),
  "Testing HTTP Callouts" L35383+ and "Performing DML Operations and Mock Callouts" L35675+
  (`Test.setMock` requirement and the `Test.startTest` ordering rule), "Callout Limits and
  Limitations" L35841+ (100 callouts, 120 s cumulative, 10 s default timeout, Developer Edition
  concurrency, `Expect: 100-Continue`), "Apex Callouts in Read-Only Mode" L35868+, "Releasing
  Savepoints and Using Callouts" L8725+ (both exact `CalloutException` messages), Triggers
  "Implementation Considerations" L14900 (callouts must be async from a trigger), Queueable
  `Database.AllowsCallouts` L16164, `@Future(callout=true)` L5134, and Continuation-Specific Limits
  L36288+. https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf
- Apex Reference Guide v67.0 — `Http` L216114, `HttpCalloutMock` L216168 (the `respond` contract),
  `HttpRequest` L216215 with `setTimeout` semantics and the 1–120,000 ms range (L216720), `setHeader`
  100 KB (L216680), `setBody` 6 MB/12 MB (L216506), compression (L216271–216279),
  `setClientCertificateName` (L216582+); `HttpResponse` L216751 with `getBody` / `getBodyAsBlob` size
  caps (L216863, L216887); `Limits.getCallouts()` / `getLimitCallouts()` L220503, L220532 (the
  runtime callout budget used in `references/code-examples.md`).
- Metadata API Developer Guide — `NamedCredential` L89887+ and `NamedCredentialParameter` L90253+
  (`namedCredentialType` enum, `Url` / `Authentication` / `HttpHeader` / `ClientCertificate`
  parameter types, `calloutStatus`, `generateAuthorizationHeader`, the 56.0 deprecations),
  `ExternalCredential` L63601+ (`authenticationProtocol` enum, `NamedPrincipal` vs
  `PerUserPrincipal`, `principal` removed in 58.0), `RemoteSiteSetting` L103804+
  (`disableProtocolSecurity`, `isActive`, `url`). Every XML block in
  `references/code-examples.md` is built from these field tables.
  https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf
- Salesforce App Limits Cheat Sheet — Per-Transaction Apex Limits L72–91 (100 callouts, 120 s
  cumulative, 6 MB/12 MB heap, 50 sync / 1 async `System.enqueueJob`, CPU time) and Static Apex
  Limits L386–415 (10 s default callout timeout, 6 MB/12 MB callout request-or-response size and the
  footnote that it counts against heap). Used for every numeric limit stated in this package.
- Salesforce Well-Architected — Trusted (secret management, least-privilege remote identity) and
  Resilient (failure classification, graceful degradation) framing for the pillar tagging above.
  https://architect.salesforce.com/well-architected/overview
