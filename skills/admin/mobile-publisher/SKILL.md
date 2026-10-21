---
name: mobile-publisher
description: "Use when planning, configuring, or maintaining a Salesforce Mobile Publisher branded app — a customer-facing or partner-facing mobile app distributed through Apple App Store or Google Play, built on either the Experience Cloud (LWR/Aura) Mobile Publisher template or the Field Service Mobile Publisher template. Triggers: 'salesforce mobile publisher branded app', 'experience cloud mobile app store distribution', 'mobile publisher push notifications certificate', 'app store review rejection salesforce', 'mobile publisher version policy update'. NOT for the standard mobile app — use admin/lightning-app-builder-advanced. NOT for Field Service mobile — use admin/fsl-mobile-app-setup."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Security
triggers:
  - "configure mobile publisher branded app for experience cloud"
  - "salesforce mobile publisher push notification certificate APN FCM"
  - "mobile publisher app store rejection review process"
  - "mobile publisher version update salesforce minimum version"
  - "white label salesforce app distribute apple play store"
  - "mobile publisher app icon splash screen branding configuration"
tags:
  - admin
  - mobile-publisher
  - experience-cloud
  - mobile
  - app-store
  - branding
inputs:
  - "the source surface being published (Experience Cloud site, Field Service mobile flow)"
  - "target distribution: Apple App Store, Google Play, enterprise / private distribution"
  - "branding assets: app icon (multiple sizes), splash screen, color scheme, app name"
  - "push-notification provider details (APN team / key ID for iOS, FCM project for Android)"
outputs:
  - "Mobile Publisher build configuration with reviewed branding asset set"
  - "App Store / Play Store submission checklist with reviewer notes"
  - "release plan covering minimum-version policy, push-cert renewal cadence, OS-version drop"
  - "documented disambiguation between Mobile Publisher, the standard Salesforce Mobile App, and FSL Mobile"
dependencies: []
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-10-21
---

# Mobile Publisher

Activate when a Salesforce customer needs a branded mobile app distributed through the public app stores (or through enterprise distribution) that wraps an Experience Cloud site or Field Service mobile experience. The skill produces the build-configuration plan, the asset checklist, and the operational runbook for ongoing version maintenance — and clearly distinguishes Mobile Publisher from the standard Salesforce Mobile App and from Field Service Mobile.

**Grounding status.** The corpus names Mobile Publisher in one place: an Experience Cloud site's `ExperienceBundle` carries a `nativeConfig.json` whose Required `mobilePublisherAppUpdateConfig` container holds `enableAppUpdate` (show an optional update message), `forceAppUpdate` (require the update) and `minVersion` (iOS/Android minimum app versions, "currently hard coded" to versions that support enhanced domains), plus `nativeTabMenu.branding` tint colours (api_meta 264 L62823-62825, L62894-62917, L62932-62936). UNVERIFIED (2026-10-21): everything else about the product — its SKU, its two templates, its build pipeline, its Setup page and its shell-release cadence — is Help-only throughout this package. Apple and Google store rules (review times, asset sizes, name lengths, TestFlight expiry, account-deletion rules, fees) are third-party policy outside the corpus and are unverified wherever they appear. What the corpus does hold is the platform's own push plumbing, cited inline below.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Which Mobile Publisher template** is in scope: Experience Cloud (LWR or Aura), or Field Service. The two templates are sold and packaged separately, share some configuration but differ in capabilities (UNVERIFIED (2026-10-21): Help-only packaging claim).
- **Distribution model:** Apple App Store + Google Play (public), enterprise distribution (Apple Developer Enterprise Program, managed Google Play), or both. Public distribution requires Apple/Google developer accounts owned by the customer (UNVERIFIED (2026-10-21): store policy, not in corpus).
- **Push-notification scope:** are notifications a launch requirement? The platform's push-configuration types take credentials from the customer's own accounts: a Google Firebase project ID plus that project's service-account private key for Android, and an Apple Developer team ID plus a `.p8` key or `.p12` certificate for iOS (api_meta 264 L68456-68461, L68468-68471, L68503-68504).
- **Existing app, or net-new?** A net-new app has a clean slate. Replacing an existing native or hybrid app raises continuity questions: deep links, push subscriptions, identity migration, App Store Connect / Play Console transfer.

