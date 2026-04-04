# LLM Anti-Patterns — OmniScript Versioning

## 1. Suggesting CLI Commands That Do Not Exist for OmniScript Activation

**What the LLM generates wrong:** The LLM suggests commands like `sf omnistudio activate --type CreateCase --subtype Default` or `sf data deploy omniscript-version`.

**Why it happens:** The LLM knows Salesforce CLI patterns and analogizes from other metadata types. OmniScript activation does not have a direct CLI command — it is a property set via the UI, DataPack import, or Metadata API.

**Correct pattern:** OmniScript activation is done via (1) the OmniStudio UI, (2) DataPack import with the activate option, or (3) Metadata API deployment setting `IsActive: true` on the `OmniProcess` metadata type. There is no standalone `sf omnistudio activate` command.

**Detection hint:** Any CLI command that includes "activate" with an omniscript-specific subcommand.

---

## 2. Claiming Inactive Versions Are Automatically Deleted

**What the LLM generates wrong:** "When you activate version 5, version 4 is automatically deleted and cannot be used for rollback."

**Why it happens:** Some deployment systems auto-purge old artifacts. The LLM applies this mental model to OmniStudio.

**Correct pattern:** Inactive OmniScript versions are NOT deleted when a new version is activated. They persist in the org until explicitly deleted. This is exactly what makes rollback possible — reactivate the prior version number.

**Detection hint:** Any statement that inactive versions are deleted or purged automatically on activation.

---

## 3. Suggesting Direct Production Editing as a Safe Practice

**What the LLM generates wrong:** "To quickly fix a typo in the active OmniScript, you can edit it directly in production — since it's already active, you don't need to create a new version for minor changes."

**Why it happens:** The LLM optimizes for convenience. Some systems do allow in-place edits to live configurations for minor changes.

**Correct pattern:** Editing an active OmniScript in production changes the definition for all current and future users immediately, and creates no versioned rollback point. Always create a new version, test it in a sandbox, and activate the new version. Even typo fixes should follow this process in a production org with active users.

**Detection hint:** Any recommendation to edit an active OmniScript in production directly.

---

## 4. Treating OmniScript Version Numbers as Semantic Versions

**What the LLM generates wrong:** "Use version 2.0.0 for major changes and 2.0.1 for patches."

**Why it happens:** Semantic versioning (Major.Minor.Patch) is a common convention. The LLM applies it to OmniScript.

**Correct pattern:** OmniScript version numbers are sequential integers auto-assigned by the platform (1, 2, 3...). You cannot set custom version labels. Semantic meaning must be tracked externally — in release notes, a custom object, or a version tracking convention your team documents separately.

**Detection hint:** Any reference to "2.0.0", "v2.1", or semantic versioning notation for OmniScript versions.

---

## 5. Not Mentioning the Type/Subtype/Language Identity Triplet

**What the LLM generates wrong:** Instructions for activating "the CreateCase OmniScript version 4" without specifying the Subtype and Language.

**Why it happens:** Simple examples in documentation often use just the Type name. The LLM omits the Subtype and Language as "optional details."

**Correct pattern:** OmniScript identity is always the full triplet: Type + Subtype + Language. Version numbers exist within that triplet. Always include all three when describing an activation, rollback, or version comparison. Different languages of the same OmniScript have independent version histories.

**Detection hint:** Any OmniScript activation or rollback instruction that identifies the script by Type alone without Subtype and Language.
