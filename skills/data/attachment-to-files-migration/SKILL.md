---
name: attachment-to-files-migration
description: "Migrating Classic Notes & Attachments to Salesforce Files (ContentDocument / ContentVersion / ContentDocumentLink): bulk extraction, owner and parent preservation, sharing translation, idempotent re-runs, and post-migration cleanup. Triggers: 'attachments to files', 'notes and attachments migration', 'ContentDocument from Attachment', 'enable Files for Salesforce'. NOT for general file storage strategy (use data/file-and-document-integration) or for ContentVersion API patterns in new code (use integration/file-and-document-integration)."
category: data
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Security
  - Reliability
triggers:
  - "How do I migrate Classic Attachments to Salesforce Files?"
  - "Convert Notes (Note sObject) to ContentNote"
  - "Preserve owner and parent record on migrated files"
  - "Bulk migrate attachments without hitting heap or DML limits"
  - "Recover from a partial Attachment-to-Files migration"
tags:
  - attachments
  - notes
  - files
  - contentdocument
  - contentversion
  - contentdocumentlink
  - migration
inputs:
  - "Source object scope (which parent objects have Attachments / Notes to migrate)"
  - "Volume estimate (count and total bytes of Attachment records)"
  - "Whether sharing on the original Attachment was OWD-private, parent-inherited, or explicitly granted"
  - "Migration window: live cutover vs phased background batch"
  - "Whether the org has Salesforce Files Sync, Content Libraries, or restrictive Content Pack policies in play"
outputs:
  - "Batch Apex (or Bulk API 2.0 job) that converts Attachment → ContentVersion → ContentDocumentLink"
  - "Idempotent reconciliation report (Attachments processed, ContentDocuments created, failures by reason)"
  - "Cleanup script that deletes original Attachments only after verification"
  - "Updated reports / list views / LWC references to use ContentDocument relationships"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-29
---

# Attachment to Files Migration

This skill activates when a practitioner needs to convert legacy Classic `Attachment` (and `Note`) records to modern Salesforce Files (`ContentDocument` / `ContentVersion` / `ContentDocumentLink`), preserving parent linkage, owner, sharing, and an audit trail through a re-runnable, idempotent process.

---

## Before Starting

Gather this context before working on anything in this domain:

- Inventory the volume: `SELECT COUNT(Id), SUM(BodyLength) FROM Attachment` and the same on `Note`. Sub-100K and < 5GB total can be done with Batch Apex; larger requires Bulk API 2.0 + external orchestration to avoid heap pressure.
- Confirm "Notes" are Classic Notes (`Note` sObject) vs Enhanced Notes (`ContentNote`, already a Files record). Only Classic `Note` records need migrating; Enhanced Notes are already Files.
- Inventory parent-object distribution: `SELECT ParentId.Type, COUNT(Id) FROM Attachment GROUP BY ParentId.Type`. Some parents (Email, Task) have idiosyncratic Files behavior — Email attachments may already be linked via `EmailMessage` instead.
- Confirm the org has Files enabled and that `ContentDocumentLink` has an OWD permitting users to receive shared files. If OWD is private and the migration runs as an integration user, all migrated files will be invisible to the original owners until ContentDocumentLink rows are created with the correct visibility.

---

## Core Concepts

### 1. Object Model Mapping

| Classic Object | Files Equivalent | Notes |
|---|---|---|
| `Attachment` | `ContentVersion` (one row per version) + `ContentDocument` (parent envelope) + `ContentDocumentLink` (parent linkage and sharing) | A new `ContentDocument` is implicitly created when you insert a `ContentVersion` with no `ContentDocumentId` |
| `Note` (Classic) | `ContentNote` (special `ContentVersion` subtype) | Body is HTML in `ContentNote`; Classic Notes are plain text — escape & wrap in `<p>` tags |
| `Attachment.ParentId` | `ContentDocumentLink.LinkedEntityId` | Links the file to the original parent record |
| `Attachment.OwnerId` | `ContentVersion.OwnerId` (and indirectly `ContentDocument.OwnerId`) | Owner must exist and be active at insert time, otherwise the row fails |
| `Attachment.IsPrivate` | `ContentDocumentLink.Visibility = 'InternalUsers'` (vs `AllUsers`) | Private attachments map to internal-user visibility, NOT to the same record-level private flag |