---

## Questions to Ask Before Configuring

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| How will the store reviewer sign in if the site login is SSO-only? | Gotcha 1: a reviewer who cannot finish the IdP flow rejects the build (UNVERIFIED (2026-10-21): Apple guideline behaviour) | A named fallback test account and the review-notes text |
| Who owns the APNs key or certificate and the Firebase service account, and who rotates them? | Gotcha 2: a rotated credential not re-entered in Salesforce stops delivery | An owner, a rotation date, and a test-push step after each rotation |
| Who resubmits each store build when Salesforce ships a new shell, and on what cadence? | Gotcha 3: skipped shell updates lead to store notices (UNVERIFIED (2026-10-21): Help-only support-window claim) | A per-store owner and a calendar slot after each release |
| For the Field Service template, is every needed capability already working in the standard Field Service app? | Gotcha 4: branding does not add a capability the source lacks | A verified capability list before the branding work starts |
| What bundle ID will the app ship under, and does it survive a rebrand? | Gotcha 5: the store will not rename a bundle ID in place (UNVERIFIED (2026-10-21): store policy) | A bundle ID convention signed off by the brand owner |
| Where in the site does a user delete their own account? | Gotcha 6: both stores reject apps without an in-app deletion path (UNVERIFIED (2026-10-21): store policy) | The page, the confirmation step and the reversal window |
| How long will the TestFlight acceptance cycle run? | Gotcha 7: TestFlight builds expire (UNVERIFIED (2026-10-21): the 90-day figure is Apple policy) | A refresh-upload date inside the window |

Configuring with these answers turns a one-off build into an app with named owners for every credential, store and shell update, which is what keeps it in the stores after launch.

---

## Core Concepts

### What Mobile Publisher is

Mobile Publisher is a Salesforce service that takes an Experience Cloud site (or a Field Service mobile experience) and produces native iOS and Android binaries with the customer's branding, distributed under the customer's developer account on the App Store and Google Play. Salesforce hosts the build pipeline; the customer owns the app-store presence, the developer accounts, the push certificates, and the user reviews. UNVERIFIED (2026-10-21): this division of ownership is Help-only.

It is paid as a separate SKU and tied to the source experience (Experience Cloud or Field Service). The native shell is updated on Salesforce's release cadence; the customer's content updates flow through Experience Cloud / Field Service publishing without an app-store resubmission, *unless* the change touches the native shell (icon, splash, push, deep links, certain plugins). UNVERIFIED (2026-10-21): the SKU, the shell cadence and the list of shell-only changes are not in the corpus.

### What Mobile Publisher is NOT

- **Not the standard Salesforce Mobile App.** That app is "Salesforce" branded, distributed by Salesforce, and configured via Salesforce App Manager + App Settings. It customizes via Lightning App Builder, mobile navigation menus, and quick actions. Mobile Publisher produces a *separate, customer-branded* app.
- **Not a generic mobile app builder.** The source must be an Experience Cloud site or Field Service mobile flow. You cannot point Mobile Publisher at an arbitrary Lightning app, an internal Sales Cloud surface, or a custom Lightning app page outside Experience Cloud.
- **Not the Field Service Lightning Mobile customization story.** FSL Mobile is the standard FSL app's offline / scheduling / asset-tracking configuration. Mobile Publisher for Field Service is a *re-skinned, customer-distributed* version of that same experience under the customer's brand.
- **Not Apple Developer or Google Play account ownership.** The customer owns those accounts. Salesforce builds binaries on behalf of the customer; submission and review happen under customer credentials.

UNVERIFIED (2026-10-21): the four distinctions above are Help-only. The corpus confirms only that branding records (`CustomBrandAsset`) apply "to an Experience Cloud site or to an org using the Salesforce mobile app" (object_reference 264 L87781-87782).

### The build / submit / maintain cycle

