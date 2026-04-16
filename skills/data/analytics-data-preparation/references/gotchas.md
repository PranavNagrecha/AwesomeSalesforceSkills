# Gotchas — Analytics Data Preparation (XMD Metadata)

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: SOQL Cannot Query WaveXmd — Use REST API Only

**What happens:** Developers attempt `SELECT Id FROM WaveXmd`. Throws INVALID_TYPE. WaveXmd is not accessible via SOQL under any circumstances.

**Impact:** Code that reads or updates WaveXmd via SOQL never works. Integration tests built around SOQL queries fail at runtime.

**How to avoid:** Always use the Wave REST API for XMD operations: `GET` and `PATCH /wave/datasets/{id}/xmds/{type}`.

---

## Gotcha 2: Modifying System XMD Fails — PATCH Returns HTTP 400

**What happens:** PATCH to `xmds/system` returns HTTP 400. System XMD is immutable.

**Impact:** Practitioners waste time debugging the API call without realizing the endpoint type is incorrect.

**How to avoid:** Target `xmds/main` for all customizations. System XMD is read-only.

---

## Gotcha 3: Main XMD Has No Version History — No Undo After PATCH

**What happens:** PATCH overwrites main XMD immediately with no backup or rollback.

**Impact:** Incorrect PATCH payloads corrupt label/format settings with no recovery path.

**How to avoid:** Always GET and save main XMD JSON before any PATCH operation. Treat this as a mandatory pre-flight step.

---

## Gotcha 4: External CSV Files Are Not Auto-Refreshed

**What happens:** The Files node in a recipe references a specific Salesforce File version. When the CSV content changes but the file name or ID is the same, the recipe continues to use the old data until the file is explicitly updated via the Files API.

**Impact:** Teams update the CSV on their local machine but forget to re-upload to Salesforce Files, causing the recipe to run on stale reference data with no error.

**How to avoid:** Build a Salesforce Files API upload step into the deployment or data refresh pipeline for any CSV used by a recipe Files node.
