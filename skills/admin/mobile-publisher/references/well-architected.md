# Well-Architected Notes — Mobile Publisher

UNVERIFIED (2026-10-21): the shell-maintenance, native-module, distribution and branding-scope claims in the pillar and tradeoff notes below are Help-only; only the push-credential and packaging facts carry corpus lines.

## Relevant Pillars

- **Operational Excellence** — Mobile Publisher apps require ongoing maintenance: native shell upgrades resubmitted to the stores, push certificate rotation, OS-version policy review, account-deletion compliance. Treating Mobile Publisher as a launch-only project (rather than an operational obligation) is the highest-cost mistake.
- **Security** — Push credentials (APNs `.p8` key or `.p12` certificate, Firebase service-account private key) are sensitive — the platform keeps them out of packages and source control (pkg2_dev 264 L9467-9469). The Apple Developer + Google Play developer accounts hold the legal authority for the app. SSO/IdP configuration on the source experience must consider mobile review constraints (reviewer can't complete enterprise MFA).

## Architectural Tradeoffs

- **Mobile Publisher vs custom-native build** — Mobile Publisher trades flexibility for speed and shared maintenance. The customer cannot add arbitrary native modules; Salesforce maintains the native shell. For most Experience Cloud / Field Service apps the tradeoff is correct. For apps that need general native development (custom payment integrations, hardware peripherals beyond what FSL covers), a custom-native build is the honest answer despite the cost.
- **Public store distribution vs enterprise distribution** — Public stores require store review and are the right path for partner/customer apps. Enterprise distribution (Apple Developer Enterprise Program, managed Google Play) is the right path for employee-only apps where store review is irrelevant overhead. Pick one explicitly; the cost of "we'll do both" is real (separate signing, separate distribution, separate analytics).
- **Branded source experience vs branded shell only** — Mobile Publisher brands the shell (icon, splash, store presence) but the source experience inherits its own branding from Experience Cloud / FSL. Misalignment between shell brand and source-experience brand is jarring; align both before publish.

## Anti-Patterns

1. **Treating native-shell upgrades as optional** — Salesforce's support window for older shells is finite. Skipping cycles invites store-side notices and eventual app removal (UNVERIFIED (2026-10-21): Help-only support window; no corpus line). Schedule resubmissions as recurring operational work.
2. **Ignoring developer-account ownership** — Apps published under the wrong legal entity (e.g. system integrator's account instead of customer's) become impossible to migrate cleanly. Verify ownership at procurement, not at submission.
3. **Skipping the test track** — Production submission without a full TestFlight + Play Internal Testing pass surfaces push, deep-link, and login bugs in the worst possible place: the App Store reviewer's hands. Test on real devices first.

## Official Sources Used

- Metadata API Developer Guide (Winter '27), `ExtlClntAppApplePushConfig` — iOS push takes a `.p8` key (`signingKey`, `keyIdentifier`, `teamIdentifier`) or a `.p12` certificate (`certificate`, `password`), and a Required `environment` of Production or Sandbox: api_meta 264 L68468-68471, L68480-68483.
- Metadata API Developer Guide (Winter '27), `ExtlClntAppAndroidPushConfig` — Android push takes Required `fcmProject` and `serviceAccount` (Base64 Admin SDK private key, max 8,000 characters); no server-key field: api_meta 264 L68456-68462.
- Metadata API Developer Guide (Winter '27), `ExtlClntAppPushSettings` — pilot or beta type, API 64.0+: api_meta 264 L68370, L68394.
- Second-Generation Managed Packaging Developer Guide (Winter '27) — APNS and Firebase credentials "can't be packaged or added to source control": pkg2_dev 264 L9467-9469.
- Object Reference (Winter '27), `MobileDeviceAppRegistration.DeviceSystemToken` — the token APNs or FCM uses to reach a device: object_reference 264 L186403-186410.
- Object Reference (Winter '27), `CustomBrandAsset` — branding applies to an Experience Cloud site or to an org using the Salesforce mobile app: object_reference 264 L87781-87782.
- UNVERIFIED (2026-10-21): the Help and store-policy links below were not fetchable or are outside the corpus; they are kept as pointers, not as grounding.
- Mobile Publisher product documentation — https://help.salesforce.com/s/articleView?id=sf.branded_apps_overview.htm — overview, capabilities, prerequisites.
- Experience Cloud Mobile Publisher Configuration — https://help.salesforce.com/s/articleView?id=sf.branded_apps_setup.htm — branding, push, identity setup.
- Field Service Mobile Publisher — https://help.salesforce.com/s/articleView?id=sf.fs_mp_overview.htm — Field Service variant capabilities and limits.
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html — Operational Excellence and Security pillar framing.
- Apple App Store Review Guidelines — https://developer.apple.com/app-store/review/guidelines/ — login completeness, account deletion, IAP policy referenced in submission planning.
- Google Play Developer Policy — https://play.google.com/about/developer-content-policy/ — account deletion, target API level, distribution policy.
