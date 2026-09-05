# Metadata Examples — Inbound Email Service

Deployable shapes for an Email Service. Element names, required flags and
enum values come from the Metadata API Developer Guide v62 PDF,
`EmailServicesFunction` section (api_meta.pdf p. 1017–1020, field table for
`EmailServicesFunction` and the nested `EmailServicesAddress` table). The
worked example extends that field table to a realistic two-address service;
the guide ships no sample definition for this type.

Validate the result with:

```bash
python3 skills/admin/email-service-inbound/scripts/check_email_service_inbound.py \
    --manifest-dir force-app/main/default
```

## Where the files live

| Type | package.xml `<name>` | File in a DX project | Notes |
|---|---|---|---|
| Email service + its addresses | `EmailServicesFunction` | `emailservices/Quote_Intake.emailservices-meta.xml` | Available in API version 42.0 and later; components have the suffix `.xml` and live in the `emailservices` folder (api_meta.pdf, `EmailServicesFunction` § File Suffix and Directory Location / Version) |
| Handler class | `ApexClass` | `classes/QuoteIntakeEmailHandler.cls` | Referenced by `apexClass`; must already exist in the target org or ship in the same deployment |
| Handler test | `ApexClass` | `classes/QuoteIntakeEmailHandlerTest.cls` | |

`EmailServicesAddress` is **not** a separate deployable type — addresses are
nested inside the `EmailServicesFunction` file as repeated
`<emailServicesAddresses>` elements (api_meta.pdf: `emailServicesAddresses`
is typed `EmailServicesAddress`, "A list of EmailServiceAddress records").

`EmailServicesFunction` does **not** support the `*` wildcard in package.xml
(api_meta.pdf, Wildcard Support note closing the `EmailServicesFunction`
section) — list every service by `functionName`.

UNVERIFIED (2026-09-05): the guide states the MDAPI suffix (`.xml`) and
folder (`emailservices`) but not the Salesforce DX source-format filename.
The `-meta.xml` form above matches the convention used by the sibling
`apex/apex-email-services` checker; confirm against `sf project retrieve`
output in your own project before scripting around it.

## The email service

```xml
<?xml version="1.0" encoding="UTF-8"?>
<EmailServicesFunction xmlns="http://soap.sforce.com/2006/04/metadata">
    <functionName>Quote_Intake</functionName>
    <apexClass>QuoteIntakeEmailHandler</apexClass>
    <isActive>true</isActive>

    <!-- Attachments: All | BinaryOnly | TextOnly | NoContent | None -->
    <attachmentOption>BinaryOnly</attachmentOption>
    <isTextAttachmentsAsBinary>false</isTextAttachmentsAsBinary>

    <!-- Sender allow-list at the service level. Blank = accept from anyone. -->
    <authorizedSenders>acme.example,partner-vendor.example</authorizedSenders>
    <authorizationFailureAction>Discard</authorizationFailureAction>

    <!-- SPF / SenderId / DomainKeys verification of the sending server -->
    <isAuthenticationRequired>true</isAuthenticationRequired>
    <authenticationFailureAction>Bounce</authenticationFailureAction>

    <!-- Failures page the integration team, not the sender -->
    <isErrorRoutingEnabled>true</isErrorRoutingEnabled>
    <errorRoutingAddress>salesforce-integrations@acme.example</errorRoutingAddress>

    <!-- Service switched off (cutover, incident): hold, do not lose mail -->
    <functionInactiveAction>Requeue</functionInactiveAction>

    <!-- Org daily processing limit reached: hold, do not lose mail -->
    <overLimitAction>Requeue</overLimitAction>

    <isTlsRequired>false</isTlsRequired>

    <!-- Address 1: production intake -->
    <emailServicesAddresses>
        <developerName>Quote_Intake_Prod</developerName>
        <localPart>quotes</localPart>
        <isActive>true</isActive>
        <runAsUser>svc.email.intake@acme.example</runAsUser>
        <authorizedSenders>acme.example</authorizedSenders>
    </emailServicesAddresses>

    <!-- Address 2: partner intake, same handler, wider allow-list -->
    <emailServicesAddresses>
        <developerName>Quote_Intake_Partner</developerName>
        <localPart>quotes-partner</localPart>
        <isActive>true</isActive>
        <runAsUser>svc.email.partner@acme.example</runAsUser>
        <authorizedSenders>partner-vendor.example</authorizedSenders>
    </emailServicesAddresses>
</EmailServicesFunction>
```

