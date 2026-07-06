---
name: agentexchange-publishing
description: "Use when an ISV or consulting partner is creating, pricing, publishing, or maintaining an AgentExchange listing through the Partner Console — covers the listing plan, the 5-step Listing Builder workflow (Fill in the Basics, Set Pricing, Add Details, Link Your Solution, Grow Your Business), commercialization models (revenue share vs. annual fee vs. freemium), AgentExchange Checkout setup (Stripe connection, pricing plans, fees, geographic eligibility), Private Offers, Security Review gating, and post-publish listing updates. NOT for building the agent or managed package itself (use agentforce/agentforce-agent-creation and devops/second-generation-managed-packages), NOT for LMA/Trialforce licensing internals (use devops/isv-license-management-and-trialforce), and NOT for the customer-side install experience."
category: agentforce
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Operational Excellence
triggers:
  - "publish my agent solution to AgentExchange as a partner listing"
  - "set up pricing plans and Stripe checkout on my AgentExchange listing"
  - "enable private offers so customers can negotiate pricing on my listing"
  - "walk me through the Partner Console listing builder steps"
  - "updating my company contact info isn't showing up on the public listing"
tags:
  - agentexchange
  - partner-console
  - listing-builder
  - checkout
  - private-offers
inputs:
  - "What is being listed: a packaged solution (managed package) or a consulting service"
  - "The commercialization intent: free, freemium, revenue share, or annual fee"
  - "Whether payments should be collected on-platform via AgentExchange Checkout (and the company's country of establishment)"
  - "Security Review status of the packaged solution"
outputs:
  - "A completed listing plan (basic details + pricing model + pricing plans) ready for business approval"
  - "A step-by-step Partner Console publishing sequence tailored to the listing type"
  - "A Checkout / Private Offers configuration decision with eligibility checks applied"
  - "A post-publish maintenance checklist for keeping the public listing accurate"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-07-06
---

# AgentExchange Publishing

This skill activates when a Salesforce partner needs to take a solution — an agent, agent actions, an app, or a consulting service — to market on **AgentExchange**, Salesforce's unified marketplace for "apps, AI agents, Bolt solutions, Flow solutions, Lightning data, components, and more." It covers the partner-side workflow: the listing plan, the Partner Console Listing Builder, commercialization models, AgentExchange Checkout, Private Offers, and post-publish maintenance.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Listing type.** A packaged-solution listing uses the full 5-step Listing Builder flow; a consultant listing uses a shorter 3-step flow (Fill in the Basics, Add Details, Grow Your Business) with no pricing or solution-linking steps.
- **Security Review status.** For a packaged solution, the application must pass Salesforce's Security Review and Assessment under the AgentExchange ISV Program Track before it can be distributed from a listing. If the review hasn't passed, that is the critical path — not the listing copy.
- **Where payment happens.** AgentExchange Checkout (on-platform payment via Stripe) has hard eligibility gates: the partner company must be based in the United States, United Kingdom, or a European Union country; the solution must be distributed in a managed package; and Checkout can't be used with OEM apps. Off-platform billing uses the partner's own payment systems plus the Channel Order App (COA).
- **Publishing permissions.** Publishing packages requires both the **Create AgentExchange Packages** and **Upload AgentExchange Packages** permissions; customers installing need admin rights or the **Download AgentExchange Packages** permission.
- **Maturity honesty.** The official docs describe the Partner Console, Listing Builder, Checkout, and Private Offers as current, operating functionality without attaching a GA/Beta/Pilot label. Do not assert a maturity level the docs don't state.

---

## Core Concepts

### The Partner Console

The AgentExchange Partner Console is "the one-stop shop to create, publish, manage your listings, and much more" — the complete business management site for ISV partners and consultants. Partners reach it by logging into the Partner Community and clicking **Publishing**; authentication into the console is automatic. Its main tabs:

- **Home** — Company Info, Notifications (things to fix or review), Your Analytics (tile views, tile hovers, lead events), and Your Listings.
- **Listings** — access in-progress and published listings, and create new ones.
- **Technologies** — solution connections, trial templates, License Management Org registration, and security reviews.

