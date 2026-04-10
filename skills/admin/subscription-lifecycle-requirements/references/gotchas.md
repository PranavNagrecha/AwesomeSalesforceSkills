# Gotchas — Subscription Lifecycle Requirements

Non-obvious Salesforce CPQ platform behaviors that cause real production problems when documenting or implementing subscription lifecycle requirements.

## Gotcha 1: Amendments Never Modify Existing SBQQ__Subscription__c Records

**What happens:** Every amendment action — adding quantity, removing a product, changing quantity — produces new delta `SBQQ__Subscription__c` records. The original subscription records created from the initial contract activation are never updated or deleted. After multiple amendments, a single contract may have dozens of subscription records that together represent the current entitlement state.

**When it occurs:** Any time an amendment quote is activated. The ledger grows with each amendment cycle. This also means that a query like `SELECT Id, SBQQ__Quantity__c FROM SBQQ__Subscription__c WHERE SBQQ__Contract__c = :contractId ORDER BY CreatedDate DESC LIMIT 1` will return the wrong quantity — it returns only the most recent delta, not the total.

**How to avoid:** Requirements must explicitly state the ledger model. Reports and integrations must aggregate all subscription records per product per contract using `SUM(SBQQ__Quantity__c)` grouped by product. Any integration design document that shows a single subscription record per product is incorrect and must be revised. The `SBQQ__AmendedSubscription__c` field on each delta record points back to the record it is modifying, which allows traversal of the change chain.

---

## Gotcha 2: End Dates on Existing Contract Subscription Records Are Immutable

**What happens:** After a contract is activated, the `SBQQ__EndDate__c` field on each child `SBQQ__Subscription__c` record cannot be changed by direct DML or by a subsequent amendment. Attempting to directly update the field either fails silently (if the record is managed by the CPQ package) or produces a trigger validation error.

**When it occurs:** When a business requirement states that a contract needs to be "extended" or "shortened" and the implementation team attempts to edit the end date on the subscription record directly. This also occurs when an administrator tries to adjust the end date after a co-termination calculation they disagree with.

**How to avoid:** Requirements for contract end date changes must be modeled as amendments. To extend a contract, the correct approach is to create an amendment that adds a new subscription line covering the extension period. To shorten a contract, the approach is a cancellation amendment that removes lines as of the new end date. Both approaches create new delta subscription records rather than modifying existing ones, which preserves the audit trail. Requirements that describe "editing the end date" must be revised before development begins.

---

## Gotcha 3: Amendment Pricing Lock Requires a Zero-Out Swap for Price Changes

**What happens:** Existing subscription lines on an amendment quote are priced at the original contracted price, regardless of what the current price book says. If a price book entry is updated to $1,500 after the original contract was signed at $1,200, the amendment quote for that existing line will show $1,200. Changing the price book entry, modifying price rules, or editing the line directly on the amendment quote will not override the locked price for standard subscription lines.

**When it occurs:** Any time the business wants to apply a price increase (or decrease) to a customer's existing subscription before the renewal date. This is common in annual price increase scenarios where the business wants to immediately apply new pricing to all active customers, not wait until renewal.

**How to avoid:** Document this constraint explicitly in requirements. If mid-term repricing is a business requirement, the only standard-CPQ workaround is the zero-out swap: remove the existing line at $0 (generating a $0 cancellation delta record) and add the product as a new line at the new price (generating a new subscription record priced from the current price book, prorated to the co-termination date). This workaround must be scoped as a custom development item — it is not achievable manually at scale without automation. Requirements documents must flag this as a gap and quantify how frequently mid-term repricing occurs to size the custom development effort.

---

## Gotcha 4: Co-Termination Silently Shortens New Subscription Lines

**What happens:** When co-termination is enabled and a new product is added via amendment, CPQ sets the new line's end date to the co-termination date — the earliest end date among all active subscription lines on the contract. If the co-termination date is 2 months away, the new product's first term is 2 months, not 12 months. The customer is billed the prorated 2-month amount, not the annual amount.

**When it occurs:** Any amendment that adds a new product to a contract where some existing subscription lines are approaching their end date. It is especially common on contracts with mixed subscription lengths (e.g., some annual lines, some multi-year lines) or on contracts that were themselves the result of multiple amendments with staggered start dates.

**How to avoid:** Requirements for new product additions must state the expected term and price. Before finalizing any amendment, the co-termination date must be communicated to the account team and the customer so that the prorated charge is not a surprise. Configuration requirements should specify whether co-termination is enabled (for billing simplicity) or disabled (for per-product renewal flexibility), and worked examples with real timeline scenarios must be included in the sign-off documentation.

---

## Gotcha 5: Renewal Quotes Reprice at List, Not at Contracted Price

**What happens:** When CPQ generates a renewal quote, it reprices all lines using the current price book entry — the opposite behavior from amendments. A customer who was contracted at $1,200/year and whose list price is now $1,500/year will receive a renewal quote for $1,500/year unless a `SBQQ__ContractedPrice__c` record exists for the account and product.

**When it occurs:** Any renewal generated without pre-created contracted price records. This is the default behavior and affects all renewals unless the org explicitly manages contracted price records. Businesses that assume "the renewal will come in at the same price as the contract" are frequently surprised to find renewal quotes reflecting current list.

**How to avoid:** Requirements for renewal pricing must explicitly state whether renewal is at list price, at contracted price, or at a negotiated increase percentage. If contracted price renewal is required, requirements must also specify how `SBQQ__ContractedPrice__c` records are created and maintained — manually by a sales ops team, automatically on contract activation by an Apex trigger, or via a batch job. The maintenance plan for contracted price records when list prices change must also be documented, as stale contracted price records will lock renewal quotes to outdated pricing.
