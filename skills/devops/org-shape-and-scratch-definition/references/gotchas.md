# Gotchas -- Org Shape And Scratch Definition

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Org Shape Silently Excludes Key Features

**What happens:** When using `sourceOrg` for Org Shape, the resulting scratch org is missing features like MultiCurrency, PersonAccounts, and certain ISV-partner features. No error or warning is produced during org creation. The absence only surfaces when deploying metadata or running code that depends on those features.

**When it occurs:** Every time Org Shape is used and the source org has MultiCurrency, PersonAccounts, or ISV-specific features enabled. This is by design, not a bug.

**How to avoid:** Maintain a documented list of features your source org uses that are excluded from Org Shape. Declare them explicitly in the `features` array alongside `sourceOrg`. Test the scratch org after creation by verifying feature availability in Setup before starting development.

---

## Gotcha 2: orgPreferences Silently Ignored in Modern CLI

**What happens:** The `orgPreferences` block in the definition file is deprecated since Winter '20. Some CLI versions silently skip it instead of throwing an error. Scratch orgs are created successfully, but the preferences (Translation Workbench, Chatter, Lightning Experience, etc.) are not applied.

**When it occurs:** When a legacy definition file containing `orgPreferences` is used with Salesforce CLI v2 or recent versions of the `sf` CLI. The CLI does not always warn about the deprecated key.

**How to avoid:** Search your definition file for the string `orgPreferences`. If found, migrate every preference to the equivalent `settings` block using Metadata API settings type names. Run `sf org create scratch` and verify the settings are applied in the resulting org.

---

## Gotcha 3: Feature Names Are Case-Sensitive with No Fuzzy Matching

**What happens:** Declaring a feature with incorrect casing (e.g., `"multicurrency"` instead of `"MultiCurrency"`, or `"personaccounts"` instead of `"PersonAccounts"`) causes org creation to fail with an `INVALID_INPUT` error. The error message does not suggest the correct spelling.

**When it occurs:** Any time a human or AI writes a feature name from memory rather than copying it from the official documentation.

**How to avoid:** Always copy feature names from the official Salesforce documentation or a validated definition file. Keep a reference list of feature names in your project wiki. The checker script in this skill validates feature name casing.

---

## Gotcha 4: Dev Hub Edition Limits Which Features and Editions Are Available

**What happens:** The Dev Hub org's edition constrains what scratch orgs can be created. An Enterprise Edition Dev Hub cannot create scratch orgs with features that require Unlimited or Performance edition entitlements. A Developer Edition Dev Hub cannot use Org Shape at all.

**When it occurs:** When a team uses a Developer Edition Dev Hub (common in partner orgs or trial environments) and tries to enable Org Shape, or when a definition file specifies features that exceed the Dev Hub's entitlements.

**How to avoid:** Verify the Dev Hub edition before authoring the definition file. Use `sf org display --target-org <devhub>` to check. For Org Shape, ensure the Dev Hub is Enterprise Edition or higher. For specific features, confirm entitlement in the Dev Hub's Company Information page.

---

## Gotcha 5: release Field Behavior Changes During Preview Windows

**What happens:** When `release` is omitted from the definition file, scratch orgs default to the current release. During Salesforce preview windows (approximately three weeks before each release), "current" means the preview release. This causes scratch orgs to be provisioned on an unreleased version with potentially different API behavior, breaking CI pipelines that were stable the day before.

**When it occurs:** Three times per year during the Spring, Summer, and Winter preview windows. The exact dates vary and are announced on the Salesforce Trust site.

**How to avoid:** Set `"release": "Previous"` in definition files used by CI pipelines to ensure they always get the GA release. Maintain a separate definition file with `"release": "Preview"` for intentional forward-compatibility testing.
