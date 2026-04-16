# LLM Anti-Patterns — Package Development Strategy

Common mistakes AI coding assistants make when advising on Salesforce package type selection and development strategy.

---

## Anti-Pattern 1: Recommending Unlocked Packages for AppExchange ISV Products

**What the LLM generates:** "Use unlocked packages for your new AppExchange app — they're the modern recommended approach."

**Why it happens:** LLMs associate "unlocked packages" with "modern DX development" without distinguishing between internal org use and ISV AppExchange listing requirements.

**The correct pattern:** Unlocked packages do not provide IP protection — Apex source is accessible to the subscriber org admin. AppExchange Security Review requires managed packages (1GP or 2GP) for ISV product listings. Use 2GP managed packages for new ISV products; use unlocked packages only for internal customer org modularization.

**Detection hint:** Any recommendation of unlocked packages for a product intended for AppExchange listing is incorrect. If the context is "internal org" and no AppExchange listing is intended, unlocked packages are appropriate.

---

## Anti-Pattern 2: Treating 1GP and 2GP as Equivalent Choices

**What the LLM generates:** "You can use either 1GP or 2GP managed packages for your new product — choose based on your team's experience."

**Why it happens:** LLMs present both as valid options without applying Salesforce's own recommendation to use 2GP for all new development.

**The correct pattern:** Salesforce explicitly recommends 2GP for all new managed package development. 1GP is org-centric, not DX-compatible, and has limited dependency management. 2GP supports scratch org development, source format, CI/CD, and explicit package dependencies. The choice of 1GP for new development is a deliberate tradeoff that should be justified, not a default.

**Detection hint:** Any recommendation of 1GP for a new ISV product without explicitly acknowledging that 2GP is the Salesforce-recommended choice should be questioned.

---

## Anti-Pattern 3: Suggesting Namespace Can Be Changed Post-Registration

**What the LLM generates:** "You can rename your namespace later by submitting a support case to Salesforce."

**Why it happens:** LLMs generate plausible-sounding workarounds for irreversible platform decisions.

**The correct pattern:** Namespace registration is permanent and irreversible. Salesforce Support cannot change a registered namespace. All API names of managed package components include the namespace prefix permanently. A namespace change would require a completely new package with a full subscriber migration.

**Detection hint:** Any response that suggests namespace changes are possible via support cases or any other mechanism is incorrect.

---

## Anti-Pattern 4: Recommending 2GP for Internal Org Modularization Without License Considerations

**What the LLM generates:** "Use 2GP managed packages to modularize your internal org — it's the most modern approach."

**Why it happens:** LLMs recommend 2GP broadly without distinguishing the licensing and namespace requirements of managed packages vs. unlocked packages.

**The correct pattern:** 2GP managed packages require namespace registration (a permanent decision) and are intended for ISV/AppExchange use. For internal org modularization without AppExchange ambitions, unlocked packages are the correct choice — no namespace required, no IP protection overhead, simpler dependency model for internal use.

**Detection hint:** If the use case is explicitly internal customer org development (not ISV), recommending 2GP managed packages over unlocked packages adds unnecessary complexity.

---

## Anti-Pattern 5: Confusing Package Type with Deployment Method

**What the LLM generates:** "Unmanaged packages are the same as metadata API deployments — just use whichever you prefer."

**Why it happens:** LLMs conflate unmanaged packages (which use the same metadata format as deployments) with the Metadata API deployment mechanism.

**The correct pattern:** Unmanaged packages are a specific Salesforce artifact type that can be installed via a URL. Metadata API deployments are a deployment mechanism. Unlocked packages and managed packages are versioned, immutable artifacts with distinct lifecycle management. These are not interchangeable — each has distinct installation, versioning, and dependency management behaviors.

**Detection hint:** Any response that equates "unmanaged package" with "metadata deployment" without noting the installation and lifecycle differences is imprecise.

---

## Anti-Pattern 6: Recommending Beta Package Versions for Production Subscriber Installations

**What the LLM generates:** "Create a beta version of your package and install it in the subscriber's org to test before releasing."

**Why it happens:** LLMs apply software "beta testing" concepts to Salesforce package beta versions without noting the restrictions.

**The correct pattern:** Salesforce 2GP beta package versions (created with `--skip-validation`) cannot be installed in production orgs. They can only be installed in sandbox orgs and scratch orgs. If a subscriber needs to test a pre-release version, use a patch version or a release candidate (full validation). Beta versions are for internal developer testing only.

**Detection hint:** Any workflow that installs a beta package version (`--skip-validation`) in a subscriber's production org is not possible — the installation will fail.