### 2. The Three-Object Insert Sequence

Every migrated attachment requires three inserts in the right order:

| Step | sObject | Required fields | Purpose |
|---|---|---|---|
| 1 | `ContentVersion` | `Title`, `PathOnClient`, `VersionData`, `OwnerId`, `FirstPublishLocationId` (optional) | Creates the file content; auto-creates a `ContentDocument` |
| 2 | (auto) Query `ContentDocumentId` from inserted `ContentVersion` | n/a | Capture the parent envelope ID |
| 3 | `ContentDocumentLink` | `ContentDocumentId`, `LinkedEntityId`, `ShareType`, `Visibility` | Links the file to the original parent record and sets sharing |

If you set `FirstPublishLocationId` on the `ContentVersion`, Salesforce auto-creates the `ContentDocumentLink` to that parent — but you still need explicit links for any additional parents and to control `Visibility` precisely.

### 3. Sharing Translation

Classic Attachment sharing was simple: inherits parent record sharing, plus an `IsPrivate` flag that hid it from everyone except the owner and admins. Files sharing is multi-dimensional:

| Dimension | Values | Migration default |
|---|---|---|
| `ContentDocumentLink.ShareType` | `V` (Viewer), `C` (Collaborator), `I` (Inferred from parent) | `V` for migrated parent links |
| `ContentDocumentLink.Visibility` | `AllUsers`, `InternalUsers`, `SharedUsers` | `AllUsers` if `Attachment.IsPrivate=false`; `InternalUsers` if private |
| `ContentDocument.SharingPrivacy` | `N` (None), `P` (Private on Record) | `P` matches `Attachment.IsPrivate=true` |

`ShareType` controls what the linked user can do; `Visibility` controls who in the parent record's audience sees it. They are independent. Setting only one results in surprising access patterns.

### 4. Heap and DML Considerations at Volume

Attachment bodies live in `Attachment.Body` (a Blob). When you query `SELECT Body FROM Attachment LIMIT N`, every body is loaded into Apex heap (6 MB default). At an average 500 KB per attachment, you can hold ~10 attachments in heap simultaneously before risk. Migration jobs MUST stream — query a small batch, insert, release references, repeat — never bulk-load the full body set.

| Approach | Records per chunk | Where it fits |
|---|---|---|
| Batch Apex with `scope=10` | 10 | Standard for ~100K attachments, average <2MB each |
| Batch Apex with `scope=1` | 1 | Required when individual files exceed 5MB |
| Bulk API 2.0 from external | configurable | Required for >500K attachments or >10GB total |
| Queueable chain | 1–10 per execution | Required when callouts to external storage are part of the chain |

---

## Common Patterns

### Pattern 1: Idempotent Batch with Origin Tracking

**When to use:** Most migrations. Volume 10K–500K Attachments, runs in-org without external dependencies.

**How it works:**
1. Add a custom field `Source_Attachment_Id__c` (External ID, Unique) to a custom object or to `ContentVersion` itself if your org allows custom fields on it (it does).
2. Batch Apex scope = 10. Query `SELECT Id, ParentId, OwnerId, Name, Body, BodyLength, IsPrivate FROM Attachment WHERE Id NOT IN (SELECT Source_Attachment_Id__c FROM ContentVersion)`.
3. For each row: build `ContentVersion`, set `Source_Attachment_Id__c` = original `Attachment.Id`, insert.
4. Re-query to get `ContentDocumentId` from the inserted versions.
5. Build `ContentDocumentLink` rows for each parent; insert.
6. Log per-Attachment outcome to a custom `Migration_Log__c` object: success / failure / reason.

