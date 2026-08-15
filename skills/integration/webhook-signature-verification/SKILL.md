---
name: webhook-signature-verification
description: "Accept inbound webhooks (Stripe, GitHub, Slack, partner) and verify HMAC signatures in Apex REST — Crypto.verifyHMac platform verification, secret in Protected Custom Metadata, replay-window rejection. NOT for designing the receiver end to end — Sites routing, guest-user access, idempotency, the 5-second response window — use integration/webhook-inbound-patterns. NOT for signing a webhook Salesforce sends out — use integration/outbound-webhook-from-salesforce."
category: integration
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
triggers:
  - "webhook hmac verification apex"
  - "stripe webhook salesforce"
  - "verify signature inbound callout"
  - "hmac sha256 apex"
tags:
  - webhook
  - hmac
  - signature
  - apex-rest
inputs:
  - "webhook provider HMAC spec"
  - "shared secret location"
outputs:
  - "@RestResource endpoint with signature verification"
dependencies: []
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-08-14
---


# Webhook Signature Verification

An inbound webhook is an HTTP POST from a third party that Salesforce did not
initiate and cannot authenticate by session. When the endpoint is exposed through
a public Salesforce Site, the signature check is the *entire* authentication
boundary — there is no user, no token, and no network control in front of it.

Three properties have to hold, and each fails independently:

| Property | Established by | Fails when |
|---|---|---|
| **Authenticity** — the sender holds the shared secret | HMAC over the payload | Secret is wrong, or the wrong encoding of the right secret |
| **Integrity** — the bytes were not altered in transit | HMAC over the **raw** body | The body was parsed and re-serialised before hashing |
| **Freshness** — this is not a replay of an earlier valid request | Timestamp tolerance + idempotency key | Neither is implemented — the signature alone never establishes this |

Most broken webhook endpoints have the first two and not the third.

**Scope.** This skill owns the *verification* step: which Apex crypto method to
call, over which bytes, against which secret, and what to reject. Designing the
receiver end to end — Sites routing, guest-user access model, the idempotency
schema, the response-window budget — belongs to
`integration/webhook-inbound-patterns`. Those subjects appear below only as far as
they change the verification decision (for example: on a public Site the signature
is the only gate, which raises the stakes on every gotcha here). Signing a webhook
Salesforce *sends* is `integration/outbound-webhook-from-salesforce`.

---

## Before Starting

1. **Identify the signature scheme.** HMAC (shared secret) or asymmetric
   (RSA/ECDSA against a published public key)? They need different Apex methods
   and different secret storage. Do not assume HMAC.

2. **Get the exact header name, value format, and signed payload.** Not every
   provider signs the body alone — Stripe signs `"{timestamp}.{body}"`. Getting
   this wrong produces 100% verification failure that looks like a key problem.

3. **Decide how the request reaches Apex.** `/services/apexrest/*` requires an
   authenticated session, which a webhook does not have. Either the provider
   obtains a token (Connected App, client credentials flow) or you expose the class
   through a Salesforce Site guest user. Pick before you write the class.

4. **Choose where the secret lives.** Protected Custom Metadata, read via
   `getAll()`. Not a literal, not a Custom Setting, not a Named Credential (which
   is for outbound).

---

## Core Concepts

### `Crypto.verifyHMac` is the method you want

```apex
public static Boolean Crypto.verifyHMac(
    String algorithmName,   // hmacMD5 | hmacSHA1 | hmacSHA256 | hmacSHA512
    Blob   data,
    Blob   privateKey,      // max 4 KB
    Blob   macToVerify
)
```

`Crypto.generateMac` produces a MAC and is correct for *building* a signature (in
tests, or when calling out). It is the wrong tool for checking one, because it
forces you to write the comparison yourself — and `String.equals` short-circuits
on the first differing character. Both Stripe and GitHub explicitly tell
integrators to compare signatures in constant time.

**What the Apex Reference Guide does and does not say.** Its `verifyHMac` entry
documents the signature, the four valid algorithm names, the 4 KB key cap, the
Base64 symmetry rule, and the Boolean return. It makes **no timing claim**. So
`verifyHMac` is the recommended method here because it keeps the comparison out
of your code entirely, not because Salesforce documents it as constant-time —
that property is undocumented, and this skill does not assert it. Detail in
[`references/gotchas.md`](references/gotchas.md), Gotcha 4.

