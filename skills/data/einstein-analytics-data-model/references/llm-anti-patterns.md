# LLM Anti-Patterns: Einstein Analytics Data Model (XMD)

Common mistakes AI coding assistants make when generating or advising on CRM Analytics XMD.

---

## Anti-Pattern 1: Writing to main or system XMD

**What the LLM generates:** `PATCH /wave/datasets/{id}/xmds/main` or a PUT to `xmds/system`.

**Why it happens:** "Main" sounds like the org-wide layer, and many REST APIs use PATCH for partial updates.

**The correct pattern:** The Xmd resource supports GET and PUT, and PUT works on the user type only. Write to `PUT /wave/datasets/<datasetID>/versions/<versionID>/xmds/user`.

**Detection hint:** Any write method on a URL ending in `xmds/main` or `xmds/system`, or any PATCH on an Xmd URL.

---

## Anti-Pattern 2: Dropping the version segment from the URL

**What the LLM generates:** `GET /wave/datasets/{id}/xmds/main`.

**Why it happens:** The model assumes XMD is attached to the dataset as a whole.

**The correct pattern:** Every Xmd resource URL includes `/versions/<versionID>/`. Read `currentVersionId` from the Dataset resource first.

**Detection hint:** An `xmds/` URL with no `versions/` segment.

---

## Anti-Pattern 3: Sending a delta and calling it a merge

**What the LLM generates:** A payload with one changed label and the claim "only the label changes; everything else is preserved."

**Why it happens:** The model generalizes from merge-patch APIs.

**The correct pattern:** The XMD guide says an upload overwrites current customizations and is not appended. GET the full user XMD, edit it, and PUT the full document. Keep the pre-change copy.

**Detection hint:** The words "additive merge" or "only include changed properties" next to an XMD write.

---

## Anti-Pattern 4: Treating the user XMD as a personal preference

**What the LLM generates:** "Use user XMD to change the label just for yourself; use main XMD for everyone."

**Why it happens:** The type name `user` reads like "per user."

**The correct pattern:** The Standard User XMD is the dataset's customization file. Every visualization that uses the dataset shows its formatting.

**Detection hint:** Any claim that user XMD affects only the requesting user.

---

## Anti-Pattern 5: Querying WaveXmd with SOQL or Apex

**What the LLM generates:** `SELECT Id FROM WaveXmd WHERE ...`

**Why it happens:** The model sees `WaveXmd` in Metadata API lists and assumes an sObject of the same name.

**The correct pattern:** There is no `WaveXmd` sObject in the Object Reference or the Tooling API. Use the REST Xmd resources, or retrieve the `WaveXmd` metadata type.

**Detection hint:** `WaveXmd` inside a SOQL string.

---

## Anti-Pattern 6: Packaging the Standard User XMD

**What the LLM generates:** "Add the XMD to your change set and it will deploy with the dataset."

**Why it happens:** The model assumes all customization is metadata.

**The correct pattern:** The Standard User XMD is tied to a dataset version that is not packageable. Deploy `WaveXmd` (the Primary User XMD), then run the dataflow so it applies.

**Detection hint:** A deployment plan with XMD but no dataflow run after it.

---

## Anti-Pattern 7: Reclassifying a field by moving it between XMD arrays

**What the LLM generates:** Instructions to move a field from `measures` to `dimensions` in XMD to change how it aggregates.

**Why it happens:** The XMD file has separate `dimensions` and `measures` arrays, so the model treats them as the type definition.

**The correct pattern:** The XMD guide lists formatting, labels, colors, and actions as what XMD customizes. Change the field type upstream, for example the External Data metadata `type` (Text, Numeric, Date) or the recipe output type.

**Detection hint:** An XMD edit offered as the fix for "this number is being summed."

---

## Anti-Pattern 8: Joining datasets with a SAQL `join` keyword

**What the LLM generates:** `q = join a by 'Id', b by 'AccountId';`

**Why it happens:** SQL habits.

**The correct pattern:** SAQL combines streams with `cogroup`, including `left` and `full` outer forms, and `coalesce()` for unmatched values.

**Detection hint:** The token `join` used as a SAQL statement.
