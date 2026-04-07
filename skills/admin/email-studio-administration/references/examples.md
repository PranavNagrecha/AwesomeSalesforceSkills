# Examples — Email Studio Administration

## Example 1: Dynamic Content Blocks for Loyalty Tier Personalization

**Context:** A retailer sends a monthly newsletter to 500,000 subscribers. Subscribers have a `LoyaltyTier` attribute on their subscriber record with values of `Gold`, `Silver`, `Bronze`, and `None`. The marketing team wants to show tier-specific offers and imagery without maintaining four separate email templates.

**Problem:** Without dynamic content, the team was cloning the email four times per campaign, updating each copy, and sending to four segmented lists. A copy change to the header required four edits. A/B testing was impossible because the audience was already split. Reporting was fragmented across four send jobs.

**Solution:**

In Content Builder, replace the hero image block and offer copy block with Dynamic Content blocks:

```
Dynamic Content Block: Hero Image
  Rule 1: LoyaltyTier = "Gold"     → Gold hero image + "Exclusive Gold Offer" headline
  Rule 2: LoyaltyTier = "Silver"   → Silver hero image + "Silver Member Savings" headline
  Rule 3: LoyaltyTier = "Bronze"   → Bronze hero image + "Bronze Member Deal" headline
  Default:                         → Generic promotional image + "Shop Our Latest Offers"

Dynamic Content Block: CTA Button Copy
  Rule 1: LoyaltyTier = "Gold"     → "Unlock Your Gold Reward"
  Rule 2: LoyaltyTier = "Silver"   → "Claim Your Silver Benefit"
  Rule 3: LoyaltyTier = "Bronze"   → "See Your Bronze Deal"
  Default:                         → "Shop Now"
```

Preview the email using the subscriber preview feature with a test subscriber from each tier to confirm each variation renders correctly. Run Content Detective on the final email before scheduling.

**Why it works:** Rules evaluate top-to-bottom at send time. Each subscriber sees exactly one variation per block — whichever rule matches first. The default catches any subscriber with `LoyaltyTier = None` or a missing value. One send definition, one approval, one deliverability report, zero version proliferation.

---

## Example 2: Commercial vs Transactional Send Classification for Order Confirmation

**Context:** A retailer is adding a post-purchase order confirmation email to their Marketing Cloud implementation. The email contains only the order ID, items purchased, estimated delivery date, and a link to track the order. No promotional content, no offers, no "you might also like" recommendations.

**Problem:** The team defaulted to using the existing Commercial Send Classification from their newsletter. This added a CAN-SPAM unsubscribe footer and enrolled the email in the global unsubscribe process. When a customer unsubscribed from the order confirmation, they were globally unsubscribed and stopped receiving all commercial marketing emails — including the weekly newsletter they had opted into separately.

**Solution:**

Create a dedicated Transactional Send Classification:

```
Send Classification Name: Order Confirmation - Transactional
  Sender Profile:       orders@example.com / "Example Orders"
  Delivery Profile:     Transactional IP pool / physical address optional
  Unsubscribe Profile:  Transactional (unsubscribes recorded separately from commercial opt-out)
  Send Classification:  Transactional
```

Assign this classification to the Order Confirmation Triggered Send Definition. Remove the unsubscribe footer from the email. Confirm the email body contains zero promotional content before classifying as Transactional.

**Why it works:** The Transactional classification tells the Email Studio suppression engine to exclude this send from the global commercial unsubscribe list. Customers who unsubscribe from the order confirmation do not lose their newsletter subscription. The email complies with CAN-SPAM because it meets the definition of a transactional message: its primary purpose is the facilitation of a completed commercial transaction.

---

## Example 3: A/B Subject Line Test with Holdout Send

**Context:** A B2C brand wants to test whether urgency-framing ("Last Chance") or benefit-framing ("Save 30%") drives higher open rates for a flash sale email to 200,000 subscribers.

**Problem:** The team was guessing which subject line to use. Previous campaigns showed inconsistent open rates across similar sends, and there was no structured way to learn from each campaign.

**Solution:**

Configure an A/B test in Email Studio:

```
Test Dimension:     Subject Line
Version A:          "Last Chance: Flash Sale Ends Tonight"
Version B:          "Save 30% — Flash Sale On Now"

Test Split:         10% → Version A (20,000 subscribers)
                    10% → Version B (20,000 subscribers)
                    80% → Holdout (160,000 subscribers — receives winner)

Winner Criteria:    Open Rate
Evaluation Window:  4 hours after test send
Auto-Send Winner:   Enabled
```

Schedule the test send for 8am. At 12pm, the system compares open rates across both test groups. Whichever version has the higher open rate at 12pm automatically sends to the 160,000 holdout subscribers.

**Why it works:** The holdout model ensures that the majority of the audience receives the statistically better-performing subject line without delaying the full send by more than the evaluation window. The 10/10/80 split is standard for large lists — for smaller audiences (under 10,000 total), increase the test groups to 25/25/50 to get enough open events for reliable comparison.

---

## Anti-Pattern: Using Transactional Classification for a Promotional Email to Avoid the Unsubscribe Footer

**What practitioners do:** Assign a Transactional Send Classification to a marketing newsletter or promotional offer email because it removes the unsubscribe footer and prevents contacts from opting out of the send.

**What goes wrong:** CAN-SPAM and CASL evaluate email content, not the platform-level classification field. A promotional email is legally a commercial email regardless of its Send Classification in Marketing Cloud. Recipients have the legal right to opt out of commercial messages. Sending promotional content under a Transactional classification can result in ISP spam complaints, ESP contract violations, and regulatory enforcement action. Additionally, Marketing Cloud's suppression engine cannot enforce global unsubscribes correctly when commercial sends are mis-classified.

**Correct approach:** Use Commercial Send Classification for any email where the primary purpose is marketing, promotion, or awareness. If the team's concern is that global unsubscribe is too broad, use Publication List-level unsubscribes to allow subscribers to opt out of specific send types while remaining opted in to others.
