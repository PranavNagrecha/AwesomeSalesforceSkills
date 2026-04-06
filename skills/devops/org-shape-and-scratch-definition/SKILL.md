---
name: org-shape-and-scratch-definition
description: "Use this skill when authoring, debugging, or optimizing a scratch org definition file (project-scratch-def.json): schema structure, features array, settings hierarchy, Org Shape sourcing, edition selection, orgPreferences-to-settings migration, and release pinning. NOT for scratch org lifecycle management (use scratch-org-management), CI pipeline design, or sandbox configuration."
category: devops
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
  - Security
triggers:
  - "my scratch org is missing a feature I expected like Communities or MultiCurrency"
  - "I need to write a project-scratch-def.json that matches our production org capabilities"
  - "how do I use Org Shape and still declare features that Org Shape does not capture"
  - "scratch org creation fails with INVALID_INPUT or unsupported feature error"
  - "should I use orgPreferences or settings in my scratch org definition file"
tags:
  - scratch-org-definition
  - org-shape
  - project-scratch-def
  - dev-hub
  - sfdx
  - devops
inputs:
  - "Target org edition and features that must be available in the scratch org"
  - "Dev Hub org edition (Enterprise, Performance, Unlimited, or Partner)"
  - "Source org ID if using Org Shape"
  - "Specific Salesforce settings or preferences required (e.g., Translation Workbench, Person Accounts, MultiCurrency)"
outputs:
  - "A valid project-scratch-def.json file with correct schema, features, and settings"
  - "Diagnosis of definition-file errors and recommended fixes"
  - "Migration guidance from deprecated orgPreferences to settings blocks"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-05
---

# Org Shape and Scratch Definition

This skill activates when a practitioner needs to author, troubleshoot, or refine the scratch org definition file (`project-scratch-def.json`). It covers the full schema depth of the definition file including edition selection, feature declarations, settings blocks, Org Shape sourcing, and release channel pinning. It does not cover scratch org lifecycle commands, CI pipeline orchestration, or sandbox strategy.

---

## Before Starting

Gather this context before working on anything in this domain:

- What Dev Hub edition is in use? Org Shape requires Enterprise Edition or higher on the Dev Hub.
- Which features does the target org need that go beyond the default Developer edition scratch org (e.g., Communities, MultiCurrency, ServiceCloud, PersonAccounts)?
- Is the team migrating from the deprecated `orgPreferences` block, or starting fresh with `settings`?

---

## Core Concepts

Understanding the scratch org definition file requires clarity on four areas: schema structure, the features array, the settings hierarchy, and Org Shape.

### Definition File Schema

The `project-scratch-def.json` file is the declarative blueprint for a scratch org. It lives at the root of an SFDX project (or a path specified by `--definition-file`). The top-level keys include `orgName`, `edition`, `features`, `settings`, `language`, `country`, `hasSampleData`, `release`, and `sourceOrg`. The `edition` field accepts values like `Developer`, `Enterprise`, `Group`, and `Professional`. If omitted, `Developer` is the default. The edition determines the baseline feature ceiling -- for example, you cannot use Record Types in a `Group` edition scratch org.

### Features Array

The `features` array enables specific platform capabilities that are not part of the base edition. Examples include `Communities`, `ServiceCloud`, `LightningServiceConsole`, `API`, `AuthorApex`, `MultiCurrency`, `PersonAccounts`, `StateAndCountryPicklist`, and `AnalyticsCRMAnalyticsPlusPlatform`. Feature names are case-sensitive strings. An invalid or misspelled feature name causes org creation to fail with an `INVALID_INPUT` error. Some features depend on edition -- for instance, `PersonAccounts` requires `Enterprise` edition or higher.

### Settings Hierarchy

Since Winter '20, the `settings` object replaced the deprecated `orgPreferences` block. Settings are organized by Metadata API type. For example, Translation Workbench is enabled via `languageSettings.enableTranslationWorkbench: true`, and chatter is controlled by `chatterSettings.enableChatter: true`. The structure mirrors the Salesforce Metadata API settings types, so any setting available in `<SettingsType>` metadata can be expressed here using camelCase property paths. Attempting to use the old `orgPreferences` key will produce a deprecation warning and may be silently ignored in newer CLI versions.

### Org Shape

Org Shape lets you create scratch orgs that replicate the shape (features, settings, limits) of an existing source org. You enable it by setting `"sourceOrg": "<orgId>"` in the definition file and omitting `edition`, `features`, and `settings` that conflict. The source org must be connected to the Dev Hub. However, Org Shape does not capture every feature -- notably, `MultiCurrency`, `PersonAccounts`, and certain ISV features are excluded and must still be declared explicitly in the `features` array alongside the `sourceOrg` reference. Org Shape is only available when the Dev Hub is Enterprise Edition or above.

---

## Common Patterns

### Pattern: Hybrid Org Shape with Explicit Feature Overrides

**When to use:** Your team wants scratch orgs that closely mirror production but production uses features Org Shape does not capture (MultiCurrency, PersonAccounts).

**How it works:**
1. Set `sourceOrg` to the 15- or 18-character Org ID of the source org.
2. Add the uncaptured features to the `features` array explicitly.
3. Add any settings that Org Shape does not carry over to the `settings` block.
4. Omit `edition` -- Org Shape infers it from the source.

