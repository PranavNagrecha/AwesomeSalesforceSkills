---
name: email-service-inbound
description: "Inbound email processing in Salesforce via Email Services + the `Messaging.InboundEmailHandler` Apex interface. Covers EmailService configuration (running user, accept-from address, attachment handling, error / failure routing), the EmailServicesAddress per-routing-address pattern, the handler's `Messaging.InboundEmail` payload (text body, HTML body, headers, attachments, in-reply-to threading), and the canonical Email-to-Case alternative for case creation. NOT for outbound email (use admin/email-templates-and-alerts), NOT for Email-to-Case flow customization itself (use admin/email-to-case-configuration). Trigger keywords: EmailServicesFunction, EmailServicesAddress, runAsUser, localPart, EmailDomainName, attachmentOption, overLimitAction, errorRoutingAddress, routing address, inbound email limit."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Security
  - Operational Excellence
triggers:
  - "messaging inboundemailhandler apex class email service"
  - "salesforce email service routing address EmailServicesAddress"
  - "inbound email parse threading in-reply-to message-id"
  - "email service binary attachment max size limit"
  - "email service running user authorized senders"
  - "email-to-case vs custom email service decision"
  - "configure an email service to create records from inbound email"
  - "inbound email handler not firing after deploy"
  - "find the salesforce email service routing address for an org"
  - "deploy EmailServicesFunction metadata to production"
  - "sender gets a bounce reply from my apex email handler"
  - "email service address stopped working after sandbox refresh"
  - "attachments missing from inbound email in apex"
  - "email services daily limit exceeded messages bounced"
tags:
  - email-service
  - inboundemailhandler
  - emailservicesaddress
  - inbound-email
  - email-to-case
  - emailservicesfunction
  - routing-address
  - inbound-email-limits
inputs:
  - "What the inbound email needs to produce: Case, custom record, file upload, audit log, downstream API call"
  - "Sender population: known users, anonymous public, mixed"
  - "Volume: emails / day, peak / minute"
  - "Attachment handling: discard, attach to record, archive"
  - "Threading: standalone emails or part of a conversation"
outputs:
  - "Email Service + EmailServicesAddress configuration"
  - "Apex class implementing Messaging.InboundEmailHandler"
  - "Routing-address policy (accept-from, max retention, error response)"
  - "Decision: custom email service vs Email-to-Case"
  - "Deployable EmailServicesFunction XML with nested address records"
  - "package.xml entries and the post-deploy SOQL that reveals the routing address"
dependencies: []
version: 1.1.0
author: Pranav Nagrecha
updated: 2026-09-05
---

# Inbound Email Service

Salesforce can accept inbound email and run Apex against each
message. The mechanism: an **Email Service** (org-level
configuration) maps one or more **Email Service Addresses** (the
local-part + Salesforce-supplied domain) to a class implementing
`Messaging.InboundEmailHandler`. Apex receives the parsed email,
returns a `Messaging.InboundEmailResult`, and the platform
responds (delivery success, error reply, drop) accordingly.

The classic alternative is **Email-to-Case** — a built-in service
that creates a Case from each email, with extensive admin
configuration (auto-response, routing, threading, contact lookup).
Email-to-Case is the right answer for case creation; custom email
service is the right answer for everything else (file uploads,
custom-object creation, audit logging, complex routing).

What this skill is NOT. Outbound email — `admin/email-templates-and-alerts`.
Email-to-Case-specific configuration — `admin/email-to-case-configuration`.
This skill is the custom-handler path.

---

## Before Starting

- **Decide custom service vs Email-to-Case.** Case creation? E2C
  is built; don't reinvent. Anything else? Custom service.
- **Plan the running user.** The handler runs as the user
  configured on each Email Services Address (`runAsUser`). Their permissions determine
  what the handler can do. Use a dedicated integration user.
- **Plan the accept-from policy.** Anonymous public addresses
  receive spam; consider authorized-senders allow-listing or
  rate limiting.
- **Plan attachment handling.** Salesforce has limits (~25 MB combined email
  size, max attachment size, total org file storage). Decide
  store vs discard before traffic ramps.

---

## Questions to Ask Before Configuring