**Why not the alternative:** Without origin tracking, a re-run after a partial failure duplicates files. With it, the `WHERE NOT IN` clause in step 2 makes the job re-runnable safely.

### Pattern 2: Notes (Classic) → ContentNote

**When to use:** The org used Classic Notes (`Note` sObject) and is enabling Enhanced Notes / Files-only.

**How it works:**
1. Query `SELECT Id, Title, Body, ParentId, OwnerId FROM Note`.
2. For each, build a `ContentNote`: `Title = Note.Title`, `Content = Blob.valueOf('<p>' + Note.Body.escapeHtml4() + '</p>')`. Replace newlines with `<br/>`.
3. Insert the `ContentNote`.
4. Insert `ContentDocumentLink` with `LinkedEntityId = Note.ParentId`, `ShareType = 'V'`, `Visibility = 'AllUsers'`.

**Why not the alternative:** Inserting Notes as `ContentVersion` with `Title.html` extension does not produce a "Note" — it produces an HTML file. Users browsing the related list won't see it as a Note. `ContentNote` is the correct sObject.

### Pattern 3: Phased Live Cutover

**When to use:** Org cannot tolerate downtime; migration must run in production while users continue creating Attachments.

**How it works:**
1. Deploy a Trigger on `Attachment` that, on `after insert`, copies the new Attachment to Files immediately (via Queueable to avoid synchronous DML on the same operation).
2. Run the bulk historical migration in the background. Both the trigger and the batch use the `Source_Attachment_Id__c` deduplication so a record migrated by the trigger isn't double-processed.
3. Once the batch finishes, run a verification report: `SELECT COUNT(Id) FROM Attachment WHERE Id NOT IN (SELECT Source_Attachment_Id__c FROM ContentVersion)`. Expect zero.
4. Disable Attachment creation org-wide via permission set removal of `Modify All Data`-equivalent on Attachment, or via a validation rule that fails on insert with a "use Files" message.
5. After a soak window, archive (export + delete) original Attachments.

**Why not the alternative:** A pure batch migration leaves a window where users are still creating Attachments. The trigger closes the window without waiting for the batch to finish.

### Pattern 4: Selective Migration with Filter Predicate

**When to use:** Only a subset of Attachments are needed in Files (e.g., only those on Cases from the last 3 years).

**How it works:**
1. Identify the predicate (e.g., `WHERE Parent.CreatedDate > LAST_N_YEARS:3 AND Parent.Type = 'Case'`).
2. Run the standard batch but constrain the `start()` query to the predicate.
3. Add a `Migration_Reason__c` field on `Migration_Log__c` so excluded Attachments are logged with the reason.
4. Decide cleanup separately: out-of-scope Attachments may be retained as-is, archived to external storage, or deleted after a separate sign-off.

