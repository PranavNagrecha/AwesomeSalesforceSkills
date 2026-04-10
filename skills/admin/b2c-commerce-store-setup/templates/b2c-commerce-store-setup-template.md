# B2C Commerce Store Setup — Work Template

Use this template when working on SFCC storefront setup, cartridge configuration, or Business Manager administration tasks.

> **Platform check:** This template is for Salesforce B2C Commerce (SFCC) — Business Manager-based storefronts. If the request involves WebStore, BuyerGroup, or CommerceEntitlementPolicy, use `admin/b2b-commerce-store-setup` instead.

---

## Scope

**Skill:** `b2c-commerce-store-setup`

**Request summary:** (fill in what the user asked for)

**Instance type:** [ ] Sandbox / Development  [ ] Staging  [ ] Production

---

## Context Gathered

Answer these before starting any configuration work:

- **Site ID:** _____________________ (max 32 alphanumeric chars, no spaces)
- **Cartridge path (current):** _____________________
- **Custom cartridges to add/modify:** _____________________
- **Storefront catalog ID:** _____________________
- **Currency:** _____________________  **Primary locale:** _____________________
- **Active promotion count (current):** _____________________ (alert if > 800)
- **Known constraints or limits in play:** _____________________

---

## Cartridge Path

Document the target cartridge path. All custom and integration cartridges must appear to the LEFT of `app_storefront_base`.

```
[custom-cartridges]:[integration-cartridges]:app_storefront_base
```

Proposed path:

```
_____:_____:app_storefront_base
```

Verification: `app_storefront_base` is the rightmost entry: [ ] Yes  [ ] No — fix before proceeding

---

## Site Creation Checklist (new sites only)

- [ ] Site ID defined: _____________________ (validated: alphanumeric, ≤ 32 chars, no spaces)
- [ ] Storefront catalog assigned
- [ ] Currency and primary locale set
- [ ] Cartridge path configured (custom cartridges left of app_storefront_base)
- [ ] Site preferences reviewed (`Merchant Tools > Site Preferences`)
- [ ] Additional locales added if required (`Merchant Tools > Localization`)

---

## Deployment Runbook

For catalog or preference changes, check each step in sequence:

- [ ] Catalog import / data change completed
- [ ] BM import job status: FINISHED
- [ ] Full Search Index rebuild triggered (`Merchant Tools > Search > Search Indexes > Full Rebuild`)
- [ ] Search Index rebuild job status: FINISHED (monitor via `Administration > Operations > Jobs`)
- [ ] Storefront search validated for new/changed products
- [ ] If production: replication job completed AND production search index also rebuilt

---

## Quota Audit

| Resource | Current Count | Threshold | Status |
|---|---|---|---|
| Active promotions | | 1,000 (perf) / 10,000 (hard) | |
| Product line items (test basket) | | 400 (hard) | |
| Replicable custom objects | | 400,000 (hard) | |

Action items from quota audit:
- _____________________

---

## Approach

Which pattern from SKILL.md applies?

- [ ] Custom cartridge installation
- [ ] Search index rebuild after catalog change
- [ ] Promotion hygiene / quota management
- [ ] New site creation
- [ ] Staging-to-production replication
- [ ] Other: _____________________

Rationale: _____________________

---

## Review Checklist

- [ ] Site ID is alphanumeric, ≤ 32 chars, no spaces
- [ ] All custom cartridges are LEFT of app_storefront_base in the path
- [ ] No files modified directly inside app_storefront_base
- [ ] Custom cartridge code uploaded to WebDAV before saving cartridge path
- [ ] Full Search Index rebuild completed after any catalog or preference change
- [ ] Active promotion count below 800 (hard alert: >1,000)
- [ ] Session data writes store only IDs, not serialized full objects
- [ ] Production replication followed by production search index rebuild (if applicable)
- [ ] End-to-end storefront test: browse, search, add-to-basket, checkout flow

---

## Notes

Record any deviations from the standard pattern, environment-specific quirks, or follow-up items:

_____________________
