# Gotchas — Apex Email Services

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Inactive Email Service Address Silently Discards All Mail

**What happens:** If the Email Service configuration in Setup > Email Services has **Active** unchecked, every email sent to the service address is discarded without any error, bounce, or log entry. The handler Apex class is never invoked. No exception is thrown. No debug log is generated.

**When it occurs:** Most commonly during initial deployment. Practitioners scaffold the handler, configure the Email Service, copy the generated address, and start testing — but forget to tick **Active** before saving. It also occurs after an org refresh where the sandbox Email Service is not re-activated, or after a deployment that overwrites metadata and resets the active flag.

**How to avoid:** Make the **Active** checkbox the first thing you verify when debugging "no traffic" issues. Include "Email Service address is Active" as a mandatory item in your deployment checklist. If deploying via Metadata API or a package, confirm `EmailServicesFunction` metadata includes `isActive: true` in the deployed file.

---

## Gotcha 2: handleInboundEmail Runs as the Context User — and Its Default Access Mode Inverted at API 67.0

**What happens:** There is no authenticated sender at any API version — `email.fromAddress` is unverified header data — and `UserInfo.getUserId()` returns the Email Service's configured **Context User**, never the person who sent the mail. What the handler's database operations *enforce* is gated by the `apiVersion` in the class's `.cls-meta.xml`, not by the org's release. At **66.0 and below**, a handler class declared without a sharing keyword is `without sharing` and its SOQL/DML run in system mode: record-level security, field-level security, and permission sets are entirely bypassed, and any `insert` or `update` inside the handler affects records the sending user could never access through the UI. At **67.0+** (Summer '26) both defaults invert — the bare class runs `with sharing`, and SOQL, SOSL, DML, and `Database` methods default to user mode, evaluated against that Context User. See [`agents/_shared/AGENT_CONTRACT.md`](../../../../agents/_shared/AGENT_CONTRACT.md) § *Apex security idiom by API version* for the canonical table.

**When it occurs:** Any time the handler inserts records with sensitive fields, attaches files to restricted records, or queries data based on sender identity without re-validating permissions. The risk is elevated when senders are external (the handler accepts emails from any address by default unless `Accept Email From` is configured).

**How to avoid:** Restrict sender addresses in the Email Service configuration (`Accept Email From` field). Read the handler's `.cls-meta.xml` before reasoning about enforcement: at 66.0 and below, delegate any record access that should respect sharing to a helper class declared `with sharing` (the keyword is a class modifier — there is no method-level form — and the callee's keyword governs the queries it runs itself); at 67.0+ the default is already `with sharing` plus user mode, which relocates the escalation surface onto the Context User rather than removing it — point the Email Service at a least-privilege integration user, not a System Administrator. Never treat `fromAddress` alone as a trusted identity — validate it against known internal users before granting elevated record access. Log all handler invocations to a custom audit object.

---

## Gotcha 3: Attachment Lists Are Null, Not Empty, When No Attachments Exist

**What happens:** When an inbound email has no text attachments, `email.textAttachments` is `null` — not an empty list. The same applies to `email.binaryAttachments`. Calling `.isEmpty()` or iterating with a for-each loop on a null list throws a `NullPointerException` and causes the handler to fail.

**When it occurs:** Any time you write `for (InboundEmail.TextAttachment a : email.textAttachments)` without a null guard. This works fine during testing (where you control the email object) but fails in production when emails arrive without attachments.

**How to avoid:** Always guard both attachment lists before iterating:

```apex
if (email.textAttachments != null) {
    for (Messaging.InboundEmail.TextAttachment att : email.textAttachments) {
        // safe
    }
}
if (email.binaryAttachments != null) {
    for (Messaging.InboundEmail.BinaryAttachment att : email.binaryAttachments) {
        // safe
    }
}
```

---

## Gotcha 4: Large Attachments Processed Synchronously Can Exhaust Heap

**What happens:** Binary attachments are passed directly into `handleInboundEmail` as `Blob` values. The heap ceiling here is **50 MB** — email services are documented as an exception to the ordinary 6 MB synchronous / 12 MB asynchronous Apex heap, so a large attachment does *not* blow heap merely by arriving. What blows heap is **transforming** it: `EncodingUtil.base64Encode(blob)` allocates a second, ~33%-larger copy; `blob.toString()` allocates a third; string concatenation in a parse loop allocates one per iteration. Three copies of a 15 MB attachment plus parse intermediates is how you reach 50 MB and get a `System.LimitException` that fails the email processing.

Get the number right in both directions. Under-stating it (12 MB) makes teams defer work that would have fit and mis-size their chunking; assuming heap is unbounded because "50 MB is huge" ignores that the multiplier is on transformations, not on the payload.

**When it occurs:** When emails arrive with large PDFs, images, or binary files. The problem is invisible during unit tests because test `InboundEmail` objects use synthetic small payloads that never approach real attachment sizes.

**How to avoid:** Store the attachment Blob to a `ContentVersion` immediately (this operation is fast and uses minimal heap for the DML statement itself), then enqueue a `Queueable` to perform any expensive processing. The Queueable runs in a separate transaction with a fresh CPU and DML budget and a retry surface — but its heap ceiling is the ordinary 12 MB asynchronous limit, *lower* than the handler's 50 MB, so size the deferred work against 12 MB.

---

## Gotcha 5: Test Classes Cannot Send Real Emails — Construct InboundEmail Directly

**What happens:** Apex test classes cannot trigger actual email delivery to an Email Service address. Developers who try to test handlers by routing real emails through a sandbox are testing the Email Services infrastructure, not their handler logic — and real email delivery in sandboxes is unreliable and slow.

**When it occurs:** When writing the first test for an `InboundEmailHandler`, especially when inheriting code from developers unfamiliar with Apex Email Services testing conventions.

**How to avoid:** Instantiate `Messaging.InboundEmail` and `Messaging.InboundEnvelope` directly in your test class and call `handleInboundEmail` as a regular Apex method:

```apex
@IsTest
static void testOrderCreation() {
    Messaging.InboundEmail email = new Messaging.InboundEmail();
    email.subject = '[ORD-12345] NEW_ORDER';
    email.plainTextBody = 'Order details here.';
    email.fromAddress = 'wms@vendor.example.com';

    Messaging.InboundEnvelope env = new Messaging.InboundEnvelope();
    env.toAddress = 'orders@abc.salesforce.com';
    env.fromAddress = 'wms@vendor.example.com';

    Test.startTest();
    OrderEmailHandler handler = new OrderEmailHandler();
    Messaging.InboundEmailResult result = handler.handleInboundEmail(email, env);
    Test.stopTest();

    System.assertEquals(true, result.success);
    System.assertEquals(1, [SELECT COUNT() FROM Order__c WHERE OrderNumber__c = 'ORD-12345']);
}
```
