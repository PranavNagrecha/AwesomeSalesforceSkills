# LLM Anti-Patterns — Inbound Email Service

Mistakes AI assistants make when advising on inbound email
handlers.

---

## Anti-Pattern 1: `public class` instead of `global class`

**What the LLM generates.** `public class MyHandler implements
Messaging.InboundEmailHandler`.

**Correct pattern.** `global` for both class and method —
required by the interface contract.

**Detection hint.** Same as SandboxPostCopy; any non-global
implementation of a system interface is wrong.

---

## Anti-Pattern 2: Treating `email.headers` as a Map

**What the LLM generates.** `email.headers.get('In-Reply-To')`.

**Why it happens.** Java / Python `Map<String, String>` mental
model.

**Correct pattern.** `email.headers` is a `List<Header>`. Iterate.

**Detection hint.** Any `.get('header-name')` call on `email.headers`
is wrong-shape.

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

**Correct pattern.** Subject-token threading (`[Acme:Case-12345]`).
Email clients are reliable about preserving the subject; less
reliable about preserving headers.

**Detection hint.** Any threading recipe relying solely on
header-parsing is going to break for some clients.

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
