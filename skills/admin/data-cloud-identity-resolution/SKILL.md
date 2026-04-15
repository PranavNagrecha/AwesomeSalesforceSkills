---
name: data-cloud-identity-resolution
description: "Use this skill when configuring or troubleshooting Data Cloud identity resolution rulesets — matching rules, reconciliation rules, unified profiles, and cross-device identity linking. Trigger keywords: identity resolution ruleset, unified individual, match rule, reconciliation rule, unified profile, cross-device identity, Data Cloud deduplication, cluster creation. NOT for CRM duplicate management (Duplicate Rules / Matching Rules on standard objects), and NOT for Experience Cloud or Salesforce Identity login deduplication."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Performance
  - Reliability
tags:
  - data-cloud
  - identity-resolution
  - unified-profile
  - match-rules
  - reconciliation-rules
  - customer-data-platform
inputs:
  - "Data Cloud org with ingested DMO data (Individual, Contact Point Email/Phone/Address, Device, and/or Party Identification DMOs mapped)"
  - "Business requirement describing which identity attributes to match on (email, phone, name, address, device ID, etc.)"
  - "Clarification on whether real-time resolution is needed or batch nightly runs are acceptable"
  - "Confirmation of how many identity resolution rulesets already exist in the org (hard limit: 2)"
  - "Multi-data-space context: which data space(s) the ruleset should be scoped to"
outputs:
  - "Configured identity resolution ruleset with match rules and reconciliation rules"
  - "Unified Individual profiles created across source data streams"
  - "Documented match-rule type selections with rationale (Exact vs. Fuzzy vs. Normalized vs. Compound)"
  - "Reconciliation rule configuration per attribute with selected source precedence"
  - "Checklist confirming ruleset ID lock-in, run frequency limits, and real-time vs. batch constraints"
triggers:
  - "configure identity resolution ruleset in data cloud"
  - "set up match rules for unified profiles"
  - "unified individual not matching across data sources"
  - "reconciliation rules for data cloud identity"
  - "cross-device identity linking data cloud"
  - "data cloud deduplication ruleset setup"
  - "identity cluster creation not working correctly"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-15
---

# Data Cloud Identity Resolution

This skill activates when a practitioner needs to configure, modify, or diagnose identity resolution rulesets in Data Cloud — the platform capability that merges records from different data sources into a single Unified Individual profile using match rules and reconciliation rules. It covers ruleset design, match rule type selection, reconciliation rule behavior, cross-device identity, and the hard org limits that make these configurations difficult to reverse.

---

## Before Starting

Gather this context before working on anything in this domain:

- **How many identity resolution rulesets already exist in the org?** Navigate to Data Cloud Setup > Identity Resolution. The hard platform limit is 2 rulesets per org, counting any auto-created ruleset from the Starter Data Bundle. This limit cannot be raised with a support case — it is a hard constraint.
- **Have all required DMOs been mapped?** Identity resolution requires source records to be mapped to the Individual DMO (for person identity) and at least one Contact Point DMO (Email, Phone, or Address) before match rules can reference those fields. Run the Data Cloud health check or inspect the data stream mappings.
- **Is the ruleset ID known?** Every ruleset is assigned a 4-character ID at creation time. This ID cannot be changed after the ruleset is created. It is embedded in downstream references, including activation targets and segmentation filters.
- **What is the recency and completeness of source data?** Reconciliation rules use field-level recency (most-recently-updated record wins) or priority-based source precedence. If source data has irregular update timestamps, the reconciliation output may not reflect the most trusted value.
- **Is real-time resolution required?** Only Exact and Exact Normalized match methods are evaluated in real-time processing. Fuzzy matching (first name only) is batch-only. This distinction affects resolution latency SLAs.

---

## Core Concepts

### Identity Resolution Rulesets

An identity resolution ruleset is a named configuration that defines how Data Cloud identifies records from different sources as belonging to the same real-world individual. The ruleset contains:

1. **Match rules** — criteria that compare field values across Individual and Contact Point DMO records to determine whether two records represent the same person.
2. **Reconciliation rules** — field-level rules that decide which source value to use when two matched records have different values for the same attribute (e.g., two different phone numbers).

The ruleset runs on a schedule. When it runs, it creates or updates **Unified Individual** records — the merged profiles that downstream segmentation, activation, and Agentforce grounding use. The org-level hard limit is **2 identity resolution rulesets total** across all data spaces in the org. This includes any ruleset auto-created when the Starter Data Bundle is provisioned. Plan the ruleset strategy before any configuration work begins.

