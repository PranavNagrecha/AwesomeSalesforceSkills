# Mobile Publisher — Work Template

Use this template when planning a Mobile Publisher build, submission, or maintenance cycle.

UNVERIFIED (2026-10-21): the two templates, the shell release schedule and the Approach checks are Help-only; the push fields and the `nativeConfig.json` update flags are grounded (api_meta 264 L68456-68504, L62894-62917).

## Scope

**Skill:** `mobile-publisher`

**Request summary:** (fill in what the user asked for)

## Context Gathered

- Mobile Publisher template: Experience Cloud (LWR/Aura) | Field Service
- Distribution: Apple App Store + Google Play | Apple Enterprise | Managed Google Play | combination
- Customer-owned developer accounts confirmed: Apple Developer (Org tier) | Google Play developer
- Source experience identified (Experience Cloud site name or FSL surface):
- Push-notification scope: launch requirement | post-launch | not in scope
- Bundle ID convention chosen and reserved on both stores:

## Approach

- [ ] Standard Salesforce Mobile App ruled out (audience or branding requirement justifies Mobile Publisher)
- [ ] Custom-native ruled out (capability set is within Mobile Publisher scope)
- [ ] Underlying source experience verified working in standard Salesforce Mobile App / standard FSL Mobile

## Branding Asset Checklist

UNVERIFIED (2026-10-21): the sizes, name lengths and deletion/privacy requirements in this checklist are Apple and Google policy, not in the corpus; re-check the current store guidelines.

- [ ] App icon iOS 1024×1024 PNG (no alpha channel)
- [ ] App icon Android 512×512 PNG
- [ ] Android adaptive icon foreground 432×432
- [ ] Android adaptive icon background 432×432
- [ ] Splash / launch image variants per device family
- [ ] App name ≤ 30 chars (App Store), ≤ 50 chars (Play)
- [ ] Primary, accent, background hex colors defined
- [ ] Privacy policy URL live and reachable
- [ ] Account-deletion path live (in-app self-service)

## Push Configuration

- [ ] APNs `.p8` private key (or `.p12` TLS certificate + password) generated under customer's Apple Developer account
- [ ] Key ID + team ID + bundle ID and APNs `environment` (Production or Sandbox) entered in the push configuration
- [ ] Firebase project ID + service-account Admin SDK private key (Base64) from the customer's Firebase project
- [ ] Credentials entered in each org that holds its own push configuration — they cannot be packaged or kept in source control; a retrieved record keeps only `pushConfigLink`
- [ ] Test push delivered end-to-end through TestFlight + Play Internal Testing
- [ ] Synthetic monitor in place to alert on delivery failures post-launch

## Submission Checklist

UNVERIFIED (2026-10-21): the reviewer-account, privacy-questionnaire and screenshot requirements below are store policy.

- [ ] Fallback test account provisioned with bypassed MFA for App Store reviewer
- [ ] Reviewer credentials documented in App Store submission notes
- [ ] Review notes describe how to reach core functionality from a cold-start state
- [ ] Privacy questionnaire completed (App Privacy + Play Data Safety)
- [ ] Account-deletion path documented in submission notes
- [ ] Screenshots captured at required device sizes (iPhone, iPad, Android phone, tablet)

## Operational Plan

- [ ] Resubmission cadence aligned with Salesforce native shell release schedule
- [ ] Owner named per store for submission, push-cert renewal, and OS-version policy
- [ ] `enableAppUpdate` / `forceAppUpdate` in the site's `nativeConfig.json` tested in non-production
- [ ] TestFlight expiration tracker in place (90-day reminder; UNVERIFIED (2026-10-21): Apple policy)

## Notes

Record deviations: enterprise distribution choice, IdP-only login fallback strategy, capability gaps that surfaced during the underlying-experience verification.
