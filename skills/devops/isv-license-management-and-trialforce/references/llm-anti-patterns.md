# LLM Anti-Patterns — ISV License Management and Trialforce

Common mistakes AI coding assistants make when generating or advising on ISV license management and Trialforce wiring. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Recommending a custom license-check Custom Setting instead of the LMA

**What the LLM generates:** A `License_Config__c` Custom Setting with `Expires_On__c` and an `Apex` enforcement class that checks the date on every entry point.

```apex
// Wrong — subscriber-side Custom Setting is editable by the subscriber
public class LicenseGuard {
    public static void check() {
        if (License_Config__c.getOrgDefaults().Expires_On__c < Date.today()) {
            throw new LicenseException('Expired');
        }
    }
}
```

**Why it happens:** LLMs trained on generic SaaS-licensing patterns default to "check a date column" without recognizing that Salesforce has a platform-native cross-org license channel (the LMA) that is the only enforceable surface. The phrase "license check in Salesforce" is not strongly associated in training data with `sfLma__License__c`.

**Correct pattern:** Use the LMA. The package's components are auto-disabled when `sfLma__License__c.Status` is not `Active`. No partner Apex is required for enforcement. License-aware *feature gating* (as opposed to *license validity enforcement*) uses Feature Parameters, not Custom Settings:

```apex
// Right — query the FP value, which the LMA controls cross-org
public class FeatureGate {
    public static Boolean betaReportsEnabled() {
        return System.FeatureManagement.checkPackageBooleanValue(
            'YourNamespace', 'Enable_Beta_Reports'
        );
    }
}
```

**Detection hint:** Any Custom Setting or Custom Object named `License_*`, `Subscription_*`, or `Trial_*` in a managed package's source is suspicious. Grep for `getOrgDefaults().*Expir` and `Date.today()` checks against subscriber-editable fields.

---

## Anti-Pattern 2: Mixing up TMO, TSO, and Trialforce Template

**What the LLM generates:** Instructions that say "create a Trialforce Source Org from your Trialforce template" or "request a Trialforce Source Org from Salesforce."

**Why it happens:** Salesforce's own documentation uses three almost-identical acronyms (TMO, TSO, and "Template") in a hierarchical relationship that LLMs often flatten into a single "Trialforce Org" concept. Training data also contains historical references to the older Trialforce model that didn't separate management from source.

**Correct pattern:** Three distinct concepts in a strict hierarchy:

```text
Trialforce Management Org (TMO)
├── created by:  Salesforce, on partner-portal case request
├── purpose:     control plane; holds branding and templates
│
├── Trialforce Source Org (TSO)
│   ├── created by:  the partner, FROM the TMO
│   ├── purpose:     real org configured to look like a fresh install
│   │
│   └── Trialforce Template
│       ├── created by:  the partner, by snapshotting the TSO
│       ├── purpose:     immutable approved snapshot used to mint trials
│       └── trials:      created from a Template, not a TSO directly
```

A TSO is created from a TMO, not from a template. A template is created from a TSO, not requested from Salesforce. Trials are minted from approved templates.

**Detection hint:** Any sentence that has "create" + ("TSO" or "Trialforce Source Org") + "from a template" is reversed. Any sentence that has "request a TSO from Salesforce" — TSOs aren't requested; only TMOs are.

---

## Anti-Pattern 3: Calling FeatureManagement methods without the namespace argument from a 1GP package

**What the LLM generates:**

```apex
// In a 1GP package's class invoked by subscriber code:
System.FeatureManagement.checkPackageBooleanValue('Enable_Beta_Reports');
```

**Why it happens:** The two-argument `checkPackage*Value(namespace, name)` and one-argument `checkPackage*Value(name)` overloads coexist. LLMs default to the simpler signature, which works only when the calling Apex is *inside* the package namespace. A 1GP package's `global` class invoked from subscriber Apex runs in the subscriber namespace context — the one-argument call returns the subscriber's value (almost always `null`).

**Correct pattern:** From any class consumed by subscriber Apex (typically `global` classes in 1GP), pass the namespace explicitly:

```apex
// Right — explicit namespace ensures the FP lookup hits the package's FP, not
// a subscriber-namespace coincidence
System.FeatureManagement.checkPackageBooleanValue(
    'YourPackageNamespace',
    'Enable_Beta_Reports'
);
```

**Detection hint:** Grep for `FeatureManagement.checkPackage*Value\s*\(\s*['"]\w+['"]\s*\)` (one-string-arg form) inside any class with `global` modifier or any class in a managed-package namespace directory. Flag every one-argument call for review.

---

## Anti-Pattern 4: Asserting that AppExchange Checkout replaces the LMA

**What the LLM generates:** "Once you enable AppExchange Checkout, you don't need to maintain the LMA — Checkout handles licensing." Or: "Checkout writes to a separate Subscription object and the LMA becomes optional."

**Why it happens:** Training data (including older partner-program marketing) sometimes describes Checkout as a "modernization" of partner billing, which LLMs over-generalize into "Checkout supersedes the LMA."

**Correct pattern:** AppExchange Checkout sits *on top of* the LMA. Every Checkout signup creates an `sfLma__License__c` record in the partner's LMA. Checkout adds subscription-management fields (renewal date, payment status, plan) but does not replace license enforcement, seat tracking, or the package-side license-status enforcement. If the LMA is misconfigured, Checkout signups still appear to work but enforcement and tracking are broken.

**Detection hint:** Any phrase like "Checkout replaces", "Checkout supersedes", "you don't need the LMA when using Checkout", or "Checkout handles licensing on its own" is wrong.

---

## Anti-Pattern 5: Treating Feature Parameter writes as synchronous and immediately observable

**What the LLM generates:**

```apex
// Wrong — assumes the FP is readable in the same transaction
System.FeatureManagement.setPackageBooleanValue('FeatureFlag', true);
Boolean now = System.FeatureManagement.checkPackageBooleanValue('FeatureFlag');
System.assert(now == true);  // Fails — propagation hasn't happened yet
```

Or recommends using FPs as "real-time feature flags" interchangeable with Custom Settings.

**Why it happens:** Feature-flag platforms outside Salesforce (LaunchDarkly, Unleash, Split) emphasize sub-second flip-to-effect timing. LLMs apply that mental model to Salesforce Feature Parameters without recognizing that propagation is asynchronous and Salesforce-scheduled.

**Correct pattern:** Treat FP writes as fire-and-forget configuration changes that take minutes to propagate. For features that must respond to admin action *within the same user session*, do not gate on a Feature Parameter — use a subscriber-side Custom Setting that the package owns and exposes via a configuration UI inside the subscriber. Reserve FPs for cross-org configuration the *partner* (not the subscriber) controls, and document the propagation-window assumption to internal ops.

**Detection hint:** Any code path that does `setPackage*Value` followed by `checkPackage*Value` of the same FP within the same execution context. Also flag any documentation phrase like "instantly enable" or "immediately apply" near a Feature Parameter.