Each answer sets a specific, Required element on the
`EmailServicesFunction` record. Skipping one does not leave a blank — it
leaves a default whose failure mode nobody chose.

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "If we are switched off during a cutover, or the org hits its daily inbound limit — hold the mail, bounce it, or drop it?" | `functionInactiveAction` and `overLimitAction` are Required; `Discard` loses messages with no notice to anyone | Two explicit enum values instead of `UseSystemDefault`, and a documented data-loss position |
| "Who gets paged when a message fails to process — the sender, or us?" | Without `isErrorRoutingEnabled` + `errorRoutingAddress`, notifications go to the sender and intake breaks silently | A monitored internal address, and a rule that failure text sent outward stays generic |
| "Which username does each address run as, and what can that user see?" | `runAsUser` is Required *per address*, so two addresses on one service can run the same Apex with different visibility | One named integration user per address plus its permission set |
| "Which senders are legitimate, and must we verify the sending server?" | `authorizedSenders` filters before Apex; `isAuthenticationRequired` turns on SPF / SenderId / DomainKeys checks | An allow-list, and a decision on `authenticationFailureAction` for unverified mail |
| "What do we need from attachments — nothing, filenames only, text, binary, or everything?" | `attachmentOption` filters at the platform layer before the bytes reach the heap | The right enum, plus size / count / MIME caps for whatever survives it |
| "How many inbound messages a day, across every email service and On-Demand Email-to-Case?" | The daily limit is org-wide (user licences x 1,000, max 1,000,000), not per service | A capacity number checked against licence count before the service exists |
| "Who owns re-pointing the forwarding rule after each sandbox refresh?" | The routing domain is generated per address per org and cannot be promoted from sandbox | A named owner and the address stored in Custom Metadata, not in Apex |

What a proper configuration adds over just writing the handler: the mail
that arrives while you are deploying, over quota, or failing is held rather
than lost, the people who need to know are told, and the address survives a
sandbox refresh as a data edit rather than a re-deployment.

---

## Core Concepts

### Email Service vs Email Services Address

- **Email Service** (org-level) — the configuration: running
  user, max retention, accept-from policy, accept attachments,
  error response template.
- **Email Services Address** (per address) — the actual local-part
  + Salesforce-supplied subdomain. One Email Service can have
  many Addresses (e.g. `quotes-prod@...`, `quotes-dev@...`,
  `quotes-eu@...`), all routing to the same handler.

The handler doesn't see which Address received the email
*directly* — it sees the recipient in `email.toAddresses`. Branch
on the recipient if you need per-address logic.

`EmailServicesAddress` is not a separate deployable type: addresses are
nested inside the `EmailServicesFunction` file as repeated
`<emailServicesAddresses>` elements. The fields that decide behaviour:

| Element | Level | Required | What it decides |
|---|---|---|---|
| `apexClass` | service | yes | The handler. Must exist in the target org, or ship in the same payload |
| `attachmentOption` | service | yes | `None` / `NoContent` / `TextOnly` / `BinaryOnly` / `All` — platform-level attachment filter |
| `isTextAttachmentsAsBinary` | service | no | `true` delivers text attachments as `BinaryAttachment` (Blob), not `TextAttachment` (String) |
| `authorizedSenders` | service **and** address | no | Sender allow-list. Blank accepts anyone |
| `authorizationFailureAction` | service | yes | What an unlisted sender gets — even when the allow-list was set on the address |
| `isAuthenticationRequired` / `authenticationFailureAction` | service | no / yes | SPF, SenderId and DomainKeys verification of the sending server |
| `isErrorRoutingEnabled` / `errorRoutingAddress` | service | no | Send failure notifications to an internal address instead of the sender |
| `functionInactiveAction` | service | yes | Mail arriving while the service is off: `UseSystemDefault` / `Bounce` / `Discard` / `Requeue` |
| `overLimitAction` | service | yes | Mail arriving after the org's daily limit: same four values |
| `runAsUser` | address | yes | Username whose permissions the handler assumes for mail to *that* address |
| `localPart` | address | yes | The string before the `@`. The domain is system-generated and read-only |

Deployable XML, the handler, the test class and the post-deploy
verification SOQL: `references/metadata-examples.md`.

