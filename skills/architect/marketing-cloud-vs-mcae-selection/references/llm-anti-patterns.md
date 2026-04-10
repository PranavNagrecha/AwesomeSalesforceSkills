# LLM Anti-Patterns — Marketing Cloud vs. MCAE Selection

Common mistakes AI coding assistants make when generating or advising on Marketing Cloud vs. MCAE platform selection. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Treating MCE and MCAE as Interchangeable Products

**What the LLM generates:** Advice that frames MCE and MCAE as "two editions of the same product" or suggests that either can handle the same use cases with different configuration. For example: "You can use either Marketing Cloud Engagement or Account Engagement — they both do email marketing. Account Engagement is better for smaller lists and Marketing Cloud Engagement is better for larger ones."

**Why it happens:** Training data contains marketing copy that groups both products under "Salesforce Marketing Cloud" without clearly differentiating their architectures. LLMs pattern-match to the common framing of "edition A vs. edition B" from other software contexts.

**Correct pattern:**

```
MCE and MCAE are architecturally distinct products with separate licenses, separate data stores,
and non-overlapping capabilities. They are not editions of each other. The correct framing is:

- MCE: B2C, high-volume, multi-channel (email, SMS, push, advertising), Data Extension model
- MCAE: B2B, lead nurturing, CRM-aligned, Prospect model with scoring and grading

Features do not transfer between them. Selecting the wrong product requires a re-platform,
not a reconfiguration.
```

**Detection hint:** Flag any response that uses phrases like "either will work," "both can do," or "just configure it differently" when the topic is MCE vs. MCAE selection.

---

## Anti-Pattern 2: Recommending MCAE for High-Volume B2C Sends

**What the LLM generates:** A recommendation to use MCAE for a B2C consumer email program with subscriber counts above 75,000, often justified by MCAE's "tight Salesforce integration." For example: "Since you're already on Salesforce, use Account Engagement — it integrates natively with your CRM and you won't need Marketing Cloud Connect."

**Why it happens:** LLMs over-index on the CRM integration benefit of MCAE without accounting for the prospect record limits that make it structurally unsuitable for high-volume consumer audiences.

**Correct pattern:**

```
MCAE prospect record limits by edition:
- Growth: 10,000 prospects
- Plus: 10,000 prospects
- Advanced: 10,000 prospects
- Premium: 75,000 prospects

For any B2C audience exceeding 75,000 subscribers, MCAE is not a viable platform.
MCE is the correct platform for high-volume consumer sends. If CRM integration is needed,
Marketing Cloud Connect is the appropriate bridge.
```

**Detection hint:** Flag any recommendation of MCAE for a use case that mentions "consumer," "subscriber list," "B2C," or subscriber counts above 50,000.

---

## Anti-Pattern 3: Claiming MC Connect Provides a Shared Data Store

**What the LLM generates:** A statement that Marketing Cloud Connect unifies the MCE and MCAE databases, creating a single contact record across both platforms. For example: "With Marketing Cloud Connect, your MCAE prospect data and MCE subscriber data are synchronized into a unified contact record."

**Why it happens:** LLMs extrapolate from the term "connect" to assume data unification. MC Connect is described as an integration mechanism, which LLMs associate with data merging.

**Correct pattern:**

```
Marketing Cloud Connect creates sending and reporting bridges between MCE and MCAE.
It does NOT merge the underlying data stores.

- MCAE data store: MCAE database, synced to Salesforce CRM Leads/Contacts
- MCE data store: Data Extensions in the MCE business unit

After MC Connect is configured:
- MCAE prospect lists can be used as MCE sending audiences
- MCE send results (opens, clicks, bounces) can be returned to MCAE prospect activity history
- The underlying records in each data store remain separate and must be managed independently
```

**Detection hint:** Flag any claim that MC Connect "unifies," "merges," "shares," or "synchronizes data between" MCE and MCAE data stores.

---

## Anti-Pattern 4: Claiming Features Transfer Between Platforms

