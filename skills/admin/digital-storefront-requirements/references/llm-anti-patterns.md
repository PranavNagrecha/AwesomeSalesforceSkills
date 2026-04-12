# LLM Anti-Patterns — Digital Storefront Requirements

Common mistakes AI coding assistants make when generating or advising on Salesforce B2C Commerce digital storefront requirements. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Claiming SFRA Bootstrap 4 Satisfies WCAG 2.1 AA

**What the LLM generates:** "SFRA uses Bootstrap 4 which is WCAG 2.1 AA compliant, so your storefront will be accessible by default."

**Why it happens:** LLMs conflate Bootstrap 4's documented accessibility features (some ARIA roles, semantic HTML) with full WCAG AA certification. Training data contains many generic statements that "Bootstrap is accessible" without the nuance that storefront-specific implementations always require additional work.

**Correct pattern:**

```
SFRA ships with Bootstrap 4, which provides some semantic HTML and ARIA landmark patterns.
However, SFRA does not certify WCAG 2.1 AA compliance for any storefront implementation.

Common WCAG AA failures in SFRA storefronts include:
- 1.4.3 Contrast (Minimum): default Bootstrap theme colors often fail 4.5:1 ratio
- 2.4.7 Focus Visible: custom components frequently lack visible focus indicators
- 4.1.3 Status Messages: dynamic cart updates lack aria-live regions in base SFRA
- 3.3.1 Error Identification: checkout form errors are not always programmatically associated

Accessibility compliance is the merchant's legal responsibility.
A professional third-party audit (Deque, Level Access) is required before launch.
```

**Detection hint:** Flag any response containing "Bootstrap 4 is accessible" or "SFRA handles accessibility" without a qualifying caveat about merchant-side audit requirements.

---

## Anti-Pattern 2: Recommending Direct Modification of app_storefront_base for Branding

**What the LLM generates:** Code snippets or instructions that edit files inside `app_storefront_base/cartridge/templates/` or `app_storefront_base/cartridge/static/` to apply branding changes.

**Why it happens:** LLMs follow the path of least resistance — the base cartridge files are visible and editable, so the model suggests editing them directly. The downstream upgrade impact is not in the immediate context window, so the model doesn't surface it.

**Correct pattern:**

```
Never modify app_storefront_base directly. All customizations must live in an overlay
cartridge following the app_custom_* naming convention:

1. Create cartridge: app_custom_[brand]
2. Copy ONLY the files that differ from app_storefront_base
3. Position in Business Manager cartridge path:
   app_custom_[brand]:app_storefront_base
4. All styling overrides go in:
   app_custom_[brand]/cartridge/static/default/css/brand.css
```

**Detection hint:** Flag any response that instructs editing a path beginning with `app_storefront_base/` or that does not mention the `app_custom_*` overlay cartridge convention.

---

## Anti-Pattern 3: Treating SFRA and PWA Kit as Interchangeable Options with No Architecture Consequence

**What the LLM generates:** "You can use either SFRA or PWA Kit — both are supported by Salesforce. Just pick the one your team prefers."

**Why it happens:** LLMs often produce artificially balanced "either/or" advice to avoid commitment. The architectural, deployment, and long-term investment differences between SFRA and PWA Kit are significant and should drive a deliberate decision, not a preference.

**Correct pattern:**

```
SFRA and PWA Kit are architecturally distinct and the choice has long-term consequences:

SFRA:
- Server-side rendered, cartridge-based, Bootstrap 4
- Deploy via WebDAV to the SFCC instance
- No PWA installability; responsive web only
- Recommended for: teams without React skills, existing SFRA investments

PWA Kit / Composable Storefront:
- React/Node.js, headless, SCAPI-driven
- Deploy to Salesforce Managed Runtime (NOT WebDAV)
- Supports PWA installability, offline, native app feel
- Salesforce-recommended for new builds as of Spring '25

Decision criteria: team skills, existing customization investment, mobile requirements,
time horizon, and composability needs.
```

**Detection hint:** Flag any response that presents SFRA and PWA Kit as equivalent without providing decision criteria, or that says "just pick whichever you prefer."

---

