# LLM Anti-Patterns: Analytics Data Preparation (XMD and External Data)

Mistakes AI assistants make when advising on CRM Analytics XMD and external data loads, with the correct move for each. Correction (2026-10-03): the previous version of this file told readers to PATCH main XMD as an additive merge and to avoid PUT. The CRM Analytics REST API Developer Guide documents the opposite: GET for every XMD type and PUT on the user type only, and the XMD guide says each upload overwrites.

## Anti-Pattern 1: Querying WaveXmd With SOQL

**What the LLM generates:** `SELECT Id FROM WaveXmd WHERE ...` to read dataset formatting.

**Why it happens:** The model sees "WaveXmd" in Metadata API lists and assumes it is an sObject.

**The correct pattern:** WaveXmd is a Metadata API type (suffix `.xmd`, folder `wave`), and no WaveXmd object appears in the Object Reference. Read XMD with `GET /wave/datasets/<id>/versions/<versionId>/xmds/<type>` or a Metadata API retrieve.

**Detection hint:** `FROM WaveXmd` in any SOQL.

---

## Anti-Pattern 2: PATCHing main or system XMD

**What the LLM generates:** `PATCH /wave/datasets/{id}/xmds/main` with a partial body, or a PUT to `xmds/system`.

**Why it happens:** Partial-update semantics are common in other Salesforce REST resources, and the version segment of the path is easy to drop.

**The correct pattern:** The documented methods are GET on all types and PUT on `xmds/user` only, under `/versions/<versionID>/`. For deployable changes, deploy WaveXmd.

**Detection hint:** `xmds/main` or `xmds/system` paired with PATCH or PUT; any XMD path without `/versions/`.

---

## Anti-Pattern 3: Sending a Partial XMD Document

**What the LLM generates:** A PUT body containing only the two dimensions being relabeled.

**Why it happens:** The model assumes the API merges.

**The correct pattern:** "Each time you upload the XMD file, CRM Analytics overwrites the current dataset customizations." GET the current user XMD, edit in place, and PUT the whole document.

**Detection hint:** A PUT body that is much shorter than the GET response for the same version, or a payload with no `dates` or `measures` arrays when the dataset has them.

---

## Anti-Pattern 4: Telling Users That User XMD Is Personal

**What the LLM generates:** "User XMD only affects your own view; other users keep the default labels."

**Why it happens:** The word "user" suggests per-user scope.

**The correct pattern:** The Standard User XMD is the dataset's custom formatting: "If you modify the XMD for a dataset, every UI visualization that uses the dataset shows the modified format." Changes affect everyone who uses the dataset.

**Detection hint:** "per-user", "only you", or "personal" near "user XMD".

---

## Anti-Pattern 5: Omitting the Backup and the Rename Review

**What the LLM generates:** XMD update instructions with no prior GET or retrieve, and no check for renamed fields.

**Why it happens:** Success-path examples skip the defensive steps.

**The correct pattern:** Commit the current XMD before any write, because uploads overwrite and an invalid upload reverts all formatting to defaults. Review the XMD in the same change as any field rename, because stale field names cause errors.

**Detection hint:** A write step with no GET or retrieve before it.

---

## Anti-Pattern 6: Using Hidden Fields as a Security Control

**What the LLM generates:** "Set `showInExplorer` to false so managers can't see the salary column."

**Why it happens:** Hiding looks like access control in the UI.

**The correct pattern:** Hidden fields remain available in SAQL, dashboard JSON, and the REST API. Remove the field from the dataset or apply a security predicate.

**Detection hint:** `showInExplorer` recommended for a sensitive field.

---

## Anti-Pattern 7: Uploading External Data Without a Metadata File

**What the LLM generates:** An InsightsExternalData insert with `Format` Csv and no `MetadataJson`, followed by a numeric chart built on the result.

**Why it happens:** The metadata file is documented as optional.

**The correct pattern:** Without metadata, "every field is treated as text." Send a metadata JSON whose `fields` follow the CSV column order, with `defaultValue` on every Numeric field and `numberOfLinesToIgnore` set explicitly.

**Detection hint:** An upload plan with no `MetadataJson`, or a Numeric field without `defaultValue`.

---

## Anti-Pattern 8: Treating an External CSV as Self-Refreshing

**What the LLM generates:** "Upload the CSV once and the recipe will always use the latest version."

**Why it happens:** LLMs assume file references are dynamic pointers, not static snapshots.

**The correct pattern:** Build an explicit refresh step. With the External Data API, each refresh is a new InsightsExternalData job (`Operation` Overwrite, Append, or Upsert), counted against 50 jobs per dataset per rolling 24 hours. UNVERIFIED (2026-10-03): the earlier statement that a recipe Files node references one specific Salesforce File version was not re-read in a fetched source; keep the refresh step either way.

**Detection hint:** Any design that assumes the CSV updates itself without a scheduled upload.