1. **Build** — Mobile Publisher produces an iOS `.ipa` and an Android `.aab` from the configured branding + source experience. Salesforce engineers handle compilation; the customer reviews the build artifact in a TestFlight / Play Internal Testing track. UNVERIFIED (2026-10-21): build formats and the hand-off are Help-only.
2. **Submit** — The customer submits to App Store Connect / Google Play Console under their developer account. Apple's review averages 1–3 days; Google's averages hours to a day. Rejections are most often around: privacy policy URL, account-deletion path (required by both stores), in-app purchase compliance, and login flow clarity. UNVERIFIED (2026-10-21): review times and rejection causes are store-side observations, not in the corpus.
3. **Maintain** — Native shell updates on the Salesforce-driven cadence (typically 2–3× per year). The customer is responsible for resubmission to the stores within the support window. UNVERIFIED (2026-10-21): the cadence and the support window are Help-only. On credentials: the platform's iOS push type accepts either a `.p8` private key or a `.p12` TLS certificate (api_meta 264 L68468-68471); whether each expires is Apple policy (UNVERIFIED (2026-10-21)). A stale credential stops delivery, so tie every rotation to a Salesforce-side update.

---

## Common Patterns

### Mapping branding requirements to the asset set

| Asset | Spec | Where it lands |
|---|---|---|
| App icon | iOS 1024×1024 PNG (no alpha), Android 512×512 PNG | Both stores' product pages |
| Adaptive icon (Android) | 432×432 foreground + 432×432 background layers | Android home screen |
| Splash / launch image | Aspect-ratio variants per device family | First-paint screen on launch |
| App name | ≤ 30 chars (App Store), ≤ 50 chars (Play) | Store listing + home screen |
| Color scheme | 6-digit hex for `iconTintColor`, `iconTintColorUnselected`, `barTintColor` (api_meta 264 L62932-62936) | Native tab bar (`nativeTabMenu.branding` in the site's `nativeConfig.json`) |
| Privacy policy | Public URL | Required by both stores; rejection if missing |

UNVERIFIED (2026-10-21): every size, character limit and store requirement in this table (all rows but Color scheme) is Apple or Google policy, not in the corpus — confirm against the current store guidelines before commissioning assets.

### Push-notification configuration

The platform's push-credential types are documented on the External Client App push plugin (`ExtlClntAppPushSettings`, a pilot or beta type, API 64.0+, api_meta 264 L68370, L68394). UNVERIFIED (2026-10-21): that Mobile Publisher Settings stores its credentials in these types; the fields below are what the platform asks for.

- **iOS (APNs):** either a `.p8` private key (`signingKey` + `keyIdentifier` + `teamIdentifier`) or a `.p12` TLS certificate (`certificate` + `password`), plus a Required `environment` of `Production` or `Sandbox` (api_meta 264 L68468-68471, L68480-68483). `applicationBundle` is "the bundle ID of the iOS mobile app from Apple App Store Connect" (L68474). Earlier text called `.p12` "legacy"; the platform type accepts both. UNVERIFIED (2026-10-21): whether `.p8` keys expire is Apple policy.
- **Android (FCM):** `fcmProject` (the Firebase project ID) and `serviceAccount` ("the Base64-encoded Admin SDK private key" for the Firebase service account, max 8,000 characters) are both Required (api_meta 264 L68456-68462). Earlier text offered a "Server Key (legacy)" option; the platform's Android push type has no server-key field. UNVERIFIED (2026-10-21): how the Android `applicationId` is set for a Mobile Publisher build.
- **Credentials do not travel in a package.** APNs and Firebase credentials "can't be packaged or added to source control" (pkg2_dev 264 L9467-9469). A retrieved `ExtlClntAppPushSettings` keeps only `pushConfigLink` (org ID:record ID), so the destination org "refers to the information in the source org" (api_meta 264 L68408-68411, L68426-68431); enter credentials in an org only where it holds its own push configuration.
- **Device tokens:** each registered device's push token is `MobileDeviceAppRegistration.DeviceSystemToken`, which APNs or FCM "uses ... to deliver messages to the device" (object_reference 264 L186403-186410).
- **Test path:** TestFlight / Play Internal Testing must receive a test notification *before* App Store submission. A push pipeline that fails silently in production is a top support escalation.

### Version-policy decisions

The native shell carries a *minimum supported OS version* and a *target OS version*. Mobile Publisher inherits these from Salesforce's current release. UNVERIFIED (2026-10-21): Help-only; the corpus's `minimumOsVersion` field belongs to a connected app's mobile settings (`MobileApplicationDetail`, api_meta 264 L91671, L91719), not to Mobile Publisher. Customers should:

- Track the **minimum OS version** Salesforce supports — older OS users will be unable to install/update the app once it shifts.
- Plan a **forced-update strategy** for security-critical updates: the site's `nativeConfig.json` sets `enableAppUpdate` true with `forceAppUpdate` false to encourage an update, or both true to require it (api_meta 264 L62898-62913); keep it opt-in unless mandatory.
- Document the **resubmission cadence** and assign ownership: missing two cycles can mean Apple or Google takes the app down for "outdated platform support."

UNVERIFIED (2026-10-21): the OS-version shift and the store takedown after two missed cycles are Help-only or store-side claims with no corpus line; the update flags are grounded above, and `minVersion` is the minimum *app* version, not an OS version (L62915-62917).

---

## Decision Guidance

| Situation | Choice | Rationale |
|---|---|---|
| Customer wants their employees to use Salesforce CRM on mobile | Standard Salesforce Mobile App | Free, self-service customization, no app-store overhead |
| External partners need a branded app to access partner-portal records | Mobile Publisher (Experience Cloud) | Customer brand on stores; partners don't see Salesforce branding |
| Field Service techs need offline scheduling + custom branding | Mobile Publisher (Field Service) | Re-skinned FSL Mobile; full FSL capabilities + customer brand |
| Need an arbitrary mobile app with custom screens unrelated to Salesforce | Custom native dev (out of scope) | Mobile Publisher requires Salesforce-side source experience |
| Distribute a private app to internal employees only | Standard Salesforce app + MAM, or enterprise Mobile Publisher | Public stores not required for employee use |
| App Store rejected for "missing account deletion" | Add account-deletion path in Experience Cloud + resubmit | Both stores require an in-app deletion path; not optional |

UNVERIFIED (2026-10-21): the SKU fits, the "free" standard app and the store deletion rule in this table are Help-only or store policy. The earlier rationale named "Apple ATT" (App Tracking Transparency, a tracking-consent rule, not account deletion) and a "2024+" date for both stores; both are dropped as ungrounded.

---

## Recommended Workflow

1. Confirm the source experience type (Experience Cloud vs Field Service). This drives template choice, pricing, and capability set.
2. Confirm the customer owns Apple Developer + Google Play developer accounts. If not, surface this as a 2–4 week prerequisite — account approval is not instant (UNVERIFIED (2026-10-21): store-side lead time).
3. Inventory branding assets against the spec table. Missing assets are the top cause of build delay; commission them up front.
4. Configure push-notification credentials in a non-production org first — the iOS type's Required `environment` is `Production` or `Sandbox` (api_meta 264 L68480-68483); the credentials cannot be packaged (pkg2_dev 264 L9467-9469), so either enter them in the org or keep only `pushConfigLink` in the retrieved settings (api_meta 264 L68408-68411). Test send-and-receive end-to-end through TestFlight + Play Internal Testing before invoking the production build.
5. Draft store-listing copy: app name, subtitle, description, keywords, screenshots (at least 3 per device family). Include privacy policy URL and account-deletion URL — both are mandatory (UNVERIFIED (2026-10-21): store policy, including the screenshot count).
6. Submit to TestFlight + Play Internal Testing first. Verify deep links, push, and login flow on real devices. Production submission only after the test track passes.
7. Run `python3 skills/admin/mobile-publisher/scripts/check_mobile_publisher.py --manifest-dir force-app` on the source site's metadata, then document the resubmission cadence, push-credential owners, and minimum-OS-version policy in a runbook built from `templates/mobile-publisher-template.md`. Mobile Publisher apps are operational obligations, not "build and forget."

---

## Review Checklist

- [ ] Source experience is Experience Cloud (LWR/Aura) or Field Service — not a custom Lightning app outside Experience Cloud
- [ ] Customer owns the Apple Developer and Google Play accounts (not the partner / not Salesforce)
- [ ] Branding asset set is complete, sized correctly, free of alpha channels (iOS) and properly layered (Android adaptive) (UNVERIFIED (2026-10-21): store asset rules)
- [ ] Privacy policy URL and account-deletion path are live and reachable (UNVERIFIED (2026-10-21): store policy)
- [ ] Push credentials (APNs `.p8` key or `.p12` certificate, Firebase project ID + service-account key) are tested end-to-end on the test track
- [ ] Store-listing copy is reviewed for prohibited claims (medical, financial, "as featured by Apple")
- [ ] Resubmission cadence is documented; an owner is named for each store
- [ ] `enableAppUpdate` / `forceAppUpdate` in the site's `nativeConfig.json` set deliberately and tested before going live (api_meta 264 L62898-62913)
- [ ] Login flow is clear to a reviewer who is not familiar with Salesforce — App Store reviewers reject when the path is unclear

---

## Salesforce-Specific Gotchas

- **App Store reviewer login** — Reviewers receive a test account in the submission notes. If your Experience Cloud login flow requires SSO with a third-party IdP, provide a fallback username/password test account, or expect a rejection citing "unable to test core functionality." (UNVERIFIED (2026-10-21): store review behaviour.)
- **Account deletion is mandatory** — Apple and Google require an in-app account-deletion path. The Experience Cloud site must expose a self-service deletion flow or the app will be rejected. The earlier "since iOS 16 / since 2024" dates had no source and are dropped. (UNVERIFIED (2026-10-21): store policy.)
- **Release-train misalignment** — Salesforce native-shell updates are gated by the org's release version; sandboxes preview earlier than production. A Mobile Publisher build pinned to a specific shell version may behave differently against a sandbox than against production for several weeks per year. UNVERIFIED (2026-10-21): the shell gating and the sandbox timing are Help-only; the corpus documents a preview release choice only for scratch orgs (sfdx_dev 264 L9974-9976).
- **Push token rotation breaks subscriptions** — Replacing the APNs key or FCM credential without a token-refresh roll-out can leave devices on stale registrations; each device's token lives in `MobileDeviceAppRegistration.DeviceSystemToken` (object_reference 264 L186403-186410). UNVERIFIED (2026-10-21): that a credential swap invalidates existing tokens. Plan a re-subscribe step in the rollout.
- **Bundle ID is permanent** — Once an app is on the store under `com.customer.app`, that bundle ID is sticky. Renaming requires submitting a new app and migrating users — Apple does not support bundle-ID renames in place. (UNVERIFIED (2026-10-21): store policy.)
- **TestFlight 90-day limit** — TestFlight builds expire 90 days after upload. Long-running test cycles need to factor in re-builds; otherwise testers find the app expired silently. (UNVERIFIED (2026-10-21): Apple policy.)
- **Field Service Mobile Publisher inherits FSL feature flags** — A capability disabled in the underlying FSL config (e.g. asset photo capture) cannot be re-enabled by the Mobile Publisher shell. Configure FSL first; brand it second. (UNVERIFIED (2026-10-21): Help-only.)

---

## Output Artifacts

- Mobile Publisher template selection and template-version note (Experience Cloud vs Field Service).
- Branding asset bundle conforming to the spec table.
- Push-notification credentials configuration (APNs key ID + team ID, or `.p12` certificate; Firebase project ID + service-account key) with renewal schedule.
- Store-listing copy: app name, subtitle, description, keywords, screenshots set per device family.
- Privacy policy URL + account-deletion URL.
- Release runbook: resubmission cadence, owner per store, minimum-OS-version review interval, force-update playbook.

---

## Related Skills

- `admin/lightning-app-builder-advanced` — for the standard Salesforce Mobile App's customization (no app-store path).
- `admin/fsl-mobile-app-setup` — for Field Service Lightning's standard mobile app config (the underlying FSL surface that FSL-flavored Mobile Publisher re-skins).
- `lwc/experience-cloud-authentication` — login-flow patterns for Experience Cloud, the source surface most Mobile Publisher Experience Cloud apps wrap.
- `admin/experience-cloud-seo-settings` — Experience Cloud configurations that surface when the same site is the source for a Mobile Publisher app and a public website.
