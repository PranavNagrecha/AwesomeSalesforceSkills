# Examples — Inbound Email Service

## Example 1 — Returning `success = false` exposes a stack trace

**Wrong code.**

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

**Right code.**

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

Subject tokens survive client mangling better than `In-Reply-To`
header threading.

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

**Right policy.**

- Skip attachments larger than 5 MB unless from allow-listed domain.
- Skip non-allow-listed MIME types.
- Cap attachments per email at 10.
- Document retention: how long do attached files live before
  archive?

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
