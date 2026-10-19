# Gotchas — ISV License Management and Trialforce

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Beta package versions silently bypass the LMA

**What happens:** A package version uploaded as a *beta* (the unstable, pre-release version) installs into a subscriber org but does not create a `sfLma__License__c` record in the LMO. The partner sees the test install succeed and assumes their LMA wiring is correct — until the first released version installs and exposes a misconfiguration that was hidden during beta testing.

**When it occurs:** Any time the partner is using beta versions for QA or pilot testing. Both 1GP beta versions and 2GP unreleased versions exhibit this — only versions in the released state (1GP) or promoted state (2GP) participate in the LMA channel.

**How to avoid:** Test LMA wiring exclusively with released package versions installed into a throwaway Developer Edition org. Document explicitly in the QA runbook that "LMA verified" is a step that runs only on released versions. For 2GP partners, this means promoting a candidate version to released specifically for an LMA-wiring smoke test; budget the namespace cost (you cannot un-promote a 2GP version).

---

## Gotcha 2: Registration defaults become every subscriber's license terms

**What happens:** Each license record is "created according to the values you specified when you registered the package" — the default license behavior, including trial length and number of seats. Defaults accepted without review become the terms of every install, and correcting them later is a per-license edit on the **Modify License** page; the LMA tells you not to edit license records directly. The License Type field is "a legacy field and can be ignored."

**When it occurs:** First-time registrations where nobody from billing reviewed the defaults, and any partner selling through AppExchange Checkout: "You can't use the LMA to modify licenses provisioned through AppExchange Checkout."

**How to avoid:** Agree trial length and seats with billing before clicking **Register Package**, and record them in the runbook. Route Checkout customers to the Checkout subscription path rather than the LMA. Do not add a validation rule to enforce defaults — validation rules on license records can block license creation (Gotcha 8).

---

## Gotcha 3: Feature Parameter propagation is asynchronous and unobservable from the publisher side

**What happens:** When the partner edits a Feature Parameter value on a `sfLma__License__c` record, the change does not appear in the subscriber's `System.FeatureManagement.checkPackageBooleanValue()` call for some interval (typically 5–60 minutes, but bounded only by Salesforce-managed scheduling). UNVERIFIED (2026-10-19): the Summer '26 2GP guide documents the two directions and that neither change requires a package upgrade, but states no propagation interval. There is no published API to query the propagation queue, no Setup-side audit log of the most recent successful push, and no exception or status change in the LMA when propagation is delayed.

**When it occurs:** Always — but bites hardest in support escalations where a customer says "the feature still isn't enabled" 2 minutes after the partner flipped the LMA setting. The partner cannot distinguish "propagation in flight" from "propagation failed" from a fixed surface.

**How to avoid:** Document a propagation SLA to internal CSMs (e.g. "FP changes take up to 60 minutes; if not visible after 90, escalate to Salesforce support"). For features where time-to-effect must be fast, use a `LmoToSubscriber` FP as a one-way enabler combined with a subscriber-side polling Apex that refreshes a Custom Setting cache — this lets the package react quickly once the FP arrives without the partner having to test sub-minute latency.

---

## Gotcha 4: Trialforce templates die when the source TSO is deleted or downgraded

UNVERIFIED (2026-10-19): Trialforce template lifecycle is documented only in the ISVforce Guide and Salesforce Help, neither of which could be fetched; the Summer '26 2GP guide mentions Trialforce only for post-install scripts.

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

**What happens:** "You can move an LMA to a different org, but your package and license records don't automatically move with it. You must manually relink your packages and refresh the licenses." A partner who installs a fresh LMA and stops there has license records split across two orgs.

**When it occurs:** Partners who put the LMA somewhere other than the PBO — against Salesforce's strong recommendation to use the PBO as the LMO — and later move it, or who move it to clean up an org.

**How to avoid:** Follow the documented order: log a case with Partner Support to remove the association with the current org, install the LMA in the new org, associate your packages with it, then refresh licenses for each package. Check the new org first — Slack and the DLRS package cannot be installed in the same org as the LMA.

---

## Gotcha 7: AppExchange Checkout requires the LMA to be on the same Trust pod as the listing PBO

UNVERIFIED (2026-10-19): no pod-alignment requirement appears in the Summer '26 2GP guide's LMA chapters; treat this gotcha as unconfirmed until Salesforce Partner Support confirms it.

**What happens:** When a partner enables AppExchange Checkout for a paid listing, Checkout requires the LMA to be reachable for license-record creation at signup time. If the LMA is in a different Salesforce instance (pod) than the PBO that owns the listing, Checkout signups can experience cross-pod latency or, in edge cases, fail outright with non-actionable errors.

**When it occurs:** Partners with large LMAs that have been migrated to org pods optimized for data volume, where the listing-owning PBO has stayed on its original pod. Detection is hard because signups succeed in development testing (small data volume hides the latency tail).

**How to avoid:** Before enabling Checkout, file a partner case asking Salesforce to verify the LMA and PBO pod alignment. If misaligned, request a pod-migration plan rather than assuming Checkout will route across pods reliably. Document the pod assignment of every partner org as part of the partner ops runbook.

---

## Gotcha 8: Customizing the LMO's Lead and License objects stops license creation

**What happens:** Customers install the package and no lead or license appears in the LMA. Nothing errors in the partner's org.

**When it occurs:** When the LMO has a `before_create` or `before_update` trigger, a required custom field, a validation rule, or a workflow rule on leads or licenses, or an inactive lead manager. The 2GP guide lists each as a cause: "If a trigger fails, it can block license creation," and "The LMA doesn't populate a required custom field." Slack or the DLRS package in the org blocks the LMA install itself.

**How to avoid:** Treat the LMA custom objects as read-only, use `after_` triggers only, and keep validation rules and required fields off Lead and License. After fixing a cause, missing licenses appear in the LMA "within a few days" — so check before go-live, not after.