**Why not the alternative:** Migrating everything "to be safe" inflates Files storage by orders of magnitude and may push the org over its allocation. Files storage is pricier per MB than Attachment storage; a deliberate predicate is cost discipline.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| <100K Attachments, <5GB total, low-traffic org | Batch Apex with `scope=10` | Native, runnable in-org, idempotent if source-tracking is added |
| >500K Attachments OR >10GB | Bulk API 2.0 from external script | Avoids heap pressure and Apex CPU limits at scale |
| Production org with active Attachment creation | Trigger + Batch combo (Pattern 3) | Closes the live-data window |
| Need selective subset | Predicate-driven batch (Pattern 4) | Controls Files storage cost and migration scope |
| Classic Notes (`Note` sObject) present | Separate `ContentNote` job (Pattern 2) | Notes need different sObject; do NOT mix into Attachment batch |
| Email attachments (parent is `EmailMessage`) | Verify if already linked via `EmailMessageRelation` | Some email attachments are stored in Files already |
| Cleanup of source Attachments | Separate post-verification batch with audit log | Never delete in the same transaction as create — reconcile first |
| Migration must preserve `CreatedDate` | Set `Audit Field Customization` permission and write to `CreatedDate` on `ContentVersion` | Default is "now"; explicit field write needs the special perm |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Profile the source.** Run COUNT/SUM queries on `Attachment` and `Note`, group by parent type and by size bucket (<1MB, 1–5MB, 5–25MB, >25MB). Confirm Files is enabled and check the org's Files storage allocation.
2. **Add `Source_Attachment_Id__c` (External ID, Unique) to `ContentVersion`.** This single field unlocks idempotent re-runs and reconciliation.
3. **Build the batch class.** Use `scope=10` as default; lower it to `scope=1` if any single file may exceed ~5MB. Implement `start` (query Attachments not yet migrated), `execute` (build ContentVersion + ContentDocumentLink rows, insert with `Database.insert(rows, false)` for partial-success), `finish` (chain to next batch or write summary log).
4. **Translate sharing.** For each `Attachment.IsPrivate=true`, set `ContentDocumentLink.Visibility='InternalUsers'`. For `false`, use `'AllUsers'`. Choose `ShareType='V'` for parent-record links.
5. **Run on a sandbox copy first.** Migrate a representative slice (10K records spanning all parent types). Verify file accessibility from each parent record's UI, owner correctness, and sharing visibility against expected users.
6. **Cutover in production.** Deploy the Attachment-after-insert trigger. Start the batch. Monitor `Migration_Log__c` for failures and re-run the batch to retry — the dedup key makes it safe.
7. **Verify and clean up.** After zero-pending count is confirmed, run a separate cleanup batch that deletes original Attachments in chunks of 200, gated by a flag (`Cleanup_Approved__c`). Keep the `Migration_Log__c` for audit.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] `Source_Attachment_Id__c` (External ID, Unique) is on `ContentVersion` and populated for every migrated row
- [ ] Batch `scope` accounts for the largest individual file size — no heap-exceeded errors in the test run
- [ ] `Database.insert(rows, false)` is used for partial-success; failures are logged with reason, not lost
- [ ] `ContentDocumentLink.Visibility` correctly maps `Attachment.IsPrivate` (`InternalUsers` vs `AllUsers`)
- [ ] Owner (`OwnerId`) matches the original Attachment owner; orphaned-owner cases (inactive user) are handled with a documented fallback
- [ ] Migration_Log__c rows exist for every Attachment with success/failure outcome
- [ ] Verification count: `SELECT COUNT(Id) FROM Attachment WHERE Id NOT IN (SELECT Source_Attachment_Id__c FROM ContentVersion)` = 0 (or matches the documented exclusion predicate)
- [ ] Cleanup of source Attachments is GATED on a separate approval flag — not auto-deleted in the same transaction
- [ ] Reports, list views, and LWC components that referenced `Attachments` relationships have been updated to `ContentDocumentLinks` or `AttachedContentDocuments`
- [ ] If the org used Classic Notes, a separate ContentNote migration job is included in the cutover plan

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **`ContentDocument` is created implicitly by `ContentVersion` insert — there is no direct insert path.** Inserting a `ContentDocument` record directly is not supported. The pattern is: insert `ContentVersion` (which auto-creates a `ContentDocument` parent), re-query the inserted `ContentVersion` to read its `ContentDocumentId`, then build the `ContentDocumentLink`. Trying to model the migration with a `ContentDocument` insert step fails with no clear error.

2. **`Attachment.Body` query loads the full blob into heap.** A query like `SELECT Body FROM Attachment WHERE ...` materializes every blob in the result set. With heap limited to 6 MB (12 MB async), even a small batch of large files OOMs the transaction. Always set a small `scope` and treat each row's body as a one-time stream — assign to `ContentVersion.VersionData` immediately and let it go out of scope.

