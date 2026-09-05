# Gotchas — Inbound Email Service

Non-obvious behaviors of Salesforce Email Services that bite real
inbound-email integrations. Grounded in the Metadata API Developer Guide
(`EmailServicesFunction`), the Apex Developer Guide (Email Services /
Using the InboundEmail Object / Email Limits) and the Apex Reference Guide
(`InboundEmail`, `InboundEmailResult`, `InboundEnvelope`).

---

## Gotcha 1: `global` is not required — but it is required for packaging

**What happens.** Guidance that says "the handler must be `global`" is
wrong as a blanket rule, and guidance that says "`public` always works" is
wrong for packages. Both official samples exist: the Apex Developer Guide's
`CreateTaskEmailExample` and `unsubscribe` samples are declared
`public with sharing class ... implements Messaging.InboundEmailHandler`,
while the Apex Reference Guide's `AttachEmailMessageToCaseExample` is
declared `global class`.

**When it occurs.** `public` is enough for a class deployed into the org
that owns it. The access modifier must be `global` when the class has to be
visible outside its namespace — a managed package, or an `apexClass`
reference resolved across namespaces.

**How to avoid.** Default to `public with sharing`, matching the guide's
own sample. Escalate to `global` only when the handler ships in a managed
package, and record that reason in the class header so the next reader does
not "simplify" it back.

---

## Gotcha 2: `headers` is a List, but you rarely need it

**What happens.** Code calls `email.headers.get('In-Reply-To')` expecting
`Map` semantics and does not compile: `headers` is
`InboundEmail.Header[]`, and `Header` exposes only `name` and `value`.

**When it occurs.** Any port of a Java/Python mail-parsing idiom.

**How to avoid.** For the three headers that matter, do not iterate at all
— the platform already parsed them into first-class properties:
`email.messageId` (Message-ID), `email.inReplyTo` (String) and
`email.references` (`String[]`). Iterate `headers` only for a header
Salesforce does not surface, and lowercase `h.name` before comparing:

```apex
private static String header(Messaging.InboundEmail email, String wanted) {
    if (email.headers == null) return null;
    for (Messaging.InboundEmail.Header h : email.headers) {
        if (h.name != null && h.name.equalsIgnoreCase(wanted)) return h.value;
    }
    return null;
}
```

---

## Gotcha 3: `success = false` returns your `message` to the sender

**What happens.** `InboundEmailResult.message` is documented as "A message
that Salesforce returns in the body of a reply email"; when `success` is
`false`, Salesforce "rejects the inbound email and sends a reply email to
the original sender containing the message specified in the Message field."
A stack trace assigned there is mailed to whoever sent the message —
potentially an anonymous outsider.

**When it occurs.** Every failure path in a handler that stringifies the
exception into `result.message`.

**How to avoid.** Generic, actionable text for the sender; the exception
detail goes to a debug log or a logging object. Note the same reference
also says `message` "can be populated with text irrespective of the value
returned by the Success field" — so a `success = true` result can still
reply, which is how acknowledgement replies are built.

---

## Gotcha 4: the ~25 MB email ceiling is a platform limit, not a service setting

**What happens.** "Email services reject email messages and notify the
sender if the email (combined body text, body HTML, and attachments)
exceeds approximately 25 MB (varies depending on language and character
set)" (Apex Developer Guide, Email Services). The rejection happens before
your Apex runs, so the org has no handler-side record of the attempt.

**When it occurs.** Users forwarding scanned documents or photo sets. The
guide is explicit that the size counts headers and encoding too: "an email
with a 35-MB attachment likely exceeds the 25-MB size limit for an email
message after accounting for the headers, body, and encoding."

**How to avoid.** There is no `maxEmailSize` element in the
`EmailServicesFunction` metadata type — do not go looking for one and do
not promise a tunable cap. For payloads near the ceiling, move intake to a
file-upload or REST endpoint and tell senders the limit up front. Base64
transfer encoding inflates a binary by roughly a third, so an ~18 MB file
is already close.

---

## Gotcha 5: the address domain is generated per org and per address

**What happens.** A customer wants `support@acme.example` to reach the
handler. The address Salesforce creates has a system-generated domain part;
`EmailServicesAddress.EmailDomainName` is documented as "A read only field
you can query that contains the system-generated domain part of this email
service address. The system generates a unique domain-part for each email
service address to ensure that no two email service addresses are
identical."

**When it occurs.** Every new address, in every org, including each
sandbox refresh.

**How to avoid.** Set only `localPart` in metadata; read the full address
back with SOQL after deploy (see `metadata-examples.md` § Verification).
Route the customer-facing address by forwarding from the customer's own
mail server. Never hardcode a routing address in Apex, a template, or a
runbook — it differs per org.

