# Examples — Marketing Cloud Engagement Setup

## Example 1: Multi-Brand Enterprise — Isolating Two Brands Under One MC Account

**Context:** A retail holding company operates two distinct consumer brands — one for apparel and one for home goods — under a single Marketing Cloud Engagement Enterprise 2.0 account. The marketing teams for each brand must not see the other's subscriber data, templates, or campaign results. Both brands share a single dedicated IP.

**Problem:** The initial setup used a single Business Unit with two data extensions (one per brand). Marketing coordinators for Brand A could browse Brand B's data extensions and email templates. An accidental send to the wrong data extension exposed Brand A subscribers to Brand B messaging, damaging brand perception and triggering subscriber complaints.

**Solution:**

Two separate Business Units — `BrandA-US` and `BrandB-US` — were provisioned via a Salesforce Support case. Each BU received:

- Its own Sender Profile: `From Name: Brand A` / `from@branda.com` and `From Name: Brand B` / `from@brandb.com`
- Its own Delivery Profile referencing the shared dedicated IP and each brand's legal physical address
- Its own Commercial Send Classification linking the above profiles
- User role assignments scoped to the BU (Brand A marketers assigned only to `BrandA-US`)

```
BrandA-US BU:
  Sender Profile:    Brand A Mailer (from@branda.com)
  Delivery Profile:  BrandA-Delivery (123 Commerce St, Atlanta GA 30301)
  Send Classification: BrandA-Commercial (Type: Commercial)
  Users: brandA-team-members (role: Content Creator or Administrator)

BrandB-US BU:
  Sender Profile:    Brand B Mailer (from@brandb.com)
  Delivery Profile:  BrandB-Delivery (456 Market Ave, Chicago IL 60601)
  Send Classification: BrandB-Commercial (Type: Commercial)
  Users: brandB-team-members (role: Content Creator or Administrator)
```

**Why it works:** Business Unit isolation is enforced at the platform level — users assigned to BU A cannot see or access BU B's data extensions, content, or subscriber lists without an explicit role assignment in that BU. The shared dedicated IP means both brands contribute to the same sender reputation, so list hygiene practices must be coordinated across teams even though data is isolated.

---

## Example 2: Transactional Send Classification for Order Confirmation Emails

**Context:** An e-commerce company sends order confirmation emails through Marketing Cloud Engagement. These emails must reach customers regardless of whether those customers have opted out of marketing emails. The existing setup uses the default Commercial Send Classification for all sends.

**Problem:** Customers who unsubscribed from marketing emails stopped receiving order confirmations. Customer service volume increased significantly as customers could not confirm their purchase details. The company was at risk of violating its own terms of service (guaranteed order confirmation delivery).

**Solution:**

A dedicated Transactional Send Classification was created for order confirmation emails:

1. Created a new Sender Profile: `From Name: Brand Orders` / `orders@brand.com` (separate from-address for clarity)
2. Reused the existing Delivery Profile (same physical address, same IP)
3. Created a new Send Classification:
   - Name: `Brand-Transactional`
   - Type: **Transactional**
   - Sender Profile: `Brand Orders`
   - Delivery Profile: `Brand-Delivery`
   - Unsubscribe Profile: standard (transactional emails still include unsubscribe link for CAN-SPAM, but commercial unsubscribe status is ignored)

```
Send Classification: Brand-Transactional
  Type:              Transactional
  Sender Profile:    Brand Orders (orders@brand.com)
  Delivery Profile:  Brand-Delivery (physical address present)
  Note:              Use ONLY for order confirmations, shipping updates, password resets
```

The triggered send definition for the order confirmation journey was updated to reference `Brand-Transactional`.

An internal policy document was created listing the approved message types for Transactional classification: order confirmations, shipping updates, password resets, account security alerts.

**Why it works:** A Transactional Send Classification bypasses the commercial unsubscribe list, ensuring delivery to all subscribers including those who have globally opted out of marketing. The separate `orders@brand.com` from-address makes the transactional nature of the message immediately recognizable to subscribers and inbox providers, reducing spam complaint rates on these sends.

---

## Anti-Pattern: Using One BU with Folders Instead of Separate Business Units

**What practitioners do:** To avoid the delay and overhead of opening a Salesforce Support case for new BUs, administrators create a single BU and use folder structures within Email Studio to simulate brand separation. They name folders `Brand-A/` and `Brand-B/` and manually train users to only access their folder.

**What goes wrong:** Folder-based access control in Marketing Cloud Engagement is not enforceable at the platform level — any user with Content Creator or higher role can navigate to any folder. One misclick or incorrect data extension selection causes a cross-brand send. Subscriber lists are commingled in the single All Subscribers list, making CAN-SPAM unsubscribe management ambiguous (which brand's opt-out was intended?). Sender Profiles are also shared, so from-address combinations that belong to one brand are visible to the other team's users.

**Correct approach:** Provision separate Business Units for distinct brands, subscriber populations, or compliance boundaries. Open a Salesforce Support case with the BU name, locale, sending domain, and business justification. The 1–3 business day provisioning lead time is a one-time cost; the folder workaround creates ongoing operational and compliance risk.
