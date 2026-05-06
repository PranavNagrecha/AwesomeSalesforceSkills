# LLM Anti-Patterns — Salesforce Files Architecture

Mistakes AI assistants commonly make when generating Salesforce
Files Apex / SOQL.

---

## Anti-Pattern 1: Recommending `Attachment` for new development

**What the LLM generates.**

```apex
Attachment a = new Attachment(
    ParentId = caseId,
    Name = 'contract.pdf',
    Body = body
);
insert a;
```

**Why it happens.** `Attachment` is older training data with simpler
shape; the LLM defaults to it.

**Correct pattern.** Use `ContentVersion` + `ContentDocumentLink`.
`Attachment` is deprecated for new development; new orgs should
not introduce it.

**Detection hint.** Any new Apex creating `Attachment` records,
unless explicitly migrating legacy data.

---

## Anti-Pattern 2: Inserting `ContentDocument` directly

**What the LLM generates.**

```apex
ContentDocument cd = new ContentDocument(Title = 'doc.pdf');
insert cd;  // Wrong
```

**Why it happens.** The LLM picks the most "obvious" parent object
to insert.

**Correct pattern.** Insert `ContentVersion` (with the binary in
`VersionData`); the platform creates the `ContentDocument`. Do not
insert `ContentDocument` directly.

**Detection hint.** Any direct `insert` against `ContentDocument`.

---

## Anti-Pattern 3: SOQL on `ContentDocument.ParentId`

**What the LLM generates.**

```apex
SELECT Id FROM ContentDocument WHERE ParentId = :recordId
```

**Why it happens.** Mirrors `Attachment.ParentId` intuition.

**Correct pattern.** Query `ContentDocumentLink WHERE
LinkedEntityId = :recordId`. There is no `ParentId` on
`ContentDocument`.

**Detection hint.** Any SOQL referencing `ContentDocument.ParentId`.

---

## Anti-Pattern 4: Forgetting `IsLatest = true` when listing files

**What the LLM generates.**

```apex
SELECT Id, Title FROM ContentVersion WHERE ContentDocumentId IN :ids
```

**Why it happens.** The LLM treats versions as identical to single
files.

**Correct pattern.** Add `AND IsLatest = true` for the current-
version view. Omit it deliberately for version history.

**Detection hint.** Any `ContentVersion` enumeration without an
`IsLatest` filter.

---

## Anti-Pattern 5: Bulk loading file blobs without heap consideration

**What the LLM generates.**

```apex
List<ContentVersion> all = [
    SELECT Id, VersionData FROM ContentVersion WHERE IsLatest = true
];
```

**Why it happens.** The LLM does not surface that `VersionData`
loads the full blob into heap.

**Correct pattern.** For bulk operations, batch with small chunks
(1–5 records per execution); for sync use cases, query
`ContentSize` first and process selectively. Apex heap limits are
12 MB sync / 36 MB async.

**Detection hint.** Any `SELECT ... VersionData ...` without a
`LIMIT` or batch context.

---

## Anti-Pattern 6: Omitting `Visibility` on `ContentDocumentLink` insert

**What the LLM generates.**

```apex
ContentDocumentLink cdl = new ContentDocumentLink(
    ContentDocumentId = docId,
    LinkedEntityId = recordId,
    ShareType = 'V'
);
insert cdl;
```

**Why it happens.** `Visibility` is not always required in default
contexts; the LLM omits it.

**Correct pattern.** Set `Visibility` explicitly. `'AllUsers'`
exposes to community / portal users; `'InternalUsers'` restricts to
internal. The default behavior in mixed-audience orgs is risky.

**Detection hint.** Any `ContentDocumentLink` insert without
`Visibility`.

---

## Anti-Pattern 7: Using `Document` object for record-attached files

**What the LLM generates.**

```apex
Document d = new Document(
    FolderId = ..., Body = ..., Name = 'attached.pdf'
);
insert d;
```

**Why it happens.** Confusion between `Document` (Classic-only,
folder-based) and `ContentDocument` (Files).

**Correct pattern.** `Document` is Classic-only and not suitable
for record-attached files in Lightning Experience. Use
`ContentVersion` + `ContentDocumentLink`.

**Detection hint.** Any `Document` (not `ContentDocument`) DML in
modern orgs.
