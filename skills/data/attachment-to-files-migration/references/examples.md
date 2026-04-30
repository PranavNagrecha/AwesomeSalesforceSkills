# Examples — Attachment to Files Migration

## Example 1: Idempotent Batch Apex (Pattern 1 in SKILL.md)

```apex
public with sharing class AttachmentToFilesBatch
        implements Database.Batchable<sObject>, Database.Stateful {

    public Integer successCount = 0;
    public Integer failureCount = 0;

    public Database.QueryLocator start(Database.BatchableContext bc) {
        // Re-runnable: skip Attachments that already have a ContentVersion
        Set<Id> migratedSourceIds = new Set<Id>();
        for (ContentVersion cv : [
            SELECT Source_Attachment_Id__c
            FROM ContentVersion
            WHERE Source_Attachment_Id__c != null
        ]) {
            migratedSourceIds.add((Id) cv.Source_Attachment_Id__c);
        }
        return Database.getQueryLocator([
            SELECT Id, ParentId, OwnerId, Name, Body, BodyLength, IsPrivate, Description
            FROM Attachment
            WHERE Id NOT IN :migratedSourceIds
        ]);
    }

    public void execute(Database.BatchableContext bc, List<Attachment> scope) {
        // Step 1: insert ContentVersions
        List<ContentVersion> versions = new List<ContentVersion>();
        Map<Integer, Attachment> indexToAttachment = new Map<Integer, Attachment>();
        Integer i = 0;
        for (Attachment a : scope) {
            ContentVersion cv = new ContentVersion(
                Title = a.Name,
                PathOnClient = a.Name,
                VersionData = a.Body,
                OwnerId = a.OwnerId,
                Description = a.Description,
                Source_Attachment_Id__c = a.Id
            );
            versions.add(cv);
            indexToAttachment.put(i, a);
            i++;
        }
        Database.SaveResult[] versionResults = Database.insert(versions, false);

        // Step 2: re-query ContentDocumentId for successful inserts
        Set<Id> insertedVersionIds = new Set<Id>();
        for (Database.SaveResult sr : versionResults) {
            if (sr.isSuccess()) insertedVersionIds.add(sr.getId());
        }
        Map<Id, ContentVersion> versionToDoc = new Map<Id, ContentVersion>(
            [SELECT Id, ContentDocumentId, Source_Attachment_Id__c
             FROM ContentVersion WHERE Id IN :insertedVersionIds]
        );

        // Step 3: build ContentDocumentLink rows
        List<ContentDocumentLink> links = new List<ContentDocumentLink>();
        List<Migration_Log__c> logs = new List<Migration_Log__c>();
        for (ContentVersion cv : versionToDoc.values()) {
            // Find the source Attachment to get parent and IsPrivate
            Attachment src = null;
            for (Attachment a : scope) {
                if (a.Id == cv.Source_Attachment_Id__c) { src = a; break; }
            }
            if (src == null) continue;
            ContentDocumentLink cdl = new ContentDocumentLink(
                ContentDocumentId = cv.ContentDocumentId,
                LinkedEntityId = src.ParentId,
                ShareType = 'V',
                Visibility = src.IsPrivate ? 'InternalUsers' : 'AllUsers'
            );
            links.add(cdl);
            logs.add(new Migration_Log__c(
                Source_Attachment_Id__c = src.Id,
                Status__c = 'Success',
                ContentDocument_Id__c = cv.ContentDocumentId
            ));
            successCount++;
        }
        Database.insert(links, false);

        // Log version-level failures
        for (Integer j = 0; j < versionResults.size(); j++) {
            if (!versionResults[j].isSuccess()) {
                Attachment src = indexToAttachment.get(j);
                logs.add(new Migration_Log__c(
                    Source_Attachment_Id__c = src.Id,
                    Status__c = 'Failure',
                    Error__c = versionResults[j].getErrors()[0].getMessage().left(255)
                ));
                failureCount++;
            }
        }
        if (!logs.isEmpty()) Database.insert(logs, false);
    }

    public void finish(Database.BatchableContext bc) {
        System.debug('AttachmentToFilesBatch finished: ' + successCount + ' success, ' + failureCount + ' failed');
        // Optionally chain to next batch (e.g., NoteToContentNoteBatch) here
    }
}
```

**Run:** `Database.executeBatch(new AttachmentToFilesBatch(), 10);` — scope=10 keeps heap pressure low.

**Re-run after partial failure:** Just re-execute. The `start` query excludes already-migrated source IDs.

---

## Example 2: Classic Note → ContentNote Conversion

