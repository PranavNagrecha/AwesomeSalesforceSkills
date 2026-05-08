# Gotchas — ISV License Management and Trialforce

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Beta package versions silently bypass the LMA

**What happens:** A package version uploaded as a *beta* (the unstable, pre-release version) installs into a subscriber org but does not create a `sfLma__License__c` record in the LMO. The partner sees the test install succeed and assumes their LMA wiring is correct — until the first released version installs and exposes a misconfiguration that was hidden during beta testing.

**When it occurs:** Any time the partner is using beta versions for QA or pilot testing. Both 1GP beta versions and 2GP unreleased versions exhibit this — only versions in the released state (1GP) or promoted state (2GP) participate in the LMA channel.

**How to avoid:** Test LMA wiring exclusively with released package versions installed into a throwaway Developer Edition org. Document explicitly in the QA runbook that "LMA verified" is a step that runs only on released versions. For 2GP partners, this means promoting a candidate version to released specifically for an LMA-wiring smoke test; budget the namespace cost (you cannot un-promote a 2GP version).

---

## Gotcha 2: Default License Type left unset means permanent free licenses

**What happens:** When a package is registered with the LMA but the `sfLma__Package__c.DefaultLicenseType__c` and `DefaultLicenseSeats__c` fields are left blank (the form does not require them), every subsequent install creates a `sfLma__License__c` record with no Type, no expiration, and no seat enforcement. Subscribers receive functionally permanent licenses, and the partner cannot retroactively enforce terms without manually editing every License record one by one.

**When it occurs:** First-time LMA setups by partners who follow the AppExchange Publishing Console wizard without reading the optional-field guidance. Almost every partner-side support ticket about "why aren't subscribers getting trial expirations?" traces to this.

**How to avoid:** Set Default License Type, Default Seats, and (for trials) Default Expiration on every `sfLma__Package__c` record at the moment of registration. Add a validation rule on `sfLma__Package__c` enforcing non-null defaults so future package registrations cannot land in this state.

---

## Gotcha 3: Feature Parameter propagation is asynchronous and unobservable from the publisher side

**What happens:** When the partner edits a Feature Parameter value on a `sfLma__License__c` record, the change does not appear in the subscriber's `System.FeatureManagement.checkPackageBooleanValue()` call for some interval (typically 5–60 minutes, but bounded only by Salesforce-managed scheduling). There is no published API to query the propagation queue, no Setup-side audit log of the most recent successful push, and no exception or status change in the LMA when propagation is delayed.

**When it occurs:** Always — but bites hardest in support escalations where a customer says "the feature still isn't enabled" 2 minutes after the partner flipped the LMA setting. The partner cannot distinguish "propagation in flight" from "propagation failed" from a fixed surface.

**How to avoid:** Document a propagation SLA to internal CSMs (e.g. "FP changes take up to 60 minutes; if not visible after 90, escalate to Salesforce support"). For features where time-to-effect must be fast, use a `LmoToSubscriber` FP as a one-way enabler combined with a subscriber-side polling Apex that refreshes a Custom Setting cache — this lets the package react quickly once the FP arrives without the partner having to test sub-minute latency.

---

## Gotcha 4: Trialforce templates die when the source TSO is deleted or downgraded

**What happens:** Salesforce silently invalidates Trialforce Templates whose source TSO has been deleted, expired, or downgraded to a Salesforce edition that doesn't support the originating package's required features. Trial signups against the invalidated template fail at the AppExchange-side request submit; prospects see a generic error and abandon.

**When it occurs:** Common at year-end when partners audit org usage and clean up old TSOs they think are unused. Also occurs when a TSO that started as Enterprise Edition expires its temporary EE entitlement and reverts to a lesser edition.

**How to avoid:** Maintain a TSO inventory document listing every TSO, its template-source role, the Salesforce edition it requires, and its renewal date. Treat TSO deletions as a release-train action with a sign-off step. After every TSO change (refresh, edition change, package upgrade), test trial signup end-to-end with a fresh prospect-equivalent email before assuming the AppExchange listing's trial method still works.

---

## Gotcha 5: SubscriberToLmo Feature Parameters cannot be tested in beta versions

**What happens:** A partner adds a `SubscriberToLmo` Feature Parameter to a beta package version, installs in a test org, and calls `setPackageBooleanValue()`. The call appears to succeed (no exception). But because the beta version is not LMA-registered, the propagation channel is inactive, and the value never reaches the LMO. The partner cannot test the FP wiring until the version is promoted to released.

**When it occurs:** Whenever a partner tries to develop a Subscriber-to-LMO FP iteratively in beta. The default-value path of an `LmoToSubscriber` FP can be exercised in beta, but the propagation surface cannot.

**How to avoid:** Plan a release-cycle gate where `SubscriberToLmo` FP wiring is the last item validated before promoting a version. Stage the validation: ship the FP definition in a release, validate end-to-end, then ship its consumer Apex in a follow-up release. For partners on a 2GP source-tracked workflow, dedicate one promoted version per cycle to FP-channel validation rather than mixing it with feature work.

---

## Gotcha 6: Moving the LMA to a different LMO orphans existing License records

**What happens:** A partner who initially installed the LMA in their PBO and later wants to move it to a dedicated LMO finds no Setup UI for migration. If they install a fresh LMA in the new LMO and re-register the package, every existing subscriber's License record continues to live in the old LMO. New installs land in the new LMO. The partner now has license enforcement split across two orgs with no consolidation path.

**When it occurs:** Partners outgrowing their initial LMA setup, typically 12–24 months in, often coinciding with an attempt to clean up the PBO.

**How to avoid:** File a Partner Community case requesting LMA migration assistance *before* installing the LMA in the destination org. Salesforce's partner-support team coordinates the cutover and re-points existing subscriber installs to the new LMO. Skipping the case and self-migrating is the second-most-common cause of "I have two LMAs and no idea which is authoritative."

---

## Gotcha 7: AppExchange Checkout requires the LMA to be on the same Trust pod as the listing PBO

**What happens:** When a partner enables AppExchange Checkout for a paid listing, Checkout requires the LMA to be reachable for license-record creation at signup time. If the LMA is in a different Salesforce instance (pod) than the PBO that owns the listing, Checkout signups can experience cross-pod latency or, in edge cases, fail outright with non-actionable errors.

**When it occurs:** Partners with large LMAs that have been migrated to org pods optimized for data volume, where the listing-owning PBO has stayed on its original pod. Detection is hard because signups succeed in development testing (small data volume hides the latency tail).

**How to avoid:** Before enabling Checkout, file a partner case asking Salesforce to verify the LMA and PBO pod alignment. If misaligned, request a pod-migration plan rather than assuming Checkout will route across pods reliably. Document the pod assignment of every partner org as part of the partner ops runbook.