### `Messaging.InboundEmailHandler` interface

```apex
public with sharing class IncomingQuoteHandler implements Messaging.InboundEmailHandler {
    public Messaging.InboundEmailResult handleInboundEmail(
        Messaging.InboundEmail email,
        Messaging.InboundEnvelope envelope
    ) {
        Messaging.InboundEmailResult result = new Messaging.InboundEmailResult();
        try {
            processQuote(email);
            result.success = true;
        } catch (Exception ex) {
            ApplicationLogger.error('Quote email failed', ex);
            result.success = false;
            // Mailed to the sender: no exception text, no record Ids.
            result.message = 'We could not process this request. '
                + 'Please contact support@acme.example.';
        }
        return result;
    }
}
```

Three things to know:

1. **`global` is not required.** The Apex Developer Guide's own samples
   (`CreateTaskEmailExample`, `unsubscribe`) are `public with sharing`.
   Use `global` only when the class must be visible outside its namespace
   — a managed package. (`references/gotchas.md` § 1.)
2. **`InboundEmail` payload** — `subject`, `fromAddress`, `fromName`,
   `toAddresses`, `ccAddresses`, `replyTo`, `plainTextBody`, `htmlBody`,
   the matching `plainTextBodyIsTruncated` / `htmlBodyIsTruncated` flags,
   `messageId`, `inReplyTo`, `references`, `authenticationResults`,
   `binaryAttachments`, `textAttachments`, and `headers`
   (`InboundEmail.Header[]`, exposing only `name` and `value`).
   `InboundEnvelope` carries just `fromAddress` and `toAddress`.
3. **Return value.** `success = true` → delivery confirmed.
   `success = false` → Salesforce rejects the email and replies to the
   sender with `message`. `message` is sent irrespective of `success`, so
   a successful acknowledgement reply is also possible.

### Email threading via `In-Reply-To` and `References` headers

Email clients thread replies by `Message-Id` and `In-Reply-To`
headers. Salesforce has already parsed all three onto the object — do not
iterate `headers` for them:

```apex
Set<String> parents = new Set<String>();
if (String.isNotBlank(email.inReplyTo)) {
    parents.add(email.inReplyTo);          // String
}
if (email.references != null) {
    parents.addAll(email.references);      // String[]
}
String mine = email.messageId;             // this message's own Message-ID
```

`references` is documented as containing the parent emails' References and
message IDs "and possibly the In-Reply-To fields", so it often survives a
client that dropped `inReplyTo`. Check both, then fall back to a subject
token. Store your own outbound `Message-Id` on the record (or use
`EmailMessage.MessageIdentifier`, which is `idLookup`-enabled) so the
lookup has something to match.

For threading inbound emails to existing Salesforce records:

- **Email-to-Case threading** — uses `[ref:...]` token in subject /
  body. The system inserts the token in outbound replies; inbound
  replies preserve it; E2C extracts it and links the email to the
  existing case.
- **Custom service threading** — implement your own. Either embed
  a token in your outbound emails (case-insensitive, robust against
  client mangling) or look up by `In-Reply-To` against a stored
  Message-Id of your previous outbound.

### Attachment handling

```apex
for (Messaging.InboundEmail.BinaryAttachment att : email.binaryAttachments) {
    ContentVersion cv = new ContentVersion(
        Title = att.fileName,
        PathOnClient = att.fileName,
        VersionData = att.body,
        FirstPublishLocationId = parentRecordId
    );
    insert cv;
}
```

The attachment lists are `null`, not empty, when nothing was sent, and
`attachmentOption` = `NoContent` delivers metadata with `att.body` set to
`null` — guard both before touching `body`. Collect the records and issue
one DML statement after the loop.

Limits:

- **Max email size**: email services reject a message whose combined body
  text, body HTML and attachments exceeds approximately 25 MB, varying with
  language and character set. This is a platform ceiling, **not** a
  per-service setting — there is no `maxEmailSize` element.
  (`references/gotchas.md` § 4.)
- **Heap**: email services get **50 MB**, not the 6 MB synchronous budget.
  Do the Blob work inside the handler; hand off a `ContentVersion` Id, not
  a `Blob`. (`references/gotchas.md` § 11.)