```apex
public with sharing class NoteToContentNoteBatch
        implements Database.Batchable<sObject> {

    public Database.QueryLocator start(Database.BatchableContext bc) {
        return Database.getQueryLocator([
            SELECT Id, Title, Body, ParentId, OwnerId, IsPrivate
            FROM Note
            WHERE Id NOT IN (SELECT Source_Attachment_Id__c FROM ContentVersion WHERE FileType = 'SNOTE')
        ]);
    }

    public void execute(Database.BatchableContext bc, List<Note> scope) {
        List<ContentNote> notes = new List<ContentNote>();
        Map<Integer, Note> indexToNote = new Map<Integer, Note>();
        Integer i = 0;
        for (Note n : scope) {
            String htmlBody = '<p>' + n.Body.escapeHtml4().replaceAll('\\n', '<br/>') + '</p>';
            ContentNote cn = new ContentNote(
                Title = n.Title,
                Content = Blob.valueOf(htmlBody),
                OwnerId = n.OwnerId
            );
            notes.add(cn);
            indexToNote.put(i, n);
            i++;
        }
        Database.SaveResult[] noteResults = Database.insert(notes, false);

        // Link each ContentNote to the original parent
        Set<Id> insertedNoteIds = new Set<Id>();
        for (Database.SaveResult sr : noteResults) {
            if (sr.isSuccess()) insertedNoteIds.add(sr.getId());
        }
        Map<Id, ContentVersion> versions = new Map<Id, ContentVersion>(
            [SELECT Id, ContentDocumentId FROM ContentVersion
             WHERE Id IN (SELECT LatestPublishedVersionId FROM ContentDocument
                          WHERE Id IN (SELECT ContentDocumentId FROM ContentNote WHERE Id IN :insertedNoteIds))]
        );
        // ContentNote.Id IS the ContentDocument.Id — directly usable
        List<ContentDocumentLink> links = new List<ContentDocumentLink>();
        for (Integer j = 0; j < noteResults.size(); j++) {
            if (!noteResults[j].isSuccess()) continue;
            Note src = indexToNote.get(j);
            links.add(new ContentDocumentLink(
                ContentDocumentId = noteResults[j].getId(),
                LinkedEntityId = src.ParentId,
                ShareType = 'V',
                Visibility = src.IsPrivate ? 'InternalUsers' : 'AllUsers'
            ));
        }
        Database.insert(links, false);
    }

    public void finish(Database.BatchableContext bc) {}
}
```

**Critical detail:** `ContentNote.Content` must be HTML wrapped in `<p>...</p>`, escaped, with newlines converted. Plain text gets rendered as a single line.

---

## Example 3: Live Cutover Trigger

```apex
trigger AttachmentToFilesTrigger on Attachment (after insert) {
    System.enqueueJob(new MirrorAttachmentToFilesQueueable(Trigger.new));
}

public class MirrorAttachmentToFilesQueueable implements Queueable {
    private List<Id> attachmentIds;

    public MirrorAttachmentToFilesQueueable(List<Attachment> atts) {
        this.attachmentIds = new List<Id>();
        for (Attachment a : atts) this.attachmentIds.add(a.Id);
    }

    public void execute(QueueableContext ctx) {
        // Reload with body (Trigger.new doesn't have body in async)
        List<Attachment> atts = [
            SELECT Id, ParentId, OwnerId, Name, Body, IsPrivate, Description
            FROM Attachment WHERE Id IN :attachmentIds
        ];

        // Insert ContentVersions
        List<ContentVersion> versions = new List<ContentVersion>();
        for (Attachment a : atts) {
            versions.add(new ContentVersion(
                Title = a.Name,
                PathOnClient = a.Name,
                VersionData = a.Body,
                OwnerId = a.OwnerId,
                Description = a.Description,
                Source_Attachment_Id__c = a.Id
            ));
        }
        Database.insert(versions, false);

        // Re-query for ContentDocumentId, then build ContentDocumentLinks
        Map<Id, ContentVersion> byId = new Map<Id, ContentVersion>(
            [SELECT Id, ContentDocumentId, Source_Attachment_Id__c
             FROM ContentVersion WHERE Id IN :versions]
        );
        Map<Id, Attachment> srcById = new Map<Id, Attachment>(atts);
        List<ContentDocumentLink> links = new List<ContentDocumentLink>();
        for (ContentVersion cv : byId.values()) {
            Attachment src = srcById.get((Id) cv.Source_Attachment_Id__c);
            if (src == null) continue;
            links.add(new ContentDocumentLink(
                ContentDocumentId = cv.ContentDocumentId,
                LinkedEntityId = src.ParentId,
                ShareType = 'V',
                Visibility = src.IsPrivate ? 'InternalUsers' : 'AllUsers'
            ));
        }
        Database.insert(links, false);
    }
}
```

**Why the Queueable:** Inserting `ContentVersion` from the same transaction as the `Attachment` insert risks "MIXED_DML_OPERATION" errors when the parent operation also touches setup objects. Queueable defers to a clean transaction context.

---

## Example 4: Verification Queries

```sql
-- Pending Attachments not yet migrated
SELECT COUNT(Id)
FROM Attachment
WHERE Id NOT IN (SELECT Source_Attachment_Id__c FROM ContentVersion)

-- Reconciliation by parent type
SELECT Parent.Type, COUNT(Id) total
FROM Attachment GROUP BY Parent.Type

SELECT LinkedEntity.Type, COUNT(Id) total
FROM ContentDocumentLink
WHERE ContentDocumentId IN (SELECT ContentDocumentId FROM ContentVersion WHERE Source_Attachment_Id__c != null)
GROUP BY LinkedEntity.Type

-- Failed migrations from log
SELECT Source_Attachment_Id__c, Error__c, COUNT(Id)
FROM Migration_Log__c
WHERE Status__c = 'Failure'
GROUP BY Source_Attachment_Id__c, Error__c
ORDER BY COUNT(Id) DESC
```

---

## Example 5: Cleanup Batch (Gated by Approval Flag)

```apex
public with sharing class AttachmentCleanupBatch
        implements Database.Batchable<sObject> {

    public Database.QueryLocator start(Database.BatchableContext bc) {
        return Database.getQueryLocator([
            SELECT Id FROM Attachment
            WHERE Id IN (SELECT Source_Attachment_Id__c FROM ContentVersion WHERE Source_Attachment_Id__c != null)
            AND Id IN (SELECT Source_Attachment_Id__c FROM Migration_Log__c WHERE Status__c = 'Success' AND Cleanup_Approved__c = true)
        ]);
    }

    public void execute(Database.BatchableContext bc, List<Attachment> scope) {
        Database.delete(scope, false);
    }

    public void finish(Database.BatchableContext bc) {}
}
```

**Run** only after manual sign-off updates `Cleanup_Approved__c = true` on the Migration_Log__c rows. Never auto-cascade from successful migration to cleanup.
