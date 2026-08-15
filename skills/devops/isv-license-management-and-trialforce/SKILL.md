---
name: isv-license-management-and-trialforce
description: "Use when an ISV partner is wiring license enforcement, trial provisioning, or feature-flag distribution into a managed package — covers License Management App (LMA) install and registration, Lead/License object. NOT for general managed-package version creation, ancestor pinning, or PostInstall handler design — use devops/managed-package-development."
category: devops
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Operational Excellence
  - Reliability
triggers:
  - "register a managed package with the License Management App so I can sell licenses"
  - "package install fails because the license expired or wasn't refreshed in the subscriber org"
  - "set up Trialforce so prospects can request a trial of our AppExchange solution"
  - "add a feature parameter so we can flip a feature on for one subscriber without re-releasing"
  - "decide between LMO-to-subscriber and subscriber-to-LMO feature parameter direction"
  - "AppExchange Checkout integration with the LMA for paid managed packages"
tags:
  - isv-license-management-and-trialforce
  - managed-packages
  - appexchange
  - trialforce
  - feature-management
inputs:
  - "package type and generation (1GP managed, 2GP managed, unlocked) and the License Management Org / TMO it's registered with"
  - "the trial mechanism the ISV plans to use (AppExchange listing trial, SignupRequest API, free install)"
  - "whether AppExchange Checkout is in scope and the pricing model (per-user, flat, freemium)"
outputs:
  - "License Management App (LMA) registration plan and License-record lifecycle map"
  - "Trialforce architecture diagram (TMO vs TSO vs Template) and trial-method decision"
  - "Feature Parameter inventory with direction (LmoToSubscriber / SubscriberToLmo), default values, and Apex consumption pattern"
dependencies: []
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-08-14
---

# ISV License Management and Trialforce

Activate this skill when an ISV partner is designing or troubleshooting the license-and-trial surface of a Salesforce managed package — the cross-org channels by which the partner's License Management Org (LMO) controls what a subscriber org can do, how trial provisioning is delivered, and how runtime feature flags are flipped after the package has been installed. This is the `partner ↔ subscriber` plane, not the in-package code plane.

---

## Before Starting

Gather this context before proposing any change:

- **Package generation.** 1GP and 2GP managed packages differ on what is wired through the LMA, and only 1GP packages can be created and managed inside a 1GP packaging org. Feature Parameters work for both 1GP and 2GP managed packages but require slightly different declaration paths.
- **Which org is which.** ISVs juggle four org roles: the **Partner Business Org (PBO)** holds the AppExchange listing and the security review record; the **License Management Org (LMO)** holds the License Management App (LMA) and `sfLma__License__c` records; the **packaging org** (1GP) or DX hub (2GP) builds package versions; the **TMO / TSO** issues trials. These are usually distinct orgs. Conflating them is the most common ISV mistake.
- **Trial method already chosen?** AppExchange listing trial, SignupRequest API, and free install map to different Trialforce setups and different conversion-tracking surfaces. Pick the trial method *before* designing the LMA + Trialforce wiring, not after.
- **Edition limits.** A 1GP package can include up to **200 Feature Parameters**. Beta package versions can't register with the LMA, so `SubscriberToLmo` Feature Parameters can't be tested in beta — only released package versions.

---

## Core Concepts

### Concept 1 — The License Management App (LMA) is the ISV's seat-of-truth

The LMA is a free Salesforce-published managed package that the ISV installs in their **License Management Org**. It creates two key custom objects:

- **`sfLma__Package__c`** — one record per registered managed package (the version number and the Salesforce-issued package ID).
- **`sfLma__License__c`** — one record per subscriber org that installs the package. The license record carries seat count, status (`Active` / `Suspended` / `Uninstalled`), expiration date, and the subscriber org's 18-character Org ID.

Salesforce updates the License record automatically when a subscriber installs, upgrades, or uninstalls. The ISV adjusts seat counts and expiration dates as part of their billing process. Subscriber orgs query their license state through the platform — if a license is expired or suspended, the package's components stop being usable in that org. The LMA is the only supported way to enforce subscription billing on a 1GP managed package, and is required for AppExchange Checkout.

