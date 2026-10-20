# Gotchas — Data Storage Management

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Storage Usage Lags a Mass Delete — and the Recycle Bin Is Not Why

**What happens:** An admin or developer runs a mass delete (Bulk API, data loader, or SOQL delete in anonymous Apex) and then checks Setup > Storage Usage expecting the number to drop. The storage usage does not change or changes only slightly.

**When it occurs:** After any large delete. The cause is **asynchronous storage recalculation**, not the Recycle Bin: Salesforce Help states that when you add or remove a large number of records or files, "the change in your org's storage usage isn't reflected immediately." (UNVERIFIED (2026-10-20): Help-only quote; no corpus file holds it.)

The Recycle Bin is the wrong suspect, and chasing it does damage. Per *Manage the Recycle Bin*: "Records in the Recycle Bin don't count against your Salesforce org's storage usage," and "There isn't a limit on the number of deleted records that the Recycle Bin can hold." The 15-day figure is how long a deleted record stays **restorable**. It is not a storage-accounting window, and emptying the bin reclaims nothing.

**How to avoid:** Wait and re-check Setup > Storage Usage before concluding the delete failed. Treat `Database.emptyRecycleBin()` and Bulk API `hardDelete` as recoverability decisions, not storage levers — hard delete bypasses the bin ("aren't stored in the Recycle Bin", api_asynch 264 L1630-1631), so there is no restore window of any length. The bin figures are salesforce_large_data_volumes_bp 264 L736-738. Standard deletes via DML, REST, or non-hardDelete Bulk API all route to the bin and remain restorable for 15 days; `DELETE /services/data/vXX.0/sobjects/{Type}/{id}` does not bypass it.

---

## Gotcha 2: ContentVersion Renditions Double-Count File Storage

**What happens:** An org uploads a moderate volume of documents (PDFs, Word files, images) and observes file storage growing at 2–4x the expected rate based on the raw file sizes. Setup > Storage Usage shows ContentDocument consuming far more than the sum of uploaded file sizes.

**When it occurs:** Salesforce automatically generates preview thumbnails and document renditions (PDF previews for Word/Excel, image thumbnails) for every ContentVersion upload. Each rendition is stored as its own ContentVersion record with `IsMajorVersion = false` and a system-generated `ContentDocumentId`. These rendition records count against file storage. Orgs with millions of small uploaded files (images, short PDFs) can find that renditions account for 50–200% of the raw file storage. UNVERIFIED (2026-10-20): this whole paragraph, including the 50–200% and 1.5–2x figures below, is field experience; no corpus file says renditions are stored as ContentVersion records or count toward file storage.

**How to avoid:** There is no supported way to disable rendition generation. Mitigation strategies include: (1) compressing source files before upload to reduce the rendition size, (2) using the ContentDistribution feature only where previews are genuinely needed, (3) factoring rendition overhead (estimate 1.5–2x multiplier) into storage capacity planning. When auditing file storage, query `SELECT SUM(ContentSize), IsLatest, FileType FROM ContentVersion GROUP BY IsLatest, FileType` to separate actual uploads from renditions.

---

## Gotcha 3: Field History Tracking Records Accumulate Silently

**What happens:** An admin enables field history tracking on a high-volume object (Opportunity, Case, custom transactional object) with many tracked fields. Six months later, the history tables are huge and Setup > Storage Usage is high for some other reason; the admin blames the history. (The earlier version of this gotcha said the history inflated data storage; the guide says it does not, see below.)

**When it occurs:** Every change to a tracked field creates one `OpportunityFieldHistory`, `CaseHistory`, or custom object `__History` record. An Opportunity with 10 tracked fields that is updated 20 times generates 200 history records, so the table grows quickly and slows history queries. **They do not count toward data storage:** "Field history tracking data doesn't count against your data storage limits" (secguide 262 L4555-4556, L4634-4635), and the same is stated for Field Audit Trail data (secguide 262 L4755-4756). An earlier version of this gotcha said they did and priced them at 2 KB each; that arithmetic is removed. Without Field Audit Trail, Salesforce retains history up to 18 months in the UI and up to 24 months via the API (secguide 262 L4553-4554).

**How to avoid:** Do not count history objects as a storage lever. Audit which fields actually need tracking for volume and report-performance reasons, and disable tracking on low-value fields. If retention beyond 18/24 months is required, Field Audit Trail keeps history until you delete it (secguide 262 L4554-4555) and its retention is set with a `HistoryRetentionPolicy` (api_meta 264 L46305-46331).

---

## Gotcha 4: Orphaned ContentDocuments Persist Until Explicitly Deleted

**What happens:** A parent record (Account, Case, Opportunity) is deleted. The ContentDocumentLink joining the file to the parent is deleted automatically. But the ContentDocument itself — and all its ContentVersion records — persists in file storage unless explicitly deleted. Over time, these orphaned files accumulate and inflate file storage with no way to access them from the standard UI.

**When it occurs:** Any workflow that deletes records without first deleting associated files. This includes: bulk data cleanup jobs, automated record lifecycle management (case aging, opportunity purges), and user-initiated record deletes. Salesforce does not cascade-delete ContentDocuments when the last ContentDocumentLink is removed — this is intentional (files could be linked to multiple records), but the side-effect is orphan accumulation. UNVERIFIED (2026-10-20): link cleanup on parent delete and the no-cascade behaviour are Help-only; object_reference 264 L76789 mentions link deletion only for an owner change.

**How to avoid:** Before deleting high-volume records with attached files, run: `SELECT Id FROM ContentDocument WHERE Id NOT IN (SELECT ContentDocumentId FROM ContentDocumentLink)` (unfiltered, so the running user needs Query All Files at API 59.0+, object_reference 264 L77253-77254). Include ContentDocument deletion in any data cleanup job that targets records with file attachments. After large deletes, run an orphan audit query and batch-delete results via Bulk API.

---

## Gotcha 5: The Limits API Reports Storage in MB, Not GB

**What happens:** An automated monitoring script queries the Limits API and compares `DataStorageMB.Max` against a threshold defined in GB. The comparison logic has an off-by-1000 error, triggering false positives or — more dangerously — never triggering because the comparison direction is inverted.

**When it occurs:** The Limits API endpoint `/services/data/vXX.0/limits/` returns both `DataStorageMB` and `FileStorageMB` (api_rest 264 L8191, L8193; the field names carry the unit, MB). The Setup UI displays storage in GB. Practitioners who build alerts after reading the Setup UI documentation and then use the Limits API without checking the unit often mix units.

**How to avoid:** Always read `DataStorageMB` and treat the values as megabytes. To compare against a GB threshold, multiply the threshold by 1024 (not 1000 — Salesforce uses binary megabytes; UNVERIFIED (2026-10-20): the 1024 convention is not stated in api_rest, whose sample shows `"Max": 1024` for both fields at L2163-2174, so confirm against your own org's Setup figures). Test the monitoring script against a sandbox with known storage values before deploying to production. Log the raw API values alongside human-readable converted values in any alert output.
