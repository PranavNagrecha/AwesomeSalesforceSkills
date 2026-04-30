# LLM Anti-Patterns — Attachment to Files Migration

Common mistakes AI coding assistants make when generating or advising on Attachment-to-Files migrations. These patterns help the consuming agent self-check its output before shipping.

## Anti-Pattern 1: Inserting `ContentDocument` Directly

**What the LLM generates:**

```apex
ContentDocument doc = new ContentDocument(Title = a.Name);
insert doc; // intended as parent, then insert a ContentVersion linked to it
```

**Why it happens:** Following the parent-child mental model from other Salesforce object hierarchies.

**Correct pattern:** `ContentDocument` is auto-created when you insert a `ContentVersion` that has no `ContentDocumentId`. Inserting `ContentDocument` directly is not supported and silently misbehaves. The pattern is: insert `ContentVersion` → re-query to get `ContentDocumentId` → insert `ContentDocumentLink`.

## Anti-Pattern 2: Loading All Attachment Bodies in a Single SOQL

**What the LLM generates:**

```apex
List<Attachment> all = [SELECT Id, Name, Body, ParentId FROM Attachment LIMIT 1000];
for (Attachment a : all) { /* migrate */ }
```

**Why it happens:** Default loop-and-insert pattern; LIMIT 1000 looks "safe."

**Correct pattern:** Use Batch Apex with `scope=10` (or 1 for large files). Heap is 6 MB sync / 12 MB async; even 50 average-sized files OOM the transaction. The body field cannot be streamed via SOQL — small batch is the only mechanism.

## Anti-Pattern 3: Skipping the `Source_Attachment_Id__c` Origin Tracking

**What the LLM generates:** A migration script that queries all Attachments, inserts ContentVersions, but stores no link back to the source. On a re-run after partial failure, every successful insert is duplicated.

**Why it happens:** Origin tracking is a discipline pattern, not a Salesforce-mandated field. The model writes the simpler version that "works" on the happy path.

**Correct pattern:** Add a custom field `Source_Attachment_Id__c` (External ID, Unique) on `ContentVersion`. Set it on every insert. Use it in the `start` query to exclude already-migrated rows. Without this, the migration is not re-runnable and any partial failure forces manual cleanup.

## Anti-Pattern 4: Setting `FirstPublishLocationId` AND Inserting Explicit `ContentDocumentLink`

**What the LLM generates:**

```apex
cv.FirstPublishLocationId = a.ParentId; // convenience auto-link
insert cv;
// then also:
ContentDocumentLink cdl = new ContentDocumentLink(
    ContentDocumentId = ..., LinkedEntityId = a.ParentId, ShareType = 'V', Visibility = 'AllUsers'
);
insert cdl;
```

**Why it happens:** Wanting both the convenience and the explicit control.

**Correct pattern:** Pick one. `FirstPublishLocationId` auto-creates a `ContentDocumentLink` with default `ShareType='I'` and `Visibility` based on parent OWD. If you need explicit `ShareType`/`Visibility`, omit `FirstPublishLocationId` and build the link yourself. Otherwise, accept the defaults and don't add the explicit insert. Doing both creates two link rows.

## Anti-Pattern 5: Mapping `Attachment.IsPrivate=true` to `ShareType` Instead of `Visibility`

**What the LLM generates:**

```apex
ContentDocumentLink cdl = new ContentDocumentLink(
    ContentDocumentId = docId,
    LinkedEntityId = parentId,
    ShareType = a.IsPrivate ? 'V' : 'C', // wrong axis
    Visibility = 'AllUsers'
);
```

**Why it happens:** Conflating "private" with "limited share type."

**Correct pattern:** `ShareType` controls capability (View, Collaborate, Inferred); `Visibility` controls audience (`AllUsers`, `InternalUsers`, `SharedUsers`). `IsPrivate=true` maps to `Visibility='InternalUsers'` (file is internal-only, not visible to community/portal users), while `ShareType` should typically be `'V'` for migrated parent links regardless. Mixing the axes results in incorrect access patterns.

