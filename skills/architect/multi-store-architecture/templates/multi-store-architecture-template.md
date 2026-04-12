# Multi-Store Architecture — Work Template

Use this template when designing or reviewing a multi-store Commerce architecture for B2B, D2C, or SFCC deployments.

---

## Scope

**Skill:** `multi-store-architecture`

**Request summary:** (describe what the stakeholder asked for)

**Platform type:**
- [ ] Org-based B2B Commerce
- [ ] Org-based D2C Commerce
- [ ] Salesforce Commerce Cloud (SFCC / Business Manager)
- [ ] Hybrid

**Number of stores required:** ___

**Reason for multiple stores:** (regional brand, currency boundary, buyer segment, regulatory, other)

---

## Prerequisites Verified

- [ ] **Platform identity confirmed** — org-based B2B/D2C vs. SFCC
- [ ] **Org multi-currency status** — enabled / not enabled / not applicable (SFCC)
  - If not enabled and multi-currency is needed: enable BEFORE proceeding
- [ ] **Commerce edition confirmed** — B2B Commerce or D2C Commerce license in place
- [ ] **SFCC realm structure confirmed** (SFCC only) — same realm or cross-realm

---

## Store Inventory

| Store Name | Region | Currency | Default Language | Buyer Segment |
|---|---|---|---|---|
| (store 1) | | | | |
| (store 2) | | | | |
| (store 3) | | | | |

---

## Catalog Architecture Decision

**Catalog pattern chosen:**
- [ ] Single shared product catalog (recommended default)
- [ ] Separate product catalogs (justify below)

**Justification if separate catalogs:** (describe why product universes are genuinely disjoint)

**Product catalog name(s):**

| Catalog Name | WebStore(s) Using It | Storefront Catalog Name |
|---|---|---|
| | | |

---

## Per-Store Configuration Plan

### Store: ___________________

**WebStore Name:**
**Currency:**
**Default Language:**
**WebStoreCatalog linked to:**

**Buyer Groups:**
| Buyer Group Name | Accounts Assigned | Price Book |
|---|---|---|
| | | |

**Entitlement Policy:**
- Policy name:
- Products included/excluded:
- Validation plan (how we confirm isolation):

**Localization:**
- Languages supported:
- Translation records needed (ProductLocalization, CategoryLocalization):

---

### Store: ___________________ (copy block per store)

---

## Multi-Currency Configuration

- [ ] Org multi-currency enabled (date / confirmation)
- Currencies activated:
  - [ ] USD
  - [ ] EUR
  - [ ] GBP
  - [ ] Other: ___

**Price book per currency:**
| Price Book Name | Currency | Store(s) Using It |
|---|---|---|
| | | |

**Cart currency strategy:**
- How is buyer's store/currency determined at session start?
- What happens if buyer needs to switch currency? (expected: new cart / store re-selection)

---

## SFCC-Specific Configuration (if applicable)

- [ ] Master catalog defined in Business Manager
- [ ] Storefront catalog per site created and assigned
- [ ] Per-site currency and locale set in Site Preferences
- [ ] Cross-realm sync pipeline defined (if applicable)

---

## Validation Plan

- [ ] Buyer in Store A cannot access Store B products via direct URL or API
- [ ] Store A buyer sees Store A pricing; Store B buyer sees Store B pricing
- [ ] Language displays correctly per store locale setting
- [ ] Cart currency matches store default currency
- [ ] No mid-session currency switch scenarios possible in current UX design

---

## Known Risks and Mitigations

| Risk | Likelihood | Mitigation |
|---|---|---|
| Entitlement misconfiguration exposes cross-store products | Medium | Validation test: access Store B products as Store A buyer before go-live |
| Multi-currency not enabled before price book build | Low (if caught here) | Enable org multi-currency in Step 0 |
| SFCC cross-realm catalog sync not in scope | Confirm with team | Define API-based sync pipeline if cross-realm required |

---

## Notes and Deviations

(Record any deviations from the standard shared-catalog pattern and the reason for each.)