- **Daily messages**: org-wide across all email services *and* On-Demand
  Email-to-Case — number of user licences multiplied by 1,000, maximum
  1,000,000. Overflow is handled by `overLimitAction`.
- **Org-wide file storage**: every saved attachment counts against the
  org's File Storage allocation. Plan retention.

### Email-to-Case vs custom service decision

| Need | Use |
|---|---|
| Create a Case from an email | **Email-to-Case** |
| Auto-response from a template | **Email-to-Case** (or On-Demand E2C) |
| Threading replies to existing Case | **Email-to-Case** with `[ref:...]` token |
| Create a Lead / Opportunity / Custom Object | **Custom service** |
| Upload a file to a record | **Custom service** |
| Trigger a downstream API callout | **Custom service** |
| Complex routing (e.g. "if subject starts with X, do Y") | **Custom service** (or E2C with assignment rules — depends) |
| Multi-language / encoded payloads | **Custom service** for full control |

---

## Common Patterns

### Pattern A — Lead-from-email-form

**When to use.** Marketing landing page submits a form via email
to a known address; need to create a Lead from each.

```apex
public with sharing class LeadFromEmail implements Messaging.InboundEmailHandler {
    public Messaging.InboundEmailResult handleInboundEmail(
        Messaging.InboundEmail email, Messaging.InboundEnvelope envelope
    ) {
        Messaging.InboundEmailResult res = new Messaging.InboundEmailResult();
        try {
            Lead l = new Lead(
                Email = email.fromAddress,
                LastName = email.fromName != null ? email.fromName : '(unknown)',
                Company = parseCompanyFromBody(email.plainTextBody),
                LeadSource = 'Email Form'
            );
            insert l;
            res.success = true;
        } catch (DmlException ex) {
            res.success = false;
            res.message = 'Could not create lead: ' + ex.getMessage();
        }
        return res;
    }
}
```

### Pattern B — File upload to existing record via subject token

**When to use.** Users email attachments to a routing address with
the record Id in the subject (`Upload — 0061a000007ABC`).

The handler parses the Id from the subject, validates it, attaches
files. Returns success / failure to the sender.

### Pattern C — Anti-spam allow-list

**When to use.** Public-facing routing address that gets spam.

```apex
private static final Set<String> ALLOWED_DOMAINS = new Set<String>{
    'acme.com', 'partner.example.com'
};

public Messaging.InboundEmailResult handleInboundEmail(
    Messaging.InboundEmail email, Messaging.InboundEnvelope envelope
) {
    String fromDomain = email.fromAddress.substringAfter('@').toLowerCase();
    if (!ALLOWED_DOMAINS.contains(fromDomain)) {
        Messaging.InboundEmailResult res = new Messaging.InboundEmailResult();
        res.success = false;
        res.message = 'Sender domain not authorized';
        return res;
    }
    // ... legitimate processing ...
}
```

For more nuanced allow-listing, store the list in Custom Metadata
or Custom Setting so admins can manage without redeploying Apex. Note the
platform already does the coarse version for free: `authorizedSenders` on
the service or the address rejects unlisted senders before Apex runs, and
`authorizationFailureAction` (service level) decides whether they are
bounced or discarded. Reach for Apex allow-listing when the rule is
per-sender-plus-content, not per-domain.

---

## Decision Guidance

| Situation | Approach | Reason |
|---|---|---|
| Create a Case from email | **Email-to-Case** | Built-in; threading, routing, auto-response included |
| Create any other record from email | **Custom Email Service + InboundEmailHandler** | E2C only creates Cases |
| Public address receives spam | **Custom service with allow-list** | E2C also has spam handling but per-Case |
| Need to upload files | **Custom service** | E2C Email Message attachments tied to Case |
| Threading replies to existing record | **`inReplyTo` + `references` first, subject token as fallback** | The identifiers come from the sender's client and are not always present; the token is in the visible subject |
| Inbound volume approaching (user licences x 1,000) | **Model the org-wide daily budget before adding the service** | The limit is shared across all email services and On-Demand Email-to-Case; overflow is handled by `overLimitAction` |
| Multi-language / RTL / encoded text attachment | **Custom handler reading `TextAttachment.charset`** | The body is re-encoded as UTF-8 for Apex; the original character set survives only on that property |
| Inbound email triggers a callout | **Custom service** + Platform Event for async work | Don't do the callout in the handler synchronously |
| Anonymous public access undesirable | **`authorizedSenders` + `authorizationFailureAction`** | Platform-level allow-list; rejects before Apex runs. Add `isAuthenticationRequired` to verify the sending server via SPF / SenderId / DomainKeys |

