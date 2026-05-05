---
name: email-service-inbound
description: "Inbound email processing in Salesforce via Email Services + the `Messaging.InboundEmailHandler` Apex interface. Covers EmailService configuration (running user, accept-from address, attachment handling, error / failure routing), the EmailServicesAddress per-routing-address pattern, the handler's `Messaging.InboundEmail` payload (text body, HTML body, headers, attachments, in-reply-to threading), and the canonical Email-to-Case alternative for case creation. NOT for outbound email (use admin/email-templates-and-alerts), NOT for Email-to-Case flow customization itself (use service/email-to-case)."
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
tags:
  - email-service
  - inboundemailhandler
  - emailservicesaddress
  - inbound-email
  - email-to-case
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
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-05-05
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
Email-to-Case-specific configuration — `service/email-to-case`.
This skill is the custom-handler path.

---

## Before Starting

- **Decide custom service vs Email-to-Case.** Case creation? E2C
  is built; don't reinvent. Anything else? Custom service.
- **Plan the running user.** The handler runs as the user
  configured on the Email Service. Their permissions determine
  what the handler can do. Use a dedicated integration user.
- **Plan the accept-from policy.** Anonymous public addresses
  receive spam; consider authorized-senders allow-listing or
  rate limiting.
- **Plan attachment handling.** Salesforce has limits (max email
  size, max attachment size, total org file storage). Decide
  store vs discard before traffic ramps.

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

### `Messaging.InboundEmailHandler` interface

```apex
global class IncomingQuoteHandler implements Messaging.InboundEmailHandler {
    global Messaging.InboundEmailResult handleInboundEmail(
        Messaging.InboundEmail email,
        Messaging.InboundEnvelope envelope
    ) {
        Messaging.InboundEmailResult result = new Messaging.InboundEmailResult();
        try {
            processQuote(email);
            result.success = true;
        } catch (Exception ex) {
            result.success = false;
            result.message = 'Could not process: ' + ex.getMessage();
            ApplicationLogger.error('Quote email failed', ex);
        }
        return result;
    }
}
```

Three things to know:

1. **`global` is required.** Same as `SandboxPostCopy`.
2. **`InboundEmail` payload** — `subject`, `fromAddress`,
   `fromName`, `toAddresses`, `ccAddresses`, `plainTextBody`,
   `htmlBody`, `headers` (a list, not a map — the `references` /
   `inReplyTo` headers are critical for threading), `binaryAttachments`,
   `textAttachments`.
3. **Return value.** `success = true` → delivery confirmed.
   `success = false` + `message` → bounce-back response. The
   `message` is what the sender sees.

### Email threading via `In-Reply-To` and `References` headers

Email clients thread replies by `Message-Id` and `In-Reply-To`
headers. Salesforce's email service parses them in `email.headers`:

```apex
String inReplyTo = null;
for (Messaging.InboundEmail.Header h : email.headers) {
    if (h.name.toLowerCase() == 'in-reply-to') {
        inReplyTo = h.value;
        break;
    }
}
```

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

Limits:

- **Max email size**: ~25 MB total (configured per Email Service;
  email-with-attachments above this are bounced).