---

## Gotcha 6: the handler runs as `runAsUser`, set per address, not per service

**What happens.** `runAsUser` is a **required** field on
`EmailServicesAddress`, not on `EmailServicesFunction`: "the username of
the user whose permissions the email service assumes when processing
messages sent to this address." Two addresses on the same service can
therefore run the same Apex as two different users, with different FLS,
sharing and record visibility.

**When it occurs.** The moment a second address is added — typically a
partner or regional intake — and it inherits a different (often more
restricted) service user.

**How to avoid.** Treat the running user as part of the address
configuration. Document one permission set per intake user, and diff the
two users when one address processes mail correctly and the other silently
fails DML.

---

## Gotcha 7: `In-Reply-To` and `References` are set by the sender's client

**What happens.** `inReplyTo` and `references` are copied from the RFC 2822
headers the sending client supplied. Some clients omit them on
"forward-as-new", some rewrite them, and a user pasting a reply into a
fresh compose window produces neither.

**When it occurs.** Any threading design that assumes the reply chain is
intact.

**How to avoid.** Check `inReplyTo` **and** `references` (the reference
guide describes `references` as containing "a list of the parent emails'
References and message IDs, and possibly the In-Reply-To fields", so it
often survives when `inReplyTo` does not), and fall back to a visible
subject token. Store your own outbound `Message-Id` on the record so the
lookup has something to match.

---

## Gotcha 8: attachment storage growth is unbounded by default

**What happens.** Spam and accidental large attachments accumulate as
files; the org's File Storage allocation fills; unrelated uploads start
failing.

**When it occurs.** Public-facing addresses, and any service left on
`attachmentOption` = `All` without a size or count cap in the handler.

**How to avoid.** Use `attachmentOption` to do the coarse filtering at the
platform level before Apex ever sees the bytes — `None` (message accepted,
attachments discarded), `NoContent` (filename and MIME type given to Apex
with the body set to `null`), `TextOnly`, `BinaryOnly` or `All`. Then cap
size, count and MIME type in the handler, and write down a retention rule.

---

## Gotcha 9: synchronous callouts from the handler block email processing

**What happens.** Handler issues an HTTP callout; callout latency times
volume backs up inbound processing, and once the org crosses the daily
message limit the remaining mail is handled by `overLimitAction` rather
than by your code.

**When it occurs.** "Notify the downstream system on each email"
requirements at any real volume.

**How to avoid.** Publish a Platform Event from the handler and do the
callout in a subscriber (`apex/apex-event-bus-subscriber`). The handler
returns quickly and the retry semantics move to the event bus.

---

## Gotcha 10: the daily limit is org-wide and shared with On-Demand Email-to-Case

**What happens.** The limit is not per service and not per address:
"Salesforce limits the total number of messages that all email services
combined, including On-Demand Email-to-Case, can process daily…
Salesforce calculates the limit by multiplying the number of user licenses
by 1,000; maximum 1,000,000. For example, if you have 10 licenses, your org
can process up to 10,000 email messages a day" (Apex Developer Guide, Email
Limits / Inbound Email Limits). Overflow is "bounced, discarded, or queued
for processing the next day, depending on how you configure the failure
response settings for each email service."

**When it occurs.** Small-licence orgs with a chatty inbound integration; a
new email service quietly consuming the budget an existing Email-to-Case
flow depends on.

**How to avoid.** Size the licence count against total inbound volume
before adding a service, and set `overLimitAction` deliberately.
`Requeue` holds the message for processing within 24 hours and only bounces
it if still unprocessed; `Discard` loses it silently. Default `Requeue` for
anything business-critical.

---

## Gotcha 11: email-service Apex gets a 50 MB heap, not 6 MB

**What happens.** "Email services heap size is 50 MB" (Salesforce Developer
Limits and Allocations Quick Reference, Apex Governor Limits, footnote 4;
same footnote in the Apex Developer Guide governor-limit table). Handlers
therefore survive attachment payloads that would blow a synchronous
transaction, which is exactly why people write attachment-heavy logic
inside them.

**When it occurs.** Two ways round. Teams refuse to process a 20 MB
attachment because "the heap is 6 MB" — needlessly. Or they move the
attachment logic into a Queueable and it fails there, because the raised
ceiling belongs to the email-service context and does not travel with the
Blob.

**How to avoid.** Do the Blob work inside `handleInboundEmail`. If you must
hand off, pass the `ContentVersion` Id, never the `Blob`. Every other
governor limit is unchanged — SOQL, DML rows and CPU time are the normal
synchronous budget, so bulk the attachment inserts into one DML statement.

