# Well-Architected Notes — ISV License Management and Trialforce

## Relevant Pillars

- **Security** — License enforcement is a security boundary between the ISV and the subscriber. The LMA is the only enforceable surface; subscriber-side license-check artifacts (Custom Settings, Custom Objects) are editable by the subscriber's admin and provide no real enforcement. Feature Parameters with `LmoToSubscriber` direction must not be used as authorization decisions because propagation is asynchronous — they are configuration, not access control.
- **Operational Excellence** — The LMA's missing observability is the largest operational gap. Salesforce sends no notifications when licenses expire, suspensions occur, or Feature Parameter propagation falls behind. Partners must build the alerting layer themselves (suspension watcher job, FP propagation SLA dashboard, Trialforce template approval tracker).
- **Reliability** — Trialforce template invalidation (TSO deletion, edition downgrade) silently fails downstream signups. Partners must own the lifecycle of every TSO and treat template re-approval as a release-train action, not a side effect of an upgrade. AppExchange Checkout licenses can't be modified in the LMA, so seat changes for those customers need their own runbook path.

## Architectural Tradeoffs

| Tradeoff | Why it matters |
|---|---|
| LMA in PBO vs dedicated LMO | PBO consolidates partner-ops surface but mixes listing-management traffic with license-enforcement state; partners with multiple packages eventually split, and migration is unsupported via Setup UI. Recommend dedicated LMO from day one. |
| `LmoToSubscriber` vs `SubscriberToLmo` Feature Parameter direction | LmoToSubscriber is for partner-controlled configuration (feature flips, tier gating). SubscriberToLmo is for telemetry. Mixing directions in one FP "for flexibility" is not supported — direction is a property of the FP definition. |
| Trialforce TMO with custom branding vs Environment Hub TSO | TMO requires Salesforce-side provisioning (case-driven, weeks) and is mandatory for branded login pages. Environment Hub is faster but does not support custom branding. Pick based on whether brand consistency is a sales-cycle priority. |
| Feature Parameter for feature-gating vs new package version | FPs are minutes-to-effect, no security review, no version churn. New version is hours-to-effect (subscriber upgrade window), full security review on metadata changes. Prefer FPs for binary toggles where the underlying code is already shipped. |
| AppExchange Checkout vs partner-owned billing | Checkout-provisioned licenses can't be modified in the LMA (pkg2_dev.txt L22966), so seat changes leave the partner's hands. With partner-owned billing, every renewal means a Modify License edit in the LMA. UNVERIFIED (2026-10-19): Checkout's invoicing, refund and dunning controls are not in the corpus. |

## Anti-Patterns

1. **Treating the LMA as optional for paid packages** — Without LMA registration, license enforcement is impossible. The "we'll add it later" plan requires a Salesforce-side reconciliation case for every existing install.
2. **Storing license state in subscriber-editable artifacts** — Custom Settings, Custom Objects, and Custom Metadata Types in the subscriber are all editable (or at minimum visible) to the subscriber admin. License truth must live in the LMO, not the subscriber.
3. **Iterating on Feature Parameter wiring with beta package versions** — Beta versions cannot register with the LMA, so the FP propagation channel is inactive. Partners burn weeks "testing" FPs that were never going to propagate.
4. **Snapshotting Trialforce templates without re-approving** — Templates are immutable post-approval; "updating" a template means snapshotting the TSO again and submitting the new template for approval. Partners who edit-in-place find their listing's trial method points at an unapproved template that fails at signup.

## Official Sources Used

- ISVforce Guide — License Management App overview and registration — https://developer.salesforce.com/docs/atlas.en-us.packagingGuide.meta/packagingGuide/lma_intro.htm
- ISVforce Guide — Manage Licenses for Managed Packages — https://developer.salesforce.com/docs/atlas.en-us.packagingGuide.meta/packagingGuide/lma_managing_licenses.htm
- ISVforce Guide — Trialforce overview, TMO, TSO, and Templates — https://developer.salesforce.com/docs/atlas.en-us.packagingGuide.meta/packagingGuide/trialforce_overview.htm
- ISVforce Guide — Feature Parameters and Feature Management — https://developer.salesforce.com/docs/atlas.en-us.packagingGuide.meta/packagingGuide/fma_intro.htm
- ISVforce Guide — AppExchange Checkout Integration — https://developer.salesforce.com/docs/atlas.en-us.packagingGuide.meta/packagingGuide/checkout_overview.htm
- Apex Reference Guide — `System.FeatureManagement` Class — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_class_System_FeatureManagement.htm
- Metadata API Developer Guide — `FeatureParameterBoolean`, `FeatureParameterDate`, `FeatureParameterInteger` — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_featureparameterboolean.htm
- Salesforce CLI Reference — https://developer.salesforce.com/docs/atlas.en-us.sfdx_cli_reference.meta/sfdx_cli_reference/cli_reference.htm
- Salesforce DX Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_intro.htm
- 2GP Developer Guide, Get Started with the LMA (Summer '26 PDF, pkg2_dev.txt L22774 PBO as LMO, L22781 no Slack/DLRS, L22800 one LMO per package, L22832 beta versions don't display in the LMA). Supports Gotchas 1 and 6 and the registration steps.
- 2GP Developer Guide, Lead and License Records / Modify a License Record / Troubleshoot / Best Practices (pkg2_dev.txt L22950 licenses created from registration values, L22966 Checkout licenses can't be modified in the LMA, L23134 License Type is legacy, L23189–23205 moving the LMA, L23240–23262 causes of missing licenses, L23295 treat LMA objects as read-only). Supports Gotchas 2, 6, 8 and Concept 4.
- 2GP Developer Guide, Feature Parameters (pkg2_dev.txt L10420–10425 beta testing limits and the 200-parameter limit, L23620 direction can't change after release, L23686 `checkPackageBooleanValue('YourBooleanFeatureParameter')`); Apex Reference L215378 `checkPackageBooleanValue(String apiName)`. Supports Gotcha 5 and Pattern 3. Apex Reference L215378, L215406, L215427: every `checkPackage*Value` signature takes only `String apiName` — there is no namespace overload (Anti-pattern 3).
- Metadata API Developer Guide, FeatureParameterBoolean / Date / Integer (api_meta.txt L66299–66300 `.featureParameterBoolean` in `featureParameters/`; L66321–66331 fields `dataFlowDirection`, `masterLabel`, `value` — "The default value for this feature parameter"; L66433, L66529 the same `value` field on Date and Integer) and 2GP guide L23669–23677 (override a default on the subscriber's license record). Supports Gotcha 7 and the checker.
