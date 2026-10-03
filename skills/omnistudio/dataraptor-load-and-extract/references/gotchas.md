# Gotchas: DataRaptor Load and Extract

Non-obvious platform behaviors that cause real production problems in this domain. Each gotcha names the official source it rests on. Current documentation calls DataRaptors "Omnistudio Data Mappers."

## Gotcha 1: Load Preview Writes Real Records

**What happens:** A developer tests a Load on the Preview tab in a shared org with realistic JSON. The records are created or updated for real. Test data ends up in UAT or, worse, production.

**When it occurs:** Any Load Preview, including "just checking the mapping" runs.

**How to avoid:** Preview Loads only in a developer sandbox or scratch org. Use input JSON that targets throwaway records. Clean up afterward.

**Source:** Trailhead, "Build a Data Mapper Turbo Extract and Data Mapper Load": "The Objects Created panel lists the resulting objects, which are saved permanently."

---

## Gotcha 2: An Upsert Key That Doesn't Match Creates a New Record

**What happens:** A Load is meant to update existing Contacts, but every run creates duplicates. The Upsert Key field carries a value that doesn't match a unique existing record, so the Load inserts.

**When it occurs:** Upsert Keys on fields that are blank, formatted differently from the incoming data, or not unique.

**How to avoid:** Choose Upsert Key fields that match exactly one record. The key doesn't have to be an External ID field, but uniqueness is your responsibility. Test a known-existing record in a sandbox Preview.

**Source:** Trailhead, "Create or Update: How Does an Omnistudio Data Mapper Load Decide?" ("It's possible to designate any field in the Omnistudio Data Mapper Fields mapping as an Upsert Key... If the Omnistudio Data Mapper Load can't find a match with any existing record, it creates a new record.")

---

## Gotcha 3: Empty "Is Required For Upsert" Fields Skip the Record

**What happens:** Some records from an OmniScript never reach Salesforce, with no error in the user interface.

**When it occurs:** A field marked Is Required For Upsert arrives empty for those records.

**How to avoid:** Mark fields required only when a record without them must not be written. Validate those fields in the OmniScript or Integration Procedure first, and log skipped records.

**Source:** Trailhead, same unit: "All Is Required For Upsert fields must have data. If not, the Omnistudio Data Mapper Load skips that record."

---

## Gotcha 4: Without `rollbackOnError`, a Multi-Object Load Commits Partial Work

**What happens:** A Load writes an order header, then fails on the line items. The header stays committed.

**When it occurs:** Multi-object Loads with `rollbackOnError` false, which is the value in the documented sample. `errorIgnored` true also lets processing continue past errors.

**How to avoid:** Set `rollbackOnError` true for Loads that represent one business transaction. Leave `errorIgnored` false unless partial success is acceptable and handled.

**Source:** Industries Common Resources Developer Guide, OmniDataTransform fields `rollbackOnError` ("must not commit if there is an error (true) or commit what has been executed (false)") and `errorIgnored`.

---

## Gotcha 5: Large Loads Switch to Apex Batch Jobs

**What happens:** A Load that behaves synchronously in testing returns before the records exist when a production call carries many records. Downstream steps read data that isn't written yet.

**When it occurs:** Input record counts above `synchronousProcessThreshold`, or Loads with `processSuperBulk` true, which spreads the upsert over several Apex batch jobs.

**How to avoid:** Set the threshold deliberately. Keep interactive OmniScript calls below it. For migrations and integrations, use Bulk API 2.0 or Batch Apex outside OmniStudio. UNVERIFIED (2026-10-03): the guide doesn't say how a threshold of 0 (the value in its sample) behaves; confirm in a sandbox before relying on it.

**Source:** Industries Common Resources Developer Guide, OmniDataTransform fields `synchronousProcessThreshold` ("If it's more than this number, then it uses a batch job") and `processSuperBulk`.

---

## Gotcha 6: Extracts Don't Check Field Access Unless Told To

**What happens:** An Extract built by an admin returns fields that the running external user's profile hides.

**When it occurs:** Extracts used by guest, portal, or restricted internal users with the field-level security option off.

**How to avoid:** Turn on the Options-tab check of the user's field access (`fieldLevelSecurityEnabled`) for every Extract that serves restricted users, and test as that user.

**Source:** Trailhead, "Explore Data Mapper Features" (Options tab: "whether to check the user's access permissions for the fields before executing"). Industries Common Resources Developer Guide, OmniDataTransform `fieldLevelSecurityEnabled`.

---

## Gotcha 7: Cached Extract Responses Can Be Stale

**What happens:** Users see an old phone number after it was changed, because the Extract response is served from platform cache.

**When it occurs:** Extracts with a platform cache type set and a long time to live.

**How to avoid:** Use Session Cache for user-specific data and Org Cache for shared reference data, and keep the time to live short for data that changes.

**Source:** Trailhead, "Explore Data Mapper Features" (Platform Cache Type and Time to Live in Minutes). Industries Common Resources Developer Guide, OmniDataTransform `responseCacheType` and `responseCacheTtlMinutes`.

---

## Gotcha 8: OmniDataTransform Records Are Internal

**What happens:** A script updates `OmniDataTransform` or `OmniDataTransformItem` records directly to bulk-edit mappings. Data Mappers start failing.

**When it occurs:** DML or Data Loader edits on the standard objects behind Data Mappers.

**How to avoid:** Change Data Mappers in the designer or through the `OmniDataTransform` metadata type, never through record DML.

**Source:** Industries Common Resources Developer Guide, Omnistudio Standard Objects: OmniDataTransform is "For internal use only... Don't perform any create, edit, or delete operations on this object."

---

## Gotcha 9: Turning On Omnistudio Metadata Is One-Way

**What happens:** A team enables Omnistudio metadata to deploy Data Mappers with Salesforce CLI, and later finds the setting can't be turned off. Enabling can also fail when component unique names contain spaces or special characters.

**When it occurs:** Moving from DataPacks to metadata-based deployment.

**How to avoid:** Rename components with spaces or special characters first, and agree on the deployment model before enabling `enableOmniStudioMetadata`.

**Source:** Industries Common Resources Developer Guide, OmniStudioSettings `enableOmniStudioMetadata` ("This setting can't be enabled if metadata component unique names contain spaces or special characters. After it's enabled, the setting can't be disabled.").
