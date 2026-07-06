# Examples — AgentExchange Publishing

All walkthroughs below are grounded in the official Trailhead publishing module, the
ISVforce Packaging Guide (Checkout), and Salesforce Help. Names and prices are
illustrative; the step sequences, eligibility rules, and fee numbers are documented.

## Example 1: Publishing a paid agent solution with Checkout

**Context:** a US-based ISV has an Agentforce solution packaged as a managed package
(Security Review passed) and wants a self-service, subscription-priced listing.

**Problem:** the team wants customers to buy directly from the listing rather than routing
every deal through a manual order process.

**Solution:**

1. **Listing plan first.** Draft the plan — basic details, pricing model, pricing plans —
   and submit it to the Salesforce account representative for business approval. Use
   `templates/agentexchange-publishing-template.md`:

   ```markdown
   **Listing type:** solution
   **Pricing model:** revenue-share
   **Checkout enabled:** yes
   **Company country:** United States
   **Distribution:** managed package
   **OEM app:** no
   **Security review passed:** yes
   ```

2. **Build in the Partner Console.** Partner Community → **Publishing** (auto-authenticates
   into the console) → **Listings** → new listing, then in order:
   - *Fill in the Basics* — listing title, required/compatible Salesforce products,
     supported editions, languages, business needs, contact info.
   - *Set Pricing* — pricing model + Solution Pricing tiers; add the pricing plan details
     and get the plan approved.
   - *Add Details* — tagline, description, highlights, terms and conditions, logos,
     screenshots, videos.
   - *Link Your Solution* — connect the managed package, confirm security compliance, pick
     "Install from your AgentExchange listing" as the install method.
   - *Grow Your Business* — configure a test drive from a trial template, a free trial, and
     lead capture.

3. **Wire Checkout.** In the Partner Console: create a Stripe account, connect it to the
   listing, and add the pricing plans (one-time or subscription; per user or per company).
   As a US partner, submit a W-9 to Salesforce.

4. **Submit for approval.** With the basics complete and pricing set, submit the listing
   for approval; once approved and public, test the buy/install path end to end.

**Why it works:** every gate is satisfied in order — business approval before the builder,
completed basics + pricing before the listing submission, Security Review before
distribution, and Checkout eligibility (US-based partner, managed package, not OEM) before
promising on-platform payment.

---

## Example 2: Consultant listing (3-step flow)

**Context:** a consulting partner wants to list implementation services, not a package.

**Problem:** the team assumed they needed a package, pricing plans, and a Security Review
before they could appear on the marketplace.

**Solution:** consultant listings use the shorter documented flow — "Fill in the Basics,
Add Details, and Grow Your Business." There is no Set Pricing step, no Link Your Solution
step, no package, and therefore no package Security Review on the critical path.

```markdown
**Listing type:** consultant
**Pricing model:** n/a
**Checkout enabled:** no
```

**Why it works:** the Listing Builder branches on listing type; forcing the solution-shaped
5-step plan onto a consultant listing invents work (and blockers) that don't exist.

---

## Example 3: Choosing a commercialization model

**Context:** an ISV is deciding how to charge for a paid solution.

**Problem:** the documented options get conflated with Checkout, which is a *payment
channel*, not a pricing model.

**Solution:** pick from the documented models first, then decide the payment channel:

| Model | Documented shape | Fits when |
|---|---|---|
| Revenue Share | Share 15% of the app's revenue with Salesforce | Usage-scaled economics |
| Annual Fee | Fixed, upfront yearly fee based on customer orgs and/or users | Predictable per-org cost |
| Freemium | Free to use up to specific feature-based limits | Land-and-expand motion |

Then the channel: Checkout (on-platform card/bank-transfer payment) if eligible, otherwise
the partner's own payment systems with orders handled through the Channel Order App (COA).

**Why it works:** separating model from channel prevents the common error of ruling out a
pricing model because the team isn't Checkout-eligible.

---

## Example 4: Checkout eligibility screen

**Context:** a partner headquartered in India with customers in the US asks to enable
Checkout.

**Problem:** the team read "accept payments from any country Stripe supports" and concluded
they were eligible.

**Solution:** the eligibility gates apply to the *partner*:

- Company must be based in the United States, United Kingdom, or a European Union country
  → **not met** (India) → Checkout is unavailable; use off-platform billing + COA.
- Had the company been UK-based: the solution must be distributed in a managed package,
  must not be an OEM app, and Checkout is available in English only to eligible partners.
  Fee math for the plan: 15% revenue share on bank transfers; 15% + $0.30 per transaction
  on credit cards; no minimum revenue share, setup fees, monthly service charges, or card
  storage fees. EU/UK partners can enable VAT.

Run the checker to catch this mechanically:

```bash
python3 scripts/check_agentexchange_publishing.py --plan listing-plan.md
# WARN: Checkout is enabled but 'Company country: india' is not in the documented
#       eligibility set (United States, United Kingdom, or an EU country). Customers
#       may pay from any Stripe-supported country, but the partner-location rule
#       still applies.
```

**Why it works:** the two geography rules point in opposite directions — partner location
is restricted, customer location is "any country Stripe supports" — and checking them
separately avoids both false positives and false negatives.

---

## Example 5: Fixing public contact info after publish

**Context:** a published listing shows a stale support contact. An admin edits the Business
Contact field in the listing's "Fill in the Basics" stage and republishes — nothing changes.

**Problem:** per Salesforce Help, updating the Business Contact field during "Fill in the
Basics" "will not appear on the public listing."

**Solution:** log into the Partner Community → **Publishing** → Partner Console **Home** →
Overview → **Company Info**, and update the Customer Support Email Address there. Per the
same article, "Updates will be reflected on all your public listings."

**Why it works:** public-facing company contact data is sourced from the console Home page,
not from the per-listing field — the in-listing edit is the trap, the Home-page edit is the
documented path.

---

## Anti-Pattern: promising on-platform payments before checking the gates

**What practitioners do:** design the whole go-to-market around "buy now on the listing,"
then discover late that the company is based outside the US/UK/EU, the app ships as OEM, or
the solution isn't in a managed package.

**What goes wrong:** the pricing pages, sales motion, and revenue forecasts all assume a
payment channel the partner cannot enable; the fallback (own payment systems + COA) has a
different operational shape.

**Correct approach:** screen the three documented Checkout gates (partner geography,
managed-package distribution, no OEM) during the listing-plan stage — the workbook and
checker in this skill front-load exactly that.
