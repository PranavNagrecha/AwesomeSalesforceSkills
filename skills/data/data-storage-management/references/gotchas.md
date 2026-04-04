# Gotchas — Data Storage Management

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Deleting Records Does Not Immediately Free Storage

**What happens:** An admin or developer runs a mass delete (Bulk API, data loader, or SOQL delete in anonymous Apex) and then checks Setup > Storage Usage expecting the number to drop. The storage usage does not change or changes only slightly.

**When it occurs:** Any delete operation that sends records to the Recycle Bin. Standard deletes via DML, REST API, or Bulk API (non-hardDelete) all route records to the Recycle Bin. Records in the Recycle Bin continue to count against data storage until they are permanently purged — either by emptying the bin, waiting for the 15-day automatic purge (30 days for Bulk API hard deletes), or calling `Database.emptyRecycleBin()`.

**How to avoid:** After any mass delete operation intended to reclaim storage, explicitly empty the Recycle Bin. For automation, use Bulk API with `hardDelete` operation (which bypasses the Recycle Bin entirely) only when you are certain the data should not be recoverable. In Apex, `Database.emptyRecycleBin(recordIds)` purges specific records. Via REST: `DELETE /services/data/vXX.0/sobjects/{Type}/{id}` with `allOrNone=false` does not bypass the bin — use the Bulk API hardDelete job type for bin bypass.

---

## Gotcha 2: ContentVersion Renditions Double-Count File Storage

**What happens:** An org uploads a moderate volume of documents (PDFs, Word files, images) and observes file storage growing at 2–4x the expected rate based on the raw file sizes. Setup > Storage Usage shows ContentDocument consuming far more than the sum of uploaded file sizes.

**When it occurs:** Salesforce automatically generates preview thumbnails and document renditions (PDF previews for Word/Excel, image thumbnails) for every ContentVersion upload. Each rendition is stored as its own ContentVersion record with `IsMajorVersion = false` and a system-generated `ContentDocumentId`. These rendition records count against file storage. Orgs with millions of small uploaded files (images, short PDFs) can find that renditions account for 50–200% of the raw file storage.

**How to avoid:** There is no supported way to disable rendition generation. Mitigation strategies include: (1) compressing source files before upload to reduce the rendition size, (2) using the ContentDistribution feature only where previews are genuinely needed, (3) factoring rendition overhead (estimate 1.5–2x multiplier) into storage capacity planning. When auditing file storage, query `SELECT SUM(ContentSize), IsLatest, FileType FROM ContentVersion GROUP BY IsLatest, FileType` to separate actual uploads from renditions.

---

## Gotcha 3: Field History Tracking Records Accumulate Silently

**What happens:** An admin enables field history tracking on a high-volume object (Opportunity, Case, custom transactional object) with many tracked fields. Six months later, data storage usage is significantly higher than projected record growth explains.

**When it occurs:** Every change to a tracked field creates one `OpportunityFieldHistory`, `CaseHistory`, or custom object `__History` record. An Opportunity with 10 tracked fields that is updated 20 times generates 200 history records. At 2 KB each, that is 400 KB per Opportunity. An org with 1 million Opportunities and active tracking can accumulate hundreds of millions of history records. Salesforce retains history records for 18 months then auto-purges, but current records within that window count toward data storage.

**How to avoid:** Audit which fields actually need tracking before enabling it. Disable tracking on low-value fields. If comprehensive field-level audit history is required for compliance, evaluate Field Audit Trail (a platform add-on) which stores history outside the standard data storage allocation, or consider writing changes to a Big Object instead of relying on standard tracking.

---

## Gotcha 4: Orphaned ContentDocuments Persist Until Explicitly Deleted

**What happens:** A parent record (Account, Case, Opportunity) is deleted. The ContentDocumentLink joining the file to the parent is deleted automatically. But the ContentDocument itself — and all its ContentVersion records — persists in file storage unless explicitly deleted. Over time, these orphaned files accumulate and inflate file storage with no way to access them from the standard UI.

**When it occurs:** Any workflow that deletes records without first deleting associated files. This includes: bulk data cleanup jobs, automated record lifecycle management (case aging, opportunity purges), and user-initiated record deletes. Salesforce does not cascade-delete ContentDocuments when the last ContentDocumentLink is removed — this is intentional (files could be linked to multiple records), but the side-effect is orphan accumulation.

**How to avoid:** Before deleting high-volume records with attached files, run: `SELECT Id FROM ContentDocument WHERE Id NOT IN (SELECT ContentDocumentId FROM ContentDocumentLink)`. Include ContentDocument deletion in any data cleanup job that targets records with file attachments. After large deletes, run an orphan audit query and batch-delete results via Bulk API.

---

## Gotcha 5: The Limits API Reports Storage in MB, Not GB

**What happens:** An automated monitoring script queries the Limits API and compares `DataStorageMB.Max` against a threshold defined in GB. The comparison logic has an off-by-1000 error, triggering false positives or — more dangerously — never triggering because the comparison direction is inverted.

**When it occurs:** The Limits API endpoint `/services/data/vXX.0/limits/` returns both `DataStorageMB` and `FileStorageMB` in megabytes. The Setup UI displays storage in GB. Practitioners who build alerts after reading the Setup UI documentation and then use the Limits API without checking the unit often mix units.

**How to avoid:** Always read `DataStorageMB` and treat the values as megabytes. To compare against a GB threshold, multiply the threshold by 1024 (not 1000 — Salesforce uses binary megabytes). Test the monitoring script against a sandbox with known storage values before deploying to production. Log the raw API values alongside human-readable converted values in any alert output.
