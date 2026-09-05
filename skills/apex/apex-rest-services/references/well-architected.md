# Well-Architected Notes — Apex REST Services

## Relevant Pillars

### Security

Custom REST endpoints expose Salesforce behavior to external callers, so sharing, CRUD/FLS, and contract design all carry security consequences.

Tag findings as Security when:
- the endpoint lacks explicit sharing or secure data access
- raw exceptions or sensitive fields are exposed
- caller identity assumptions are undocumented

### Reliability

Reliable REST contracts use explicit status codes, stable payloads, and clear versioning.

Tag findings as Reliability when:
- error handling is ambiguous
- incompatible changes are introduced without versioning
- resource classes perform too much logic inline

### Operational Excellence

APIs must be supportable. Stable contracts and clear logs reduce client-side confusion and operational toil.

Tag findings as Operational Excellence when:
- endpoint behavior is hard to diagnose
- resource classes are hard to test because of mixed concerns
- versioning and deprecation are undocumented

## Architectural Tradeoffs

- **Custom Apex REST vs standard APIs:** custom endpoints offer control but add maintenance and security surface.
- **Typed DTOs vs dynamic JSON:** typed requests are clearer and safer, but dynamic payloads can be flexible when contracts vary.
- **Inline logic vs service delegation:** inline code is faster to start and slower to operate later.

## Anti-Patterns

1. **Business logic embedded in the resource class** — transport and domain concerns become inseparable.
2. **No versioned contract** — external consumers become fragile.
3. **Status-code ambiguity** — clients cannot recover intelligently.
4. **Returning sObjects or collections directly** — the platform owns serialization, so nulls vanish, the `attributes` envelope leaks a version-pinned URL, and heap exhaustion mid-stream arrives as a `200` with a truncated body (apexdev L18474–18477).
5. **Treating the status code as free-form** — codes outside the documented `statusCode` table are rewritten to `500`, so `422` and `429` never reach the client as themselves (apexrefguide L228768–228770).
6. **Shipping the class without the Apex Class Access permission set** — a correct endpoint that returns `403` to every caller is indistinguishable, from the client's side, from a broken one (apexdev L12325–12329, L18686).

## Official Sources Used

- Apex Developer Guide v67.0 (Summer '26), *Exposing Apex Classes as REST Web Services* — `apexdev.txt` L18369–18700 (governor limits and the 6 MB / 12 MB request-or-response cap at L18387–18389; the OAuth 2.0 / Session ID authentication list at L18395–18398; allowed parameter and return types at L18425–18437; one-method-per-verb at L18446–18448; `requestBody` vs. method parameters at L18459–18461; the heap-exhaustion `200` at L18471–18477; the managed-package namespace path at L18466–18470; the platform response-status table at L18680–18696) — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf
- Apex Developer Guide v67.0, *RestResource Annotation* and *URL Guidelines* — `apexdev.txt` L6345–6370 (mapping relative to `/services/apexrest/`, case sensitivity, `global` class requirement, the 255-character path cap, the wildcard placement rule, and the exact-match / longest-wildcard / 404 resolution order); *ReadOnly Annotation* L6161–6178 (the 1,000,000-row relaxation and the DML/`System.schedule`/async block)
- Apex Developer Guide v67.0, *Exposing Data with Apex REST Web Service Methods* and *Versioned Behavior Changes* — `apexdev.txt` L18724–18739 and L44493–44506 (Apex REST methods run in user mode by default; at API 67.0+ classes without an explicit sharing declaration run `with sharing` and database operations default to user mode; `WITH SECURITY_ENFORCED` is no longer supported and `WITH USER_MODE` replaces it) — supports the *Security* pillar section above
- Apex Reference Guide v67.0 (Summer '26), *RestContext / RestRequest / RestResponse Classes* — `apexrefguide.txt` L228267–228870 (`RestContext.request` and `.response` as read-write properties, the public no-arg constructors that make `RestContext`-driven tests possible, `addHeader`/`addParameter` "intended for unit testing of Apex REST classes", the `requestURI` and `resourcePath` semantics, the `responseBody` void-vs-return rule, the complete valid `statusCode` table, and the "Invalid status code for HTTP response" conversion to `500`) — supports the *Reliability* pillar and the status-code anti-pattern
- Apex Developer Guide v67.0, *Class Security Usage* — `apexdev.txt` L12320–12360 (class security applies at Apex transaction entry points including Apex REST services, and is checked only at the entry point, not on classes it calls) — supports the permission-set boundary in the *Security* pillar
- Salesforce Developer Limits and Allocations Quick Reference (App Limits Cheat Sheet) — L481–500 (25 concurrent requests running 20 seconds or longer in production and sandboxes, 5 in Developer Edition and trial orgs, `REQUEST_LIMIT_EXCEEDED` on exceeding it), L500–507 (the 10-minute API timeout), L693–700 (16,384 bytes for the combined URI and headers, `431` and `414`) — supports the *Operational Excellence* framing and the size-ceiling gotcha
- Metadata API Developer Guide, *ApexClass* — `api_meta.txt` L22212–22280 (the `.cls` / `ClassName.cls-meta.xml` file pair, and `apiVersion` / `status` as its fields) — supports the deployment artifacts in `references/code-examples.md` — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf
- REST API Developer Guide v67.0 — `api_rest.txt` L502–560 (the `Authorization: Bearer` header and OAuth 2.0 as the authorization mechanism for calls under `/services/`), which is the flow an Apex REST caller uses; the guide itself documents no `/services/apexrest/` resources, because those are defined by your classes rather than by the platform — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_rest.pdf
- Salesforce Well-Architected — security, reliability, and operational framing for the pillar tagging above
