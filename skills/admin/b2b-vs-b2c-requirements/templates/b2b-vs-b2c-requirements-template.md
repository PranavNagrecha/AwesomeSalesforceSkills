# B2B vs D2C Commerce Requirements — Work Template

Use this template when working on a Salesforce Commerce platform selection decision before any storefront implementation begins.

## Scope

**Skill:** `b2b-vs-b2c-requirements`

**Request summary:** (fill in what the client or user asked for)

---

## 1. Buyer Persona

| Question | Answer |
|---|---|
| Are buyers business entities (Accounts) or individual consumers? | |
| Do multiple contacts within the same organization share a cart or order history? | |
| Are orders placed on behalf of an Account, or by individuals acting independently? | |
| Are order approval workflows or spending limits required at the account level? | |

**Conclusion:** [ ] Business Account buyer (→ B2B Commerce)   [ ] Individual consumer (→ D2C Commerce)   [ ] Both (→ B2B2C hybrid)

---

## 2. Guest Checkout Requirements

| Question | Answer |
|---|---|
| Is anonymous browsing (no login required) needed? | |
| Is guest checkout (purchase without account creation) a firm requirement? | |
| What is the org's Salesforce release version? (Must be Winter '24+ for B2B guest checkout) | |

**Conclusion:** [ ] Guest checkout required   [ ] Guest checkout not required

---

## 3. Pricing and Catalog Segmentation

| Question | Answer |
|---|---|
| Is pricing negotiated per account or account tier (contract pricing)? | |
| Do different buyers need to see different product catalogs? | |
| Is pricing uniform across all buyers (or segment-based without per-account negotiation)? | |

**Conclusion:** [ ] Account-gated pricing/catalog (→ B2B Commerce)   [ ] Uniform/segment pricing (→ D2C Commerce)

---

## 4. License Verification

| License | Active in Org? | Notes |
|---|---|---|
| B2B Commerce | [ ] Yes / [ ] No | Check Installed Packages or WebStore creation dialog |
| D2C Commerce | [ ] Yes / [ ] No | Check Installed Packages or WebStore creation dialog |

**License gap (if any):** (describe any licenses that need to be procured before implementation begins)

---

## 5. Platform Decision

**Recommended platform:**

[ ] B2B Commerce — because: (fill in rationale)

[ ] D2C Commerce — because: (fill in rationale)

[ ] B2B2C Hybrid (two WebStores) — because: (fill in rationale)

**Unmet requirements requiring custom development:** (list any requirements that cannot be satisfied natively by the selected platform)

---

## 6. Follow-On Skills

After this decision is finalized, activate the appropriate implementation skill:

| Next Step | Skill |
|---|---|
| B2B Commerce storefront implementation | admin/b2b-commerce-store-setup |
| Salesforce B2C Commerce (SFCC) setup | admin/b2c-commerce-store-setup |
| Product catalog configuration | admin/commerce-product-catalog |
| Pricing and promotions setup | admin/commerce-pricing-and-promotions |

---

## 7. Review Checklist

- [ ] Buyer persona documented (Account-based vs. individual consumer)
- [ ] Guest checkout requirement confirmed or ruled out
- [ ] Pricing model documented (negotiated/contract vs. uniform)
- [ ] Catalog segmentation needs documented
- [ ] Active licenses verified in org
- [ ] Platform decision recorded with rationale
- [ ] Unmet requirements flagged
- [ ] Follow-on implementation skill identified

---

## Notes

(Record any deviations from the standard decision process, ambiguous requirements, or open questions.)
