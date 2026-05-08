# Well-Architected Notes — Mobile Publisher

## Relevant Pillars

- **Operational Excellence** — Mobile Publisher apps require ongoing maintenance: native shell upgrades resubmitted to the stores, push certificate rotation, OS-version policy review, account-deletion compliance. Treating Mobile Publisher as a launch-only project (rather than an operational obligation) is the highest-cost mistake.
- **Security** — Push credentials (APN AuthKey, FCM service-account JSON) are sensitive. The Apple Developer + Google Play developer accounts hold the legal authority for the app. SSO/IdP configuration on the source experience must consider mobile review constraints (reviewer can't complete enterprise MFA).

## Architectural Tradeoffs

- **Mobile Publisher vs custom-native build** — Mobile Publisher trades flexibility for speed and shared maintenance. The customer cannot add arbitrary native modules; Salesforce maintains the native shell. For most Experience Cloud / Field Service apps the tradeoff is correct. For apps that need general native development (custom payment integrations, hardware peripherals beyond what FSL covers), a custom-native build is the honest answer despite the cost.
- **Public store distribution vs enterprise distribution** — Public stores require store review and are the right path for partner/customer apps. Enterprise distribution (Apple Developer Enterprise Program, managed Google Play) is the right path for employee-only apps where store review is irrelevant overhead. Pick one explicitly; the cost of "we'll do both" is real (separate signing, separate distribution, separate analytics).
- **Branded source experience vs branded shell only** — Mobile Publisher brands the shell (icon, splash, store presence) but the source experience inherits its own branding from Experience Cloud / FSL. Misalignment between shell brand and source-experience brand is jarring; align both before publish.

## Anti-Patterns

1. **Treating native-shell upgrades as optional** — Salesforce's support window for older shells is finite. Skipping cycles invites store-side notices and eventual app removal. Schedule resubmissions as recurring operational work.
2. **Ignoring developer-account ownership** — Apps published under the wrong legal entity (e.g. system integrator's account instead of customer's) become impossible to migrate cleanly. Verify ownership at procurement, not at submission.
3. **Skipping the test track** — Production submission without a full TestFlight + Play Internal Testing pass surfaces push, deep-link, and login bugs in the worst possible place: the App Store reviewer's hands. Test on real devices first.

## Official Sources Used

- Mobile Publisher product documentation — https://help.salesforce.com/s/articleView?id=sf.branded_apps_overview.htm — overview, capabilities, prerequisites.
- Experience Cloud Mobile Publisher Configuration — https://help.salesforce.com/s/articleView?id=sf.branded_apps_setup.htm — branding, push, identity setup.
- Field Service Mobile Publisher — https://help.salesforce.com/s/articleView?id=sf.fs_mp_overview.htm — Field Service variant capabilities and limits.
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html — Operational Excellence and Security pillar framing.
- Apple App Store Review Guidelines — https://developer.apple.com/app-store/review/guidelines/ — login completeness, account deletion, IAP policy referenced in submission planning.
- Google Play Developer Policy — https://play.google.com/about/developer-content-policy/ — account deletion, target API level, distribution policy.