The LMA is registered with a package via **AppExchange Publishing → Package** form using the `sfLma__License_Management_Org__c` setting on the package record. Once registered, every subsequent install of any version of that package writes to the same License Management Org.

### Concept 2 — Trialforce splits provisioning into TMO + TSO + Template

Trialforce is the trial-org provisioning service. It uses three distinct org roles:

- **Trialforce Management Org (TMO)** — the partner's control plane. Created by Salesforce on request via a partner-portal case. Holds the Trialforce Source Orgs and Templates. Required for custom-branded trial login pages.
- **Trialforce Source Organization (TSO)** — a real Salesforce org configured to look like a brand-new install of the partner's product. The partner installs their managed package in the TSO, loads sample data, and configures users. The TSO is the snapshot-source.
- **Trialforce Template** — an approximate snapshot of a TSO at a point in time. New trials are spun up from a Template, not from the TSO directly. Templates require Salesforce approval after creation. Updating a template is a non-trivial process: re-snapshot the TSO, log a case to re-approve.

For non-CRM solutions, the Environment Hub can create TSOs without a TMO. CRM solutions and any partner that wants custom branding still require a TMO.

### Concept 3 — Feature Parameters are the LMA's runtime switchboard

Feature Parameters (FP) are package-scoped key/value records that flow between the LMO and the subscriber org without requiring a package upgrade. They come in three types — `FeatureParameterBoolean`, `FeatureParameterDate`, `FeatureParameterInteger` — and in two **directions**:

- **`LmoToSubscriber`** — the partner sets a value in the LMO; Salesforce propagates it to the subscriber org. Subscriber Apex reads it via `System.FeatureManagement.checkPackageBooleanValue()` (or `checkPackageDateValue` / `checkPackageIntegerValue`). Use to flip features on per customer, expire trial-only features, or provision-tier-gate functionality.
- **`SubscriberToLmo`** — the subscriber's package writes a value via `System.FeatureManagement.setPackageBooleanValue()`; Salesforce propagates it back to the LMO. Use for activation metrics, customer preferences, and per-org telemetry visible in the LMA.

Feature Parameters are **not** real-time. Propagation runs on a Salesforce-managed schedule (typically minutes, not seconds) in both directions. Critical decisions — whether a transaction is allowed — must not depend on a Feature Parameter that was flipped seconds ago. They are configuration, not authorization.

### Concept 4 — AppExchange Checkout sits on top of the LMA, not next to it

AppExchange Checkout adds e-commerce (credit-card billing, subscription renewals, self-service signup) to AppExchange listings. It does **not replace** the LMA — every Checkout purchase still creates a License record in the partner's LMA. Checkout adds a `Subscription` record (in the partner's billing system) and pushes lifecycle events (renewal, cancellation, upgrade) into the LMA. If the LMA is misconfigured, Checkout signups appear to succeed but the partner can't actually enforce or track the subscription.

---

## Common Patterns

### Pattern 1 — Register-then-track LMA wiring

**When to use:** The package is approaching first AppExchange listing or first paid release.

**How it works:**
1. Install the LMA managed package in a fresh **License Management Org** (recommended: the Partner Business Org or a dedicated production org — never a sandbox).
2. In the partner-side packaging org (1GP) or DX project (2GP), upload the package version and capture the `04t...` package version ID.
3. In the AppExchange Publishing Console, open the listing's package record and set the License Management Org to the LMO from step 1. The LMO must be in a Salesforce edition that supports the LMA (Enterprise+).
4. Verify by installing the package into a throwaway sandbox and confirming a `sfLma__License__c` record is auto-created in the LMO within 2–3 minutes.
5. In the LMA, set the **Default License Type** (`Trial` / `Active` / `Free`) and **Default Seats** for the package. These apply to every new install until manually overridden.
6. Build a scheduled job in the LMO that watches `sfLma__License__c` for `Status='Suspended'` and notifies the customer-success team — the LMA does not include outbound notifications.

**Why not skip the LMA:** Without LMA registration, the partner has no view of installs, no way to enforce expiration, and no path to AppExchange Checkout. Adding the LMA later requires a Salesforce-side reconciliation case for existing installs.

### Pattern 2 — Trialforce template lifecycle for a CRM solution

**When to use:** The package is a CRM-overlay solution and the partner wants AppExchange-listing-driven trials.

