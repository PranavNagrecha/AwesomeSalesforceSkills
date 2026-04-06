# LLM Anti-Patterns -- Org Shape And Scratch Definition

Common mistakes AI coding assistants make when generating or advising on scratch org definition files.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Using Deprecated orgPreferences Instead of Settings

**What the LLM generates:**

```json
{
  "orgPreferences": {
    "enabled": ["S1DesktopEnabled", "ChatterEnabled"]
  }
}
```

**Why it happens:** Training data contains many pre-Winter '20 examples that use `orgPreferences`. The LLM has seen this pattern far more frequently than the newer `settings` block.

**Correct pattern:**

```json
{
  "settings": {
    "lightningExperienceSettings": {
      "enableS1DesktopEnabled": true
    },
    "chatterSettings": {
      "enableChatter": true
    }
  }
}
```

**Detection hint:** Search for the string `orgPreferences` in generated JSON. Any occurrence is incorrect for modern Salesforce CLI usage.

---

## Anti-Pattern 2: Inventing Non-Existent Feature Names

**What the LLM generates:**

```json
{
  "features": ["LightningExperience", "ChatterEnabled", "RecordTypes", "CustomObjects"]
}
```

**Why it happens:** The LLM infers feature names from general Salesforce terminology rather than the specific list of valid scratch org feature strings. Names like `LightningExperience` and `RecordTypes` sound plausible but are not valid feature values.

**Correct pattern:**

```json
{
  "features": ["API", "AuthorApex", "Communities", "LightningComponentBundle"]
}
```

**Detection hint:** Compare each feature name against the official configuration values documentation. Flag any feature name that does not appear in the Salesforce DX scratch org features reference.

---

## Anti-Pattern 3: Setting Both sourceOrg and edition

**What the LLM generates:**

```json
{
  "sourceOrg": "00D5f000003EXAMPLE",
  "edition": "Enterprise",
  "features": ["MultiCurrency"]
}
```

**Why it happens:** The LLM treats `edition` as a required field and includes it alongside `sourceOrg` to be "safe." In reality, Org Shape infers the edition from the source org, and specifying both can cause conflicts or unpredictable behavior.

**Correct pattern:**

```json
{
  "sourceOrg": "00D5f000003EXAMPLE",
  "features": ["MultiCurrency"]
}
```

**Detection hint:** If the JSON contains both `"sourceOrg"` and `"edition"` at the top level, flag it as a conflict.

---

## Anti-Pattern 4: Wrong Case on Feature Names

**What the LLM generates:**

```json
{
  "features": ["multicurrency", "personAccounts", "communities", "stateAndCountryPicklist"]
}
```

**Why it happens:** LLMs normalize text to common casing conventions (camelCase, lowercase). Salesforce feature names use a specific PascalCase convention that does not follow consistent rules -- `MultiCurrency`, `PersonAccounts`, `Communities`, `StateAndCountryPicklist`.

**Correct pattern:**

```json
{
  "features": ["MultiCurrency", "PersonAccounts", "Communities", "StateAndCountryPicklist"]
}
```

**Detection hint:** Compare feature names case-sensitively against the official list. Any lowercase-starting feature name in the features array is suspect.

---

## Anti-Pattern 5: Treating Org Shape as Complete

**What the LLM generates:** "Use Org Shape to mirror your production org. Set `sourceOrg` and you are done -- no need to specify features or settings."

**Why it happens:** The LLM oversimplifies Org Shape by treating it as a full clone of the source org. Documentation says Org Shape captures the "shape," which the LLM interprets as everything.

**Correct pattern:** "Use Org Shape as a baseline, then explicitly declare features that Org Shape does not capture. Known exclusions include MultiCurrency, PersonAccounts, and certain ISV features. Always verify the resulting scratch org has the features you need."

**Detection hint:** If guidance says Org Shape captures "everything" or "all features" without caveats, flag it. Look for absence of MultiCurrency/PersonAccounts exception notes.

---

## Anti-Pattern 6: Placing Settings Under Wrong Metadata Type Names

**What the LLM generates:**

```json
{
  "settings": {
    "translationSettings": {
      "enableTranslationWorkbench": true
    }
  }
}
```

**Why it happens:** The LLM guesses at Metadata API type names. The correct type is `languageSettings`, not `translationSettings`. These names do not always follow intuitive naming.

**Correct pattern:**

```json
{
  "settings": {
    "languageSettings": {
      "enableTranslationWorkbench": true
    }
  }
}
```

**Detection hint:** Cross-reference each settings key against the Metadata API settings types. Common mistakes include `translationSettings` (correct: `languageSettings`), `emailSettings` (correct: `emailAdministrationSettings`), and `securitySettings` (correct: `securitySettings` is valid but specific sub-settings may live under `passwordPolicies` or `sessionSettings`).

---

## Anti-Pattern 7: Omitting release Field Without Understanding Default Behavior

**What the LLM generates:** A definition file with no `release` field and no mention of release pinning, even when the user asks about CI stability.

**Why it happens:** The LLM does not associate CI stability with Salesforce release cycles. It treats the definition file as a static document and does not consider the temporal behavior of scratch org provisioning during preview windows.

**Correct pattern:** When CI stability is a concern, always include `"release": "Previous"` and explain that omitting it means scratch orgs will use the preview release during Salesforce preview windows, which occur three times per year.

**Detection hint:** If the context mentions CI, pipelines, or stability, and the generated definition file has no `release` field, flag it as incomplete.
