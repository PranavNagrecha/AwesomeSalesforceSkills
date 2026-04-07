# Examples — Soft Credits and Matching Gifts (NPSP)

## Example 1: Board Member Soft Credit for Cultivated Major Gift

**Context:** A nonprofit's major gifts officer cultivated a $25,000 gift from a corporate donor. The board member who made the introduction and stewarded the relationship over 18 months should receive soft credit for fundraising attribution reporting.

**Problem:** Without explicit OCR configuration, only the primary donor contact (the corporate donor's representative) receives credit. The board member appears in no giving or attribution reports, making it impossible to demonstrate their fundraising impact during a board performance review.

**Solution:**

1. Open the $25,000 Opportunity record.
2. Navigate to the Contact Roles related list.
3. Add the board member as a Contact Role with Role = "Soft Credit" (confirm this role is in NPSP Settings > Contact Roles > Soft Credit Roles list).
4. Save. No `npsp__Partial_Soft_Credit__c` record is needed because the full $25,000 should attribute to the board member's soft credit total.
5. Trigger rollup recalculation for the board member Contact or wait for the nightly batch.

```
// Query to verify OCR was created correctly
SELECT Id, ContactId, OpportunityId, Role, IsPrimary
FROM OpportunityContactRole
WHERE OpportunityId = '[opp_id]'
```

Expected result: two OCR records — one with Role = "Donor" (primary, IsPrimary = true) for the corporate contact, and one with Role = "Soft Credit" (IsPrimary = false) for the board member.

**Why it works:** NPSP reads non-primary OCR roles against the org's configured soft credit role list. A match causes the opportunity amount to roll up into `npsp__Soft_Credit_This_Year__c` on the board member's Contact record. The primary donor's hard credit total is unaffected.

---

## Example 2: 100% Employer Matching Gift via Find Matched Gifts

**Context:** An employee donates $500 to a nonprofit. The employee's employer has a 1:1 matching gift program and has an open Matching Gift opportunity for $10,000 on file (representing the annual pool of matching funds). The employer contact is the corporate giving manager.

**Problem:** The admin manually adds an OCR with role "Soft Credit" to the employee's $500 Opportunity for the corporate giving manager. After recalculation, the employer contact shows $500 in soft credit totals — but this is the wrong model. The employer should receive hard credit via a Matching Gift opportunity, not a soft credit on the employee's donation. The soft credit approach also fails when the matching pool is tracked separately (the Matching Gift opportunity's closed amount never updates).

**Solution:**

1. Verify the employer Account has an open Matching Gift opportunity. If not, create one:
   - Account: employer Account
   - Opportunity Name: e.g., "Acme Corp Matching Gifts 2025"
   - Stage: "Pledged"
   - Amount: matching pool (e.g., $10,000)
   - Record Type: Matching Gift (if configured)
2. On the employee's $500 donation Opportunity, click Find Matched Gifts.
3. NPSP searches for Matching Gift opportunities on the employee's employer Account. Select the correct one.
4. NPSP will:
   - Populate `npsp__Matching_Gift__c` on the $500 donation with the Matching Gift opportunity ID
   - Create an OCR on the Matching Gift opportunity with Role = "Matched Donor" for the employer contact
   - Create an `npsp__Partial_Soft_Credit__c` record if the match is partial (for 1:1, it will be $500)

```
// Verify Partial_Soft_Credit__c was created correctly
SELECT Id, npsp__Opportunity__c, npsp__Contact__c, npsp__Amount__c, npsp__Contact_Role_ID__c
FROM npsp__Partial_Soft_Credit__c
WHERE npsp__Opportunity__c = '[matching_gift_opp_id]'
```

Expected: `npsp__Amount__c` = 500, `npsp__Contact_Role_ID__c` populated with the OCR Id.

5. Trigger rollup recalculation for the employer contact. Verify `npsp__Soft_Credit_This_Year__c` reflects $500.

**Why it works:** The Matching Gift opportunity is the vehicle for the employer's giving record. NPSP uses the `npsp__Partial_Soft_Credit__c` amount (not the full matching pool amount) when calculating the employer's soft credit rollup for this transaction.

---

## Example 3: Partial Soft Credits Split Between Two Solicitors

**Context:** A $10,000 gift was co-solicited by two major gift officers. Each should receive $5,000 in soft credit attribution for their individual fundraising totals.

**Problem:** Adding two OCRs with the same soft credit role and no partial credit records causes NPSP to credit the full $10,000 to each officer — totaling $20,000 in attributed soft credits, which overstates team performance.

**Solution:**

1. Add two OCR records on the $10,000 Opportunity — one for each major gift officer — both with Role = "Soft Credit".
2. For each OCR, create an `npsp__Partial_Soft_Credit__c` record:
   - `npsp__Opportunity__c`: the $10,000 Opportunity
   - `npsp__Contact__c`: the respective officer's Contact
   - `npsp__Amount__c`: 5000
   - `npsp__Contact_Role_ID__c`: the corresponding OCR Id

```
// Both records should look like this (one per officer)
npsp__Partial_Soft_Credit__c psc = new npsp__Partial_Soft_Credit__c(
    npsp__Opportunity__c = oppId,
    npsp__Contact__c = officerContactId,
    npsp__Amount__c = 5000,
    npsp__Contact_Role_ID__c = ocrId
);
```

3. Trigger rollup recalculation for both contacts. Each should show $5,000 in soft credit this year.

**Why it works:** When `npsp__Partial_Soft_Credit__c` records exist for an OCR, NPSP uses `npsp__Amount__c` from those records — not the full opportunity amount — for rollup calculations. Without partial records, NPSP defaults to the full opportunity amount per OCR.

---

## Anti-Pattern: Adding OCR on the Original Gift to Credit the Employer for a Matching Gift

**What practitioners do:** Instead of creating a Matching Gift opportunity and using Find Matched Gifts, they add an OCR with role "Soft Credit" directly to the employee's donation Opportunity, with the employer contact listed.

**What goes wrong:**
- The employer receives soft credit (not hard credit) on the original donation — this is incorrect for matching gift accounting, where the employer's match is a separate, distinct gift.
- The employer's Matching Gift opportunity (if it exists) is never linked, so its closed amount never updates and the matching pool balance is not tracked.
- NPSP rollup reports mix the employer's attributed soft credits with their actual hard gifts, corrupting giving history.
- The Matched Donor role and `npsp__Matching_Gift__c` lookup are never populated, so NPSP matching gift reports do not include this transaction.

**Correct approach:** Always use Find Matched Gifts to link employee donations to the employer's Matching Gift opportunity. The employer's credit flows through the Matching Gift opportunity, not through the employee's donation.
