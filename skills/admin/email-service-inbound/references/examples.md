# Examples — Inbound Email Service

## Example 1 — Returning `success = false` exposes a stack trace

**Wrong code** (catch-block excerpt from the handler).

```apex
} catch (Exception ex) {
    res.success = false;
    res.message = ex.getMessage() + '\n' + ex.getStackTraceString();
    return res;
}
```

**What goes wrong.** The sender (potentially anonymous public)
receives a bounce-back containing the Apex stack trace —
information disclosure.

**Right code** (catch-block excerpt from the handler).

```apex
} catch (Exception ex) {
    ApplicationLogger.error('Inbound email failed', ex);
    res.success = false;
    res.message = 'We could not process your email. Please contact support@acme.com if this persists.';
    return res;
}
```

Friendly message to the sender; full stack trace logged for the
admin.

---

## Example 2 — Threading via subject token

**Context.** Outbound emails carry `[Acme:Case-12345]` in the
subject. Inbound replies preserve the token. Custom service uses
it to thread to the existing Case.

```apex
private static Pattern TOKEN_RE = Pattern.compile('\\[Acme:Case-(\\d+)\\]');

private static Id resolveCaseFromSubject(String subject) {
    if (subject == null) return null;
    Matcher m = TOKEN_RE.matcher(subject);
    if (!m.find()) return null;
    String caseNumber = m.group(1);
    List<Case> cs = [SELECT Id FROM Case WHERE CaseNumber = :caseNumber LIMIT 1];
    return cs.isEmpty() ? null : cs[0].Id;
}
```

Subject tokens survive client mangling better than header threading, but
they are the *fallback*, not the first attempt: the platform already parses
the RFC 2822 identifiers into `email.messageId`, `email.inReplyTo` and
`email.references`, so try those first and fall through to the token only
when the chain is broken.

```apex
private static Id resolveCase(Messaging.InboundEmail email) {
    Set<String> parents = new Set<String>();
    if (String.isNotBlank(email.inReplyTo)) parents.add(email.inReplyTo);
    if (email.references != null) parents.addAll(email.references);
    if (!parents.isEmpty()) {
        List<EmailMessage> prior = [
            SELECT ParentId FROM EmailMessage
            WHERE MessageIdentifier IN :parents AND ParentId != null
            WITH USER_MODE ORDER BY MessageDate DESC LIMIT 1
        ];
        if (!prior.isEmpty()) return prior[0].ParentId;
    }
    return resolveCaseFromSubject(email.subject);   // token fallback
}
```

`EmailMessage.MessageIdentifier` is the object-reference field that stores
"the ID of the email message" and is `idLookup`-enabled, which is what
makes this lookup possible on the standard object.

---

## Example 3 — Allow-list-driven anti-spam

**Context.** Public address `quotes@inbound.acme.com` receives spam.

**Approach.** Custom Metadata Type `Allowed_Email_Domain__mdt` with
records like `acme.com`, `partner-vendor.com`. Handler checks
sender's domain against the list:

```apex
private static Set<String> allowedDomains() {
    Set<String> out = new Set<String>();
    for (Allowed_Email_Domain__mdt d : Allowed_Email_Domain__mdt.getAll().values()) {
        out.add(d.Domain__c.toLowerCase());
    }
    return out;
}
```

Admin-editable list; no Apex redeploy when a new partner needs
access.

---

## Example 4 — Attachment storage policy

**Wrong instinct.** Save every binary attachment to ContentVersion
without size / type / count checks.

**What goes wrong.** Spammer sends 10 MB attachments daily for
months; org's File Storage allocation fills up; legitimate file
operations start failing.

**Right policy.** Two layers. The platform layer filters before Apex
runs, via `attachmentOption` on the `EmailServicesFunction`
(`None` | `NoContent` | `TextOnly` | `BinaryOnly` | `All`); the Apex layer
enforces size, count and MIME type on what survives. Drive the thresholds
from Custom Metadata so a policy change is a data deploy, not a code
deploy.

```apex
/**
 * Attachment admission policy. Returns the reason an attachment was
 * refused, or null when it is acceptable. Thresholds live in
 * Email_Intake_Policy__mdt so admins can tune them without Apex.
 */
public with sharing class AttachmentPolicy {

    private final Integer maxBytes;
    private final Integer maxCount;
    private final Set<String> allowedMimeSubTypes;

    public AttachmentPolicy(String policyName) {
        Email_Intake_Policy__mdt p = Email_Intake_Policy__mdt.getInstance(policyName);
        this.maxBytes = (Integer) (p.Max_Attachment_MB__c * 1024 * 1024);
        this.maxCount = (Integer) p.Max_Attachments_Per_Email__c;
        this.allowedMimeSubTypes = new Set<String>();
        for (String s : p.Allowed_Mime_Types__c.split(',')) {
            this.allowedMimeSubTypes.add(s.trim().toLowerCase());
        }
    }

    public Integer maxAttachments() {
        return this.maxCount;
    }

    /** null => accept. Non-null => the audit reason for refusing. */
    public String refuse(Messaging.InboundEmail.BinaryAttachment att) {
        // attachmentOption = NoContent hands over metadata with a null body.
        if (att.body == null) {
            return 'no body (service is set to NoContent, or the part was empty)';
        }
        if (att.body.size() > this.maxBytes) {
            return 'over ' + this.maxBytes + ' bytes';
        }
        String mime = att.mimeTypeSubType == null
            ? ''
            : att.mimeTypeSubType.toLowerCase();
        if (!this.allowedMimeSubTypes.contains(mime)) {
            return 'MIME type ' + mime + ' not allow-listed';
        }
        return null;
    }
}
```

Refusals are audit events, not errors: log the reason against the parent
record and still return `success = true`, so the sender is not bounced for
attaching a signature image.

| Layer | Control | Where it lives |
|---|---|---|
| Platform | Accept none / metadata-only / text / binary / all | `attachmentOption` in `emailservices/*.xml` |
| Platform | Text attachments delivered as Blob instead of String | `isTextAttachmentsAsBinary` |
| Apex | Per-attachment byte cap | `Email_Intake_Policy__mdt.Max_Attachment_MB__c` |
| Apex | Per-email count cap | `Email_Intake_Policy__mdt.Max_Attachments_Per_Email__c` |
| Apex | MIME allow-list | `Email_Intake_Policy__mdt.Allowed_Mime_Types__c` |
| Operations | Retention / archive of stored files | Documented, with an owner and a review date |

The ~25 MB per-message ceiling is not one of these layers — it is enforced
by the platform before the handler runs, and is not configurable (see
`gotchas.md` § 4).

---

## Anti-Pattern: Doing a synchronous callout in the handler

```apex
HttpRequest req = new HttpRequest();
req.setEndpoint('https://crm-extension.example.com/notify');
req.setMethod('POST');
new Http().send(req);  // synchronous, in the handler
```

**What goes wrong.** Inbound email volume spikes; every email
makes a callout; callout latency (or failure) blocks email
processing; emails stack up in the platform's incoming queue.

**Correct.** Publish a Platform Event from the handler; an Apex
subscriber does the callout asynchronously. The handler returns
`success = true` immediately; the callout happens later.
