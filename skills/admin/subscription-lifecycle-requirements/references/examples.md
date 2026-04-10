# Examples — Subscription Lifecycle Requirements

## Example 1: Mid-Term Upgrade Creating a Delta Subscription Record

**Context:** A customer has an active 12-month contract signed on January 1 for 10 seats of a product at $100/seat/month ($1,200/year). On July 1 (month 6 of 12), they want to add 5 more seats.

**Problem:** The requirements team initially wrote "add 5 seats to the existing subscription." If taken literally, this implies editing the existing `SBQQ__Subscription__c` record to change the quantity from 10 to 15. CPQ does not do this — attempting to edit the record directly bypasses CPQ pricing and breaks the renewal and reporting chain.

**Solution:**

The correct requirements statement is: "At the amendment effective date, CPQ creates a new delta `SBQQ__Subscription__c` record for +5 seats, prorated to the co-termination date. The original record for 10 seats remains unchanged."

With a 12-month term and co-termination at December 31, the amendment on July 1 has 6 months remaining.

Proration calculation:
```
Effective Term = 6 months
Product Term   = 12 months
Unit Price     = $100/seat/month × 12 = $1,200/seat/year

Prorated Amount = (6 / 12) × $1,200 × 5 seats = $3,000
```

After the amendment, the contract has two subscription records:
- Original: 10 seats × $1,200/year, end date December 31
- Delta: +5 seats × $1,200/year, prorated at $3,000, end date December 31

The renewal quote generated from this contract will include 15 seats total (10 + 5), repriced at current list at the time of renewal.

**Why it works:** The ledger model means both records are additive. Reports summing subscription quantities across the contract will correctly total 15 seats. Integrations that read only the most recently created subscription record will under-count entitlement — this is the most common integration bug caused by misunderstanding the ledger model.

---

## Example 2: Co-Termination on a Multi-Product Contract

**Context:** A customer's contract has two products:
- Product A: 12-month subscription, started January 1, ends December 31
- Product B: 6-month subscription, started April 1, ends September 30

On June 1, the customer wants to add Product C as an annual subscription.

**Problem:** The requirements state "add Product C for 12 months starting June 1." With co-termination enabled, CPQ will not give Product C a full 12-month term — it will align Product C to the earliest contract end date (September 30, which is 4 months away from the June 1 amendment date).

**Solution:**

Requirements must explicitly state whether co-termination is enabled and what the expected proration of new lines is.

If co-termination is enabled:
```
Amendment Effective Date:  June 1
Co-Termination Date:       September 30 (earliest end date from Product B)
Product C Effective Term:  4 months
Product C Annual Price:    $2,400/year
Prorated Charge:           (4 / 12) × $2,400 = $800
```

Product C ends September 30. The contract now has three lines, all ending September 30 (Product A's remaining term is also cut to September 30 for the purposes of the renewal quote grouping, though Product A's existing subscription record end date remains December 31 — the immutability constraint).

If co-termination is disabled, Product C would be added for a full 12-month term (June 1 to May 31 next year) and the customer is billed $2,400 with no proration.

**Why it works:** Documenting the co-termination date and showing worked examples in requirements prevents billing disputes after go-live. Stakeholders seeing a $800 charge instead of an expected $2,400 annual charge will escalate unless the proration behavior is agreed to in writing before the contract is signed.

---

## Example 3: List Price Change After Contract Activation — Zero-Out Swap Workaround

**Context:** Product A's list price was $1,200/year at contract signing in January. The business raises the price to $1,500/year in March. A customer amends their contract in June. The business wants the amendment to apply the new $1,500 price to the existing 10-seat subscription.

**Problem:** Standard CPQ behavior will show the existing 10-seat line on the amendment quote at $1,200 (the contracted price, locked). Updating the price book entry to $1,500 in February has no effect on existing subscription records.

**Solution:**

The zero-out swap workaround requires a requirements decision that the business consciously accepts the additional complexity:

1. On the amendment quote, remove the existing 10-seat line (set quantity to 0 or delete the line). This generates a $0 delta subscription record that cancels the original 10-seat entitlement.
2. Add a net-new 10-seat line for Product A. Since this is a new line on the amendment, CPQ prices it from the current price book: $1,500/year.
3. The new 10-seat line is prorated to the co-termination date at the $1,500 rate.

```
Amendment Date:   June 1
Remaining Term:   6 months
New Unit Price:   $1,500/year
Prorated Charge:  (6 / 12) × $1,500 × 10 seats = $7,500
```

This workaround must be implemented with a custom Apex button or flow to reliably zero-out and re-add lines — doing it manually is error-prone at scale.

**Why it works:** The requirements document must flag this scenario explicitly. The workaround results in three subscription records (original 10-seat record, $0 cancellation delta, new 10-seat delta at $1,500), which increases ledger complexity. The business must confirm that their billing integration and entitlement reports can handle this three-record pattern.

---

## Anti-Pattern: Writing Requirements That Assume Subscription Records Are Editable

**What practitioners do:** Write requirements like "when a customer upgrades, update the Subscription record to reflect the new quantity." This language implies direct record edits.

**What goes wrong:** The development team implements direct DML updates to `SBQQ__Subscription__c`, which bypasses CPQ's amendment processing engine. The result is that the upgrade appears to work on the record, but renewal quotes are generated incorrectly (the delta is missing from the renewal quantity calculation), proration is never calculated, and the contract amendment history is incomplete. These bugs typically surface during the first renewal cycle, months after go-live.

**Correct approach:** Rewrite requirements to use CPQ amendment language: "when a customer upgrades, initiate a CPQ amendment from the active contract. CPQ creates a new delta Subscription record for the quantity change, prorated to the co-termination date. The original Subscription record is not modified."