For asymmetric providers:

```apex
public static Boolean Crypto.verify(String algorithmName, Blob data,
                                    Blob signature, String certDevName)
```

with the provider's public certificate stored in **Setup → Certificate and Key
Management**, so rotation is a Setup change rather than a deploy.

### The Base64 symmetry rule

> "You may supply a private key that has been encoded using Base64 encoding.
> However if you do, then you must also supply the Base64-encoded private key when
> verifying the MAC using the `verifyHMac` method."
> — Apex Reference Guide, `Crypto.generateMac`

Record in a comment which form the provider uses. Stripe's `whsec_...` is an
opaque ASCII string used raw; some providers issue a Base64 blob that must be
decoded first.

### Raw body only

`RestRequest.requestBody` is a `Blob` — the exact bytes the sender hashed.
`JSON.serialize(JSON.deserializeUntyped(...))` reorders keys, strips whitespace,
and normalises numbers, so a MAC computed over the round trip never matches. Verify
first; parse second.

### Headers are case-insensitive; Apex maps are not

`RestRequest.headers` is a `Map<String, String>` with exact-match lookup. Proxies
and provider clients normalise header casing differently, so
`headers.get('Stripe-Signature')` can return `null` in production while working in
a test that used the same spelling. Always look up case-insensitively.

### Size ceiling

"The maximum request or response size is 6 MB for synchronous Apex or 12 MB for
asynchronous Apex." A provider posting near that ceiling has outgrown the webhook
shape; move to notification-plus-pull.

---

## Common Patterns

### Pattern A — verify, stage, return 200, process async

The default. The resource verifies, upserts the raw event against an External Id,
enqueues a Queueable, and returns. Providers time out in single-digit seconds and
retry on timeout; anything slower turns one event into repeated deliveries. Full
implementation in [`references/examples.md`](references/examples.md), Example 2.

### Pattern B — replay window before HMAC

If the provider signs a timestamp, check it first. A replay flood then costs a
`Long` comparison rather than a crypto operation. Stripe's libraries "have a
default tolerance of 5 minutes between the timestamp and the current time," and
Stripe warns against a tolerance of `0` because it disables the recency check
entirely.

### Pattern C — accept multiple signatures during rotation

Stripe emits one signature per active secret while a secret roll is in flight
(previous secret active for up to 24 hours), so a verifier that loops over every
`v1=` value rides the rotation with no downtime. Where the provider does not do
this, hold `Secret__c` and `Previous_Secret__c` on the metadata record and try
both, removing the old value in a separate, dated change.

### Pattern D — layer IP allowlisting where the provider publishes ranges

Stripe publishes its webhook source IPs and recommends allowlisting them in
addition to signature verification. This is defence in depth, not a replacement:
IP ranges change, and an allowlist alone proves nothing about payload integrity.

---

## Decision Guidance

| Situation | Approach |
|---|---|
| Provider issues a shared secret | `Crypto.verifyHMac('hmacSHA256', rawBody, secret, mac)` |
| Provider publishes a public certificate / JWKS | `Crypto.verify(alg, data, sig, certDevName)` with the cert in Certificate and Key Management |
| Provider can send a bearer token | Connected App + OAuth 2.0 client credentials flow, **and** keep the signature check |
| Provider cannot authenticate at all | Public Site + guest-user Apex class access; the HMAC check is the only gate |
| Provider signs a derived payload | Reconstruct the derivation from the raw body string, never from a re-serialised object |
| Payload approaches 6 MB | Notification-plus-pull: the event carries an id, Salesforce fetches the body |
| Provider offers several signature schemes | Pin one in code; never let the sender choose the algorithm |

---

## Recommended Workflow

1. **Read the provider's signature documentation and write down four things**:
   header name, value grammar, exactly which bytes are signed, and the algorithm.
   Note whether the secret is used raw or Base64-decoded.
2. **Store the secret as protected Custom Metadata** and expose it through a small
   accessor using `getAll()` so it costs no SOQL query. Never a literal, never a
   Custom Setting.