---

## Gotcha 12: sandbox routing addresses cannot be promoted to production

**What happens.** "Email service addresses that you create in your sandbox
can't be copied to your production org" (Apex Developer Guide, Email
Services). The service definition deploys; the working address you tested
against does not follow it.

**When it occurs.** Every promotion, and again after every sandbox refresh
— the refreshed sandbox generates fresh domain parts, so anything pinned to
the old address stops receiving.

**How to avoid.** Deploy the `EmailServicesFunction` (which carries
`localPart`), then re-read `EmailDomainName` in each org and re-point
forwarding rules there. Keep the routing address in Custom Metadata or a
Custom Setting rather than in Apex, so a refresh is a data edit rather than
a deployment.

---

## Gotcha 13: `authorizationFailureAction` lives on the service, `authorizedSenders` on both

**What happens.** An address-level `authorizedSenders` list rejects a
sender, but the action taken is the one configured on the **parent
service**: an unlisted sender "performs the action specified in the
`authorizationFailureAction` field of its associated email service"
(Metadata API guide, `EmailServicesAddress` § `authorizedSenders`). Set a
tight allow-list on a partner address while the service is on
`UseSystemDefault` and you cannot predict, per address, what a rejected
sender experiences.

**When it occurs.** Multi-address services where each address has a
different sender population.

**How to avoid.** Decide the failure behaviour once, at service level, and
choose addresses to match it. If two addresses genuinely need different
rejection behaviour — bounce partners, discard the public address — they
need two separate `EmailServicesFunction` records pointing at the same
`apexClass`.

---

## Gotcha 14: bodies and text attachments arrive truncated, with a flag you must read

**What happens.** `InboundEmail` exposes `plainTextBodyIsTruncated` and
`htmlBodyIsTruncated`, and `InboundEmail.TextAttachment` exposes
`bodyIsTruncated`. A parser that reads to the end of `plainTextBody` and
finds no terminator treats a truncated message as a malformed one and
rejects a legitimate email.

**When it occurs.** Long threads with quoted history, and machine-generated
mail with large text payloads.

**How to avoid.** Read the flag before parsing and branch on it: process
what arrived, mark the record as partial, and alert rather than bounce. On
`TextAttachment`, also read `charset` — the reference notes the original
character set is recorded there while "the body is re-encoded as UTF-8 as
input to the Apex method", so the original encoding is only recoverable
from that property.

---

## Gotcha 15: `isTextAttachmentsAsBinary` silently changes which Apex type you get

**What happens.** With `isTextAttachmentsAsBinary` = `true`, "text
attachments are supplied to the Apex code as a
`Messaging.BinaryAttachment` instead of as a
`Messaging.TextAttachment`… the body is supplied as an Apex Blob instead
of as an Apex String." The handler still compiles — it simply finds
`email.textAttachments` empty and the CSV it expected sitting in
`binaryAttachments` as a Blob.

**When it occurs.** An admin flips the setting in Setup to fix a character
encoding complaint, without touching the Apex.

**How to avoid.** Handle both lists in every handler that accepts text
payloads, and assert the setting in the test class comments. The related
trap: `attachmentOption` = `NoContent` delivers attachment metadata with
the body set to `null`, so `att.body.size()` throws a null pointer while
the filename reads perfectly.

---

## Gotcha 16: `EmailServicesFunction` has no wildcard, and no `addressInactiveAction`

**What happens.** Two separate omissions catch deployments. `package.xml`
rejects `<members>*</members>` for this type ("This metadata type doesn't
support the wildcard character * (asterisk) in the package.xml manifest
file", closing the `EmailServicesFunction` section) — a manifest built by
wildcarding every type silently ships no email services at all. And
`AddressInactiveAction`, which the SOAP object `EmailServicesFunction`
documents as a settable picklist, has no counterpart in the Metadata API
field table.

**When it occurs.** Org-comparison tooling that wildcards types; and any
attempt to encode "what happens when a single address is switched off" in
version control.

**How to avoid.** Name every service explicitly in `package.xml`. Treat
`addressInactiveAction` as org configuration that lives outside source
control — set it in Setup, and record the intended value in the skill's
work template so a rebuild does not lose it.

UNVERIFIED (2026-09-05): whether `addressInactiveAction` is genuinely
absent from the Metadata API or merely undocumented in the v62 field table
could not be settled from the PDFs — the SOAP object reference lists it and
the Metadata API `EmailServicesFunction` table does not. Retrieve one
existing service in your org and inspect the returned XML before relying on
either behaviour.
