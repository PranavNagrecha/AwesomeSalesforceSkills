# Marketing Cloud Data Sync — Work Template

Use this template when configuring, diagnosing, or extending Marketing Cloud Connect Synchronized Data Sources for a specific project or campaign requirement.

## Scope

**Skill:** `marketing-cloud-data-sync`

**Request summary:** (describe the sync requirement — e.g., "configure Contact and Account sync for Q3 ABM campaign," "diagnose missing lead fields in MC," "add CampaignMember object to existing sync")

---

## Context Gathered

Answer these before starting any sync configuration or diagnosis work:

- **MC Connect status:** Is Marketing Cloud Connect installed and is the Salesforce Connector active in Marketing Cloud Setup > Platform Tools > Apps > Salesforce Integration?
  - [ ] Yes — proceed
  - [ ] No — stop; resolve MC Connect setup before continuing (see `admin/marketing-cloud-connect` skill)

- **Connected user FLS:** Does the MC Connect connected user have read access to all fields intended for sync?
  - Connected user profile/permission set: _______________
  - FLS verified for target fields: [ ] Yes / [ ] Not checked

- **Objects to sync:** List each CRM object and the intended purpose in Marketing Cloud:
  | Object | MC Use Case | Approx. Field Count Needed |
  |--------|-------------|---------------------------|
  | Contact | Send audience / personalization | ___ |
  | Lead | (if applicable) | ___ |
  | Account | Account name, industry personalization | ___ |
  | (other) | | |

- **Field count check:** For each object, is the needed field count at or below 250?
  - [ ] Yes, all objects under 250 fields
  - [ ] No — prioritize and reduce field selection before proceeding

- **Unsupported fields identified:** Are any of the target fields encrypted (Shield), binary, or rich text?
  - Fields to exclude: _______________
  - Shadow field workaround planned: [ ] Yes / [ ] N/A

- **Sync mode:** What is the maximum acceptable data latency for the send use case?
  - [ ] Near-real-time (use Automatic/Triggered sync)
  - [ ] Up to 15 minutes (use Scheduled sync)
  - [ ] Longer acceptable (use Scheduled with wider interval)

---

## Sync Configuration Record

Document the sync configuration for each object:

### Object: _______________

- **Sync mode:** Automatic / Scheduled (circle one)
- **Total fields selected:** _____ (must be ≤ 250)
- **Fields explicitly excluded (with reason):**
  - `FieldName__c` — encrypted / binary / rich text / out of cap / not needed for sends
  - _______________
- **SDE name in Marketing Cloud:** `_______________`
- **Last verified field count in SDE:** _____ columns (post-sync audit)

---

## Contact Builder Relationship Map

For each SDE that needs to feed a send audience, document the relationship:

| SDE Name | Sendable DE Name | Join Key (SDE field) | Join Key (Sendable DE field) | Relationship Type |
|----------|-----------------|----------------------|------------------------------|-------------------|
| Contact_Salesforce | Sendable_Contacts | ContactID | ContactKey | One-to-one |
| Account_Salesforce | Sendable_Contacts | Id | AccountId | Many-to-one |
| (other) | | | | |

**Contact Builder relationship verified in Data Designer:** [ ] Yes / [ ] Pending

---

## Approach

Which pattern from SKILL.md applies?

- [ ] **SDE-to-Sendable DE Join** — configuring a new sync pipeline for a campaign
- [ ] **Sync Failure Diagnosis** — records missing or SDE is stale
- [ ] **Field selection audit** — checking for 250-field cap issues
- [ ] **New object onboarding** — adding a CRM object not previously synchronized

Describe any deviation from the standard pattern and why:

_______________

---

## Diagnosis Checklist (for sync failure scenarios)

If records are missing from the SDE or the SDE appears stale, work through in order:

- [ ] Check sync status in Contact Builder > Synchronized Data Sources (last sync time, error indicators)
- [ ] Compare SDE column list to intended field selection (check for silent 250-field exclusion)
- [ ] Check for field type mismatches (CRM field type changed after sync was configured?)
- [ ] Check for deleted CRM fields still present in the sync field mapping — remove them
- [ ] Check Salesforce API limit consumption (Setup > System Overview > API Requests)
- [ ] Verify connected user FLS for each missing field
- [ ] If record counts are wrong and all above checks pass — trigger incremental sync, wait one cycle, recheck before considering full sync

---

## Review Checklist

Tick each item before marking this sync configuration complete:

- [ ] MC Connect installed and Salesforce Connector active in MC Setup
- [ ] All synchronized objects configured in Contact Builder > Synchronized Data Sources
- [ ] Field selections at or below 250 fields per object
- [ ] Post-sync column list audit completed — no unexpected missing fields
- [ ] Encrypted, binary, and rich text fields excluded from all sync mappings
- [ ] Contact Builder relationships defined — each SDE linked to the appropriate sendable DE via subscriber key
- [ ] Sync mode (Automatic vs Scheduled) documented and appropriate for the use case
- [ ] Test send or preview run — personalization fields from SDE resolve correctly
- [ ] Sync failure triage completed if any issues encountered

---

## Notes

(Record any deviations from standard pattern, outstanding decisions, or follow-up items)

_______________
