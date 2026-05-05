# Gotchas — Inbound Email Service

Non-obvious behaviors of Salesforce Email Services that bite real
inbound-email integrations.

---

## Gotcha 1: `Messaging.InboundEmailHandler` requires `global` access

**What happens.** `public class MyHandler implements ...` compiles
but the platform can't invoke it.

**How to avoid.** `global` for both class and `handleInboundEmail`
method.

---

## Gotcha 2: `email.headers` is a List, not a Map

**What happens.** Apex code calls `email.headers.get('In-Reply-To')`
expecting Map semantics; doesn't compile.

**How to avoid.** Iterate the list:

```apex
for (Messaging.InboundEmail.Header h : email.headers) {
    if (h.name.toLowerCase() == 'in-reply-to') {
        return h.value;
    }
}
```

Header names are case-sensitive in the platform's representation;
normalize on read.

---

## Gotcha 3: `success = false` bounce-back exposes the message string

**What happens.** Stack trace in `result.message` reaches the
sender — information disclosure.

**How to avoid.** Generic friendly message to the sender; log the
full exception detail for admins.

---

## Gotcha 4: Max email size is platform-bounded

**What happens.** Emails above the configured Max Email Size are
bounced before the handler sees them. Sender gets a generic SMTP
bounce; the org's logs don't capture the attempt.

**How to avoid.** Configure Max Email Size deliberately (default is
~10 MB; ceiling is ~25 MB). For larger payloads, use a different
intake (file upload to S3, a REST API endpoint).

---

## Gotcha 5: Email Services Address subdomain is Salesforce-supplied

**What happens.** Customer wants `support@acme.com` to route to
the handler. Salesforce's Email Services Address looks like
`support@a1b2c3.k1234.apex.salesforce.com`.

**How to avoid.** Customer-side mail-server forwards
`support@acme.com` to the Salesforce-supplied address. SPF /
DKIM headers preserved correctly when the forwarding mail server
is configured to do so.

---

## Gotcha 6: Handler runs in the configured running user's context

**What happens.** Running user is "Marketing Admin"; the handler
tries to update a Case the running user can't see / edit; DML
fails with insufficient permissions.

**How to avoid.** Plan the running user's permissions to match
the handler's needs. Document the user's permission set
explicitly.

---

## Gotcha 7: `In-Reply-To` and `Message-Id` are unreliable across email clients

**What happens.** Some clients strip `In-Reply-To`; some mangle
it; some include the wrong value. Threading purely on header
content produces broken threads.

**How to avoid.** Subject-token threading (`[Acme:Case-12345]`)
is more robust because the token is in the rendered subject the
sender sees; clients are less likely to strip / modify the
visible subject.

---

## Gotcha 8: Attachment storage growth is unbounded by default

**What happens.** Spam / accidental large attachments accumulate;
File Storage allocation fills; legitimate uploads start failing.

**How to avoid.** Per-attachment size cap, per-email count cap,
allow-listed MIME types, documented retention / archive policy.

---

## Gotcha 9: Synchronous callouts from the handler block email processing

**What happens.** Handler does an HTTP callout; callout latency
× volume backs up the inbound queue.

**How to avoid.** Publish a Platform Event; Apex subscriber does
the callout asynchronously. Handler returns `success = true`
quickly.
