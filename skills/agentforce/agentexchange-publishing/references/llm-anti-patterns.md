# LLM Anti-Patterns — AgentExchange Publishing

Common mistakes AI assistants make when generating or advising on AgentExchange publishing.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Inventing a metadata type or API for listings

**What the LLM generates:** a `package.xml` entry, an `AgentExchangeListing` metadata type,
a `sf agentexchange publish` CLI command, or a REST endpoint to "deploy" the listing.

**Why it happens:** everything else in a Salesforce repo is metadata-and-CLI shaped, so the
model pattern-fills a deployment story. Listings aren't metadata — they're authored in the
web-based Partner Console (Partner Community → Publishing).

**Correct pattern:**

```text
Partner Community → Publishing → Partner Console → Listings → (5-step or 3-step builder)
```

**Detection hint:** any `package.xml`, metadata type name, or CLI command claimed to create
or publish a listing.

---

## Anti-Pattern 2: Conflating pricing model with payment channel

**What the LLM generates:** "choose between Revenue Share, Annual Fee, or Checkout" — or
advice that a partner must use Checkout to charge for a solution.

**Why it happens:** both live in the "Set Pricing / money" cluster, and the model flattens
them. The documented commercialization models are Revenue Share (15%), Annual Fee (fixed,
upfront, yearly, based on customer orgs and/or users), and freemium; Checkout is the
separate on-platform *payment* capability (Stripe, card/bank transfer), with off-platform
billing + Channel Order App (COA) as the alternative channel.

**Correct pattern:** decide the model first, then the channel — and only offer Checkout if
the eligibility gates pass.

**Detection hint:** "Checkout" listed alongside Revenue Share / Annual Fee as if it were a
pricing model.

---

## Anti-Pattern 3: Getting the Checkout geography rule backwards

**What the LLM generates:** "Checkout lets you sell only to US, UK, and EU customers," or
"any partner can enable Checkout as long as Stripe supports their country."

**Why it happens:** the docs contain two opposite-direction geography statements and the
model swaps their subjects.

**Correct pattern:** the *partner company* must be based in the United States, United
Kingdom, or an EU country; *customers* can pay from any country Stripe supports.

**Detection hint:** any sentence applying the US/UK/EU restriction to customers, or
omitting it for partners.

---

## Anti-Pattern 4: Applying the 5-step flow to consultant listings

**What the LLM generates:** instructions telling a consulting partner to Set Pricing, link
a managed package, and pass Security Review before their services listing can go live.

**Why it happens:** the 5-step solution flow dominates the documentation, so the model
treats it as universal.

**Correct pattern:** consultant listings use three steps — "Fill in the Basics, Add
Details, and Grow Your Business" — with no pricing, no package linking, and no package
Security Review.

**Detection hint:** "Security Review" or "Link Your Solution" on a consultant-listing plan.

---

## Anti-Pattern 5: Hallucinating fee numbers or maturity labels

**What the LLM generates:** "Salesforce takes a 25% cut," "2.9% + $0.30 card fees,"
"AgentExchange Checkout is GA as of Spring '25," or "Private Offers (Beta)."

**Why it happens:** models blend Stripe's public retail pricing and generic marketplace
lore into the Salesforce numbers, and pattern-fill GA/Beta labels.

**Correct pattern:** cite only the documented figures — 15% revenue share on bank
transfers; 15% + $0.30 per transaction on credit cards; no minimum revenue share, no setup
fees, monthly service charges, or card storage fees. The docs attach no GA/Beta/Pilot label
to the Partner Console, Checkout, or Private Offers — state none.

**Detection hint:** any percentage other than 15%, any per-transaction fee other than
$0.30, or any GA/Beta/Pilot claim without a release-notes citation.

---

## Anti-Pattern 6: Fixing public contact info in the wrong place

**What the LLM generates:** "to change the support contact shown on your listing, edit the
Business Contact field in the Fill in the Basics step and republish."

**Why it happens:** the field name matches the user's goal, and the model doesn't know the
documented exception that this field "will not appear on the public listing."

**Correct pattern:** update Company Info from the Partner Console Home page (Home →
Overview → Company Info); those updates are reflected on all public listings.

**Detection hint:** advice routing public contact-info changes through the Business Contact
field inside a listing step.

---

## Anti-Pattern 7: Treating Private Offers as an off-platform workaround

**What the LLM generates:** "for custom pricing, take the deal off AgentExchange and
negotiate directly," or an invented "private listing URL" mechanism.

**Why it happens:** the model generalizes from other marketplaces' private-offer mechanics
instead of the documented feature.

**Correct pattern:** enable the **Request Private Offer** button on the listing so
customers "initiate a private offer conversation without leaving the marketplace, helping
shorten the sales cycle."

**Detection hint:** custom-pricing guidance that never mentions the Request Private Offer
button, or invents URLs/mechanisms the docs don't describe.
