# LLM Anti-Patterns — Analytics Data Preparation (XMD)

Common mistakes AI coding assistants make when generating or advising on CRM Analytics XMD metadata.

---

## Anti-Pattern 1: Using SOQL to Access WaveXmd

**What the LLM generates:** `SELECT Id, Name FROM WaveXmd WHERE DatasetId = '{id}'`

**Why it happens:** LLMs apply standard Salesforce SOQL patterns to analytics metadata objects.

**The correct pattern:** WaveXmd is not SOQL-accessible. Use `GET /wave/datasets/{id}/xmds/main`.

**Detection hint:** Any SOQL query against `WaveXmd` fails with INVALID_TYPE.

---

## Anti-Pattern 2: Attempting to Modify System XMD

**What the LLM generates:** Instructions to PATCH `xmds/system` to change field labels.

**Why it happens:** LLMs assume the "system" layer is the base that can be overridden.

**The correct pattern:** System XMD is immutable. Always PATCH `xmds/main`.

**Detection hint:** Any write operation targeting `xmds/system` returns HTTP 400.

---

## Anti-Pattern 3: Using Full Replacement (PUT) Instead of Additive Merge (PATCH)

**What the LLM generates:** HTTP PUT to update XMD, or a PATCH payload that replaces all dimensions/measures.

**Why it happens:** Many REST APIs use PUT for full replacement.

**The correct pattern:** XMD PATCH is additive-merge. Include only changed properties. Sending a full replace payload overwrites all existing customizations.

**Detection hint:** PATCH payloads should contain only the fields being changed, not the entire XMD document.

---

## Anti-Pattern 4: Treating External CSV as Self-Refreshing

**What the LLM generates:** "Upload the CSV once and the recipe will always use the latest version."

**Why it happens:** LLMs assume file references are dynamic pointers, not static snapshots.

**The correct pattern:** The Files node in CRM Analytics recipes references a specific Salesforce File. When the CSV content changes, the file must be re-uploaded or updated via the Content API. Build a refresh step into the pipeline.

**Detection hint:** Any design that assumes the CSV auto-updates without an explicit upload step will produce stale data.

---

## Anti-Pattern 5: Omitting Backup Before XMD PATCH

**What the LLM generates:** XMD PATCH instructions with no prior GET/backup step.

**Why it happens:** LLMs provide update instructions without considering recovery scenarios.

**The correct pattern:** Always GET and save the current main XMD before any PATCH. Main XMD has no version history and cannot be recovered after modification without a backup.

**Detection hint:** Any XMD update workflow that does not begin with a GET/backup step creates an unrecoverable risk.
