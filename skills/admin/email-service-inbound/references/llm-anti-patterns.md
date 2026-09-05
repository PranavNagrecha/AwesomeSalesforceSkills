# LLM Anti-Patterns — Inbound Email Service

Mistakes AI assistants make when advising on inbound email
handlers.

---

## Anti-Pattern 1: asserting `global` is mandatory on the handler

**What the LLM generates.** "`Messaging.InboundEmailHandler`
implementations must be declared `global`" — usually reasoning by
analogy with `Database.Batchable` folklore or `SandboxPostCopy`.

**Why it happens.** The Apex Reference Guide's
`AttachEmailMessageToCaseExample` sample is `global`, and that sample is
the one most often quoted.

**Correct pattern.** `public with sharing` is sufficient and is what the
Apex Developer Guide's own samples use (`CreateTaskEmailExample`,
`unsubscribe`). `global` is needed only when the class must be visible
outside its namespace — a managed package. Stating the rule as
"always global" produces packaging-shaped code in an org that has no
package, and hides the one case that actually matters.

**Detection hint.** Any explanation of the access modifier that does not
mention namespace visibility or packaging is repeating folklore. See
`references/gotchas.md` § 1.

---

## Anti-Pattern 2: Treating `email.headers` as a Map

**What the LLM generates.** `email.headers.get('In-Reply-To')`.

**Why it happens.** Java / Python `Map<String, String>` mental
model.

**Correct pattern.** `email.headers` is
`InboundEmail.Header[]`, whose elements expose only `name` and `value`.
More importantly, the three headers people actually want are already
parsed onto the object: `email.messageId`, `email.inReplyTo` and
`email.references`. Reaching for `headers` at all is usually the tell that
the model does not know those properties exist.

**Detection hint.** Any `.get('header-name')` call on `email.headers`
is wrong-shape; any header loop hunting for `In-Reply-To` or `Message-ID`
is redundant work.

---

## Anti-Pattern 3: Stack trace exposed in `success = false` message

**What the LLM generates.**

```apex
res.message = ex.getMessage() + ' ' + ex.getStackTraceString();
```

**Why it happens.** "Tell the sender what went wrong" is a
helpful instinct.

**Correct pattern.** Generic friendly message to the sender; full
exception logged to an admin-visible store.

**Detection hint.** Any `result.message =` containing `getStackTraceString()`
is information disclosure.

---

## Anti-Pattern 4: Recommending custom service for case creation

**What the LLM generates.** Long Apex handler that creates a Case
from an email.

**Why it happens.** "Implement the handler" is the visible task;
Email-to-Case isn't surfaced.

**Correct pattern.** Email-to-Case is built. Use it for case
creation. Custom service for everything else.

**Detection hint.** Any "create a Case from an email" Apex recipe
that doesn't first ask "have you considered Email-to-Case?" is
re-inventing built-in functionality.

---

## Anti-Pattern 5: Synchronous callout in the handler

**What the LLM generates.** Handler that issues an HTTP callout
inline.

**Why it happens.** "Trigger downstream API" is a common
requirement; synchronous is the simple shape.

**Correct pattern.** Publish a Platform Event from the handler;
Apex subscriber does the callout async. Handler returns quickly;
inbound queue stays clear.

**Detection hint.** Any `Http.send()` / `HttpRequest` in an
inbound-email handler is going to back up under load.

---

## Anti-Pattern 6: Threading purely on `In-Reply-To`

**What the LLM generates.** Handler that parses `In-Reply-To` and
matches against a stored Message-Id.

**Why it happens.** RFC-compliant; sounds robust.

**Correct pattern.** Check `inReplyTo` *and* `references` — the reference
guide describes `references` as carrying "a list of the parent emails'
References and message IDs, and possibly the In-Reply-To fields", so it
frequently survives when `inReplyTo` alone does not — then fall back to a
visible subject token (`[Acme:Case-12345]`).

**Detection hint.** A threading recipe that reads `inReplyTo` but never
`references`, or that has no fallback path at all, breaks for
forward-as-new and for clients that recompose rather than reply.

---

## Anti-Pattern 7: No allow-list / spam handling on public addresses

**What the LLM generates.** Public-facing handler with no
sender-domain checks.

**Why it happens.** "Process the email" is the surface task;
spam isn't part of the requirement.

**Correct pattern.** Custom Metadata-driven allow-list of sender
domains; reject (with a friendly message) anything else.

**Detection hint.** Any public-facing-address recipe without
spam handling is going to drown in junk.

---

## Anti-Pattern 8: No attachment policy

**What the LLM generates.**

```apex
for (Messaging.InboundEmail.BinaryAttachment att : email.binaryAttachments) {
    // save without checks
}
```

**Why it happens.** Saving is the visible action; the policy
side is implicit.

**Correct pattern.** Per-attachment size cap, per-email count
cap, allow-listed MIME types, documented retention.

**Detection hint.** Any attachment-handling recipe without
explicit caps is going to fill File Storage.

---

## Anti-Pattern 9: inventing a `maxEmailSize` setting on the email service

**What the LLM generates.** "Set Max Email Size on the Email Service to
25 MB" — or XML containing a `<maxEmailSize>` element.

**Why it happens.** Every other quota on the platform is configurable, and
the ~25 MB figure reads like a default rather than a ceiling.

**Correct pattern.** The `EmailServicesFunction` metadata type has no such
field. The ~25 MB limit on combined body plus attachments is enforced by
the platform before the handler runs, varies with character set and
transfer encoding, and is not tunable. Advice about "raising the limit"
is advice to change intake mechanism.

**Detection hint.** Any `<maxEmailSize>` in generated XML, or any sentence
of the form "the default is N MB and the maximum is 25 MB", is fabricated.
See `references/gotchas.md` § 4.

---

## Anti-Pattern 10: budgeting the handler's heap at 6 MB

**What the LLM generates.** "Attachments must stay under the 6 MB
synchronous heap limit, so process them asynchronously."

**Why it happens.** The synchronous heap figure is the most-repeated
number in Apex guidance, and the email-service exception is a footnote.

**Correct pattern.** Email services get a 50 MB heap. The attachment work
belongs *inside* `handleInboundEmail`, where the raised ceiling applies.
Deferring the Blob to a Queueable moves it into a context with the ordinary
limit — the opposite of the intended fix. Hand off a `ContentVersion` Id if
you need async work, never the `Blob`.

**Detection hint.** Any recommendation to move attachment parsing out of
the handler *for heap reasons* has the limit backwards. See
`references/gotchas.md` § 11.

---

## Anti-Pattern 11: hardcoding the routing address

**What the LLM generates.** A test class, runbook or Apex constant
containing a literal address like
`quotes@a1b2c3.k1234.apex.salesforce.com`, presented as the address to use.

**Why it happens.** The address looks like configuration the author
controls, because `localPart` is.

**Correct pattern.** Only the local-part is settable; the domain part is
system-generated and unique per address per org, and sandbox addresses
cannot be copied to production. Read it back from
`EmailServicesAddress.EmailDomainName` and store it in Custom Metadata.

**Detection hint.** Any literal `*.apex.salesforce.com` address outside a
clearly-labelled illustrative example will be wrong in every org but the
one it was copied from. See `references/gotchas.md` § 5 and § 12.