### How to read it

- `functionName`, `apexClass`, `attachmentOption`,
  `authenticationFailureAction`, `authorizationFailureAction`,
  `functionInactiveAction` and `overLimitAction` are all marked **Required**
  in the field table. A file that omits any of them is rejected at deploy
  time, not at runtime.
- `functionName` is a 64-character API name: begins with a letter, no
  spaces, no trailing underscore, no two consecutive underscores, unique in
  the org.
- `developerName` on each address has the same rules but a **25-character**
  cap, and must be unique among addresses under the same parent service.
- `localPart` is only the string before the `@`. The domain part is
  generated by Salesforce per address and is not settable here — query
  `EmailServicesAddress.EmailDomainName` after deploy to learn it
  (object_reference.pdf, `EmailServicesAddress` § `EmailDomainName`:
  "A read only field you can query that contains the system-generated
  domain part").
- `runAsUser` is a **username**, not an Id — the field is typed `string` in
  the Metadata API even though the SOAP object exposes it as
  `RunAsUserId` (a reference).
- `authorizedSenders` exists on both the service and each address. An
  unlisted sender triggers `authorizationFailureAction`, which is defined
  on the **service** only.
- The four `EmailServicesErrorAction` fields share one enum:
  `UseSystemDefault`, `Bounce`, `Discard`, `Requeue`. `Requeue` holds the
  message for retry for 24 hours and only then bounces it.
- `attachmentOption` values: `None` (message accepted, attachments
  discarded), `NoContent` (filename/MIME type given to Apex, body `null`),
  `TextOnly`, `BinaryOnly`, `All`.
- `isTextAttachmentsAsBinary` = `true` hands text attachments to Apex as
  `Messaging.InboundEmail.BinaryAttachment` (Blob body) instead of
  `TextAttachment` (String body) — flip it and your handler stops
  compiling against the right type.
- `isTlsRequired` is documented as "Not currently in use." Set it, but do
  not design around it.
- There is no `maxEmailSize` element. The ~25 MB ceiling is a platform
  limit, not per-service configuration (see `gotchas.md` § 4).

## The handler class

`classes/QuoteIntakeEmailHandler.cls`

```apex
/**
 * Inbound handler for the Quote_Intake email service.
 * `public` is sufficient: the Apex Developer Guide's own sample
 * (`CreateTaskEmailExample`) is declared `public with sharing`.
 * Use `global` only when the class must be visible outside its namespace.
 */
public with sharing class QuoteIntakeEmailHandler
        implements Messaging.InboundEmailHandler {

    private static final Integer MAX_ATTACHMENT_BYTES = 5 * 1024 * 1024;
    private static final Integer MAX_ATTACHMENTS = 10;

    public Messaging.InboundEmailResult handleInboundEmail(
        Messaging.InboundEmail email,
        Messaging.InboundEnvelope envelope
    ) {
        Messaging.InboundEmailResult result = new Messaging.InboundEmailResult();
        try {
            // 1. Thread on the RFC 2822 identifiers the platform already parsed.
            //    email.inReplyTo / email.references / email.messageId are
            //    first-class properties; no header iteration required.
            Id existingQuoteId = resolveThread(email);

            // 2. Create or update the quote request record.
            Quote_Request__c qr = new Quote_Request__c(
                Id                 = existingQuoteId,
                Requester_Email__c = email.fromAddress,
                Subject__c         = email.subject,
                Body__c            = email.plainTextBody,
                Message_Id__c      = email.messageId
            );
            upsert qr;

            // 3. Attachments: collect first, DML once. Never insert in the loop.
            List<ContentVersion> files = collectAttachments(email, qr.Id);
            if (!files.isEmpty()) {
                insert files;
            }

            // 4. Truncated bodies are a data-loss signal, not an error.
            if (email.plainTextBodyIsTruncated == true) {
                qr.Body_Truncated__c = true;
                update qr;
            }

            result.success = true;
        } catch (Exception ex) {
            // Never put ex.getStackTraceString() here: `message` is returned
            // in the body of a reply email to the original sender.
            System.debug(LoggingLevel.ERROR, 'Quote intake failed: ' + ex);
            result.success = false;
            result.message =
                'We could not process your quote request. '
                + 'Please contact support@acme.example and quote reference '
                + email.messageId + '.';
        }
        return result;
    }

    /** Match this reply to an existing request via In-Reply-To / References. */
    private Id resolveThread(Messaging.InboundEmail email) {
        Set<String> parents = new Set<String>();
        if (String.isNotBlank(email.inReplyTo)) {
            parents.add(email.inReplyTo);
        }
        if (email.references != null) {
            parents.addAll(email.references);
        }
        if (parents.isEmpty()) {
            return null;
        }
        List<Quote_Request__c> found = [
            SELECT Id
            FROM Quote_Request__c
            WHERE Message_Id__c IN :parents
            WITH USER_MODE
            ORDER BY CreatedDate DESC
            LIMIT 1
        ];
        return found.isEmpty() ? null : found[0].Id;
    }

    /** Size / count capped; returns records for a single bulk insert. */
    private List<ContentVersion> collectAttachments(
        Messaging.InboundEmail email, Id parentId
    ) {
        List<ContentVersion> out = new List<ContentVersion>();
        // The attachment lists are null, not empty, when nothing was sent.
        if (email.binaryAttachments == null) {
            return out;
        }
        for (Messaging.InboundEmail.BinaryAttachment att : email.binaryAttachments) {
            if (out.size() >= MAX_ATTACHMENTS) {
                break;
            }
            // attachmentOption = NoContent delivers metadata with a null body.
            if (att.body == null || att.body.size() > MAX_ATTACHMENT_BYTES) {
                continue;
            }
            out.add(new ContentVersion(
                Title                     = att.fileName,
                PathOnClient              = att.fileName,
                VersionData               = att.body,
                FirstPublishLocationId    = parentId
            ));
        }
        return out;
    }
}
```

## The test class

`classes/QuoteIntakeEmailHandlerTest.cls`

Both `Messaging.InboundEmail` and `Messaging.InboundEnvelope` have public
no-argument constructors (apexref.pdf, `InboundEmail()` and the
`InboundEmail.BinaryAttachment()` constructor signatures), so a test builds
the payload directly — no email needs to be sent.

```apex
@IsTest
private class QuoteIntakeEmailHandlerTest {

    private static Messaging.InboundEmail baseEmail() {
        Messaging.InboundEmail e = new Messaging.InboundEmail();
        e.subject       = 'Quote request: 400 widgets';
        e.fromAddress   = 'buyer@acme.example';
        e.fromName      = 'A Buyer';
        e.toAddresses   = new String[]{ 'quotes@a1b2c3.k1234.apex.salesforce.com' };
        e.plainTextBody = 'Please quote 400 widgets.';
        e.messageId     = '<msg-1@acme.example>';
        e.plainTextBodyIsTruncated = false;
        return e;
    }

    private static Messaging.InboundEnvelope baseEnvelope() {
        Messaging.InboundEnvelope env = new Messaging.InboundEnvelope();
        env.fromAddress = 'buyer@acme.example';
        env.toAddress   = 'quotes@a1b2c3.k1234.apex.salesforce.com';
        return env;
    }

    @IsTest
    static void createsRequestOnFirstEmail() {
        Test.startTest();
        Messaging.InboundEmailResult r =
            new QuoteIntakeEmailHandler().handleInboundEmail(baseEmail(), baseEnvelope());
        Test.stopTest();

        System.Assert.isTrue(r.success, 'First email should be accepted');
        System.Assert.areEqual(
            1,
            [SELECT COUNT() FROM Quote_Request__c WHERE Message_Id__c = '<msg-1@acme.example>'],
            'One request should exist'
        );
    }

    @IsTest
    static void threadsReplyOntoExistingRequest() {
        insert new Quote_Request__c(Message_Id__c = '<msg-1@acme.example>');

        Messaging.InboundEmail reply = baseEmail();
        reply.messageId  = '<msg-2@acme.example>';
        reply.inReplyTo  = '<msg-1@acme.example>';
        reply.references = new String[]{ '<msg-1@acme.example>' };

        Test.startTest();
        Messaging.InboundEmailResult r =
            new QuoteIntakeEmailHandler().handleInboundEmail(reply, baseEnvelope());
        Test.stopTest();

        System.Assert.isTrue(r.success, 'Reply should be accepted');
        System.Assert.areEqual(
            1, [SELECT COUNT() FROM Quote_Request__c],
            'Reply must update the existing request, not create a second one'
        );
    }

    @IsTest
    static void nullAttachmentListDoesNotThrow() {
        Messaging.InboundEmail e = baseEmail();
        e.binaryAttachments = null;   // what the platform sends when none exist

        Test.startTest();
        Messaging.InboundEmailResult r =
            new QuoteIntakeEmailHandler().handleInboundEmail(e, baseEnvelope());
        Test.stopTest();

        System.Assert.isTrue(r.success, 'No attachments is not a failure');
    }

    @IsTest
    static void oversizedAttachmentIsSkippedNotFatal() {
        Messaging.InboundEmail e = baseEmail();
        Messaging.InboundEmail.BinaryAttachment att =
            new Messaging.InboundEmail.BinaryAttachment();
        att.fileName        = 'huge.bin';
        att.mimeTypeSubType = 'application/octet-stream';
        att.body            = Blob.valueOf('x'.repeat(20));
        e.binaryAttachments = new Messaging.InboundEmail.BinaryAttachment[]{ att };

        Test.startTest();
        Messaging.InboundEmailResult r =
            new QuoteIntakeEmailHandler().handleInboundEmail(e, baseEnvelope());
        Test.stopTest();

        System.Assert.isTrue(r.success, 'Attachment policy rejections are not errors');
    }
}
```

## package.xml

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>QuoteIntakeEmailHandler</members>
        <members>QuoteIntakeEmailHandlerTest</members>
        <name>ApexClass</name>
    </types>
    <types>
        <!-- No wildcard support for this type: name every service. -->
        <members>Quote_Intake</members>
        <name>EmailServicesFunction</name>
    </types>
    <version>62.0</version>
</Package>
```

## Retrieve and deploy

```bash
# Retrieve what already exists (name the service; * is not supported)
sf project retrieve start \
    --metadata "EmailServicesFunction:Quote_Intake" \
    --target-org sandbox

# Validate without committing (Apex tests run because ApexClass is in the payload)
sf project deploy start \
    --manifest manifest/package.xml \
    --dry-run \
    --test-level RunSpecifiedTests \
    --tests QuoteIntakeEmailHandlerTest \
    --target-org sandbox

# Deploy for real
sf project deploy start \
    --manifest manifest/package.xml \
    --test-level RunSpecifiedTests \
    --tests QuoteIntakeEmailHandlerTest \
    --target-org sandbox
```

Deploy the `ApexClass` in the same payload as the `EmailServicesFunction`,
or before it. `apexClass` is a required reference; a service pointing at a
class that does not exist in the target org fails the deployment.

## Verification after deploy

The routing address is generated per org, so the deploy alone does not tell
you where to send mail. Query it:

```sql
SELECT Id, DeveloperName, LocalPart, EmailDomainName, IsActive,
       Function.FunctionName, Function.IsActive, Function.ApexClassId,
       RunAsUserId
FROM   EmailServicesAddress
WHERE  Function.FunctionName = 'Quote_Intake'
```

Concatenate `LocalPart` + `@` + `EmailDomainName` to get the address to
send test mail to. Both `IsActive` flags must be `true` or the mail is
handled by `functionInactiveAction` instead of by your Apex.

Setup cross-check: **Setup → Email → Email Services →** _Quote Intake_ →
the **Email Addresses** related list shows the same two addresses with
their generated domains and run-as users.

UNVERIFIED (2026-09-05): the exact Setup breadcrumb wording is quoted from
the Apex Developer Guide's instruction to "enter Email Services in the
Quick Find box, then select Email Services" (apexdev.pdf, Email Services);
the related-list label was not verifiable from the PDFs, and
help.salesforce.com cannot be fetched.
