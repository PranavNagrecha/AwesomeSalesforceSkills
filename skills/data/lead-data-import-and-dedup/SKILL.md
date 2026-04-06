---
name: lead-data-import-and-dedup
description: "Lead data import quality and deduplication strategy: matching rule design for Leads, Data Import Wizard dedup behavior, Web-to-Lead data quality controls, cross-object Lead-to-Contact fuzzy dedup, and enrichment patterns. Use when importing leads from CSV/list files, configuring duplicate detection for incoming leads, diagnosing why duplicate leads are bypassing rules, or designing web form data quality workflows. Triggers: leads from a trade show import are creating duplicates, web-to-lead form submissions are bypassing duplicate rules, deduplicating leads against existing contacts before conversion, setting up matching rules for lead imports. NOT for Data Loader mechanics or Bulk API setup (use data/bulk-api-patterns). NOT for large-scale merge execution across millions of records (use data/large-scale-deduplication). NOT for post-conversion record merge behavior (use data/record-merge-implications)."
category: data
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
  - Security
triggers:
  - "imported leads from a trade show CSV and now have thousands of duplicates"
  - "web-to-lead form submissions are creating duplicate leads even with a duplicate rule enabled"
  - "how do I deduplicate leads against existing contacts before converting them"
  - "Data Import Wizard dedup is not matching records I expect to be duplicates"
  - "set up matching rules so list uploads do not create duplicate leads"
  - "lead import deduplication matching rules and duplicate detection configuration"
  - "web-to-lead duplicate detection is not blocking duplicate records"
  - "configure matching rules for lead deduplication during import"
tags:
  - lead
  - deduplication
  - data-import
  - matching-rules
  - web-to-lead
  - data-quality
  - duplicate-rules
inputs:
  - "Source of incoming lead data (CSV upload, Web-to-Lead form, API integration, marketing automation sync)"
  - "Volume of records being imported and estimated duplicate rate"
  - "Fields available for matching (Email, Phone, Name, Company)"
  - "Whether existing Contacts or converted Leads must also be checked"
  - "Whether blocking or alerting behavior is required for duplicates"
outputs:
  - "Matching rule and duplicate rule configuration recommendation"
  - "Data Import Wizard dedup field selection guidance"
  - "Web-to-Lead data quality design (field validation, Apex handler, or Assignment Rule approach)"
  - "Cross-object Lead-to-Contact dedup strategy (native vs. third-party)"
  - "Lead enrichment pattern recommendation"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-06
---

# Lead Data Import and Dedup

Use this skill when leads are entering Salesforce from file imports, web forms, or marketing integrations and you need to prevent duplicates, detect existing duplicates, or enrich incoming data before it pollutes the CRM. It covers matching rule design specific to Lead objects, the limitations of Data Import Wizard dedup, Web-to-Lead bypass behavior, and the constraints of native vs. third-party cross-object matching. It does not cover large-scale batch merge execution or Data Loader mechanics.

---

## Before Starting

Gather this context before designing any lead import or dedup workflow:

- **Data entry channel** — is data arriving via CSV upload (Data Import Wizard or Data Loader), Web-to-Lead POST, a marketing automation sync (Pardot/Marketing Cloud), or a direct API call? Each channel has different dedup capabilities and failure modes.
- **Most common wrong assumption** — practitioners assume that enabling a Duplicate Rule with "Block" action will prevent all duplicate leads from entering the org. Web-to-Lead submissions and API inserts bypass the blocking action silently; the rule evaluates but does not stop the insert.
- **Matching algorithm limits** — the Standard Lead Matching Rule uses Jaro-Winkler (name fuzzy) and Metaphone 3 (phonetic) algorithms. Data Import Wizard performs only single-field exact-match dedup on a user-chosen field (Email, Name, or a custom external ID). These are fundamentally different capabilities.
- **5-active-rules-per-object limit** — an org can have at most 5 active Duplicate Rules per object and 5 active Matching Rules. Plan rule slots carefully in orgs with existing dedup configuration.
- **Cross-object scope** — standard matching rules can check a Lead against existing Contacts (Lead-to-Contact rule exists out of the box), but native matching is still limited to the algorithm and field coverage of that rule. Fuzzy cross-object matching at volume requires third-party tooling.

---

## Core Concepts

### Standard Lead Matching Rule and Its Algorithms

The Standard Lead Matching Rule (enabled by default in all Salesforce orgs) uses three matching methods on different field groups:

| Field(s) | Matching Method | Behavior |
|---|---|---|
| First Name, Last Name | Jaro-Winkler fuzzy | Tolerates transpositions and minor misspellings |
| Last Name (phonetic) | Metaphone 3 | Catches phonetic variants (e.g., "Smith" vs. "Smyth") |
| Email | Exact | Case-insensitive exact match only |
| Phone | Normalized exact | Strips formatting characters before comparison |
| Company | Jaro-Winkler fuzzy | Tolerates abbreviations and minor differences |

A match is declared when the combined score across enabled fields exceeds the rule's configured threshold. Practitioners often assume the standard rule catches all near-duplicates; in practice it misses records with mismatched email domains and correct names, or same-email leads with different company names when Email is weighted too low.

Custom matching rules can extend this by adding additional field comparisons, but each rule still uses only the built-in algorithm options — there is no way to inject custom similarity logic through native configuration alone.

### Data Import Wizard Dedup: Single-Field Exact Match Only

The Data Import Wizard's built-in dedup capability is significantly more limited than Duplicate Rules:

- The wizard prompts you to choose **one field** for duplicate matching during import: Email, Name, or a custom External ID field.
- Matching is **exact** on that one field. No fuzzy matching, no multi-field scoring.
- If the chosen field is blank on incoming records, those records are always inserted as new — no fallback matching occurs.
- The wizard will show a "duplicates found" summary at the end of import but does **not** prevent insert of non-matching records.

For list imports where data quality is poor (name variants, missing email, abbreviated company), the Data Import Wizard dedup will miss a high percentage of true duplicates. A pre-import cleansing step (normalizing email, standardizing company name) dramatically improves match rates before the wizard runs.

### Web-to-Lead Bypass Behavior

Web-to-Lead is a POST-based lead capture mechanism that inserts records via an internal Salesforce pathway that does **not** enforce Duplicate Rule blocking:

- A Duplicate Rule set to "Block" will **not** stop a Web-to-Lead submission from creating a duplicate. The rule evaluates, the alert is recorded in the Duplicate Record Set, but the insert proceeds.
- Only "Alert" mode produces visible behavior (a Duplicate Record Set is created and the lead is flagged).
- This is documented Salesforce behavior, not a bug. The same applies to API-based lead inserts via REST or SOAP when the calling integration does not check duplicate rule results.

The practical implication: if your org relies on Duplicate Rule blocking to prevent web form spam or duplicate capture, the rule will silently fail for every form submission. The correct design pattern is a post-insert Apex trigger or a Flow on Lead creation that checks for duplicates and either merges, alerts, or routes the record — rather than relying on blocking.

### Cross-Object Lead-to-Contact Dedup

Salesforce ships a standard "Lead-to-Contact" matching rule that checks incoming Lead records against existing Contacts using Email (exact) and Name (fuzzy). This is the native mechanism for detecting leads that already exist as contacts in the org before conversion.

Native limitations:
- Matching is limited to the fields and algorithms in the standard rule.
- There is no built-in "auto-convert" or "auto-merge" action when a match is found — a Duplicate Record Set is created and a human or automation must act on it.
- For high-volume orgs (>500K contacts), the match evaluation at lead insert time can add meaningful save latency.
- Complex cross-object matching (e.g., Lead Company matches Account Name + Lead Email domain matches Account website domain) is not supported natively.

For true fuzzy cross-object dedup at volume, third-party tools (DemandTools, Cloudingo, Plauti) are the standard recommendation.

---

## Common Patterns

### Pre-Import Normalization + Data Import Wizard

**When to use:** CSV-based list imports from trade shows, marketing events, or vendor lists where email is present but data quality varies.

**How it works:**

1. Before uploading to Salesforce, run the CSV through a normalization script or spreadsheet formula:
   - Lowercase and trim all email addresses.
   - Standardize phone numbers to E.164 format.
   - Strip common company suffixes ("Inc.", "LLC", "Ltd") from Company field before import if exact matching will be used.
2. Remove exact-email duplicates within the import file itself before uploading (VLOOKUP or `pandas.drop_duplicates` on Email).
3. Use Data Import Wizard with Email as the match field and "Update existing records" mode. This performs an exact-match upsert on Email — records with matching email are updated rather than inserted as new.
4. After import, run a SOQL query to find leads with no email that were inserted without dedup protection. Route these to a data steward for manual review.

**Why not skip normalization:** The Data Import Wizard's exact-match on Email will miss `John@example.com` vs. `john@example.com` unless email is lowercased. Without stripping suffixes, "Acme Inc." and "Acme" are treated as different companies.

