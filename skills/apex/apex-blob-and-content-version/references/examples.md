# Examples — Apex Blob And ContentVersion

## Example 1: LWC File Picker → Apex → Record-Shared File

**Context:** A Case detail page has a custom LWC that accepts PDFs under 4 MB. On selection the LWC base64-encodes the bytes and posts to an `@AuraEnabled` method. The file must appear in the Case's Files related list.

**Problem:** Developers routinely insert ContentVersion with no link, causing the file to land in the uploader's private library instead of on the Case. Or they set `ContentDocumentId` on the first insert, thinking it creates the link — it doesn't.

**Solution:**

```apex
public with sharing class CaseFileService {
    @AuraEnabled
    public static Id attachFile(Id caseId, String fileName, String base64Body) {
        if (caseId == null || String.isBlank(fileName) || String.isBlank(base64Body)) {
            throw new AuraHandledException('caseId, fileName, base64Body are all required.');
        }
        Blob body = EncodingUtil.base64Decode(stripDataUrlPrefix(base64Body));
        if (body.size() > 4_500_000) {
            throw new AuraHandledException('Use lightning-file-upload for files over 4 MB.');
        }
        ContentVersion cv = new ContentVersion(
            Title = fileName,
            PathOnClient = fileName,
            VersionData = body,
            FirstPublishLocationId = caseId
        );
        insert cv;
        return [SELECT ContentDocumentId FROM ContentVersion WHERE Id = :cv.Id].ContentDocumentId;
    }

    private static String stripDataUrlPrefix(String b64) {
        return b64.startsWith('data:') ? b64.substringAfter(',') : b64;
    }
}
```

**Why it works:** `FirstPublishLocationId = caseId` tells Salesforce to create a ContentDocumentLink with inferred sharing. Stripping any `data:...;base64,` prefix handles browsers that emit FileReader URLs directly. The 4.5 MB guard rejects payloads before they exhaust heap.

---

## Example 2: Scheduled Batch Exports Each Account As A CSV File

**Context:** A nightly Batch exports each Account's child Opportunities as a CSV and attaches it to the Account. The Batch processes 5,000 Accounts per run, each producing a CSV between 50 KB and 2 MB.

**Problem:** Naive implementations build all 5,000 Blobs in heap before a single insert, exhausting heap around Account #800.

**Solution:**

```apex
public with sharing class AccountOppExportBatch
    implements Database.Batchable<SObject>, Database.Stateful {

    public Database.QueryLocator start(Database.BatchableContext bc) {
        return Database.getQueryLocator('SELECT Id, Name FROM Account WHERE IsDeleted = false');
    }

    public void execute(Database.BatchableContext bc, List<Account> scope) {
        List<ContentVersion> versions = new List<ContentVersion>();
        for (Account a : scope) {
            Blob body = Blob.valueOf(AccountCsvBuilder.build(a.Id));
            versions.add(new ContentVersion(
                Title = a.Name + '_Opportunities_' + Date.today().format(),
                PathOnClient = a.Id + '.csv',
                VersionData = body,
                FirstPublishLocationId = a.Id
            ));
            body = null;
        }
        insert versions;
    }

    public void finish(Database.BatchableContext bc) { }
}
```

**Why it works:** Batch processes ~200 Accounts per `execute` by default; heap is reclaimed between executions. Nulling `body` after adding to the list is paranoid but free. The list insert is one DML for the batch, well under the limit.

---

## Example 3: Pull An External Asset And Store It As A File

**Context:** A product image URL lives on an external CDN. When a Product2 is created, a trigger must fetch the image and attach it to the product record.

**Problem:** Triggers cannot perform callouts. Developers sometimes try to bypass this with `@future(callout=true)`, but `@future` has a 12 MB heap limit and the response can overflow. Synchronous callout from the trigger throws `CalloutException`.

**Solution:**

```apex
public with sharing class Product2TriggerHandler {
    public static void afterInsert(List<Product2> newProducts) {
        List<Id> needsImage = new List<Id>();
        for (Product2 p : newProducts) {
            if (String.isNotBlank(p.External_Image_URL__c)) needsImage.add(p.Id);
        }
        if (!needsImage.isEmpty()) {
            System.enqueueJob(new ProductImageFetchQueueable(needsImage));
        }
    }
}

public with sharing class ProductImageFetchQueueable
    implements Queueable, Database.AllowsCallouts {

    private final List<Id> productIds;
    public ProductImageFetchQueueable(List<Id> productIds) { this.productIds = productIds; }

    public void execute(QueueableContext ctx) {
        Product2 first = [SELECT Id, Name, External_Image_URL__c
                          FROM Product2 WHERE Id = :productIds[0] LIMIT 1];
        HttpRequest req = new HttpRequest();
        req.setEndpoint(first.External_Image_URL__c);
        req.setMethod('GET');
        req.setTimeout(60_000);
        HttpResponse res = new Http().send(req);

        if (res.getStatusCode() == 200) {
            insert new ContentVersion(
                Title = first.Name,
                PathOnClient = first.Name + '.jpg',
                VersionData = res.getBodyAsBlob(),
                FirstPublishLocationId = first.Id
            );
        }

        if (productIds.size() > 1) {
            List<Id> remaining = new List<Id>(productIds);
            remaining.remove(0);
            System.enqueueJob(new ProductImageFetchQueueable(remaining));
        }
    }
}
```

**Why it works:** The trigger enqueues, the Queueable performs the callout with `Database.AllowsCallouts`, and the chain processes one product per invocation so heap never carries more than one image at a time.

---

## Anti-Pattern: Storing File Bytes On A Custom Long Text Field

**What practitioners do:**

```apex
CustomObj__c.File_Base64__c = EncodingUtil.base64Encode(fileBlob);
update parent;
```

**What goes wrong:** Long Text Area caps at 131,072 characters — about 95 KB binary after base64. The field fills up, subsequent writes silently truncate, and there is no version history, preview, or mobile support.

**Correct approach:** Use ContentVersion for binary data. Custom text fields are for structured data, not file bytes.

---

## Anti-Pattern: Setting Both `ContentDocumentId` And `FirstPublishLocationId`

**What practitioners do:**

```apex
ContentVersion cv = new ContentVersion(
    Title = 'v2',
    VersionData = body,
    ContentDocumentId = existingDocId,
    FirstPublishLocationId = accountId
);
insert cv;
```

**What goes wrong:** `FirstPublishLocationId` is silently ignored when `ContentDocumentId` is set. The new version is added to the existing document, but no new link to the Account is created.

**Correct approach:** Insert a separate `ContentDocumentLink` for the Account after the version insert.
