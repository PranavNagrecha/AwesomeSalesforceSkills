# AgentExchange Listing Plan — Workbook

Fill this in **before** opening the Partner Console Listing Builder. The listing plan is
"the basic details of your listing plus your pricing model and pricing plans," and it goes
to your Salesforce account representative for business approval first.

The `**Field:** value` lines below are machine-checkable — validate with:

```bash
python3 ../scripts/check_agentexchange_publishing.py --plan agentexchange-publishing-template.md
```

---

## 1. Listing Identity

**Listing title:** <!-- public name of the offer -->
**Listing type:** solution <!-- solution | consultant -->
**Status:** draft <!-- draft | in-review | published -->
**One-line value proposition:** <!-- what the solution does, for whom -->

## 2. Gates (fail any of these and stop here)

**Distribution:** managed package <!-- managed package | unmanaged | services-only -->
**Security review passed:** no <!-- yes | no | scheduled — required before a packaged solution can be distributed (AgentExchange ISV Program Track) -->
**Publisher permissions verified:** no <!-- Create AgentExchange Packages + Upload AgentExchange Packages -->

## 3. Pricing Model (solution listings only)

**Pricing model:** revenue-share <!-- free | freemium | revenue-share | annual-fee | n/a -->

Documented shapes:
- *Revenue Share* — share 15% of the app's revenue with Salesforce.
- *Annual Fee* — fixed, upfront yearly fee based on the number of customer orgs and/or users.
- *Freemium* — free to use up to specific feature-based limits.

### Pricing plans

| Plan name | One-time or subscription | Per user or per company | Price | Notes |
|---|---|---|---|---|
| | | | | |

## 4. Payment Channel

**Checkout enabled:** no <!-- yes | no -->
**Company country:** <!-- Checkout requires the partner company to be based in the United States, United Kingdom, or an EU country -->
**OEM app:** no <!-- yes | no — Checkout can't be used with OEM apps -->
**Stripe account connected:** no <!-- yes | no — created and connected to the listing in the Partner Console -->
**Tax setup:** <!-- US: W-9 submitted to Salesforce; EU/UK: VAT enabled if applicable -->
**Private offers enabled:** no <!-- yes | no — adds the Request Private Offer button to the listing -->

If Checkout is off (or ineligible): describe the off-platform billing motion and Channel
Order App (COA) handling here.

Fee model reference (documented): 15% revenue share on bank transfers; 15% + $0.30 per
transaction on credit cards; no minimum revenue share, no setup fees, monthly service
charges, or card storage fees.

## 5. Listing Builder Content Prep

Work the steps in order once the plan is approved. Consultant listings: only Basics,
Details, and Grow apply.

### Fill in the Basics
- [ ] Listing title
- [ ] Required / compatible Salesforce products
- [ ] Supported editions and languages
- [ ] Business needs
- [ ] Contact information (note: the Business Contact field here does NOT feed the public listing)

### Set Pricing
- [ ] Pricing model + Solution Pricing tiers entered
- [ ] Pricing plan details added and plan approved (basics + pricing must be complete
      before the listing can be submitted for approval)

### Add Details
- [ ] Tagline, description, highlights
- [ ] Terms and conditions
- [ ] Logos, screenshots, videos

### Link Your Solution
- [ ] Managed package connected
- [ ] Security compliance confirmed
- [ ] Install method selected (recommended: "Install from your AgentExchange listing")

### Grow Your Business
- [ ] Test drive configured from a trial template
- [ ] Free trial configured
- [ ] Lead capture enabled

## 6. Post-Publish Maintenance

- [ ] Public contact info maintained from Partner Console Home → Overview → Company Info
      (updates reflect on ALL public listings)
- [ ] Notifications reviewed for items to fix
- [ ] Your Analytics reviewed (tile views, tile hovers, lead events)
- [ ] Live listing content, pricing plans, and install path re-verified after each change

## Notes / Deviations

<!-- record anything that deviates from the standard flow and why -->
