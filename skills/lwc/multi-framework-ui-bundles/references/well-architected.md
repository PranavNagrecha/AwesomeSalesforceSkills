# Well-Architected Notes — Multi-Framework UI Bundles

## Relevant Pillars

- **Security** — the whole point of running React *on* the platform instead of beside it is
  inherited security: `createDataSDK()` handles authentication automatically, so no tokens,
  client secrets, or OAuth plumbing belong in application code. Keep it that way — flag any
  credential material in the bundle. The `isActive` flag gates accessibility of the app, and
  an `Experience`-target bundle is *external-facing* by definition, so review what data the
  GraphQL queries and Apex `fetch()` calls expose to that audience.
- **Operational Excellence** — this capability is **open beta** (scratch orgs/sandboxes,
  English default language, no production deploys), with Lightning-page micro-frontend
  embedding in a narrower closed pilot (Spring 2026). Well-architected here means managing
  the lifecycle honestly: record the beta boundary in the design doc, use the required
  `version` field on the bundle deliberately, and re-verify restrictions each release cycle
  as the beta evolves.
- **Performance** — the deployable artifact is a built web app under a 2,500-file cap. Ship
  Vite build output only; a lean bundle is both a deployability requirement and a load-time
  win.
- **Reliability** — the announcement notes some platform APIs are unavailable in the beta
  runtime. Isolate SDK access behind a thin data module (as in `references/examples.md`) so
  signature changes during beta touch one file, not every component.

## Architectural Tradeoffs

- **React ecosystem vs. GA stability.** Multi-Framework buys the React/Vite/Tailwind
  ecosystem and existing web-dev skills, at the cost of beta restrictions and churn risk. For
  a production deadline, LWC remains the GA path; Multi-Framework doesn't replace LWC — they
  run side by side.
- **UI bundle vs. LWR site for external surfaces.** An `Experience`-target bundle surfaces in
  the Digital Experiences app, but LWR site development (`lwc/lwr-site-development`) is the
  established route for portals today. Pick the beta path only when React itself is the
  requirement.
- **ACC embed vs. custom chat.** Embedding the Agentforce Conversation Client gives streaming,
  theming, and Lightning-Type-driven interactive rendering for free, at the cost of accepting
  its (Beta) container contract. Hand-built chat gives pixel control and re-implements
  everything else.

## Anti-Patterns

1. **Beta in the critical path** — committing a production go-live to a capability whose docs
   say beta apps cannot be deployed to production orgs. Sequence it as a pilot with an LWC
   fallback.
2. **Bypassing the SDK data plane** — calling REST APIs with hand-managed tokens from inside
   a UI bundle, forfeiting the automatic authentication that justifies the architecture.
3. **Source-tree deployment** — treating `uiBundles/<app>/` as the dev workspace instead of
   the build target, blowing the 2,500-file cap and leaking dev artifacts into org metadata.

## Official Sources Used

- Metadata API Developer Guide — UIBundle — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_uibundle.htm
- Build with React, Run on Salesforce: Introducing Salesforce Multi-Framework (Salesforce Developers Blog, April 2026) — https://developer.salesforce.com/blogs/2026/04/build-with-react-run-on-salesforce-introducing-salesforce-multi-framework
- Build a React App with Salesforce Multi-Framework (Beta) — https://developer.salesforce.com/docs/platform/einstein-for-devs/guide/reactdev-overview.html
- Build and Deploy a React App Using Agentforce Vibes (Beta) — https://developer.salesforce.com/docs/platform/einstein-for-devs/guide/reactdev-vibe-code.html
- Get Started — Agentforce Conversation Client Developer Guide — https://developer.salesforce.com/docs/platform/accsdk/guide/acc-get-started.html
- Agentforce Conversation Client Web SDK (Beta) — https://developer.salesforce.com/docs/platform/accsdk/guide/acc-sdk-overview.html
