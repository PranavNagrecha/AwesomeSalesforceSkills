# LLM Anti-Patterns — CPQ vs Standard Products Decision

Common mistakes AI coding assistants make when generating or advising on CPQ vs standard Products decisions.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Recommending CPQ for Every Quoting Scenario

**What the LLM generates:** "For quoting in Salesforce, you should use Salesforce CPQ which provides a comprehensive configure-price-quote solution." — even when the org has 10 products with flat pricing and no bundling needs.

**Why it happens:** CPQ is heavily represented in training data as the "enterprise quoting solution." LLMs default to the most feature-rich option without evaluating whether the complexity and cost are justified.

**Correct pattern:**

```text
Before recommending CPQ, evaluate:
1. Product catalog size and complexity (bundles? options? exclusions?)
2. Pricing model (flat list price vs volume tiers vs contracted rates)
3. Number of quoting users (drives per-user licensing cost)
4. Whether standard Products + Pricebooks + custom fields can cover requirements
5. Whether the org already holds a CPQ subscription: the package "continues to be
   available for existing customers" with "no longer any new feature development"
   (CPQ Developer Guide v67.0)

Recommend standard objects when the catalog is simple and quoting is straightforward.
```

**Detection hint:** Look for CPQ recommendations that lack a cost-benefit analysis or requirements assessment.

---

## Anti-Pattern 2: Understating CPQ Licensing Cost

**What the LLM generates:** "CPQ is available as an add-on to Sales Cloud" without mentioning the per-user monthly cost, or stating a generic "additional licensing may apply."

**Why it happens:** LLMs avoid specific pricing because it changes over time. However, omitting the cost entirely makes the recommendation misleading. UNVERIFIED (2026-10-03): the "$75+/user/month" figure used in this skill is older list pricing that could not be fetched; use the customer's current quote.

**Correct pattern:**

```text
Salesforce CPQ requires a separate per-user licence. At the older list price of
$75/user/month, 50 quoting users cost $45,000/year before implementation.
Replace the price with the current quote, measure the user count from quote
activity, and state the lifecycle notice alongside the cost.
```

**Detection hint:** Check for CPQ recommendations that do not include a specific per-user cost figure or total cost estimate.

---

## Anti-Pattern 3: Confusing CPQ Objects with Standard Quote Objects

**What the LLM generates:** Code or configuration that references the standard Quote and QuoteLineItem objects when the org uses CPQ, or references SBQQ__Quote__c and SBQQ__QuoteLine__c when the org uses standard quoting.

**Why it happens:** LLMs mix up the two data models because both involve "quotes" and "quote lines." Training data includes examples from both models without clear disambiguation.

**Correct pattern:**

```text
Standard quoting: Quote (standard object) + QuoteLineItem (standard object)
CPQ quoting: SBQQ__Quote__c (managed package) + SBQQ__QuoteLine__c (managed package)

These are separate object sets. Code and configuration must target the correct
model for the org. Ask which model the org uses before writing any quote-related
automation.
```

**Detection hint:** Search for `SBQQ__` references in code intended for standard-quoting orgs, or standard `Quote` object references in CPQ orgs.

---

## Anti-Pattern 4: Claiming Standard Objects Can Do Everything CPQ Does

**What the LLM generates:** "You can replicate CPQ bundling by creating a custom junction object between Products and using Apex to enforce inclusion/exclusion rules." — implying that custom development is straightforward and equivalent.

**Why it happens:** LLMs are biased toward showing that problems are solvable with code. They underestimate the ongoing maintenance cost and edge-case complexity of replicating CPQ's configuration engine in custom Apex.

**Correct pattern:**

```text
While technically possible to build custom bundling logic on standard objects,
the maintenance burden can exceed CPQ licensing cost for orgs with genuine
bundle complexity (UNVERIFIED (2026-10-03): the "12-18 months" crossover often
quoted is a practitioner estimate, not a documented figure).
Evaluate the total cost of ownership, not just the initial build effort.
```

**Detection hint:** Look for recommendations to "build custom" CPQ features without a maintenance cost estimate or TCO comparison.

---

## Anti-Pattern 5: Ignoring the Migration Path from Standard to CPQ

**What the LLM generates:** "Start with standard Products and Pricebooks, and you can always upgrade to CPQ later if you need more features." — without mentioning the data migration cost or split data architecture.

**Why it happens:** LLMs provide optimistic guidance about incremental adoption without accounting for the fact that CPQ uses different objects (SBQQ__*) than standard quoting. Migration from standard to CPQ is a project, not a toggle.

**Correct pattern:**

```text
Migrating from standard quoting to CPQ requires:
- Data migration of existing Quote and QuoteLineItem records to SBQQ objects
- Updating all automations, integrations, and reports to reference CPQ objects
- Retraining the sales team on the CPQ interface
- Deciding how to handle historical quotes (migrate vs maintain parallel)

Factor migration cost into the decision. Starting with standard objects is valid,
but "upgrade later" is not free.
```

**Detection hint:** Look for "start simple and upgrade later" advice that does not mention migration effort, data model differences, or historical data handling.

---

## Anti-Pattern 6: Hallucinating CPQ Features That Do Not Exist

**What the LLM generates:** References to CPQ features like "CPQ AI-powered pricing recommendations" or "CPQ native e-signature" that are not part of the CPQ managed package.

**Why it happens:** LLMs confuse CPQ features with Revenue Cloud Advanced features, third-party AppExchange add-ons, or entirely hallucinated capabilities.

**Correct pattern:**

```text
Verify every claimed CPQ feature against the official CPQ documentation:
https://help.salesforce.com/s/articleView?id=sf.cpq_parent.htm

CPQ core features: product bundles, guided selling, price rules, discount
schedules, contracted pricing, subscription management, advanced approvals,
quote document generation.

CPQ does NOT natively include: e-signature, AI pricing, revenue recognition,
billing/invoicing (these require separate products or add-ons). Advanced
Approvals ships as its own package: the CPQ Developer Guide documents "the API
from the Advanced Approvals package".
```

**Detection hint:** Flag any CPQ feature claim that is not in the official CPQ documentation. Cross-reference against the CPQ feature list before presenting to users.

---

## Anti-Pattern 7: Recommending A Net-New CPQ Purchase From Pre-2026 Material

**What the LLM generates:** "For complex bundles and subscriptions, purchase Salesforce CPQ" for a customer with no CPQ subscription, with no mention of the product's lifecycle.

**Why it happens:** Most comparison content in training data predates the current notice. The model learned CPQ as the default enterprise quoting answer and has no signal that its status changed.

**Correct pattern:** Quote the CPQ Developer Guide v67.0 notice: the package "continues to be available for existing customers, however, there is no longer any new feature development", with support "for the duration of your contract". For an existing customer, treat CPQ as a renewal decision scored against today's feature set. For a net-new customer, CPQ is not sold ("Salesforce is no longer selling new Salesforce CPQ licenses to new customers", salesforce.com, 10 July 2026); route the complex-quoting evaluation to `architect/revenue-cloud-architecture`.

**Detection hint:** A CPQ recommendation that never states whether the customer already holds a CPQ subscription.