The 4-character ruleset ID is assigned at creation and is **immutable**. Any reference to a ruleset in activation targets, data actions, or journey builder configurations uses this ID. If a ruleset must be replaced, the old one must be deactivated and a new one created — but with only 2 total slots available, this is a high-stakes decision.

### Match Rule Types

Data Cloud supports four match rule types. Selecting the wrong type for a given attribute causes either false positives (merging people who should not be merged) or missed merges (failing to unify records that are the same person):

- **Exact** — Case-insensitive exact string comparison. Appropriate for identifiers like Salesforce Contact ID, loyalty member ID, or hashed email. The safest option but requires the field values to be identical across sources.
- **Fuzzy** — Partial-match algorithm for first names only (not last names, email, or phone). Designed to handle common name variations (e.g., "Bob" vs. "Robert"). **Fuzzy matching is batch-only** — it is not evaluated in real-time resolution jobs. Using fuzzy in a ruleset that must support real-time identity resolution will silently degrade performance.
- **Normalized (Email, Phone, Address)** — Pre-processes field values to remove formatting variation before comparing. Phone normalization strips dashes, spaces, and country codes. Email normalization lowercases the address. Address normalization applies USPS-style standardization. In real-time contexts, Exact Normalized is supported; full address normalization is batch-only.
- **Compound** — Combines multiple fields (e.g., first name + last name + zip code) into a single match rule. Reduces false positives when no single identifier is reliable. All individual fields within a Compound rule must match for the rule to fire.

Match rules are evaluated using **OR logic by default** — if any single rule fires, the records are considered a match. The order of rules in the ruleset affects which record "wins" as the primary when reconciliation runs.

### Reconciliation Rules

Reconciliation rules operate at the field level on the Unified Individual profile. When two matched records have different values for the same field, the reconciliation rule determines which value to store in the Unified Individual.

Available strategies:
- **Most Recent** — Use the value from the record with the most recent `LastModifiedDate` (or equivalent). Requires the source to populate this field reliably.
- **Source Priority** — Define a ranked list of data sources. The highest-priority source's value wins regardless of timestamp. Useful when one source (e.g., CRM) is more trusted than others.
- **Most Frequent** — Use the value that appears most often across matched records. Less common; useful for stable attributes like preferred name.

**Critical behavior:** Changing a reconciliation rule after the ruleset has run does not update existing Unified Individual clusters incrementally. It triggers a **full re-run** of the entire ruleset. For orgs with large data volumes, this can take hours and temporarily causes downstream segments and activations to reference stale unified profiles. Plan reconciliation rule changes during low-traffic windows.

### Cross-Device Identity

The Device DMO enables Data Cloud to link a physical person (Individual) to their devices (cookies, mobile device IDs, IDFA, GAID). Device DMO records must include:
- A device identifier field mapped to the Device DMO `Device Id` field.
- A foreign key back to the Individual DMO (typically via Contact Point linking or direct `Individual Id` mapping).

Cross-device match rules use the Device DMO as a match surface. When two source records share the same device identifier, they can be unified under a single Individual even if no email or phone is present. Device-based matching uses Exact match type; fuzzy or normalized matching is not supported on Device DMO fields.

---

## Common Patterns

### Pattern 1: Email-Primary Unified Profile Across CRM and Commerce

**When to use:** An org ingests Salesforce CRM Contact records and an external commerce platform's customer records into Data Cloud and needs to unify them into a single Unified Individual per real person.

**How it works:**
1. Confirm both CRM and commerce data streams have mapped the `Email` field to the Contact Point Email DMO's `Email Address` field, and both have a foreign key back to the Individual DMO.
2. In Identity Resolution Setup, create a new ruleset. Assign a meaningful 4-character ID (e.g., `EMLP`) — remember this is permanent.
3. Add a match rule: type = **Normalized**, attribute = Contact Point Email > Email Address. This handles case variations and whitespace.
4. Set reconciliation rules: for `First Name` and `Last Name`, use **Source Priority** with CRM ranked above commerce (CRM data is more likely to reflect legal name). For `Email Address`, use **Most Recent** to capture email updates from either source.
5. Save and run the ruleset. Inspect the Unified Individual record count and compare to the pre-resolution Individual count to validate the merge rate.
6. If the merge rate is unexpectedly low, audit the Contact Point Email mappings in both data streams — a common cause is one stream mapping to the DMO field `Email` instead of `Email Address`.

**Why not the alternative:** Using an Exact match on raw email without Normalization misses merges where one source stores `User@Example.com` and another stores `user@example.com`. The Normalized type handles this.

### Pattern 2: Multi-Attribute Compound Match to Reduce False Positives