**What the LLM generates:** A statement that MCAE capabilities (scoring, grading, Engagement Studio) are available in MCE through configuration or add-ons, or vice versa. For example: "You can enable lead scoring in Marketing Cloud Engagement by using Einstein and configuring the scoring rules in Journey Builder."

**Why it happens:** LLMs conflate Einstein Lead Scoring (a Sales Cloud feature predicting conversion likelihood from historical data) with MCAE's Scoring (activity-based numeric points per engagement action). They also extrapolate from the general principle that Salesforce products are configurable to conclude that capabilities can be ported between them.

**Correct pattern:**

```
Capabilities exclusive to MCAE — not available in MCE:
- Scoring (activity-based numeric score, e.g., +20 per email click)
- Grading (profile-based letter grade A–F based on explicit criteria)
- Engagement Studio (rule-based prospect-level nurture programs)
- Native bidirectional Salesforce Lead/Contact field sync with configurable sync rules
- Prospect-level CRM activity logging

Capabilities exclusive to MCE — not available in MCAE:
- SMS / MobileConnect
- Push notifications / MobilePush
- Advertising audiences / Advertising Studio
- Interaction Studio / Personalization
- Journey Builder (multi-channel, event-driven, at scale)

There is no configuration path to port these capabilities from one platform to the other.
```

**Detection hint:** Flag any claim that a platform-specific capability (scoring, grading, SMS, push, Journey Builder) can be "enabled," "configured," or "added" in the other platform.

---

## Anti-Pattern 5: Ignoring License Requirements When Recommending Both Platforms

**What the LLM generates:** A recommendation to use both MCE and MCAE without noting that each requires its own license, or a suggestion that "upgrading" to a higher edition of one unlocks access to the other. For example: "To get both Journey Builder for high-volume sends and lead scoring, just upgrade to Marketing Cloud Advanced — that includes both."

**Why it happens:** LLMs pattern-match to "upgrade for more features" logic common in SaaS products. They also underestimate the complexity of Salesforce's multi-product licensing model.

**Correct pattern:**

```
MCE and MCAE are separately licensed products. There is no single edition or SKU that
includes both.

To use both platforms:
1. A Marketing Cloud Engagement license is required (edition: Basic, Pro, Corporate, Enterprise,
   or Marketing Cloud Advanced).
2. A Marketing Cloud Account Engagement license is required separately (Growth, Plus, Advanced,
   or Premium edition).
3. Marketing Cloud Connect must be configured to enable the cross-platform sending bridge.

Each license is independently priced. Recommend verifying current Salesforce pricing with
an Account Executive before finalizing the platform recommendation.
```

**Detection hint:** Flag any recommendation to use both platforms that does not explicitly state both licenses are required. Also flag any claim that one license "includes" access to the other.

---

## Anti-Pattern 6: Conflating "Marketing Cloud" Branding with MCE Specifically

**What the LLM generates:** Advice that assumes a customer who says "we have Marketing Cloud" specifically has MCE (with Journey Builder, Email Studio, etc.) when they may have MCAE only, or vice versa.

**Why it happens:** The "Marketing Cloud" brand name is applied to multiple products. LLMs default to MCE when they hear "Marketing Cloud" because MCE is the flagship product associated with that brand.

**Correct pattern:**

```
During discovery, always confirm the exact products licensed:
- Marketing Cloud Engagement (MCE): login at mc.exacttarget.com or mc.salesforce.com — includes
  Journey Builder, Email Studio, Contact Builder, Automation Studio
- Marketing Cloud Account Engagement (MCAE): accessed via Salesforce App Launcher → Account
  Engagement — includes Engagement Studio, Pardot Forms, Scoring/Grading

Verification: Setup → Company Information → Permission Set Licenses (look for
"Marketing Cloud" vs. "Pardot" / "Account Engagement" license entries)

Never assume product from the brand name alone.
```

**Detection hint:** Flag any advice that treats "Marketing Cloud" as a synonym for MCE without first confirming the customer's licensed products.