## Anti-Pattern 4: Scoping Einstein Recommenders as a Day-1 Launch Feature Without Data Warm-Up Caveat

**What the LLM generates:** "Add Einstein Recommenders to the homepage, PDP, and cart for personalized product recommendations at launch."

**Why it happens:** LLMs describe Einstein Recommenders based on what they do (personalize product recommendations) without surfacing the operational prerequisite: behavioral data must accumulate for 2–4 weeks before the ML model produces meaningful output. For a new storefront at launch, there is no behavioral history.

**Correct pattern:**

```
Einstein Recommenders require:
1. Separate Einstein Recommenders add-on license (confirm during requirements, not implementation)
2. Behavioral data warm-up period: 2–4 weeks of live shopper interactions before
   recommendations are populated with meaningful ML-driven results

For a new storefront launch:
- Phase 1 (launch): render fallback content in recommendation zones
  (manually curated bestsellers, new arrivals, category top-sellers from catalog data)
- Phase 2 (3–4 weeks post-launch): switch recommendation zones to Einstein-driven output
  once sufficient behavioral data has been ingested

Do NOT promise Einstein Recommenders as a day-1 launch feature for a new storefront.
```

**Detection hint:** Flag any response that mentions Einstein Recommenders as a launch feature without explicitly noting the warm-up period and fallback content requirement.

---

## Anti-Pattern 5: Advising PWA Kit Deployment via WebDAV

**What the LLM generates:** Instructions to deploy a PWA Kit build by uploading files to the SFCC instance via WebDAV at `/cartridges/`, or instructions to add PWA Kit as a cartridge in the Business Manager cartridge path.

**Why it happens:** LLMs trained on SFRA deployment patterns apply the same WebDAV/cartridge model to PWA Kit because both are described as "Salesforce Commerce Cloud storefront" technologies. The deployment model is fundamentally different and the distinction is not always explicit in training data.

**Correct pattern:**

```
PWA Kit does NOT deploy via WebDAV. It deploys to Salesforce Managed Runtime — a
separate Node.js hosting environment at runtime.commercecloud.salesforce.com.

Deployment options:
1. Managed Runtime dashboard — upload the built bundle directly
2. sfcc-ci CLI:
   sfcc-ci code:deploy --code-version <version> --instance <instance>

There is NO cartridge path entry for PWA Kit. The Managed Runtime environment is
separate from the SFCC instance. WebDAV uploads for PWA Kit code have no effect.

Common symptom of this mistake: PWA Kit bundle uploaded to WebDAV, storefront
unchanged, no errors — because the upload was simply ignored.
```

**Detection hint:** Flag any response that includes WebDAV path references or Business Manager cartridge path instructions in the context of a PWA Kit deployment.

---

## Anti-Pattern 6: Treating Experience Cloud Requirements as Interchangeable with B2C Commerce Storefront Requirements

**What the LLM generates:** Advice that conflates Salesforce Experience Cloud (Lightning Web Runtime, Digital Experiences, Community Cloud) with Salesforce B2C Commerce (SFRA, PWA Kit, Business Manager).

**Why it happens:** Both are described as "digital storefronts" or "customer-facing Salesforce experiences" in some contexts. LLMs frequently conflate them because both involve customer-facing web experiences on the Salesforce platform. The underlying infrastructure, licensing, deployment model, and development approach are entirely different.

**Correct pattern:**

```
B2C Commerce (SFCC) and Experience Cloud are entirely distinct platforms:

B2C Commerce (this skill):
- Business Manager admin interface
- SFRA or PWA Kit storefront architecture
- Cartridge-based or SCAPI-driven development
- Use case: transactional e-commerce storefront

Experience Cloud (separate skill domain):
- Lightning org with Digital Experiences enabled
- LWR (Lightning Web Runtime) or Aura pages
- Lightning components (LWC) development
- Use case: partner portals, customer communities, self-service hubs

If the user mentions WebStore, BuyerGroup, LWR, Digital Experiences, or Community Cloud,
route to the Experience Cloud skill — not this skill.
```

**Detection hint:** Flag any response to a B2C Commerce storefront question that mentions WebStore, LWR, Digital Experiences, Community Cloud, or Lightning App Builder as implementation tools.
