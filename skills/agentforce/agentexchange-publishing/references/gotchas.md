# Gotchas — AgentExchange Publishing

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: The Business Contact field is a dead end for public updates

**What happens:** you edit the Business Contact field during the "Fill in the Basics" stage
of a listing, but the public listing never shows the new contact details. There is no error
and no warning.

**When it occurs:** any time a partner tries to update public-facing company contact info
from inside the per-listing builder steps instead of the console Home page.

**How to avoid:** update contact details from the Partner Console **Home** page (Home →
Overview → Company Info, e.g. the Customer Support Email Address). Per Salesforce Help,
those updates "will be reflected on all your public listings."

---

## Gotcha 2: Checkout geography is asymmetric

**What happens:** a partner outside the US/UK/EU plans a "buy now on the listing" motion,
or a US/UK/EU partner wrongly assumes it can only sell to customers in those regions.

**When it occurs:** whenever the two documented geography rules get conflated. The *partner
company* must be based in the United States, United Kingdom, or a European Union country —
but payments can be accepted "from any country that Stripe, our payment partner, supports."

**How to avoid:** screen partner geography at listing-plan time; screen customer geography
against Stripe's supported countries. They are independent checks.

---

## Gotcha 3: Checkout has solution-type exclusions, not just geography

**What happens:** a listing that seems Checkout-eligible on geography still can't enable
payments.

**When it occurs:** the solution isn't distributed in a managed package, or the app is an
OEM app — both documented exclusions. Checkout is also available in English only, to
eligible partners.

**How to avoid:** verify all three gates (managed package, not OEM, US/UK/EU partner)
before designing the pricing motion; fall back to the partner's own payment systems plus
the Channel Order App (COA) when any gate fails.

---

## Gotcha 4: Basics + pricing gate the listing submission

**What happens:** a team polishes the later Listing Builder steps but can't submit the
listing for approval.

**When it occurs:** per the documented flow, a listing can be submitted for approval only
once Fill in the Basics is complete and pricing is set ("Add your pricing plan details,
and get your plan approved") — teams that treat those two steps as deferrable stall the
submission.

**How to avoid:** get the listing plan (details + pricing model + pricing plans) approved
by the account representative up front, then complete Fill in the Basics and Set Pricing
early — the marketing content in Add Details can be prepared offline in parallel.

---

## Gotcha 5: Security Review gates the listing, not just the package

**What happens:** a finished, polished listing can't distribute the solution.

**When it occurs:** the application hasn't passed the "Security Review and Assessment as
part of the requirements under the AgentExchange ISV Program Track." The Link Your Solution
step also asks you to confirm security compliance.

**How to avoid:** treat Security Review as the critical path for any packaged-solution
listing; sequence listing-copy work in parallel, not ahead of it. Consultant listings have
no package and skip this gate entirely.

---

## Gotcha 6: Credit cards cost more than bank transfers on Checkout

**What happens:** margin models built on "15% revenue share" undercount card-heavy revenue.

**When it occurs:** Checkout's documented fee structure is 15% on bank transfers, but
"15%, plus a $0.30 per transaction fee" on credit cards. Per-transaction fees bite hardest
on low-priced, high-volume subscription plans.

**How to avoid:** model both payment methods; note the offsetting documented facts — no
minimum revenue share, and no setup fees, monthly service charges, or card storage fees.
