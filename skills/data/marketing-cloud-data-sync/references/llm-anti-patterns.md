# LLM Anti-Patterns — Marketing Cloud Data Sync

Common mistakes AI coding assistants make when generating or advising on Marketing Cloud Data Sync.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Instructing the Practitioner to Write Data to an SDE

**What the LLM generates:** Instructions like "use a Query Activity to populate the Synchronized Data Extension with enriched records" or "use AMPscript's `UpsertDE()` to update the Contact SDE with engagement scores" or a Query Activity configuration that targets the SDE as the destination DE.

**Why it happens:** LLMs treat Data Extensions as a uniform category. Training data on AMPscript and Query Activities does not consistently distinguish between standard DEs (writable) and Synchronized DEs (read-only, system-managed). The LLM generalizes from the writable DE pattern.

**Correct pattern:**

```
SDEs are READ-ONLY. Do not use them as:
- Query Activity target (destination)
- AMPscript InsertDE() or UpsertDE() target
- Import Activity destination
- Journey Builder update target

Correct: Query FROM the SDE (as source) INTO a standard DE (as target).
All writes go to standard DEs; SDEs are source-only lookup tables.
```

**Detection hint:** Look for "insert into [Object_Salesforce]", "target DE = Contact_Salesforce", or `UpsertDE("Contact_Salesforce"` in any generated automation or AMPscript.

---

## Anti-Pattern 2: Recommending SDE as Direct Send Audience

**What the LLM generates:** Advice like "navigate to Email Studio > Send, select the Contact_Salesforce data extension as your audience, and send" — or a Journey Builder entry source that points directly to the Synchronized Data Extension.

**Why it happens:** The SDE appears in the Data Extensions list and looks like any other DE. LLMs do not have a reliable model of the MC send relationship requirement (the DE must be linked to a subscriber attribute and have a send relationship defined). The LLM defaults to the pattern it sees most often: select a DE, send to it.

**Correct pattern:**

```
SDEs cannot be send audiences. Required steps:
1. Create a SENDABLE Data Extension (in the main DE folder, not Synchronized Data Sources)
   with a field linked to Subscriber Key or Contact Key.
2. Populate it via Query Activity (querying FROM the SDE).
3. Define a Contact Builder relationship linking the sendable DE to the SDE
   via the shared subscriber key.
4. Use the SENDABLE DE as the send audience in Email Studio or Journey Builder.
```

**Detection hint:** Any output that says "send to [SDE name]" without first describing a sendable DE and Contact Builder relationship step is incorrect.

---

## Anti-Pattern 3: Claiming All CRM Fields Can Be Synced

**What the LLM generates:** Statements like "you can sync any Salesforce field to Marketing Cloud" or a field selection that includes encrypted fields, binary (Blob) fields, or rich text area fields — without flagging that these types are unsupported.

**Why it happens:** The LLM generalizes from the broad statement that MC Connect syncs CRM object fields. It does not have reliable training signal on the specific unsupported types (encrypted, binary, rich text) because these exclusions are documented in separate, less-trafficked help articles.

**Correct pattern:**

```
Fields that CANNOT be synced to Marketing Cloud via Synchronized Data Sources:
- Fields encrypted with Salesforce Shield Platform Encryption
- Binary (Blob) fields
- Rich Text Area (RTA) fields
- Most complex formula fields

Workaround: Create a plain text formula field or a non-encrypted shadow field in CRM.
Document excluded fields and the reason in the sync configuration record.
```

**Detection hint:** Generated field lists that include `__EncryptedString`, `RTA`, or `Body` type fields without a caveat about unsupported types should be flagged.

---

## Anti-Pattern 4: Treating Full Sync as the Default Fix for Stale or Missing Data

**What the LLM generates:** Troubleshooting instructions like "if records are missing from the SDE, trigger a full sync from Contact Builder" — recommended as the first or primary resolution step regardless of the actual failure mode.

**Why it happens:** "Full sync" sounds like a definitive reset that fixes any data inconsistency. LLMs anchor on this as a safe default because it superficially parallels patterns in other systems (e.g., full re-index, full refresh). The significant API cost and the fact that full sync does not fix the most common root causes (FLS gaps, field type mismatches, deleted field mappings, the 250-field cap) is not well-represented in training data.

**Correct pattern:**

```
Diagnose BEFORE triggering a full sync:
1. Check field type mismatches (CRM field type changed after sync configured?)
2. Check for deleted CRM fields still in the sync mapping
3. Check the Salesforce API limit consumption (Setup > System Overview > API Requests)
4. Check the connected user's FLS for the missing fields
5. Check SDE column list for silent 250-field exclusion

Full sync is a LAST RESORT — use only when record counts are materially wrong
and incremental sync cannot recover. Full sync does NOT fix field-level issues.
```

**Detection hint:** Any troubleshooting response that recommends "trigger a full sync" as the first step, or without a diagnostic sequence before it, is applying this anti-pattern.

---

## Anti-Pattern 5: Ignoring the 250-Field Cap When Selecting Fields for Sync

**What the LLM generates:** A field selection guide or setup walkthrough that says "select all fields you might need for personalization" without mentioning the 250-field cap or recommending a field count audit. In some cases, the LLM may explicitly say "select all available fields to avoid missing any data in future campaigns."

**Why it happens:** The 250-field cap is documented in a specific, low-traffic help article. LLMs trained on general Marketing Cloud documentation absorb the broad "you can sync Contact fields" message without the critical cap and silent-exclusion detail. The "select everything" heuristic feels safe because it avoids the future problem of a missing field — without the LLM modeling the silent exclusion failure mode.

**Correct pattern:**

```
ALWAYS audit field count before saving sync configuration:
- Count selected fields per object before saving
- Maximum: 250 fields per synchronized object
- Fields beyond 250 are silently excluded (no error, no log)
- After initial sync, compare the SDE column list to the intended selection
- Selection discipline: sync only fields needed for active or planned campaigns
- Document excluded fields and the reason
```

**Detection hint:** Any field selection guidance that says "select all" or "select everything you might need" without referencing the 250-field limit is applying this anti-pattern. Also flag any setup guide that does not include a post-sync column count audit step.

---

## Anti-Pattern 6: Recommending Manual Import Activity as an Alternative to SDE Sync for CRM Data

**What the LLM generates:** Advice to "use an Import Activity to load Contact data from a Salesforce report export into a Marketing Cloud DE on a schedule" as an equivalent alternative to Synchronized Data Sources — or as a workaround for any sync limitation.

**Why it happens:** Import Activity is a well-documented, frequently used Marketing Cloud pattern. LLMs surface it as a flexible fallback whenever a data loading requirement appears. The LLM does not reliably distinguish between the use case for Import Activity (external file-based loads, SFTP sources) and the use case for Synchronized Data Sources (native CRM object sync without file intermediaries).

**Correct pattern:**

```
Import Activity is NOT a substitute for Synchronized Data Sources when:
- The data source is a Salesforce CRM object (Contact, Lead, Account, etc.)
- Near-real-time or 15-minute sync latency is required
- The team does not want to manage scheduled Salesforce report exports and SFTP

Use Synchronized Data Sources when: CRM object data needs to be available in
Marketing Cloud with minimal latency and without file-based intermediaries.

Use Import Activity when: Data comes from an external system via SFTP,
a flat file, or a non-CRM source that MC Connect does not cover.
```

**Detection hint:** Any recommendation to export a Salesforce report to CSV and import it into MC as a CRM sync workaround — without explicitly stating that this is a fallback for cases where MC Connect is unavailable — is applying this anti-pattern.