- **Max single attachment**: limited by the email-size cap.
- **Org-wide file storage**: every saved attachment counts against
  the org's File Storage allocation. Plan retention.

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
global class LeadFromEmail implements Messaging.InboundEmailHandler {
    global Messaging.InboundEmailResult handleInboundEmail(
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

global Messaging.InboundEmailResult handleInboundEmail(
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
or Custom Setting so admins can manage without redeploying Apex.

---

## Decision Guidance

| Situation | Approach | Reason |
|---|---|---|
| Create a Case from email | **Email-to-Case** | Built-in; threading, routing, auto-response included |
| Create any other record from email | **Custom Email Service + InboundEmailHandler** | E2C only creates Cases |
| Public address receives spam | **Custom service with allow-list** | E2C also has spam handling but per-Case |
| Need to upload files | **Custom service** | E2C Email Message attachments tied to Case |
| Threading replies to existing record | **Subject token** (`[ref:...]`) or `In-Reply-To` header parsing | Email clients mangle these; tokens are more robust |
| Inbound volume > 1K / day per address | **Plan governor budget** + dedicated running user | High volume can hit Apex governor in a single batch |
| Multi-language / RTL / encoded subject | **Custom handler with explicit charset handling** | E2C parses for the common cases; edge cases break it |
| Inbound email triggers a callout | **Custom service** + Platform Event for async work | Don't do the callout in the handler synchronously |
| Anonymous public access undesirable | **Email Service `Authorize Email Addresses`** | Per-Service allow-list at the platform level |

---

## Recommended Workflow

1. **Decide custom service vs Email-to-Case.** Case creation → E2C; everything else → custom.
2. **Provision a dedicated running user** for the Email Service. Document its required permissions.
3. **Implement `Messaging.InboundEmailHandler`** with the right business logic.
4. **Configure Email Service** in Setup → Email → Email Services. Set running user, max email size, accept attachments, error-response template.
5. **Create one or more Email Services Addresses.** Each gets a Salesforce-supplied subdomain.
6. **Plan threading** if applicable (subject token, `In-Reply-To` parse).
7. **Test by sending real emails** to the address. Verify success / failure paths.
8. **Monitor.** Inbound email volume, handler exceptions, attachment storage growth.

---

## Review Checklist

- [ ] Class implements `Messaging.InboundEmailHandler` with `global` access.
- [ ] Handler returns `InboundEmailResult` with explicit `success` value (never silently throws).
- [ ] Running user is dedicated to the Email Service, with documented permissions.
- [ ] Allow-list / spam handling for public-facing addresses.
- [ ] Attachment retention policy explicit.
- [ ] Threading via subject token or `In-Reply-To` if applicable.
- [ ] Test class covers success path, malformed input, attachment-too-large, allow-list-rejection.
- [ ] Email Service `Max Email Size` and `Accept Attachments` configured deliberately.

---

## Salesforce-Specific Gotchas

1. **`Messaging.InboundEmailHandler` requires `global` access.** Same as `SandboxPostCopy`. (See `references/gotchas.md` § 1.)
2. **`email.headers` is a `List<Header>`, not a `Map`.** Iterate to find the header you want. (See `references/gotchas.md` § 2.)
3. **Returning `success = false`** triggers a bounce-back to the sender. The `message` is what the sender sees — don't expose stack traces. (See `references/gotchas.md` § 3.)
4. **Max email size has a hard ceiling**; emails above are bounced before the handler sees them. (See `references/gotchas.md` § 4.)
5. **Email Services Address subdomain is Salesforce-supplied**, not customer-domain-mappable. For customer domains, use email forwarding from the customer side. (See `references/gotchas.md` § 5.)
6. **The handler runs in the configured running user's context**, not the sender's. FLS / sharing applies to that user. (See `references/gotchas.md` § 6.)
7. **In-Reply-To / Message-Id headers are unreliable** across email clients; subject-token threading is more robust. (See `references/gotchas.md` § 7.)

---

## Output Artifacts

| Artifact | Description |
|---|---|
| `Messaging.InboundEmailHandler` class | The handler implementation |
| Test class | Covers handler with synthetic `InboundEmail` payloads |
| Email Service configuration | Documented setup steps in Setup → Email → Email Services |
| Allow-list source | Custom Metadata / Custom Setting for admin-managed sender list |
| Threading strategy | Subject token format or `In-Reply-To` parsing logic |

---

## Related Skills

- `service/email-to-case` — when the requirement is case creation; this skill is the custom-service alternative.
- `admin/email-templates-and-alerts` — outbound email infrastructure.
- `apex/apex-event-bus-subscriber` — when the handler publishes a Platform Event for async downstream work.
- `apex/dynamic-apex` — when the handler needs Schema describe to create records of varying types.
