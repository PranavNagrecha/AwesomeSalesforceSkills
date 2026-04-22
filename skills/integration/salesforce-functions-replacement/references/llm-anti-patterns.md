# LLM Anti-Patterns — Salesforce Functions Replacement

Common mistakes AI coding assistants make when migrating off retired Salesforce Functions.

## Anti-Pattern 1: Recommending Functions as if still GA

**What the LLM generates:** "Use Salesforce Functions for this Node.js workload." (In 2025 / 2026.)

**Why it happens:** Pretraining predates retirement; model does not know Functions is EOL.

**Correct pattern:**

```
Salesforce Functions was retired January 2025. Every greenfield Apex
-adjacent compute workload must choose another target: Heroku for
Salesforce-native compute, Apex Queueable for simple compute,
Agentforce Actions for LLM workloads, or an external container
reached via Named Credentials.
```

**Detection hint:** `project.toml`, `functions.yaml`, or `Function.get(...).invoke(...)` references in newly written code.

---

## Anti-Pattern 2: Port everything to Apex

**What the LLM generates:** "Rewrite the PDF generator in Apex."

**Why it happens:** The model wants to stay on-platform and underestimates Apex CPU limits and library gaps.

**Correct pattern:**

```
Apex can replace small-compute Functions (<5s, standard library).
Library-heavy work (PDF, image processing, specialized ML) does NOT
fit Apex. Port those to Heroku or an external container. Trying to
rewrite a PDF generator in Apex produces CPU limit errors under
volume.
```

**Detection hint:** Apex class with 300+ lines of manually-implemented PDF or image-processing logic.

---

## Anti-Pattern 3: Heroku deploy without Private Space for sensitive data

**What the LLM generates:** Heroku common runtime deploy for a workload that processes PCI or PII.

**Why it happens:** The model does not model compliance tiers.

**Correct pattern:**

```
PCI / PII / HIPAA workloads run on Heroku Private Spaces or Heroku
Shield. Common runtime is not compliant for protected data. Tier the
workload and pick the Heroku plan accordingly; budget for it upfront.
```

**Detection hint:** Heroku app manifest with `stack: heroku-22` and no `private_space` and a workload that handles customer payment data.

---

## Anti-Pattern 4: Continuing to use legacy Auth Provider for external callouts

**What the LLM generates:** Adds Auth Provider + Named Credential combo for Heroku callout.

**Why it happens:** Model learned the older Auth Provider pattern; External Client Apps are newer.

**Correct pattern:**

```
External Client Apps are the forward-looking auth surface for external
callouts. For new integrations, configure External Client App +
Named Credential. Auth Providers remain supported but are legacy;
migrate during the Functions replacement work.
```

**Detection hint:** Named Credential metadata referencing `authProviderId` to a hand-authored Auth Provider rather than an External Client App.

---

## Anti-Pattern 5: Big-bang cutover of all Functions in one release

**What the LLM generates:** Migration plan: "Deploy all replacements one weekend; shut Functions off Monday."

**Why it happens:** The model optimizes for plan simplicity.

**Correct pattern:**

```
Migrate Function-by-Function with each cutover independently
verifiable. Maintain dual-write or shadow-run where possible. Track
invocation count per Function until zero, then retire. Big-bang
creates an untestable blast radius on a hard deadline.
```

**Detection hint:** A migration plan with a single cutover date for all Functions rather than a per-workload sequence.