## Anti-Pattern 6: Migrating Classic Notes as `ContentVersion` with `.html` Extension

**What the LLM generates:**

```apex
ContentVersion cv = new ContentVersion(
    Title = n.Title,
    PathOnClient = n.Title + '.html',
    VersionData = Blob.valueOf('<p>' + n.Body + '</p>')
);
```

**Why it happens:** Treating Notes as just-another-Attachment.

**Correct pattern:** Use the `ContentNote` sObject, not `ContentVersion` with an HTML extension. `ContentNote` is a special version subtype that surfaces in the Notes related list and is editable inline. A `.html` ContentVersion appears in the Files related list as a generic HTML attachment — wrong UI surface, wrong user expectation. Also: Note body must be HTML-escaped (`Note.Body.escapeHtml4()`) and wrapped in `<p>...</p>`, with `\n` → `<br/>`. Plain-text body produces a single run-on line.

## Anti-Pattern 7: Auto-Cascading Delete in the Same Transaction as Migration

**What the LLM generates:** Batch class that, after successful `ContentVersion` insert, immediately deletes the source `Attachment` in the same `execute` method.

**Why it happens:** Trying to be efficient and avoid a second batch run.

**Correct pattern:** Migration and cleanup are TWO batches separated by manual approval. Reasons: (a) verification queries need time to run against migrated data; (b) cutover plans typically include a "soak" period during which the source must remain readable in case rollback is needed; (c) deleting in the same transaction means a failure between insert-success and delete leaves orphaned ContentDocuments with no source to retry from. Gate cleanup on a separate `Cleanup_Approved__c` flag.

## Anti-Pattern 8: Loading Body in Trigger.new Then Passing Across Async Boundary

**What the LLM generates:**

```apex
trigger AttachmentToFiles on Attachment (after insert) {
    System.enqueueJob(new MirrorQueueable(Trigger.new));
}

public class MirrorQueueable implements Queueable {
    private List<Attachment> records;
    public MirrorQueueable(List<Attachment> recs) { this.records = recs; }
    public void execute(QueueableContext ctx) {
        for (Attachment a : records) {
            ContentVersion cv = new ContentVersion(VersionData = a.Body); // null!
            insert cv;
        }
    }
}
```

**Why it happens:** Assumption that `Trigger.new` carries all fields.

**Correct pattern:** Pass IDs across the async boundary. Re-query in the Queueable with explicit `SELECT Body, ParentId, OwnerId, IsPrivate, Name FROM Attachment WHERE Id IN :ids`. `Body` is a "not loaded" field on `Trigger.new` and any reference to it after the trigger context returns null.

## Anti-Pattern 9: Defaulting `Visibility='AllUsers'` Without Checking Parent OWD

**What the LLM generates:** Migration code that hardcodes `Visibility='AllUsers'` for every link. On a Private-OWD parent (common for Custom Objects holding sensitive data), every insert fails with `FIELD_INTEGRITY_EXCEPTION`.

**Why it happens:** Following the most-permissive default; not thinking about OWD.

**Correct pattern:** Either default to `Visibility='InternalUsers'` (safe) and escalate on parents with public-read OWD, or detect OWD via `EntityDefinition.InternalSharingModel` and assign accordingly. Document the chosen approach in the migration plan.

## Anti-Pattern 10: Treating EmailMessage Attachments the Same as Other Parents

**What the LLM generates:** A blanket migration that processes every `Attachment` regardless of parent type, then deletes all sources.

**Why it happens:** EmailMessage is one parent type among many; the model doesn't distinguish.

**Correct pattern:** EmailMessage attachments may be referenced by inline `cid:` URIs in the email body. Deleting the source Attachment after migration severs those inline references. Treat EmailMessage parents as a separate cohort: either keep both copies, update inline URIs to point at the new ContentDocument, or exclude from cleanup. Default cleanup logic should EXCLUDE `Attachment WHERE Parent.Type = 'EmailMessage'` until an explicit decision is made.
