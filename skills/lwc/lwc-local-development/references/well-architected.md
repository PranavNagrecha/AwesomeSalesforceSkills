# Well-Architected Notes — LWC Local Development

## Relevant Pillars

- **Operational Excellence** — Live Preview tightens the inner development loop: edit, save, see,
  without a deploy round-trip. The operational risk is a stale preview — several edit categories
  (`@api`, `@wire`, `@salesforce` imports, `.js-meta.xml`) don't hot-reload, so a disciplined
  workflow knows when to refresh (single component) or redeploy + restart (app/site). Preview is
  the inner loop; Jest and the deploy pipeline remain the outer loop that actually gates change.
- **Security** — the preview server loads real org data and metadata locally. Salesforce
  recommends running against **sandbox or scratch orgs**, not production, precisely so production
  data isn't pulled onto a developer machine. Components that read data still do so through the
  running user's LDS/Apex context, so respect CRUD/FLS in any Apex the component calls — preview
  doesn't relax those checks.
- **Reliability** — preview confirms rendering against one org's data; it is not a correctness
  proof. Treating a clean preview as "tested" is a reliability trap. Pair it with Jest coverage.

## Architectural Tradeoffs

- **Speed vs. fidelity.** Single-component preview is the fastest loop but renders the component
  in isolation; app preview is slower to set up but reproduces navigation and cross-component
  context. Start with single-component preview and escalate to app preview only when context
  matters.
- **Live-reload convenience vs. the manual-reload cliff.** Most edits reload instantly, which
  trains a "just save" habit — but `@api`/`@wire`/`@salesforce`/`.js-meta.xml` edits break that
  habit silently. The tradeoff is worth it, provided the team internalizes the exceptions.
- **Local iteration vs. real verification.** Preview replaces the deploy-and-click loop, not the
  test suite. Keep Jest and pipeline deploys in the definition of done.

## Anti-Patterns

1. **Preview-as-test** — shipping because it "looked right" in Live Preview, with no Jest and no
   pipeline deploy. Preview renders; it doesn't assert or run in CI.
2. **Production preview** — pointing `--target-org` at production for convenience, pulling
   production data onto a local server against Salesforce's sandbox/scratch recommendation.
3. **Assuming full hot-reload** — expecting `@api`/`@wire`/`.js-meta.xml` changes to appear on
   save, then debugging a "broken" component that is really just a stale build.

## Official Sources Used

- Preview Components with Live Preview (Test Components / Get Started) — https://developer.salesforce.com/docs/platform/lwc/guide/get-started-test-components.html
- Winter '26 for Developers (Local Dev Beta single-component preview; unified testing note) — https://developer.salesforce.com/blogs/2025/09/winter26-developers
- Salesforce CLI Lightning Dev plugin (`@salesforce/plugin-lightning-dev`) — https://github.com/salesforcecli/plugin-lightning-dev
- Preview a Single Component with Local Dev (Beta) release note (256) — https://help.salesforce.com/s/articleView?id=release-notes.rn_lwc_single_component_preview.htm&language=en_US&release=256&type=5
- Single Component Live Preview GA release note (262) — https://help.salesforce.com/s/articleView?language=en_US&id=release-notes.rn_lwc_single_component.htm&release=262&type=5
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
