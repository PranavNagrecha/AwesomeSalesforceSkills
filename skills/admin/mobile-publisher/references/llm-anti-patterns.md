# LLM Anti-Patterns — Mobile Publisher

Common mistakes AI coding assistants make when generating or advising on Mobile Publisher.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Conflating Mobile Publisher with the standard Salesforce Mobile App

**What the LLM generates:** Advice that says "use Mobile Publisher to customize your Salesforce mobile app" with a how-to that references App Manager, Lightning Pages for mobile, and the standard navigation menu — features of the standard Salesforce Mobile App, not Mobile Publisher.

**Why it happens:** Both products surface in the same docs neighborhood. LLMs blend "Salesforce mobile" guidance without distinguishing the two SKUs and their distribution models.

**Correct pattern:**

- **Standard Salesforce Mobile App** = free, "Salesforce" branded, distributed by Salesforce, customized via App Manager + Lightning App Builder.
- **Mobile Publisher** = paid SKU, customer-branded, distributed by the customer on their developer accounts, source experience must be Experience Cloud or Field Service Mobile.

Use the standard app for internal Salesforce-CRM users. Use Mobile Publisher for external-facing or branded apps.

**Detection hint:** Any answer about "Mobile Publisher" that doesn't mention App Store / Play Store / customer-owned developer accounts is conflating the products.

---

## Anti-Pattern 2: Suggesting custom native screens / SDKs as a Mobile Publisher feature

**What the LLM generates:** Recommendations to "add a custom React Native module" or "embed a native SDK" inside a Mobile Publisher app, framed as a normal part of the build.

**Why it happens:** Mobile Publisher produces native binaries, and LLMs assume native binaries imply general-purpose native development.

**Correct pattern:**

Mobile Publisher templates have a fixed plugin and capability set. The customer cannot add arbitrary native code or SDKs. If the requirement is general native development, Mobile Publisher is the wrong tool — recommend a custom-native build (Swift / Kotlin) or hybrid framework (Capacitor, React Native) outside the Mobile Publisher SKU.

**Detection hint:** Any answer that talks about "embedding custom native modules" inside Mobile Publisher should be flagged. The honest answer is "you can't; consider an alternative."

---

## Anti-Pattern 3: Skipping the "customer owns the developer account" requirement

**What the LLM generates:** A getting-started checklist that skips Apple Developer / Google Play account ownership, or implies Salesforce can publish under their own developer account.

**Why it happens:** LLMs default to abstracting away "boring" prerequisites. Account ownership is not boring — it's the legal entity behind the app on the store.

**Correct pattern:**

The customer owns:
- The Apple Developer account (Organization tier, ~$99/year) under the customer's legal name.
- The Google Play developer account (~$25 one-time) under the customer's legal name.

Salesforce builds binaries on the customer's behalf. Submission, store presence, ratings, refunds, and DMCA takedowns all happen under the customer's accounts. Account approval (especially Apple) can take 2–4 weeks for a new entity. Always surface this prerequisite.

**Detection hint:** Any timeline that says "ready in 2 weeks" without verifying developer-account status is suspect.

---

## Anti-Pattern 4: Treating push-notification setup as a Salesforce-side-only task

**What the LLM generates:** Steps that configure push from Salesforce (Notification Builder, Connected App settings) and stop there, without addressing the platform-side credentials (APN AuthKey, FCM service account) that come from the customer's developer accounts.

**Why it happens:** Salesforce-side push configuration is well-documented for the standard mobile app. Mobile Publisher requires platform-side credentials in addition; LLMs may stop at the Salesforce side.

**Correct pattern:**

Push for Mobile Publisher requires three things:

1. Salesforce-side: Notification Type registration, Connected App for push, custom-notification subscription.
2. **Platform-side: APN Auth Key (`.p8`) for iOS and FCM service-account JSON for Android, both generated under the customer's developer accounts.**
3. Mobile Publisher Settings configured with the bundle ID, Team ID, Key ID (iOS), and FCM credentials (Android).

Without (2), notifications fail silently — Salesforce believes they were sent.

**Detection hint:** A push setup answer that doesn't mention APN AuthKey / FCM service-account JSON is incomplete.

---

## Anti-Pattern 5: Ignoring App Store rejection categories

**What the LLM generates:** A go-live plan that treats App Store / Play Store submission as a formality, with no contingency for rejection or guidance on what reviewers commonly cite.

**Why it happens:** LLMs treat the build artifact as the deliverable. The store review is the actual gate, and rejection is normal.

**Correct pattern:**

The top rejection categories for Mobile Publisher apps:

- App Completeness (login flow unclear to reviewer): provide a fallback test account.
- Data Collection / Privacy: have a public privacy policy URL; the in-app account-deletion flow is mandatory.
- In-App Purchase: any digital subscription that's "the way to use the app" must use Apple's IAP, not Stripe / Salesforce Order. Most B2B apps avoid this by not selling subscriptions in-app.
- Reviewer can't reach core functionality: requires data setup, demo content, or "review notes" written for someone unfamiliar with the customer's business.

Plan for 1–2 rejection cycles. Allocate a week of buffer in the launch plan.

**Detection hint:** A timeline that assumes "submit Friday, live Monday" is naive; assume two review cycles.