---

## Recommended Workflow

1. **Route the requirement.** Case creation goes to
   `admin/email-to-case-configuration` — stop here. Anything else
   continues. Run the `## Questions to Ask Before Configuring` table and
   record the answers in `templates/email-service-inbound-template.md`;
   each row names the element it sets.
2. **Provision the running user(s).** One integration user per address,
   with a named permission set. `runAsUser` is a username, per address,
   and Required — an address without one fails the deploy.
3. **Write the handler** against the shape in
   `references/metadata-examples.md` § The handler class:
   `public with sharing`, thread on `inReplyTo` / `references` with a
   subject-token fallback, null-guard both attachment lists, collect then
   insert once, and keep exception detail out of
   `InboundEmailResult.message`.
4. **Write the test class** from `references/metadata-examples.md` § The
   test class — `new Messaging.InboundEmail()` and
   `new Messaging.InboundEnvelope()` build the payload directly. Cover
   first email, threaded reply, `binaryAttachments = null`, and an
   attachment refused by policy.
5. **Author the `EmailServicesFunction` XML.** Copy the service block from
   `references/metadata-examples.md`, then set the six Required elements
   deliberately — `apexClass`, `attachmentOption`,
   `authenticationFailureAction`, `authorizationFailureAction`,
   `functionInactiveAction`, `overLimitAction` — plus one nested
   `<emailServicesAddresses>` per intake population.
6. **Check before deploying.**
   ```bash
   python3 skills/admin/email-service-inbound/scripts/check_email_service_inbound.py \
       --manifest-dir force-app/main/default
   ```
   It flags an unresolvable `apexClass`, an inactive service, an address
   missing `runAsUser`, `isErrorRoutingEnabled` with no
   `errorRoutingAddress`, an invented `maxEmailSize`, DML inside an
   attachment loop, a stack-trace leak and a synchronous callout. Then
   `sf project deploy start --dry-run` with the handler test.
7. **Read the routing address back and smoke-test.** The domain part is
   generated per org, so query
   `SELECT LocalPart, EmailDomainName, IsActive FROM EmailServicesAddress
   WHERE Function.FunctionName = '<name>'`, send a real message to
   `LocalPart@EmailDomainName`, and verify the success path, the
   failure reply, and that `errorRoutingAddress` received the failure
   notification. Store the address in Custom Metadata — it changes on
   every sandbox refresh.

---

## Review Checklist

- [ ] Handler is `public with sharing` unless it ships in a managed package.
- [ ] Handler returns `InboundEmailResult` with an explicit `success` value (never silently throws); `message` carries no exception detail.
- [ ] Both attachment lists null-guarded; `att.body` null-guarded; one DML statement after the loop, not inside it.
- [ ] `runAsUser` set on every address, each a documented integration user with a named permission set.
- [ ] `attachmentOption` chosen deliberately; size / count / MIME caps in Apex on whatever it lets through.
- [ ] `authorizedSenders` + `authorizationFailureAction` set for public-facing addresses.
- [ ] `isErrorRoutingEnabled` true with a monitored `errorRoutingAddress`.
- [ ] `functionInactiveAction` and `overLimitAction` are not `UseSystemDefault`.
- [ ] Threading reads `inReplyTo` **and** `references`, with a subject-token fallback.
- [ ] Truncation flags (`plainTextBodyIsTruncated`, `htmlBodyIsTruncated`) read before parsing.
- [ ] Test class covers first email, threaded reply, null attachment list, and a policy-refused attachment.
- [ ] Routing address read from `EmailServicesAddress.EmailDomainName`, stored in Custom Metadata, never hardcoded.
- [ ] `scripts/check_email_service_inbound.py --manifest-dir …` is clean.

