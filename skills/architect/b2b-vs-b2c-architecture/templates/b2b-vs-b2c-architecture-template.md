# B2B vs B2C Commerce Architecture — Decision Framework Template

Use this template when an architect or practitioner must evaluate and document the platform architecture decision between Salesforce B2B Commerce (on Core) and Salesforce B2C Commerce (SFCC).

---

## Scope

**Skill:** `b2b-vs-b2c-architecture`

**Project / Client:** (fill in)

**Request summary:** (describe the commerce platform decision being evaluated)

**Date:** (fill in)

---

## 1. Traffic and Scale Requirements

| Metric | Estimate | Notes |
|---|---|---|
| Expected peak concurrent sessions | | Anonymous or authenticated? |
| Expected annual order volume | | |
| Expected peak orders per hour | | |
| Buyer authentication model | Authenticated only / Guest / Mixed | |

**Capacity analysis conclusion:**
> If peak concurrent anonymous sessions exceed ~500 or the storefront targets consumer-scale traffic, SFCC or D2C on Core with CDN must be evaluated. B2B Commerce on Core is appropriate for authenticated B2B account-based workloads.

---

## 2. Buyer Identity and CRM Data Requirements

| Requirement | Needed? | Platform Implication |
|---|---|---|
| Buyers are business accounts in Salesforce CRM | Yes / No | Points to B2B Commerce on Core |
| Contract pricing per account or buyer tier | Yes / No | B2B Commerce on Core (BuyerGroup + Pricebook) |
| Account-gated product catalog | Yes / No | B2B Commerce on Core (CommerceEntitlementPolicy) |
| Real-time account credit limit check at checkout | Yes / No | B2B Commerce on Core (same-org SOQL) |
| Order approval workflow at account level | Yes / No | B2B Commerce on Core (Flow Approval step) |
| Guest / anonymous purchasing required | Yes / No | Points to D2C/SFCC |
| Buyers are individual consumers | Yes / No | Points to D2C/SFCC |

**CRM data dependency assessment:**
(List every piece of CRM data the storefront needs at checkout runtime and note whether it is available natively in each platform option.)

---

## 3. Extensibility Requirements

| Customization Need | B2B Commerce on Core Path | SFCC Path |
|---|---|---|
| Custom pricing logic | Commerce Extension (Apex) | SFRA cartridge + hooks |
| Custom tax calculation | Commerce Extension (Apex) | SFRA cartridge / third-party cartridge |
| Custom shipping rules | Commerce Extension (Apex) | SFRA cartridge |
| Custom checkout step (UI) | Flow Screen Component (LWC) | SFRA controller + ISML template |
| Custom product search ranking | B2B Commerce Search API + LWC | SFCC Einstein Search or cartridge override |
| Headless front end (PWA/mobile) | B2B Commerce Webstore REST API | SCAPI (Shopper Commerce API) |

**Commerce Extensions note:** Commerce Extensions (Winter '24+) apply ONLY to B2B Commerce and D2C Commerce on Core. They do not exist in SFCC.

---

## 4. Integration Surface Analysis

List each external system that must integrate with the commerce platform:

| External System | Data Flow Direction | B2B Commerce on Core Integration | SFCC Integration |
|---|---|---|---|
| Salesforce CRM (Accounts, Contacts) | Storefront reads CRM data | Native (same org) | Requires Salesforce Connector or custom API |
| Salesforce Order Management | Orders → OMS | Native (OrderSummary in same org) | Requires Salesforce Connector for B2C Commerce |
| ERP / inventory system | Storefront reads inventory | Commerce Extension callout or named cred | SFCC inventory import / hook callout |
| Payment processor | Checkout payment | Standard Commerce payment integration | SFCC payment cartridge |
| Tax engine (external) | Checkout tax calc | Commerce Extension callout | SFRA cartridge or hooks |
| PIM | Product data → storefront | Product2 / import API | SFCC catalog import / Management API |
| Personalization platform | Storefront reads segments | LWC + API callout | SCAPI or on-page script |

---

## 5. Team Capability Assessment

| Skill Area | Team Has This? | Platform Requirement |
|---|---|---|
| Apex development | Yes / No | B2B Commerce on Core (Commerce Extensions, triggers) |
| Flow Builder | Yes / No | B2B Commerce on Core (checkout flow customization) |
| LWC development | Yes / No | B2B Commerce on Core (storefront UI) |
| Salesforce DX / SFDX | Yes / No | B2B Commerce on Core (DevOps pipeline) |
| Node.js / JavaScript | Yes / No | SFCC (SFRA cartridges, controllers) |
| SFRA cartridge development | Yes / No | SFCC (checkout and UI customization) |
| Business Manager administration | Yes / No | SFCC (site configuration, promotions, catalog) |
| SFCC deployment tooling (b2c-tools, sgmf-scripts) | Yes / No | SFCC (DevOps pipeline) |

---

## 6. Platform Comparison Summary

| Dimension | B2B Commerce on Core | SFCC | Winner for This Project |
|---|---|---|---|
| Infrastructure | Salesforce org (shared platform) | Dedicated hosted infrastructure | |
| CRM data access | Native (zero-latency) | External integration required | |
| Peak anonymous traffic scale | Platform-limited | Dedicated, CDN-backed | |
| Checkout customization | Flow Builder + Commerce Extensions | SFRA cartridges + hooks | |
| Order data in Salesforce | Native (OrderSummary) | Requires integration | |
| DevOps model | SFDX / Salesforce DX | SFCC tooling / Business Manager | |
| Required team skills | Apex / Flow / LWC | Node.js / SFRA / Business Manager | |
| Licensing | B2B Commerce license | B2C Commerce Cloud license | |

---

## 7. Recommendation

**Selected platform:** (B2B Commerce on Core / SFCC / Hybrid)

**Primary drivers:**
1. (cite the highest-weight factor — e.g., "Real-time CRM data access at checkout with no integration overhead")
2. (cite the second factor)
3. (cite the third factor if applicable)

**Capability gaps accepted:**
(List any requirements the selected platform does not cover natively and how the gap will be addressed — custom build, third-party, or accepted as out of scope.)

| Gap | Disposition |
|---|---|
| (describe gap) | Custom-build / Third-party / Out of scope |

---

## 8. Follow-On Skills

After locking the platform decision, activate the appropriate implementation skills:

- **B2B Commerce on Core selected:** `admin/b2b-commerce-store-setup`
- **SFCC selected:** `admin/b2c-commerce-store-setup`
- **Commerce Extensions in scope (Core only):** `apex/commerce-extensions-development`
- **SFCC + Salesforce CRM integration in scope:** `integration/salesforce-b2c-commerce-connector`

---

## Notes and Open Questions

(Record any assumptions, unresolved questions, or items that could change the recommendation.)

- 
- 
