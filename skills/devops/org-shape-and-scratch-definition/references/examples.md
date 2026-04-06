# Examples -- Org Shape And Scratch Definition

## Example 1: Hybrid Org Shape with MultiCurrency and Person Accounts

**Context:** A financial services company uses Person Accounts and MultiCurrency in production. The team adopts Org Shape to replicate the production environment in scratch orgs for development.

**Problem:** After creating scratch orgs with only `sourceOrg`, developers discover that Person Accounts and MultiCurrency are missing. Deployment of Account-related metadata fails because the scratch org lacks the PersonAccount record type. The team assumes Org Shape is broken, but it is working as designed -- these features are explicitly excluded from Org Shape capture.

**Solution:**

```json
{
  "sourceOrg": "00D5f000003EXAMPLE",
  "features": ["MultiCurrency", "PersonAccounts"],
  "settings": {
    "accountSettings": {
      "enableAccountOwnerReport": true
    }
  }
}
```

**Why it works:** Org Shape captures the bulk of the source org's shape -- edition, most features, and most settings. The features array supplements it with the specific capabilities Org Shape does not capture. This hybrid approach gives the best of both worlds: automatic mirroring for the 90% case and explicit declaration for the known gaps.

---

## Example 2: Migrating from Deprecated orgPreferences to Settings

**Context:** A team's `project-scratch-def.json` has been in use since 2018 and still uses the `orgPreferences` block to enable Translation Workbench and Chatter. After a CLI upgrade, developers notice these preferences are no longer being applied to new scratch orgs, but no error is thrown.

**Problem:** The `orgPreferences` block was deprecated in Winter '20. Newer CLI versions silently ignore it. The scratch orgs are created without Translation Workbench, which causes deployment failures for custom labels with translations.

**Solution:**

```json
{
  "orgName": "Team Dev Org",
  "edition": "Developer",
  "features": ["API", "AuthorApex"],
  "settings": {
    "languageSettings": {
      "enableTranslationWorkbench": true
    },
    "chatterSettings": {
      "enableChatter": true
    },
    "lightningExperienceSettings": {
      "enableS1DesktopEnabled": true
    }
  }
}
```

Before (deprecated, silently ignored):

```json
{
  "orgPreferences": {
    "enabled": [
      "S1DesktopEnabled",
      "Translation",
      "ChatterEnabled"
    ]
  }
}
```

**Why it works:** The `settings` block maps directly to Metadata API settings types. Each setting type (e.g., `languageSettings`, `chatterSettings`) corresponds to a Metadata API type, and property names use camelCase. This approach is forward-compatible and actively maintained by Salesforce.

---

## Example 3: Pinning Release Channel for CI Stability

**Context:** A team's CI pipeline creates scratch orgs on every pull request. During Salesforce preview windows (roughly three times per year), their pipeline starts failing because new scratch orgs are provisioned on the preview release, which has API changes and behavior differences.

**Problem:** Without release pinning, scratch orgs default to the current preview release during the preview window. Apex tests that passed yesterday now fail due to changed platform behavior.

**Solution:**

```json
{
  "orgName": "CI Scratch",
  "edition": "Developer",
  "features": ["API"],
  "release": "Previous",
  "settings": {
    "lightningExperienceSettings": {
      "enableS1DesktopEnabled": true
    }
  }
}
```

**Why it works:** Setting `"release": "Previous"` ensures scratch orgs are always provisioned on the current GA release, even during preview windows. This gives the CI pipeline stability. The team can maintain a separate definition file with `"release": "Preview"` for forward-compatibility testing on a non-blocking branch.

---

## Anti-Pattern: Copying the Full Org Shape and Then Overriding Everything

**What practitioners do:** They set `sourceOrg` to mirror production but then also declare `edition`, a full `features` array, and extensive `settings` blocks that duplicate or contradict what Org Shape provides.

**What goes wrong:** When both `sourceOrg` and `edition` are specified, the behavior is unpredictable. Some features may conflict, producing cryptic errors during org creation. Even when creation succeeds, the resulting org may not match expectations because the explicit values do not cleanly merge with the shape-derived values.

**Correct approach:** Use Org Shape for the baseline and only add explicit `features` or `settings` for capabilities that Org Shape is documented as not capturing. Never set `edition` alongside `sourceOrg` -- let Org Shape infer the edition from the source org.
