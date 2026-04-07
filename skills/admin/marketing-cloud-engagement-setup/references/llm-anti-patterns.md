# LLM Anti-Patterns — Marketing Cloud Engagement Setup

Common mistakes AI coding assistants make when generating or advising on Marketing Cloud Engagement Setup.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Confusing Marketing Cloud Engagement With MCAE (Pardot/Account Engagement)

**What the LLM generates:** Instructions to "go to Account Engagement Setup" or "use Pardot Business Units" when the user is asking about Marketing Cloud Engagement Business Units. Or vice versa: suggesting Marketing Cloud Engagement Sender Profiles to a user who is configuring MCAE prospect routing.

**Why it happens:** Both products carry the "Marketing Cloud" brand name. Training data contains overlapping terminology. "Business Unit" appears in both products but means different things (MCAE Business Units are licensing/tenant partitions; MC Engagement BUs are operational send containers).

**Correct pattern:**

```
Marketing Cloud Engagement (formerly ExactTarget):
  - Used for: B2C email at scale, Journey Builder, Email Studio
  - Business Units: operational isolation, each has own subscribers and content
  - Setup: https://mc.exacttarget.com

Marketing Cloud Account Engagement (formerly Pardot):
  - Used for: B2B marketing automation, lead nurturing, scoring
  - Business Units: multi-org tenant partitions for MCAE
  - Setup: within Salesforce CRM Setup > Account Engagement

These are separate products. Never conflate instructions for one with the other.
```

**Detection hint:** If the user mentions Journey Builder, Email Studio, Sender Profiles, or ExactTarget — that is MC Engagement. If they mention Pardot, prospects, scoring, or Account Engagement — that is MCAE.

---

## Anti-Pattern 2: Claiming Admins Can Self-Provision New Business Units from Setup UI

**What the LLM generates:** Step-by-step instructions like "In Marketing Cloud Setup, click Business Units > New, then fill in the BU name and locale…" with a screenshot description of a New button that does not exist.

**Why it happens:** LLMs generalize from other Salesforce products where objects like users, profiles, and permission sets can be created from the Setup UI. They extrapolate that BUs would follow the same self-service pattern.

**Correct pattern:**

```
New Business Unit provisioning in Enterprise 2.0:
1. Open a Salesforce Support case.
2. Provide: BU name, locale, sending domain, brand contact name and email, parent account ID.
3. Wait for Salesforce to provision the BU (typically 1–3 business days).
4. After provisioning, configure Sender Profiles, Delivery Profiles, and Send Classifications within the new BU.

There is no self-service New button for Business Units in Marketing Cloud Engagement Setup.
```

**Detection hint:** Any instructions that include "click New" or "create a new Business Unit from Setup" for MC Engagement are incorrect.

---

## Anti-Pattern 3: Treating Transactional Send Classification as a Performance Optimization

**What the LLM generates:** Advice like "Use the Transactional Send Classification for high-priority emails to improve deliverability speed" or "Set sends to Transactional if you want them to go out faster." Some outputs describe Transactional as a "priority queue."

**Why it happens:** The word "transactional" in common usage implies speed and reliability. LLMs map this to the idea of a faster-delivery mechanism rather than a legal opt-out bypass designation.

**Correct pattern:**

```
Transactional Send Classification:
  - Purpose: bypass the commercial unsubscribe list for LEGALLY transactional messages
  - Approved uses: order confirmations, shipping updates, password resets, security alerts
  - NOT a performance tier — delivery speed is not affected
  - CAN-SPAM implication: using Transactional for any promotional or marketing content
    is a legal violation that can result in account suspension

Use Commercial Send Classification for all marketing, promotional, or opt-in content.
```

**Detection hint:** Any description of Transactional as "faster," "priority," or "more reliable" is incorrect framing.

---

## Anti-Pattern 4: Assuming Unsubscribes Propagate Account-Wide Across All Business Units

**What the LLM generates:** Reassurance like "Once a subscriber opts out, Marketing Cloud will honor that preference across your entire account and all Business Units automatically."

**Why it happens:** This is the expected behavior in simpler email systems and seems like the reasonable default. LLMs extrapolate from the concept of a global unsubscribe without knowing that MC Engagement implements it per-BU.

**Correct pattern:**

```
MC Engagement unsubscribe scope:
  - An unsubscribe from BU A is recorded in BU A's All Subscribers list only.
  - BU B's All Subscribers list for the same email address is NOT automatically updated.
  - The subscriber will continue to receive commercial emails from BU B.

If account-wide unsubscribe propagation is required:
  - Build a custom Automation Studio process to sync unsubscribes across BU All Subscribers lists.
  - Or maintain a shared suppression data extension and reference it in all sends.

This is NOT provided natively by the platform.
```

**Detection hint:** Phrases like "global unsubscribe propagates to all BUs" or "account-wide opt-out is automatic" are incorrect for MC Engagement Enterprise 2.0.

---

## Anti-Pattern 5: Recommending Custom Roles That Can Be Applied Account-Wide

**What the LLM generates:** Instructions to "create a custom role in the parent BU and it will be available to assign in all child Business Units" or "define your custom role once and apply it across the account."

**Why it happens:** Other Salesforce platforms (Sales Cloud profiles, permission sets) can be defined once and assigned across the org. LLMs generalize this pattern to MC Engagement custom roles.

**Correct pattern:**

```
MC Engagement custom role scope:
  - Custom roles are created within a specific Business Unit.
  - A custom role created in BU A does NOT appear in BU B's role assignment dropdown.
  - There is no account-level custom role template or import mechanism.

Correct approach:
  1. Document the custom role configuration (name, base role, specific permission overrides).
  2. Recreate the custom role in each BU where it is needed.
  3. Maintain a role runbook so consistent configurations can be replicated as new BUs are added.
```

**Detection hint:** Any claim that custom roles are "account-level" or "inherited by child BUs" is incorrect.

---

## Anti-Pattern 6: Describing Physical Address as an Email Template Requirement Instead of a Delivery Profile Setting

**What the LLM generates:** Instructions like "Add your company's physical mailing address to each email template footer to comply with CAN-SPAM" or "Create a template variable for the mailing address and populate it before each send."

**Why it happens:** In many email systems, the physical address is added as static content in each template. LLMs carry this assumption into MC Engagement advice.

**Correct pattern:**

```
MC Engagement CAN-SPAM physical address:
  - The physical mailing address is configured on the Delivery Profile, not the email template.
  - When the Delivery Profile is applied via the Send Classification, MC Engagement
    automatically inserts the physical address into the email footer at send time.
  - You do NOT need to manually add the address to every template.

To configure:
  Email Studio > Admin > Delivery Profiles > Edit > Physical Mailing Address fields
```

**Detection hint:** Any instruction to "add the mailing address to your template" for CAN-SPAM compliance in MC Engagement is misplacing the responsibility.