```json
{
  "sourceOrg": "00D000000000001",
  "features": ["MultiCurrency", "PersonAccounts"],
  "settings": {
    "languageSettings": {
      "enableTranslationWorkbench": true
    }
  }
}
```

**Why not the alternative:** Using Org Shape alone silently omits these features, leading to deployment failures or missing functionality during development that only surfaces during UAT.

### Pattern: Edition-Pinned Minimal Definition for Package Development

**When to use:** You are building an unlocked or managed package and need a lightweight, fast-provisioning scratch org with only the features the package requires.

**How it works:**
1. Set `edition` explicitly (usually `Developer`).
2. Declare only the features your package metadata requires.
3. Pin `release` to `"Previous"` if you need stability against preview-release breakage.

```json
{
  "orgName": "Package Dev Scratch",
  "edition": "Developer",
  "features": ["LightningComponentBundle", "API"],
  "settings": {
    "lightningExperienceSettings": {
      "enableS1DesktopEnabled": true
    }
  },
  "release": "Previous"
}
```

**Why not the alternative:** Including unnecessary features slows provisioning and introduces surface area for flaky CI failures.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Scratch orgs must closely mirror production | Org Shape + explicit feature overrides | Captures most settings automatically; fill gaps with features array |
| Building a package with minimal dependencies | Edition-pinned definition with targeted features | Faster provisioning, fewer moving parts, reproducible across Dev Hubs |
| Team needs stability during Salesforce preview windows | Set `"release": "Previous"` | Avoids preview-release regressions breaking CI pipelines |
| Migrating from legacy orgPreferences | Replace with equivalent settings blocks | orgPreferences deprecated since Winter '20; settings is the only supported path |
| Definition file works locally but fails in CI | Audit Dev Hub edition and feature entitlements | CI Dev Hub may have different edition or missing feature licenses |

---

## Recommended Workflow

Step-by-step instructions for authoring or debugging a scratch org definition file:

1. **Identify target capabilities** -- List every Salesforce feature, setting, and edition requirement the development work needs. Cross-reference with the source production org if available.
2. **Choose sourcing strategy** -- Decide between Org Shape (`sourceOrg`) and manual feature/settings declaration. Use Org Shape when the source org is Enterprise+ and the Dev Hub supports it; otherwise, declare manually.
3. **Draft the definition file** -- Write `project-scratch-def.json` with the chosen edition (or sourceOrg), features array, and settings blocks. Use the Metadata API settings type names for the settings hierarchy.
4. **Validate feature names** -- Confirm each feature string against the official Salesforce feature list. Misspelled or unsupported feature names cause creation failure with no partial-match hint.
5. **Test org creation** -- Run `sf org create scratch --definition-file config/project-scratch-def.json --target-dev-hub <hub>` and inspect the output for warnings or errors. Fix any `INVALID_INPUT` messages.
6. **Verify feature availability** -- After creation, open the scratch org and confirm the expected features are enabled (e.g., check Setup > Company Information for MultiCurrency, check Communities setup page).
7. **Commit and document** -- Store the validated definition file in the project repo under `config/`. Document any Org Shape gaps that required explicit overrides.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Definition file has valid JSON syntax and all required top-level keys
- [ ] Edition is appropriate for the features declared (no Group edition with Record Types)
- [ ] No use of deprecated `orgPreferences` -- all preferences expressed via `settings`
- [ ] Org Shape source org is connected to the Dev Hub (if using sourceOrg)
- [ ] Features excluded from Org Shape (MultiCurrency, PersonAccounts) are declared explicitly
- [ ] Feature names are spelled exactly as documented (case-sensitive)
- [ ] `release` is set intentionally (`Previous`, `Current`, or omitted for default)
- [ ] Scratch org creation succeeds and target features are verified in the running org

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Org Shape silently omits features** -- MultiCurrency, PersonAccounts, and certain ISV-specific features are not captured by Org Shape. The scratch org creates successfully but is missing capabilities, which only surfaces when deploying metadata that depends on them.
2. **orgPreferences deprecation is silent** -- Since Winter '20, `orgPreferences` is deprecated. Some CLI versions silently ignore it rather than erroring, so your definition file appears to work but the preferences are not applied.
3. **Feature names are case-sensitive** -- Declaring `"multicurrency"` instead of `"MultiCurrency"` produces an `INVALID_INPUT` error. There is no fuzzy matching or helpful suggestion in the error message.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| `project-scratch-def.json` | The validated scratch org definition file ready for use with `sf org create scratch` |
| Definition file audit report | List of issues found in an existing definition file (deprecated keys, missing features, edition mismatches) |

---

## Related Skills

- scratch-org-management -- Use for scratch org lifecycle operations (creation, deletion, allocation management, CI automation)
- unlocked-package-development -- Use when the definition file is part of a package development workflow
- environment-strategy -- Use for broader environment planning across sandboxes, scratch orgs, and production

---

## Official Sources Used

- Scratch Org Definition File -- https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_scratch_orgs_def_file.htm
- Scratch Org Definition Configuration Values -- https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_scratch_orgs_def_file_config_values.htm
- Salesforce DX Developer Guide -- https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_intro.htm