### The listing plan

Before touching the Listing Builder, partners prepare a **listing plan** (also called a business plan): "the basic details of your listing plus your pricing model and pricing plans." The plan is submitted to the partner's Salesforce account representative for business approval. Treat it as a real artifact — this skill's `templates/agentexchange-publishing-template.md` is a fill-in workbook for it.

### Commercialization models

For paid solutions, partners choose between:

- **Revenue Share** — share 15% of the app's revenue with Salesforce.
- **Annual Fee** — a fixed, upfront, yearly fee based on the number of customer orgs and/or users.
- **Freemium** — free to use up to specific feature-based limits, with paid expansion.

Off-platform paid deals run through the Channel Order App (COA) and the partner's own payment systems. On-platform payment is the separate Checkout capability below.

### AgentExchange Checkout

Checkout is AgentExchange's integrated payment platform: customers buy the solution directly from the listing with a credit card or bank transfer. Setup is per-listing, in the Partner Console: create a Stripe account, connect it to the listing, and add pricing plans. Key documented parameters:

| Parameter | Documented behavior |
|---|---|
| Partner eligibility | Company based in the US, UK, or an EU country; English only, eligible partners |
| Customer reach | Payments accepted from any country Stripe supports |
| Solution constraints | Must be distributed in a managed package; can't be used with OEM apps |
| Plan shapes | One-time and subscription plans; charged per user or per company |
| Revenue share | 15% on bank transfers; 15% + $0.30 per transaction on credit cards |
| Fees | No minimum revenue share; no setup fees, monthly service charges, or card storage fees |
| Tax | US partners submit a W-9; EU/UK partners can enable VAT; US sales tax supported |
| Integrations | Works with the License Management App (LMA) and the Checkout Management App (CMA) |

### Private Offers

Partners can activate a **Request Private Offer** button on a listing so customers "initiate a private offer conversation without leaving the marketplace, helping shorten the sales cycle" — negotiated terms and pricing without an off-platform sales dance. The partner FAQ attributes the button to partners enrolled in the AgentExchange Partner Program; note that distributing a packaged solution is separately gated on the passed Security Review under the ISV Program Track.

---

## Common Patterns

### Full commercial listing (solution + Checkout)

**When to use:** an ISV with a managed-package solution, a US/UK/EU-based company, and a self-service pricing motion.

**How it works:** complete the listing plan and get business approval → run the 5-step Listing Builder (Basics → Set Pricing, adding pricing plan details and getting the plan approved → Add Details → Link Your Solution, choosing "Install from your AgentExchange listing" → Grow Your Business) → connect a Stripe account to the listing and add one-time or subscription pricing plans → submit the listing for approval.

**Why not the alternative:** skipping Checkout means every deal needs an off-platform order via COA; and per the documented flow, the listing can only be submitted for approval once the basics are complete and pricing is set — so leaving Set Pricing half-done stalls submission.

### Consultant listing

**When to use:** a consulting partner listing services rather than a packaged solution.

**How it works:** the 3-step flow — Fill in the Basics, Add Details, Grow Your Business. There is no Set Pricing or Link Your Solution step and no package or Security Review to gate on.

### Sales-assisted listing with Private Offers

**When to use:** enterprise-priced solutions where public list pricing doesn't fit, but you still want the buying conversation to start (and stay) on the marketplace.

**How it works:** publish the listing, then enable the Request Private Offer button so customers open a negotiation directly from the listing. Combine with lead capture from the Grow Your Business step so marketplace activity lands in your pipeline.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Consulting services, no package | Consultant listing (3-step flow) | No pricing or solution-linking steps apply |
| Managed package, company in US/UK/EU, self-service pricing | Checkout with one-time or subscription plans | On-platform payment; 15% revenue share, no setup/monthly fees |
| Company based outside US/UK/EU | Off-platform billing + COA | Checkout requires the partner to be US/UK/EU-based |
| OEM app | Off-platform billing + COA | Checkout can't be used with OEM apps |
| Enterprise/negotiated pricing | Private Offers on the listing | Customers negotiate without leaving the marketplace |
| Free-with-limits go-to-market | Freemium model | Documented model: free up to specific feature-based limits |
| Predictable per-org economics preferred over % of revenue | Annual Fee model | Fixed, upfront yearly fee based on customer orgs and/or users |

