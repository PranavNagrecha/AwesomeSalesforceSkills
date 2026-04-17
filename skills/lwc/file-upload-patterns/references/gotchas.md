# Gotchas — LWC File Upload Patterns

## Gotcha 1: Heap exceeded

**What happens:** Error at 12MB file.

**When it occurs:** Single Apex call.

**How to avoid:** Chunk.


---

## Gotcha 2: No MIME validation

**What happens:** User uploads .exe renamed .pdf.

**When it occurs:** Extension-only check.

**How to avoid:** Server-side magic-byte validation.


---

## Gotcha 3: Missing ContentDocumentLink

**What happens:** File uploaded but not visible on record.

**When it occurs:** Custom flow forgot link.

**How to avoid:** Insert ContentDocumentLink with LinkedEntityId.