### Apex Trigger Post-Insert Duplicate Check for Web-to-Lead

**When to use:** The org receives leads via Web-to-Lead or API, Duplicate Rule blocking does not apply to this channel, and the business requires real-time duplicate detection and routing.

**How it works:**

1. Write an after-insert Apex trigger on Lead.
2. In the trigger, call `Datacloud.DuplicateRule.findDuplicates()` to detect whether the new lead matches existing leads or contacts.
3. If a match is found above confidence threshold: set a custom `Duplicate_Status__c` field, create a Task for the owning rep, or — for automated programs — invoke a Flow to auto-assign the record to a dedup queue.
4. Do not auto-merge from an after-insert trigger: `Database.merge()` in a trigger context that fired on insert can cause recursive trigger execution and governor limit issues. Queue merges to a batch job instead.

```apex
trigger LeadDuplicateCheck on Lead (after insert) {
    List<SObject> newLeads = new List<SObject>(Trigger.new);
    Datacloud.FindDuplicatesResult[] results =
        Datacloud.DuplicateRule.findDuplicates(newLeads);

    List<Lead> toUpdate = new List<Lead>();
    for (Integer i = 0; i < results.size(); i++) {
        Integer matchCount = 0;
        for (Datacloud.DuplicateResult dr : results[i].getDuplicateResults()) {
            matchCount += dr.getMatchResults().size();
        }
        if (matchCount > 0) {
            Lead l = new Lead(Id = Trigger.new[i].Id);
            l.Duplicate_Status__c = 'Potential Duplicate';
            toUpdate.add(l);
        }
    }
    if (!toUpdate.isEmpty()) {
        update toUpdate;
    }
}
```

**Why not use a Flow trigger alone:** Flow duplicate detection using the standard Duplicate Rule action works for record-created flows, but the "Block" action in Flow context also does not prevent the insert if the lead was created via API or Web-to-Lead. The Apex approach gives programmatic control over the response.

### Alert-Mode Duplicate Rule + Duplicate Record Set Review Queue

**When to use:** The org wants to capture all suspected duplicates for human review without blocking any lead creation (e.g., for marketing orgs where every lead must be captured).

**How it works:**