3. **Write the resource in the fixed order**: read raw body → read signature
   header case-insensitively → reject if absent or malformed → reject if the
   timestamp is outside tolerance → `Crypto.verifyHMac` → *only then* deserialise.
4. **Make it idempotent.** Upsert against the provider's event id on an External
   Id, Unique field, and act only when `Database.UpsertResult` indicates a new row.
5. **Return 2xx immediately** and move all processing to a Queueable or a platform
   event subscriber. No callouts, no email, no Flow inside the handler.
6. **Expose the endpoint deliberately** — Connected App with client credentials, or
   Site guest user with the narrowest possible object access — and record which
   shape you chose and why.
7. **Test the negatives**: tampered body with a captured signature, stale
   timestamp with a valid signature, missing header, and a header supplied in
   different casing from the handler's spelling.

---

## Review Checklist

- [ ] `Crypto.verifyHMac` used, not `generateMac` plus an equality comparison
- [ ] The `Blob` hashed is `req.requestBody`, untouched — no `JSON.serialize` between
- [ ] Signature header read case-insensitively
- [ ] Signature scheme matched exactly (`v1`), not by prefix
- [ ] Timestamp tolerance enforced, and checked before the HMAC
- [ ] Idempotency via External Id, Unique upsert on the provider's event id
- [ ] Secret in protected Custom Metadata; comment records raw vs Base64 form
- [ ] Rejection responses are terse and identical for every failure reason
- [ ] Raw body, signature header, and secret never logged
- [ ] Handler returns 2xx before any processing; work is enqueued
- [ ] Rotation path accepts both current and previous secret
- [ ] Endpoint exposure (Connected App or Site guest user) documented, with guest
      user object access minimised
- [ ] Negative tests: tampered body, stale timestamp, missing header, odd casing

---

## Salesforce-Specific Gotchas

Full detail in [`references/gotchas.md`](references/gotchas.md).

1. **The Base64 rule on `privateKey` is bidirectional** — encode on both sides or
   neither. Key cap is 4 KB.
2. **Apex map keys are case-sensitive; HTTP header names are not.** Intermittent
   401s in production, green tests locally.
3. **Re-serialising the body guarantees 100% verification failure** — which
   usually gets "fixed" by deleting the check.
4. **`generateMac` + `equals` is a hand-rolled comparison**; `verifyHMac` is not.
5. **A valid signature is not a fresh request.** Replay window plus idempotency.
6. **Slow handlers cause retries, not patience.** Verify, stage, 200, enqueue.
7. **Apex REST needs a session** — webhooks have none. Connected App or Site.
8. **Not every provider uses HMAC.** Asymmetric schemes need `Crypto.verify`.
9. **Logging the payload logs the data**, and logging the signature makes a
   captured request replayable from your log store.
10. **Accepting any `vN` scheme is a downgrade attack.** Pin `v1`.
11. **Rotation without dual acceptance is a silent outage** of 401s.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Provider signature contract note | Header name, value grammar, signed-bytes definition, algorithm, secret encoding form, and the provider doc URL it came from |
| Apex REST resource | Verify → stage → 2xx → enqueue, with a case-insensitive header lookup and terse rejections |
| Secret metadata | Protected `Webhook_Secret__mdt` record plus the accessor class, with a rotation note naming when the previous value may be removed |
| Staging object | External Id, Unique on the provider event id, restricted to the integration's permission set, with a retention policy |
| Negative test class | Tampered body, stale timestamp, missing header, alternate header casing |
| Exposure decision record | Connected App vs Site guest user, with the guest user's granted object access enumerated |

---

## Related Skills

- `integration/webhook-inbound-patterns` — the receiver design this skill sits
  inside: Sites routing, guest-user access model, idempotency schema, and the
  response-window budget. Read it first if you are building the endpoint rather
  than fixing the signature check.
- `integration/outbound-webhook-from-salesforce` — signing a webhook Salesforce
  sends, which is the mirror image of this problem
- `apex/apex-rest-services` — the `@RestResource` surface itself: URL mapping
  rules, supported HTTP methods, and response handling
- `security/guest-user-security` — hardening the Site guest user that a public
  webhook endpoint necessarily exposes
- `integration/retry-and-backoff-patterns` — the provider side of at-least-once
  delivery, and what your 2xx does and does not promise