---

## Salesforce-Specific Gotchas

1. **`global` is a packaging decision, not an interface requirement.** The guide's own samples are `public with sharing`. (§ 1.)
2. **`email.headers` is `InboundEmail.Header[]`, not a `Map`** — and the three headers you want are already parsed onto the object. (§ 2.)
3. **`success = false` mails your `message` to the sender.** Never a stack trace. `message` is also sent when `success` is true. (§ 3.)
4. **The ~25 MB ceiling is a platform limit, not a service setting.** There is no `maxEmailSize` element to raise. (§ 4.)
5. **The address domain is generated per address per org** and is read-only. Query `EmailDomainName`; never hardcode. (§ 5.)
6. **`runAsUser` is Required per address, not per service** — two addresses on one service can run the same Apex as different users. (§ 6.)
7. **`inReplyTo` comes from the sender's client**; check `references` too and keep a subject-token fallback. (§ 7.)
8. **The daily message limit is org-wide** and shared with On-Demand Email-to-Case: licences x 1,000, max 1,000,000. (§ 10.)
9. **Email-service Apex gets a 50 MB heap, not 6 MB** — keep the Blob work in the handler. (§ 11.)
10. **Sandbox routing addresses cannot be copied to production**, and refreshes regenerate them. (§ 12.)
11. **`authorizationFailureAction` is service-level** even when `authorizedSenders` was set on the address. (§ 13.)
12. **Bodies and text attachments arrive truncated with a flag** you must read before parsing. (§ 14.)
13. **`EmailServicesFunction` accepts no `*` wildcard in package.xml.** Name every service. (§ 16.)

---

## Output Artifacts

| Artifact | Description |
|---|---|
| `Messaging.InboundEmailHandler` class | The handler implementation (`references/metadata-examples.md`) |
| Test class | Synthetic `InboundEmail` / `InboundEnvelope` payloads; four named cases |
| `emailservices/<Name>.emailservices-meta.xml` | The service plus its nested address records |
| `package.xml` entries | `ApexClass` + `EmailServicesFunction` (no wildcard) |
| Running-user permission set | One per address, named in the config workbook |
| Allow-list source | Custom Metadata / Custom Setting for admin-managed sender list |
| Threading strategy | `inReplyTo` / `references` lookup plus the subject-token format |
| Routing-address record | `LocalPart` + `EmailDomainName` per org, stored in Custom Metadata |

---

## Reference Files

| File | Read it when |
|---|---|
| `references/metadata-examples.md` | You are writing the `EmailServicesFunction` XML, the handler, the test class or the package.xml, or you need the post-deploy SOQL that reveals the routing address |
| `references/gotchas.md` | A configured service behaves unexpectedly — mail bounced or vanished, attachments missing or the wrong Apex type, an address that worked in sandbox and not in production, a `global`/`public` compile argument |
| `references/examples.md` | You want worked before/after code: safe failure messages, threaded case lookup, Custom-Metadata allow-listing, and the two-layer attachment policy |
| `references/llm-anti-patterns.md` | You are reviewing AI-generated inbound-email code or advice, or want the detection hints for each recurring mistake |
| `references/well-architected.md` | You are justifying the design — pillar mapping, the tradeoffs behind one-service-many-addresses, and the official sources behind every claim here |

Supporting files: `templates/email-service-inbound-template.md` (work
template mapping each decision to its metadata element) and
`scripts/check_email_service_inbound.py --manifest-dir <dir>` (metadata +
handler checks).

---

## Related Skills

- `admin/email-to-case-configuration` — when the requirement is case creation; this skill is the custom-service alternative.
- `admin/email-templates-and-alerts` — outbound email infrastructure, including the reply your handler acknowledges with.
- `apex/apex-email-services` — the Apex-side treatment of the same handler; this skill owns the service configuration.
- `apex/apex-event-bus-subscriber` — when the handler publishes a Platform Event for async downstream work.
- `apex/dynamic-apex` — when the handler needs Schema describe to create records of varying types.
- `admin/custom-metadata-types` — where the sender allow-list and the per-org routing address belong.