1. Set all active Lead Duplicate Rules to "Alert" action (not "Block").
2. Enable "Report" on the rule — this creates a Duplicate Record Set for every flagged record.
3. Create a List View or Report on Duplicate Record Sets filtered to Lead object.
4. Assign a data steward or use a Flow to route high-confidence duplicates (e.g., exact email match) to a dedup queue automatically.
5. Set up a weekly Duplicate Jobs run (if available in the org's edition) to surface existing duplicates that predate the rule.

**Why not Block mode:** Block mode prevents data entry through the standard UI but silently fails for Web-to-Lead, API inserts, and Apex DML unless the calling code explicitly checks the `AllowSave` duplicate rule options. Alert-mode with a review queue captures everything without losing leads.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| CSV import, email present, <50K records | Data Import Wizard with Email match field + pre-normalization | Simple, no-code, sufficient for exact email dedup |
| CSV import, no reliable email, name+company matching needed | External pre-matching (Python/Excel) then upload pre-deduped file | DIW does not support multi-field fuzzy matching |
| Web-to-Lead receiving duplicates | Alert-mode Duplicate Rule + after-insert Apex or Flow for routing | Blocking rules do not stop Web-to-Lead inserts |
| API-based lead integration creating duplicates | After-insert Apex trigger calling findDuplicates() | Integration code bypasses blocking rules |
| Leads matching existing Contacts before conversion | Standard Lead-to-Contact Matching Rule (Alert mode) + review queue | Native cross-object detection, manual or Flow-based resolution |
| Lead-to-Contact fuzzy dedup at volume (>500K contacts) | Third-party tool (DemandTools or Cloudingo) | Native rules have performance impact and algorithm limitations at this scale |
| Web form spam or bot-generated leads | Lead Assignment Rule to quarantine queue + Apex blacklist check | Dedup rules are not designed for spam filtering |

---

## Recommended Workflow

1. **Identify the data entry channel** — determine whether leads are coming from CSV file imports, Web-to-Lead forms, API/integration sync, or a combination. Each channel has different dedup capabilities. Document the channel and estimated volume.
2. **Audit existing Duplicate and Matching Rules** — check Setup > Duplicate Rules and Matching Rules for the Lead object. Confirm whether the Standard Lead Matching Rule is active, whether any rule is set to Block vs. Alert, and whether the Lead-to-Contact rule is enabled. Note how many of the 5-active-rule slots are consumed.
3. **Design the matching and dedup strategy per channel** — for CSV imports, choose the Data Import Wizard dedup field and plan a pre-import normalization step. For Web-to-Lead or API, confirm that Alert mode is configured and design an Apex trigger or Flow to handle post-insert routing. For cross-object matching, determine whether native Lead-to-Contact rules are sufficient or whether third-party tooling is required.
4. **Implement and test in sandbox** — deploy matching rule and duplicate rule configuration changes, any Apex trigger, and any Flow. Test with sample records that represent real-world data quality (missing email, name variants, different phone formats). Confirm that Duplicate Record Sets are created as expected for Alert-mode rules.
5. **Execute the import or enable the channel** — run the CSV import or activate the Web-to-Lead form. For imports, review the post-import duplicate summary from the wizard and run a SOQL query on `DuplicateRecordItem` to assess how many flagged records require review.
6. **Work the Duplicate Record Set queue** — assign the Duplicate Record Set list view to a data steward. Merge or discard flagged records. For automated programs, configure a scheduled Flow or Apex batch to auto-merge high-confidence duplicates (exact email match) and route low-confidence ones to a queue.
7. **Establish ongoing prevention controls** — after the import cleanup is complete, confirm that Duplicate Rules are active and set to Alert or Block as appropriate. Schedule a recurring Duplicate Jobs run (if available) to catch drift. Document the dedup field choice and rule configuration for future imports.

---

## Review Checklist

- [ ] Duplicate Rule action confirmed (Alert vs. Block) and Web-to-Lead bypass behavior understood
- [ ] Data Import Wizard dedup field chosen and pre-import normalization completed for the import file
- [ ] Standard Lead Matching Rule active and field coverage reviewed (Email, Name, Phone, Company)
- [ ] Lead-to-Contact Matching Rule evaluated — active if cross-object detection is needed
- [ ] Apex trigger or Flow in place for Web-to-Lead or API channels where blocking rules do not apply
- [ ] Duplicate Record Set list view or report configured and assigned to a data steward
- [ ] Post-import SOQL query run on `DuplicateRecordItem` to confirm flagging behavior
- [ ] Ongoing Duplicate Jobs or scheduled scan configured to prevent future drift

---

## Salesforce-Specific Gotchas

1. **Blocking Duplicate Rules do not block Web-to-Lead or API inserts** — a Duplicate Rule with action "Block" will evaluate and create a Duplicate Record Set but will not prevent the record from being inserted when the lead arrives via Web-to-Lead POST, REST API, or Apex DML. This silently creates duplicates that the admin believes are being blocked.

2. **Data Import Wizard dedup is single-field exact match only** — practitioners assume the wizard uses the same fuzzy matching as the Standard Matching Rule. It does not. Choosing "Name" as the match field performs a case-insensitive exact match on the full name string. Missing email addresses result in those records always being inserted as new.

3. **5 active Duplicate Rules per object is a hard limit** — attempting to activate a sixth Duplicate Rule on Lead will fail. Orgs with managed packages that include dedup rules may hit this limit unexpectedly. Audit active rules before designing new ones.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Matching rule and duplicate rule configuration spec | Which rules to enable, field coverage, action (Alert/Block), and active rule slot inventory |
| Pre-import normalization script or spreadsheet formula | Python or Excel steps to normalize email, phone, and company before CSV upload |
| Apex after-insert trigger for post-insert duplicate detection | Trigger calling `Datacloud.DuplicateRule.findDuplicates()` and setting a status field |
| Duplicate Record Set list view config | List view on `DuplicateRecordSet` filtered to Lead, for data steward review queue |
| Post-import SOQL query set | Queries on `DuplicateRecordItem` and `Lead` to confirm dedup coverage after import |

---

## Related Skills

- admin/duplicate-management — standard Duplicate Management UI setup, matching rule configuration, and duplicate rule design. Use this skill for the foundational rule configuration before designing import-specific workflows.
- data/large-scale-deduplication — for batch merge execution of identified duplicate pairs at volume (>10K records). Use after this skill has identified duplicates.
- data/record-merge-implications — field resolution rules, child record re-parenting behavior, and merge semantics for individual Lead merges.
- data/data-quality-and-governance — broader data quality framework, validation rules, and governance controls that complement lead dedup.