**How it works:**
1. Request a TMO via partner-portal case (`Partner Programs & Benefits` → `ISV Technology Request`).
2. From the TMO, create a TSO (or use Environment Hub for non-CRM).
3. In the TSO, install the managed package, configure users, load representative sample data, set up custom branding (if approved).
4. From the TMO, create a **Trialforce Template** — the wizard takes a snapshot of the TSO. Snapshot creation can take hours.
5. Submit the template for Salesforce approval. **Templates aren't usable until approved.**
6. In the AppExchange Partner Console, connect the TMO and link the approved template to the listing's trial method.
7. After every package update that ships a UI or schema change, rebuild the TSO state and re-snapshot — old templates issue trials with the old code.

**Why not skip the template re-approval:** Trial signups from a stale template land prospects in an org that doesn't match the current sales demo and silently locks the partner into supporting an old code path.

### Pattern 3 — LmoToSubscriber Feature Parameter for one-customer feature flip

**When to use:** A specific subscriber needs a feature enabled for them only — without shipping a new package version.

**How it works:**
1. In the package source, define a `FeatureParameterBoolean` (e.g. `Enable_Beta_Reports`) with a `defaultValue` of `false` and direction `LmoToSubscriber`.
2. In subscriber-side Apex that gates the feature, call `System.FeatureManagement.checkPackageBooleanValue('namespace', 'Enable_Beta_Reports')` and branch on the result.
3. Release the package version. Existing subscribers receive `false` (the default).
4. To flip for one customer: in the LMO, open their `sfLma__License__c` record, find the related Feature Parameter record (created automatically when the FP was added to a registered version), and set `Value__c = true`.
5. Within the propagation window (minutes), the customer's Apex sees `true` on the next call.

**Why not a custom field on a Custom Setting:** Custom Settings live in the subscriber's data — the partner has no cross-org write path without the LMA. Feature Parameters are the only sanctioned cross-org config channel.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Partner is shipping a free, non-paid 2GP managed package and never plans to monetize | Skip the LMA; use the standard 2GP install flow | LMA registration is recommended but not required for free packages, and adds operational overhead |
| Partner is selling licenses and wants to enforce subscription expiration | Register with the LMA in a dedicated production LMO; rely on Salesforce's automatic License-status enforcement | Subscription enforcement without the LMA requires custom Apex license checks and breaks AppExchange Checkout |
| Partner needs branded login screens during trial | TMO with custom branding; TSO + Template; CRM-trial requires TMO | Environment-Hub-only TSOs cannot do custom branding; TMO is the only supported branded path |
| Partner needs to flip a feature for one customer without a release | `LmoToSubscriber` Feature Parameter | Custom Settings can't be written cross-org; new package version is too heavy for a single-customer flip |
| Partner wants telemetry on how many subscribers are using a feature | `SubscriberToLmo` Feature Parameter (Boolean for usage flag, Integer for counter) | LMA telemetry without FPs requires hand-rolled callouts; FPs use the platform-native channel |
| Partner is moving an existing LMA to a new LMO | Salesforce-side reconciliation case via Partner Community | Direct LMA replication is unsupported and orphans existing Licenses |
| Trial method needs IDs/passwords for a non-Salesforce signup form | `SignupRequest` API with TMO-backed template | AppExchange-listing trial doesn't support custom signup forms |
| Beta package version needs SubscriberToLmo Feature Parameter testing | Not testable; promote to released version first | Beta package versions can't register with the LMA, so the FP propagation channel is inactive |

---

## Recommended Workflow

When a request lands that involves any of: LMA setup, Trialforce setup, Feature Parameter design, AppExchange Checkout, or license enforcement in a managed package, follow these steps:

1. **Identify which org is which.** Get the partner to label PBO, LMO, TMO, TSO, packaging org, and DX-hub explicitly. Half of all ISV-licensing tickets resolve once the org map is correct.
2. **Confirm package generation and trial method.** 1GP vs 2GP and trial-method choice gate every downstream decision; capture both before recommending anything.
3. **Audit current LMA state.** If an LMA exists, query `sfLma__Package__c` and `sfLma__License__c` counts and statuses; if not, plan the registration sequence per Pattern 1.
4. **Map Feature Parameters to direction and consumer.** For every requested feature flag, decide direction (`LmoToSubscriber` or `SubscriberToLmo`) and where in the subscriber Apex it's read. Don't add an FP without a confirmed reader.
5. **Validate the change in a sandbox-installed test subscriber org.** Install the package into a throwaway test org, confirm License record creation, exercise the FP propagation, and only then ship.
6. **Document the per-customer override path.** Write down (in the partner's runbook) exactly which LMA fields a CSM edits to flip an FP, set seats, or extend an expiration — operational handoff is where most LMA setups go wrong months later.

---

## Review Checklist

- [ ] Partner Business Org, License Management Org, TMO, and packaging org are explicitly named and not the same org (unless intentional and documented)
- [ ] LMA managed package is installed in the LMO and registered against every released package version
- [ ] Default License Type and Default Seats are set on each `sfLma__Package__c` record — not left blank
- [ ] Every Feature Parameter has a confirmed reader (Apex `FeatureManagement.checkPackage*Value` call or LMA report) — no zombie FPs
- [ ] Beta package versions are not relied on for `SubscriberToLmo` FP testing
- [ ] Trialforce templates are re-snapshotted and re-approved after every release that changes the trial UX
- [ ] License-suspension monitoring is wired (custom job or alert in the LMO) — Salesforce does not notify
- [ ] AppExchange Checkout (if used) has its renewal-event handler verified end-to-end against the LMA
- [ ] FP propagation latency is documented; no transactional code paths gate on a just-flipped FP

---

## Salesforce-Specific Gotchas

1. **Only released package versions can register with the LMA.** Beta versions install but do not create License records, and they do not propagate Feature Parameters. Do not test the LMA wiring with a beta — it will appear silently broken.
2. **Default License Type defaults to nothing useful.** If the partner forgets to set the default on `sfLma__Package__c`, every new install creates a License record with no Type set, and the package's components are usable indefinitely until a human edits the License — there is no built-in trial-expiration safety net.
3. **Feature Parameter propagation is not real-time.** Salesforce-managed schedules push values in both directions on the order of minutes. Code that flips an FP and then immediately reads it in the same transaction will get the old value.
4. **Feature Parameter limit is 200 per package.** The 200-FP cap is per registered package version. Partners who ship a large feature matrix must consolidate into Integer/Date FPs (bitmask, date-cohort) rather than one Boolean per feature.
5. **Trialforce Templates expire when the underlying TSO is deleted or the Salesforce edition changes.** A TSO downgrade or deletion silently invalidates downstream Templates, and trials created from an invalidated template fail at signup.
6. **Subscriber Apex cannot debug PostInstall failures.** When Feature Parameters or LMA wiring fails on install, the Automated Process user runs the PostInstall script and the partner has no debug log unless the LMA's Subscriber Support Console is set up — set it up *before* the first paid customer install.
7. **Moving the LMA between orgs is unsupported in the Setup UI.** The partner-portal case is the only supported migration path. Partners who manually replicate `sfLma__License__c` records will have broken propagation for the migrated subscribers.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| LMA registration runbook | Step-by-step: install LMA → upload package → register LMO → verify with test install → set defaults → wire suspension alerts |
| Trialforce architecture diagram | TMO ↔ TSO ↔ Template flow with arrows for who-creates-who, plus the trial-method choice that consumes the Template |
| Feature Parameter inventory | Per-FP table: name, type, direction, default value, reader location, and operational owner in the LMO |
| Org-role label map | Names every org (PBO, LMO, TMO, TSO, packaging, DX hub) so subsequent troubleshooting starts from a known state |

---

## Related Skills

- `devops/managed-package-development` — 1GP package version creation, PostInstall handler, namespace mechanics. Use alongside when the partner is also building or upgrading the package itself.
- `devops/second-generation-managed-packages` — 2GP version creation, ancestor pinning, source-tracked packaging. Use for the build side; this skill covers the licensing side.
- `devops/multi-package-development` — for partners shipping multiple related packages from one DX project.
- `architect/experience-cloud-licensing-model` — for non-ISV licensing (Experience Cloud member licenses, login-based pools).
- `apex/apex-callout-retry-and-resilience` — for the partner's billing-system integration that pushes renewals into the LMA.
