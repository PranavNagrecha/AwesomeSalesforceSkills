---
name: multi-language-and-translation
description: "Use when configuring Salesforce Translation Workbench, translating custom labels, picklist values, field labels, page layout sections, or Experience Cloud language switcher. Triggers: 'how to add a language to Salesforce', 'translate custom labels', 'Translation Workbench setup', 'picklist value translation', 'RTL language support'. NOT for Marketing Cloud email localization, NOT for Apex string formatting by locale (use formula fields or Apex String.format patterns), NOT for multi-currency (use currency management admin)."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - User Experience
  - Operational Excellence
triggers:
  - "how do I translate custom labels and field labels into Spanish or French"
  - "my Experience Cloud site needs to support multiple languages with a language switcher"
  - "how do I enable Translation Workbench and add a new language to the org"
  - "picklist values are showing in English even after I added translations"
  - "how do I support right-to-left languages like Arabic or Hebrew in Salesforce"
tags:
  - translation
  - multi-language
  - translation-workbench
  - custom-labels
  - localization
  - experience-cloud
inputs:
  - "List of languages to support and their locale codes (e.g., es for Spanish)"
  - "List of components to translate: field labels, picklist values, custom labels, validation messages"
  - "Whether the org uses Experience Cloud sites with language switcher"
outputs:
  - "Translation Workbench configuration steps for each language"
  - "Export/import workflow for bulk translations via Translation Workbench spreadsheet"
  - "Custom label translation setup"
  - "Experience Cloud language switcher configuration"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-04
---

# Multi-Language and Translation

Use this skill when configuring Salesforce to support multiple languages for internal users or Experience Cloud site visitors. This covers enabling Translation Workbench, adding supported languages, translating custom labels, field labels, picklist values, page layout section names, and configuring the Experience Cloud language switcher.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm the org edition — Translation Workbench requires Enterprise, Unlimited, Performance, or Developer Edition.
- Identify the languages to add using their Salesforce locale code (e.g., `es` for Spanish, `fr` for French, `ar` for Arabic).
- Determine what needs translating: field labels, picklist values, custom labels, validation rule error messages, page layout section names. Each has a different translation path.
- For RTL languages (Arabic, Hebrew), confirm the org has enabled RTL support and test the UI rendering — not all custom components support RTL automatically.

---

## Core Concepts

### Translation Workbench Architecture

Translation Workbench (Setup > Translation Workbench > Translation Settings) is the central management tool for Salesforce UI translations. Key concepts:

- **Default language**: The org's default language. All metadata is authored in this language.
- **Supported languages**: Languages you enable in Translation Workbench. Only supported languages are available to users and translatable via the Workbench.
- **Translation override vs. auto-translation**: Translations for standard Salesforce UI elements are provided by Salesforce for supported languages. Custom components (custom labels, custom field labels, picklist values) require manual entry or import.

### Custom Label Translations

Custom Labels (`Setup > Custom Labels`) are the standard mechanism for translatable string constants used in Apex, Visualforce, and Flow. Each label supports translations per language:

1. Create the Custom Label with the English value.
2. Open the label, click "New Local Translations/Overrides".
3. Select the language, enter the translated value.

In Apex: `System.Label.My_Label` returns the translation for the running user's language.
In Visualforce: `{!$Label.My_Label}` returns the translation.
In Flow: Use the `{!$Label.My_Label}` merge field in text elements.

### Picklist Value Translation

Picklist values are translated via Translation Workbench > Translate:
1. Select the entity type: "Picklist Value"
2. Select the object and picklist field
3. Enter translated values for each language

**Critical rule**: The picklist value API value (the stored database value) does not change when you add translations. Only the displayed label changes. Validation rules and Apex should use the API value, not the translated label.

### Experience Cloud Language Switcher

For Experience Cloud sites:
1. Enable Translation Workbench and add supported languages.
2. In Experience Builder, add the Language Switcher component to the site header.
3. In Site Settings, set the default language and enable language-specific content.
4. Translated content for Experience Cloud pages is managed via Content Management or by creating language variants of the site.

### RTL Language Support

For Arabic (ar), Hebrew (iw/he), or other RTL languages:
- Salesforce Lightning Experience supports RTL layout natively when the user's language is set to a RTL locale.
- Custom LWC components may need CSS `direction: rtl` and `text-align: start` adjustments.
- Experience Cloud sites support RTL via the site-level language setting.