**When to use:** An org has a high rate of false-positive merges (strangers being unified) when using only email or phone as the match key — common in B2B orgs where many employees share a company email domain, or in consumer orgs where family members share a phone number.

**How it works:**
1. In the ruleset, add a **Compound** match rule using Individual > First Name (Fuzzy) + Individual > Last Name (Exact) + Contact Point Address > Postal Code (Exact).
2. **Note:** Because this rule uses Fuzzy on First Name, it will only run in batch mode, not real-time.
3. Run the ruleset and compare precision metrics: sample 50 Unified Individual clusters and manually verify that matched records represent the same real person.
4. If false positives remain, add a fourth attribute to the Compound rule or switch First Name from Fuzzy to Exact if the first-name variation is not the actual cause of missed merges.
5. If false negatives (missed merges) increase, reconsider whether the address postal code is consistently populated across all sources — null values in a Compound field cause the rule to skip those records.

**Why not the alternative:** Using separate single-attribute match rules for name and postal code with OR logic merges any person sharing the same last name OR the same postal code — far too broad.

### Pattern 3: Ruleset Slot Conservation in Multi-Business-Unit Orgs

**When to use:** An org houses two or more business units in a single Data Cloud org and each BU wants its own identity resolution configuration.

**How it works:**
1. Recognize the hard 2-ruleset limit immediately. Do not attempt to create a third ruleset — the UI will block it.
2. Evaluate whether the BUs can share a single ruleset with shared match rules. If BUs have non-overlapping customer bases (no shared email addresses), a shared ruleset produces zero false-positive cross-BU merges.
3. If the BUs have distinct identity attributes (e.g., one uses email, one uses loyalty ID), use a Compound rule per BU within the same ruleset. Or use a single match rule per attribute type, since OR logic means a record only needs to match on one attribute.
4. If the BUs genuinely require separate reconciliation logic (different source priority rankings), escalate to Salesforce architecture review — the only option is separate Data Cloud orgs or separate data spaces with a single shared ruleset.
5. Document the 4-character ruleset ID for each ruleset in the org's architecture decision record immediately after creation.

**Why not the alternative:** Assuming the limit is configurable or can be raised via support wastes planning time. The 2-ruleset limit is a hard platform constraint as of Spring '25.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Email is the primary identity attribute, sources may have mixed casing | Normalized match on Contact Point Email > Email Address | Handles `User@Domain.com` vs `user@domain.com` without Fuzzy overhead |
| Real-time identity resolution is required (< 1 hour latency) | Use only Exact or Exact Normalized match rules | Fuzzy and full address normalization are batch-only; using them silently degrades real-time performance |
| Two sources have high false-positive merge rate on single attribute | Compound match rule combining 2–3 attributes | OR logic on single-attribute rules is too broad; Compound requires ALL fields to match |
| Reconciliation source trust differs by BU or product line | Source Priority reconciliation ranked by data source | Most Recent is unreliable when source timestamps are inconsistent or backfilled |
| First name varies across sources (Bob/Robert, Liz/Elizabeth) | Fuzzy match on Individual > First Name within Compound rule | Handles common English name variations; accept batch-only limitation |
| Org has consumed 1 of 2 ruleset slots | Document carefully before creating a second ruleset; validate no third ruleset creation is expected | Hard limit cannot be raised; losing a slot to a test ruleset blocks production needs |
| Device ID is available but no email/phone | Exact match on Device DMO > Device Id | Device-based matching uses Exact type; fuzzy/normalized not supported on Device DMO |
| Reconciliation rule must be changed post-run | Schedule the change during a low-traffic window | Change triggers full re-run of all clusters, not incremental; downstream segments reference stale profiles during re-run |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Audit existing rulesets and org slot usage.** Navigate to Data Cloud Setup > Identity Resolution and count existing rulesets, including any auto-created by the Starter Data Bundle. If both slots are occupied, stop and escalate before attempting to create a new ruleset.

2. **Verify DMO mappings are complete.** Confirm that the data streams contributing to identity resolution have mapped fields to the Individual DMO (at minimum: `Individual Id`, `First Name`, `Last Name`) and to at least one Contact Point DMO (Contact Point Email, Phone, or Address). Incomplete mappings silently prevent match rules from finding candidates.

3. **Select match rule types based on resolution latency requirements.** If real-time resolution is required, use only Exact or Exact Normalized match types. If batch nightly resolution is acceptable, Fuzzy on first name and full address Normalized are available. Document the rationale for each match rule type selected.

4. **Assign the ruleset ID thoughtfully before saving.** Choose a meaningful 4-character alphanumeric ID (e.g., `EMLP` for email-primary, `CMPS` for compound-name) and document it in the architecture decision log. The ID cannot be changed after the ruleset is saved.

