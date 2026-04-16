# LLM Anti-Patterns — Einstein Analytics Data Model (XMD)

Common mistakes AI coding assistants make when generating or advising on CRM Analytics XMD.

---

## Anti-Pattern 1: Attempting to PATCH System XMD

**What the LLM generates:** Code calling `PATCH /wave/datasets/{id}/xmds/system`.

**Why it happens:** LLMs assume "system" is the base layer that can be overridden.

**The correct pattern:** System XMD is immutable. Always PATCH `xmds/main`.

**Detection hint:** Any write operation targeting `xmds/system` is incorrect.

---

## Anti-Pattern 2: Using SOQL to Query WaveXmd

**What the LLM generates:** `SELECT Id, Name FROM WaveXmd WHERE DatasetId = '{id}'`

**Why it happens:** LLMs apply standard Salesforce SOQL patterns to analytics metadata.

**The correct pattern:** Use `GET /wave/datasets/{id}/xmds/main` — WaveXmd is not SOQL-accessible.

**Detection hint:** Any SOQL query against `WaveXmd` fails with INVALID_TYPE.

---

## Anti-Pattern 3: Presenting Datasets as Analogous to Salesforce Object Model

**What the LLM generates:** Descriptions of CRM Analytics datasets with "related lists," "lookup fields," or "parent-child relationships."

**Why it happens:** LLMs conflate the Salesforce object model with CRM Analytics columnar data model.

**The correct pattern:** CRM Analytics datasets are columnar stores. Cross-dataset joins are SAQL queries at runtime — not persistent relationship metadata in XMD.

**Detection hint:** Any description of CRM Analytics XMD referencing "lookup field" or "foreign key" is incorrect.

---

## Anti-Pattern 4: Using PUT Instead of PATCH for XMD Updates

**What the LLM generates:** HTTP PUT to update XMD, resulting in full replacement of all properties.

**Why it happens:** Many REST APIs use PUT for updates.

**The correct pattern:** XMD updates use HTTP PATCH with a minimal delta payload. PUT overwrites all existing customizations.

**Detection hint:** Any PUT to an XMD endpoint risks deleting existing customizations.

---

## Anti-Pattern 5: Assuming Main XMD Customizations Are Versioned

**What the LLM generates:** "You can roll back the XMD change using the previous version."

**Why it happens:** LLMs know datasets are versioned and incorrectly extend this to XMD.

**The correct pattern:** Main XMD is NOT versioned. Previous state must be backed up manually before PATCH.

**Detection hint:** Any mention of "rolling back" an XMD change assumes version history that does not exist.