---

## Common Patterns

### Bulk Export/Import via Translation Workbench Spreadsheet

**When to use:** Large orgs with hundreds of custom labels, picklist values, or field labels to translate.

**How it works:**
1. Translation Workbench > Export Translations: select the language and metadata types to export.
2. The export generates a ZIP containing a bilingual tab-delimited text file.
3. Send the file to a translation service. They fill the translation column.
4. Import via Translation Workbench > Import Translations: upload the completed file.

**Why not manual entry:** Manual entry is impractical for large translation sets. The export/import workflow enables external translation vendors and version control of translated strings.

### Validation Rule Error Message Translation

**When to use:** Validation rule error messages must display in the user's language.

**How it works:**
1. Write the validation rule error message using a Custom Label merge field: `$Label.Account_Name_Required`.
2. Create translations for that label in each supported language.
3. When the validation rule fires, the error message displays in the user's language.

**Why not hardcode the message in the formula:** A hardcoded message string in a validation rule formula cannot be translated.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Translating standard field labels | Translation Workbench > Standard Field Labels | Native mechanism |
| Translating custom field labels | Translation Workbench > Custom Field Labels | Native mechanism |
| Translating picklist values | Translation Workbench > Picklist Values | API value unchanged; only label translated |
| Translating strings in Apex/VF/Flow | Custom Labels with per-language translations | Labels are the standard translation mechanism for code strings |
| Large-scale translation (100+ items) | Export/import via Translation Workbench spreadsheet | Enables vendor translation workflow |
| Experience Cloud multi-language | Language Switcher component + Translation Workbench | Native Experience Cloud localization |
| RTL support | Enable RTL language, test custom components | Custom LWC may need CSS direction adjustments |

---

## Recommended Workflow

1. **Enable Translation Workbench.** Setup > Translation Workbench > Translation Settings > Enable.
2. **Add supported languages.** For each language, select it and set an active translator user (optional). Language becomes available to users and translatable.
3. **Audit translatable components.** List all custom labels, custom field labels, custom picklist values, page layout section names, and validation rule messages that need translation.
4. **For code strings in Apex/Visualforce/Flow:** Ensure all user-facing strings use Custom Labels (not hardcoded). Create translations for each label in each supported language.
5. **For field/picklist labels:** Enter translations via Translation Workbench > Translate, or use the bulk export/import workflow for large volumes.
6. **Test each language.** Create a test user with the target language locale. Log in as that user and verify that all translated elements display correctly in the target language.
7. **For Experience Cloud:** Add Language Switcher component to site header. Test the switcher and confirm page content changes language as expected.

---

## Review Checklist

- [ ] Translation Workbench enabled and required languages added as Supported Languages
- [ ] All custom labels used for user-facing strings have translations for each supported language
- [ ] Picklist values translated — API values confirmed unchanged
- [ ] Validation rule error messages use Custom Labels (not hardcoded strings)
- [ ] Tested with a user whose profile language is set to each supported language
- [ ] Experience Cloud language switcher configured and tested (if applicable)
- [ ] RTL languages tested in relevant UI contexts — custom components checked for direction issues

---

## Salesforce-Specific Gotchas

1. **Picklist API value does NOT change with translation** — Translations only affect the displayed label. Validation rules, Apex conditions, and SOQL WHERE clauses must use the API value (the English/default language value), not the translated label.
2. **Translation Workbench export includes metadata you may not intend to translate** — The export for a language includes all translatable metadata. Review the export carefully before sending to a vendor to avoid including internal/system labels that should not change.
3. **RTL support requires more than enabling the language** — Native Lightning Experience and standard components support RTL. Custom LWC components and Experience Cloud custom templates may need explicit CSS `direction: rtl` adjustments.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Translation enablement checklist | Step-by-step list for enabling Translation Workbench and adding languages |
| Translation audit spreadsheet | Inventory of all translatable components with current status per language |
| Custom Label translation guide | How to create and maintain label translations for each supported language |

---

## Related Skills

- picklist-and-value-sets — picklist design and value management (upstream of translation)
- experience-cloud-security — Experience Cloud configuration (includes language/region settings)
