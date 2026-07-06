# Well-Architected Notes — AgentExchange Publishing

## Relevant Pillars

- **Security** — distribution from a listing is gated on passing Salesforce's Security
  Review and Assessment under the AgentExchange ISV Program Track, and the Link Your
  Solution step asks the partner to confirm security compliance. Treat the review as a
  design input for the packaged solution, not a post-hoc checkbox: the marketplace gate is
  the enforcement point, but the work happens in the package. Payment data never transits
  partner infrastructure — Checkout runs on Stripe as the payment partner.
- **Operational Excellence** — the Partner Console is the single operational surface:
  Notifications flag "things they must fix or review," Your Analytics reports tile views,
  tile hovers, and lead events, and Company Info on the Home page is the one place
  public-facing contact updates actually propagate from. Build the post-publish routine
  around those three, not around re-editing listing steps.
- **Reliability** — the publishing pipeline has ordered, blocking dependencies: listing-plan
  business approval before the builder, completed basics + set pricing before the listing
  can be submitted for approval, Security Review before distribution. Plans that treat
  these as parallelizable produce launch dates that slip; sequence the gates explicitly.

## Architectural Tradeoffs

- **Checkout vs. own billing + COA.** Checkout gives an on-listing buy motion with a
  documented cost (15% on bank transfers; 15% + $0.30/transaction on cards; no minimum,
  setup, monthly, or card-storage fees) but hard gates: US/UK/EU-based partner, managed
  package, no OEM apps, English only. Off-platform billing through the partner's own
  payment systems and the Channel Order App keeps flexibility at the cost of a self-service
  purchase path.
- **Revenue Share vs. Annual Fee vs. freemium.** Revenue share (15%) scales cost with
  success; the annual fee is fixed, upfront, and sized by customer orgs and/or users;
  freemium trades short-term revenue for adoption up to feature-based limits. The choice is
  a business-model decision recorded in the listing plan and approved before the build.
- **Public pricing vs. Private Offers.** Public plans enable self-service; the Request
  Private Offer button keeps negotiated enterprise deals on-marketplace and shortens the
  sales cycle, at the cost of a human in the loop per deal. Many listings need both.

## Anti-Patterns

1. **Listing-first, review-later** — polishing marketing content while the Security Review
   is unstarted; the review gates distribution, so it owns the critical path.
2. **Channel decisions before eligibility checks** — announcing "buy on AgentExchange"
   before verifying the partner-geography, managed-package, and no-OEM gates.
3. **Per-listing contact drift** — maintaining public contact info in each listing's
   Business Contact field (which doesn't reach the public listing) instead of once, on the
   Partner Console Home page, where updates propagate to all public listings.

## Official Sources Used

- AgentExchange Checkout Overview (ISVforce / Packaging Guide) — https://developer.salesforce.com/docs/atlas.en-us.packagingGuide.meta/packagingGuide/appexchange_checkout_overview.htm
- Trailhead: Get to Know the AgentExchange Partner Console — https://trailhead.salesforce.com/content/learn/modules/appexchange-partners-publishing/appexchange-partner-console
- Trailhead: Create a Listing with the Listing Builder — https://trailhead.salesforce.com/content/learn/modules/appexchange-partners-publishing/appexchange-listing-builder
- Partner Program FAQ: AgentExchange ISV (Security Review, Private Offers) — https://help.salesforce.com/s/articleView?id=000394757&language=en_US&type=1
- Updating your AgentExchange Listing (Salesforce Help) — https://help.salesforce.com/s/articleView?id=000389531&language=en_US&type=1
- What Is AgentExchange? (Install Guide) — https://developer.salesforce.com/docs/atlas.en-us.appExchangeInstallGuide.meta/appExchangeInstallGuide/appexchange_install_whatis.htm