5. **Configure reconciliation rules field by field.** For each Unified Individual attribute that will be populated: select Source Priority when one source is more trusted; select Most Recent when sources are equally trusted but update timestamps are reliable; select Most Frequent only for stable attributes like preferred name. Never leave reconciliation rules at default without reviewing them — default behavior varies by org configuration.

6. **Run the ruleset and validate cluster quality.** After the first run completes, sample 50–100 Unified Individual clusters. For each: verify that all merged source records represent the same real-world person. If false positives exist, tighten the match rules. If false negatives exist (known duplicates not merged), check that the linking Contact Point DMO fields are populated on both records.

7. **Document the configuration in the org's architecture decision record.** Record: ruleset ID, match rule types and rationale, reconciliation rule settings, slot consumption (1/2 or 2/2), and any known batch-vs-real-time constraints. This documentation is required before the skill run is considered complete.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Org ruleset slot count confirmed (1/2 or 2/2) before creation
- [ ] All contributing data streams have Individual DMO and Contact Point DMO fields mapped
- [ ] Match rule types documented with real-time vs. batch rationale
- [ ] Ruleset 4-character ID recorded in architecture decision log (immutable after save)
- [ ] Reconciliation rules reviewed field by field — not left at defaults
- [ ] Post-run cluster quality sampled: 50+ Unified Individual records spot-checked for false positives and false negatives
- [ ] If reconciliation rule was changed on an existing ruleset: full re-run scheduled during a low-traffic window
- [ ] Manual run frequency: no more than 4 manual runs per 24 hours per ruleset (platform limit)
- [ ] Cross-device matching: Device DMO records have `Device Id` and `Individual Id` foreign key populated if device identity is in scope

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **2-Ruleset Org Limit Counts the Starter Data Bundle Ruleset** — When an org provisions the Starter Data Bundle, Data Cloud auto-creates one identity resolution ruleset. This consumes one of the two available slots. Practitioners who do not know this discover they can only create one additional ruleset, not two. Always audit the existing ruleset list before planning multi-ruleset configurations.

2. **Fuzzy Match Is Batch-Only, Not Real-Time** — Fuzzy match on first name is not evaluated during real-time identity resolution processing. If a ruleset contains any Fuzzy match rule, the real-time resolution path silently skips that rule and only evaluates Exact and Exact Normalized rules. This means real-time profiles may be less unified than batch profiles, causing inconsistent Unified Individual counts depending on when a downstream process runs.

3. **Changing a Reconciliation Rule Triggers a Full Re-Run** — Modifying any reconciliation rule setting on an existing, already-run ruleset does not update existing clusters incrementally. It triggers a complete re-computation of all clusters in the ruleset. For orgs with millions of Individual records, this can take hours. During the re-run, downstream segmentation and activation targets reference the previous (stale) Unified Individual values. Schedule reconciliation rule changes during low-traffic windows and communicate the latency to dependent teams.

4. **Ruleset ID Is Immutable After Creation** — The 4-character ID assigned to a ruleset at creation time cannot be changed. It is referenced in activation targets, data actions, and API calls. If the wrong ID was chosen (e.g., a test ID), the only remediation is to delete the ruleset (freeing the slot) and create a new one with the correct ID — but deletion requires deactivating all downstream references first.

5. **Manual Run Frequency Is Limited to 4 Per 24 Hours** — Each identity resolution ruleset can be triggered manually at most 4 times within a 24-hour period. Automated scheduled runs do not count against this limit, but attempts to trigger manual runs to test configuration changes after the 4th trigger will silently fail or return an error in the UI. Do not plan iterative same-day testing loops that exceed this limit.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Identity Resolution Ruleset | Named configuration in Data Cloud Setup containing match rules and reconciliation rules |
| Unified Individual Records | Merged DMO records combining data from all matched source records into a single identity |
| Architecture Decision Record Entry | Documentation of ruleset ID, match rule types, reconciliation settings, and slot consumption |
| Cluster Quality Sample Report | Spot-check of 50+ Unified Individual clusters confirming merge accuracy |

---

## Related Skills

- `data/data-cloud-data-streams` — Ensure data streams are mapped to Individual and Contact Point DMOs before identity resolution can be configured
- `architect/data-cloud-architecture` — Covers end-to-end Data Cloud architecture patterns including multi-ruleset design in shared orgs
- `data/data-cloud-ingestion-api` — Ingestion API pattern for pushing identity attributes (email, phone, device ID) into Data Cloud from external systems
- `admin/data-cloud-provisioning` — Org setup prerequisites including Starter Data Bundle configuration that affects ruleset slot availability