3. **Setting `FirstPublishLocationId` AND inserting an explicit `ContentDocumentLink` for the same parent creates two links.** The convenience parameter `FirstPublishLocationId` on `ContentVersion` auto-creates the `ContentDocumentLink`. If your migration also inserts an explicit `ContentDocumentLink` to the same parent for control over `ShareType` / `Visibility`, you get two link rows. Pick one approach per parent and stick to it.

4. **`Visibility='AllUsers'` is rejected if the parent object's OWD is private.** Setting `ContentDocumentLink.Visibility='AllUsers'` on a link whose `LinkedEntityId` parent has private OWD throws a `FIELD_INTEGRITY_EXCEPTION`. Either change the OWD before migrating (rare) or downgrade visibility to `InternalUsers` for those parents and document the difference.

5. **Owner of an inactive user fails silently in `ContentDocumentLink` insert.** If `Attachment.OwnerId` points to a deactivated user, the `ContentVersion` insert with that `OwnerId` succeeds (Salesforce permits inactive owners on Files), but downstream logic that expects "owner can see file" breaks. Decide a fallback: (a) reassign ownership to a designated migration user, (b) preserve the inactive owner and accept the visibility consequence, or (c) skip and log. There is no platform default.

6. **`CreatedDate` and `CreatedById` are not preserved without "Audit Field Customization" permission.** `ContentVersion.CreatedDate` defaults to the migration timestamp; original `Attachment.CreatedDate` is lost unless the migration user has the "Set Audit Fields upon Record Creation" permission AND your code explicitly sets `CreatedDate` and `CreatedById`. Some migrations decide audit history isn't worth preserving; others must preserve it for compliance — confirm before starting.

7. **ContentNote body is HTML — Classic Note body is plain text.** Naively setting `ContentNote.Content = Blob.valueOf(Note.Body)` produces unrendered text instead of paragraphs. The body must be wrapped (`<p>...</p>`), HTML-escaped (`Note.Body.escapeHtml4()`), and have newlines converted (`replaceAll('\\n', '<br/>')`). Otherwise the migrated Note appears as a single line of run-on text.

8. **Files sharing has both `ShareType` and `Visibility` — they are not synonyms.** `ShareType` controls what the audience can do (`V`iew, `C`ollaborate, `I`nferred). `Visibility` controls who in the parent's audience sees the file (`AllUsers`, `InternalUsers`, `SharedUsers`). Setting `ShareType='V'` with `Visibility='SharedUsers'` is meaningless — `SharedUsers` requires no automatic propagation, so no one will see it. Migrate with explicit choices on both axes.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Batch Apex class (e.g., `AttachmentToFilesMigration.cls`) | Idempotent migration job with origin tracking and partial-success logging |
| `Source_Attachment_Id__c` field on `ContentVersion` | External ID, Unique — enables re-runs and reconciliation |
| `Migration_Log__c` custom object | Per-Attachment outcome log: success, failure with reason, file size, parent type |
| Cleanup batch class | Deletes source Attachments after a separate approval gate |
| Verification SOQL pack | Reconciliation queries for confirming zero-pending and matching counts by parent type |
| Updated downstream references | Reports, list views, LWC `getRelatedListRecords` calls switched from Attachment to ContentDocumentLink |

---

## Related Skills

- `data/file-and-document-integration` — Use when designing new file-storage architecture (post-migration), not the migration itself
- `integration/file-and-document-integration` — Use when ingesting files from external systems into Salesforce Files
- `apex/batch-apex-patterns` — Use when designing the batch class structure (scope, state, finish-chaining)
- `data/data-archival-strategies` — Use when the migration plan includes archival of source Attachments to external storage
- `security/sharing-and-visibility` — Use when the OWD on parent objects must be reviewed before setting `ContentDocumentLink.Visibility`