---

## Recommended Workflow

1. **Classify the listing and check the gates** — solution vs. consultant listing; for solutions, confirm the managed package exists and the Security Review has passed (or plan for it); confirm the publisher holds Create + Upload AgentExchange Packages permissions.
2. **Draft the listing plan** — basic details + pricing model + pricing plans (use `templates/agentexchange-publishing-template.md`), then submit it to your Salesforce account representative for business approval before building anything in the console.
3. **Build the listing in the Partner Console** — Partner Community → Publishing → Listings → create the listing and work the steps in order: Fill in the Basics; Set Pricing (add pricing plan details and get the plan approved); Add Details; Link Your Solution (connect the managed package, confirm security compliance, pick the install method); Grow Your Business (test drives via trial templates, free trials, lead capture). Consultant listings: Basics → Details → Grow only.
4. **Configure payment** — if Checkout-eligible (US/UK/EU company, managed package, not OEM), create and connect the Stripe account and add pricing plans on the listing; US partners submit a W-9, EU/UK partners enable VAT as needed. Otherwise wire the off-platform COA motion. Optionally enable the Request Private Offer button.
5. **Submit and verify** — submit the listing for review; once public, verify the live listing's content, pricing plans, and install path end to end.
6. **Maintain post-publish** — update public-facing company contact details from the Partner Console Home page (Home → Overview → Company Info), not the Business Contact field inside the listing steps; watch Notifications and Your Analytics (tile views, tile hovers, lead events) for follow-ups.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Listing type identified; consultant listings use the 3-step flow, solutions the 5-step flow
- [ ] Security Review passed (or scheduled as the critical path) for any packaged solution
- [ ] Listing plan (details + pricing model + pricing plans) approved by the account representative
- [ ] Checkout eligibility verified before promising on-platform payment: US/UK/EU company, managed package, not OEM
- [ ] Checkout fee math uses documented numbers: 15% bank transfer; 15% + $0.30/transaction credit card
- [ ] Private Offers enablement decision recorded for negotiated-pricing motions
- [ ] Public contact details maintained from Partner Console Home, not the in-listing Business Contact field
- [ ] No GA/Beta/Pilot maturity claim made that the docs don't state

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Business Contact edits vanish from the public listing** — updating the Business Contact field during the "Fill in the Basics" stage does not appear on the public listing. Public contact info is maintained from the Partner Console Home page, and those updates apply to all your public listings.
2. **Checkout eligibility is about the partner, not the customer** — the *partner company* must be based in the US, UK, or an EU country, but payments can be accepted from any country Stripe supports. Teams routinely invert this and wrongly rule Checkout in or out.
3. **Basics + pricing gate listing submission** — per the documented flow, a listing can be submitted for approval only once Fill in the Basics is complete and pricing is set; leaving either half-done stalls the submission, not just the copywriting.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| `templates/agentexchange-publishing-template.md` | Fill-in listing-plan workbook (basics + pricing model + pricing plans + Checkout/Private Offers decisions) with machine-checkable fields |
| `scripts/check_agentexchange_publishing.py` | Stdlib validator for a completed listing plan: flow shape, pricing model, Checkout eligibility gates, Security Review gate |
| Partner Console publishing sequence | Ordered step list (5-step or 3-step) tailored to the listing type |

---

## Related Skills

- `devops/second-generation-managed-packages` — build and version the managed package the listing's Link Your Solution step connects to.
- `devops/isv-license-management-and-trialforce` — LMA registration, Trialforce trial templates (used by the Grow Your Business test-drive setup), and Checkout licensing integration internals.
- `devops/appexchange-app-analytics` — deeper marketplace usage analytics beyond the Partner Console's tile views / tile hovers / lead events.
- `agentforce/agent-security-review` — pre-production hardening of the agent itself before submitting the packaged solution to the marketplace Security Review.
