# Gotchas — Mobile Publisher

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

UNVERIFIED (2026-10-21): the corpus names Mobile Publisher only for the site's app-update flags (`mobilePublisherAppUpdateConfig`, api_meta 264 L62894-62917), so the product behaviour below is Help-only, and the Apple and Google review rules are third-party policy; each gotcha is marked where it asserts one. The push-credential facts are grounded on the platform's push types (api_meta 264 L68456-68504).

## Gotcha 1: SSO logins fail App Store review without a fallback test account

**What happens:** Apple's App Store review reviewer cannot complete the SSO flow because the customer's IdP requires hardware MFA, a corporate-network-only redirect, or an enterprise certificate the reviewer doesn't have. The submission is rejected under guideline 2.1 (App Completeness). UNVERIFIED (2026-10-21): Apple guideline number and behaviour.

**When it occurs:** Any Mobile Publisher app whose Experience Cloud login is configured for IdP-only authentication. Affects most enterprise / B2B partner apps.

**How to avoid:** Provision a sandbox test account that bypasses MFA via a static OTP, or configure a username/password fallback path enabled only for accounts in a "store reviewer" permission set. Provide credentials in the App Store submission's review notes. Document this for every release; a reviewer who can't sign in is the most common rejection cause.

---

## Gotcha 2: Push notifications stop when the APNs key or certificate is rotated

**What happens:** Six months after launch, push delivery rate drops to ~0%. The Salesforce-side dashboards show "sent" but devices receive nothing. No error surfaces in Salesforce — the failure is on Apple's side after the key was rotated for security. UNVERIFIED (2026-10-21): the "sent but not delivered" symptom is a field observation, not in the corpus.

**When it occurs:** When the customer's security team rotates or revokes the APNs `.p8` key or `.p12` certificate without updating the Salesforce-side push configuration. The platform's iOS push type holds exactly one of the two (`signingKey` + `keyIdentifier` + `teamIdentifier`, or `certificate` + `password`, api_meta 264 L68468-68471), so the old value keeps being used until someone replaces it.

**How to avoid:** Document key ownership and rotation in the Mobile Publisher runbook. Tie key-rotation to a checklist that includes updating Salesforce-side configuration and re-testing through TestFlight. Add a synthetic monitor: a once-daily test push to a known device, alarm if no delivery confirmation. UNVERIFIED (2026-10-21): whether a `.p8` key expires is Apple policy; rotate on a schedule either way.

---

## Gotcha 3: Native shell upgrades require resubmission within Salesforce's support window

**What happens:** Salesforce releases a new Mobile Publisher native shell. Customer skips two release cycles ("we don't have the bandwidth"). Salesforce drops support for the older shell; customers on the older shell receive store-side notices and eventually an app removal. UNVERIFIED (2026-10-21): the support window and the removal path are Help-only or store policy.

**When it occurs:** When Mobile Publisher resubmissions are not on a scheduled cadence with assigned ownership.

**How to avoid:** Treat Mobile Publisher resubmissions as platform-maintenance work, not project-driven work. Schedule each release immediately after Salesforce's announcement. Assign an owner per store — Apple submissions and Google submissions often have different bottlenecks. Build a 30-day buffer into the customer's internal review process.

---

## Gotcha 4: FSL feature flags propagate, branding doesn't override capability

**What happens:** A Mobile Publisher (Field Service) implementation is configured with custom branding, then a missing capability surfaces ("technicians can't capture photos"). The team enables the FSL Mobile capability, expecting the branded app to inherit immediately. Nothing changes in the branded app until the next native shell rebuild. UNVERIFIED (2026-10-21): the rebuild dependency is Help-only.

**When it occurs:** Mid-implementation when the branded app and the underlying FSL configuration are tracked separately.

**How to avoid:** Configure the underlying FSL Mobile capability set *first*, verify in the standard FSL Mobile app, *then* engage Mobile Publisher for re-skinning. Branding is the last step, not the first.

---

## Gotcha 5: Bundle ID renames are not supported in place

**What happens:** A merged company changes their brand and wants to rename the app from `com.oldbrand.partners` to `com.newbrand.partners`. There is no in-place rename path (UNVERIFIED (2026-10-21): store policy; the platform records the iOS bundle ID as `applicationBundle`, api_meta 264 L68474). The customer must publish a new app, migrate users, and ask existing users to download the new app and abandon the old one.

**When it occurs:** Brand changes, M&A, and "we picked the wrong bundle ID" scenarios.

**How to avoid:** Choose the bundle ID carefully on first publish. Use a convention that anticipates brand longevity (e.g. parent-company TLD rather than product-specific). For an unavoidable rename, plan a 3–6 month migration: publish the new app, dual-publish for a transition window, deprecate the old app with a forced-update prompt that links to the new app.

---

## Gotcha 6: Account-deletion path is mandatory and platform-enforced

**What happens:** Submission is rejected with "your app does not provide an in-app account deletion path." The team adds a "Contact us to delete" page, expecting that to satisfy the requirement; resubmission is rejected again.

**When it occurs:** Apple and Google require an *in-app, self-service* account-deletion path. Email or web links are not sufficient. UNVERIFIED (2026-10-21): store policy, not in the corpus; the earlier "since iOS 16, June 2022 / since 2024" dates had no source and are dropped.

**How to avoid:** Add a Lightning page to the Experience Cloud site that lets the user initiate deletion, with a confirmation step and a 30-day soft-delete window (so support can reverse accidental deletes). Surface it in the app's account / profile menu. Document the deletion flow in the App Store submission notes — reviewers test it.

---

## Gotcha 7: TestFlight builds expire after 90 days

UNVERIFIED (2026-10-21): the 90-day TestFlight expiry is Apple policy, not in the corpus.

**What happens:** A QA team uploads a TestFlight build, runs a 60-day acceptance cycle, and forgets the upload date. After day 90, testers report the app crashes on launch. The build expired and re-distribution requires a new upload — and a new round of testing.

**When it occurs:** Long-running test cycles, slow customer approval, regulated industries with mandatory testing windows.

**How to avoid:** Plan the TestFlight cycle to fit within 90 days, or schedule a refresh upload before expiration. Apple does not extend the limit. Calendar a reminder 14 days before expiry.
